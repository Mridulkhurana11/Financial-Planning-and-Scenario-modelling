@echo off
setlocal
cd /d "%~dp0frontend"

where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js / npm was not found. Install Node 20+ from https://nodejs.org
  pause
  exit /b 1
)

if not exist node_modules (
  echo Installing frontend dependencies - first run only...
  call npm install
  if errorlevel 1 (
    pause
    exit /b 1
  )
)

if not exist public\data\financial_plan.json (
  echo Dashboard data is missing. Run run_windows.bat or:
  echo   .venv\Scripts\python.exe run_analysis.py
  echo from the project root first.
  pause
  exit /b 1
)

echo Starting the dashboard - use the exact URL Vite prints below.
echo Keep this window open. Press Ctrl+C to stop the server.
echo.
call npm run dev
