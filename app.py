"""
Streamlit管琁E��面
記事生成�Eプレビュー・note保存を操作できるWebUI
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを�E動読み込み
load_dotenv(Path(__file__).parent / ".env")

# パス設宁E
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# ペ�Eジ設宁E
st.set_page_config(
    page_title="note 自動記事生戁E,
    page_icon="✍︁E,
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    /* メインフォンチE*/
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

    /* カーチE*/
    .article-card {
        background: #f8fffe;
        border: 1px solid #d4f0e8;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* スチE�Eタスバッジ */
    .badge-draft { background: #fff3cd; color: #856404; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; }
    .badge-saved { background: #d1f0e0; color: #155724; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; }

    /* ボタンスタイル */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* サイドバー */
    .css-1d391kg { background: #f0faf5; }

    /* タチE*/
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ========== セチE��ョン状態�E初期匁E==========
if "generated_articles" not in st.session_state:
    st.session_state.generated_articles = []
if "rss_articles" not in st.session_state:
    st.session_state.rss_articles = []
if "current_article" not in st.session_state:
    st.session_state.current_article = None


# ========== サイドバー ==========
with st.sidebar:
    st.markdown("## ⚙︁E設宁E)

    st.markdown("### 🔑 API設宁E)
    gemini_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", "") or (st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""),
        type="password",
        help="Google Gemini APIキー�E�無料！E
    )

    st.markdown("### 📝 note設宁E)
    note_email = st.text_input(
        "noteメールアドレス",
        value=os.environ.get("NOTE_EMAIL", ""),
        help="noteアカウント�Eメールアドレス"
    )
    note_password = st.text_input(
        "noteパスワーチE,
        value=os.environ.get("NOTE_PASSWORD", ""),
        type="password",
        help="noteアカウント�EパスワーチE
    )

    st.markdown("### 📡 収集設宁E)
    categories = st.multiselect(
        "収集カチE��リ",
        ["tech", "business"],
        default=["tech", "business"],
        help="RSSから収集するカチE��リ"
    )
    max_articles = st.slider("生�E記事数", 1, 10, 3)
    max_age_hours = st.slider("収集期間�E�時間！E, 12, 168, 48)

    st.markdown("---")
    st.markdown("### 📊 統訁E)

    # 保存済み記事数を表示
    articles_dir = Path("data/articles")
    if articles_dir.exists():
        total = len(list(articles_dir.glob("article_*.json")))
        st.metric("保存済み記亁E, f"{total}件")
    else:
        st.metric("保存済み記亁E, "0件")


# ========== メインエリア ==========
st.markdown("""
<div class="main-header">
    <h1>✍︁Enote 自動記事生成シスチE��</h1>
    <p>RSS収集 ↁEAI記事生戁EↁEnote下書き保存を自動化</p>
