#!/usr/bin/env python3
"""
Diagnose network performance issues
"""
import requests
import time
import subprocess
import socket

def test_basic_connectivity():
    """Test basic network connectivity"""
    print("🌐 BASIC NETWORK DIAGNOSTICS")
    print("=" * 40)
    
    # Test DNS resolution
    try:
        start = time.time()
        ip = socket.gethostbyname('google.com')
        dns_time = (time.time() - start) * 1000
        print(f"✅ DNS Resolution: {dns_time:.1f}ms (google.com -> {ip})")
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
    
    # Test basic HTTP to fast services
    fast_services = [
        ('Google', 'https://www.google.com'),
        ('Cloudflare', 'https://1.1.1.1'),
        ('GitHub', 'https://api.github.com'),
        ('Singapore CDN', 'https://httpbin.org/get'),
    ]
    
    print("\n📡 HTTP Response Times:")
    for name, url in fast_services:
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                print(f"✅ {name}: {response_time:.1f}ms")
            else:
                print(f"⚠️ {name}: {response_time:.1f}ms (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {name}: Failed ({str(e)[:50]})")

def test_fly_io_infrastructure():
    """Test Fly.io specific infrastructure"""
    print("\n🚁 FLY.IO INFRASTRUCTURE TEST")
    print("=" * 40)
    
    # Test Fly.io endpoints
    fly_endpoints = [
        ('Fly.io API', 'https://api.fly.io/'),
        ('Fly.io Registry', 'https://registry.fly.io/'),
        ('Fly.io App (General)', 'https://httpbin.fly.dev/get'),
    ]
    
    for name, url in fly_endpoints:
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                print(f"✅ {name}: {response_time:.1f}ms")
            else:
                print(f"⚠️ {name}: {response_time:.1f}ms (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {name}: Failed ({str(e)[:50]})")

def test_crypto_exchanges():
    """Test crypto exchange APIs (what our app uses)"""
    print("\n₿ CRYPTO EXCHANGE API SPEEDS")
    print("=" * 40)
    
    exchange_apis = [
        ('Binance', 'https://api.binance.com/api/v3/ping'),
        ('Binance Spot', 'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT'),
        ('CoinGecko', 'https://api.coingecko.com/api/v3/ping'),
    ]
    
    for name, url in exchange_apis:
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                print(f"✅ {name}: {response_time:.1f}ms")
                if name == 'Binance Spot':
                    data = response.json()
                    if 'price' in data:
                        print(f"   📊 BTC Price: ${float(data['price']):,.2f}")
            else:
                print(f"⚠️ {name}: {response_time:.1f}ms (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {name}: Failed ({str(e)[:50]})")

def test_current_deployment_detailed():
    """Detailed test of current deployment"""
    print("\n🔍 CURRENT DEPLOYMENT DETAILED TEST")
    print("=" * 40)
    
    app_url = "https://crypto-assistant-prod.fly.dev"
    
    # Test health endpoint
    try:
        print("Testing health endpoint...")
        start = time.time()
        response = requests.get(f"{app_url}/health", timeout=30)
        health_time = (time.time() - start) * 1000
        
        if response.status_code == 200:
            print(f"✅ Health endpoint: {health_time:.1f}ms")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint: HTTP {response.status_code}")
    except requests.exceptions.Timeout:
        print("❌ Health endpoint: TIMEOUT (30+ seconds)")
    except Exception as e:
        print(f"❌ Health endpoint: {e}")
    
    # Test if it's a resource issue by trying lightweight endpoint
    try:
        print("\nTesting if server is overloaded...")
        start = time.time()
        response = requests.get(f"{app_url}/health", timeout=5)
        quick_time = (time.time() - start) * 1000
        print(f"Quick test: {quick_time:.1f}ms")
    except requests.exceptions.Timeout:
        print("❌ Even quick test timed out - server likely overloaded")
    except Exception as e:
        print(f"❌ Quick test failed: {e}")

def main():
    print("🩺 COMPREHENSIVE NETWORK & DEPLOYMENT DIAGNOSIS")
    print("=" * 60)
    print("🌍 Testing from your Singapore location...\n")
    
    test_basic_connectivity()
    test_fly_io_infrastructure()
    test_crypto_exchanges()
    test_current_deployment_detailed()
    
    print("\n" + "=" * 60)
    print("📋 DIAGNOSIS SUMMARY:")
    print("1. If basic connectivity is fast (< 200ms):")
    print("   → Problem is with Fly.io deployment")
    print("2. If crypto exchanges are fast (< 500ms):")
    print("   → Problem is with our app configuration")
    print("3. If everything is slow (> 1000ms):")
    print("   → Network/ISP issue from Singapore")
    print("4. If only our deployment is slow:")
    print("   → Resource starvation (256MB RAM insufficient)")
    
    print("\n💡 NEXT STEPS:")
    print("- If basic internet is fast: Upgrade Fly.io resources")
    print("- If everything is slow: Check your internet connection")
    print("- If crypto APIs work: Our deployment needs optimization")

if __name__ == "__main__":
    main()