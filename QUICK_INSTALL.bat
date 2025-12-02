@echo off
REM CodeForge Studio - One-Click Installation
REM Installs all dependencies automatically

echo.
echo ===============================================================
echo   CodeForge Studio - Quick Installation
echo ===============================================================
echo.

REM Check Python
echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python from: https://python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check Node.js
echo [2/5] Checking Node.js...
node --version
if errorlevel 1 (
    echo [ERROR] Node.js not found
    echo Please install Node.js from: https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

REM Install Python dependencies
echo [3/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed
echo.

REM Install llama-cpp-python
echo [4/5] Installing llama-cpp-python (this may take a moment)...
echo.

REM Detect GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing CPU version (no GPU detected)
    pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
) else (
    echo [INFO] Installing GPU version (NVIDIA detected)
    pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
    if errorlevel 1 (
        echo Trying alternative CUDA version...
        pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu118
    )
    if errorlevel 1 (
        echo GPU version failed, installing CPU version...
        pip install llama-cpp-python --prefer-binary
    )
)

if errorlevel 1 (
    echo [WARNING] llama-cpp-python installation failed
    echo The application will work but without local AI features
    echo You can continue or install manually later
    echo.
)
echo.

REM Install Node dependencies
echo [5/5] Installing Node.js dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo [OK] Node.js dependencies installed
echo.

REM Success
echo ===============================================================
echo   ✅ Installation Complete!
echo ===============================================================
echo.
echo Next steps:
echo   1. Double-click "start.bat" to launch the application
echo   2. Or run: python launcher.py
echo   3. Browser will open automatically
echo   4. Set admin token: "localdev"
echo.
echo Troubleshooting:
echo   - If AI doesn't work: Run install_llama.bat
echo   - Check SETUP_GUIDE.md for common issues
echo   - View logs in codeforge_launcher.log
echo.
echo ===============================================================
echo.

pause