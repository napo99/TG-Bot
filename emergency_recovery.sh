#!/bin/bash

# EMERGENCY AWS PRODUCTION RECOVERY SCRIPT
# =========================================
# 
# This script provides emergency recovery procedures for the AWS production instance
# when the Telegram bot is not responding.
#
# Instance Details:
# - IP: 13.239.14.166
# - Instance ID: i-0be83d48202d03ef1
# - SSH Key: ~/.ssh/crypto-bot-key.pem
# - User: ec2-user
# - Region: ap-southeast-2

set -e

echo "🚨 EMERGENCY AWS PRODUCTION RECOVERY"
echo "===================================="
echo "🎯 Target: 13.239.14.166 (i-0be83d48202d03ef1)"
echo "⏰ Time: $(date)"
echo ""

# Configuration
AWS_IP="13.239.14.166"
INSTANCE_ID="i-0be83d48202d03ef1"
REGION="ap-southeast-2"
SSH_KEY="~/.ssh/crypto-bot-key.pem"
SECURITY_GROUP_ID="sg-0d979f270dae48425"

# Step 1: Check Instance Status
echo "🔍 STEP 1: Checking AWS Instance Status"
echo "======================================="

echo "📊 Instance state:"
aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output table

INSTANCE_STATE=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text)

echo "Instance state: $INSTANCE_STATE"

if [ "$INSTANCE_STATE" != "running" ]; then
    echo "❌ Instance is not running. Starting instance..."
    aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
    echo "⏳ Waiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
    echo "✅ Instance is now running"
    
    # Wait additional time for services to initialize
    echo "⏳ Waiting 60 seconds for services to initialize..."
    sleep 60
else
    echo "✅ Instance is running"
fi

# Step 2: Check Security Groups
echo ""
echo "🛡️  STEP 2: Checking Security Groups"
echo "===================================="

echo "📋 Current security group rules:"
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --query 'SecurityGroups[0].IpPermissions[?FromPort==`8080` || FromPort==`8001` || FromPort==`22`]'

echo ""
echo "🔧 Adding missing security group rules (ignore if they already exist):"

# Add SSH rule
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null && echo "✅ SSH (22) rule added" || echo "ℹ️  SSH (22) rule already exists"

# Add Bot port rule
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp --port 8080 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null && echo "✅ Bot (8080) rule added" || echo "ℹ️  Bot (8080) rule already exists"

# Add Market data port rule
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp --port 8001 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null && echo "✅ Market (8001) rule added" || echo "ℹ️  Market (8001) rule already exists"

# Step 3: Test Basic Connectivity
echo ""
echo "🔗 STEP 3: Testing Basic Connectivity"
echo "====================================="

echo "📡 Testing SSH connectivity..."
if timeout 10 ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i ~/.ssh/crypto-bot-key.pem ec2-user@$AWS_IP "echo 'SSH connection successful'"; then
    echo "✅ SSH connection: WORKING"
    SSH_WORKING=true
else
    echo "❌ SSH connection: FAILED"
    SSH_WORKING=false
fi

echo ""
echo "📡 Testing service ports..."
if timeout 5 bash -c "</dev/tcp/$AWS_IP/8080"; then
    echo "✅ Bot port (8080): OPEN"
    BOT_PORT_OPEN=true
else
    echo "❌ Bot port (8080): CLOSED"
    BOT_PORT_OPEN=false
fi

if timeout 5 bash -c "</dev/tcp/$AWS_IP/8001"; then
    echo "✅ Market port (8001): OPEN"
    MARKET_PORT_OPEN=true
else
    echo "❌ Market port (8001): CLOSED"
    MARKET_PORT_OPEN=false
fi

# Step 4: Service Health Check & Recovery
echo ""
echo "🏥 STEP 4: Service Health Check & Recovery"
echo "=========================================="

