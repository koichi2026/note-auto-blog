# AIでnoteブログ記事を自動生成！初心者でもできる完全ガイド

## はじめに

「毎日ブログを更新したいけど、ネタ探しや文章作成が大変…」
「AIを使って効率よく記事を作りたいけど、どこから始めればいいの？」

そんな悩みを持つ方に向けて、この記事ではAIを使ったnoteブログ記事の自動生成システムの作り方を、ゼロから丁寧に解説します。

プログラミング経験がない方でも、この記事の手順通りに進めれば、以下のことが自動でできるようになります。

- note.comの最新AI記事を自動収集
- ClaudeのAIが初心者向け解説記事を自動生成
- noteの下書きに自動保存（投稿は手動）
- スマホからでも操作できるWebアプリ

では、さっそく始めましょう！

---

## 第1章：システムの全体像を理解しよう

### このシステムで何ができるの？

このシステムは大きく3つのステップで動きます。

```
①RSS収集
note.comの最新AI記事を自動で集める
     ↓
②AI記事生成
Claude AIが初心者向け解説記事を自動で書く
     ↓
③note下書き保存
書いた記事をnoteに自動で下書き保存する
```

### 使う主なツール

| ツール | 役割 | 料金 |
|--------|------|------|
| Python | プログラムを動かす土台 | 無料 |
| Streamlit | 操作画面（WebアプリUI） | 無料 |
| Claude API | AI記事生成エンジン | 従量課金（記事1本約0.5円） |
| Playwright | noteへの自動保存 | 無料 |
| GitHub | ファイル管理・バックアップ | 無料 |
| Streamlit Cloud | スマホからアクセス用 | 無料 |

---

## 第2章：準備するもの

### 必要なアカウント

以下のアカウントを事前に作成しておいてください。

**1. Anthropic Console（Claude APIキー取得用）**
- URL: https://console.anthropic.com
- 用途: AI記事生成のAPIキーを取得
- 料金: 最初に$5分の無料クレジットあり

**2. GitHubアカウント**
- URL: https://github.com
- 用途: プログラムファイルの管理・バックアップ
- 料金: 無料

**3. Streamlit Cloudアカウント**
- URL: https://share.streamlit.io
- 用途: スマホからアクセスできるWebアプリのホスティング
- 料金: 無料

**4. noteアカウント**
- URL: https://note.com
- 用途: 生成した記事を下書き保存する先
- 料金: 無料

### 必要なソフトウェア（PC）

- **Python 3.12以上**（プログラム実行環境）
- **Git**（ファイル管理ツール）
- **メモ帳**（ファイル編集用）

---

## 第3章：Pythonのインストール

### Windows の場合

1. https://www.python.org/downloads/windows/ を開く
2. 最新のPythonインストーラーをダウンロード
3. インストーラーを起動

⚠️ **重要！** インストール画面で必ず確認：

```
☑ Add python.exe to PATH  ← 必ずチェックを入れる！
```

チェックを入れたら「Install Now」をクリック。

4. インストール完了後、PowerShellを**一度閉じて開き直す**
5. 以下のコマンドで確認：

```powershell
python --version
```

`Python 3.12.x` と表示されれば成功です！

---

## 第4章：プロジェクトファイルの準備

### フォルダ構成

デスクトップに以下の構成でフォルダを作成します：

```
Desktop/
└── note-auto-blog/
    ├── app.py                    # メインのWebアプリ
    ├── pipeline.py               # 一括実行スクリプト
    ├── requirements.txt          # 必要なライブラリ一覧
    ├── .env.example              # 環境変数テンプレート
    ├── collectors/
    │   ├── __init__.py
    │   └── rss_collector.py      # RSS収集プログラム
    ├── generators/
    │   ├── __init__.py
    │   └── article_generator.py  # AI記事生成プログラム
    └── publishers/
        ├── __init__.py
        └── note_publisher.py     # note自動保存プログラム
```

### ライブラリのインストール

PowerShellを開いて以下を実行：

```powershell
cd $env:USERPROFILE\Desktop\note-auto-blog
pip install -r requirements.txt
playwright install chromium
```

`requirements.txt` の内容：
```
anthropic>=0.40.0
feedparser>=6.0.0
playwright>=1.40.0
streamlit>=1.30.0
python-dotenv>=1.0.0
nest_asyncio>=1.5.0
```

---

## 第5章：APIキーの取得と設定

### Claude APIキーの取得

1. https://console.anthropic.com にアクセス
2. アカウント作成・ログイン
3. 左メニュー「API Keys」→「Create key」
4. 名前を入力（例：note-blog）→「Create key」
5. 表示されたキー（`sk-ant-api03-xxxx`）をコピー

⚠️ **キーは一度しか表示されません！必ずコピーして保存してください。**

### .envファイルの作成

`.env.example` をコピーして `.env` という名前で保存し、メモ帳で開いて編集：

```
ANTHROPIC_API_KEY=sk-ant-api03-ここにキーを貼り付け

NOTE_EMAIL=noteに登録したメールアドレス
NOTE_PASSWORD=noteのパスワード
```

⚠️ **このファイルは絶対にGitHubに公開しないでください！**

---

## 第6章：各プログラムの役割と仕組み

### RSS収集プログラム（rss_collector.py）

note.comのAI関連記事をRSSで収集します。

