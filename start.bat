@echo off
title TruthLens — Fake News Detector
color 0A
echo.
echo  ████████╗██████╗ ██╗   ██╗████████╗██╗  ██╗
echo     ██╔══╝██╔══██╗██║   ██║╚══██╔══╝██║  ██║
echo     ██║   ██████╔╝██║   ██║   ██║   ███████║
echo     ██║   ██╔══██╗██║   ██║   ██║   ██╔══██║
echo     ██║   ██║  ██║╚██████╔╝   ██║   ██║  ██║
echo     ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
echo.
echo  [*] Starting TruthLens Fake News Detector...
echo.

:: Start Backend
echo  [1/2] Starting Python Backend (FastAPI)...
start "TruthLens Backend" cmd /k "cd /d "%~dp0backend" && uvicorn main:app --reload --port 8000"

:: Wait for backend to initialize
timeout /t 3 /nobreak > nul

:: Start Frontend
echo  [2/2] Starting Frontend Server...
start "TruthLens Frontend" cmd /k "cd /d "%~dp0frontend" && python -m http.server 5000"

:: Wait a moment then open browser
timeout /t 2 /nobreak > nul

echo.
echo  [✓] Both servers are running!
echo  [✓] Opening browser...
echo.
echo  Backend API : http://127.0.0.1:8000
echo  Frontend UI : http://localhost:5000
echo.

start http://localhost:5000

echo  Press any key to stop all servers and exit...
pause > nul

:: Kill servers when done
taskkill /FI "WindowTitle eq TruthLens Backend*" /F > nul 2>&1
taskkill /FI "WindowTitle eq TruthLens Frontend*" /F > nul 2>&1
echo  [✓] Servers stopped. Goodbye!
timeout /t 2 /nobreak > nul
