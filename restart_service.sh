#!/bin/bash
echo "Stopping market data service..."
pkill -f "python.*main.py" 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 3

echo "Starting market data service..."
cd /Users/screener-m3/projects/crypto-assistant/services/market-data
python main.py > /tmp/market-data-restart.log 2>&1 &

echo "Waiting for service to start..."
sleep 5

echo "Testing service..."
curl -s http://localhost:8001/health | grep -q "success" && echo "✅ Service is running" || echo "❌ Service failed to start"