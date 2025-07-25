#!/bin/bash
# AWS Production Deployment Commands - COPY & PASTE READY

echo "🚀 AWS PRODUCTION DEPLOYMENT"
echo "==========================="
echo ""
echo "📋 STEP 1: SSH to AWS Instance"
echo "ssh -i ~/.ssh/crypto-assistant.pem ec2-user@13.239.14.166"
echo ""
echo "📋 STEP 2: Execute on AWS (copy all commands below):"
echo ""

cat << 'EOF'
# Navigate to project
cd /home/ec2-user/TG-Bot

# Check current branch and commits
echo "Current branch: $(git branch --show-current)"
echo "Current commit: $(git log --oneline -1)"

# Create backup branch
git branch backup-before-secure-deploy-$(date +%Y%m%d-%H%M%S)

# Stop current services (old compromised token)
docker-compose down

# Switch to main branch (where security updates are)
git checkout main

# Pull latest secure code from GitHub
git pull origin main

# MANUAL STEP: Create prod.env with your new production token
# IMPORTANT: Replace YOUR_PRODUCTION_TOKEN with actual token manually on AWS
echo "TELEGRAM_BOT_TOKEN=YOUR_PRODUCTION_TOKEN_HERE" > prod.env
echo "TELEGRAM_CHAT_ID=1145681525" >> prod.env

# Copy to active environment
cp prod.env .env

# Clean deployment (remove old containers)
docker-compose down -v
docker system prune -f

# Fresh build with new token
docker-compose build --no-cache
docker-compose up -d

# Wait for startup
sleep 30

# Validation commands
echo ""
echo "🔍 VALIDATION:"
docker-compose ps
curl -f http://localhost:8001/health
docker logs crypto-telegram-bot | tail -10
docker logs crypto-telegram-bot | grep -i error | wc -l

echo ""
echo "✅ If all commands successful:"
echo "   - @napo_crypto_prod_bot should respond immediately"
echo "   - 4 pending messages will be processed"
echo "   - Production fully operational"
EOF

echo ""
echo "📋 STEP 3: Test in Telegram"
echo "   Send to @napo_crypto_prod_bot:"
echo "   /start"
echo "   /price BTC-USDT"
echo "   /analysis SOL-USDT 15m"
echo ""
echo "🔒 SECURITY: All credentials stay on AWS only - never in GitHub!"