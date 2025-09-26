#!/usr/bin/env python3
"""
Test the complete Base44 integration with the correct bot_id
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def test_final_integration():
    """Test all Base44 API endpoints with the correct bot_id"""
    
    bot_id = os.getenv('BASE44_APP_ID')
    api_key = os.getenv('BASE44_FUNCTION_TOKEN')
    api_url = os.getenv('API_BASE_URL')
    
    print(f"🔍 Testing Complete Base44 Integration...")
    print(f"Bot ID: {bot_id}")
    print(f"API Key: {api_key[:10]}..." if api_key else "API Key: NOT FOUND")
    
    if not bot_id or not api_key:
        print("❌ Missing credentials!")
        return False
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Test 1: getBotConfig
    print(f"\n📡 Test 1: getBotConfig")
    endpoint = f"{api_url}/getBotConfig"
    payload = {"bot_id": bot_id}
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! getBotConfig working")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ FAILED: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Test 2: logBotActivity
    print(f"\n📡 Test 2: logBotActivity")
    endpoint = f"{api_url}/logBotActivity"
    payload = {
        "bot_id": bot_id,
        "activity_type": "test_integration",
        "message": "Testing Base44 integration",
        "user_id": "test_user",
        "guild_id": "1312293967965978684",
        "affiliate_email": "bot@base44.app"
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! logBotActivity working")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ FAILED: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Test 3: updateBotStatus
    print(f"\n📡 Test 3: updateBotStatus")
    endpoint = f"{api_url}/updateBotStatus"
    payload = {
        "bot_id": bot_id,
        "status": "active",
        "last_activity": "2025-01-01T00:00:00Z"
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! updateBotStatus working")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ FAILED: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    print(f"\n🎉 ALL TESTS PASSED! Base44 integration is working!")
    return True

if __name__ == "__main__":
    success = test_final_integration()
    if success:
        print(f"\n🚀 Your Discord bot is ready for Base44 integration!")
    else:
        print(f"\n❌ Some tests failed. Check the errors above.")
