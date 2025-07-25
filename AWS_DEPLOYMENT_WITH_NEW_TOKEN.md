# AWS Production Deployment - New Token Migration

## Current Situation ✅
- **DEV Bot**: @napo_assistant_bot - Working locally (no conflicts)
- **PROD Bot**: @napo_crypto_prod_bot - New token validated, ready for AWS
- **Issue**: AWS still running old compromised token

## Deployment Plan 🚀

### Phase 1: AWS Preparation
```bash
# SSH to AWS instance
ssh -i ~/.ssh/crypto-assistant.pem ec2-user@13.239.14.166

# Stop current services (running old token)
cd /home/ec2-user/TG-Bot
docker-compose down

# Backup current state
git branch backup-before-new-token-$(date +%Y%m%d-%H%M%S)
```

### Phase 2: Update Production Environment
```bash
# Pull latest code with new token
git pull origin main

# Update production environment file
# MANUAL STEP: Update prod.env with your new bot token
# echo "TELEGRAM_BOT_TOKEN=YOUR_NEW_PROD_TOKEN" > prod.env
# echo "TELEGRAM_CHAT_ID=YOUR_CHAT_ID" >> prod.env

# Copy to active environment
cp prod.env .env
```

### Phase 3: Fresh Deployment
```bash
# Clean rebuild with new token
docker-compose build --no-cache
docker-compose up -d

# Verify services are healthy
sleep 30
docker-compose ps
curl -f http://localhost:8001/health
```

### Phase 4: Validation
```bash
# Check bot startup
docker logs crypto-telegram-bot | tail -20

# Test market data connection
docker exec crypto-telegram-bot curl -s http://crypto-market-data:8001/health

# Verify no errors
docker logs crypto-telegram-bot | grep -i error | wc -l  # Should be 0
```

## Expected Results ✅
- @napo_crypto_prod_bot will start responding immediately
- 4 pending messages will be processed
- Production bot fully operational with new secure token
- DEV bot continues working locally without conflicts

## Security Validation ✅
- [x] Old compromised token will be completely removed from AWS
- [x] New token has been tested and validated  
- [x] No hardcoded credentials in any files
- [x] Environment properly isolated (prod.env → .env on AWS)

## Rollback Plan (if needed)
```bash
# If deployment fails
git checkout backup-before-new-token-YYYYMMDD-HHMMSS
docker-compose up -d --build
```

## Ready for Execution 🎯
All components tested and validated locally. AWS deployment ready to proceed.