@echo off
REM Emergency Fix Script - Use if setup fails
REM This will forcefully reinstall everything

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ======================================================================
echo   CodeForge Studio - Emergency Fix
echo ======================================================================
echo.
echo   This will:
echo   1. Kill all Node.js processes
echo   2. Delete node_modules
echo   3. Reinstall all dependencies
echo   4. Create workspace folder
echo.
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b 0

echo.
echo [1/5] Killing Node.js processes...
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   [OK] Processes killed

echo.
echo [2/5] Cleaning old installation...
if exist node_modules (
    rmdir /s /q node_modules
    echo   [OK] Deleted node_modules
) else (
    echo   [OK] Already clean
)

if exist package-lock.json (
    del /f /q package-lock.json
    echo   [OK] Deleted package-lock.json
)

echo.
echo [3/5] Installing dependencies (this may take 2-3 minutes)...
call npm install express cors multer axios --save

if errorlevel 1 (
    echo.
    echo   [ERROR] Installation failed!
    echo.
    echo   Try these solutions:
    echo   1. Check internet connection
    echo   2. Run as Administrator
    echo   3. Clear npm cache: npm cache clean --force
    echo.
    pause
    exit /b 1
)

echo   [OK] Dependencies installed

echo.
echo [4/5] Creating workspace folder...
if not exist workspace mkdir workspace
echo   [OK] Workspace ready

echo.
echo [5/5] Verifying installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Node.js not found
    exit /b 1
)

if not exist node_modules\express (
    echo   [ERROR] Express not installed
    exit /b 1
)

if not exist node_modules\cors (
    echo   [ERROR] CORS not installed
    exit /b 1
)

if not exist node_modules\multer (
    echo   [ERROR] Multer not installed
    exit /b 1
)

echo   [OK] All packages verified!

echo.
echo ======================================================================
echo   [SUCCESS] Emergency fix complete!
echo ======================================================================
echo.
echo   Now run: python launcher.py
echo.
pause