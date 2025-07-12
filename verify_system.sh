#!/bin/bash
# System Health Verification Script
# Usage: ./verify_system.sh [--full]

set -e

echo "🔍 Crypto Trading Bot System Health Check"
echo "========================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ "$2" = "OK" ]; then
        echo -e "${GREEN}✅ $1${NC}"
    elif [ "$2" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

# Check if running in project directory
if [ ! -f "docker-compose.yml" ]; then
    print_status "Not in crypto-assistant project directory" "ERROR"
    exit 1
fi

print_status "Project directory verified" "OK"

# 1. Check Docker availability
if ! command -v docker &> /dev/null; then
    print_status "Docker not installed or not in PATH" "ERROR"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_status "Docker daemon not running" "ERROR"
    exit 1
fi

print_status "Docker daemon running" "OK"

# 2. Check containers
echo ""
echo "📦 Container Status:"
echo "-------------------"

telegram_running=$(docker ps --filter "name=crypto-telegram-bot" --format "{{.Names}}" | wc -l)
market_running=$(docker ps --filter "name=crypto-market-data" --format "{{.Names}}" | wc -l)

if [ "$telegram_running" -eq 0 ]; then
    print_status "Telegram bot container not running" "ERROR"
    echo "   Run: docker-compose up -d"
    exit 1
else
    print_status "Telegram bot container running" "OK"
fi

if [ "$market_running" -eq 0 ]; then
    print_status "Market data container not running" "ERROR"
    echo "   Run: docker-compose up -d"
    exit 1
else
    print_status "Market data container running" "OK"
fi

# 3. Check service endpoints
echo ""
echo "🌐 Service Endpoints:"
echo "--------------------"

# Check market data service
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    print_status "Market data service responding (port 8001)" "OK"
else
    print_status "Market data service not responding" "ERROR"
    echo "   Check: docker logs crypto-market-data"
    exit 1
fi

# Check telegram bot service
if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    print_status "Telegram bot service responding (port 8080)" "OK"
else
    print_status "Telegram bot service not responding" "ERROR"
    echo "   Check: docker logs crypto-telegram-bot"
    exit 1
fi

# 4. Test market data API
echo ""
echo "🧪 API Functionality:"
echo "---------------------"

api_response=$(curl -s -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "timeframe": "15m"}' | head -c 100)

if echo "$api_response" | grep -q "success"; then
    print_status "Market data API functional" "OK"
else
    print_status "Market data API not responding correctly" "ERROR"
    echo "   Response: $api_response"
    exit 1
fi

# 5. Check for errors in logs
echo ""
echo "📋 Log Analysis:"
echo "----------------"

telegram_errors=$(docker logs --tail=50 crypto-telegram-bot 2>&1 | grep -i error | wc -l)
market_errors=$(docker logs --tail=50 crypto-market-data 2>&1 | grep -i error | wc -l)

if [ "$telegram_errors" -gt 0 ]; then
    print_status "Telegram bot has $telegram_errors errors in recent logs" "WARN"
    echo "   Check: docker logs crypto-telegram-bot | grep -i error"
else
    print_status "No errors in telegram bot logs" "OK"
fi

if [ "$market_errors" -gt 0 ]; then
    print_status "Market data service has $market_errors errors in recent logs" "WARN"
    echo "   Check: docker logs crypto-market-data | grep -i error"
else
    print_status "No errors in market data logs" "OK"
fi

# 6. Check resource usage
echo ""
echo "💾 Resource Usage:"
echo "------------------"

# Get memory usage for containers
telegram_memory=$(docker stats --no-stream crypto-telegram-bot 2>/dev/null | tail -n 1 | awk '{print $4}' | sed 's/MiB//')
market_memory=$(docker stats --no-stream crypto-market-data 2>/dev/null | tail -n 1 | awk '{print $4}' | sed 's/MiB//')

if [ ! -z "$telegram_memory" ] && [ ! -z "$market_memory" ]; then
    total_memory=$(echo "$telegram_memory + $market_memory" | bc 2>/dev/null || echo "unknown")
    if [ "$total_memory" != "unknown" ] && [ $(echo "$total_memory < 400" | bc) -eq 1 ]; then
        print_status "Memory usage: ${total_memory}MB (within limits)" "OK"
    else
        print_status "Memory usage: ${total_memory}MB (check if excessive)" "WARN"
    fi
else
    print_status "Memory usage information unavailable" "WARN"
fi

# 7. Full test if requested
if [ "$1" = "--full" ]; then
    echo ""
    echo "🎯 Full System Test:"
    echo "-------------------"
    
    # Test specific API endpoints
    echo "Testing price endpoint..."
    price_test=$(curl -s -X POST http://localhost:8001/price \
      -H "Content-Type: application/json" \
      -d '{"symbol": "BTC/USDT"}')
    
    if echo "$price_test" | grep -q "success"; then
        print_status "Price endpoint working" "OK"
    else
        print_status "Price endpoint failed" "ERROR"
    fi
    
    echo "Testing volume scan endpoint..."
    volume_test=$(curl -s -X POST http://localhost:8001/volume_scan \
      -H "Content-Type: application/json" \
      -d '{"symbol": "BTC/USDT"}')
    
    if echo "$volume_test" | grep -q "success"; then
        print_status "Volume scan endpoint working" "OK"
    else
        print_status "Volume scan endpoint failed" "ERROR"
    fi
fi

echo ""
echo "🎉 System Health Check Complete!"
echo "================================"

# Summary
total_checks=6
if [ "$telegram_errors" -gt 0 ] || [ "$market_errors" -gt 0 ]; then
    print_status "System operational with warnings" "WARN"
    echo ""
    echo "💡 Next steps:"
    echo "   • Review error logs for any issues"
    echo "   • Test bot commands in Telegram"
    echo "   • Monitor resource usage"
else
    print_status "All systems operational" "OK"
    echo ""
    echo "💡 System ready for:"
    echo "   • Telegram bot commands"
    echo "   • Market data analysis"
    echo "   • Development work"
fi

echo ""
echo "📖 For troubleshooting, see: SYSTEM_PROTECTION_GUIDE.md"