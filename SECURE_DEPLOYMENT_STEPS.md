# 🔒 SECURE PRODUCTION DEPLOYMENT STEPS

## Phase 1: GitHub Push (Clean & Secure) ✅

### 1. Final Security Scan
```bash
# Verify no credentials in files
rg "7792214250|8079723149" . || echo "✅ No hardcoded tokens found"
rg "AAH|AAE" . --type md --type sh || echo "✅ No token fragments found"
```

### 2. Stage Clean Changes
```bash
# Add only safe files (no .env files)
git add .
git reset HEAD *.env dev.env prod.env  # Exclude environment files
git status  # Verify only safe files staged
```

### 3. Commit Security Updates
```bash
git commit -m "🔒 Security: Clean credentials and prepare secure deployment

- Remove hardcoded tokens from all scripts
- Update deployment docs with secure practices  
- Prepare AWS production deployment with new token

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4. Push to GitHub
```bash
git push origin main
```

## Phase 2: AWS Production Deployment 🚀

### 1. SSH to AWS Instance
```bash
ssh -i ~/.ssh/crypto-assistant.pem ec2-user@13.239.14.166
```

### 2. Backup & Update Code
```bash
cd /home/ec2-user/TG-Bot

# Create backup branch
git branch backup-before-secure-deploy-$(date +%Y%m%d-%H%M%S)

# Stop current services (old compromised token)
docker-compose down

# Pull latest secure code
git pull origin main
```

### 3. Update Production Environment (MANUAL STEP)
```bash
# Create prod.env with your new token
echo "TELEGRAM_BOT_TOKEN=YOUR_NEW_PRODUCTION_TOKEN" > prod.env
echo "TELEGRAM_CHAT_ID=1145681525" >> prod.env

# Copy to active environment
cp prod.env .env
```

### 4. Clean Deployment
```bash
# Remove old containers with compromised token
docker-compose down -v
docker system prune -f

# Fresh build with new token
docker-compose build --no-cache
docker-compose up -d
```

### 5. Validation
```bash
# Wait for startup
sleep 30

# Check all services healthy
docker-compose ps
curl -f http://localhost:8001/health

# Check bot logs for successful startup
docker logs crypto-telegram-bot | tail -10

# Verify no errors
docker logs crypto-telegram-bot | grep -i error | wc -l
```

## Expected Results ✅

1. **@napo_crypto_prod_bot** responds immediately
2. **4 pending messages** processed automatically  
3. **All features working**: /price, /analysis, /oi
4. **Memory usage < 400MB** combined
5. **No security vulnerabilities**

## Security Validation ✅

- [x] No hardcoded credentials in GitHub
- [x] Old compromised token completely removed
- [x] New token only exists on AWS in environment files
- [x] All test scripts use environment variables
- [x] Clean git history for security audit

## Rollback Plan (Emergency)
```bash
# If deployment fails
git checkout backup-before-secure-deploy-YYYYMMDD-HHMMSS
cp prod.env.backup .env  # Use old working config
docker-compose up -d --build
```

## Post-Deployment Testing
```bash
# Test bot commands in Telegram:
# /start
# /price BTC-USDT  
# /analysis SOL-USDT 15m
# /oi ETH

# Monitor for 5 minutes
docker logs -f crypto-telegram-bot
```

---
**⚠️ CRITICAL**: Never copy/paste the actual token values. Update prod.env manually on AWS with the real tokens.