#!/bin/bash

# Security Group Fix Script
# This script will ensure the security group has the correct rules

set -e

REGION="ap-southeast-2"
GROUP_NAME="crypto-bot-sg"

echo "=== Security Group Configuration Fix ==="
echo "Group: $GROUP_NAME"
echo "Region: $REGION"
echo ""

# Function to check if command exists
check_command() {
    command -v "$1" >/dev/null 2>&1
}

if ! check_command aws; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Get security group ID
echo "Getting security group ID..."
GROUP_ID=$(aws ec2 describe-security-groups --group-names "$GROUP_NAME" --region "$REGION" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)

if [ "$GROUP_ID" == "None" ] || [ -z "$GROUP_ID" ]; then
    echo "❌ Security group '$GROUP_NAME' not found!"
    echo "Creating security group..."
    
    # Create security group
    GROUP_ID=$(aws ec2 create-security-group \
        --group-name "$GROUP_NAME" \
        --description "Security group for crypto bot deployment" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text)
    
    echo "✅ Created security group: $GROUP_ID"
fi

echo "Security Group ID: $GROUP_ID"
echo ""

# Function to add ingress rule if it doesn't exist
add_ingress_rule() {
    local port=$1
    local protocol=$2
    local cidr=$3
    
    echo "Checking rule for port $port..."
    
    # Check if rule already exists
    existing_rule=$(aws ec2 describe-security-groups \
        --group-ids "$GROUP_ID" \
        --region "$REGION" \
        --query "SecurityGroups[0].IpPermissions[?FromPort==\`$port\` && ToPort==\`$port\` && IpProtocol==\`$protocol\`]" \
        --output text 2>/dev/null)
    
    if [ -z "$existing_rule" ]; then
        echo "Adding ingress rule for port $port..."
        aws ec2 authorize-security-group-ingress \
            --group-id "$GROUP_ID" \
            --protocol "$protocol" \
            --port "$port" \
            --cidr "$cidr" \
            --region "$REGION"
        echo "✅ Added rule for port $port"
    else
        echo "✅ Rule for port $port already exists"
    fi
}

# Add required ingress rules
echo "Configuring ingress rules..."

# SSH (port 22)
add_ingress_rule 22 tcp "0.0.0.0/0"

# Telegram Bot (port 8080)
add_ingress_rule 8080 tcp "0.0.0.0/0"

# Market Data Service (port 8001)
add_ingress_rule 8001 tcp "0.0.0.0/0"

# HTTP (port 80) - optional
add_ingress_rule 80 tcp "0.0.0.0/0"

# HTTPS (port 443) - optional
add_ingress_rule 443 tcp "0.0.0.0/0"

echo ""
echo "Current security group rules:"
aws ec2 describe-security-groups \
    --group-ids "$GROUP_ID" \
    --region "$REGION" \
    --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,Port:FromPort,ToPort:ToPort,Source:IpRanges[*].CidrIp}' \
    --output table

echo ""
echo "=== Security group configuration completed ==="