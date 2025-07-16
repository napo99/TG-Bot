#!/bin/bash
# URGENT: AWS Instance Recovery Script
# Instance 13.239.14.166 (i-0be83d48202d03ef1) is DOWN

echo "🚨 EMERGENCY AWS RECOVERY"
echo "========================="

# Step 1: Check instance status
echo "1️⃣ Checking instance status..."
aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2 \
  --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' --output table

# Step 2: Start instance if stopped
echo "2️⃣ Starting instance..."
aws ec2 start-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2

# Step 3: Wait for running state
echo "3️⃣ Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2

# Step 4: Get current IP
echo "4️⃣ Getting current IP address..."
NEW_IP=$(aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "Current IP: $NEW_IP"

# Step 5: Test connectivity
echo "5️⃣ Testing connectivity..."
ping -c 3 $NEW_IP

# Step 6: SSH and recover services
echo "6️⃣ Recovering services..."
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@$NEW_IP "
echo 'Connected to instance'
cd /home/ec2-user/TG-Bot 2>/dev/null || cd /home/ec2-user/crypto-assistant
pwd

echo 'Checking Docker status...'
sudo systemctl status docker | head -3

echo 'Checking containers...'
docker ps -a

echo 'Starting services...'
docker-compose -f docker-compose.aws.yml up -d

echo 'Waiting 30 seconds...'
sleep 30

echo 'Testing health endpoints...'
curl -s http://localhost:8080/health || echo 'Bot health failed'
curl -s http://localhost:8001/health || echo 'Market data health failed'

echo 'Container status:'
docker ps
"

echo "✅ Recovery script complete"
echo "Test externally: curl http://$NEW_IP:8080/health"