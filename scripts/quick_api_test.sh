#!/bin/bash
# Quick API Test - Simple bash script for API testing
# Usage: ./quick_api_test.sh [production]

BASE_URL="http://localhost:8001"

if [ "$1" = "production" ]; then
    BASE_URL="http://13.239.14.166:8001"
    echo "🔍 Testing AWS Production APIs"
else
    echo "🔍 Testing Local APIs"
fi

echo "Base URL: $BASE_URL"
echo

# Test health endpoint
echo -n "Health check: "
curl -s -f "$BASE_URL/health" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅"
else
    echo "❌"
fi

# Test price endpoint  
echo -n "Price endpoint: "
curl -s -f -X POST "$BASE_URL/combined_price" \
    -H "Content-Type: application/json" \
    -d '{"symbol":"BTC-USDT"}' > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅"
else
    echo "❌"
fi

# Test OI endpoint
echo -n "OI endpoint: "
curl -s -f -X POST "$BASE_URL/oi_analysis" \
    -H "Content-Type: application/json" \
    -d '{"symbol":"BTC"}' > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅"
else
    echo "❌"
fi

# Test analysis endpoint
echo -n "Analysis endpoint: "
curl -s -f -X POST "$BASE_URL/comprehensive_analysis" \
    -H "Content-Type: application/json" \
    -d '{"symbol":"BTC/USDT","timeframe":"15m"}' > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅"
else
    echo "❌"
fi

echo
echo "Quick test complete"