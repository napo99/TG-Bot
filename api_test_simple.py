import requests
import json

# Test 1: Health Check
print("Testing Health Check...")
try:
    response = requests.get("http://localhost:8001/health", timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Price Data
print("Testing Price Data...")
try:
    response = requests.post(
        "http://localhost:8001/price", 
        json={"symbol": "BTC-USDT"},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Comprehensive Analysis
print("Testing Comprehensive Analysis...")
try:
    response = requests.post(
        "http://localhost:8001/comprehensive_analysis", 
        json={"symbol": "BTC-USDT", "timeframe": "15m"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 4: Multi-Exchange OI
print("Testing Multi-Exchange OI...")
try:
    response = requests.post(
        "http://localhost:8001/multi_oi", 
        json={"symbol": "BTC-USDT"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 5: Volume Scan
print("Testing Volume Scan...")
try:
    response = requests.post(
        "http://localhost:8001/volume_scan", 
        json={"symbol": "BTC-USDT"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")