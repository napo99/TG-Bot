#!/bin/bash
# Quick test script for rapid diagnosis
# Purpose: Let Claude quickly identify what's broken and fix it

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔬 QUICK DIAGNOSIS - Crypto Assistant"
echo "===================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Test 1: Docker status
echo -n "Docker running: "
if docker info &> /dev/null; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ FAIL - Docker not running${NC}"
    exit 1
fi

# Test 2: Expected containers
echo -n "Containers running: "
TELEGRAM_RUNNING=$(docker ps --format "{{.Names}}" | grep -c "telegram" || echo "0")
MARKET_RUNNING=$(docker ps --format "{{.Names}}" | grep -c "market" || echo "0")

if [ "$TELEGRAM_RUNNING" -gt 0 ] && [ "$MARKET_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✅ Both services${NC}"
else
    echo -e "${RED}❌ FAIL - Missing: $([ "$TELEGRAM_RUNNING" -eq 0 ] && echo "telegram")$([ "$MARKET_RUNNING" -eq 0 ] && echo " market")${NC}"
    echo "Fix: docker-compose up -d"
    exit 1
fi

# Test 3: Health endpoints
echo -n "Telegram API: "
if curl -s -f http://localhost:8080/health &> /dev/null; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "Fix: Check telegram-bot container logs"
    exit 1
fi

echo -n "Market Data API: "
if curl -s -f http://localhost:8001/health &> /dev/null; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "Fix: Check market-data container logs"
    exit 1
fi

# Test 4: Core functionality
echo -n "Market Analysis: "
RESPONSE=$(curl -s -X POST http://localhost:8001/comprehensive_analysis \
    -H "Content-Type: application/json" \
    -d '{"symbol": "BTC/USDT", "timeframe": "15m"}' \
    -w "%{http_code}")

if [[ "$RESPONSE" == *"200" ]]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "Fix: Check market-data logs for API errors"
    exit 1
fi

# Test 5: Memory pressure (critical for t3.micro)
MEMORY_PERCENT=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
echo -n "Memory usage: ${MEMORY_PERCENT}% "
if [ "$MEMORY_PERCENT" -gt 85 ]; then
    echo -e "${RED}❌ CRITICAL${NC}"
    echo "Fix: docker system prune or restart containers"
    exit 1
elif [ "$MEMORY_PERCENT" -gt 70 ]; then
    echo -e "${YELLOW}⚠️ HIGH${NC}"
else
    echo -e "${GREEN}✅${NC}"
fi

echo -e "\n${GREEN}🎉 ALL TESTS PASSED - System healthy${NC}"
echo ""
echo "Quick diagnostics:"
echo "  Logs: docker-compose logs -f"
echo "  Status: docker-compose ps"
echo "  Restart: docker-compose restart"
echo "  Memory: free -h"