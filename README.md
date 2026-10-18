# J.A.R.V.I.S. Unified Cross-Platform AI Operating System
### SOTA Windows 11 (RTX 5060 Edition) • macOS (Apple Silicon M-Series Edition)

[![J.A.R.V.I.S. Godmode](https://img.shields.io/badge/J.A.R.V.I.S.-v12.0_GODMODE-amber.svg)](https://github.com/JeevanM26/project-hack)
[![Platforms](https://img.shields.io/badge/Platforms-Windows_11_%7C_macOS-blue.svg)](https://github.com/JeevanM26/project-hack)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

An agentic, multi-modal, cross-platform AI operating assistant designed for developer hackathons and daily desktop automation.

---

## 📂 Cross-Platform Architecture

```
project-hack/
├── windows/                     # 🪟 Windows 11 RTX 5060 SOTA Godmode Hub
│   ├── backend/main.py          # FastAPI server, OmniParser SoM, 5-Agent Swarm, Sentinel
│   ├── index.html               # Avengers 3D Three.js holographic command center
│   ├── hackathon_app/           # Dynamic code synthesis workspace
│   ├── requirements.txt         # Windows dependencies (pywinauto, pyautogui, etc.)
│   ├── run_windows.bat          # One-click Windows batch launcher
│   └── run.py                   # Python launcher for Windows
│
├── mac/                         # 🍏 macOS Apple Silicon M-Series Edition
│   ├── main.py                  # FastAPI server, Faster-Whisper, AppleScript osascript
│   ├── index.html               # Arc Reactor HUD with Web Audio visualizer
│   ├── test_app.py              # 17-point automated integration test suite
│   ├── bro                      # J.A.R.V.I.S. CLI Command Terminal Bridge
│   ├── requirements.txt         # macOS dependencies (faster-whisper, etc.)
│   ├── run.sh                   # macOS bash launcher
│   ├── PATTERN.md               # System architectural specification
│   └── NOTES.md                 # Development & failure mode logs
│
├── run_windows.bat              # Root launcher for Windows
├── run_mac.sh                   # Root launcher for macOS
└── README.md                    # Master cross-platform documentation
```

---

## ⚡ Feature Comparison Matrix

| Feature | Windows 11 Edition (`windows/`) | macOS Edition (`mac/`) |
| :--- | :--- | :--- |
| **Visual Cortex** | OmniParser v2 + UI-TARS Set-of-Mark (#1, #2 tags) | Holographic Optical Scanline Overlay |
| **Code Supervisor** | **Autonomous Anti-Hallucination Sentinel** (AST + Auto-Heal) | 3-Tier Multi-Model Cascade (Local Gemma + Gemini) |
| **Code Synthesis** | Dynamic 5-Agent Swarm with fresh bespoke generators | Automated scaffold generator & IDE bridge |
| **Desktop Automation** | Native Win32 UIA, `pyautogui`, `os.startfile` | Native AppleScript `osascript`, `open -a`, Spotlight |
| **Speech Engine** | Sarvam AI Multilingual (`en-IN`, `hi-IN`, `kn-IN`) + SAPI5 | Local Faster-Whisper + Web Speech API |
| **Audio Playback** | OS-level media keys + YouTube physical tab player | Embedded HUD YouTube player + Spotify |
| **Live Error Demo** | **Live Notepad Mistake & Auto-Heal Demonstration** | 17-point integration test suite |

---

## 🚀 How to Run

### On Windows 11
1. Open PowerShell / Command Prompt in this folder.
2. Install dependencies:
   ```bash
   pip install -r windows/requirements.txt
   ```
3. Run J.A.R.V.I.S.:
   ```bash
   .\run_windows.bat
   ```
   *Or:*
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
4. Navigate to `http://127.0.0.1:8000` in your browser.

---

### On macOS (Apple Silicon / Intel)
1. Open Terminal in this folder.
2. Make scripts executable and run:
   ```bash
   chmod +x run_mac.sh
   ./run_mac.sh
   ```
   *Or navigate to `mac/`:*
   ```bash
   cd mac
   chmod +x run.sh
   ./run.sh
   ```
3. Navigate to `http://localhost:8000` in your browser.

---

## 🛡️ Hackathon Highlights: Solving AI Hallucinations

J.A.R.V.I.S. introduces the **Autonomous Anti-Hallucination Sentinel**:
- **Continuous Output Observation**: Monitors workspace code (`.py`, `.html`, `.js`), compiler outputs, and live browser console logs.
- **Deterministic AST Grounding**: Extracts deterministic symbol tables to catch hallucinated methods or undefined references.
- **Real-Time Self-Correction (Auto-Healing)**: Automatically patches broken code, missing DOM bindings, and unhandled logic errors on the fly.
- **Automated Headless Smoke Tests**: Spawns headless Playwright Chromium to verify DOM rendering and zero console errors before handing over the project.
- **Audible SAPI5 Confirmation**: Announces verbally through speakers when the code is verified 100% functional.
