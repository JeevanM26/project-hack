@echo off
title J.A.R.V.I.S. v12.0 SOTA GODMODE (Windows Edition)
cd /d "%~dp0"
echo ============================================================
echo   J.A.R.V.I.S. v12.0 SOTA GODMODE (Windows 11 RTX 5060)
echo   OmniParser Set-of-Mark + 5-Agent Gemma 4 Swarm + Sentinel
echo ============================================================
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
