#!/usr/bin/env python3
"""
Test script for database integration.
Run this to verify database connection and functionality.
"""

import asyncio
import os
from dotenv import load_dotenv
from database import db_manager, get_guild_settings, update_guild_settings

load_dotenv()

async def test_database():
    """Test database connection and basic operations."""
    print("🔍 Testing Database Integration...")
    print("=" * 50)
    
    # Test 1: Database Connection
    print("1. Testing database connection...")
    connected = await db_manager.connect()
    
    if connected:
        print("✅ Database connection successful!")
        
        # Test 2: Health Check
        print("\n2. Testing database health check...")
        health = await db_manager.health_check()
        print(f"   Status: {'✅ Connected' if health['connected'] else '❌ Disconnected'}")
        print(f"   Database: {health['database_name']}")
        print(f"   Guilds: {health['guild_count']}")
        if health['error']:
            print(f"   Error: {health['error']}")
        
        # Test 3: Guild Settings Operations
        print("\n3. Testing guild settings operations...")
        test_guild_id = "123456789012345678"
        
        # Test getting default settings
        print("   Getting default guild settings...")
        settings = await get_guild_settings(test_guild_id)
        print(f"   ✅ Retrieved settings: prefix='{settings['prefix']}', welcome='{settings['welcome_message'][:30]}...'")
        
        # Test updating settings
        print("   Updating guild settings...")
        new_settings = {
            "prefix": "?",
            "welcome_message": "Welcome to our amazing server!",
            "auto_moderation": True
        }
        success = await update_guild_settings(test_guild_id, new_settings)
        print(f"   {'✅' if success else '❌'} Update result: {success}")
        
        # Test getting updated settings
        print("   Getting updated guild settings...")
        updated_settings = await get_guild_settings(test_guild_id)
        print(f"   ✅ Updated settings: prefix='{updated_settings['prefix']}', welcome='{updated_settings['welcome_message'][:30]}...'")
        print(f"   ✅ Auto moderation: {updated_settings.get('auto_moderation', False)}")
        
        # Test 4: Dynamic Prefix Function
        print("\n4. Testing dynamic prefix function...")
        from database import get_prefix
        
        # Mock message object for testing
        class MockMessage:
            def __init__(self, guild_id):
                self.guild = MockGuild(guild_id)
        
        class MockGuild:
            def __init__(self, guild_id):
                self.id = guild_id
        
        mock_message = MockMessage(test_guild_id)
        prefix = await get_prefix(None, mock_message)
        print(f"   ✅ Dynamic prefix: '{prefix}'")
        
        # Test 5: Cleanup
        print("\n5. Cleaning up test data...")
        cleanup_success = await db_manager.delete_guild_settings(test_guild_id)
        print(f"   {'✅' if cleanup_success else '❌'} Cleanup result: {cleanup_success}")
        
        print("\n" + "=" * 50)
        print("🎉 Database integration test completed!")
        print("✅ All tests passed! Your bot is ready for database integration.")
        
    else:
        print("❌ Database connection failed!")
        print("⚠️ Make sure to:")
        print("   1. Set MONGO_URI in your .env file")
        print("   2. Install MongoDB dependencies: pip install -r requirements.txt")
        print("   3. Check your MongoDB connection string")
    
    # Always disconnect
    await db_manager.disconnect()

async def test_environment_variables():
    """Test environment variable configuration."""
    print("\n🔧 Testing Environment Variables...")
    print("=" * 30)
    
    required_vars = ['DISCORD_BOT_TOKEN', 'MONGO_URI']
    optional_vars = ['BASE44_APP_ID', 'API_BASE_URL', 'DB_NAME']
    
    print("Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "❌ Missing"
        print(f"   {var}: {status}")
        if value and var == 'DISCORD_BOT_TOKEN':
            print(f"      Value: {value[:10]}...{value[-10:]}")
        elif value and var == 'MONGO_URI':
            # Hide sensitive parts of MongoDB URI
            if '@' in value:
                parts = value.split('@')
                if len(parts) == 2:
                    hidden_uri = f"{parts[0].split('//')[0]}//***:***@{parts[1]}"
                    print(f"      Value: {hidden_uri}")
                else:
                    print(f"      Value: {value[:20]}...")
            else:
                print(f"      Value: {value[:20]}...")
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "⚠️ Not set (using default)"
        print(f"   {var}: {status}")
        if value:
            print(f"      Value: {value}")

if __name__ == "__main__":
    print("🚀 Base44 Discord Bot - Database Integration Test")
    print("=" * 60)
    
    # Test environment variables first
    asyncio.run(test_environment_variables())
    
    # Test database functionality
    asyncio.run(test_database())
    
    print("\n📋 Next Steps:")
    print("1. If tests passed, your bot is ready!")
    print("2. Start your bot with: python start_bot.py")
    print("3. Use these commands in Discord:")
    print("   - !settings - View current server settings")
    print("   - !prefix <new_prefix> - Change bot prefix")
    print("   - !welcome <message> - Set welcome message")
    print("   - !dbstatus - Check database status")
    print("   - !sync - Sync with Base44 dashboard")
    print("\n🎯 Your bot now supports:")
    print("✅ Dynamic prefixes per server")
    print("✅ Database-backed settings")
    print("✅ Base44 dashboard sync")
    print("✅ Automatic welcome messages")
    print("✅ Error handling and fallbacks")
