# J.A.R.V.I.S. Unified Cross-Platform AI Operating System
### 🍏 macOS (Apple Silicon M-Series Edition) • 🪟 Windows 11 (RTX 5060 Edition)

[![J.A.R.V.I.S. Godmode](https://img.shields.io/badge/J.A.R.V.I.S.-v12.0_GODMODE-amber.svg)](https://github.com/JeevanM26/project-hack)
[![Platforms](https://img.shields.io/badge/Platforms-macOS_%7C_Windows_11-blue.svg)](https://github.com/JeevanM26/project-hack)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

An agentic, multi-modal, cross-platform AI operating assistant designed for developer hackathons and daily desktop automation.

---

## 🚀 Quick Setup & Run (macOS First)

### 🍏 On macOS (Apple Silicon M-Series / Intel)
1. Open Terminal in this repository:
   ```bash
   chmod +x run_mac.sh
   ./run_mac.sh
   ```
   *Or directly inside `mac/`:*
   ```bash
   cd mac
   chmod +x run.sh
   ./run.sh
   ```
2. Open your browser to:
   ```
   http://localhost:8000
   ```
3. Run the automated integration test suite:
   ```bash
   python3 mac/test_app.py
   ```

---

### 🪟 On Windows 11
1. Double-click **`run_windows.bat`** (or open PowerShell):
   ```bash
   pip install -r windows/requirements.txt
   .\run_windows.bat
   ```
   *Or:*
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
2. Open your browser to:
   ```
   http://127.0.0.1:8000
   ```

---

## 📂 Cross-Platform Architecture

```
project-hack/
├── mac/                         # 🍏 macOS Apple Silicon M-Series Edition
│   ├── main.py                  # FastAPI server, Faster-Whisper, AppleScript osascript
│   ├── index.html               # Arc Reactor HUD with Web Audio visualizer
│   ├── test_app.py              # 17-point automated integration test suite
│   ├── bro                      # J.A.R.V.I.S. CLI Command Terminal Bridge
│   ├── requirements.txt         # macOS dependencies (faster-whisper, etc.)
│   ├── run.sh                   # macOS bash launcher
│   ├── PATTERN.md               # System architectural specification
│   ├── NOTES.md                 # Development & failure mode logs
│   ├── memory.ses               # Session state token
│   └── README.md                # macOS edition documentation
│
├── windows/                     # 🪟 Windows 11 RTX 5060 SOTA Godmode Hub
│   ├── backend/main.py          # FastAPI server, OmniParser SoM, 5-Agent Swarm, Sentinel
│   ├── index.html               # Avengers 3D Three.js holographic command center
│   ├── hackathon_app/           # Dynamic code synthesis workspace
│   ├── requirements.txt         # Windows dependencies (pywinauto, pyautogui, etc.)
│   ├── run_windows.bat          # One-click Windows batch launcher
│   └── run.py                   # Python launcher for Windows
│
├── run_mac.sh                   # 🍏 Root launcher for macOS
├── run_windows.bat              # 🪟 Root launcher for Windows
└── README.md                    # Master cross-platform documentation
```

---

## ⚡ Feature Comparison Matrix

| Feature | macOS Edition (`mac/`) | Windows 11 Edition (`windows/`) |
| :--- | :--- | :--- |
| **Visual Cortex** | Holographic Optical Scanline Overlay | OmniParser v2 + UI-TARS Set-of-Mark (#1, #2 tags) |
| **Speech Engine** | Local Faster-Whisper + Web Speech API | Sarvam AI Multilingual (`en-IN`, `hi-IN`, `kn-IN`) + SAPI5 |
| **Desktop Automation** | Native AppleScript `osascript`, `open -a`, Spotlight | Native Win32 UIA, `pyautogui`, `os.startfile` |
| **Code Supervisor** | 3-Tier Multi-Model Cascade (Local Gemma + Gemini) | **Autonomous Anti-Hallucination Sentinel** (AST + Auto-Heal) |
| **Code Synthesis** | Automated scaffold generator & IDE bridge | Dynamic 5-Agent Swarm with fresh bespoke generators |
| **Audio Playback** | Embedded HUD YouTube player + Spotify | OS-level media keys + YouTube physical tab player |
| **Verification Suite**| 17-point automated test suite (`test_app.py`) | **Live Notepad Mistake & Auto-Heal Demonstration** |

---

## 🍏 macOS Highlights (Apple Silicon M-Series)

1. **Local Faster-Whisper Transcription**:
   - Zero-latency, on-device audio speech-to-text running directly on Apple Silicon Neural Engine.
2. **AppleScript & Spotlight Automation**:
   - Control macOS volume via `osascript`, search files with Spotlight `mdfind` and reveal directly in Finder.
3. **Interactive Arc Reactor HUD**:
   - Live Web Audio API frequency visualizer reacting in real time to microphone input.
4. **J.A.R.V.I.S. CLI Bridge (`bro` / `jarvis`)**:
   - Execute commands directly from the macOS terminal without opening a browser.
5. **17-Point Automated Test Suite**:
   - Run `python3 mac/test_app.py` to verify all chat endpoints, system scans, calculator integrations, and media players.

---

## 🪟 Windows 11 Highlights: Autonomous Anti-Hallucination Sentinel

1. **Continuous Output Observation**: Monitors workspace code (`.py`, `.html`, `.js`), compiler outputs, and live browser console logs.
2. **Deterministic AST Grounding**: Extracts deterministic symbol tables to catch hallucinated methods or undefined references.
3. **Real-Time Self-Correction (Auto-Healing)**: Automatically patches broken code, missing DOM bindings, and unhandled logic errors on the fly.
4. **Live Notepad Mistake Demo**: Launch Notepad, inject intentional typos/hallucinations, and watch J.A.R.V.I.S. detect and auto-heal them on screen in real time!
5. **Fresh Calculator Generator**: Dynamically crafts bespoke calculators tailored to your prompt (Cyberpunk Matrix, Cosmic Violet, Obsidian Dark) with unique build IDs.
