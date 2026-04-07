@echo off
echo Stopping any existing backend server on port 8001...

REM Find and kill process using port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo Killing process %%a
    taskkill /PID %%a /F
)

timeout /t 2 /nobreak >nul

echo Starting backend server...
python start.py
