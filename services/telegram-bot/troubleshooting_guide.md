# AWS Deployment Troubleshooting Guide

## Current Issue Summary
- **Health checks failing**: http://13.239.14.166:8080/health and http://13.239.14.166:8001/health
- **Instance**: i-0be83d48202d03ef1 (13.239.14.166)
- **Region**: ap-southeast-2
- **Instance Type**: t3.micro

## Network Connectivity Test Results
- **Port 8080**: Connection refused (service not running)
- **Port 8001**: Connection timeout (port blocked or service not running)

## Root Cause Analysis

### Most Likely Causes (in order of probability):

1. **Docker Services Not Started** (90% probability)
   - Services not running after deployment
   - Need to start docker-compose services

2. **Security Group Misconfiguration** (70% probability)
   - Ports 8080 and 8001 not open in security group
   - Need to add ingress rules

3. **Service Binding Issues** (40% probability)
   - Services binding to localhost instead of 0.0.0.0
   - Need to fix Docker configuration

4. **Resource Constraints** (20% probability)
   - t3.micro instance running out of memory
   - Need to check system resources

## Step-by-Step Resolution

### Step 1: Execute Security Group Fix
```bash
# Run on local machine
chmod +x fix_security_groups.sh
./fix_security_groups.sh
```

### Step 2: Connect to Instance and Diagnose
```bash
# Connect via SSH
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166

# Check Docker status
sudo docker ps -a
sudo docker-compose ps

# Check if project exists
ls -la /home/ec2-user/crypto-assistant/
```

### Step 3: Start Services
```bash
# On the EC2 instance
cd /home/ec2-user/crypto-assistant
sudo docker-compose down
sudo docker-compose up -d
sudo docker-compose ps
```

### Step 4: Check Service Health
```bash
# On the EC2 instance
sudo docker-compose logs telegram-bot
sudo docker-compose logs market-data

# Check port bindings
sudo netstat -tlnp | grep -E "(8080|8001)"

# Test local health endpoints
curl http://localhost:8080/health
curl http://localhost:8001/health
```

### Step 5: Fix Common Issues

#### If Docker is not installed:
```bash
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### If project directory is missing:
```bash
# Clone repository
cd /home/ec2-user
git clone https://github.com/your-username/crypto-assistant.git
cd crypto-assistant
```

#### If services fail to start:
```bash
# Check system resources
free -h
df -h

# Check Docker logs
sudo docker logs crypto-market-data
sudo docker logs crypto-telegram-bot

# Restart Docker service
sudo systemctl restart docker
```

## Files Created for Resolution

1. **aws_diagnosis.md** - Complete diagnostic analysis
2. **fix_deployment.sh** - Comprehensive fix script
3. **fix_security_groups.sh** - Security group configuration
4. **docker-compose.production.yml** - Production Docker configuration
5. **start_services.sh** - Service startup script
6. **troubleshooting_guide.md** - This guide

## Expected Resolution Time
- **Simple case** (services not started): 2-5 minutes
- **Security group issues**: 5-10 minutes
- **Complex configuration issues**: 10-30 minutes

## Success Criteria
After fixes are applied, these should work:
- `curl http://13.239.14.166:8080/health` returns HTTP 200
- `curl http://13.239.14.166:8001/health` returns HTTP 200
- Services show as "Up" in `docker-compose ps`

## Prevention Measures

1. **Auto-start services on boot**:
   ```bash
   # Add to crontab
   @reboot cd /home/ec2-user/crypto-assistant && sudo docker-compose up -d
   ```

2. **Health check monitoring**:
   ```bash
   # Create monitoring script
   */5 * * * * curl -f http://localhost:8080/health || sudo docker-compose restart telegram-bot
   ```

3. **Log rotation**:
   ```bash
   # Configure Docker log rotation
   sudo tee /etc/docker/daemon.json <<EOF
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   EOF
   ```

## Emergency Contacts & Resources
- AWS Console: https://console.aws.amazon.com/
- Docker Documentation: https://docs.docker.com/
- Instance Logs: `sudo journalctl -u docker.service`

## Post-Resolution Verification
1. Monitor services for 24 hours
2. Test all API endpoints
3. Check resource utilization
4. Verify auto-restart functionality
5. Document any additional configurations needed