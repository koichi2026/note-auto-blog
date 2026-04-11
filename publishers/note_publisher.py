"""
note下書き保存モジュール
Playwrightを使ってnote.comに記事を下書き保存します
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

SESSION_DIR = Path("data/sessions")
SESSION_FILE = SESSION_DIR / "note_session.json"


async def save_to_note(
    title: str,
    body_text: str,
    hashtags: list,
    note_email: str,
    note_password: str,
    headless: bool = True
) -> dict:
    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "message": "Playwrightがインストールされていません"}

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context_options = {}
        if SESSION_FILE.exists():
            context_options["storage_state"] = str(SESSION_FILE)

        context = await browser.new_context(**context_options)
        page = await context.new_page()

        try:
            # ログイン
            print("🔐 ログイン中...")
            await page.goto("https://note.com/login", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            inputs = await page.query_selector_all("input")
            if len(inputs) < 2:
                return {"success": False, "message": "ログインフォームが見つかりませんでした"}

            await inputs[0].fill(note_email)
            await inputs[1].fill(note_password)
            await asyncio.sleep(0.5)
            await page.click("button:has-text('ログイン')")
            await asyncio.sleep(4)

            # ログイン確認
            if "login" in page.url:
                return {"success": False, "message": "ログインに失敗しました"}

            print("✅ ログイン成功")
            await context.storage_state(path=str(SESSION_FILE))

            # 新規記事作成ページへ
            print("📝 新規記事作成ページを開いています...")
            await page.goto("https://note.com/notes/new", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(4)

            current_url = page.url
            print(f"📍 エディタURL: {current_url}")

            # タイトル入力
            print("✏️ タイトルを入力中...")
            title_selectors = [
                "textarea[placeholder*='タイトル']",
                "input[placeholder*='タイトル']",
                "[data-testid='title']",
                ".title-input",
                "h1[contenteditable='true']",
                "div[contenteditable='true']:first-of-type",
            ]
            title_input = None
            for selector in title_selectors:
                try:
                    title_input = await page.wait_for_selector(selector, timeout=3000)
                    if title_input:
                        break
                except Exception:
                    continue

            if title_input:
                await title_input.click()
                await asyncio.sleep(0.5)
                await title_input.fill(title)
            else:
                # Tabキーで最初のフィールドに移動
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.5)
                await page.keyboard.type(title)

            await asyncio.sleep(1)

            # 本文入力
            print("📄 本文を入力中...")
            body_selectors = [
                ".ProseMirror",
                "[contenteditable='true']",
                "div[role='textbox']",
                ".ql-editor",
            ]
            body_input = None
            for selector in body_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if len(elements) > 1:
                        body_input = elements[-1]
                    elif len(elements) == 1:
                        body_input = elements[0]
                    if body_input:
                        break
                except Exception:
                    continue

            if body_input:
                await body_input.click()
                await asyncio.sleep(1)
                # クリップボード経由で貼り付け
                await page.evaluate("(text) => navigator.clipboard.writeText(text)", body_text)
                await asyncio.sleep(0.5)
                await page.keyboard.press("Control+v")
                await asyncio.sleep(2)
            else:
                return {"success": False, "message": "本文入力欄が見つかりませんでした"}

            # 下書き保存ボタンをクリック
            print("💾 下書き保存中...")
            await asyncio.sleep(1)
            try:
                save_btn = await page.wait_for_selector("button:has-text('下書き保存')", timeout=5000)
                if save_btn:
                    await save_btn.click()
                    await asyncio.sleep(3)
                    print("✅ 下書き保存完了!")
                    await context.storage_state(path=str(SESSION_FILE))
                    return {
                        "success": True,
                        "message": "下書き保存完了",
                        "url": page.url
                    }
            except Exception as e:
                return {"success": False, "message": f"下書き保存ボタンが見つかりませんでした: {e}"}

        except Exception as e:
            screenshot_path = Path("data/screenshots") / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            return {"success": False, "message": f"エラー: {str(e)}"}

        finally:
            await context.close()
            await browser.close()


def save_to_note_sync(
    title: str,
    body_text: str,
    hashtags: list,
    note_email: str,
    note_password: str,
    headless: bool = True
) -> dict:
    return asyncio.run(save_to_note(
        title=title,
        body_text=body_text,
        hashtags=hashtags,
        note_email=note_email,
        note_password=note_password,
        headless=headless
    ))