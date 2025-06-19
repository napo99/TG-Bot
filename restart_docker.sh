#!/bin/bash
echo "🔄 Restarting Crypto Assistant with VWAP Fix"
echo "============================================"

# Stop existing containers
echo "1. Stopping existing containers..."
docker-compose down

# Clean up
echo "2. Cleaning up old containers and images..."
docker system prune -f

# Rebuild with latest code (includes VWAP fix)
echo "3. Building with VWAP fix..."
docker-compose build --no-cache

# Start services
echo "4. Starting services..."
docker-compose up -d

# Wait for health check
echo "5. Waiting for services to start..."
sleep 10

# Test VWAP fix
echo "6. Testing VWAP fix..."
curl -s -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "timeframe": "15m"}' | \
  jq '.data.technical_indicators.vwap' || echo "Service starting up..."

echo ""
echo "✅ Docker restart complete!"
echo "Test: /analysis btc-usdt 15m in Telegram"
echo "Expected VWAP: ~$104,850 (was ~$105,091)"