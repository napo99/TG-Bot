#!/bin/bash
set -e

echo "🚀 Starting Crypto Assistant on Fly.io..."
echo "📅 $(date)"

# Create logs directory
mkdir -p /app/logs

# Start market-data service in background
echo "📊 Starting market-data service..."
cd /app/services/market-data
python main.py > /app/logs/market-data.log 2>&1 &
MARKET_DATA_PID=$!
echo "📊 Market-data PID: $MARKET_DATA_PID"

# Wait for market-data to be ready
echo "⏳ Waiting for market-data service..."
sleep 15

# Check if market-data is healthy
for i in {1..30}; do
  if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Market-data service is healthy"
    break
  fi
  echo "⏳ Waiting for market-data... ($i/30)"
  sleep 3
done

# Verify market-data is actually running
if ! curl -f http://localhost:8001/health >/dev/null 2>&1; then
  echo "❌ Market-data service failed to start"
  echo "📋 Market-data logs:"
  tail -20 /app/logs/market-data.log
  exit 1
fi

# Start telegram-bot service
echo "🤖 Starting telegram-bot service..."
cd /app/services/telegram-bot
python main.py > /app/logs/telegram-bot.log 2>&1 &
TELEGRAM_BOT_PID=$!
echo "🤖 Telegram-bot PID: $TELEGRAM_BOT_PID"

echo "🎯 All services started successfully!"
echo "📊 Market-data PID: $MARKET_DATA_PID"
echo "🤖 Telegram-bot PID: $TELEGRAM_BOT_PID"
echo "🔗 Health check: http://localhost:8001/health"

# Function to handle shutdown
shutdown() {
  echo "🛑 Shutting down services..."
  kill $TELEGRAM_BOT_PID $MARKET_DATA_PID 2>/dev/null || true
  wait $TELEGRAM_BOT_PID $MARKET_DATA_PID 2>/dev/null || true
  echo "✅ Shutdown complete"
  exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?