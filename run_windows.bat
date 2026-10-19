@echo off
title J.A.R.V.I.S. v12.0 SOTA GODMODE (Windows 11)
cd /d "%~dp0"
python run.py
if errorlevel 1 (
    echo.
    echo [!] Python returned an error code. Trying direct uvicorn start...
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
)
pause
