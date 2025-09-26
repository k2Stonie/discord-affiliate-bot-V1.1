#!/usr/bin/env python3
"""
Test script to get all BotConfig records using the new getBotConfigList endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def test_getBotConfigList():
    """Test the new getBotConfigList endpoint"""
    
    api_key = os.getenv('BASE44_FUNCTION_TOKEN')
    api_url = os.getenv('API_BASE_URL')
    
    print(f"🔍 Testing new getBotConfigList endpoint...")
    print(f"API Key: {api_key[:10]}..." if api_key else "API Key: NOT FOUND")
    
    if not api_key:
        print("❌ Missing API key!")
        return None
    
    # Use the new endpoint
    endpoint = f"{api_url}/getBotConfigList"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {}  # Empty body as specified
    
    try:
        print(f"\n📡 Making request to: {endpoint}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Found BotConfig records:")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Look for "AffiliateBot Main" record
            if 'bot_configs' in result:
                for config in result['bot_configs']:
                    if config.get('bot_name') == 'AffiliateBot Main':
                        bot_id = config.get('id')
                        print(f"\n🎯 Found AffiliateBot Main!")
                        print(f"Real bot_id: {bot_id}")
                        return bot_id
            
            print(f"\n⚠️  AffiliateBot Main not found in the list")
            return None
        else:
            print(f"❌ FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    bot_id = test_getBotConfigList()
    if bot_id:
        print(f"\n🚀 Next step: Update config.env with BASE44_APP_ID={bot_id}")
    else:
        print(f"\n❌ Could not find the correct bot_id")
