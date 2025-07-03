#!/usr/bin/env python3
"""
Debug the "server disconnected" error from telegram bot
"""
import requests
import json
import time

def test_api_endpoints():
    """Test each API endpoint to isolate the issue"""
    base_url = "https://crypto-assistant-prod.fly.dev"
    
    tests = [
        ("Health Check", "GET", f"{base_url}/health", None),
        ("Simple Analysis", "POST", f"{base_url}/comprehensive_analysis", {
            "symbol": "BTC/USDT", 
            "timeframe": "15m"
        }),
        ("SOL Analysis", "POST", f"{base_url}/comprehensive_analysis", {
            "symbol": "SOL/USDT", 
            "timeframe": "15m"
        })
    ]
    
    print("🔍 DEBUGGING SERVER DISCONNECTION ERROR")
    print("=" * 50)
    
    for test_name, method, url, data in tests:
        print(f"\n🧪 Testing: {test_name}")
        print(f"URL: {url}")
        
        try:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
            
            elapsed = time.time() - start_time
            
            print(f"✅ Status: {response.status_code}")
            print(f"⏱️ Time: {elapsed:.2f}s")
            print(f"📦 Content Length: {len(response.content)} bytes")
            
            # Try to parse JSON
            try:
                json_data = response.json()
                if 'success' in json_data:
                    print(f"📊 Success: {json_data['success']}")
                if 'error' in json_data:
                    print(f"❌ Error: {json_data['error']}")
                if 'data' in json_data and json_data.get('success'):
                    price_data = json_data['data'].get('price_data', {})
                    if 'current_price' in price_data:
                        print(f"💰 Price: ${price_data['current_price']:,.2f}")
            except json.JSONDecodeError:
                print(f"⚠️ Non-JSON response: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT (30+ seconds)")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ CONNECTION ERROR: {e}")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")

def test_exchange_apis_directly():
    """Test if exchange APIs are accessible from our deployment"""
    print("\n₿ TESTING EXCHANGE API ACCESSIBILITY")
    print("=" * 50)
    
    exchange_tests = [
        ("Binance Ping", "https://api.binance.com/api/v3/ping"),
        ("Binance Time", "https://api.binance.com/api/v3/time"),
        ("Binance BTC Price", "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"),
        ("Binance SOL Price", "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT"),
    ]
    
    for test_name, url in exchange_tests:
        print(f"\n🧪 {test_name}:")
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Success: {elapsed:.2f}s")
                try:
                    data = response.json()
                    if 'price' in data:
                        print(f"   Price: ${float(data['price']):,.2f}")
                    elif 'serverTime' in data:
                        print(f"   Server time: {data['serverTime']}")
                    elif data == {}:
                        print(f"   Ping successful")
                except:
                    print(f"   Response: {response.text[:50]}")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed: {e}")

def test_telegram_bot_simulation():
    """Simulate what the telegram bot does"""
    print("\n🤖 SIMULATING TELEGRAM BOT FLOW")
    print("=" * 50)
    
    # This is what happens when user sends /analysis BTC-USDT 15m
    bot_flow = [
        {
            "step": "1. Parse command",
            "action": "Extract symbol and timeframe from user message"
        },
        {
            "step": "2. Send acknowledgment", 
            "action": "Bot sends 'Fetching prices for SOL...'"
        },
        {
            "step": "3. Call API",
            "action": "POST to /comprehensive_analysis",
            "url": "https://crypto-assistant-prod.fly.dev/comprehensive_analysis",
            "data": {"symbol": "SOL/USDT", "timeframe": "15m"}
        },
        {
            "step": "4. Format response",
            "action": "Convert API response to telegram message"
        },
        {
            "step": "5. Send result",
            "action": "Send formatted analysis to user"
        }
    ]
    
    for flow_step in bot_flow:
        print(f"\n{flow_step['step']}: {flow_step['action']}")
        
        if 'url' in flow_step:
            print("   🔄 Testing this step...")
            try:
                start_time = time.time()
                response = requests.post(
                    flow_step['url'], 
                    json=flow_step['data'], 
                    timeout=25
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    print(f"   ✅ API call successful: {elapsed:.2f}s")
                    try:
                        data = response.json()
                        if data.get('success'):
                            print("   ✅ Analysis completed successfully")
                        else:
                            print(f"   ❌ Analysis failed: {data.get('error')}")
                    except:
                        print("   ⚠️ Invalid JSON response")
                else:
                    print(f"   ❌ API call failed: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print("   ❌ API call TIMEOUT - This is likely the 'server disconnected' cause!")
            except Exception as e:
                print(f"   ❌ API call error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_exchange_apis_directly()
    test_telegram_bot_simulation()