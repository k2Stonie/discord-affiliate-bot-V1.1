#!/usr/bin/env python3
"""
Test script for the new Base44 URLs
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_new_base44_urls():
    """Test the new Base44 URLs"""
    print("🔍 Testing New Base44 URLs...")
    print("=" * 50)
    
    base_url = "https://discordaffiliatebot.base44.app/functions"
    bot_id = os.getenv('BASE44_APP_ID', '68d1f85a602cecfca6c02c10')
    
    print(f"Base URL: {base_url}")
    print(f"Bot ID: {bot_id}")
    
    endpoints_to_test = [
        'getBotConfig',
        'logBotActivity', 
        'updateBotStatus'
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            try:
                url = f"{base_url}/{endpoint}"
                payload = {'bot_id': bot_id}
                
                print(f"\n🧪 Testing: {endpoint}")
                print(f"URL: {url}")
                
                async with session.post(url, json=payload) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ SUCCESS! Response: {data}")
                    elif response.status == 400:
                        text = await response.text()
                        print(f"⚠️ 400 Bad Request: {text}")
                    elif response.status == 401:
                        print(f"⚠️ 401 Unauthorized - May need authentication")
                    elif response.status == 500:
                        text = await response.text()
                        print(f"❌ 500 Server Error: {text}")
                    else:
                        text = await response.text()
                        print(f"⚠️ Status {response.status}: {text}")
                        
            except Exception as e:
                print(f"❌ {endpoint} failed: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_new_base44_urls())
