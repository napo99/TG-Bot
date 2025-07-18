#!/bin/bash
# 🚀 AWS DEPLOYMENT - PHASE 5
# Deploy proven working code to production

echo "🚀 PHASE 5: DEPLOYING TO AWS PRODUCTION"
echo "======================================="
echo ""

echo "🔑 Step 1: Connecting to AWS production instance..."
echo "Execute these commands on AWS:"
echo ""
echo "# SSH to AWS production"
echo "ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166"
echo ""
echo "# Navigate to project directory"
echo "cd /home/ec2-user/TG-Bot"
echo ""
echo "# Pull latest rollback changes"
echo "git fetch origin"
echo "git reset --hard origin/aws-deployment"
echo ""
echo "# Stop current broken containers"
echo "docker-compose -f docker-compose.aws.yml down"
echo ""
echo "# Remove old images"
echo "docker image prune -f"
echo ""
echo "# Rebuild with rolled-back code"
echo "docker-compose -f docker-compose.aws.yml build --no-cache"
echo ""
echo "# Start services"
echo "docker-compose -f docker-compose.aws.yml up -d"
echo ""
echo "# Wait for startup"
echo "sleep 30"
echo ""
echo "# Check container status"
echo "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'"
echo ""
echo "✅ PHASE 5 COMPLETE - AWS deployment finished"
echo ""
echo "🔄 Next: Execute PHASE 6 production verification..."