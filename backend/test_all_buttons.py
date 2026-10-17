import asyncio
from playwright.async_api import async_playwright

async def test_buttons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            headless=True
        )
        page = await browser.new_page()

        errors = []
        page.on("pageerror", lambda err: errors.append(f"[PAGE ERROR] {err}"))

        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await asyncio.sleep(1.0)

        buttons_to_test = [
            ("#btnDemoIncidentApp", "DevOps Incident App"),
            ("#btnDemoMedTriageApp", "Rural Triage App"),
            ("#btnDemoFinTechApp", "FinTech Fraud Radar"),
            ("#btnDemoCalculatorApp", "Calculator App"),
            ("#btnDemoSnakeGame", "Snake Canvas Game"),
            ("#btnStopPipeline", "Stop Pipeline Button"),
        ]

        for btn_sel, label in buttons_to_test:
            print(f"Testing button: {label} ({btn_sel})...")
            await page.click(btn_sel)
            await asyncio.sleep(1.0)
            if errors:
                print(f"FAILED on {label}: {errors}")
                break
            else:
                print(f"SUCCESS on {label} (no JS errors)")

        print(f"\nTotal page errors encountered: {len(errors)}")
        await browser.close()

asyncio.run(test_buttons())
