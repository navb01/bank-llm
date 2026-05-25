@echo off
setlocal enabledelayedexpansion
title BankAssist AI - Setup Wizard
color 0B
echo.
echo  ============================================================
echo    BankAssist AI - First Time Setup Wizard
echo    Version 1.0 - Enterprise Ready
echo  ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found! 
  echo Please install Python 3.11+ from https://python.org
  echo Make sure to check "Add Python to PATH" during installation
  pause
  exit /b 1
)
echo [OK] Python found

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama not found!
  echo Please install from: https://ollama.ai/download
  pause
  exit /b 1
)
echo [OK] Ollama found

REM Optional: Tesseract OCR
echo.
echo  [INFO] OCR Setup for Scanned PDFs
echo  ============================================================
echo  To support scanned PDFs, install Tesseract-OCR (optional):
echo  https://github.com/UB-Mannheim/tesseract/wiki
echo.
pause /? >nul 2>&1 && (
  set /p ocr_msg="Press Enter to continue (Tesseract is optional): "
)

echo.
echo  [STEP 1/4] Upgrading pip...
cd /d "%~dp0backend"
python -m pip install --upgrade pip
if errorlevel 1 echo [WARNING] pip upgrade had issues, continuing anyway

echo.
echo  [STEP 2/4] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Failed to install packages!
  pause
  exit /b 1
)
echo [OK] Packages installed

echo.
echo  [STEP 3/4] Pulling LLM model: llama3.2 (~2GB)
echo  This may take 10-20 minutes on first run...
ollama pull llama3.2
if errorlevel 1 (
  echo [WARNING] Failed to pull llama3.2
  echo Try manually: ollama pull llama3.2
  pause
)

echo.
echo  [STEP 4/4] Pulling embedding model: nomic-embed-text
ollama pull nomic-embed-text
if errorlevel 1 (
  echo [WARNING] Failed to pull nomic-embed-text
  echo Try manually: ollama pull nomic-embed-text
  pause
)

echo.
echo  ============================================================
echo    ✓ Setup Complete!
echo  ============================================================
echo.
echo  Next Steps:
echo  1. Double-click start.bat to launch the server
echo  2. Server will be available at: http://localhost:8000
echo  3. Admin panel: http://localhost:8000/admin
echo  4. Upload your bank circulars via the admin panel
echo  5. Ask questions via the chat interface
echo.
pause

