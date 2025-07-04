# AWS Deployment Failure Analysis

## Problem Summary
Health checks failing on AWS EC2 instance (13.239.14.166):
- http://13.239.14.166:8080/health - Connection refused
- http://13.239.14.166:8001/health - Connection timeout

## Investigation Results

### 1. Network Connectivity Test
- **Port 8080**: Connection refused (service not running)
- **Port 8001**: Connection timeout (port blocked or service not running)

### 2. Probable Root Causes

#### A. Docker Services Not Running
Most likely cause - the Docker containers are not started after instance reboot or deployment.

#### B. Security Group Configuration Issue
Ports 8080 and 8001 may not be properly configured in the security group.

#### C. Service Binding Issues
Services may be binding to localhost instead of 0.0.0.0.

## Required Diagnostic Commands

### Check EC2 Instance Status
```bash
aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2 --query 'Reservations[0].Instances[0].{State:State.Name,PublicIP:PublicIpAddress,PrivateIP:PrivateIpAddress,InstanceType:InstanceType,SecurityGroups:SecurityGroups[*].GroupName}'
```

### Check Security Group Rules
```bash
aws ec2 describe-security-groups --group-names crypto-bot-sg --region ap-southeast-2 --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Source:IpRanges[*].CidrIp}'
```

### SSH Connection Test
```bash
ssh -i ~/.ssh/crypto-bot-key.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@13.239.14.166 'echo "SSH Connection successful"'
```

### Check Docker Status (via SSH)
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 'sudo docker ps -a'
```

### Check Docker Compose Services
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 'cd /home/ec2-user/crypto-assistant && sudo docker-compose ps'
```

### Check Container Logs
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 'cd /home/ec2-user/crypto-assistant && sudo docker-compose logs telegram-bot'
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 'cd /home/ec2-user/crypto-assistant && sudo docker-compose logs market-data'
```

### Check System Resources
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 'free -h && df -h && top -bn1 | head -20'
```

### Check Port Bindings
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 'sudo netstat -tlnp | grep -E "(8080|8001)"'
```

## Likely Fixes

### 1. Start Docker Services
```bash
# SSH to instance
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166

# Navigate to project directory
cd /home/ec2-user/crypto-assistant

# Start services
sudo docker-compose up -d

# Check status
sudo docker-compose ps
```

### 2. Fix Security Group (if needed)
```bash
# Allow HTTP traffic on custom ports
aws ec2 authorize-security-group-ingress \
  --group-name crypto-bot-sg \
  --protocol tcp \
  --port 8080 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-2

aws ec2 authorize-security-group-ingress \
  --group-name crypto-bot-sg \
  --protocol tcp \
  --port 8001 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-2
```

### 3. Fix Docker Compose Configuration
Ensure services bind to 0.0.0.0 instead of localhost:

```yaml
services:
  telegram-bot:
    ports:
      - "8080:8080"
    environment:
      - HOST=0.0.0.0
      - PORT=8080
      
  market-data:
    ports:
      - "8001:8001"
    environment:
      - HOST=0.0.0.0
      - PORT=8001
```

### 4. Create Startup Script
Create a script that automatically starts services on boot:

```bash
#!/bin/bash
# /home/ec2-user/start_services.sh

cd /home/ec2-user/crypto-assistant
sudo docker-compose down
sudo docker-compose up -d
sudo docker-compose ps
```

## Next Steps

1. **SSH to Instance**: Connect and check Docker status
2. **Start Services**: Run docker-compose up -d
3. **Check Logs**: Identify any startup errors
4. **Verify Security Groups**: Ensure ports are open
5. **Test Health Endpoints**: Confirm services are responding
6. **Setup Auto-start**: Configure services to start on boot

## Expected Resolution
Most likely this is a simple case of Docker services not being started after deployment. Starting the services should resolve the health check failures.