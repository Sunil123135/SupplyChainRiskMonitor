@echo off
REM Supply Chain Risk Monitor - Setup Script (Windows)
REM This script automates the setup process for Windows

echo ========================================
echo Supply Chain Risk Monitor - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Step 1: Setup Python environment
echo.
echo Step 1: Setting up Python environment...
cd index_build

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [!] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [OK] Dependencies installed

REM Step 2: Build index
echo.
echo Step 2: Building index with demo data...
python main.py

if not exist "..\bundle\vectors.bin" (
    echo Error: Index build failed
    pause
    exit /b 1
)
if not exist "..\bundle\meta.json" (
    echo Error: Index build failed
    pause
    exit /b 1
)

echo [OK] Index built successfully

REM Step 3: Copy bundle to extension
echo.
echo Step 3: Copying bundle to Chrome extension...
cd ..
if not exist "chrome_ext\bundle" mkdir chrome_ext\bundle
copy bundle\vectors.bin chrome_ext\bundle\ >nul
copy bundle\meta.json chrome_ext\bundle\ >nul

if exist "chrome_ext\bundle\vectors.bin" (
    if exist "chrome_ext\bundle\meta.json" (
        echo [OK] Bundle copied to extension
    ) else (
        echo Error: Failed to copy meta.json
        pause
        exit /b 1
    )
) else (
    echo Error: Failed to copy vectors.bin
    pause
    exit /b 1
)

REM Step 4: Display instructions
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open Chrome and navigate to: chrome://extensions/
echo 2. Enable 'Developer mode' (toggle in top-right)
echo 3. Click 'Load unpacked'
echo 4. Select the 'chrome_ext' directory:
echo    %CD%\chrome_ext
echo.
echo 5. Test the extension:
echo    - Navigate to any page
echo    - Click the extension icon
echo    - Click 'Analyze Current Page'
echo.
echo For more help, see:
echo   - QUICKSTART.md
echo   - INSTALLATION.md
echo   - README.md
echo.
echo Happy monitoring!
echo.
pause

