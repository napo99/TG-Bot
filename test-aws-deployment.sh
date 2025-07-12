#!/bin/bash

# AWS Deployment Test Script
# Tests all critical functionality after deployment

if [ -z "$1" ]; then
    echo "Usage: $0 <EC2_PUBLIC_IP>"
    echo "Example: $0 54.123.45.67"
    exit 1
fi

PUBLIC_IP=$1
BASE_URL="http://$PUBLIC_IP:8080"

echo "🧪 Testing AWS Deployment - $PUBLIC_IP"
echo "====================================="

# Test 1: Health checks
echo "1️⃣ Testing health endpoints..."
echo -n "   Telegram Bot Health: "
if curl -s -f "$BASE_URL/health" > /dev/null; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

echo -n "   Market Data Health: "
if curl -s -f "http://$PUBLIC_IP:8001/health" > /dev/null; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 2: Webhook endpoint
echo "2️⃣ Testing webhook endpoint..."
echo -n "   Webhook accepts POST: "
response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/webhook" \
    -H "Content-Type: application/json" \
    -d '{"update_id": 1, "message": {"message_id": 1, "text": "/test"}}' \
    -o /dev/null)

if [ "$response" = "200" ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL (HTTP $response)"
fi

# Test 3: Market Data API
echo "3️⃣ Testing market data API..."
echo -n "   Price endpoint: "
if curl -s -X POST "http://$PUBLIC_IP:8001/price" \
    -H "Content-Type: application/json" \
    -d '{"symbol": "BTC-USDT"}' | grep -q "price\|success"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 4: Memory usage check
echo "4️⃣ Checking memory usage..."
echo "   SSH into instance and run: ./check-status.sh"

# Test 5: Set webhook for demo
echo "5️⃣ Setting up webhook for demo..."
echo ""
echo "🔧 Manual steps for demo setup:"
echo "1. SSH into instance:"
echo "   ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@$PUBLIC_IP"
echo ""
echo "2. Set your bot token:"
echo "   cd crypto-assistant"
echo "   sed -i 's/YOUR_BOT_TOKEN_HERE/8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8/' .env"
echo "   sed -i 's/YOUR_CHAT_ID_HERE/1145681525/' .env"
echo "   docker-compose -f docker-compose.aws.yml restart"
echo ""
echo "3. Set webhook URL:"
echo "   curl -X POST 'https://api.telegram.org/bot8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8/setWebhook' -d 'url=$BASE_URL/webhook'"
echo ""
echo "4. Test bot commands:"
echo "   Send /price BTC-USDT to your bot"
echo ""
echo "📊 Monitoring commands:"
echo "   System status: ./check-status.sh"
echo "   View logs: docker-compose -f docker-compose.aws.yml logs -f"
echo "   Restart services: ./restart-services.sh"
echo ""
echo "🎯 Demo Ready! Public URL: $BASE_URL"