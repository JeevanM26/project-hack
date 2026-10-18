#!/usr/bin/env python3
"""
J.A.R.V.I.S. Windows 11 Godmode Launcher
Launches FastAPI backend on port 8000 and opens default browser to J.A.R.V.I.S. Command Center.
"""
import os
import sys
import time
import subprocess
import webbrowser

def main():
    print("=" * 60)
    print("  J.A.R.V.I.S. v12.0 SOTA GODMODE — WINDOWS 11 EDITION")
    print("  OmniParser SoM + 5-Agent Gemma 4 Swarm + Anti-Hallucination")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Launch uvicorn
    print("\n[+] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    server_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]
    proc = subprocess.Popen(server_cmd)
    
    time.sleep(1.8)
    print("[+] Launching J.A.R.V.I.S. Command Center in default browser ...")
    if hasattr(os, "startfile"):
        try:
            os.startfile("http://127.0.0.1:8000")
        except Exception:
            webbrowser.open("http://127.0.0.1:8000")
    else:
        webbrowser.open("http://127.0.0.1:8000")
        
    print("\n[✓] J.A.R.V.I.S. is LIVE! Press Ctrl+C in this terminal to stop.\n")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[!] Shutting down J.A.R.V.I.S. ...")
        proc.terminate()

if __name__ == "__main__":
    main()
