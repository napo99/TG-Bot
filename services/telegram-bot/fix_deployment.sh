#!/bin/bash

# AWS Deployment Fix Script
# This script will diagnose and fix the deployment issues

set -e

HOST="13.239.14.166"
KEY_PATH="/Users/screener-m3/.ssh/crypto-bot-key.pem"
REGION="ap-southeast-2"

echo "=== AWS Deployment Fix Script ==="
echo "Target: $HOST"
echo "Region: $REGION"
echo ""

# Function to run SSH commands
run_ssh_command() {
    local cmd="$1"
    echo "Running: $cmd"
    ssh -i "$KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@$HOST "$cmd"
}

# Function to check if command exists
check_command() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check AWS CLI and instance status
echo "Step 1: Checking EC2 instance status..."
if check_command aws; then
    echo "Instance State:"
    aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --region $REGION --query 'Reservations[0].Instances[0].State.Name' --output text
    
    echo "Security Group Rules:"
    aws ec2 describe-security-groups --group-names crypto-bot-sg --region $REGION --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Source:IpRanges[*].CidrIp}' --output table
else
    echo "AWS CLI not available, skipping instance checks"
fi
echo ""

# Step 2: Test SSH connectivity
echo "Step 2: Testing SSH connectivity..."
if run_ssh_command "echo 'SSH connection successful'"; then
    echo "✅ SSH connection established"
else
    echo "❌ SSH connection failed"
    exit 1
fi
echo ""

# Step 3: Check Docker installation and status
echo "Step 3: Checking Docker status..."
run_ssh_command "sudo docker --version || echo 'Docker not installed'"
run_ssh_command "sudo docker-compose --version || echo 'Docker Compose not installed'"
run_ssh_command "sudo systemctl status docker || echo 'Docker service status unknown'"
echo ""

# Step 4: Check current Docker containers
echo "Step 4: Checking current Docker containers..."
run_ssh_command "sudo docker ps -a"
echo ""

# Step 5: Check if project directory exists
echo "Step 5: Checking project directory..."
run_ssh_command "ls -la /home/ec2-user/ | grep crypto"
run_ssh_command "ls -la /home/ec2-user/crypto-assistant/ 2>/dev/null || echo 'Project directory not found'"
echo ""

# Step 6: Check system resources
echo "Step 6: Checking system resources..."
run_ssh_command "free -h"
run_ssh_command "df -h"
run_ssh_command "sudo netstat -tlnp | grep -E '(8080|8001)' || echo 'No services on target ports'"
echo ""

# Step 7: Attempt to start services
echo "Step 7: Attempting to start services..."
run_ssh_command "cd /home/ec2-user/crypto-assistant && pwd && ls -la"
run_ssh_command "cd /home/ec2-user/crypto-assistant && sudo docker-compose down"
run_ssh_command "cd /home/ec2-user/crypto-assistant && sudo docker-compose up -d"
run_ssh_command "cd /home/ec2-user/crypto-assistant && sudo docker-compose ps"
echo ""

# Step 8: Check logs for any errors
echo "Step 8: Checking service logs..."
run_ssh_command "cd /home/ec2-user/crypto-assistant && sudo docker-compose logs --tail=50 telegram-bot"
run_ssh_command "cd /home/ec2-user/crypto-assistant && sudo docker-compose logs --tail=50 market-data"
echo ""

# Step 9: Test health endpoints
echo "Step 9: Testing health endpoints..."
sleep 10  # Give services time to start
if check_command curl; then
    echo "Testing port 8080..."
    curl -v --connect-timeout 10 http://$HOST:8080/health || echo "Port 8080 still not responding"
    
    echo "Testing port 8001..."
    curl -v --connect-timeout 10 http://$HOST:8001/health || echo "Port 8001 still not responding"
else
    echo "curl not available, skipping health endpoint tests"
fi

echo ""
echo "=== Fix script completed ==="
echo "Check the output above for any errors or issues"