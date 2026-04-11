"""
RSS収集モジュール
note.comの記事のみを収集します
"""

import feedparser
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

RSS_FEEDS = {
    "tech": [
        {"name": "note AI", "url": "https://note.com/hashtag/AI/rss"},
        {"name": "note ChatGPT", "url": "https://note.com/hashtag/ChatGPT/rss"},
        {"name": "note Claude", "url": "https://note.com/hashtag/Claude/rss"},
        {"name": "note 生成AI", "url": "https://note.com/hashtag/生成AI/rss"},
        {"name": "note AIツール", "url": "https://note.com/hashtag/AIツール/rss"},
        {"name": "note AI活用", "url": "https://note.com/hashtag/AI活用/rss"},
        {"name": "note プロンプト", "url": "https://note.com/hashtag/プロンプト/rss"},
        {"name": "note Anthropic", "url": "https://note.com/hashtag/Anthropic/rss"},
        {"name": "note ClaudeAI", "url": "https://note.com/hashtag/ClaudeAI/rss"},
    ],
    "business": [
        {"name": "note AI副業", "url": "https://note.com/hashtag/AI副業/rss"},
        {"name": "note 副業", "url": "https://note.com/hashtag/副業/rss"},
        {"name": "note 仕事効率化", "url": "https://note.com/hashtag/仕事効率化/rss"},
        {"name": "note ChatGPT活用", "url": "https://note.com/hashtag/ChatGPT活用/rss"},
        {"name": "note AIで稼ぐ", "url": "https://note.com/hashtag/AIで稼ぐ/rss"},
    ]
}

SCORE_KEYWORDS = {
    "high": [
        "Claude", "ChatGPT", "Gemini", "生成AI", "LLM", "プロンプト",
        "AI活用", "AI副業", "AIで稼ぐ", "自動化", "効率化",
        "使い方", "入門", "初心者", "活用法", "ツール"
    ],
    "medium": [
        "人工知能", "機械学習", "副業", "仕事術", "時短",
        "ノーコード", "収益化", "フリーランス"
    ],
    "low": [
        "まとめ", "解説", "ガイド", "レビュー"
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
    if 20 <= len(title) <= 60:
        score += 5
    return score


def clean_html(text: str) -> str:
    return re.sub(re.compile('<.*?>'), '', text)


def collect_articles(
    categories: list = ["tech", "business"],
    max_age_hours: int = 24,
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
                    # note.comの記事のみ
                    if "note.com" not in url:
                        continue
                    published = entry.get("published_parsed")
                    if published:
                        pub_dt = datetime(*published[:6])
                        if pub_dt < cutoff_time:
                            continue
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
    # 重複URLを除去
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