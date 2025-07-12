# System Protection Guide - Preventing Codebase Breakage

## 🎯 PURPOSE
This comprehensive guide establishes bulletproof protocols for maintaining system integrity and preventing accidental breakage of the crypto trading bot system.

## 🏗️ SYSTEM ARCHITECTURE OVERVIEW

### **Service Communication Map**
```
┌─────────────────────┐    HTTP/REST    ┌─────────────────────┐
│   Telegram Bot      │ ──────────────→ │   Market Data       │
│   (Port 8080/5000)  │                 │   (Port 8001)       │
│   main_webhook.py   │                 │   main.py           │
└─────────────────────┘                 └─────────────────────┘
         │                                       │
         ▼                                       ▼
   Telegram API                          Exchange APIs
```

### **Container Dependencies**
- **Telegram Bot**: Depends on Market Data Service
- **Network**: `crypto-network` (Docker bridge)
- **Service Discovery**: `http://market-data:8001`

## 🚨 CRITICAL FILES - NEVER TOUCH

### **AWS Production (ABSOLUTELY FORBIDDEN)**
```bash
❌ docker-compose.aws.yml      # Production configuration
❌ Dockerfile.aws              # AWS Docker image
❌ Any *.aws files             # AWS-specific configs
❌ Production environment vars # AWS-specific settings
```

### **Core System Files (HIGH RISK)**
```bash
⚠️  docker-compose.yml         # Local development config
⚠️  main_webhook.py            # Shared bot logic
⚠️  services/market-data/main.py # Market service core
⚠️  Dockerfile.webhook         # Local bot image
⚠️  .env                       # Environment variables
```

### **Safe to Modify (LOW RISK)**
```bash
✅ formatting_utils.py         # Display formatting
✅ test_*.py                   # Test files
✅ README.md                   # Documentation
✅ DEVELOPMENT_WORKFLOW.md     # Process docs
```

## 🔍 SERVICE IDENTIFICATION & LOGGING

### **Quick Health Check**
```bash
# 1. Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# crypto-telegram-bot   Up 5 minutes   0.0.0.0:8080->5000/tcp
# crypto-market-data    Up 5 minutes   0.0.0.0:8001->8001/tcp

# 2. Verify service endpoints
curl -f http://localhost:8001/health  # Market data health
curl -f http://localhost:8080/health  # Telegram bot health
```

### **Service Log Analysis**
```bash
# Real-time monitoring
docker logs -f crypto-telegram-bot    # Bot activity
docker logs -f crypto-market-data     # Market data activity

# Error detection
docker logs crypto-telegram-bot | grep -i error
docker logs crypto-market-data | grep -i error

# Recent activity (last 20 lines)
docker logs --tail=20 crypto-telegram-bot
docker logs --tail=20 crypto-market-data
```

### **Log Patterns to Recognize**
```bash
✅ HEALTHY STARTUP:
   "Bot application initialized successfully"
   "Market Data Service initialized"
   "Webhook application ready"

❌ COMMON ERRORS:
   "Error fetching..." → API/Network issues
   "Connection refused" → Service dependency failure
   "Port already in use" → Port conflict
   "Environment variable not set" → Configuration issue
```

## 🔧 TROUBLESHOOTING PROCEDURES

### **1. Service Won't Start**
```bash
# Check port conflicts
lsof -i :8001  # Market data port
lsof -i :8080  # Telegram bot port
lsof -i :5000  # Internal bot port

# Clean restart
docker-compose down
docker system prune -f  # Remove unused containers
docker-compose up -d
```

### **2. Bot Not Responding**
```bash
# Check service communication
docker exec crypto-telegram-bot curl -f http://market-data:8001/health

# Restart in dependency order
docker-compose restart market-data
sleep 10
docker-compose restart telegram-bot
```

### **3. API Errors**
```bash
# Verify environment variables
docker exec crypto-market-data env | grep -E "(BINANCE|BYBIT)"
docker exec crypto-telegram-bot env | grep TELEGRAM

# Test market data directly
curl -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "timeframe": "15m"}'
```

### **4. Performance Issues**
```bash
# Check resource usage
docker stats --no-stream

# Expected usage:
# crypto-telegram-bot: <200MB RAM, <10% CPU
# crypto-market-data: <200MB RAM, <15% CPU
```

## ✅ VERIFICATION CHECKLIST

### **Before Making ANY Changes**
- [ ] Document the change in DEVELOPMENT_WORKFLOW.md
- [ ] Identify exactly which files will be modified
- [ ] Confirm not touching AWS production files
- [ ] Have rollback plan ready (git commit hash)
- [ ] Test change locally first

### **After Making Changes**
- [ ] All containers show "healthy" status
- [ ] No error messages in logs
- [ ] Bot responds to `/start` command
- [ ] Price command works: `/price BTC-USDT`
- [ ] Market Intelligence features display correctly
- [ ] L/S ratios showing in expected format
- [ ] Memory usage remains under limits

### **Full System Validation**
```bash
# 1. Container health
docker ps | grep -E "(crypto-telegram-bot|crypto-market-data)"

# 2. Service endpoints
curl -f http://localhost:8001/health
curl -f http://localhost:8080/health

# 3. Bot functionality (test in Telegram)
/start
/price BTC-USDT
/analysis BTC-USDT 15m

# 4. Performance check
docker stats --no-stream | grep crypto
```

## 🤖 AUTOMATED VERIFICATION SYSTEM

