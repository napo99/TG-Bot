#!/bin/bash
# PROFESSIONAL AWS DEPLOYMENT - Following Best Practices

echo "🎯 PROFESSIONAL AWS DEPLOYMENT WORKFLOW"
echo "======================================"
echo ""
echo "🔍 CURRENT SITUATION:"
echo "   - AWS: aws-deployment branch (diverged)"
echo "   - GitHub: main branch (latest secure code)"
echo "   - Local: main branch (up to date)"
echo ""
echo "✅ SOLUTION: Clean deployment from GitHub main (source of truth)"
echo ""
echo "📋 COPY THESE COMMANDS TO AWS:"
echo ""

cat << 'EOF'
# Navigate to project
cd /home/ec2-user/TG-Bot

# Stop current services
docker-compose down

# Create backup of current state
git branch backup-diverged-state-$(date +%Y%m%d-%H%M%S)

# Reset to clean state - GitHub main is source of truth
git checkout main
git reset --hard origin/main
git clean -fd

# Pull latest from GitHub (our secure deployment)
git pull origin main

echo ""
echo "🔍 VERIFICATION - Should show latest security commit:"
git log --oneline -3

# MANUAL STEP: Create production environment
# IMPORTANT: Replace YOUR_PRODUCTION_TOKEN with actual token manually on AWS
echo "TELEGRAM_BOT_TOKEN=YOUR_PRODUCTION_TOKEN_HERE" > prod.env
echo "TELEGRAM_CHAT_ID=1145681525" >> prod.env
cp prod.env .env

# Clean deployment
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up -d

# Wait for startup
sleep 30

# Validation
echo ""
echo "🔍 DEPLOYMENT VALIDATION:"
docker-compose ps
curl -f http://localhost:8001/health
docker logs crypto-telegram-bot | tail -5
echo ""
echo "✅ Expected: @napo_crypto_prod_bot should respond immediately"
EOF

echo ""
echo "🎯 PROFESSIONAL WORKFLOW ENFORCED:"
echo "   ✅ GitHub main → AWS production (clean path)"
echo "   ✅ No branch conflicts or divergence"
echo "   ✅ Single source of truth maintained"
echo "   ✅ Professional deployment practices followed"