# note自動記事生成システム - 進捗状況

## 最終更新: 2026-04-09

---

## ✅ 完了済み

### 環境構築
- [x] Python 3.12 インストール
- [x] 必要ライブラリインストール（streamlit, feedparser, playwright, python-dotenv）
- [x] Playwright Chromiumインストール

### ファイル作成・配置
- [x] フォルダ構成作成（collectors / generators / publishers）
- [x] 全Pythonファイル配置
- [x] `.env` ファイル作成（Gemini APIキー・note認証情報）

### GitHub
- [x] GitHubリポジトリ作成（koichi2026/note-auto-blog）
- [x] コードをGitHubにプッシュ
- [x] `.env` ファイルをGitHubから削除（セキュリティ対応）
- [x] リポジトリをPublicに変更

### Streamlit Cloud
- [x] Streamlit Cloudアカウント作成
- [x] アプリデプロイ完了
- [x] アプリURL発行: https://note-auto-blog-iylhcwf2cpassyscnhqb6z.streamlit.app

### 動作確認
- [x] ローカルでアプリ起動確認
- [x] RSS収集動作確認（15件収集成功）
- [x] Streamlit CloudでのUI表示確認

---

## ⏳ 未完了・次のステップ

### 最優先
- [ ] **Claude APIキー取得**（console.anthropic.comが復旧次第）
  - 現在Gemini APIを使用中だが429エラーが頻発
  - Claude Haiku APIへの切り替えが必要
- [ ] **記事生成の動作確認**（APIキー取得後）
- [ ] **Streamlit CloudのSecretsにAPIキーを追加**

### Claude APIへの切り替え手順
1. `console.anthropic.com` でAPIキー取得（`sk-ant-xxxx`）
2. `generators/article_generator.py` をClaude版に書き換え
3. Streamlit CloudのSecrets更新:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-xxxx"
   NOTE_EMAIL = "koichi.yoshino.2023@gmail.com"
   NOTE_PASSWORD = "パスワード"
   ```
4. GitHubにプッシュ → 自動デプロイ

### 将来的な改善
- [ ] note下書き保存（Playwright）の動作確認
- [ ] 記事品質の確認・プロンプト調整
- [ ] スケジューラ設定（毎日自動実行）
- [ ] noteパスワード変更（チャットで露出したため）

---

## ⚠️ 注意事項

### セキュリティ
- noteのパスワード「koichi0620」がチャットで露出 → **早めに変更推奨**
- Gemini APIキーも複数回露出 → 必要に応じて再発行
- GitHubリポジトリはPublicのため `.env` は絶対にコミットしない

### 既知の問題
- Gemini API無料枠: 429エラー頻発（レート制限）
- Playwright note保存: Streamlit Cloud環境では動作しない可能性あり
  （Streamlit CloudはヘッドレスChromiumが制限されているため）
  → note保存はローカルPCで実行する必要があるかもしれない

---

## 📝 次回Claudeに伝えること

以下をClaudeに貼り付けてください：

```
note自動記事生成システムの開発を続けています。
claude.mdとprogress.mdを参照してください。
現在の状況：Streamlit Cloudにデプロイ完了。
次のタスク：Claude APIキーを取得してarticle_generator.pyをClaude版に切り替える。
```