### **Pre-Change Validation**
```bash
#!/bin/bash
# save as: verify_system.sh

echo "🔍 System Health Check..."

# Check containers
if ! docker ps | grep -q "crypto-telegram-bot"; then
    echo "❌ Telegram bot not running"
    exit 1
fi

if ! docker ps | grep -q "crypto-market-data"; then
    echo "❌ Market data service not running"
    exit 1
fi

# Check endpoints
if ! curl -sf http://localhost:8001/health > /dev/null; then
    echo "❌ Market data service not responding"
    exit 1
fi

if ! curl -sf http://localhost:8080/health > /dev/null; then
    echo "❌ Telegram bot not responding"
    exit 1
fi

echo "✅ All systems operational"
```

### **Post-Change Validation**
```bash
#!/bin/bash
# save as: validate_changes.sh

echo "🧪 Testing bot functionality..."

# Test market data API
response=$(curl -s -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "timeframe": "15m"}')

if echo "$response" | grep -q "success.*true"; then
    echo "✅ Market data API working"
else
    echo "❌ Market data API failed"
    exit 1
fi

# Check for errors in logs
telegram_errors=$(docker logs --tail=50 crypto-telegram-bot 2>&1 | grep -i error | wc -l)
market_errors=$(docker logs --tail=50 crypto-market-data 2>&1 | grep -i error | wc -l)

if [ "$telegram_errors" -gt 0 ] || [ "$market_errors" -gt 0 ]; then
    echo "❌ Errors detected in logs"
    echo "Telegram errors: $telegram_errors"
    echo "Market data errors: $market_errors"
    exit 1
fi

echo "✅ All validations passed"
```

## 🚫 COMMON FAILURE SCENARIOS & PREVENTION

### **1. Code Pollution**
```bash
❌ CAUSES:
- Creating multiple main files (main.py, main_webhook.py, main_new.py)
- Leaving experimental code in production
- Modifying both local and AWS configs simultaneously

✅ PREVENTION:
- ONE main file only: main_webhook.py
- Delete experimental files immediately
- Never touch AWS configs for local testing
```

### **2. Service Communication Breakdown**
```bash
❌ CAUSES:
- Incorrect MARKET_DATA_URL configuration
- Docker network issues
- Port conflicts

✅ PREVENTION:
- Always use container names: http://market-data:8001
- Use crypto-network for inter-service communication
- Check ports before starting: lsof -i :8001
```

### **3. Environment Configuration Drift**
```bash
❌ CAUSES:
- Missing environment variables
- Incorrect API keys
- Wrong service URLs

✅ PREVENTION:
- Validate .env file before starting
- Use docker exec to verify environment variables
- Test API connectivity separately
```

## 🔄 CHANGE MANAGEMENT PROTOCOL

### **Safe Change Process**
1. **Document**: Update DEVELOPMENT_WORKFLOW.md with planned change
2. **Backup**: `git commit -m "Working state before [change]"`
3. **Isolate**: Only modify local development files
4. **Test**: Run full validation checklist
5. **Verify**: External agent verification
6. **Deploy**: Only after successful local testing

### **Emergency Rollback**
```bash
# Immediate rollback to last working state
git log --oneline -5
git reset --hard <last_working_commit>
docker-compose down
docker-compose up -d --build
```

## 📊 MONITORING & ALERTING

### **Key Metrics to Track**
- **Container Status**: All containers "Up" and "healthy"
- **Response Times**: API calls < 2 seconds
- **Memory Usage**: Combined < 400MB
- **Error Rate**: Zero errors in logs
- **Bot Responsiveness**: Commands respond within 5 seconds

### **Alert Conditions**
```bash
🚨 CRITICAL ALERTS:
- Container down or unhealthy
- API endpoints not responding
- Memory usage > 500MB
- Error rate > 0

⚠️  WARNING ALERTS:
- Response time > 3 seconds
- Memory usage > 300MB
- Unusual log patterns
```

## 📝 CHANGE REQUEST TEMPLATE

```markdown
## Change Request: [Feature Name]

**Purpose**: What the feature should accomplish
**Risk Level**: LOW/MEDIUM/HIGH
**Files to Modify**: 
- [ ] file1.py (reason)
- [ ] file2.py (reason)

**Files NOT to Touch**:
- [ ] All AWS production files
- [ ] Core configuration files (unless necessary)

**Testing Plan**:
1. Local validation steps
2. Specific bot commands to test
3. Performance benchmarks

**Rollback Plan**:
- Git commit hash to revert to
- Specific steps to undo changes

**Success Criteria**:
- [ ] All existing features work
- [ ] New feature functions correctly
- [ ] No performance degradation
- [ ] No errors in logs
```

## 🎯 BEST PRACTICES SUMMARY

### **Development**
- **Start Small**: Make minimal changes first
- **Test Early**: Verify each change before adding more
- **Document Everything**: Update guides with every change
- **External Validation**: Get agent verification for major changes

### **Operations**
- **Monitor Continuously**: Regular health checks
- **Log Everything**: Comprehensive logging strategy
- **Backup Frequently**: Git commits at working states
- **Validate Always**: Use automated verification scripts

### **Emergency Response**
- **Stay Calm**: Follow documented procedures
- **Diagnose First**: Check logs and service status
- **Rollback Fast**: Don't hesitate to revert to working state
- **Document Issues**: Update guides with lessons learned

---

**Remember: The goal is to enhance the system while maintaining 100% uptime and avoiding ANY breakage. When in doubt, choose the safest approach and get external verification.**