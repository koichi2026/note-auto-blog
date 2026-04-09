# note自動記事生成システム - プロジェクト概要

## システム概要
RSSからニュースを自動収集し、AIで記事を生成してnoteに下書き保存するシステム。

## 技術スタック
- **言語**: Python 3.12
- **UI**: Streamlit
- **AI**: Gemini API（gemini-2.0-flash-lite）→ 将来的にClaude APIへ移行予定
- **RSS収集**: feedparser
- **note保存**: Playwright（ブラウザ自動操作）
- **ホスティング**: Streamlit Cloud（無料）

## ユーザー情報
- **OS**: Windows
- **GitHubユーザー名**: koichi2026
- **noteメールアドレス**: koichi.yoshino.2023@gmail.com
- **記事ジャンル**: 技術・IT系、ビジネス・マーケティング
- **ネタ収集**: RSSから自動収集

## 重要なURL
- **アプリURL**: https://note-auto-blog-iylhcwf2cpassyscnhqb6z.streamlit.app
- **GitHub**: https://github.com/koichi2026/note-auto-blog
- **Streamlit Cloud**: https://share.streamlit.io
- **Gemini API**: https://aistudio.google.com/app/apikey
- **Claude API（予定）**: https://console.anthropic.com

## ローカル起動コマンド
```powershell
cd $env:USERPROFILE\Desktop\note-auto-blog
$env:GEMINI_API_KEY="APIキーをここに"
streamlit run app.py
```

## ディレクトリ構成
```
Desktop/note-auto-blog/
├── app.py                    # Streamlit管理UI
├── pipeline.py               # CLIパイプライン
├── requirements.txt          # 必要ライブラリ
├── .env.example              # 環境変数テンプレート
├── README.md                 # セットアップガイド
├── collectors/
│   ├── __init__.py
│   └── rss_collector.py      # RSS収集（11メディア対応）
├── generators/
│   ├── __init__.py
│   └── article_generator.py  # AI記事生成（Gemini API）
└── publishers/
    ├── __init__.py
    └── note_publisher.py     # note下書き保存（Playwright）
```

## Streamlit Cloud Secrets設定
```toml
GEMINI_API_KEY = "APIキー"
NOTE_EMAIL = "koichi.yoshino.2023@gmail.com"
NOTE_PASSWORD = "パスワード"
```

設定場所: share.streamlit.io → アプリの「⋮」→ Settings → Secrets

## 今後の移行予定
- Gemini API → Claude API（Haiku）に切り替え
- `article_generator.py` の `GEMINI_API_KEY` を `ANTHROPIC_API_KEY` に変更
- Claude APIキー取得先: console.anthropic.com
