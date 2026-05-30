@echo off
title Fun With Arts - Django Backend Server
echo ===================================================
echo  Fun With Arts - Django Backend
echo ===================================================
echo.

:: Disable QuickEdit mode which freezes terminal when clicked
reg add "HKCU\Console" /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1

:: Navigate to backend directory
cd /d "C:\Users\stuti\OneDrive\Desktop\FunWithArts\backend"

echo [INFO] Working directory: %CD%
echo [INFO] Starting Django development server on http://127.0.0.1:8000/
echo [INFO] Press CTRL+C to stop the server.
echo.

:: Force Python output unbuffering with -u flag, --noreload avoids StatReloader subprocess
"C:\Users\stuti\OneDrive\Desktop\FunWithArts\.venv\Scripts\python.exe" -u manage.py runserver 127.0.0.1:8000 --noreload

echo.
echo [INFO] Server has stopped.
pause
