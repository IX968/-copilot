@echo off
title Global AI Copilot

echo.
echo ========================================
echo   Global AI Copilot Launcher
echo ========================================
echo.

REM Set project root as PYTHONPATH
set PYTHONPATH=%~dp0
cd /d %~dp0

REM Check Conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Conda not found. Please install Anaconda or Miniconda.
    pause
    exit /b 1
)

REM Activate Conda env (pytorch_python11 has CUDA torch + exllamav3)
call conda activate pytorch_python11 2>nul
if %errorlevel% neq 0 (
    echo [WARN] Conda env 'pytorch_python11' not found, using current Python.
)

REM Check dependencies
echo [CHECK] Verifying dependencies...
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Installing web dependencies...
    pip install -r requirements-web.txt
)

echo.
echo ========================================
echo   Starting Services
echo ========================================
echo.

REM Kill any leftover process on port 7891 before starting
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":7891 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>nul
)

REM Step 1: Start API server (background, /k keeps window open on crash)
echo [1/2] Starting API server (port 7891)...
start "AI Copilot API" cmd /k "python -m uvicorn backend.api.server:app --host 127.0.0.1 --port 7891 --log-level info"

REM Wait for API server ready (max 15s, retry every second)
echo [WAIT] Waiting for API server...
set RETRY=0
:WAIT_LOOP
timeout /t 1 /nobreak >nul
set /a RETRY+=1
python -c "import requests; requests.get('http://127.0.0.1:7891/api/health', timeout=1)" 2>nul
if %errorlevel% equ 0 goto API_READY
if %RETRY% lss 15 goto WAIT_LOOP
echo [ERROR] API server failed to start after 15s. Check logs.
pause
exit /b 1
:API_READY

echo [OK] API server is running.
echo.

REM Step 2: Start desktop service
echo [2/2] Starting desktop completion service...
echo.
echo   Web Console: http://127.0.0.1:7891
echo   Tab = accept, Esc = reject
echo.

python desktop/service.py

REM Cleanup: kill API server when desktop service exits
echo.
echo [CLEANUP] Shutting down API server...
taskkill /FI "WINDOWTITLE eq AI Copilot API*" /T /F >nul 2>nul

echo.
echo ========================================
echo   Exited
echo ========================================
pause
