#!/usr/bin/env python3
"""
J.A.R.V.I.S. v12.0 SOTA GODMODE — Master Launcher
Starts Ollama (if available), launches FastAPI backend on port 8000,
waits for health check, and opens J.A.R.V.I.S. Command Center in default browser.
"""
import os
import sys
import time
import subprocess
import webbrowser
import urllib.request

def main():
    print("=" * 65)
    print("  J.A.R.V.I.S. v12.0 SOTA GODMODE — WINDOWS 11 EDITION")
    print("  OmniParser SoM + 5-Agent Swarm + Anti-Hallucination Sentinel")
    print("=" * 65)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 1. Start Ollama in background if portable winget package exists and not running
    ollama_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ollama.Ollama.Portable_Microsoft.Winget.Source_8wekyb3d8bbwe\ollama.exe")
    if os.path.exists(ollama_path):
        try:
            # Check if ollama already running
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.8) as _:
                pass
            print("[✓] Ollama server is already running.")
        except Exception:
            print("[+] Starting Ollama server in background...")
            subprocess.Popen([ollama_path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)

    # 2. Launch FastAPI / Uvicorn server on port 8000
    print("\n[+] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    server_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]
    proc = subprocess.Popen(server_cmd)
    
    # 3. Wait for backend to be fully healthy before launching browser
    print("[+] Waiting for backend initialization...")
    backend_ready = False
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1.0) as resp:
                if resp.status == 200:
                    backend_ready = True
                    break
        except Exception:
            time.sleep(0.3)
    
    if backend_ready:
        print("[✓] Backend is healthy and ready!")
    else:
        print("[!] Backend is initializing; proceeding to launch browser...")

    # 4. Open J.A.R.V.I.S. Command Center
    print("[+] Launching J.A.R.V.I.S. Command Center in default browser ...")
    target_url = "http://127.0.0.1:8000"
    if hasattr(os, "startfile"):
        try:
            os.startfile(target_url)
        except Exception:
            webbrowser.open(target_url)
    else:
        webbrowser.open(target_url)
        
    print("\n" + "=" * 65)
    print("  [✓] J.A.R.V.I.S. IS LIVE AT http://127.0.0.1:8000")
    print("  Press Ctrl+C in this terminal window to stop the server.")
    print("=" * 65 + "\n")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[!] Shutting down J.A.R.V.I.S. server...")
        proc.terminate()

if __name__ == "__main__":
    main()
