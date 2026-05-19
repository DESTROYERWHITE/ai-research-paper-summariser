@echo off
setlocal
cd /d "%~dp0"
title AI Research Paper Summariser

echo.
echo ===============================================
echo   AI Research Paper Summariser
echo ===============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11+ and run this launcher again.
  pause
  exit /b 1
)

if not exist "backend\.env" (
  copy "backend\.env.example" "backend\.env" >nul
  echo Created backend\.env from backend\.env.example.
  echo Add ANTHROPIC_API_KEY there when you want live Claude summaries.
  echo.
)

python -c "import fastapi, uvicorn, httpx, docx, dotenv, pydantic_settings" >nul 2>nul
if errorlevel 1 (
  echo Installing backend dependencies...
  python -m pip install -r "backend\requirements.txt"
  if errorlevel 1 (
    echo Dependency install failed. Check your Python and internet connection.
    pause
    exit /b 1
  )
)

echo Starting local app...
echo Browser URL: http://127.0.0.1:8000
echo Close this window to stop the app.
echo.

start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo App stopped.
pause
