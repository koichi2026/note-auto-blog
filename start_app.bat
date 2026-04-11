@echo off
cd %USERPROFILE%\Desktop\note-auto-blog
set ANTHROPIC_API_KEY=ここには入力しない
set NOTE_EMAIL=koichi.yoshino.2023@gmail.com
set NOTE_PASSWORD=noteのパスワード
set GITHUB_TOKEN=ここには入力しない
set GITHUB_REPO=koichi2026/note-auto-blog
streamlit run app.py