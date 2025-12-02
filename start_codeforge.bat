@echo off
REM CodeForge Studio Starter - Windows Batch
REM Double-click this file to start CodeForge Studio

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo  CodeForge Studio - Starting...
echo ============================================================
echo.

REM Kill any existing node processes
echo Checking for existing processes...
taskkill /F /IM node.exe >nul 2>&1

REM Wait a moment
timeout /t 1 /nobreak >nul

REM Start Node server
echo.
echo Starting Node backend server...
start "CodeForge Studio Backend" /MIN node codeforge_studio_server.js

REM Wait for server to be ready
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Open browser
echo.
echo Opening browser...
start http://localhost:5050/vscode_clone.html

echo.
echo ============================================================
echo  CodeForge Studio Ready!
echo ============================================================
echo.
echo Web UI: http://localhost:5050/vscode_clone.html
echo.
echo Quick Start:
echo   1. Click "Set Auth Token" ^> enter "localdev"
echo   2. Create a file: File ^> New File
echo   3. Fuzzy search: Press Ctrl+P
echo   4. Upload folder: File ^> Add Existing Folder
echo   5. Split editor: Click "Split Right"
echo.
echo Features:
echo   - File explorer & multi-tab editor
echo   - Git integration (Source Control)
echo   - Terminal integration
echo   - AI chat (optional)
echo   - 20+ language syntax highlighting
echo.
echo ============================================================
echo.
pause
