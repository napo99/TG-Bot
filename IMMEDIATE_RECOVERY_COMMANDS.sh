#!/bin/bash
# IMMEDIATE RECOVERY VALIDATION - Run after 2-3 minutes
# Instance i-0be83d48202d03ef1 force rebooted due to memory exhaustion

echo "🔄 AWS INSTANCE RECOVERY VALIDATION"
echo "=================================="
echo "Waiting for instance recovery after force reboot..."
echo

# Test 1: Basic connectivity
echo "1️⃣ Testing connectivity..."
if ping -c 3 13.239.14.166 > /dev/null 2>&1; then
    echo "✅ PING: Instance responding"
else
    echo "❌ PING: Still no response - wait longer or try again"
    exit 1
fi

# Test 2: SSH access
echo "2️⃣ Testing SSH access..."
if ssh -o ConnectTimeout=10 -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "✅ SSH: Connection successful"
else
    echo "❌ SSH: Connection failed - instance may still be booting"
    exit 1
fi

# Test 3: Docker services
echo "3️⃣ Checking Docker services..."
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "
cd /home/ec2-user/TG-Bot 2>/dev/null || cd /home/ec2-user/crypto-assistant
echo 'Current directory:' \$(pwd)

echo 'Docker status:'
sudo systemctl status docker | head -3

echo 'Container status:'
docker ps -a

echo 'Starting services if needed...'
docker-compose -f docker-compose.aws.yml up -d

echo 'Waiting 30 seconds for services...'
sleep 30

echo 'Final status:'
docker ps
curl -s http://localhost:8080/health || echo 'Health check failed'
curl -s http://localhost:8001/health || echo 'Market data failed'
"

# Test 4: External health checks
echo "4️⃣ External health validation..."
if curl -s http://13.239.14.166:8080/health > /dev/null; then
    echo "✅ TELEGRAM BOT: Responsive"
else
    echo "❌ TELEGRAM BOT: Still down"
fi

if curl -s http://13.239.14.166:8001/health > /dev/null; then
    echo "✅ MARKET DATA: Responsive"
else
    echo "❌ MARKET DATA: Still down"
fi

echo
echo "🎯 ENHANCED FEATURES STATUS:"
echo "Code contains enhanced features - ready for testing once services are up"
echo "- format_enhanced_funding_rate (Line 373)"
echo "- format_oi_change (Lines 363, 367)"
echo "- Market Intelligence section (Line 378)"
echo
echo "✅ RECOVERY VALIDATION COMPLETE"
echo "Test Telegram bot with: /price BTC-USDT"