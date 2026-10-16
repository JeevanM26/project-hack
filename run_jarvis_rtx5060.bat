@echo off
title J.A.R.V.I.S. Core Launcher (NVIDIA RTX 5060 + 24GB RAM)
color 0b

echo =====================================================================
echo    J.A.R.V.I.S. - Gemma 4 Dynamic Swarm & Sarvam Voice OS
echo    Hardware Target: NVIDIA GeForce RTX 5060 (8GB VRAM) + 24GB RAM
echo    Optimal Model: gemma-4-12B-it (Local GPU Offload: 92%%)
echo =====================================================================
echo.

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo     Please install Python 3.11 via Microsoft Store or python.org.
    echo.
    echo [i] You can still open index.html directly in your browser to use
    echo     the complete 3D interactive interface with Web Speech simulation!
    echo.
    pause
    start "" "index.html"
    exit /b
)

:: Set environment variables
set JARVIS_GEMMA_MODEL=gemma-4-12b-it
set OLLAMA_NUM_GPU=36
set OLLAMA_CONTEXT_SIZE=8192

:: Launch backend
echo [*] Starting FastAPI Multi-Agent Swarm Backend on http://localhost:8000 ...
cd backend
start "J.A.R.V.I.S. Backend Server" uvicorn main:app --reload --port 8000

:: Open frontend
echo [*] Opening 3D Holographic Command Center in default browser ...
timeout /t 2 >nul
start "" "..\index.html"

echo.
echo [OK] J.A.R.V.I.S. Swarm is active! Press any key to stop this console.
pause
