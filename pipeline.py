"""
メインパイプライン
RSS収集 → 記事生成 → note下書き保存 を一括実行します
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

from collectors.rss_collector import collect_articles, mark_as_processed
from generators.article_generator import (
    generate_article, save_article, format_for_note,
    load_articles, update_article_status
)
from publishers.note_publisher import save_to_note_sync


def run_pipeline(
    max_articles: int = 3,
    auto_publish_to_note: bool = False,
    note_email: str = "",
    note_password: str = "",
    categories: list = ["tech", "business"]
) -> list[dict]:
    """
    メインパイプラインを実行する

    Args:
        max_articles: 生成する記事数
        auto_publish_to_note: noteに自動で下書き保存するか
        note_email: noteのメールアドレス
        note_password: noteのパスワード
        categories: 収集するカテゴリ

    Returns:
        生成された記事リスト
    """
    print("\n" + "="*60)
    print(f"🚀 パイプライン開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = []

    # ① RSS収集
    print("\n📡 Step 1: RSS記事を収集中...")
    articles = collect_articles(categories=categories, limit=max_articles * 5)

    if not articles:
        print("⚠️ 収集できた記事がありません")
        return []

    print(f"✅ {len(articles)}件の候補記事を収集")

    # ② 記事生成
    print(f"\n✍️ Step 2: Claude APIで記事を生成中（最大{max_articles}件）...")
    generated_count = 0
    processed_urls = []

    for source_article in articles:
        if generated_count >= max_articles:
            break

        print(f"\n--- 記事 {generated_count + 1}/{max_articles} ---")

        article_data = generate_article(
            source_title=source_article["title"],
            source_summary=source_article.get("summary", ""),
            category=source_article["category"],
            source_url=source_article["url"],
            source_name=source_article["source"]
        )

        if not article_data:
            print("⚠️ 記事生成失敗、次の候補へ")
            continue

        # 記事を保存
        filepath = save_article(article_data)
        article_data["_filepath"] = str(filepath)
        processed_urls.append(source_article["url"])

        # ③ note下書き保存
        if auto_publish_to_note and note_email and note_password:
            print(f"\n📤 Step 3: noteに下書き保存中...")
            body_text = format_for_note(article_data)

            publish_result = save_to_note_sync(
                title=article_data.get("title", ""),
                body_text=body_text,
                hashtags=article_data.get("hashtags", []),
                note_email=note_email,
                note_password=note_password,
                headless=True
            )

            article_data["note_publish_result"] = publish_result

            if publish_result.get("success"):
                update_article_status(str(filepath), "saved_to_note")
                print(f"✅ note下書き保存成功")
            else:
                print(f"⚠️ note保存失敗: {publish_result.get('message')}")

            # レート制限対策
            time.sleep(5)

        results.append(article_data)
        generated_count += 1

    # 処理済みURLをマーク
    if processed_urls:
        mark_as_processed(processed_urls)

    # サマリー
    print("\n" + "="*60)
    print(f"🎉 パイプライン完了!")
    print(f"   生成記事数: {len(results)}件")
    if auto_publish_to_note:
        success_count = sum(1 for r in results if r.get("note_publish_result", {}).get("success"))
        print(f"   note保存成功: {success_count}件")
    print("="*60 + "\n")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="note自動記事生成パイプライン")
    parser.add_argument("--max-articles", type=int, default=2, help="生成する記事数（デフォルト: 2）")
    parser.add_argument("--publish", action="store_true", help="noteに自動で下書き保存する")
    parser.add_argument("--categories", nargs="+", default=["tech", "business"], help="収集カテゴリ")
    parser.add_argument("--no-headless", action="store_true", help="ブラウザを表示して実行（デバッグ用）")

    args = parser.parse_args()

    note_email = os.environ.get("NOTE_EMAIL", "")
    note_password = os.environ.get("NOTE_PASSWORD", "")

    if args.publish and (not note_email or not note_password):
        print("⚠️ NOTE_EMAIL と NOTE_PASSWORD の環境変数を設定してください")
        sys.exit(1)

    run_pipeline(
        max_articles=args.max_articles,
        auto_publish_to_note=args.publish,
        note_email=note_email,
        note_password=note_password,
        categories=args.categories
    )
