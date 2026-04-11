"""
記事生成モジュール
Claude APIを使って、話題のAIテーマを調査し初心者向け解説記事を生成します
"""

import json
import os
import anthropic
from datetime import datetime
from pathlib import Path

ARTICLES_DIR = Path("data/articles")


def build_theme_research_prompt(source_articles: list) -> str:
    """収集した記事からAIテーマ候補を抽出するプロンプト"""
    articles_text = "\n".join([
        f"・{a['title']} ({a['source']})"
        for a in source_articles[:15]
    ])

    return f"""あなたはAI分野のトレンドリサーチャーです。

以下は最新のニュース・記事一覧です：
{articles_text}

これらを分析して、今最も注目されているAIテーマを3つ選んでください。

必ず以下のJSON形式のみで返答してください（コードブロック不要）：
{{
  "themes": [
    {{
      "theme": "テーマ名（20文字以内）",
      "reason": "なぜ今注目されているか（50文字以内）",
      "score": 注目度スコア（1-10の整数）
    }},
    {{
      "theme": "テーマ名2",
      "reason": "理由2",
      "score": スコア2
    }},
    {{
      "theme": "テーマ名3",
      "reason": "理由3",
      "score": スコア3
    }}
  ],
  "selected_theme": "最も注目度が高いテーマ名",
  "selected_reason": "選んだ理由（100文字以内）"
}}"""


def build_article_prompt(theme: str, reason: str, source_articles: list) -> str:
    """選ばれたテーマで初心者向け解説記事を生成するプロンプト"""
    articles_text = "\n".join([
        f"・{a['title']}"
        for a in source_articles[:5]
    ])

    return f"""あなたはnote向けの初心者向けAI解説記事を書く専門ライターです。

【テーマ】{theme}
【注目理由】{reason}
【参考ニュース】
{articles_text}

以下の構成で、AI初心者でも分かりやすい解説記事を書いてください：

【構成ルール】
1. 話題の概要（このテーマが何かを一言で説明）
2. なぜ今注目されているか（背景・きっかけ）
3. 仕組みをやさしく説明（専門用語には必ずかんたんな補足をつける）
4. 実際に何が変わるか（私たちの生活・仕事への影響）
5. 注意点（リスク・課題・気をつけること）

【文体ルール】
- 「です・ます調」で統一
- 煽りすぎず、分かりやすさ重視
- 専門用語には必ず（）で補足説明をつける
- 読者に語りかける文体
- 本文は1,500〜2,500文字

必ず以下のJSON形式のみで返答してください（コードブロック不要）：
{{
  "title": "選ばれたメインタイトル（30〜40文字）",
  "title_alternatives": ["タイトル案2（30〜40文字）", "タイトル案3（30〜40文字）"],
  "lead": "リード文（150〜200文字、記事の価値を端的に伝える）",
  "body": "本文（Markdown形式、## で5つの見出しを使って構造化）",
  "summary": "まとめ（200〜300文字、読者への行動促進）",
  "hashtags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5", "タグ6", "タグ7", "タグ8", "タグ9", "タグ10"],
  "estimated_read_time": 読了時間（分・整数）,
  "theme": "{theme}"
}}"""


def generate_article(source_title, source_summary, category, source_url, source_name, all_articles=None):
    """
    Claude APIを使って記事を生成する
    all_articles: 収集した全記事リスト（テーマ選定に使用）
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が設定されていません")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    # 記事リストがない場合は単一記事から生成
    if not all_articles:
        all_articles = [{"title": source_title, "source": source_name}]

    try:
        # Step 1: テーマ候補を3つ抽出
        print("🔍 話題のAIテーマを調査中...")
        theme_response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": build_theme_research_prompt(all_articles)
            }]
        )

        theme_text = theme_response.content[0].text
        if "```json" in theme_text:
            theme_json = theme_text.split("```json")[1].split("```")[0].strip()
        elif "```" in theme_text:
            theme_json = theme_text.split("```")[1].split("```")[0].strip()
        else:
            theme_json = theme_text.strip()

        theme_data = json.loads(theme_json)
        themes = theme_data.get("themes", [])
        selected_theme = theme_data.get("selected_theme", source_title)
        selected_reason = theme_data.get("selected_reason", "")

        print(f"📋 テーマ候補:")
        for t in themes:
            print(f"  {'★' if t['theme'] == selected_theme else '　'} {t['theme']} (スコア:{t['score']}) - {t['reason']}")
        print(f"✅ 選択テーマ: {selected_theme}")

        # Step 2: 選ばれたテーマで記事生成
        print(f"✍️ 記事生成中: {selected_theme}...")
        article_response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": build_article_prompt(selected_theme, selected_reason, all_articles)
            }]
        )

        raw_text = article_response.content[0].text
        if "```json" in raw_text:
            json_str = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            json_str = raw_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw_text.strip()

        article_data = json.loads(json_str)
        article_data.update({
            "source_title": source_title,
            "source_url": source_url,
            "source_name": source_name,
            "generated_at": datetime.now().isoformat(),
            "status": "draft",
            "ai_model": "claude-haiku-4-5",
            "themes_considered": themes,
            "selected_theme": selected_theme
        })

        print(f"✅ 記事生成完了: {article_data.get('title', '')}")
        print(f"📝 タイトル案:")
        print(f"  1. {article_data.get('title', '')}")
        for i, alt in enumerate(article_data.get('title_alternatives', []), 2):
            print(f"  {i}. {alt}")

        return article_data

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析エラー: {e}")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def format_for_note(article_data: dict) -> str:
    """記事データをnote用テキストにフォーマット"""
    lines = [
        article_data.get("lead", ""), "",
        article_data.get("body", ""), "",
        "## まとめ", "",
        article_data.get("summary", ""), ""
    ]
    hashtags = article_data.get("hashtags", [])
    if hashtags:
        lines.append(" ".join([f"#{t}" if not t.startswith("#") else t for t in hashtags]))
    return "\n".join(lines)


def save_article(article_data: dict) -> Path:
    """記事をJSONファイルとして保存"""
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    filename = ARTICLES_DIR / f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    print(f"💾 記事保存: {filename}")
    return filename


def load_articles(status_filter=None):
    """保存済み記事を読み込む"""
    if not ARTICLES_DIR.exists():
        return []
    articles = []
    for fp in sorted(ARTICLES_DIR.glob("article_*.json"), reverse=True):
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_filepath"] = str(fp)
            if status_filter is None or data.get("status") == status_filter:
                articles.append(data)
    return articles


def update_article_status(filepath: str, status: str):
    """記事のステータスを更新"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["status"] = status
    data["updated_at"] = datetime.now().isoformat()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
