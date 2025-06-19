#!/bin/bash

echo "🚀 Starting Crypto Assistant Services"
echo "===================================="

# Kill any existing services
echo "1. Stopping existing services..."
pkill -f "python.*main.py" 2>/dev/null || true
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2

# Create logs directory
mkdir -p /Users/screener-m3/projects/crypto-assistant/logs

# Start market data service
echo "2. Starting Market Data Service..."
cd /Users/screener-m3/projects/crypto-assistant/services/market-data
nohup python main.py > /Users/screener-m3/projects/crypto-assistant/logs/market-data.log 2>&1 &
MARKET_PID=$!
echo "   Market Data Service started (PID: $MARKET_PID)"

# Wait for market data service to be ready
echo "3. Waiting for Market Data Service to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "   ✅ Market Data Service ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ❌ Market Data Service failed to start"
        exit 1
    fi
    sleep 1
done

# Start Telegram bot
echo "4. Starting Telegram Bot..."
cd /Users/screener-m3/projects/crypto-assistant/services/telegram-bot
nohup python main.py > /Users/screener-m3/projects/crypto-assistant/logs/telegram-bot.log 2>&1 &
BOT_PID=$!
echo "   Telegram Bot started (PID: $BOT_PID)"

# Wait for bot to initialize
sleep 3

# Test VWAP fix
echo "5. Testing VWAP fix..."
VWAP_RESULT=$(curl -s -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "timeframe": "15m"}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['data']['technical_indicators']['vwap']:.2f}\" if data.get('success') else 'ERROR')" 2>/dev/null)

if [[ "$VWAP_RESULT" =~ ^[0-9]+\.[0-9]+$ ]]; then
    echo "   ✅ VWAP: $${VWAP_RESULT}"
    if (( $(echo "$VWAP_RESULT < 105000" | bc -l) )); then
        echo "   🎯 VWAP fix working! (Expected ~104,850)"
    else
        echo "   ⚠️  VWAP still high (Expected ~104,850)"
    fi
else
    echo "   ⚠️  Could not get VWAP value"
fi

# Save PIDs for easy stopping
echo "$MARKET_PID" > /Users/screener-m3/projects/crypto-assistant/.market_pid
echo "$BOT_PID" > /Users/screener-m3/projects/crypto-assistant/.bot_pid

echo ""
echo "🎉 All services started successfully!"
echo "======================================"
echo "📊 Market Data Service: http://localhost:8001"
echo "🤖 Telegram Bot: Running"
echo "📝 Logs: /Users/screener-m3/projects/crypto-assistant/logs/"
echo ""
echo "Test: /analysis btc-usdt 15m in Telegram"
echo ""
echo "To stop all services: ./stop_services.sh"