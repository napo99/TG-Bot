#!/bin/bash
# URGENT AWS RECOVERY SCRIPT
# Fix missing module issues and restart services

echo "🚨 URGENT AWS RECOVERY SCRIPT"
echo "Fixing missing module dependencies and restarting services"
echo "Target: AWS Instance 13.239.14.166"
echo "=========================================="

echo "Step 1: Adding files to git"
git add services/market-data/gateio_oi_provider_working.py
git add services/market-data/bitget_oi_provider_working.py
git add aws_production_test.py

echo "Step 2: Committing fixes"
git commit -m "🛠️ Fix missing module dependencies for AWS deployment

- Add gateio_oi_provider_working.py alias
- Add bitget_oi_provider_working.py alias  
- Add AWS production test script
- Resolves 'No module named gateio_oi_provider_working' error

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "Step 3: Pushing to remote repository"
git push origin aws-deployment

echo "Step 4: AWS Recovery Commands"
echo "Execute these commands on the AWS instance:"
echo ""
echo "# SSH into AWS instance:"
echo "ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166"
echo ""
echo "# Pull latest code:"
echo "cd /home/ec2-user/TG-Bot"
echo "git pull origin aws-deployment"
echo ""
echo "# Restart services:"
echo "sudo docker-compose -f docker-compose.aws.yml down"
echo "sudo docker-compose -f docker-compose.aws.yml up -d --build"
echo ""
echo "# Check container status:"
echo "sudo docker ps"
echo "sudo docker logs tg-bot-telegram-bot-1"
echo "sudo docker logs tg-bot-market-data-1"
echo ""
echo "Step 5: Test bot functionality"
echo "Send /start and /price BTC-USDT to Telegram bot"

echo ""
echo "✅ Recovery script complete!"
echo "Execute AWS commands manually to restore service"