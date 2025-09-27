@echo off
echo Starting Discord Affiliate Bot Dashboard...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found
    echo Please run this script from the dashboard directory
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if config file exists
if not exist "..\config.env" (
    echo Warning: config.env not found in parent directory
    echo Please create the configuration file with your Discord bot settings
    echo.
)

echo.
echo ========================================
echo Discord Affiliate Bot Dashboard
echo ========================================
echo.
echo Dashboard will be available at: http://localhost:5000
echo Login with your Discord account to access the dashboard
echo.
echo Press Ctrl+C to stop the dashboard
echo ========================================
echo.

REM Start the dashboard
python run_dashboard.py

pause
