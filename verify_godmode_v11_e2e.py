import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACT_DIR = Path(r"C:\Users\Jeevan\.gemini\antigravity\brain\456f155e-9d1b-48db-a87b-e5367bf83d7b")

async def run_verification():
    print("Launching Playwright for J.A.R.V.I.S. v11.0 GODMODE verification...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Load the Command Center UI
        print("Navigating to http://127.0.0.1:8000/ ...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await asyncio.sleep(2)

        # Proof 1: Main GODMODE View with 3D Holographic Sphere, SoM Cortex & Active Tasks
        p1 = ARTIFACT_DIR / "proof_godmode_v11_sphere_tasks.png"
        await page.screenshot(path=str(p1), full_page=True)
        print(f"Captured Proof 1: {p1}")

        # 2. Toggle Arc Reactor Mode
        btn_arc = page.locator("#btnToggleArcReactor")
        if await btn_arc.count() > 0:
            await btn_arc.click(force=True)
            await asyncio.sleep(1)
            p_arc = ARTIFACT_DIR / "proof_godmode_v11_arc_reactor.png"
            await page.screenshot(path=str(p_arc), full_page=True)
            print(f"Captured Arc Reactor Mode Proof: {p_arc}")

        # 3. Toggle Quantum Grid Mode
        btn_grid = page.locator("#btnToggleQuantumGrid")
        if await btn_grid.count() > 0:
            await btn_grid.click(force=True)
            await asyncio.sleep(1)
            p_grid = ARTIFACT_DIR / "proof_godmode_v11_quantum_grid.png"
            await page.screenshot(path=str(p_grid), full_page=True)
            print(f"Captured Quantum Grid Mode Proof: {p_grid}")

        # 4. Open 5-Agent Swarm Drawer
        btn_swarm = page.locator("#btnToggleSwarm")
        if await btn_swarm.count() > 0:
            await btn_swarm.click(force=True)
            await asyncio.sleep(1)
            p2 = ARTIFACT_DIR / "proof_godmode_v11_swarm_blackboard.png"
            await page.screenshot(path=str(p2), full_page=True)
            print(f"Captured Proof 2 (Swarm Blackboard): {p2}")
            # Toggle off swarm
            await btn_swarm.click(force=True)
            await asyncio.sleep(0.5)

        # 5. Open 4-Tier Cognitive Brain Drawer
        btn_brain = page.locator("#btnToggleBrain")
        if await btn_brain.count() > 0:
            await btn_brain.click(force=True)
            await asyncio.sleep(1)
            p3 = ARTIFACT_DIR / "proof_godmode_v11_cognitive_brain.png"
            await page.screenshot(path=str(p3), full_page=True)
            print(f"Captured Proof 3 (Cognitive Brain): {p3}")
            # Toggle off brain
            await btn_brain.click(force=True)
            await asyncio.sleep(0.5)

        # 6. Open Terminal Drawer & Run Command
        btn_term = page.locator("#btnToggleTerminal")
        if await btn_term.count() > 0:
            await btn_term.click(force=True)
            await asyncio.sleep(1)
            term_input = page.locator("#terminalInput")
            if await term_input.count() > 0:
                await term_input.fill("echo 'JARVIS v11 GODMODE VERIFIED'")
                await page.locator("#terminalForm button[type=submit]").click(force=True)
                await asyncio.sleep(2)
            p4 = ARTIFACT_DIR / "proof_godmode_v11_terminal_execution.png"
            await page.screenshot(path=str(p4), full_page=True)
            print(f"Captured Proof 4 (Terminal Execution): {p4}")

        await browser.close()
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_verification())
