#!/usr/bin/env python3
"""
Dashboard Runner Script
Starts the Discord Affiliate Bot Dashboard with proper configuration.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed."""
    try:
        import flask
        import flask_socketio
        import discord
        import motor
        import aiohttp
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration file exists."""
    config_path = Path("../config.env")
    if config_path.exists():
        print("✅ Configuration file found")
        return True
    else:
        print("❌ Configuration file not found: ../config.env")
        print("Please create the configuration file with your Discord bot token and other settings")
        return False

def setup_environment():
    """Setup environment variables."""
    # Add parent directory to Python path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(parent_dir)
    
    print("✅ Environment configured")

def main():
    """Main function to run the dashboard."""
    print("🚀 Starting Discord Affiliate Bot Dashboard...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    print("=" * 50)
    print("🌐 Dashboard will be available at: http://localhost:5000")
    print("🔐 Login with your Discord account to access the dashboard")
    print("📊 Manage your bot, campaigns, and analytics")
    print("=" * 50)
    
    try:
        # Import and run the dashboard
        from app import app, socketio, initialize_dashboard
        
        # Initialize dashboard
        initialize_dashboard()
        
        # Start the Flask app with SocketIO
        socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=5000,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
