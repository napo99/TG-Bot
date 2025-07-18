#!/bin/bash

# Fix AWS Security Groups for Crypto Bot
# Opens required ports: 8080 (webhook), 8001 (market data)

echo "🔧 Fixing Security Groups for Crypto Bot"
echo "======================================"

SECURITY_GROUP="crypto-bot-sg"
REGION="ap-southeast-2"

# Get security group ID
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION --query 'SecurityGroups[0].GroupId' --output text)

echo "Security Group ID: $SECURITY_GROUP_ID"

# Add port 8080 (webhook)
echo "🔓 Opening port 8080 (webhook)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8080 \
    --cidr 0.0.0.0/0 \
    --region $REGION \
    2>/dev/null || echo "Port 8080 already open"

# Add port 8001 (market data)
echo "🔓 Opening port 8001 (market data)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8001 \
    --cidr 0.0.0.0/0 \
    --region $REGION \
    2>/dev/null || echo "Port 8001 already open"

echo "✅ Security groups updated!"
echo ""
echo "🔍 Current security group rules:"
aws ec2 describe-security-groups --group-ids $SECURITY_GROUP_ID --region $REGION --query 'SecurityGroups[0].IpPermissions'

echo ""
echo "🚀 Next: SSH into instance and start services"
echo "ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166"