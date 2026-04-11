import os, asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto('https://note.com/login', wait_until='networkidle')
        await asyncio.sleep(3)
        
        print('URL:', page.url)
        
        # inputを確認
        inputs = await page.query_selector_all('input')
        print(f'input数: {len(inputs)}')
        for i, inp in enumerate(inputs):
            placeholder = await inp.get_attribute('placeholder')
            visible = await inp.is_visible()
            print(f'  input[{i}]: placeholder={placeholder}, visible={visible}')
        
        # visible なinputだけを使う
        visible_inputs = []
        for inp in inputs:
            if await inp.is_visible():
                visible_inputs.append(inp)
        
        print(f'visible input数: {len(visible_inputs)}')
        
        if len(visible_inputs) >= 2:
            await visible_inputs[0].fill(os.environ.get('NOTE_EMAIL',''))
            await visible_inputs[1].fill(os.environ.get('NOTE_PASSWORD',''))
            await page.click("button:has-text('ログイン')")
            await asyncio.sleep(4)
            print('ログイン後URL:', page.url)
        
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(test())