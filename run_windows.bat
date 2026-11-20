@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Northstar FP^&A - launcher

echo ============================================
echo  Northstar FP^&A - one-click launcher
echo ============================================
echo.

REM --- 1. Check source data -------------------------------------------------
set "MISSING_DATA="
for %%F in (train.csv test.csv features.csv stores.csv) do (
  if not exist "data\raw\%%F" set "MISSING_DATA=!MISSING_DATA! %%F"
)
if defined MISSING_DATA (
  echo ERROR: Missing dataset file^(s^):!MISSING_DATA!
  echo Put train.csv, test.csv, features.csv and stores.csv in:
  echo   %CD%\data\raw
  echo See START_HERE.md for download instructions.
  goto :fail
)
echo [OK] Dataset files found.
echo.

REM --- 2. Create or reuse the Python environment ----------------------------
where py >nul 2>nul
if not errorlevel 1 (
  set "PY_CMD=py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python was not found. Install Python 3.10+ from https://www.python.org
    goto :fail
  )
  set "PY_CMD=python"
)

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Creating Python virtual environment...
  "%PY_CMD%" -m venv .venv
  if errorlevel 1 goto :fail
)
if not exist "%PY%" (
  echo ERROR: Virtual environment was created but %PY% is missing.
  goto :fail
)
echo [OK] Python environment: %PY%
echo.

REM --- 3. Install Python dependencies only when needed ----------------------
set "NEED_PY_INSTALL="
if not exist ".venv\.requirements.txt" set "NEED_PY_INSTALL=1"
if not defined NEED_PY_INSTALL (
  fc /b "requirements.txt" ".venv\.requirements.txt" >nul
  if errorlevel 1 set "NEED_PY_INSTALL=1"
)
if not defined NEED_PY_INSTALL (
  "%PY%" -c "import pandas, numpy, sklearn, matplotlib, seaborn, jupyterlab, ipykernel, pytest" >nul 2>nul
  if errorlevel 1 set "NEED_PY_INSTALL=1"
)
if defined NEED_PY_INSTALL (
  echo Installing Python dependencies...
  "%PY%" -m pip install --upgrade pip
  if errorlevel 1 goto :fail
  "%PY%" -m pip install -r "requirements.txt"
  if errorlevel 1 goto :fail
  copy /y "requirements.txt" ".venv\.requirements.txt" >nul
  if errorlevel 1 goto :fail
) else (
  echo [OK] Python dependencies already installed.
)
echo.

REM --- 4. Run the analysis pipeline -----------------------------------------
echo Running the analysis pipeline. This can take about a minute...
"%PY%" "run_analysis.py"
if errorlevel 1 goto :fail
if not exist "frontend\public\data\financial_plan.json" (
  echo ERROR: Analysis finished but frontend\public\data\financial_plan.json is missing.
  goto :fail
)
echo [OK] Dashboard data generated.
echo.

REM --- 5. Check Node.js and npm ---------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js was not found. Install Node 20+ from https://nodejs.org
  goto :fail
)
where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm was not found. Reinstall Node.js from https://nodejs.org
  goto :fail
)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 20 ? 0 : 1)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 20 or later is required. Found:
  node --version
  goto :fail
)
echo [OK] Node.js and npm found.
echo.

REM --- 6. Install frontend dependencies only when needed --------------------
set "NPM_STAMP=frontend\node_modules\.northstar-package-lock.json"
set "NEED_NPM_INSTALL="
if not exist "frontend\node_modules\.bin\vite.cmd" set "NEED_NPM_INSTALL=1"
if not exist "%NPM_STAMP%" set "NEED_NPM_INSTALL=1"
if not defined NEED_NPM_INSTALL (
  fc /b "frontend\package-lock.json" "%NPM_STAMP%" >nul
  if errorlevel 1 set "NEED_NPM_INSTALL=1"
)
if defined NEED_NPM_INSTALL (
  echo Installing frontend dependencies...
  pushd frontend
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    popd
    goto :fail
  )
  popd
  copy /y "frontend\package-lock.json" "%NPM_STAMP%" >nul
  if errorlevel 1 goto :fail
) else (
  echo [OK] Frontend dependencies already installed.
)
echo.

REM --- 7. Start the dashboard on a free port --------------------------------
set "PORT="
for /f "delims=" %%P in ('powershell -NoProfile -Command "$p=5173; while ((Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue)) { $p++ }; $p"') do set "PORT=%%P"
if not defined PORT set "PORT=5173"

echo Starting the dashboard at http://localhost:%PORT%
echo Keep this window open. Press Ctrl+C to stop the server.
echo.

REM Open the browser only after Vite answers successfully.
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='http://localhost:%PORT%'; for ($i=0; $i -lt 40; $i++) { try { if ((Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 1 -ErrorAction Stop).StatusCode -eq 200) { Start-Process $u; break } } catch { }; Start-Sleep -Milliseconds 500 }"

pushd frontend
call npm run dev -- --port %PORT% --strictPort
set "NPM_EXIT=!ERRORLEVEL!"
popd
if not "!NPM_EXIT!"=="0" goto :fail
exit /b 0

:fail
echo.
echo Startup failed. Read the message above and see START_HERE.md.
echo.
pause
exit /b 1
