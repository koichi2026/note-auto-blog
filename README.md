# note 自動記事生成システム — セットアップガイド

## 📁 ディレクトリ構成

```
note-auto-blog/
├── app.py                        # Streamlit 管理UI（メイン画面）
├── pipeline.py                   # CLI実行用パイプライン
├── requirements.txt              # 必要ライブラリ
├── .env.example                  # 環境変数テンプレート
├── .env                          # ← 自分で作成（gitに入れない）
│
├── collectors/
│   └── rss_collector.py          # RSSフィード収集
│
├── generators/
│   └── article_generator.py      # Claude API 記事生成
│
├── publishers/
│   └── note_publisher.py         # Playwright note下書き保存
│
└── data/                         # ← 自動生成されます
    ├── articles/                 # 生成済み記事JSON
    ├── sessions/                 # noteのログインセッション
    └── seen_articles.json        # 処理済みURL管理
```

---

## 🚀 セットアップ手順

### 1. Python環境の準備（Python 3.10以上推奨）

```bash
# 仮想環境を作成（推奨）
python -m venv venv

# 仮想環境を有効化
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. ライブラリのインストール

```bash
pip install -r requirements.txt

# Playwrightのブラウザをインストール（Chromium）
playwright install chromium
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成してください：

```bash
cp .env.example .env
```

`.env` を編集して以下を入力：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxx   ← https://console.anthropic.com/ で取得
NOTE_EMAIL=your@email.com             ← noteのメールアドレス
NOTE_PASSWORD=your_password           ← noteのパスワード
```

> ⚠️ `.env` は絶対にGitHubなどに公開しないでください

---

## 💻 使い方

### A. Streamlit管理UIを使う（推奨）

```bash
streamlit run app.py
```

ブラウザが開き、以下の操作ができます：

| タブ | 機能 |
|------|------|
| 🚀 記事を生成する | RSS収集 → AI記事生成 |
| 📄 記事を管理する | 生成記事の確認・プレビュー・DL |
| 📤 noteに保存する | note下書き保存（Playwright） |
| 📡 RSS確認 | 収集先フィードの確認・管理 |

### B. コマンドラインから実行する

```bash
# 環境変数を読み込んで実行
source .env  # または set -a && . .env && set +a

# 記事生成のみ（note保存なし）
python pipeline.py --max-articles 3

# 記事生成 + note下書き保存
python pipeline.py --max-articles 3 --publish

# テックカテゴリのみ
python pipeline.py --categories tech --max-articles 2

# ブラウザを表示してデバッグ
python pipeline.py --publish --no-headless
```

---

## ⏰ 定期自動実行（スケジューラ）

### cron を使う場合（Mac/Linux）

```bash
# crontab を編集
crontab -e

# 毎朝8時に実行（例）
0 8 * * * cd /path/to/note-auto-blog && source venv/bin/activate && python pipeline.py --max-articles 3 --publish >> data/cron.log 2>&1
```

### Windows タスクスケジューラの場合

1. タスクスケジューラを開く
2. 「基本タスクの作成」
3. `python C:\path\to\note-auto-blog\pipeline.py --max-articles 3 --publish`

---

## 🔧 カスタマイズ

### RSSフィードを追加する

`collectors/rss_collector.py` の `RSS_FEEDS` に追加：

```python
RSS_FEEDS = {
    "tech": [
        # 既存のフィード...
        {"name": "あなたのメディア", "url": "https://your-media.com/rss"},
    ],
    "business": [
        # ...
    ]
}
```

### スコアリングキーワードを調整する

```python
SCORE_KEYWORDS = {
    "high": ["AI", "ChatGPT", ...],   # スコア +10
    "medium": ["技術", "ビジネス", ...], # スコア +5
}
```

### 生成される記事のプロンプトを変更する

`generators/article_generator.py` の `build_system_prompt()` を編集してください。
文体・文字数・構成などを細かく調整できます。

---

## ❓ トラブルシューティング

### note下書き保存が失敗する場合

1. **ブラウザを表示して確認する**
   ```bash
   python pipeline.py --publish --no-headless
   ```

2. **セッションをリセットする**
   ```bash
   rm -rf data/sessions/
   ```

3. **noteのUIが変わっている可能性**
   Playwrightのセレクタが古くなっている場合があります。
   `publishers/note_publisher.py` の各セレクタリストを更新してください。

### RSSが収集できない場合

- フィードURLが変わっている可能性があります
- `collectors/rss_collector.py` のURLを最新のものに更新してください

### Claude APIエラーが出る場合

- `ANTHROPIC_API_KEY` が正しく設定されているか確認
- APIの利用制限に達していないか確認（https://console.anthropic.com/）

---

## 📌 運用のポイント

1. **最初はブラウザ表示モード（`--no-headless`）で動作確認** する
2. **`data/` ディレクトリはGitに含めない**（.gitignoreに追加）
3. **定期実行前に手動で数回テスト**して品質を確認する
4. **生成記事は必ず人間が最終確認**してから投稿する
5. noteのUI変更に備えて**定期的にスクリプトをテスト**する
