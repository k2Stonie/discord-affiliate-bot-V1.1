#!/usr/bin/env python3
"""
Startup script for Discord Affiliate Bot with Base44 integration
"""
import os
import sys
from dotenv import load_dotenv

def load_config():
    """Load configuration from config.env file"""
    config_file = 'config.env'
    if os.path.exists(config_file):
        load_dotenv(config_file)
        print(f"✅ Loaded configuration from {config_file}")
    else:
        print(f"❌ Configuration file {config_file} not found!")
        print("Please create a .env file with your Discord bot token and Base44 configuration")
        return False
    
    # Verify required environment variables
    required_vars = ['DISCORD_BOT_TOKEN', 'API_BASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required configuration loaded successfully")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Discord Affiliate Bot...")
    print("=" * 50)
    
    # Load configuration
    if not load_config():
        sys.exit(1)
    
    # Import and run the bot
    try:
        import bot
        import asyncio
        print("✅ Bot module imported successfully")
        print("🎯 Starting bot...")
        
        # Run the bot
        asyncio.run(bot.run_bot())
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

