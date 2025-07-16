# 🚨 EMERGENCY AWS RECOVERY - Telegram Bot Down

## IMMEDIATE DIAGNOSIS (Run These Now)

### Step 1: Check Instance Status
```bash
# Test basic connectivity
ping -c 3 13.239.14.166

# Check if SSH works
ssh -o ConnectTimeout=10 -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "echo 'SSH OK'"
```

### Step 2: If SSH Works - Check Services
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "
echo '=== DOCKER STATUS ==='
sudo systemctl status docker | head -5

echo '=== CONTAINERS ==='
docker ps -a

echo '=== PROJECT DIRECTORY ==='
cd /home/ec2-user/TG-Bot 2>/dev/null || cd /home/ec2-user/crypto-assistant
pwd && ls -la

echo '=== DOCKER COMPOSE STATUS ==='
docker-compose -f docker-compose.aws.yml ps

echo '=== RECENT ERRORS ==='
docker logs tg-bot-telegram-bot-1 --tail 10 2>/dev/null || echo 'No telegram-bot logs'
docker logs tg-bot-market-data-1 --tail 10 2>/dev/null || echo 'No market-data logs'
"
```

### Step 3: If SSH Fails - Check AWS Console
```bash
# Check instance status (if you have AWS CLI configured)
aws ec2 describe-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2 --query 'Reservations[0].Instances[0].State.Name'

# Start instance if stopped
aws ec2 start-instances --instance-ids i-0be83d48202d03ef1 --region ap-southeast-2
```

## EMERGENCY FIXES

### Fix 1: If Containers Are Down
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "
cd /home/ec2-user/TG-Bot 2>/dev/null || cd /home/ec2-user/crypto-assistant

echo 'Stopping all services...'
docker-compose -f docker-compose.aws.yml down

echo 'Cleaning Docker...'
docker system prune -f

echo 'Starting services...'
docker-compose -f docker-compose.aws.yml up -d

echo 'Waiting 30 seconds...'
sleep 30

echo 'Checking status...'
docker ps
curl -s http://localhost:8080/health || echo 'Bot still down'
curl -s http://localhost:8001/health || echo 'Market data still down'
"
```

### Fix 2: If Memory/Resource Issues
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "
echo '=== SYSTEM RESOURCES ==='
free -h
df -h
uptime

echo 'Restarting with memory cleanup...'
cd /home/ec2-user/TG-Bot 2>/dev/null || cd /home/ec2-user/crypto-assistant
docker-compose -f docker-compose.aws.yml down
docker system prune -af  # Clean everything
sudo systemctl restart docker
docker-compose -f docker-compose.aws.yml up -d
"
```

### Fix 3: If Repository Issues
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "
cd /home/ec2-user

echo 'Checking current repo...'
cd TG-Bot 2>/dev/null || cd crypto-assistant
git remote -v
git branch

echo 'Updating code...'
git stash
git pull origin aws-deployment

echo 'Rebuilding services...'
docker-compose -f docker-compose.aws.yml down
docker-compose -f docker-compose.aws.yml up -d --build
"
```

### Fix 4: Complete Reset (Nuclear Option)
```bash
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166 "
echo 'COMPLETE RESET - Use only if other fixes fail'

cd /home/ec2-user
rm -rf TG-Bot crypto-assistant

echo 'Fresh clone...'
git clone -b aws-deployment https://github.com/napo99/TG-Bot.git
cd TG-Bot

echo 'Complete rebuild...'
docker-compose -f docker-compose.aws.yml down
docker system prune -af
docker-compose -f docker-compose.aws.yml up -d --build

echo 'Waiting 60 seconds for startup...'
sleep 60
docker ps
curl -s http://localhost:8080/health
"
```

## VALIDATION

After running fixes, test:
```bash
# External test
curl -v http://13.239.14.166:8080/health
curl -v http://13.239.14.166:8001/health

# Test Telegram bot response (replace with your bot username)
# Send: /start or /price BTC-USDT
```

## COMMON ISSUES & SOLUTIONS

| Issue | Symptoms | Fix |
|-------|----------|-----|
| Instance Stopped | SSH fails, no ping response | Start instance in AWS Console |
| Containers Crashed | SSH works, docker ps shows exited | Fix 1: Restart containers |
| Out of Memory | High memory usage, containers killed | Fix 2: Memory cleanup |
| Code Outdated | Wrong features, old version | Fix 3: Update repository |
| Complete Failure | Nothing works | Fix 4: Complete reset |

## SECURITY GROUPS (If ports are blocked)
```bash
aws ec2 authorize-security-group-ingress --group-id sg-0d979f270dae48425 --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region ap-southeast-2
aws ec2 authorize-security-group-ingress --group-id sg-0d979f270dae48425 --protocol tcp --port 8001 --cidr 0.0.0.0/0 --region ap-southeast-2
```

**START WITH STEP 1 AND REPORT RESULTS**