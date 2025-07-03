#!/usr/bin/env python3
"""
Comprehensive production test suite for Fly.io deployment
"""
import requests
import time
import json

def test_health_endpoint():
    """Test basic health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        start = time.time()
        response = requests.get("https://crypto-assistant-prod.fly.dev/health", timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {elapsed:.2f}s - {data}")
            return True, elapsed
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False, elapsed
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False, None

def test_price_endpoint():
    """Test the lightweight price endpoint"""
    print("\n💰 Testing Price Endpoint...")
    try:
        start = time.time()
        response = requests.post(
            "https://crypto-assistant-prod.fly.dev/combined_price",
            json={"symbol": "BTC/USDT"},
            timeout=15
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    spot_price = data.get('spot_price', 'N/A')
                    perp_price = data.get('perp_price', 'N/A')
                    print(f"✅ Price endpoint: {elapsed:.2f}s")
                    print(f"   📊 BTC Spot: ${spot_price}")
                    print(f"   📊 BTC Perp: ${perp_price}")
                    return True, elapsed
                else:
                    print(f"❌ Price endpoint API error: {data.get('error')}")
                    return False, elapsed
            except json.JSONDecodeError:
                print(f"❌ Price endpoint invalid JSON: {response.text[:100]}")
                return False, elapsed
        else:
            print(f"❌ Price endpoint HTTP {response.status_code}: {response.text[:100]}")
            return False, elapsed
            
    except requests.exceptions.Timeout:
        print(f"❌ Price endpoint timeout (>15s)")
        return False, 15
    except Exception as e:
        print(f"❌ Price endpoint error: {e}")
        return False, None

def test_volume_endpoint():
    """Test volume analysis endpoint"""
    print("\n📊 Testing Volume Endpoint...")
    try:
        start = time.time()
        response = requests.post(
            "https://crypto-assistant-prod.fly.dev/volume_spike",
            json={"symbol": "BTC/USDT", "timeframe": "15m"},
            timeout=20
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    volume_data = data.get('data', {})
                    current_volume = volume_data.get('current_volume', 'N/A')
                    spike_level = volume_data.get('spike_level', 'N/A')
                    print(f"✅ Volume endpoint: {elapsed:.2f}s")
                    print(f"   📊 Current Volume: {current_volume}")
                    print(f"   📊 Spike Level: {spike_level}")
                    return True, elapsed
                else:
                    print(f"❌ Volume endpoint API error: {data.get('error')}")
                    return False, elapsed
            except json.JSONDecodeError:
                print(f"❌ Volume endpoint invalid JSON: {response.text[:100]}")
                return False, elapsed
        else:
            print(f"❌ Volume endpoint HTTP {response.status_code}: {response.text[:100]}")
            return False, elapsed
            
    except requests.exceptions.Timeout:
        print(f"❌ Volume endpoint timeout (>20s)")
        return False, 20
    except Exception as e:
        print(f"❌ Volume endpoint error: {e}")
        return False, None

def test_comprehensive_endpoint():
    """Test the heavy comprehensive analysis endpoint"""
    print("\n🎯 Testing Comprehensive Analysis (Heavy)...")
    try:
        start = time.time()
        response = requests.post(
            "https://crypto-assistant-prod.fly.dev/comprehensive_analysis",
            json={"symbol": "BTC/USDT", "timeframe": "15m"},
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    price_data = data.get('data', {}).get('price_data', {})
                    volume_data = data.get('data', {}).get('volume_analysis', {})
                    current_price = price_data.get('current_price', 'N/A')
                    volume = volume_data.get('current_volume', 'N/A')
                    print(f"✅ Comprehensive analysis: {elapsed:.2f}s")
                    print(f"   📊 BTC Price: ${current_price}")
                    print(f"   📊 Volume: {volume}")
                    return True, elapsed
                else:
                    print(f"❌ Comprehensive analysis API error: {data.get('error')}")
                    return False, elapsed
            except json.JSONDecodeError:
                print(f"❌ Comprehensive analysis invalid JSON: {response.text[:100]}")
                return False, elapsed
        else:
            print(f"❌ Comprehensive analysis HTTP {response.status_code}: {response.text[:100]}")
            return False, elapsed
            
    except requests.exceptions.Timeout:
        print(f"❌ Comprehensive analysis timeout (>30s)")
        return False, 30
    except Exception as e:
        print(f"❌ Comprehensive analysis error: {e}")
        return False, None

def test_telegram_bot_status():
    """Test if telegram bot token is valid"""
    print("\n🤖 Testing Telegram Bot Status...")
    try:
        # Use production bot token
        bot_token = "8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Bot token valid: @{bot_info['username']}")
                return True
            else:
                print(f"❌ Bot token invalid: {data}")
                return False
        else:
            print(f"❌ Bot token check HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Bot token check error: {e}")
        return False

def main():
    print("🧪 COMPREHENSIVE PRODUCTION TEST SUITE")
    print("=" * 60)
    print("🌍 Testing crypto-assistant-prod.fly.dev (Hong Kong region)")
    print()
    
    results = {}
    
    # Test 1: Health endpoint
    health_ok, health_time = test_health_endpoint()
    results['health'] = (health_ok, health_time)
    
    # Test 2: Price endpoint (lightweight)
    price_ok, price_time = test_price_endpoint()
    results['price'] = (price_ok, price_time)
    
    # Test 3: Volume endpoint (medium)
    volume_ok, volume_time = test_volume_endpoint()
    results['volume'] = (volume_ok, volume_time)
    
    # Test 4: Comprehensive analysis (heavy)
    comp_ok, comp_time = test_comprehensive_endpoint()
    results['comprehensive'] = (comp_ok, comp_time)
    
    # Test 5: Bot status
    bot_ok = test_telegram_bot_status()
    results['bot'] = (bot_ok, None)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    # Calculate success rate
    total_tests = len(results)
    passed_tests = sum(1 for ok, _ in results.values() if ok)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    print()
    
    for test_name, (success, timing) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        timing_str = f" ({timing:.2f}s)" if timing else ""
        print(f"{test_name.upper():<15} {status}{timing_str}")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS")
    print("=" * 60)
    
    if health_ok and price_ok:
        print("✅ Basic functionality working - lightweight commands should work")
    
    if volume_ok:
        print("✅ Medium complexity endpoints working - /volume commands should work")
        
    if comp_ok:
        print("✅ Heavy analysis working - /analysis commands should work")
        print("🎉 ALL BOT COMMANDS SHOULD BE FUNCTIONAL!")
    else:
        print("⚠️ Heavy analysis failing - /analysis command will timeout")
        print("💡 Use lightweight commands: /price, /volume, /cvd")
        
    if bot_ok:
        print("✅ Telegram bot token valid - bot should respond")
        
    if success_rate >= 80:
        print("\n🎉 DEPLOYMENT STATUS: READY FOR PRODUCTION USE")
    elif success_rate >= 60:
        print("\n⚠️ DEPLOYMENT STATUS: PARTIALLY FUNCTIONAL")  
    else:
        print("\n❌ DEPLOYMENT STATUS: NEEDS ATTENTION")
        
    print(f"\n🔧 Current Resources: 256MB RAM, 1 vCPU (Hong Kong region)")
    if not comp_ok:
        print("💡 Consider upgrading to 512MB RAM for full functionality")

if __name__ == "__main__":
    main()