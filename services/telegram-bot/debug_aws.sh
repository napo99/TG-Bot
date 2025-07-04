#!/bin/bash

# Set environment
export AWS_DEFAULT_REGION=ap-southeast-2
export PATH=/usr/local/bin:$PATH

echo "=== EC2 Instance Status Check ==="
aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --query 'Reservations[0].Instances[0].{State:State.Name,PublicIP:PublicIpAddress,PrivateIP:PrivateIpAddress,InstanceType:InstanceType,SecurityGroups:SecurityGroups[*].GroupName,KeyName:KeyName}'

echo ""
echo "=== Security Group Details ==="
aws ec2 describe-security-groups --group-names crypto-bot-sg --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,Port:FromPort,ToPort:ToPort,Source:IpRanges[*].CidrIp}'

echo ""
echo "=== Testing SSH Connection ==="
ssh -i /Users/screener-m3/.ssh/crypto-bot-key.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@13.239.14.166 'echo "SSH Connection successful"'

echo ""
echo "=== Testing Network Connectivity ==="
ping -c 3 13.239.14.166

echo ""
echo "=== Testing Ports ==="
nc -zv 13.239.14.166 22 2>&1
nc -zv 13.239.14.166 8080 2>&1
nc -zv 13.239.14.166 8001 2>&1