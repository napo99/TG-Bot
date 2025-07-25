#!/usr/bin/env python3
"""
Production Service Monitoring Script
"""
import requests
import time
import json
from datetime import datetime

def check_service_health():
    """Check if production services are responding"""
    services = {
        "Cloud API": "https://crypto-assistant-prod.fly.dev/health",
        "Production Bot": None  # Will check via Telegram API
    }
    
    results = {}
    
    # Test cloud API
    try:
        response = requests.get(services["Cloud API"], timeout=10)
        if response.status_code == 200:
            data = response.json()
            results["Cloud API"] = {
                "status": "✅ HEALTHY",
                "response_time": f"{response.elapsed.total_seconds():.2f}s",
                "data": data
            }
        else:
            results["Cloud API"] = {
                "status": f"❌ HTTP {response.status_code}",
                "response_time": f"{response.elapsed.total_seconds():.2f}s"
            }
    except Exception as e:
        results["Cloud API"] = {
            "status": f"❌ UNREACHABLE",
            "error": str(e)
        }
    
    # Test production bot
    prod_token = "YOUR_BOT_TOKEN_HERE"
    bot_url = f"https://api.telegram.org/bot{prod_token}/getMe"
    
    try:
        response = requests.get(bot_url, timeout=5)
        data = response.json()
        if data.get('ok'):
            results["Production Bot"] = {
                "status": "✅ BOT TOKEN VALID",
                "bot_name": f"@{data['result']['username']}",
                "bot_id": data['result']['id']
            }
        else:
            results["Production Bot"] = {
                "status": "❌ BOT TOKEN INVALID",
                "error": data.get('description', 'Unknown error')
            }
    except Exception as e:
        results["Production Bot"] = {
            "status": "❌ BOT UNREACHABLE",
            "error": str(e)
        }
    
    return results

def comprehensive_test():
    """Run comprehensive market data test"""
    try:
        test_data = {
            "symbol": "BTC/USDT",
            "timeframe": "15m"
        }
        
        response = requests.post(
            "https://crypto-assistant-prod.fly.dev/comprehensive_analysis",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                price = data['data']['price_data']['current_price']
                volume = data['data']['volume_analysis']['current_volume']
                return {
                    "status": "✅ MARKET DATA WORKING",
                    "btc_price": f"${price:,.2f}",
                    "btc_volume": f"{volume:.2f} BTC",
                    "response_time": f"{response.elapsed.total_seconds():.2f}s"
                }
            else:
                return {
                    "status": "❌ API ERROR",
                    "error": data.get('error', 'Unknown error')
                }
        else:
            return {
                "status": f"❌ HTTP {response.status_code}",
                "response": response.text[:200]
            }
    except Exception as e:
        return {
            "status": "❌ MARKET DATA FAILED",
            "error": str(e)
        }

def main():
    print("🔍 PRODUCTION SERVICE MONITORING")
    print("=" * 60)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Basic health checks
    print("📊 Basic Service Health:")
    health_results = check_service_health()
    
    for service, result in health_results.items():
        print(f"  {service}: {result['status']}")
        if 'response_time' in result:
            print(f"    Response Time: {result['response_time']}")
        if 'error' in result:
            print(f"    Error: {result['error']}")
        if 'bot_name' in result:
            print(f"    Bot: {result['bot_name']}")
    
    print()
    print("📈 Market Data Functionality:")
    market_test = comprehensive_test()
    print(f"  Status: {market_test['status']}")
    
    if 'btc_price' in market_test:
        print(f"  BTC Price: {market_test['btc_price']}")
        print(f"  BTC Volume: {market_test['btc_volume']}")
        print(f"  Response Time: {market_test['response_time']}")
    elif 'error' in market_test:
        print(f"  Error: {market_test['error']}")
    
    print()
    print("🎯 RELIABILITY ASSESSMENT:")
    
    api_healthy = "✅" in health_results["Cloud API"]["status"]
    bot_valid = "✅" in health_results["Production Bot"]["status"]
    market_working = "✅" in market_test["status"]
    
    if api_healthy and bot_valid and market_working:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("🤖 Production bot should respond to Telegram commands")
    elif api_healthy and bot_valid:
        print("⚠️ BASIC SERVICES OK, MARKET DATA ISSUES")
        print("🤖 Bot might respond but with limited functionality")
    elif api_healthy:
        print("⚠️ API RESPONDING, BOT ISSUES")
        print("❌ Production bot likely not responding")
    else:
        print("❌ MAJOR OUTAGE")
        print("❌ Services appear to be down")
    
    print("\n💡 Monitoring Commands:")
    print("  flyctl status --app crypto-assistant-prod")
    print("  flyctl logs --app crypto-assistant-prod")
    print("  flyctl machine restart --app crypto-assistant-prod")

if __name__ == "__main__":
    main()