import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            headless=True
        )
        page = await browser.new_page()

        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_messages.append(f"[PAGE ERROR] {err}"))

        print("Navigating to http://127.0.0.1:8000/ ...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await asyncio.sleep(2.0)

        print("\n--- Initial Console Logs ---")
        for m in console_messages:
            print(m)

        console_messages.clear()
        print("\n--- Clicking '#btnDemoSnakeGame' ---")
        await page.click("#btnDemoSnakeGame")
        await asyncio.sleep(3.0)

        print("\n--- Console Logs after clicking Snake Game ---")
        for m in console_messages:
            print(m)

        console_messages.clear()
        print("\n--- Typing 'WRITE A PYTHON CODE TO SW' and Clicking '#btnExecuteCommand' ---")
        await page.fill("#mainCommandInput", "WRITE A PYTHON CODE TO SW")
        await page.click("#btnExecuteCommand")
        await asyncio.sleep(3.0)

        print("\n--- Console Logs after clicking Run ---")
        for m in console_messages:
            print(m)

        editor_text = await page.inner_text("#sideActiveFilenameLabel")
        terminal_text = await page.inner_text("#sideTerminalOutput")
        print(f"\nActive File: {editor_text}")
        print(f"Terminal Output (first 300 chars): {terminal_text[:300]}")

        await browser.close()

asyncio.run(main())