</div>
""", unsafe_allow_html=True)

# タチE
tab1, tab2, tab3, tab4 = st.tabs(["🚀 記事を生�Eする", "📄 記事を管琁E��めE, "📤 noteに保存すめE, "📡 RSS確誁E])


# ========== Tab 1: 記事生戁E==========
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Step 1: RSSからネタを収雁E)

        if st.button("📡 RSSを収雁E��めE, use_container_width=True, type="secondary"):
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
                        st.success(f"✁E{len(articles)}件の記事を収集しました")
                    except Exception as e:
                        st.error(f"収集エラー: {e}")

        # 収集した記事一覧
        if st.session_state.rss_articles:
            st.markdown(f"**収集記亁E {len(st.session_state.rss_articles)}件**")
            for i, article in enumerate(st.session_state.rss_articles[:10]):
                score_color = "🔴" if article["score"] >= 20 else "🟡" if article["score"] >= 10 else "⚪"
                with st.expander(f"{score_color} [{article['source']}] {article['title'][:50]}..."):
                    st.write(f"**スコア:** {article['score']}")
                    st.write(f"**カチE��リ:** {article['category']}")
                    st.write(f"**要紁E** {article.get('summary', '')[:200]}")
                    st.write(f"**URL:** {article['url']}")

    with col2:
        st.markdown("### Step 2: AIで記事を生�E")

        generate_mode = st.radio(
            "生�EモーチE,
            ["収集したRSSから自動生戁E, "手動でチE�Eマを入劁E],
            horizontal=True
        )

        if generate_mode == "手動でチE�Eマを入劁E:
            manual_topic = st.text_input("記事�EチE�Eマ�EトピチE��", placeholder="侁E 生�EAIがビジネスを変革する5つの琁E��")
            manual_category = st.selectbox("カチE��リ", ["tech", "business"])

        if st.button("✍︁E記事を生�Eする", use_container_width=True, type="primary"):
            if not gemini_key:
                st.error("Anthropic API Keyを設定してください")
            else:
                os.environ["GEMINI_API_KEY"] = gemini_key

                from generators.article_generator import generate_article, save_article
                from github_storage import save_article_to_github

                if generate_mode == "手動でチE�Eマを入劁E:
                    source_list = [{
                        "title": manual_topic,
                        "summary": "",
                        "category": manual_category,
                        "url": "",
                        "source": "手動入劁E
                    }]
                else:
                    if not st.session_state.rss_articles:
                        st.warning("先にRSSを収雁E��てください")
                        st.stop()
                    source_list = st.session_state.rss_articles[:max_articles]

                progress = st.progress(0)
                status_text = st.empty()
                generated = []

                for i, source in enumerate(source_list[:max_articles]):
                    status_text.text(f"記亁E{i+1}/{min(max_articles, len(source_list))} を生成中...")
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
                        status_text.text(f"✁E「{article.get('title', '')}」を生�Eしました")
                        time.sleep(1)

                progress.progress(1.0)
                st.session_state.generated_articles = generated
                st.success(f"🎉 {len(generated)}件の記事を生�Eしました�E�「記事を管琁E��る」タブで確認できまぁE)
                st.balloons()


# ========== Tab 2: 記事管琁E==========
with tab2:
    st.markdown("### 📄 生�E済み記事一覧")

    # ファイルから記事を読み込む
    from generators.article_generator import load_articles
    from github_storage import load_articles_from_github

    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        status_filter = st.selectbox("スチE�Eタスフィルタ", ["すべて", "draft", "saved_to_note"])

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
        st.info("まだ記事が生�EされてぁE��せん。「記事を生�Eする」タブから記事を作�Eしてください、E)
    else:
        st.markdown(f"**{len(saved_articles)}件の記亁E*")

        for article in saved_articles:
            status = article.get("status", "draft")
            status_badge = "🟢 note保存済み" if status == "saved_to_note" else "📝 下書ぁE
            generated_at = article.get("generated_at", "")[:16] if article.get("generated_at") else ""

            with st.expander(f"{status_badge} | {article.get('title', 'タイトル不�E')} | {generated_at}"):
                col_a, col_b = st.columns([2, 1])

                with col_a:
                    # 編雁E��能なタイトル
                    st.markdown("**タイトル**")
                    new_title = st.text_input(
                        "タイトル",
                        value=article.get("title", ""),
                        key=f"title_{article['_filepath']}",
                        label_visibility="collapsed"
                    )

                    # タイトル候裁E
                    if article.get("title_alternatives"):
                        st.markdown("**タイトル候裁E*")
                        for alt in article["title_alternatives"]:
                            st.markdown(f"- {alt}")

                    # ハッシュタグ
                    st.markdown("**ハッシュタグ**")
                    hashtags = article.get("hashtags", [])
                    tag_display = " ".join([f"`#{t}`" for t in hashtags])
                    st.markdown(tag_display)

                    # 参�E允E
                    st.markdown(f"**参�E允E** [{article.get('source_name', '')}]({article.get('source_url', '')})")

                with col_b:
                    st.markdown("**操佁E*")

                    # note本斁E�Eレビュー
                    if st.button("👁�E�E本斁E�Eレビュー", key=f"preview_{article['_filepath']}"):
                        from generators.article_generator import format_for_note
                        formatted = format_for_note(article)
                        st.session_state.current_article = article
                        st.session_state.current_formatted = formatted

                    # クリチE�Eボ�Eドコピ�E
                    from generators.article_generator import format_for_note
                    formatted_text = format_for_note(article)
                    st.download_button(
                        "📋 チE��ストをDL",
                        data=formatted_text,
                        file_name=f"note_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key=f"dl_{article['_filepath']}"
                    )

                # 本斁E�Eレビュー
                if st.session_state.get("current_article") == article:
                    st.markdown("---")
                    st.markdown("**📄 note用フォーマット（�Eレビュー�E�E*")
                    st.markdown(st.session_state.get("current_formatted", ""))


# ========== Tab 3: noteに保孁E==========
with tab3:
    st.markdown("### 📤 noteへの下書き保孁E)

    # 保存してぁE��ぁE��事を取征E
    pending_articles = load_articles(status_filter="draft")

    if not pending_articles:
        st.info("note保存征E��の記事がありません。記事を生�Eしてください、E)
    else:
        st.markdown(f"**保存征E��記亁E {len(pending_articles)}件**")

        if not note_email or not note_password:
            st.warning("⚠�E�Eサイドバーでnoteのメールアドレスとパスワードを設定してください")

        # 個別保孁E
        for article in pending_articles:
            col_info, col_action = st.columns([3, 1])

            with col_info:
                st.markdown(f"📝 **{article.get('title', 'タイトル不�E')}**")
                st.caption(f"生�E日晁E {article.get('generated_at', '')[:16]}")

            with col_action:
                if st.button(
                    "📤 noteに保孁E,
                    key=f"pub_{article['_filepath']}",
                    disabled=not (note_email and note_password)
                ):
                    from generators.article_generator import format_for_note, update_article_status
                    from publishers.note_publisher import save_to_note_sync

                    with st.spinner("noteに保存中...�E�少、E��征E��ください�E�E):
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
                        st.success(f"✁Enote下書き保存完亁E��E)
                        st.rerun()
                    else:
                        st.error(f"❁E保存失敁E {result.get('message')}")

        st.markdown("---")

        # 一括保孁E
        if len(pending_articles) > 1:
            if st.button(
                f"🚀 全{len(pending_articles)}件をまとめてnoteに保孁E,
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
                        st.success(f"✁E「{article.get('title', '')}」保存完亁E)
                    else:
                        st.error(f"❁E「{article.get('title', '')}」失敁E {result.get('message')}")

                    progress.progress((i + 1) / len(pending_articles))
                    time.sleep(3)  # レート制限対筁E

                st.balloons()
                st.rerun()


# ========== Tab 4: RSS確誁E==========
with tab4:
    st.markdown("### 📡 RSSフィード設定確誁E)

    from collectors.rss_collector import RSS_FEEDS

    for category, feeds in RSS_FEEDS.items():
        category_label = "🔧 技術�EIT系" if category == "tech" else "💼 ビジネス・マ�EケチE��ング"
        st.markdown(f"#### {category_label}")

        for feed in feeds:
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"**{feed['name']}**")
            with col2:
                st.code(feed['url'], language=None)

    st.markdown("---")
    st.markdown("### ➁EカスタムRSSを追加するには")
    st.markdown("`collectors/rss_collector.py` の `RSS_FEEDS` に追加してください、E)
    st.code("""
RSS_FEEDS = {
    "tech": [
        # ... 既存�EフィーチE
        {"name": "あなた�EメチE��ア吁E, "url": "https://example.com/rss.xml"},
    ]
}
""", language="python")

