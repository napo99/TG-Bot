#!/bin/bash
# ✅ LOCAL VALIDATION - PHASE 4
# Test rolled-back code locally before AWS deployment

echo "✅ PHASE 4: LOCAL VALIDATION AND TESTING"
echo "========================================"
echo ""

echo "🐳 Step 1: Building Docker containers locally..."
docker-compose -f docker-compose.aws.yml build

echo ""
echo "🚀 Step 2: Starting services locally..."
docker-compose -f docker-compose.aws.yml up -d

echo ""
echo "⏳ Step 3: Waiting for services to start..."
sleep 15

echo ""
echo "🔍 Step 4: Checking container health..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 Step 5: Testing health endpoints..."
echo "Testing market data health:"
curl -f http://localhost:8001/health || echo "❌ Market data health check failed"

echo ""
echo "Testing telegram bot health:"
curl -f http://localhost:8080/health || echo "❌ Telegram bot health check failed"

echo ""
echo "📋 Step 6: Checking logs for errors..."
echo "=== Telegram Bot Logs ==="
docker logs crypto-telegram-bot-1 | tail -10 || docker logs tg-bot-telegram-bot-1 | tail -10

echo ""
echo "=== Market Data Logs ==="
docker logs crypto-market-data-1 | tail -10 || docker logs tg-bot-market-data-1 | tail -10

echo ""
echo "🧹 Step 7: Stopping local containers..."
docker-compose -f docker-compose.aws.yml down

echo ""
echo "✅ PHASE 4 COMPLETE - Local validation finished"
echo ""
echo "🔄 Next: Execute PHASE 5 AWS deployment..."