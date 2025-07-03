#!/usr/bin/env python3
"""
Test script to validate production bot token functionality
"""
import requests
import os
from dotenv import load_dotenv

def test_bot_token():
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ No bot token found")
        return False
    
    # Test bot token validity
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Bot token VALID")
            print(f"🤖 Bot name: {bot_info.get('first_name')}")
            print(f"👤 Username: @{bot_info.get('username')}")
            print(f"🆔 Bot ID: {bot_info.get('id')}")
            return True
        else:
            print(f"❌ Bot token INVALID: {data.get('description')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return False

def test_market_data_connection():
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Market data service: HEALTHY")
            return True
        else:
            print(f"❌ Market data service: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Market data service: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Production Environment")
    print("=" * 40)
    
    bot_valid = test_bot_token()
    market_healthy = test_market_data_connection()
    
    print("=" * 40)
    if bot_valid and market_healthy:
        print("✅ Production environment: READY")
        exit(0)
    else:
        print("❌ Production environment: FAILED")
        exit(1)