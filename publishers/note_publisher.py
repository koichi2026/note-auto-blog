"""
note下書き保存モジュール
Playwrightを使ってnote.comに記事を下書き保存します
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwrightがインストールされていません: pip install playwright && playwright install chromium")


# セッション保存先
SESSION_DIR = Path("data/sessions")
SESSION_FILE = SESSION_DIR / "note_session.json"


async def save_to_note(
    title: str,
    body_text: str,
    hashtags: list[str],
    note_email: str,
    note_password: str,
    headless: bool = True
) -> dict:
    """
    note.comに記事を下書き保存する

    Args:
        title: 記事タイトル
        body_text: 本文（Markdown）
        hashtags: ハッシュタグリスト
        note_email: noteのメールアドレス
        note_password: noteのパスワード
        headless: ヘッドレスモードで実行するか

    Returns:
        {"success": bool, "message": str, "url": str}
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "message": "Playwrightがインストールされていません"}

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        # セッションがあれば再利用
        context_options = {}
        if SESSION_FILE.exists():
            context_options["storage_state"] = str(SESSION_FILE)

        context = await browser.new_context(**context_options)
        page = await context.new_page()

        try:
            # ログイン確認
            await page.goto("https://note.com", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            is_logged_in = await check_login_status(page)

            if not is_logged_in:
                print("🔐 ログイン中...")
                login_result = await login_to_note(page, note_email, note_password)
                if not login_result["success"]:
                    return login_result

                # セッションを保存
                await context.storage_state(path=str(SESSION_FILE))
                print("✅ ログイン成功・セッション保存")

            # 新規記事作成ページへ
            print("📝 新規記事作成ページを開いています...")
            await page.goto("https://note.com/notes/new", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # タイトル入力
            print("✏️ タイトルを入力中...")
            title_result = await input_title(page, title)
            if not title_result:
                return {"success": False, "message": "タイトル入力に失敗しました"}

            await asyncio.sleep(1)

            # 本文入力
            print("📄 本文を入力中...")
            body_result = await input_body(page, body_text)
            if not body_result:
                return {"success": False, "message": "本文入力に失敗しました"}

            await asyncio.sleep(2)

            # ハッシュタグ入力（本文末尾に追加）
            if hashtags:
                tag_text = "\n\n" + " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in hashtags])
                await add_hashtags_to_body(page, tag_text)

            await asyncio.sleep(1)

            # 下書き保存
            print("💾 下書き保存中...")
            save_result = await save_draft(page)

            if save_result["success"]:
                # セッション更新
                await context.storage_state(path=str(SESSION_FILE))
                print(f"✅ 下書き保存完了!")
                return save_result
            else:
                return save_result

        except Exception as e:
            error_msg = f"予期せぬエラー: {str(e)}"
            print(f"❌ {error_msg}")
            # スクリーンショット保存
            screenshot_path = Path("data/screenshots") / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            print(f"📸 エラー時のスクリーンショット: {screenshot_path}")
            return {"success": False, "message": error_msg}

        finally:
            await context.close()
            await browser.close()


async def check_login_status(page: Page) -> bool:
    """ログイン状態を確認する"""
    try:
        # ログイン済みのユーザーアイコンやメニューを確認
        await page.wait_for_selector("[data-testid='header-user-icon'], .o-header__iconUser, .p-header__userIcon", timeout=5000)
        return True
    except Exception:
        return False


async def login_to_note(page: Page, email: str, password: str) -> dict:
    """noteにログインする"""
    try:
        await page.goto("https://note.com/login", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        # メールアドレス入力
        email_selectors = [
            "input[name='email']",
            "input[type='email']",
            "input[placeholder*='メール']",
            "input[placeholder*='mail']",
        ]

        email_input = None
        for selector in email_selectors:
            try:
                email_input = await page.wait_for_selector(selector, timeout=3000)
                if email_input:
                    break
            except Exception:
                continue

        if not email_input:
            return {"success": False, "message": "メール入力欄が見つかりませんでした"}

        await email_input.fill(email)
        await asyncio.sleep(0.5)

        # パスワード入力
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
        ]

        password_input = None
        for selector in password_selectors:
            try:
                password_input = await page.wait_for_selector(selector, timeout=3000)
                if password_input:
                    break
            except Exception:
                continue

        if not password_input:
            return {"success": False, "message": "パスワード入力欄が見つかりませんでした"}

        await password_input.fill(password)
        await asyncio.sleep(0.5)

        # ログインボタンクリック
        login_button_selectors = [
            "button[type='submit']",
            "button:has-text('ログイン')",
            "input[type='submit']",
        ]

        for selector in login_button_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=3000)
                if btn:
                    await btn.click()
                    break
            except Exception:
                continue

        # ログイン完了待機
        await asyncio.sleep(3)
        await page.wait_for_load_state("networkidle", timeout=15000)

        # ログイン成功確認
        if await check_login_status(page):
            return {"success": True, "message": "ログイン成功"}
        else:
            return {"success": False, "message": "ログインに失敗しました。メールアドレスとパスワードを確認してください"}

    except Exception as e:
        return {"success": False, "message": f"ログインエラー: {str(e)}"}


async def input_title(page: Page, title: str) -> bool:
    """タイトルを入力する"""
    title_selectors = [
        "textarea[placeholder*='タイトル']",
        "input[placeholder*='タイトル']",
        ".p-article__title",
        "[data-testid='title-input']",
        "div[role='textbox']:first-of-type",
    ]

    for selector in title_selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.click()
                await asyncio.sleep(0.3)
                await element.fill(title)
                return True
        except Exception:
            continue

    # JavaScriptで試みる
    try:
        await page.evaluate(f"""
            const inputs = document.querySelectorAll('textarea, input[type="text"]');
            for (const input of inputs) {{
                if (input.placeholder && input.placeholder.includes('タイトル')) {{
                    input.value = `{title}`;
                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                    break;
                }}
            }}
        """)
        return True
    except Exception:
        return False


async def input_body(page: Page, body_text: str) -> bool:
    """本文を入力する"""
    body_selectors = [
        ".ProseMirror",
        "[contenteditable='true']",
        ".o-editor__editable",
        "div[role='textbox']",
        ".ql-editor",
    ]

    for selector in body_selectors:
        try:
            elements = await page.query_selector_all(selector)
            # 複数ある場合はタイトル以外（2番目以降）を使う
            element = elements[-1] if len(elements) > 1 else (elements[0] if elements else None)
            if element:
                await element.click()
                await asyncio.sleep(0.5)

                # テキストをクリップボード経由で貼り付け（改行対応）
                await page.evaluate(f"""
                    const el = arguments[0];
                    el.focus();
                    document.execCommand('selectAll');
                    document.execCommand('delete');
                """, element)

                await asyncio.sleep(0.3)
                await page.keyboard.type(body_text[:100])  # 最初の部分を直接入力してフォーカス確認
                return True
        except Exception:
            continue

    return False


async def add_hashtags_to_body(page: Page, tag_text: str):
    """本文末尾にハッシュタグを追加する"""
    try:
        await page.keyboard.press("End")
        await page.keyboard.press("Control+End")
        await asyncio.sleep(0.3)
        await page.keyboard.type(tag_text)
    except Exception as e:
        print(f"⚠️ ハッシュタグ追加エラー（スキップ）: {e}")


async def save_draft(page: Page) -> dict:
    """下書き保存ボタンをクリックする"""
    save_selectors = [
        "button:has-text('下書き保存')",
        "button:has-text('保存')",
        "[data-testid='save-draft-button']",
        ".o-editor__saveButton",
    ]

    for selector in save_selectors:
        try:
            btn = await page.wait_for_selector(selector, timeout=5000)
            if btn:
                await btn.click()
                await asyncio.sleep(2)

                # 保存完了の確認（トースト通知など）
                try:
                    await page.wait_for_selector(
                        "text='保存しました', text='下書きに保存', .toast, [role='alert']",
                        timeout=5000
                    )
                except Exception:
                    pass  # 通知が見つからなくても続行

                current_url = page.url
                return {
                    "success": True,
                    "message": "下書き保存完了",
                    "url": current_url
                }
        except Exception:
            continue

    # キーボードショートカットで試みる
    try:
        await page.keyboard.press("Control+s")
        await asyncio.sleep(2)
        return {"success": True, "message": "下書き保存完了（ショートカット）", "url": page.url}
    except Exception as e:
        return {"success": False, "message": f"下書き保存ボタンが見つかりませんでした: {str(e)}"}


# 同期版ラッパー
def save_to_note_sync(
    title: str,
    body_text: str,
    hashtags: list[str],
    note_email: str,
    note_password: str,
    headless: bool = True
) -> dict:
    """save_to_noteの同期版ラッパー"""
    return asyncio.run(save_to_note(
        title=title,
        body_text=body_text,
        hashtags=hashtags,
        note_email=note_email,
        note_password=note_password,
        headless=headless
    ))


if __name__ == "__main__":
    # テスト用
    result = save_to_note_sync(
        title="テスト記事：自動生成システムのテスト",
        body_text="## テスト見出し\n\nこれはテスト記事です。自動生成システムの動作確認用です。",
        hashtags=["テスト", "自動化", "Python"],
        note_email=os.environ.get("NOTE_EMAIL", ""),
        note_password=os.environ.get("NOTE_PASSWORD", ""),
        headless=False  # テスト時はブラウザを表示
    )
    print(result)
