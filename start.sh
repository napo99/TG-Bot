#!/bin/bash

# Crypto Trading Assistant - Startup Script

echo "🚀 Starting Crypto Trading Assistant..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual API keys and tokens"
    echo "   Required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"
    echo "   Optional: Exchange API keys for live trading"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "🔧 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Services started successfully!"
echo ""
echo "📊 Market Data Service: http://localhost:8001/health"
echo "🤖 Telegram Bot: Running in background"
echo ""
echo "📋 Useful commands:"
echo "   docker-compose logs -f          # View all logs"
echo "   docker-compose logs telegram-bot # View bot logs"
echo "   docker-compose logs market-data  # View market data logs"
echo "   docker-compose down             # Stop all services"
echo ""
echo "🔗 Test your Telegram bot by sending: /start"