"""
記事生成モジュール
Claude APIを使って、AI初心者向けのツール活用記事を生成します
テーマ：Claude・ChatGPT・GeminiなどのAIツールの使い方・活用法
"""

import json
import os
import anthropic
from datetime import datetime
from pathlib import Path
import random

ARTICLES_DIR = Path("data/articles")

# AI初心者向けテーマリスト
BEGINNER_THEMES = [
    {"theme": "Claudeの使い方入門", "angle": "初めてClaudeを使う人向けの基本操作と便利な使い方"},
    {"theme": "ChatGPTで仕事を効率化する方法", "angle": "ビジネスシーンでChatGPTを活用する具体的な方法"},
    {"theme": "AIツールでブログ記事を書く方法", "angle": "AIを使って質の高いブログ記事を効率的に作成する方法"},
    {"theme": "Geminiの使い方と活用術", "angle": "GoogleのAI「Gemini」の基本から応用まで"},
    {"theme": "AIで副業を始める方法", "angle": "AIツールを使って副収入を得る具体的な方法"},
    {"theme": "ClaudeとChatGPTの違いと使い分け", "angle": "それぞれの特徴を理解して使い分ける方法"},
    {"theme": "AIプロンプトの書き方入門", "angle": "AIに伝わりやすい指示文の書き方と具体例"},
    {"theme": "AIで英語学習を効率化する方法", "angle": "AIツールを英語学習に活用する具体的な方法"},
    {"theme": "AIで資料作成を自動化する方法", "angle": "PowerPoint・Googleスライドの作成をAIで効率化"},
    {"theme": "AIツールの料金比較と選び方", "angle": "無料・有料プランの違いと自分に合ったAIの選び方"},
    {"theme": "Claudeで議事録を自動作成する方法", "angle": "会議の音声・テキストからAIで議事録を作る方法"},
    {"theme": "AIプロンプトで副業収入を得る方法", "angle": "プロンプトエンジニアリングを活用した収益化"},
    {"theme": "AIで動画台本を自動生成する方法", "angle": "YouTubeやSNS動画の台本をAIで効率的に作成"},
    {"theme": "AIチャットボットの作り方入門", "angle": "ノーコードでオリジナルAIチャットボットを作る方法"},
    {"theme": "Claudeを使った文章改善テクニック", "angle": "ビジネス文書・メール・ブログをAIで品質アップ"},
]


def select_theme(source_articles: list) -> dict:
    return random.choice(BEGINNER_THEMES)


def build_article_prompt(theme: str, angle: str, source_articles: list) -> str:
    news_text = "\n".join([f"・{a['title']}" for a in source_articles[:5]])

    return f"""あなたはnote向けのAI初心者向け解説記事を書く専門ライターです。

【記事テーマ】{theme}
【記事の切り口】{angle}
【参考トレンド情報】
{news_text}

以下の構成で、AI初心者でも実践できる解説記事を書いてください：

## 必須構成（この順番で書く）
1. **話題の概要**（このテーマが何かを一言で、なぜ今知るべきかを説明）
2. **なぜ注目されているか**（背景・社会的な変化・メリット）
3. **仕組みをやさしく説明**（技術的な話をたとえ話で分かりやすく）
4. **実際の使い方・ステップ**（初心者でもすぐ実践できる手順を具体的に）
5. **活用事例**（実際にどんな場面で使えるか、具体例3つ）
6. **注意点・デメリット**（リスクや気をつけること）

## 文体ルール
- 「です・ます調」で統一
- 専門用語には必ず（）で補足説明
- 煽りすぎず、分かりやすさ重視
- 読者への語りかけを適度に入れる
- 本文は2,000〜2,500文字
- 各見出しの下に必ず3文以上書く

必ず以下のJSON形式のみで返答してください（コードブロック不要）：
{{"title": "メインタイトル（30〜40文字、初心者向けと分かるもの）", "title_alternatives": ["タイトル案2（30〜40文字）", "タイトル案3（30〜40文字）"], "lead": "リード文（150〜200文字、初心者が読みたくなる内容）", "body": "本文（Markdown形式、## で6つの見出しを使って2000文字以上）", "summary": "まとめ（200〜300文字、読者への行動促進）", "hashtags": ["AI", "Claude", "ChatGPT", "AI活用", "初心者向け", "AIツール", "仕事効率化", "生成AI", "AI入門", "デジタル活用"], "estimated_read_time": 7, "theme": "{theme}"}}"""


def generate_article(source_title, source_summary, category, source_url, source_name, all_articles=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が設定されていません")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    if not all_articles:
        all_articles = [{"title": source_title, "source": source_name}]

    try:
        selected = select_theme(all_articles)
        theme = selected["theme"]
        angle = selected["angle"]

        print(f"📋 今回のテーマ: 【{theme}】")
        print(f"   切り口: {angle}")
        print(f"✍️ 初心者向け記事を生成中...")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": build_article_prompt(theme, angle, all_articles)}]
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
            "generated_at": datetime.now().isoformat(),
            "status": "draft",
            "ai_model": "claude-haiku-4-5",
            "selected_theme": theme
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
