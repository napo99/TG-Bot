#!/bin/bash
# Production Health Check - AWS production monitoring
# Usage: ./production_health_check.sh

PROD_URL="http://13.239.14.166:8001"

echo "☁️ AWS Production Health Check"
echo "================================"
echo "Target: $PROD_URL"
echo

# Test connectivity
echo -n "🔗 Connectivity: "
curl -s -f --max-time 5 "$PROD_URL/health" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Connected"
else
    echo "❌ Cannot connect"
    exit 1
fi

# Get health status
echo "📊 System Status:"
HEALTH=$(curl -s "$PROD_URL/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "❌ Cannot retrieve health status"
fi

echo
echo "🧪 Quick Function Test:"

# Test price function with timing
echo -n "Price API: "
START=$(date +%s%N)
curl -s -f -X POST "$PROD_URL/combined_price" \
    -H "Content-Type: application/json" \
    -d '{"symbol":"BTC-USDT"}' > /dev/null 2>&1
END=$(date +%s%N)
if [ $? -eq 0 ]; then
    DURATION=$(( (END - START) / 1000000 ))
    echo "✅ ${DURATION}ms"
else
    echo "❌ Failed"
fi

# Test OI function with timing  
echo -n "OI API: "
START=$(date +%s%N)
curl -s -f -X POST "$PROD_URL/oi_analysis" \
    -H "Content-Type: application/json" \
    -d '{"symbol":"BTC"}' > /dev/null 2>&1
END=$(date +%s%N)
if [ $? -eq 0 ]; then
    DURATION=$(( (END - START) / 1000000 ))
    echo "✅ ${DURATION}ms"
else
    echo "❌ Failed"
fi

echo
echo "📈 Production check complete"