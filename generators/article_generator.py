"""
記事生成モジュール
Claude APIを使って、収集したnote記事を参考に初心者向け解説記事を生成します
"""

import json
import os
import anthropic
from datetime import datetime, timezone, timedelta
JST = timezone(timedelta(hours=9))
from pathlib import Path
import random

ARTICLES_DIR = Path("data/articles")


def build_article_prompt(source_articles: list) -> str:
    """収集したnote記事を参考に初心者向け記事を生成するプロンプト"""

    # 参考記事の情報を整理
    articles_info = "\n\n".join([
        f"【参考記事{i+1}】\nタイトル: {a['title']}\n要約: {a.get('summary', '')[:200]}\nURL: {a['url']}"
        for i, a in enumerate(source_articles[:5])
    ])

    return f"""あなたはnote向けのAI初心者向け解説記事を書く専門ライターです。

以下のnote.comの記事を参考にして、新しい初心者向け記事を書いてください。

【参考にしたnote記事】
{articles_info}

【重要なルール】
- 参考記事の表現・言葉・文章を絶対にそのまま使わないこと
- 参考記事のアイデアや情報を元に、完全に独自の言葉で書き直すこと
- AIを初めて使う初心者でも理解できる内容にすること
- 専門用語には必ず（）でかんたんな補足をつけること

【必須構成（この順番で書く）】
## 1. はじめに（このテーマが初心者に必要な理由）
## 2. そもそも〇〇って何？（やさしい説明・たとえ話を使う）
## 3. なぜ今注目されているの？（背景・メリット）
## 4. 実際の使い方（初心者でもすぐできる手順を具体的に）
## 5. こんな場面で使える！（活用事例を3つ）
## 6. 注意点・気をつけること

【文体ルール】
- 「です・ます調」で統一
- 煽りすぎず、分かりやすさ重視
- 読者への語りかけを適度に入れる（「〜ではないでしょうか」「ぜひ試してみてください」など）
- 本文は2,000〜2,500文字
- 各見出しの下に必ず3文以上書く
- 年号（2024年・2023年など）は使わず「最近」「現在」「今」などの表現を使う

必ず以下のJSON形式のみで返答してください（コードブロック不要）：
{{"title": "メインタイトル（30〜40文字、初心者向けと分かるもの）", "title_alternatives": ["タイトル案2（30〜40文字）", "タイトル案3（30〜40文字）"], "lead": "リード文（150〜200文字、初心者が読みたくなる内容）", "body": "本文（Markdown形式、## で6つの見出しを使って2000文字以上）", "summary": "まとめ（200〜300文字、読者への行動促進）", "hashtags": ["AI", "Claude", "ChatGPT", "AI活用", "初心者向け", "AIツール", "仕事効率化", "生成AI", "AI入門", "デジタル活用"], "estimated_read_time": 7}}"""


def generate_article(source_title, source_summary, category, source_url, source_name, all_articles=None):
    """Claude APIを使って初心者向けAI活用記事を生成する"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が設定されていません")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    if not all_articles:
        all_articles = [{"title": source_title, "source": source_name, "url": source_url, "summary": source_summary}]

    try:
        print(f"📚 参考にするnote記事:")
        for i, a in enumerate(all_articles[:5], 1):
            print(f"  {i}. {a['title'][:40]}")

        print(f"✍️ 初心者向け記事を生成中...")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": build_article_prompt(all_articles)
            }]
        )

        raw_text = response.content[0].text
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
            "generated_at": datetime.now(JST).isoformat(),
            "status": "draft",
            "ai_model": "claude-haiku-4-5",
            "reference_articles": [a["title"] for a in all_articles[:5]]
        })

        print(f"✅ 記事生成完了!")
        print(f"📝 タイトル1: {article_data.get('title', '')}")
        for i, alt in enumerate(article_data.get('title_alternatives', []), 2):
            print(f"📝 タイトル{i}: {alt}")

        return article_data

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析エラー: {e}")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def format_for_note(article_data: dict) -> str:
    lines = [article_data.get("lead", ""), "", article_data.get("body", ""), "", "## まとめ", "", article_data.get("summary", ""), ""]
    hashtags = article_data.get("hashtags", [])
    if hashtags:
        lines.append(" ".join([f"#{t}" if not t.startswith("#") else t for t in hashtags]))
    return "\n".join(lines)


def save_article(article_data: dict) -> Path:
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    filename = ARTICLES_DIR / f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    print(f"💾 記事保存: {filename}")
    return filename


def load_articles(status_filter=None):
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
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["status"] = status
    data["updated_at"] = datetime.now().isoformat()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
