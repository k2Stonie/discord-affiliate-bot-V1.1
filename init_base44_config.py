#!/usr/bin/env python3
"""
Initialize Base44 BotConfig entity
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def init_bot_config():
    """Initialize BotConfig in Base44"""
    print("🚀 Initializing Base44 BotConfig...")
    print("=" * 50)
    
    base_url = "https://discordaffiliatebot.base44.app/functions"
    bot_id = os.getenv('BASE44_APP_ID', '68d1f85a602cecfca6c02c10')
    
    # Default bot configuration
    bot_config = {
        "bot_id": bot_id,
        "active": True,
        "affiliate_id": "default_affiliate",
        "message_templates": [
            {
                "name": "welcome_campaign",
                "content": "Welcome {username}! Check out our amazing offers:",
                "has_buttons": True,
                "button_labels": ["Get Started", "Learn More"],
                "selected_link_name": "main_affiliate_link"
            }
        ],
        "target_roles": [
            {
                "role_id": "123456789",
                "role_name": "VIP Member",
                "enabled": True
            }
        ],
        "affiliate_links": [
            {
                "name": "main_affiliate_link",
                "url_template": "https://yourstore.com/affiliate",
                "enabled": True
            }
        ],
        "prefix": "!",
        "welcome_message": "Welcome to the server!",
        "auto_moderation": False
    }
    
    print(f"Bot ID: {bot_id}")
    print(f"Config: {bot_config}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Try to create/update BotConfig
            url = f"{base_url}/getBotConfig"
            payload = {"bot_id": bot_id}
            
            print(f"\n🧪 Testing getBotConfig...")
            async with session.post(url, json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ BotConfig already exists: {data}")
                    return True
                elif response.status == 500:
                    text = await response.text()
                    print(f"❌ BotConfig not found: {text}")
                    
                    # Try to create BotConfig using updateBotStatus
                    print(f"\n🔧 Attempting to create BotConfig...")
                    create_url = f"{base_url}/updateBotStatus"
                    create_payload = {
                        "bot_id": bot_id,
                        "status": "active",
                        "message": "Bot initialized successfully",
                        "config": bot_config
                    }
                    
                    async with session.post(create_url, json=create_payload) as create_response:
                        print(f"Create Status: {create_response.status}")
                        if create_response.status == 200:
                            create_data = await create_response.json()
                            print(f"✅ BotConfig created: {create_data}")
                            return True
                        else:
                            create_text = await create_response.text()
                            print(f"❌ Failed to create BotConfig: {create_text}")
                            return False
                else:
                    text = await response.text()
                    print(f"⚠️ Unexpected status: {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_activity_logging():
    """Test activity logging"""
    print(f"\n🧪 Testing activity logging...")
    
    base_url = "https://discordaffiliatebot.base44.app/functions"
    bot_id = os.getenv('BASE44_APP_ID', '68d1f85a602cecfca6c02c10')
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{base_url}/logBotActivity"
            payload = {
                "bot_id": bot_id,
                "affiliate_email": "bot@base44.app",
                "activity_type": "startup",
                "timestamp": "2024-01-01T00:00:00.000Z",
                "success": True
            }
            
            async with session.post(url, json=payload) as response:
                print(f"Activity Log Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Activity logged: {data}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Failed to log activity: {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
            return False

if __name__ == "__main__":
    async def main():
        success = await init_bot_config()
        if success:
            await test_activity_logging()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Base44 BotConfig initialized successfully!")
            print("✅ Your bot should now work with Base44 integration!")
        else:
            print("❌ Failed to initialize BotConfig")
            print("⚠️ Bot will continue working with default settings")
    
    asyncio.run(main())