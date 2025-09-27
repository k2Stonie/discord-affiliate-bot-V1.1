#!/bin/bash

echo "Starting Discord Affiliate Bot Dashboard..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found"
    echo "Please run this script from the dashboard directory"
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check if config file exists
if [ ! -f "../config.env" ]; then
    echo "Warning: config.env not found in parent directory"
    echo "Please create the configuration file with your Discord bot settings"
    echo
fi

echo
echo "========================================"
echo "Discord Affiliate Bot Dashboard"
echo "========================================"
echo
echo "Dashboard will be available at: http://localhost:5000"
echo "Login with your Discord account to access the dashboard"
echo
echo "Press Ctrl+C to stop the dashboard"
echo "========================================"
echo

# Start the dashboard
python3 run_dashboard.py
