"""
note下書き保存モジュール
サブプロセスでPlaywrightを実行してnote.comに記事を下書き保存します
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

PLAYWRIGHT_AVAILABLE = True
SESSION_DIR = Path("data/sessions")
SESSION_FILE = SESSION_DIR / "note_session.json"

PLAYWRIGHT_SCRIPT = '''
import asyncio
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_FILE = Path("data/sessions/note_session.json")

async def save_to_note(title, body_text, note_email, note_password, headless):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context_options = {}
        if SESSION_FILE.exists():
            context_options["storage_state"] = str(SESSION_FILE)

        context = await browser.new_context(**context_options)
        page = await context.new_page()

        try:
            print("🔐 ログイン中...", flush=True)
            await page.goto("https://note.com/login", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # visibleなinputだけを使う
            inputs = await page.query_selector_all("input")
            visible_inputs = []
            for inp in inputs:
                if await inp.is_visible():
                    visible_inputs.append(inp)

            if len(visible_inputs) < 2:
                print(json.dumps({"success": False, "message": "ログインフォームが見つかりませんでした"}))
                return

            await visible_inputs[0].fill(note_email)
            await asyncio.sleep(0.5)
            await visible_inputs[1].fill(note_password)
            await asyncio.sleep(0.5)
            await page.click("button:has-text('ログイン')")
            await asyncio.sleep(5)

            if "login" in page.url:
                print(json.dumps({"success": False, "message": "ログインに失敗しました"}))
                return

            print("✅ ログイン成功", flush=True)
            await context.storage_state(path=str(SESSION_FILE))

            print("📝 新規記事作成ページを開いています...", flush=True)
            await page.goto("https://note.com/notes/new", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(4)

            print("✏️ タイトルを入力中...", flush=True)
            title_selectors = [
                "textarea[placeholder*='タイトル']",
                "input[placeholder*='タイトル']",
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
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.5)
                await page.keyboard.type(title)

            await asyncio.sleep(1)

            print("📄 本文を入力中...", flush=True)
            body_selectors = [".ProseMirror", "[contenteditable='true']", "div[role='textbox']"]
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
                await page.evaluate("(text) => navigator.clipboard.writeText(text)", body_text)
                await asyncio.sleep(0.5)
                await page.keyboard.press("Control+v")
                await asyncio.sleep(2)
            else:
                print(json.dumps({"success": False, "message": "本文入力欄が見つかりませんでした"}))
                return

            print("💾 下書き保存中...", flush=True)
            await asyncio.sleep(1)
            try:
                save_btn = await page.wait_for_selector("button:has-text('下書き保存')", timeout=5000)
                if save_btn:
                    await save_btn.click()
                    await asyncio.sleep(3)
                    await context.storage_state(path=str(SESSION_FILE))
                    print("✅ 下書き保存完了!", flush=True)
                    print(json.dumps({"success": True, "message": "下書き保存完了", "url": page.url}))
            except Exception as e:
                print(json.dumps({"success": False, "message": f"下書き保存ボタンが見つかりませんでした: {e}"}))

        except Exception as e:
            print(json.dumps({"success": False, "message": f"エラー: {str(e)}"}))
        finally:
            await context.close()
            await browser.close()

data = json.loads(sys.argv[1])
asyncio.run(save_to_note(
    data["title"],
    data["body_text"],
    data["note_email"],
    data["note_password"],
    data["headless"]
))
'''


def save_to_note_sync(
    title: str,
    body_text: str,
    hashtags: list,
    note_email: str,
    note_password: str,
    headless: bool = True
) -> dict:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(PLAYWRIGHT_SCRIPT)
        script_path = f.name

    try:
        data = {
            "title": title,
            "body_text": body_text,
            "note_email": note_email,
            "note_password": note_password,
            "headless": headless
        }

        result = subprocess.run(
            [sys.executable, script_path, json.dumps(data)],
            text=True,
            timeout=120,
            cwd=str(Path.cwd())
        )

        if result.returncode != 0:
            return {"success": False, "message": f"プロセスエラー"}

        return {"success": True, "message": "下書き保存完了"}

    except subprocess.TimeoutExpired:
        return {"success": False, "message": "タイムアウト（120秒）"}
    except Exception as e:
        return {"success": False, "message": f"実行エラー: {str(e)}"}
    finally:
        Path(script_path).unlink(missing_ok=True)
