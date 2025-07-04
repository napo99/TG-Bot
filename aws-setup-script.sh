#!/bin/bash

# AWS EC2 Instance Setup Script
# Automatically installs Docker and deploys crypto bot

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "🚀 Starting AWS EC2 Setup for Crypto Bot Demo"

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install Git
yum install -y git

# Clone the repository
cd /home/ec2-user
git clone https://github.com/screener-m3/crypto-assistant.git
cd crypto-assistant

# Switch to AWS deployment branch
git checkout aws-deployment || git checkout main

# Create environment file with placeholder values
cat > .env << EOF
# Telegram Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE

# Service Configuration  
PORT=5000
MARKET_DATA_URL=http://market-data:8001

# Redis Configuration
REDIS_URL=redis://redis:6379
EOF

# Set proper permissions
chown -R ec2-user:ec2-user /home/ec2-user/crypto-assistant
chmod +x /home/ec2-user/crypto-assistant/deploy-aws.sh

# Build and start services
cd /home/ec2-user/crypto-assistant
docker-compose -f docker-compose.aws.yml build
docker-compose -f docker-compose.aws.yml up -d

# Install monitoring tools
yum install -y htop iotop

# Create status check script
cat > /home/ec2-user/check-status.sh << 'EOF'
#!/bin/bash
echo "🔍 Crypto Bot Status Check"
echo "========================="
echo ""
echo "📊 System Resources:"
free -h
echo ""
echo "🐳 Docker Containers:"
docker-compose -f /home/ec2-user/crypto-assistant/docker-compose.aws.yml ps
echo ""
echo "📈 Memory Usage by Container:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
echo ""
echo "🔗 Service Health:"
curl -s http://localhost:8080/health || echo "Telegram bot health check failed"
curl -s http://localhost:8001/health || echo "Market data health check failed"
echo ""
echo "📋 Recent Logs (last 10 lines):"
echo "--- Telegram Bot ---"
docker-compose -f /home/ec2-user/crypto-assistant/docker-compose.aws.yml logs --tail=10 telegram-bot
echo "--- Market Data ---"
docker-compose -f /home/ec2-user/crypto-assistant/docker-compose.aws.yml logs --tail=10 market-data
EOF

chmod +x /home/ec2-user/check-status.sh

# Create restart script
cat > /home/ec2-user/restart-services.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Crypto Bot Services"
cd /home/ec2-user/crypto-assistant
docker-compose -f docker-compose.aws.yml restart
echo "✅ Services restarted"
EOF

chmod +x /home/ec2-user/restart-services.sh

echo "✅ AWS EC2 Setup Complete!"
echo "🎯 Demo environment ready for testing"