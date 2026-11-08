@echo off
setlocal
title Programming Tutor Launcher

set "ROOT=%~dp0"

echo ============================================================
echo  Programming Tutor - starting all services
echo  Root: %ROOT%
echo ============================================================
echo.

REM ============ 1. Python agent service (port 8000) ============
if not exist "%ROOT%agent-service\.venv\Scripts\python.exe" (
    echo [init] Creating Python venv and installing dependencies...
    pushd "%ROOT%agent-service"
    python -m venv .venv 2>nul
    if not exist ".venv\Scripts\python.exe" (
        py -3 -m venv .venv
    )
    if not exist ".venv\Scripts\python.exe" (
        echo [ERROR] Failed to create venv. Please install Python 3.10 or newer.
        popd
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    popd
    echo [init] Python environment ready.
    echo.
)

if not exist "%ROOT%agent-service\.env" (
    echo [ERROR] agent-service\.env not found. Please configure it first.
    pause
    exit /b 1
)

cd /d "%ROOT%agent-service"
start "AgentService-8000" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

REM ============ 2. Go backend (port 8080) ============
cd /d "%ROOT%"
start "GoBackend-8080" cmd /k "go run ./backend/cmd/server"

REM ============ 3. Frontend (port 5173) ============
cd /d "%ROOT%frontend"
start "Frontend-5173" cmd /k "npm run dev"

cd /d "%ROOT%"

echo.
echo All services started in separate windows:
echo   Agent service : http://localhost:8000/docs
echo   Go backend    : http://localhost:8080
echo   Frontend      : http://localhost:5173
echo.
echo How to test:
echo   1. Open http://localhost:5173 and log in
echo   2. Open a problem and submit WRONG Go code on purpose
echo   3. The AI diagnosis panel appears below the result
echo.
echo Stop: close the corresponding windows.
echo.
pause
