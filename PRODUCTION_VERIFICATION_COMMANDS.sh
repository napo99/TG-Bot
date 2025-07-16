#!/bin/bash
# 🔍 PRODUCTION VERIFICATION - PHASE 6
# Verify production restoration and monitor stability

echo "🔍 PHASE 6: PRODUCTION VERIFICATION"
echo "==================================="
echo ""

echo "Execute these commands on AWS production instance:"
echo ""

echo "🔍 Step 1: Check container health status..."
echo "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'"
echo ""

echo "🌐 Step 2: Test health endpoints..."
echo "curl -f http://localhost:8080/health"
echo "curl -f http://localhost:8001/health"
echo ""

echo "📱 Step 3: Test Telegram bot functionality..."
echo "# Send these commands to your Telegram bot:"
echo "# /start"
echo "# /price BTC-USDT"
echo "# /price ETH-USDT"
echo ""

echo "📋 Step 4: Monitor logs for errors..."
echo "docker logs tg-bot-telegram-bot-1 | tail -20"
echo "docker logs tg-bot-market-data-1 | tail -20"
echo ""

echo "📊 Step 5: Check system resources..."
echo "free -m"
echo "df -h"
echo ""

echo "⏱️ Step 6: Monitor stability (5 minutes)..."
echo "# Watch container status for 5 minutes"
echo "watch -n 30 'docker ps --format \"table {{.Names}}\\t{{.Status}}\"'"
echo ""

echo "SUCCESS CRITERIA:"
echo "✅ All containers show 'healthy' status"
echo "✅ Health endpoints return 200 OK"
echo "✅ Telegram bot responds to commands"
echo "✅ No errors in logs"
echo "✅ System resources stable"
echo ""
echo "🎉 If all criteria met: 48-HOUR OUTAGE RESOLVED!"
echo ""
echo "🔄 Next: Execute PHASE 7 documentation..."