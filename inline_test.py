#!/usr/bin/env python3
"""
Inline test for API endpoints - imports everything needed
"""
import requests
import json
import subprocess
import sys

def main():
    print("Market Data API Testing")
    print("=======================")
    
    # Test Docker status
    print("\n=== CHECKING DOCKER SERVICES ===")
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker is running")
            if 'crypto-market-data' in result.stdout:
                print("✅ Market Data service container is running")
            else:
                print("❌ Market Data service container is NOT running")
        else:
            print("❌ Docker is not running or accessible")
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
    
    # Test API endpoints
    print("\n=== TESTING API ENDPOINTS ===")
    
    base_url = "http://localhost:8001"
    
    # Test 1: Health Check
    print("\n--- Testing Health Check ---")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Health Check: SUCCESS (Status: {response.status_code})")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ Health Check: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Health Check: ERROR - {e}")
    
    # Test 2: Price Data
    print("\n--- Testing Price Data ---")
    try:
        response = requests.post(
            f"{base_url}/price",
            json={"symbol": "BTC-USDT"},
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        if response.status_code == 200:
            print(f"✅ Price Data: SUCCESS (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ Price Data: FAILED (Status: {response.status_code})")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Price Data: ERROR - {e}")
    
    # Test 3: Comprehensive Analysis
    print("\n--- Testing Comprehensive Analysis ---")
    try:
        response = requests.post(
            f"{base_url}/comprehensive_analysis",
            json={"symbol": "BTC-USDT", "timeframe": "15m"},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        if response.status_code == 200:
            print(f"✅ Comprehensive Analysis: SUCCESS (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ Comprehensive Analysis: FAILED (Status: {response.status_code})")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Comprehensive Analysis: ERROR - {e}")
    
    # Test 4: Multi-Exchange OI
    print("\n--- Testing Multi-Exchange OI ---")
    try:
        response = requests.post(
            f"{base_url}/multi_oi",
            json={"symbol": "BTC-USDT"},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        if response.status_code == 200:
            print(f"✅ Multi-Exchange OI: SUCCESS (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ Multi-Exchange OI: FAILED (Status: {response.status_code})")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Multi-Exchange OI: ERROR - {e}")
    
    # Test 5: Volume Scan
    print("\n--- Testing Volume Scan ---")
    try:
        response = requests.post(
            f"{base_url}/volume_scan",
            json={"symbol": "BTC-USDT"},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        if response.status_code == 200:
            print(f"✅ Volume Scan: SUCCESS (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ Volume Scan: FAILED (Status: {response.status_code})")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Volume Scan: ERROR - {e}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()