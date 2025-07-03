#!/usr/bin/env python3
"""
Direct test of production bot to see if it's responding from cloud
"""
import requests
import time
import os

def test_prod_bot_webhook():
    """Test if production bot is active by checking Telegram API"""
    prod_token = "8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
    
    # Get bot info
    url = f"https://api.telegram.org/bot{prod_token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('ok'):
            print(f"✅ Production bot token valid: @{data['result']['username']}")
            return True
        else:
            print(f"❌ Bot token issue: {data}")
            return False
    except Exception as e:
        print(f"❌ Error checking bot: {e}")
        return False

def test_webhook_info():
    """Check if bot has webhook set (would indicate cloud deployment active)"""
    prod_token = "8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
    
    url = f"https://api.telegram.org/bot{prod_token}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('ok'):
            webhook_info = data['result']
            print(f"📡 Webhook URL: {webhook_info.get('url', 'None (polling mode)')}")
            print(f"📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
            print(f"🕐 Last error: {webhook_info.get('last_error_date', 'None')}")
            return webhook_info
    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
        return None

def test_cloud_api():
    """Test if cloud API is responding"""
    try:
        response = requests.get("https://crypto-assistant-prod.fly.dev/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Cloud API responding: {response.json()}")
            return True
        else:
            print(f"❌ Cloud API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cloud API unreachable: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING PRODUCTION BOT STATUS")
    print("=" * 50)
    
    # Test 1: Bot token validity
    bot_valid = test_prod_bot_webhook()
    
    # Test 2: Webhook configuration  
    webhook_info = test_webhook_info()
    
    # Test 3: Cloud API health
    cloud_healthy = test_cloud_api()
    
    print("=" * 50)
    print("📋 DIAGNOSIS:")
    
    if bot_valid and cloud_healthy:
        if webhook_info and webhook_info.get('url'):
            print("✅ Production bot should be running from cloud (webhook mode)")
        else:
            print("⚠️ Production bot in polling mode - may be running locally or cloud")
    elif bot_valid and not cloud_healthy:
        print("❌ Bot token valid but cloud deployment down")
    else:
        print("❌ Major configuration issue")
        
    print("\n🎯 NEXT TEST: Send /analysis BTC-USDT 15m to @napo_crypto_prod_bot")
    print("📱 Monitor your internet: ON vs OFF to see source")