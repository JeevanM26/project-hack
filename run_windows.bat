@echo off
title J.A.R.V.I.S. v12.0 SOTA GODMODE (Cross-Platform Hub)
cd /d "%~dp0"
echo ============================================================
echo   Starting J.A.R.V.I.S. Windows 11 RTX 5060 Edition
echo   OmniParser Set-of-Mark + 5-Agent Gemma 4 Swarm + Sentinel
echo ============================================================
start http://127.0.0.1:8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
