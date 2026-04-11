"""
Streamlit管理画面
記事生成・プレビュー・note保存を操作できるWebUI
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを自動読み込み
load_dotenv(Path(__file__).parent / ".env")

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# ページ設定
st.set_page_config(
    page_title="note 自動記事生成",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    /* メインフォント */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
    }

    /* ヘッダー */
    .main-header {
        background: linear-gradient(135deg, #41b883 0%, #1a9962 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }

    /* カード */
    .article-card {
        background: #f8fffe;
        border: 1px solid #d4f0e8;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* ステータスバッジ */
    .badge-draft { background: #fff3cd; color: #856404; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; }
    .badge-saved { background: #d1f0e0; color: #155724; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; }

    /* ボタンスタイル */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* サイドバー */
    .css-1d391kg { background: #f0faf5; }

    /* タブ */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ========== セッション状態の初期化 ==========
if "generated_articles" not in st.session_state:
    st.session_state.generated_articles = []
if "rss_articles" not in st.session_state:
    st.session_state.rss_articles = []
if "current_article" not in st.session_state:
    st.session_state.current_article = None


# ========== サイドバー ==========
with st.sidebar:
    st.markdown("## ⚙️ 設定")

    st.markdown("### 🔑 API設定")
    gemini_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", "") or (st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""),
        type="password",
        help="Google Gemini APIキー（無料）"
    )

    st.markdown("### 📝 note設定")
    note_email = st.text_input(
        "noteメールアドレス",
        value=os.environ.get("NOTE_EMAIL", ""),
        help="noteアカウントのメールアドレス"
    )
    note_password = st.text_input(
        "noteパスワード",
        value=os.environ.get("NOTE_PASSWORD", ""),
        type="password",
        help="noteアカウントのパスワード"
    )

    st.markdown("### 📡 収集設定")
    categories = st.multiselect(
        "収集カテゴリ",
        ["tech", "business"],
        default=["tech", "business"],
        help="RSSから収集するカテゴリ"
    )
    max_articles = st.slider("生成記事数", 1, 10, 3)
    max_age_hours = st.slider("収集期間（時間）", 12, 168, 48)

    st.markdown("---")
    st.markdown("### 📊 統計")

    # 保存済み記事数を表示
    articles_dir = Path("data/articles")
    if articles_dir.exists():
        total = len(list(articles_dir.glob("article_*.json")))
        st.metric("保存済み記事", f"{total}件")
    else:
        st.metric("保存済み記事", "0件")


# ========== メインエリア ==========
st.markdown("""
<div class="main-header">
    <h1>✍️ note 自動記事生成システム</h1>
    <p>RSS収集 → AI記事生成 → note下書き保存を自動化</p>
