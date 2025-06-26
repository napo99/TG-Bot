#!/bin/bash

echo "🛑 Stopping Crypto Assistant Services"
echo "====================================="

# Read PIDs if they exist
MARKET_PID=""
BOT_PID=""

if [ -f /Users/screener-m3/projects/crypto-assistant/.market_pid ]; then
    MARKET_PID=$(cat /Users/screener-m3/projects/crypto-assistant/.market_pid)
fi

if [ -f /Users/screener-m3/projects/crypto-assistant/.bot_pid ]; then
    BOT_PID=$(cat /Users/screener-m3/projects/crypto-assistant/.bot_pid)
fi

# Stop services by PID
if [ -n "$MARKET_PID" ]; then
    echo "Stopping Market Data Service (PID: $MARKET_PID)..."
    kill $MARKET_PID 2>/dev/null || true
fi

if [ -n "$BOT_PID" ]; then
    echo "Stopping Telegram Bot (PID: $BOT_PID)..."
    kill $BOT_PID 2>/dev/null || true
fi

# Force kill any remaining processes
echo "Force stopping any remaining services..."
pkill -f "python.*main.py" 2>/dev/null || true
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true

# Clean up PID files
rm -f /Users/screener-m3/projects/crypto-assistant/.market_pid
rm -f /Users/screener-m3/projects/crypto-assistant/.bot_pid

sleep 2

echo "✅ All services stopped"