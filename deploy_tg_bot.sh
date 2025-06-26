#!/bin/bash

echo "🚀 DEPLOYING UPDATED TELEGRAM BOT"
echo "================================="
echo ""

# Check if Docker is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not available"
    echo "📋 Please use manual Docker Desktop steps in rebuild_telegram_bot.md"
    exit 1
fi

echo "🔍 Checking current status..."
docker-compose ps | grep telegram-bot

echo ""
echo "🛑 Stopping existing Telegram bot..."
docker-compose stop telegram-bot

echo ""
echo "🔨 Rebuilding Telegram bot with updated code..."
docker-compose build telegram-bot

echo ""
echo "🚀 Starting updated Telegram bot..."
docker-compose up -d telegram-bot

echo ""
echo "⏱️  Waiting for startup..."
sleep 5

echo ""
echo "📋 Container status:"
docker-compose ps | grep telegram-bot

echo ""
echo "📊 Recent logs:"
docker-compose logs telegram-bot --tail 10

echo ""
echo "✅ DEPLOYMENT COMPLETE"
echo "====================" 
echo "🤖 Test in Telegram: /oi BTC"
echo "📊 Expected: ~275K BTC (~$30B) across 13 markets"
echo ""
echo "🔍 Monitor logs: docker-compose logs telegram-bot -f"