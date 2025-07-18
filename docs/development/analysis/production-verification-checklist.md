# 🔍 Production Verification Checklist for 100% Deployment Safety

**Created**: January 17, 2025  
**Purpose**: Gather critical evidence from AWS production before deployment  
**Risk Level**: HIGH - Missing any item could cause production failure  

## 🚨 Critical Information Needed from Production

### 1. Docker Configuration Files
```bash
# SSH to production and run:
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166

# Get docker-compose configuration
cat /home/ec2-user/TG-Bot/docker-compose.yml
# OR if using different file:
ls -la /home/ec2-user/TG-Bot/docker-compose*
cat /home/ec2-user/TG-Bot/docker-compose.production.yml  # if exists

# Get Dockerfile configurations
cat /home/ec2-user/TG-Bot/services/telegram-bot/Dockerfile
cat /home/ec2-user/TG-Bot/services/market-data/Dockerfile
```

### 2. Environment Variables
```bash
# Check production environment variables
docker exec crypto-telegram-bot env | sort
docker exec crypto-market-data env | sort

# Check if .env files exist
ls -la /home/ec2-user/TG-Bot/.env*
cat /home/ec2-user/TG-Bot/.env  # if exists

# Check docker-compose environment
docker-compose config | grep -A10 environment:
```

### 3. Redis Configuration & Usage
```bash
# Check Redis connectivity
docker exec crypto-telegram-bot python -c "import os; print(os.getenv('REDIS_HOST', 'NOT_SET'))"
docker exec crypto-market-data python -c "import os; print(os.getenv('REDIS_HOST', 'NOT_SET'))"

# Check if Redis is actually being used
docker logs crypto-telegram-bot | grep -i redis | tail -20
docker logs crypto-market-data | grep -i redis | tail -20

# Redis data check
docker exec tg-bot-redis-1 redis-cli DBSIZE
docker exec tg-bot-redis-1 redis-cli KEYS "*" | head -10
```

### 4. Port Configuration Mystery
```bash
# Why is bot showing port 5000 but unhealthy?
docker inspect crypto-telegram-bot | grep -A5 "Ports"
docker inspect crypto-telegram-bot | grep -A5 "ExposedPorts"

# Check actual listening ports inside container
docker exec crypto-telegram-bot netstat -tlnp 2>/dev/null || echo "netstat not available"
docker exec crypto-telegram-bot ss -tlnp 2>/dev/null || echo "ss not available"

# Check health check configuration
docker inspect crypto-telegram-bot | grep -A10 "Healthcheck"
```

### 5. Git Repository Verification
```bash
# Check current git status
cd /home/ec2-user/TG-Bot
git remote -v
git branch -a
git log --oneline -5
git status
git diff  # Any uncommitted changes?

# Check if it's the same repository
git config --get remote.origin.url
```

### 6. Dependencies Comparison
```bash
# Get production requirements
cat /home/ec2-user/TG-Bot/services/telegram-bot/requirements.txt > /tmp/prod_bot_requirements.txt
cat /home/ec2-user/TG-Bot/services/market-data/requirements.txt > /tmp/prod_market_requirements.txt

# Check installed packages
docker exec crypto-telegram-bot pip freeze > /tmp/prod_bot_installed.txt
docker exec crypto-market-data pip freeze > /tmp/prod_market_installed.txt
```

### 7. Service Communication
```bash
# How does bot find market-data service?
docker exec crypto-telegram-bot python -c "import os; print(os.getenv('MARKET_DATA_URL', 'NOT_SET'))"

# Network configuration
docker network ls
docker network inspect tg-bot_default  # or whatever network name

# Test internal communication
docker exec crypto-telegram-bot curl -f http://crypto-market-data:8001/health || echo "Failed"
docker exec crypto-telegram-bot curl -f http://localhost:8001/health || echo "Failed"
```

### 8. Actual Running Code
```bash
# What's the actual main.py in production?
docker exec crypto-telegram-bot head -50 /app/main.py
docker exec crypto-telegram-bot grep -n "run_polling\|Flask\|webhook" /app/main.py

# Check for any modifications
docker exec crypto-telegram-bot ls -la /app/
```

### 9. Container Health Investigation
```bash
# Why is telegram-bot unhealthy?
docker logs crypto-telegram-bot --tail 100 | grep -i "error\|exception\|failed"

# Check recent restart history
docker ps -a | grep telegram-bot

# Resource usage
docker stats --no-stream
```

### 10. Configuration Files
```bash
# Any custom configuration files?
find /home/ec2-user/TG-Bot -name "*.conf" -o -name "*.ini" -o -name "*.yaml" 2>/dev/null
ls -la /home/ec2-user/TG-Bot/config/  # if exists
```

## 🔐 Security Considerations

### API Keys and Secrets
```bash
# Don't display values, just check they exist
docker exec crypto-telegram-bot python -c "
import os
keys = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'BINANCE_API_KEY', 'BINANCE_API_SECRET']
for key in keys:
    val = os.getenv(key, 'NOT_SET')
    print(f'{key}: {"SET" if val != "NOT_SET" else "NOT_SET"} (length: {len(val) if val != "NOT_SET" else 0})')
"
```

## 📊 Differences to Document

Create a comparison table:

| Component | Production | Local | Risk Level | Action Required |
|-----------|------------|-------|------------|----------------|
| main.py command | python main.py | python main.py | ✅ Safe | None |
| Port exposure | 5000 (why?) | 8080 | ⚠️ Medium | Investigate |
| Health check | Unhealthy | Unknown | 🔴 High | Fix needed |
| Redis usage | Running | Commented out? | ⚠️ Medium | Verify usage |
| Git branch | ? | main | ⚠️ Medium | Verify same |
| Environment vars | ? | ? | 🔴 High | Must match |

## 🎯 100% Certainty Checklist

Before deployment, we MUST confirm:

- [ ] Same git repository and branch
- [ ] Docker-compose files are compatible
- [ ] Environment variables match (especially service URLs)
- [ ] Redis is either used by both or neither
- [ ] Port configurations are understood
- [ ] Health check issues are resolved
- [ ] No uncommitted production changes
- [ ] Dependencies are compatible
- [ ] Service names match for inter-container communication
- [ ] No production-specific configuration files missing

## 🚀 Safe Deployment Process

Only after ALL above checks:

```bash
# 1. Create production backup
docker exec crypto-telegram-bot cp /app/main.py /app/main.py.backup
docker commit crypto-telegram-bot crypto-telegram-bot:backup-$(date +%Y%m%d)
docker commit crypto-market-data crypto-market-data:backup-$(date +%Y%m%d)

# 2. Test new code with production config locally
# Copy production docker-compose.yml locally
# Run with production environment variables
# Verify all services start and are healthy

# 3. Deploy to production
git pull origin main
docker-compose down
docker-compose up -d --build

# 4. Monitor closely
docker logs -f crypto-telegram-bot
# Be ready to rollback if any issues
```

---

**⚠️ DO NOT PROCEED with deployment until ALL items above are verified!**