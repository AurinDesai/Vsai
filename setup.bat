@echo off
REM CodeForge Studio - Complete Setup Script
REM Run this ONCE to install all dependencies

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ======================================================================
echo   CodeForge Studio - Complete Setup
echo ======================================================================
echo.

REM Check Node.js
echo [1/3] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Node.js not found!
    echo.
    echo   Please install Node.js from: https://nodejs.org/
    echo   Download the LTS version and run the installer.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo   [OK] Node.js %NODE_VERSION% found
echo.

REM Check Python
echo [2/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Python not found (optional for AI features)
) else (
    for /f "tokens=2" %%i in ('python --version') do set PY_VERSION=%%i
    echo   [OK] Python !PY_VERSION! found
)
echo.

REM Install npm packages
echo [3/3] Installing dependencies...
echo   This may take a few minutes...
echo.

REM Remove old node_modules to prevent conflicts
if exist node_modules (
    echo   Cleaning old installation...
    rmdir /s /q node_modules 2>nul
)

REM Install packages
npm install express cors multer axios

if errorlevel 1 (
    echo.
    echo   [ERROR] npm install failed!
    echo.
    echo   Troubleshooting:
    echo   1. Check your internet connection
    echo   2. Try running as Administrator
    echo   3. Delete node_modules and try again
    echo.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   [SUCCESS] Setup Complete!
echo ======================================================================
echo.
echo   Installed packages:
npm list --depth=0 2>nul

REM Create workspace folder
if not exist workspace (
    mkdir workspace
    echo.
    echo   [OK] Created workspace/ folder
)

REM Create a sample file in workspace
if not exist workspace\README.txt (
    echo Welcome to CodeForge Studio! > workspace\README.txt
    echo. >> workspace\README.txt
    echo Your code files will be saved here in the workspace folder. >> workspace\README.txt
    echo. >> workspace\README.txt
    echo Quick Start: >> workspace\README.txt
    echo 1. Run: python launcher.py >> workspace\README.txt
    echo 2. Set auth token to: localdev >> workspace\README.txt
    echo 3. Start coding! >> workspace\README.txt
    
    echo   [OK] Created welcome file in workspace
)

echo.
echo ======================================================================
echo   Next Steps:
echo ======================================================================
echo.
echo   1. Run the launcher:
echo      python launcher.py
echo.
echo   2. Open your browser to:
echo      http://localhost:5050/vscode_clone.html
echo.
echo   3. Set auth token to: localdev
echo.
echo   4. Your files will be saved to: workspace\
echo.
echo ======================================================================
echo.
pause