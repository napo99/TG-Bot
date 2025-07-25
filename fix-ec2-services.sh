#!/bin/bash

# Fix EC2 Docker Services - Run this ON the EC2 instance
# This script should be run after SSH'ing into the instance

echo "🔧 Fixing EC2 Docker Services"
echo "============================"

# Navigate to project directory
cd /home/ec2-user/crypto-assistant

echo "📋 Current Docker status:"
sudo docker ps -a

echo ""
echo "🔍 Checking docker-compose services:"
sudo docker-compose -f docker-compose.aws.yml ps

echo ""
echo "🛑 Stopping any existing services:"
sudo docker-compose -f docker-compose.aws.yml down

echo ""
echo "🧹 Cleaning up Docker resources:"
sudo docker system prune -f

echo ""
echo "🔧 Setting up environment variables:"
# Check if .env file exists and has proper values
if [ -f .env ]; then
    echo "✅ .env file exists"
    cat .env
else
    echo "❌ .env file missing - creating it"
    cat > .env << EOF
# Telegram Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=1145681525

# Service Configuration  
PORT=5000
MARKET_DATA_URL=http://market-data:8001

# Redis Configuration
REDIS_URL=redis://redis:6379
EOF
fi

echo ""
echo "🚀 Starting services:"
sudo docker-compose -f docker-compose.aws.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "📊 Service status:"
sudo docker-compose -f docker-compose.aws.yml ps

echo ""
echo "🩺 Health checks:"
echo "Telegram Bot Health:"
curl -s http://localhost:8080/health || echo "❌ Telegram bot not responding"

echo ""
echo "Market Data Health:"
curl -s http://localhost:8001/health || echo "❌ Market data not responding"

echo ""
echo "📋 Container logs (last 10 lines):"
echo "=== Telegram Bot Logs ==="
sudo docker-compose -f docker-compose.aws.yml logs --tail=10 telegram-bot

echo ""
echo "=== Market Data Logs ==="
sudo docker-compose -f docker-compose.aws.yml logs --tail=10 market-data

echo ""
echo "🔍 System resources:"
free -h
echo ""
echo "📈 Docker stats:"
sudo docker stats --no-stream

echo ""
echo "✅ Fix complete! Services should be running now."
echo "Test from outside: curl http://13.239.14.166:8080/health"