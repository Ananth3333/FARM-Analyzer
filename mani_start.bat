@echo off
title MANI EDGE COMPLETE WORKSPACE CONSOLE
echo =======================================================
echo   STARTING ALL MANI EDGE SERVERS AND HARDWARE SIMULATORS
echo =======================================================
echo.

:: 1. Force clear hanging network port blocks from previous runs
taskkill /f /im uvicorn.exe >nul 2>&1

:: 2. Launch the Core Web Host Platform Server
echo [SYSTEM] Launching Dashboard Web platform Server (Port 8000)...
start cmd /k "cd /d "%USERPROFILE%\Desktop\Mani_Platform" && call venv\Scripts\activate && title MANI WEB DASHBOARD && uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 2 >nul

:: 3. Launch the Automated Real-Time Live Data Stream Simulator
echo [SYSTEM] Launching Telemetry Data Stream Simulator...
start cmd /k "cd /d "%USERPROFILE%\Desktop\Mani_Platform" && call venv\Scripts\activate && title MANI DATA SIMULATOR && python mani_simulator.py"

echo.
echo =======================================================
echo   WORK ENVIRONMENT OPERATIONAL! MINIMIZE THIS SYSTEM WINDOW.
echo   Open Browser to: http://localhost:8000
echo =======================================================
pause
