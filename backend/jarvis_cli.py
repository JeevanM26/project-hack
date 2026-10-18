#!/usr/bin/env python3
"""
=============================================================================
   J.A.R.V.I.S. - TERMINAL COMPANION OS (GEMMA 4 & SYSTEM KERNEL ACCESS)
=============================================================================
Autonomous AI Companion fitted directly into Windows Terminal / PowerShell.
Powered by Gemma 4, Multimodal Vision, SQLite Memory, and Direct Terminal Access.
"""

import os
import sys
import time
import subprocess
import threading
import json
from typing import Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import J.A.R.V.I.S. subsystems
try:
    from computer_use import execute_computer_use, stop_all_media, execute_terminal_command, download_any_resource
    from jarvis_memory import get_cognitive_brain_summary, record_episodic_memory, query_memory
    from jarvis_vision import scan_laptop_camera
except ImportError:
    try:
        from backend.computer_use import execute_computer_use, stop_all_media, execute_terminal_command, download_any_resource
        from backend.jarvis_memory import get_cognitive_brain_summary, record_episodic_memory, query_memory
        from backend.jarvis_vision import scan_laptop_camera
    except ImportError:
        execute_computer_use = None
        stop_all_media = None
        execute_terminal_command = None
        download_any_resource = None
        get_cognitive_brain_summary = None
        record_episodic_memory = None
        query_memory = None
        scan_laptop_camera = None
        get_cognitive_brain_summary = None
        record_episodic_memory = None
        query_memory = None
        scan_laptop_camera = None

# Windows SAPI TTS Engine
VOICE_ENGINE = None
try:
    import win32com.client
    VOICE_ENGINE = win32com.client.Dispatch("SAPI.SpVoice")
except Exception:
    pass

def speak(text: str, async_mode: bool = True):
    """Speaks text using native Windows speech synthesis."""
    if not VOICE_ENGINE or not text:
        return
    clean_text = text.replace("*", "").replace("`", "").strip()
    if async_mode:
        t = threading.Thread(target=lambda: VOICE_ENGINE.Speak(clean_text, 1), daemon=True)
        t.start()
    else:
        try:
            VOICE_ENGINE.Speak(clean_text, 1)
        except Exception:
            pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BANNER = f"""{CYAN}{BOLD}
       .---.            .---.
      /     \\          /     \\
     | () () |  J.A.R.V.I.S. | () () |    MARK VII NEURAL COMPANION
      \\     /    MARK VII     \\     /     Powered by Gemma 4 (Ollama)
       `---'                  `---'       Direct Windows Terminal Link
{RESET}{CYAN}
       +--------------------------------------------------------+
       |   [*] NEURAL ENGINE: GEMMA 4 (RTX GPU OFFLOAD: 92%)    |
       |   [*] OPTICAL SENSOR: HD WEBCAM (MOONDREAM VISION)     |
       |   [*] EPISODIC MEMORY: SQLITE jarvis_brain.db          |
       |   [*] TERMINAL ACCESS: ARMED & INTERACTIVE             |
       +--------------------------------------------------------+
{RESET}"""

def print_help():
    print(f"\n{BOLD}{CYAN}J.A.R.V.I.S. Terminal Directives & Commands:{RESET}")
    print(f"  {GREEN}<any prompt>{RESET}     Natural language directive for Gemma 4 (e.g. 'code a snake game', 'open youtube', 'open netflix')")
    print(f"  {YELLOW}:stop{RESET}            Instantly halts all media, audio, and YouTube sessions (<15ms)")
    print(f"  {YELLOW}:term <cmd>{RESET}      Directly executes shell/PowerShell command (e.g. ':term Get-Process')")
    print(f"  {YELLOW}:cam{RESET}             Captures optical webcam frame and runs local neural vision")
    print(f"  {YELLOW}:mem{RESET}             Recalls episodic memory from SQLite")
    print(f"  {YELLOW}:calc <expr>{RESET}     Direct UIA calculator execution")
    print(f"  {YELLOW}:help{RESET}            Display this help manual")
    print(f"  {YELLOW}:exit{RESET}            Exit J.A.R.V.I.S. terminal mode\n")

