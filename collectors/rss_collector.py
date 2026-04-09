"""
RSS収集モジュール
技術・IT系、ビジネス・マーケティング系のRSSフィードを収集し、スコアリングします
"""

import feedparser
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import re

# RSS フィード設定
RSS_FEEDS = {
    "tech": [
        {"name": "TechCrunch Japan", "url": "https://jp.techcrunch.com/feed/"},
        {"name": "GIGAZINE", "url": "https://gigazine.net/news/rss_2.0/"},
        {"name": "はてなブックマーク テクノロジー", "url": "https://b.hatena.ne.jp/hotentry/it.rss"},
        {"name": "Zenn トレンド", "url": "https://zenn.dev/feed"},
        {"name": "ITmedia NEWS", "url": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"},
        {"name": "ASCII.jp", "url": "https://ascii.jp/rss.xml"},
    ],
    "business": [
        {"name": "MarkeZine", "url": "https://markezine.jp/rss/index.rdf"},
        {"name": "ITmedia ビジネス", "url": "https://rss.itmedia.co.jp/rss/2.0/bizid.xml"},
        {"name": "東洋経済オンライン", "url": "https://toyokeizai.net/list/feed/rss"},
        {"name": "ダイヤモンドオンライン", "url": "https://diamond.jp/list/feed/rss"},
        {"name": "日経xTECH", "url": "https://xtech.nikkei.com/rss/index.rdf"},
    ]
}

# スコアリング用キーワード
SCORE_KEYWORDS = {
    "high": [
        "AI", "人工知能", "ChatGPT", "Claude", "LLM", "生成AI",
        "DX", "デジタル変革", "スタートアップ", "資金調達",
        "マーケティング", "SNS", "X（Twitter）", "Instagram",
        "セキュリティ", "サイバー", "クラウド", "AWS", "Google",
        "iPhone", "Android", "アップデート", "新機能",
        "副業", "フリーランス", "リモートワーク", "働き方"
    ],
    "medium": [
        "技術", "開発", "エンジニア", "プログラミング",
        "ビジネス", "経営", "戦略", "売上", "成長",
        "トレンド", "最新", "2024", "2025", "注目"
    ],
    "low": [
        "まとめ", "解説", "入門", "基礎", "ガイド"
    ]
}

SEEN_ARTICLES_FILE = Path("data/seen_articles.json")


def load_seen_articles() -> set:
    """既に処理済みの記事URLを読み込む"""
    if SEEN_ARTICLES_FILE.exists():
        with open(SEEN_ARTICLES_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_articles(seen: set):
    """処理済み記事URLを保存する"""
    SEEN_ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)


def score_article(title: str, summary: str = "") -> int:
    """記事のスコアを計算する（高いほど優先度が高い）"""
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

    # タイトルの長さボーナス（短すぎず長すぎない記事を優先）
    title_len = len(title)
    if 20 <= title_len <= 60:
        score += 5

    return score


def clean_html(text: str) -> str:
    """HTMLタグを除去する"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def collect_articles(
    categories: list = ["tech", "business"],
    max_age_hours: int = 48,
    limit: int = 20
) -> list[dict]:
    """
    RSSフィードから記事を収集する

    Args:
        categories: 収集するカテゴリリスト
        max_age_hours: 何時間以内の記事を収集するか
        limit: 最大収集件数

    Returns:
        スコアでソートされた記事リスト
    """
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

                    # 公開日時チェック
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

    # スコア降順でソート
    articles.sort(key=lambda x: x["score"], reverse=True)

    # 上位N件を返す
    top_articles = articles[:limit]

    print(f"\n✅ {len(top_articles)}件の記事を収集しました")
    return top_articles


def mark_as_processed(urls: list[str]):
    """記事を処理済みとしてマークする"""
    seen = load_seen_articles()
    seen.update(urls)
    save_seen_articles(seen)


if __name__ == "__main__":
    articles = collect_articles()
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. [{article['source']}] {article['title']}")
        print(f"   スコア: {article['score']} | カテゴリ: {article['category']}")
        print(f"   URL: {article['url']}")
