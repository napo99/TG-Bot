#!/bin/bash

# Execute AWS deployment fixes systematically
echo "🚀 Starting AWS Deployment Fixes"
echo "==============================="

# Set the working directory
cd /Users/screener-m3/projects/crypto-assistant

# Step 1: Fix Security Groups
echo "📋 Step 1: Fixing Security Groups"
echo "=================================="

# Make sure the script is executable
chmod +x fix-security-groups.sh

# Execute the security group fix
./fix-security-groups.sh

echo ""
echo "📋 Step 2: SSH into EC2 and Fix Services"
echo "========================================"

# Copy the fix script to EC2 instance
echo "📁 Copying fix script to EC2..."
scp -i ~/.ssh/crypto-bot-key.pem fix-ec2-services.sh ec2-user@13.239.14.166:~/

# SSH into instance and execute the fix
echo "🔧 Executing fix on EC2 instance..."
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "chmod +x fix-ec2-services.sh && ./fix-ec2-services.sh"

echo ""
echo "📋 Step 3: Test Health Endpoints"
echo "==============================="

# Test bot health
echo "🩺 Testing bot health..."
curl -s http://13.239.14.166:8080/health

echo ""
echo "🩺 Testing market data health..."
curl -s http://13.239.14.166:8001/health

echo ""
echo "📋 Step 4: Set Webhook"
echo "===================="

# Set webhook
echo "🔗 Setting webhook..."
curl -X POST "https://api.telegram.org/bot8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8/setWebhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "url=http://13.239.14.166:8080/webhook"

echo ""
echo "✅ AWS Deployment Fixes Complete!"
echo "================================="