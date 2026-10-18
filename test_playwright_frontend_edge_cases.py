import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACT_DIR = Path(r"C:\Users\Jeevan\.gemini\antigravity\brain\456f155e-9d1b-48db-a87b-e5367bf83d7b")
INDEX_PATH = Path(r"e:\New folder\index.html").as_uri()

async def main():
    print(f"Launching Playwright to test frontend: {INDEX_PATH}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Capture console messages
        page.on("console", lambda msg: print(f"[BROWSER {msg.type.upper()}]: {msg.text}"))

        await page.goto(INDEX_PATH, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 1. Take initial screenshot with Typing Console visible
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_edgecase_frontend_initial.png"))
        print("Captured: proof_edgecase_frontend_initial.png")

        # 2. Type "open notepad and type JARVIS GODMODE VERIFIED"
        inp = page.locator("#mainCommandInput")
        await inp.fill("open notepad and type JARVIS GODMODE VERIFIED")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_edgecase_notepad_typed.png"))
        print("Captured: proof_edgecase_notepad_typed.png")

        # 3. Type "download python"
        await inp.fill("download python")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_edgecase_download_python.png"))
        print("Captured: proof_edgecase_download_python.png")

        # 4. Type "draft a gmail to lead@google.com about Autonomous Agents"
        await inp.fill("draft a gmail to lead@google.com about Autonomous Agents")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_edgecase_gmail_draft_confirmation.png"))
        print("Captured: proof_edgecase_gmail_draft_confirmation.png")

        # 5. Type "open whatsapp and send msg to Mom: Love you"
        await inp.fill("open whatsapp and send msg to Mom: Love you")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_edgecase_whatsapp_dispatched.png"))
        print("Captured: proof_edgecase_whatsapp_dispatched.png")

        # 6. Open Active Tasks Drawer and Swarm Blackboard
        btn_tasks = page.locator("#btnToggleTasksDrawer")
        if await btn_tasks.count() > 0:
            await btn_tasks.click()
            await page.wait_for_timeout(1000)

        await page.screenshot(path=str(ARTIFACT_DIR / "proof_edgecase_tasks_drawer_active.png"))
        print("Captured: proof_edgecase_tasks_drawer_active.png")

        await browser.close()
        print("All Playwright frontend tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