if [ "$SSH_WORKING" = true ]; then
    echo "🔍 Checking service status on instance..."
    
    ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i ~/.ssh/crypto-bot-key.pem ec2-user@$AWS_IP "
        echo '📊 System Resources:'
        free -h
        echo ''
        
        echo '🐳 Docker Status:'
        sudo systemctl status docker | head -3
        echo ''
        
        echo '📦 Docker Containers:'
        cd /home/ec2-user/TG-Bot 2>/dev/null || cd /home/ec2-user/crypto-assistant
        sudo docker ps -a
        echo ''
        
        echo '📋 Container Health:'
        curl -s -m 5 http://localhost:8080/health 2>/dev/null && echo ' ✅ Bot health: OK' || echo ' ❌ Bot health: FAILED'
        curl -s -m 5 http://localhost:8001/health 2>/dev/null && echo ' ✅ Market health: OK' || echo ' ❌ Market health: FAILED'
        echo ''
        
        echo '🔄 Restarting Services:'
        sudo docker-compose -f docker-compose.aws.yml down
        sleep 5
        sudo docker-compose -f docker-compose.aws.yml up -d
        echo ''
        
        echo '⏳ Waiting 30 seconds for services to start...'
        sleep 30
        
        echo '📊 Final Status Check:'
        sudo docker ps
        echo ''
        curl -s -m 5 http://localhost:8080/health 2>/dev/null && echo '✅ Bot health: OK' || echo '❌ Bot health: FAILED'
        curl -s -m 5 http://localhost:8001/health 2>/dev/null && echo '✅ Market health: OK' || echo '❌ Market health: FAILED'
    "
else
    echo "❌ Cannot SSH into instance - manual intervention required"
    echo ""
    echo "🆘 MANUAL RECOVERY STEPS:"
    echo "1. Check AWS Console for instance status"
    echo "2. Verify security groups allow SSH (port 22)"
    echo "3. Ensure SSH key permissions: chmod 400 ~/.ssh/crypto-bot-key.pem"
    echo "4. Try SSH manually: ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@$AWS_IP"
fi

# Step 5: External Health Check
echo ""
echo "🌐 STEP 5: External Health Check"
echo "==============================="

echo "🔍 Testing external connectivity..."

if curl -s -m 5 "http://$AWS_IP:8080/health" > /dev/null; then
    echo "✅ Bot external health: ACCESSIBLE"
    echo "   Response: $(curl -s -m 5 "http://$AWS_IP:8080/health")"
else
    echo "❌ Bot external health: NOT ACCESSIBLE"
fi

if curl -s -m 5 "http://$AWS_IP:8001/health" > /dev/null; then
    echo "✅ Market external health: ACCESSIBLE"
    echo "   Response: $(curl -s -m 5 "http://$AWS_IP:8001/health")"
else
    echo "❌ Market external health: NOT ACCESSIBLE"
fi

# Step 6: Webhook Configuration
echo ""
echo "📡 STEP 6: Telegram Webhook Configuration"
echo "========================================"

BOT_TOKEN="8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
WEBHOOK_URL="http://$AWS_IP:8080/webhook"

echo "🔧 Setting Telegram webhook..."
WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" -d "url=$WEBHOOK_URL")
echo "Webhook response: $WEBHOOK_RESPONSE"

echo ""
echo "🔍 Checking webhook info..."
WEBHOOK_INFO=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
echo "Webhook info: $WEBHOOK_INFO"

# Final Summary
echo ""
echo "📋 RECOVERY SUMMARY"
echo "==================="
echo "Instance State: $INSTANCE_STATE"
echo "SSH Working: $SSH_WORKING"
echo "Bot Port Open: $BOT_PORT_OPEN"
echo "Market Port Open: $MARKET_PORT_OPEN"
echo ""
echo "🎯 Next Steps:"
echo "1. Test bot with Telegram message"
echo "2. Monitor logs: ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@$AWS_IP 'cd /home/ec2-user/TG-Bot && sudo docker-compose logs -f'"
echo "3. Check system resources: ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@$AWS_IP 'htop'"
echo ""
echo "✅ Recovery script complete!"