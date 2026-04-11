"""
RSS収集モジュール
Claude・Geminiの使い方・テクニック・設定方法に特化した記事を収集します
"""

import feedparser
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

RSS_FEEDS = {
    "claude": [
        {"name": "note Claude", "url": "https://note.com/hashtag/Claude/rss"},
        {"name": "note Anthropic", "url": "https://note.com/hashtag/Anthropic/rss"},
        {"name": "note ClaudeAI", "url": "https://note.com/hashtag/ClaudeAI/rss"},
        {"name": "note Claude使い方", "url": "https://note.com/hashtag/Claude使い方/rss"},
    ],
    "gemini": [
        {"name": "note Gemini", "url": "https://note.com/hashtag/Gemini/rss"},
        {"name": "note GoogleGemini", "url": "https://note.com/hashtag/GoogleGemini/rss"},
        {"name": "note Gemini活用", "url": "https://note.com/hashtag/Gemini活用/rss"},
    ],
    "ai_tips": [
        {"name": "note AIプロンプト", "url": "https://note.com/hashtag/AIプロンプト/rss"},
        {"name": "note プロンプトエンジニアリング", "url": "https://note.com/hashtag/プロンプトエンジニアリング/rss"},
        {"name": "note AI活用", "url": "https://note.com/hashtag/AI活用/rss"},
        {"name": "note 生成AI活用", "url": "https://note.com/hashtag/生成AI活用/rss"},
        {"name": "note AIツール", "url": "https://note.com/hashtag/AIツール/rss"},
    ]
}

SCORE_KEYWORDS = {
    "high": [
        "Claude", "Anthropic", "Gemini", "Google Gemini",
        "使い方", "テクニック", "設定", "活用法", "プロンプト",
        "できること", "機能", "コツ", "方法", "ガイド",
        "初心者", "入門", "基本", "応用"
    ],
    "medium": [
        "生成AI", "LLM", "AIツール", "自動化",
        "効率化", "時短", "仕事術"
    ],
    "low": [
        "まとめ", "解説", "レビュー"
    ],
    "penalty": [
        "月20万", "月30万", "月50万", "稼ぎ方", "儲け",
        "副業で稼ぐ", "不労所得"
    ]
}

SEEN_ARTICLES_FILE = Path("data/seen_articles.json")


def load_seen_articles() -> set:
    if SEEN_ARTICLES_FILE.exists():
        with open(SEEN_ARTICLES_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_articles(seen: set):
    SEEN_ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)


def score_article(title: str, summary: str = "") -> int:
    score = 0
    text = f"{title} {summary}".lower()
    for keyword in SCORE_KEYWORDS["high"]:
        if keyword.lower() in text:
            score += 10
    for keyword in SCORE_KEYWORDS["medium"]:
        if keyword.lower() in text:
            score += 5
    for keyword in SCORE_KEYWORDS["low"]:
        if keyword.lower() in text:
            score += 2
    for keyword in SCORE_KEYWORDS["penalty"]:
        if keyword.lower() in text:
            score -= 10
    if 20 <= len(title) <= 60:
        score += 5
    return score


def clean_html(text: str) -> str:
    return re.sub(re.compile('<.*?>'), '', text)


def collect_articles(
    categories: list = ["claude", "gemini", "ai_tips"],
    max_age_hours: int = 504,
    limit: int = 20
) -> list:
    seen_articles = load_seen_articles()
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

    for category in categories:
        feeds = RSS_FEEDS.get(category, [])
        for feed_info in feeds:
            try:
                print(f"📡 収集中: {feed_info['name']}")
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries:
                    url = entry.get("link", "")
                    if not url or url in seen_articles:
                        continue
                    if "note.com" not in url:
                        continue
                    published = entry.get("published_parsed")
                    if published:
                        pub_dt = datetime(*published[:6])
                        if pub_dt < cutoff_time:
                            pass
                    title = entry.get("title", "").strip()
                    summary = clean_html(entry.get("summary", "")).strip()[:500]
                    if not title:
                        continue
                    score = score_article(title, summary)
                    articles.append({
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "category": category,
                        "source": feed_info["name"],
                        "score": score,
                        "published": str(entry.get("published", "")),
                        "collected_at": datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"⚠️ フィード取得エラー ({feed_info['name']}): {e}")
                continue

    articles.sort(key=lambda x: x["score"], reverse=True)

    seen_urls = set()
    unique_articles = []
    for a in articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique_articles.append(a)

    top_articles = unique_articles[:limit]
    print(f"\n✅ {len(top_articles)}件のnote記事を収集しました")
    return top_articles


def mark_as_processed(urls: list):
    seen = load_seen_articles()
    seen.update(urls)
    save_seen_articles(seen)