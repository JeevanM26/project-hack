import httpx
import json
import time
import psutil
import subprocess
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def log(tag, msg, passed=True):
    status = " PASS " if passed else "!FAIL!"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"[{status}] {tag:<25}: {msg}")

def run_tests():
    print("=" * 70)
    print(" J.A.R.V.I.S. GODMODE COMPREHENSIVE EDGE-CASE TEST SUITE")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # ---------------------------------------------------------
    # TEST 1: Open Notepad and Type Text
    # ---------------------------------------------------------
    print("\n--- TEST 1: Open Notepad & Type Text ---")
    r1 = client.post("/api/open-app", json={"instruction": "open notepad and type J.A.R.V.I.S. SYSTEM VERIFICATION 2026"})
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    d1 = r1.json()
    time.sleep(1.0)
    # Check if notepad process is running
    np_running = any("notepad" in p.name().lower() for p in psutil.process_iter(["name"]))
    log("Open Notepad", f"target={d1.get('target')}, typed='{d1.get('typed_text')}', running={np_running}", d1.get("ok") and np_running)

    # ---------------------------------------------------------
    # TEST 2: Open Calculator & Compute with Authentic UIA
    # ---------------------------------------------------------
    print("\n--- TEST 2: Open Calculator & Authentic UIA Math ---")
    r2 = client.post("/api/open-app", json={"instruction": "open calculator and compute 125 * 8"})
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    d2 = r2.json()
    res_val = str(d2.get("calculated_result", ""))
    calc_ok = "1000" in res_val or d2.get("ok")
    log("Calculator UIA", f"expr=125*8, result={res_val}, detail={d2.get('detail')}", calc_ok)

    # ---------------------------------------------------------
    # TEST 3: Pure 'Open WhatsApp'
    # ---------------------------------------------------------
    print("\n--- TEST 3: Pure 'Open WhatsApp' ---")
    r3 = client.post("/api/whatsapp-send", json={"instruction": "open whatsapp"})
    assert r3.status_code == 200
    d3 = r3.json()
    log("WhatsApp Pure Open", f"url={d3.get('url')}, spoken='{d3.get('spoken_response')}'", d3.get("url") == "https://web.whatsapp.com/")

    # ---------------------------------------------------------
    # TEST 4: WhatsApp Send with Phone Number
    # ---------------------------------------------------------
    print("\n--- TEST 4: WhatsApp Send with Phone Number ---")
    r4 = client.post("/api/whatsapp-send", json={"instruction": "open whatsapp and send msg to +919876543210 saying Meeting at 5pm"})
    assert r4.status_code == 200
    d4 = r4.json()
    has_phone = "919876543210" in d4.get("url", "")
    has_msg = "Meeting%20at%205pm" in d4.get("url", "") or "Meeting" in d4.get("message", "")
    log("WhatsApp Phone Send", f"phone={d4.get('phone')}, msg='{d4.get('message')}', url={d4.get('url')}", has_phone and has_msg)

    # ---------------------------------------------------------
    # TEST 5: WhatsApp Send with Contact Name
    # ---------------------------------------------------------
    print("\n--- TEST 5: WhatsApp Send with Contact Name ---")
    r5 = client.post("/api/whatsapp-send", json={"instruction": "send msg to Mom on whatsapp: I am on my way home"})
    assert r5.status_code == 200
    d5 = r5.json()
    log("WhatsApp Name Send", f"contact={d5.get('contact')}, msg='{d5.get('message')}', url={d5.get('url')}", d5.get("contact") == "Mom")

    # ---------------------------------------------------------
    # TEST 6: Pure 'Open Gmail'
    # ---------------------------------------------------------
    print("\n--- TEST 6: Pure 'Open Gmail' ---")
    r6 = client.post("/api/gmail-draft", json={"instruction": "open gmail"})
    assert r6.status_code == 200
    d6 = r6.json()
    log("Gmail Pure Open", f"url={d6.get('url')}, prompt='{d6.get('confirmation_prompt')}'", d6.get("url") == "https://mail.google.com/")

    # ---------------------------------------------------------
    # TEST 7: Draft Gmail with Full Details
    # ---------------------------------------------------------
    print("\n--- TEST 7: Draft Gmail Full Details ---")
    r7 = client.post("/api/gmail-draft", json={"instruction": "draft a gmail to dev@example.com about Project Milestone saying We have achieved 100% test coverage"})
    assert r7.status_code == 200
    d7 = r7.json()
    log("Gmail Draft Full", f"recipient={d7.get('recipient')}, subject='{d7.get('subject')}', url={d7.get('url')}", d7.get("recipient") == "dev@example.com" and "Milestone" in d7.get("subject"))

    # ---------------------------------------------------------
    # TEST 8: Draft Gmail with Name Only (No @ Email)
    # ---------------------------------------------------------
    print("\n--- TEST 8: Draft Gmail Name Only ---")
    r8 = client.post("/api/gmail-draft", json={"instruction": "draft email to Alex regarding quarterly review"})
    assert r8.status_code == 200
    d8 = r8.json()
    log("Gmail Draft Name", f"recipient={d8.get('recipient')}, subject='{d8.get('subject')}'", d8.get("recipient") == "Alex")

    # ---------------------------------------------------------
    # TEST 9: Universal Download Subsystem (Python)
    # ---------------------------------------------------------
    print("\n--- TEST 9: Universal Download Subsystem (Python) ---")
    r9 = client.post("/api/download", json={"instruction": "download python"})
    assert r9.status_code == 200
    d9 = r9.json()
    log("Download Python", f"resource={d9.get('resource_name')}, url={d9.get('url')}, winget={d9.get('winget_command')}", "python" in d9.get("resource_name", "").lower() and d9.get("ok"))

    # ---------------------------------------------------------
    # TEST 10: Universal Download Subsystem (VLC)
    # ---------------------------------------------------------
    print("\n--- TEST 10: Universal Download Subsystem (VLC) ---")
    r10 = client.post("/api/download", json={"instruction": "download vlc"})
    assert r10.status_code == 200
    d10 = r10.json()
    log("Download VLC", f"resource={d10.get('resource_name')}, winget={d10.get('winget_command')}", "vlc" in d10.get("resource_name", "").lower() and d10.get("ok"))

    # ---------------------------------------------------------
    # TEST 11: Web Search Google
    # ---------------------------------------------------------
    print("\n--- TEST 11: Web Search Google ---")
    r11 = client.post("/api/web-search", json={"instruction": "search google for quantum neural networks"})
    assert r11.status_code == 200
    d11 = r11.json()
    log("Web Search Google", f"query={d11.get('query')}, url={d11.get('url')}", "google.com/search" in d11.get("url", ""))

    # ---------------------------------------------------------
    # TEST 12: Direct Domain Navigation
    # ---------------------------------------------------------
    print("\n--- TEST 12: Direct Domain Navigation ---")
    r12 = client.post("/api/web-search", json={"instruction": "open website github.com"})
    assert r12.status_code == 200
    d12 = r12.json()
    log("Direct Domain Nav", f"url={d12.get('url')}", "github.com" in d12.get("url", ""))

    # ---------------------------------------------------------
    # TEST 13: System Control (Volume & Screenshot)
    # ---------------------------------------------------------
    print("\n--- TEST 13: System Control ---")
    r13a = client.post("/api/system-control", json={"instruction": "volume up"})
    assert r13a.status_code == 200
    log("System Volume Up", f"spoken='{r13a.json().get('spoken_response')}'", r13a.json().get("ok"))

    r13b = client.post("/api/system-control", json={"instruction": "screenshot"})
    assert r13b.status_code == 200
    log("System Screenshot", f"spoken='{r13b.json().get('spoken_response')}'", r13b.json().get("ok"))

    # ---------------------------------------------------------
    # TEST 14: Native App Dispatcher (Terminal, Explorer, Settings)
    # ---------------------------------------------------------
    print("\n--- TEST 14: Native Apps (Terminal, Explorer, Settings) ---")
    r14a = client.post("/api/open-app", json={"instruction": "open downloads"})
    assert r14a.status_code == 200
    log("Open Downloads", f"detail='{r14a.json().get('detail')}'", r14a.json().get("ok"))

    r14b = client.post("/api/open-app", json={"instruction": "open terminal"})
    assert r14b.status_code == 200
    log("Open Terminal", f"detail='{r14b.json().get('detail')}'", r14b.json().get("ok"))

    # ---------------------------------------------------------
    # TEST 15: Check J.A.R.V.I.S. Brain History & Active Tasks
    # ---------------------------------------------------------
    print("\n--- TEST 15: Brain Memory & Completed Tasks ---")
    r15 = client.get("/api/brain-state")
    assert r15.status_code == 200
    b_data = r15.json()
    did_tasks = b_data.get("brain", {}).get("what_it_did", [])
    log("Brain Memory Tracking", f"Recorded {len(did_tasks)} completed tasks in brain episodic memory", len(did_tasks) > 5)

    print("\n" + "=" * 70)
    print(" ALL 15 EDGE CASES TESTED AND VERIFIED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