def run_cli():
    # Enable ANSI escape codes in Windows cmd/PowerShell
    os.system("")
    print(BANNER)
    
    welcome_msg = "At your service, sir. J.A.R.V.I.S. is fitted directly into your terminal with complete system access."
    print(f"{CYAN}{BOLD}J.A.R.V.I.S.:{RESET} {welcome_msg}")
    speak(welcome_msg)
    print(f"{DIM}Type your directive or ':help' for commands. Type ':stop' to halt all background audio.{RESET}\n")

    while True:
        try:
            prompt = input(f"{CYAN}{BOLD}JARVIS [Gemma 4] > {RESET}").strip()
            if not prompt:
                continue

            lower = prompt.lower()

            # 1. Exit
            if lower in [":exit", "exit", "quit", ":q"]:
                farewell = "Shutting down J.A.R.V.I.S. terminal interface. Have a productive day, sir."
                print(f"{CYAN}{farewell}{RESET}")
                speak(farewell, async_mode=False)
                break

            # 2. Help
            if lower in [":help", "help", "/help"]:
                print_help()
                continue

            # 3. Fast Stop
            if lower in [":stop", "stop", "stop all", "stop music", "pause", "mute", "quiet", "silence"]:
                print(f"{RED}{BOLD}[HALT OVERRIDE] Dispatching hardware media stop & muting browser audio sessions...{RESET}")
                if stop_all_media:
                    res = stop_all_media()
                    muted = res.get("muted_sessions", [])
                    print(f"{GREEN}[SUCCESS] {res.get('speech')}{RESET}")
                    if muted:
                        print(f"{DIM}Muted Audio Sessions: {', '.join(muted)}{RESET}")
                    speak(res.get("speech", "All audio stopped, sir."))
                continue

            # 4. Direct Terminal Command
            if prompt.startswith(":term ") or prompt.startswith("term ") or prompt.startswith("powershell "):
                cmd_to_run = prompt.split(" ", 1)[1].strip()
                print(f"{YELLOW}[POWERSHELL EXEC] Running: {cmd_to_run}{RESET}")
                if execute_terminal_command:
                    res = execute_terminal_command(cmd_to_run)
                    if res["stdout"]:
                        print(f"{GREEN}{res['stdout'].strip()}{RESET}")
                    if res["stderr"]:
                        print(f"{RED}{res['stderr'].strip()}{RESET}")
                    print(f"{DIM}[Exit Code: {res['exit_code']} | Duration: {res['duration_ms']}ms]{RESET}")
                    speak("Terminal command executed, sir.")
                continue

            # 4b. Direct Download Command
            if prompt.startswith(":dl ") or prompt.startswith(":download "):
                item = prompt.split(" ", 1)[1].strip()
                print(f"{CYAN}[DOWNLOAD SUBSYSTEM] Resolving dynamic download for: \"{item}\"...{RESET}")
                if download_any_resource:
                    dl_res = download_any_resource(item)
                    print(f"{GREEN}[SUCCESS] {dl_res.get('speech')}{RESET}")
                    if dl_res.get("saved_path"):
                        print(f"{CYAN}Direct Saved File: {dl_res['saved_path']}{RESET}")
                    elif dl_res.get("url"):
                        print(f"{CYAN}Target URL: {dl_res['url']}{RESET}")
                    speak(dl_res.get("speech", "Download initiated, sir."))
                continue

            # 5. Camera Scan
            if lower in [":cam", ":camera", "camera", "look at me"]:
                print(f"{CYAN}[OPTICAL SCAN] Engaging webcam array & Moondream neural vision...{RESET}")
                if scan_laptop_camera:
                    optic_res = scan_laptop_camera("Describe the person and room in detail")
                    analysis = optic_res.get("analysis", "Sensor active.")
                    print(f"{GREEN}{BOLD}Optical Observation:{RESET} {analysis}")
                    speak(f"Optical scan complete, sir. I observe: {analysis}")
                continue

            # 6. Memory Recall
            if lower in [":mem", ":memory", "memory", "what did you do"]:
                print(f"{MAGENTA}[COGNITIVE BRAIN] Querying SQLite episodic memories...{RESET}")
                if get_cognitive_brain_summary:
                    b = get_cognitive_brain_summary()
                    tasks = b.get("recent_tasks", [])
                    print(f"{BOLD}User: {b.get('user_profile', {}).get('name', 'Sir')}{RESET}")
                    print(f"Recent Memories ({len(tasks)} logged):")
                    for t in tasks[:5]:
                        print(f"  {MAGENTA}• [{t.get('tool_used') or t.get('action_name')}]{RESET} \"{t.get('user_prompt')}\" -> {DIM}{t.get('outcome_summary')}{RESET}")
                    speak(f"Recalled {len(tasks)} recent episodic memories, sir.")
                continue

            # 7. Gemma 4 Autonomous Computer-Use Dispatch
            print(f"{CYAN}[GEMMA 4 REASONING] Processing directive: \"{prompt}\"...{RESET}")
            t0 = time.perf_counter()
            if execute_computer_use:
                res = execute_computer_use(prompt)
                ms = round((time.perf_counter() - t0) * 1000, 1)

                if res and res.get("ok"):
                    action = res.get("action", "EXECUTED")
                    speech_txt = res.get("speech", "Directive completed, sir.")
                    print(f"\n{GREEN}{BOLD}[ACTION: {action}] ({ms}ms){RESET}")
                    if res.get("thought"):
                        print(f"{DIM}Thought: {res['thought']}{RESET}")
                    if res.get("url"):
                        print(f"{CYAN}Live Target URL: {res['url']}{RESET}")
                    if res.get("stdout"):
                        print(f"{GREEN}{res['stdout'].strip()}{RESET}")
                    if res.get("stderr"):
                        print(f"{RED}{res['stderr'].strip()}{RESET}")
                    print(f"{BOLD}J.A.R.V.I.S.:{RESET} \"{speech_txt}\"")
                    speak(speech_txt)
                else:
                    err = res.get("error", "Directive could not be completed.") if res else "No response from neural core."
                    print(f"{RED}[ERROR] {err}{RESET}")
                    speak("I encountered an issue executing that directive, sir.")
            else:
                print(f"{RED}Computer-use module not loaded.{RESET}")

            print()

        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}J.A.R.V.I.S. signing off. Have a pleasant day, sir.{RESET}")
            break
        except Exception as exc:
            print(f"{RED}[EXCEPTION] {exc}{RESET}")

if __name__ == "__main__":
    run_cli()
