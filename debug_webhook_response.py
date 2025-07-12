#!/usr/bin/env python3
"""
Debug webhook response to understand what the bot is actually returning
"""

import requests
import json
import time

def test_webhook_response():
    """Test webhook response and show actual content"""
    
    # Simulate Telegram webhook payload
    payload = {
        "update_id": int(time.time()),
        "message": {
            "message_id": int(time.time()),
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "/analysis BTC-USDT 15m"
        }
    }
    
    print("🔍 Sending webhook request...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8080/webhook",
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print(f"📊 Response Content Length: {len(response.text)}")
        print(f"📊 Response Text:\n{response.text}")
        
        # Try to parse as JSON
        try:
            json_response = response.json()
            print(f"\n📊 JSON Response: {json.dumps(json_response, indent=2)}")
        except:
            print("\n📊 Response is not JSON")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_direct_market_data():
    """Test market data service directly"""
    print("\n🔍 Testing market data service directly...")
    
    try:
        response = requests.post(
            "http://localhost:8001/comprehensive_analysis",
            json={"symbol": "BTC/USDT", "timeframe": "15m"},
            timeout=30
        )
        
        print(f"📊 Market Data Response Status: {response.status_code}")
        print(f"📊 Market Data Response: {response.text[:500]}...")
        
    except Exception as e:
        print(f"❌ Market Data Error: {e}")

if __name__ == "__main__":
    test_webhook_response()
    test_direct_market_data()