</div>
""", unsafe_allow_html=True)

# タブ
tab1, tab2, tab3, tab4 = st.tabs(["🚀 記事を生成する", "📄 記事を管理する", "📤 noteに保存する", "📡 RSS確認"])


# ========== Tab 1: 記事生成 ==========
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Step 1: RSSからネタを収集")

        if st.button("📡 RSSを収集する", use_container_width=True, type="secondary"):
            if not gemini_key:
                st.error("Anthropic API Keyを設定してください")
            else:
                with st.spinner("RSSフィードを収集中..."):
                    os.environ["GEMINI_API_KEY"] = gemini_key
                    try:
                        from collectors.rss_collector import collect_articles
                        articles = collect_articles(
                            categories=["claude","gemini","ai_tips"],
                            max_age_hours=max_age_hours,
                            limit=max_articles * 5
                        )
                        st.session_state.rss_articles = articles
                        st.success(f"✅ {len(articles)}件の記事を収集しました")
                    except Exception as e:
                        st.error(f"収集エラー: {e}")

        # 収集した記事一覧
        if st.session_state.rss_articles:
            st.markdown(f"**収集記事: {len(st.session_state.rss_articles)}件**")
            for i, article in enumerate(st.session_state.rss_articles[:10]):
                score_color = "🔴" if article["score"] >= 20 else "🟡" if article["score"] >= 10 else "⚪"
                with st.expander(f"{score_color} [{article['source']}] {article['title'][:50]}..."):
                    st.write(f"**スコア:** {article['score']}")
                    st.write(f"**カテゴリ:** {article['category']}")
                    st.write(f"**要約:** {article.get('summary', '')[:200]}")
                    st.write(f"**URL:** {article['url']}")

    with col2:
        st.markdown("### Step 2: AIで記事を生成")

        generate_mode = st.radio(
            "生成モード",
            ["収集したRSSから自動生成", "手動でテーマを入力"],
            horizontal=True
        )

        if generate_mode == "手動でテーマを入力":
            manual_topic = st.text_input("記事のテーマ・トピック", placeholder="例: 生成AIがビジネスを変革する5つの理由")
            manual_category = st.selectbox("カテゴリ", ["tech", "business"])

        if st.button("✍️ 記事を生成する", use_container_width=True, type="primary"):
            if not gemini_key:
                st.error("Anthropic API Keyを設定してください")
            else:
                os.environ["GEMINI_API_KEY"] = gemini_key

                from generators.article_generator import generate_article, save_article
                from github_storage import save_article_to_github

                if generate_mode == "手動でテーマを入力":
                    source_list = [{
                        "title": manual_topic,
                        "summary": "",
                        "category": manual_category,
                        "url": "",
                        "source": "手動入力"
                    }]
                else:
                    if not st.session_state.rss_articles:
                        st.warning("先にRSSを収集してください")
                        st.stop()
                    source_list = st.session_state.rss_articles[:max_articles]

                progress = st.progress(0)
                status_text = st.empty()
                generated = []

                for i, source in enumerate(source_list[:max_articles]):
                    status_text.text(f"記事 {i+1}/{min(max_articles, len(source_list))} を生成中...")
                    progress.progress((i) / min(max_articles, len(source_list)))

                    article = generate_article(
                        source_title=source["title"],
                        source_summary=source.get("summary", ""),
                        category=source["category"],
                        source_url=source.get("url", ""),
                        source_name=source.get("source", "")
                    )

                    if article:
                        filepath = save_article(article)
                        save_article_to_github(article)
                        article["_filepath"] = str(filepath)
                        generated.append(article)
                        status_text.text(f"✅ 「{article.get('title', '')}」を生成しました")
                        time.sleep(1)

                progress.progress(1.0)
                st.session_state.generated_articles = generated
                st.success(f"🎉 {len(generated)}件の記事を生成しました！「記事を管理する」タブで確認できます")
                st.balloons()


# ========== Tab 2: 記事管理 ==========
with tab2:
    st.markdown("### 📄 生成済み記事一覧")

    # ファイルから記事を読み込む
   from generators.article_generator import load_articles
   from github_storage import load_articles_from_github

    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        status_filter = st.selectbox("ステータスフィルタ", ["すべて", "draft", "saved_to_note"])

    filter_map = {"すべて": None, "draft": "draft", "saved_to_note": "saved_to_note"}
    github_articles = load_articles_from_github()
    local_articles = load_articles(filter_map[status_filter])
    seen = set()
    saved_articles = []
    for a in github_articles + local_articles:
        key = a.get("title","") + a.get("generated_at","")
        if key not in seen:
            seen.add(key)
            saved_articles.append(a)

    if not saved_articles:
        st.info("まだ記事が生成されていません。「記事を生成する」タブから記事を作成してください。")
    else:
        st.markdown(f"**{len(saved_articles)}件の記事**")

        for article in saved_articles:
            status = article.get("status", "draft")
            status_badge = "🟢 note保存済み" if status == "saved_to_note" else "📝 下書き"
            generated_at = article.get("generated_at", "")[:16] if article.get("generated_at") else ""

            with st.expander(f"{status_badge} | {article.get('title', 'タイトル不明')} | {generated_at}"):
                col_a, col_b = st.columns([2, 1])

                with col_a:
                    # 編集可能なタイトル
                    st.markdown("**タイトル**")
                    new_title = st.text_input(
                        "タイトル",
                        value=article.get("title", ""),
                        key=f"title_{article['_filepath']}",
                        label_visibility="collapsed"
                    )

                    # タイトル候補
                    if article.get("title_alternatives"):
                        st.markdown("**タイトル候補**")
                        for alt in article["title_alternatives"]:
                            st.markdown(f"- {alt}")

                    # ハッシュタグ
                    st.markdown("**ハッシュタグ**")
                    hashtags = article.get("hashtags", [])
                    tag_display = " ".join([f"`#{t}`" for t in hashtags])
                    st.markdown(tag_display)

                    # 参照元
                    st.markdown(f"**参照元:** [{article.get('source_name', '')}]({article.get('source_url', '')})")

                with col_b:
                    st.markdown("**操作**")

                    # note本文プレビュー
                    if st.button("👁️ 本文プレビュー", key=f"preview_{article['_filepath']}"):
                        from generators.article_generator import format_for_note
                        formatted = format_for_note(article)
                        st.session_state.current_article = article
                        st.session_state.current_formatted = formatted

                    # クリップボードコピー
                    from generators.article_generator import format_for_note
                    formatted_text = format_for_note(article)
                    st.download_button(
                        "📋 テキストをDL",
                        data=formatted_text,
                        file_name=f"note_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key=f"dl_{article['_filepath']}"
                    )

                # 本文プレビュー
                if st.session_state.get("current_article") == article:
                    st.markdown("---")
                    st.markdown("**📄 note用フォーマット（プレビュー）**")
                    st.markdown(st.session_state.get("current_formatted", ""))


# ========== Tab 3: noteに保存 ==========
with tab3:
    st.markdown("### 📤 noteへの下書き保存")

    # 保存していない記事を取得
    pending_articles = load_articles(status_filter="draft")

    if not pending_articles:
        st.info("note保存待ちの記事がありません。記事を生成してください。")
    else:
        st.markdown(f"**保存待ち記事: {len(pending_articles)}件**")

        if not note_email or not note_password:
            st.warning("⚠️ サイドバーでnoteのメールアドレスとパスワードを設定してください")

        # 個別保存
        for article in pending_articles:
            col_info, col_action = st.columns([3, 1])

            with col_info:
                st.markdown(f"📝 **{article.get('title', 'タイトル不明')}**")
                st.caption(f"生成日時: {article.get('generated_at', '')[:16]}")

            with col_action:
                if st.button(
                    "📤 noteに保存",
                    key=f"pub_{article['_filepath']}",
                    disabled=not (note_email and note_password)
                ):
                    from generators.article_generator import format_for_note, update_article_status
                    from publishers.note_publisher import save_to_note_sync

                    with st.spinner("noteに保存中...（少々お待ちください）"):
                        body_text = format_for_note(article)
                        result = save_to_note_sync(
                            title=article.get("title", ""),
                            body_text=body_text,
                            hashtags=article.get("hashtags", []),
                            note_email=note_email,
                            note_password=note_password,
                            headless=False
                        )

                    if result.get("success"):
                        update_article_status(article["_filepath"], "saved_to_note")
                        st.success(f"✅ note下書き保存完了！")
                        st.rerun()
                    else:
                        st.error(f"❌ 保存失敗: {result.get('message')}")

        st.markdown("---")

        # 一括保存
        if len(pending_articles) > 1:
            if st.button(
                f"🚀 全{len(pending_articles)}件をまとめてnoteに保存",
                type="primary",
                disabled=not (note_email and note_password)
            ):
                from generators.article_generator import format_for_note, update_article_status
                from publishers.note_publisher import save_to_note_sync

                progress = st.progress(0)
                for i, article in enumerate(pending_articles):
                    st.write(f"保存中 ({i+1}/{len(pending_articles)}): {article.get('title', '')[:40]}")
                    body_text = format_for_note(article)
                    result = save_to_note_sync(
                        title=article.get("title", ""),
                        body_text=body_text,
                        hashtags=article.get("hashtags", []),
                        note_email=note_email,
                        note_password=note_password,
                        headless=False
                    )

                    if result.get("success"):
                        update_article_status(article["_filepath"], "saved_to_note")
                        st.success(f"✅ 「{article.get('title', '')}」保存完了")
                    else:
                        st.error(f"❌ 「{article.get('title', '')}」失敗: {result.get('message')}")

                    progress.progress((i + 1) / len(pending_articles))
                    time.sleep(3)  # レート制限対策

                st.balloons()
                st.rerun()


# ========== Tab 4: RSS確認 ==========
with tab4:
    st.markdown("### 📡 RSSフィード設定確認")

    from collectors.rss_collector import RSS_FEEDS

    for category, feeds in RSS_FEEDS.items():
        category_label = "🔧 技術・IT系" if category == "tech" else "💼 ビジネス・マーケティング"
        st.markdown(f"#### {category_label}")

        for feed in feeds:
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"**{feed['name']}**")
            with col2:
                st.code(feed['url'], language=None)

    st.markdown("---")
    st.markdown("### ➕ カスタムRSSを追加するには")
    st.markdown("`collectors/rss_collector.py` の `RSS_FEEDS` に追加してください。")
    st.code("""
RSS_FEEDS = {
    "tech": [
        # ... 既存のフィード
        {"name": "あなたのメディア名", "url": "https://example.com/rss.xml"},
    ]
}
""", language="python")