収集対象のタグ：
- note Claude（Claudeの使い方記事）
- note Anthropic（Anthropicに関する記事）
- note 生成AI（生成AI全般の記事）
- note AI活用（AI活用事例の記事）
- note プロンプト（プロンプト技術の記事）
- など

スコアリング機能で関連性の高い記事を優先して収集します。

### AI記事生成プログラム（article_generator.py）

Claude APIを使って、収集した記事を参考に初心者向け記事を生成します。

生成される記事の構成：
1. はじめに（このテーマが初心者に必要な理由）
2. そもそも〇〇って何？（やさしい説明）
3. なぜ今注目されているの？
4. 実際の使い方（ステップ形式）
5. こんな場面で使える！（活用事例3つ）
6. 注意点・気をつけること

**重要なルール：**
- 参考記事の表現はそのまま使わない
- 専門用語には必ず補足説明をつける
- 古い年号は使わず「最近」「現在」などの表現を使う

### note自動保存プログラム（note_publisher.py）

Playwright（ブラウザ自動操作ツール）を使って、noteに自動ログインして記事を下書き保存します。

動作の流れ：
1. noteにログイン
2. 新規記事作成ページを開く
3. タイトルを入力
4. 本文を入力
5. 「下書き保存」ボタンをクリック

---

## 第7章：アプリの起動と使い方

### ローカルでの起動

PowerShellで以下を実行：

```powershell
cd $env:USERPROFILE\Desktop\note-auto-blog
$env:ANTHROPIC_API_KEY="sk-ant-api03-あなたのキー"
$env:NOTE_EMAIL="あなたのnoteメール"
$env:NOTE_PASSWORD="あなたのnoteパスワード"
streamlit run app.py
```

ブラウザが自動で開いて管理画面が表示されます。

### 操作手順

**Step 1: RSSを収集する**
「📡 RSSを収集する」ボタンをクリック。
note.comの最新AI記事が15件前後収集されます。

**Step 2: 記事を生成する**
「✍️ 記事を生成する」ボタンをクリック。
Claude AIが初心者向け解説記事を自動生成します（30秒〜1分）。

**Step 3: 記事を確認する**
「📄 記事を管理する」タブで生成された記事を確認。
タイトル案が3つ表示されます。

**Step 4: noteに保存する**
「📤 noteに保存する」タブで「📤 noteに保存」ボタンをクリック。
ブラウザが自動でnoteを操作して下書き保存します。

**Step 5: 手動で投稿する**
noteを開いて下書きを確認・編集して、手動で投稿します。

---

## 第8章：スマホからアクセスできるようにする

### GitHubにアップロード

PowerShellで実行：

```powershell
cd $env:USERPROFILE\Desktop\note-auto-blog
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/あなたのユーザー名/note-auto-blog.git
git push -u origin master
```

### Streamlit Cloudでデプロイ

1. https://share.streamlit.io にアクセス
2. GitHubアカウントでログイン
3. 「Create app」→「Deploy a public app from GitHub」
4. 「Paste GitHub URL」で以下を入力：
   ```
   https://github.com/あなたのユーザー名/note-auto-blog/blob/master/app.py
   ```
5. 「Advanced settings」→「Secrets」に入力：
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-api03-あなたのキー"
   NOTE_EMAIL = "あなたのnoteメール"
   NOTE_PASSWORD = "あなたのnoteパスワード"
   ```
6. 「Deploy」をクリック

数分後にURLが発行されて、スマホからどこでもアクセスできます！

---

## 第9章：よくあるトラブルと解決方法

### pipが認識されない

**原因：** Pythonインストール時に「Add python.exe to PATH」のチェックを忘れた

**解決策：** Pythonを再インストール。チェックを必ず入れる。

### RSS収集で0件になる

**原因：** 収集期間内に記事がない、またはカテゴリ設定が合っていない

**解決策：** `rss_collector.py` の `max_age_hours` を大きくする（例：504 = 3週間）

### note保存でログイン失敗

**原因：** パスワードが間違っている、またはセッションファイルが古い

**解決策：** 
- パスワードを確認
- `data/sessions/` フォルダのファイルを削除して再試行

### 記事生成で0件になる

**原因：** APIキーが正しく設定されていない

**解決策：** PowerShellで `$env:ANTHROPIC_API_KEY="正しいキー"` を設定してから起動

---

## 第10章：さらに活用するために

### 記事テーマのカスタマイズ

`article_generator.py` の `BEGINNER_THEMES` リストに独自のテーマを追加できます：

```python
{"theme": "あなたのテーマ", "angle": "記事の切り口"},
```

### 収集するRSSの追加

`rss_collector.py` の `RSS_FEEDS` に好みのnoteタグを追加できます：

```python
{"name": "note 好きなタグ", "url": "https://note.com/hashtag/好きなタグ/rss"},
```

### 定期自動実行

Windowsのタスクスケジューラを使えば、毎朝自動で記事生成・保存できます。

---

## まとめ

この記事では、AIを使ったnoteブログ記事自動生成システムの作り方を解説しました。

最初は難しく感じるかもしれませんが、手順通りに進めれば必ずできます。

- Python・GitHub・Streamlitはすべて無料
- Claude APIは記事1本あたり約0.5円と非常に安い
- 一度設定すれば毎日5分で記事の下書きが完成

ぜひ試してみてください！

質問や困ったことがあれば、コメントでお気軽にどうぞ。

---

#AI活用 #Claude #note自動化 #ブログ自動生成 #初心者向け #生成AI #Python #Streamlit #AIツール #仕事効率化
