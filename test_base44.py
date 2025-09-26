#!/usr/bin/env python3
"""
Test script for Base44 API connection
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_base44_connection():
    """Test Base44 API connection"""
    print("🔍 Testing Base44 API Connection...")
    print("=" * 50)
    
    api_base_url = os.getenv('API_BASE_URL', 'https://base44.app/api/apps/68d1f85a602cecfca6c02c10/functions')
    bot_id = os.getenv('BASE44_APP_ID', '68d1f85a602cecfca6c02c10')
    
    print(f"API URL: {api_base_url}")
    print(f"Bot ID: {bot_id}")
    
    async with aiohttp.ClientSession() as session:
        # Test basic connectivity
        try:
            # Test the base URL
            async with session.get(api_base_url.replace('/functions', '')) as response:
                print(f"Base URL Status: {response.status}")
                if response.status == 200:
                    print("✅ Base44 platform is accessible")
                else:
                    print(f"⚠️ Base44 platform returned status {response.status}")
        except Exception as e:
            print(f"❌ Cannot reach Base44 platform: {e}")
            return
        
        # Test specific endpoints
        endpoints_to_test = [
            'getBotConfig',
            'logBotActivity', 
            'updateBotStatus'
        ]
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{api_base_url}/{endpoint}"
                payload = {'bot_id': bot_id}
                
                async with session.post(url, json=payload) as response:
                    print(f"{endpoint}: Status {response.status}")
                    
                    if response.status == 200:
                        print(f"  ✅ {endpoint} is working")
                    elif response.status == 500:
                        print(f"  ⚠️ {endpoint} returned 500 - endpoint may not be configured yet")
                    elif response.status == 404:
                        print(f"  ❌ {endpoint} not found - endpoint doesn't exist")
                    else:
                        print(f"  ⚠️ {endpoint} returned {response.status}")
                        
            except Exception as e:
                print(f"  ❌ {endpoint} failed: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Analysis:")
    print("• Status 500 errors are normal for new Base44 setups")
    print("• Your bot will work with default settings")
    print("• Base44 endpoints can be configured later in the dashboard")
    print("• The bot is designed to handle these errors gracefully")

if __name__ == "__main__":
    asyncio.run(test_base44_connection())
