#!/bin/bash

echo "🚀 DEPLOYING NEW 13-MARKET OI SYSTEM"
echo "=================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Desktop."
    exit 1
fi

# Stop any running containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Remove old images to force rebuild
echo "🧹 Cleaning old images..."
docker image prune -f 2>/dev/null || true

# Build and start services
echo "🔨 Building new containers with updated code..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 15

# Health check
echo "🏥 Running health checks..."

# Check market-data service
echo "📊 Testing market-data service..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ Market-data service: HEALTHY"
else
    echo "❌ Market-data service: FAILED"
    docker-compose logs market-data --tail 10
fi

# Test the unified OI endpoint
echo "🎯 Testing /multi_oi endpoint..."
if curl -s -X POST http://localhost:8001/multi_oi \
    -H "Content-Type: application/json" \
    -d '{"base_symbol": "BTC"}' | grep -q "success.*true"; then
    echo "✅ /multi_oi endpoint: WORKING"
else
    echo "❌ /multi_oi endpoint: FAILED"
    docker-compose logs market-data --tail 5
fi

# Check telegram-bot service
echo "🤖 Checking telegram-bot service..."
if docker-compose ps telegram-bot | grep -q "Up"; then
    echo "✅ Telegram-bot service: RUNNING"
else
    echo "❌ Telegram-bot service: FAILED"
    docker-compose logs telegram-bot --tail 10
fi

echo ""
echo "📊 DEPLOYMENT STATUS:"
docker-compose ps

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Test /oi BTC in your Telegram bot"
echo "2. Verify all 13 markets are showing"
echo "3. Check that values are realistic (not $0.0M)"

echo ""
echo "📋 TROUBLESHOOTING:"
echo "• View logs: docker-compose logs [service-name]"
echo "• Restart service: docker-compose restart [service-name]"
echo "• Full restart: docker-compose down && docker-compose up -d"

echo ""
echo "✅ DEPLOYMENT COMPLETE!"