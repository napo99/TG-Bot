#!/bin/bash

# AWS EC2 Deployment Script for Crypto Assistant
# Target: t3.micro (1GB RAM, 2 vCPU) - Free Tier

set -e

echo "🚀 Starting AWS Deployment - Demo Ready"
echo "========================================"

# Configuration
INSTANCE_TYPE="t3.micro"
KEY_NAME="crypto-bot-key"
SECURITY_GROUP="crypto-bot-sg"
REGION="ap-southeast-2"  # Sydney region (free tier eligible)
AMI_ID="ami-0146fc9ad419e2cfd"  # Amazon Linux 2 for Sydney

echo "📋 Deployment Configuration:"
echo "   Instance Type: $INSTANCE_TYPE"
echo "   Region: $REGION"
echo "   Key Name: $KEY_NAME"
echo ""

# 1. Create Key Pair (if not exists)
echo "🔑 Creating SSH Key Pair..."
aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION 2>/dev/null || \
aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION --query 'KeyMaterial' --output text > ~/.ssh/${KEY_NAME}.pem
chmod 400 ~/.ssh/${KEY_NAME}.pem

# 2. Create Security Group (if not exists)
echo "🛡️  Creating Security Group..."
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || \
aws ec2 create-security-group --group-name $SECURITY_GROUP --description "Crypto Bot Security Group" --region $REGION --query 'GroupId' --output text)

# Add rules
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null || true

# 3. Launch EC2 Instance
echo "🖥️  Launching EC2 Instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=crypto-bot-demo}]' \
    --user-data file://./aws-setup-script.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"

# 4. Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# 5. Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "🎉 AWS Deployment Complete!"
echo "=========================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "SSH Access: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo "🔄 Next Steps:"
echo "1. Wait 2-3 minutes for setup to complete"
echo "2. SSH into instance and check logs: docker-compose logs -f"
echo "3. Set webhook: curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook -d url=http://$PUBLIC_IP:8080/webhook"
echo "4. Test bot commands"
echo ""
echo "📊 Monitoring:"
echo "   Bot logs: ssh ec2-user@$PUBLIC_IP 'docker-compose logs telegram-bot'"
echo "   Market data logs: ssh ec2-user@$PUBLIC_IP 'docker-compose logs market-data'"
echo "   System resources: ssh ec2-user@$PUBLIC_IP 'htop'"