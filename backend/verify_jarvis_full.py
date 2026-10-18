import time
from pathlib import Path
from playwright.sync_api import sync_playwright

artifact_dir = Path(r"C:\Users\Jeevan\.gemini\antigravity\brain\456f155e-9d1b-48db-a87b-e5367bf83d7b")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    
    # 1. Load J.A.R.V.I.S. Command Center
    page.goto("http://127.0.0.1:8000/jarvis_command_center.html")
    time.sleep(2.5)
    page.screenshot(path=str(artifact_dir / "proof_jarvis_companion_sphere.png"))
    print("Screenshot 1 captured: proof_jarvis_companion_sphere.png")
    
    # 2. Click Optical Sensor Button and wait for Moondream frame
    page.click("#btnOpticalScan")
    page.wait_for_function("() => { const img = document.getElementById('opticalImagePreview'); return img && img.src && img.src.length > 50; }", timeout=25000)
    time.sleep(1.0)
    page.screenshot(path=str(artifact_dir / "proof_optical_sensor_modal.png"))
    print("Screenshot 2 captured: proof_optical_sensor_modal.png")
    
    # Close optical modal
    page.click("#btnCloseOpticalModal")
    time.sleep(0.5)
    
    # 3. Click Brain / Memory Button
    page.click("#btnCognitiveMemory")
    time.sleep(2.0)
    page.screenshot(path=str(artifact_dir / "proof_cognitive_memory_drawer.png"))
    print("Screenshot 3 captured: proof_cognitive_memory_drawer.png")
    
    browser.close()
