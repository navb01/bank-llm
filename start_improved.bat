@echo off
setlocal enabledelayedexpansion
title BankAssist AI - Server
color 0A
cls
echo.
echo  ============================================================
echo    BankAssist AI - Enterprise Bank Circular Intelligence
echo    Version 1.0
echo  ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found
    echo  Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Ollama not found!
    echo  1. Install from: https://ollama.ai/download
    echo  2. Run: ollama pull llama3.2
    echo  3. Run: ollama pull nomic-embed-text
    echo  4. Run this script again
    pause
    exit /b 1
)

REM Get local IP for LAN access
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set SERVER_IP=%%a
    goto found
)
:found
set SERVER_IP=%SERVER_IP: =%

if "!SERVER_IP!"=="" set SERVER_IP=192.168.x.x

echo  [STEP 1/3] Ensuring dependencies...
cd /d "%~dp0backend"
pip install -q -r requirements.txt 2>nul
if errorlevel 1 (
    echo  [WARNING] Failed to install dependencies silently
    echo  Attempting verbose install...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  [ERROR] Dependency install failed
        pause
        exit /b 1
    )
)

echo  [STEP 2/3] Checking Ollama models...
ollama list >nul 2>&1
echo  [OK] Ollama connectivity verified

echo.
echo  [STEP 3/3] Launching BankAssist Server...
echo.
echo  ============================================================
echo    Server Status
echo  ============================================================
echo.
echo    🌐 Chat Interface:   http://localhost:8000
echo    ⚙️  Admin Panel:      http://localhost:8000/admin
echo    🔗 LAN Access:       http://!SERVER_IP!:8000
echo.
echo    API Documentation:  http://localhost:8000/docs
echo.
echo    📁 Vector DB:        ./vector_db
echo    📂 Documents:        ./circulars
echo    📊 Logs:             ./logs
echo.
echo  ============================================================
echo.
echo    Press Ctrl+C to stop the server
echo.

python main.py

echo.
echo  Server stopped.
pause
