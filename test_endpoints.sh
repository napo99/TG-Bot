#!/bin/bash

echo "Testing Market Data API Endpoints"
echo "================================="

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s -X GET http://localhost:8001/health | head -c 500
echo -e "\n"

# Test 2: Price Data
echo "2. Testing Price Data..."
curl -s -X POST http://localhost:8001/price \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USDT"}' | head -c 500
echo -e "\n"

# Test 3: Comprehensive Analysis
echo "3. Testing Comprehensive Analysis..."
curl -s -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USDT", "timeframe": "15m"}' | head -c 500
echo -e "\n"

# Test 4: Multi-Exchange OI
echo "4. Testing Multi-Exchange OI..."
curl -s -X POST http://localhost:8001/multi_oi \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USDT"}' | head -c 500
echo -e "\n"

# Test 5: Volume Scan
echo "5. Testing Volume Scan..."
curl -s -X POST http://localhost:8001/volume_scan \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USDT"}' | head -c 500
echo -e "\n"

echo "Test complete!"