# Service Identification & Troubleshooting Guide

## 🎯 QUICK REFERENCE

### **Service Status Check (30 seconds)**
```bash
# Run this first - identifies all issues
./verify_system.sh

# If that fails, manual check:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -f http://localhost:8001/health  # Market data
curl -f http://localhost:8080/health  # Telegram bot
```

### **Emergency Restart**
```bash
docker-compose down && docker-compose up -d
```

### **Log Analysis**
```bash
docker logs crypto-telegram-bot | grep -i error
docker logs crypto-market-data | grep -i error
```

---

## 🔍 SERVICE IDENTIFICATION

### **Container Names & Roles**
| Container Name | Service | Port | Role |
|----------------|---------|------|------|
| `crypto-telegram-bot` | Telegram Bot | 8080→5000 | User interface, command processing |
| `crypto-market-data` | Market Data | 8001→8001 | Data fetching, analysis, API |

### **Service Dependencies**
```
Telegram Bot ──depends_on──→ Market Data Service
      │                            │
      ▼                            ▼
 Telegram API                Exchange APIs
```

### **Network Configuration**
- **Docker Network**: `crypto-network` (bridge)
- **Service Discovery**: Containers communicate via hostnames
- **External Access**: Only through exposed ports

---

## 🚨 TROUBLESHOOTING SCENARIOS

### **1. "Bot Not Responding" (Most Common)**

**Symptoms:**
- Telegram commands don't respond
- `/start` or `/price` commands timeout

**Diagnosis:**
```bash
# Check container status
docker ps | grep crypto-telegram-bot

# Check logs for errors
docker logs --tail=20 crypto-telegram-bot

# Test webhook endpoint
curl -f http://localhost:8080/health
```

**Common Causes & Fixes:**

**A. Container Down**
```bash
# Fix: Restart services
docker-compose restart telegram-bot
```

**B. Market Data Service Unreachable**
```bash
# Test service communication
docker exec crypto-telegram-bot curl -f http://market-data:8001/health

# Fix: Restart market data first
docker-compose restart market-data
sleep 10
docker-compose restart telegram-bot
```

**C. Environment Variables Missing**
```bash
# Check critical env vars
docker exec crypto-telegram-bot env | grep TELEGRAM_BOT_TOKEN
docker exec crypto-telegram-bot env | grep MARKET_DATA_URL

# Fix: Verify .env file and restart
docker-compose down && docker-compose up -d
```

---

### **2. "API Errors in Bot Responses"**

**Symptoms:**
- Bot responds but shows error messages
- "Error fetching market data" messages

**Diagnosis:**
```bash
# Test market data API directly
curl -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "timeframe": "15m"}'

# Check market data logs
docker logs --tail=50 crypto-market-data | grep -i error
```

**Common Causes & Fixes:**

**A. Exchange API Issues**
```bash
# Check API credentials
docker exec crypto-market-data env | grep -E "(BINANCE|BYBIT)_API_KEY"

# Fix: Verify credentials in .env and restart
docker-compose restart market-data
```

**B. Network/Rate Limiting**
```bash
# Check for rate limit errors
docker logs crypto-market-data | grep -i "rate\|limit\|ban"

# Fix: Wait and restart service
sleep 60
docker-compose restart market-data
```

**C. Symbol Format Issues**
```bash
# Test with known working symbol
curl -X POST http://localhost:8001/price \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'

# Fix: Use correct symbol format (e.g., BTC/USDT not BTC-USDT)
```

---

### **3. "Containers Won't Start"**

**Symptoms:**
- `docker-compose up` fails
- Port binding errors
- Container exits immediately

**Diagnosis:**
```bash
# Check detailed startup logs
docker-compose up

# Check for port conflicts
lsof -i :8001  # Market data port
lsof -i :8080  # Telegram bot port
lsof -i :5000  # Internal bot port

# Check Docker logs
docker logs crypto-telegram-bot
docker logs crypto-market-data
```

**Common Causes & Fixes:**

**A. Port Conflicts**
```bash
# Find conflicting process
lsof -i :8080

# Kill conflicting process
kill -9 <PID>

# Or change port in docker-compose.yml (non-production)
```

**B. Docker Issues**
```bash
# Clean Docker system
docker system prune -f
docker-compose down
docker-compose up -d --build
```

**C. Configuration Errors**
```bash
# Check docker-compose.yml syntax
docker-compose config

# Verify .env file exists and has required variables
cat .env | grep -E "(TELEGRAM_BOT_TOKEN|BINANCE_API_KEY)"
```

---

### **4. "High Memory Usage/Performance Issues"**

**Symptoms:**
- Slow response times
- Container memory warnings
- System becoming unresponsive

**Diagnosis:**
```bash
# Check resource usage
docker stats --no-stream

# Expected: <200MB per container, <15% CPU

# Check response times
time curl -s http://localhost:8001/health

# Expected: <1 second response
```

**Common Causes & Fixes:**

**A. Memory Leaks**
```bash
# Restart services to clear memory
docker-compose restart

# Monitor for continued memory growth
watch docker stats
```

**B. Too Many Concurrent Requests**
```bash
# Check logs for request patterns
docker logs crypto-market-data | grep "POST\|GET" | tail -20

# Fix: Implement rate limiting if needed
```

**C. Large Log Files**
```bash
# Check log sizes
docker logs crypto-telegram-bot | wc -l
docker logs crypto-market-data | wc -l

# Fix: Clear logs
docker-compose down
docker system prune -f
docker-compose up -d
```

---

### **5. "Network Communication Issues"**

**Symptoms:**
- Services can't communicate
- "Connection refused" errors
- Services up but not responding

**Diagnosis:**
```bash
# Check Docker network
docker network ls | grep crypto

# Test container-to-container communication
docker exec crypto-telegram-bot ping crypto-market-data

# Check network configuration
docker network inspect crypto-network
```

**Common Causes & Fixes:**

**A. Network Corruption**
```bash
# Recreate network
docker-compose down
docker network rm crypto-network
docker-compose up -d
```

**B. DNS Resolution Issues**
```bash
# Test service discovery
docker exec crypto-telegram-bot nslookup crypto-market-data

# Fix: Restart Docker daemon if needed
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop on Mac/Windows
```

---

## 📊 MONITORING & HEALTH CHECKS

### **Automated Monitoring**
```bash
# Run every 5 minutes
*/5 * * * * /path/to/crypto-assistant/verify_system.sh > /tmp/crypto_health.log 2>&1

# Alert on failures
if ! ./verify_system.sh; then
    echo "ALERT: Crypto bot system health check failed" | mail -s "System Alert" admin@domain.com
fi
```

### **Key Metrics to Watch**
| Metric | Normal Range | Alert Threshold |
|--------|-------------|----------------|
| Memory Usage | <400MB total | >500MB |
| Response Time | <2 seconds | >5 seconds |
| Error Rate | 0 errors/hour | >5 errors/hour |
| Container Uptime | >24 hours | Restarts |

### **Health Check Endpoints**
```bash
# Market Data Health
curl http://localhost:8001/health
# Response: {"status": "healthy", "timestamp": "..."}

# Telegram Bot Health  
curl http://localhost:8080/health
# Response: {"status": "ok", "service": "telegram-bot"}
```

---

## 🔧 MAINTENANCE PROCEDURES

### **Daily Checks**
```bash
# Quick health verification
./verify_system.sh

# Check for any errors
docker logs --since="24h" crypto-telegram-bot | grep -i error
docker logs --since="24h" crypto-market-data | grep -i error

# Verify resource usage
docker stats --no-stream | grep crypto
```

### **Weekly Maintenance**
```bash
# Clean up Docker system
docker system prune -f

# Restart services for fresh state
docker-compose restart

# Backup working configuration
git add -A && git commit -m "Weekly backup - $(date)"
```

### **Performance Optimization**
```bash
# Clear logs if too large
docker-compose down
docker system prune -f --volumes
docker-compose up -d

# Monitor memory patterns
watch -n 5 "docker stats --no-stream | grep crypto"

# Check for memory leaks
docker exec crypto-market-data ps aux | grep python
```

---

## 🚫 COMMON MISTAKES TO AVOID

### **Configuration Mistakes**
```bash
❌ DON'T: Modify AWS production files (*.aws)
❌ DON'T: Change port mappings in production
❌ DON'T: Commit API keys to git
❌ DON'T: Run services outside Docker

✅ DO: Use environment variables
✅ DO: Test changes locally first
✅ DO: Follow DEVELOPMENT_WORKFLOW.md
✅ DO: Use verification scripts
```

### **Troubleshooting Mistakes**
```bash
❌ DON'T: Kill Docker daemon while containers running
❌ DON'T: Delete containers without backing up logs
❌ DON'T: Modify files inside running containers
❌ DON'T: Ignore memory/resource warnings

✅ DO: Use docker-compose commands
✅ DO: Save logs before restarting
✅ DO: Make changes in source code
✅ DO: Monitor resource usage
```

---

## 📋 TROUBLESHOOTING CHECKLIST

### **When Things Go Wrong:**

**Step 1: Quick Assessment (2 minutes)**
- [ ] Run `./verify_system.sh`
- [ ] Check `docker ps` output
- [ ] Test health endpoints
- [ ] Check recent logs for errors

**Step 2: Identify Service (3 minutes)**
- [ ] Which service is failing? (telegram-bot vs market-data)
- [ ] Is it a communication issue?
- [ ] Are environment variables correct?
- [ ] Is it a resource issue?

**Step 3: Apply Fix (5 minutes)**
- [ ] Try service restart first
- [ ] Check logs for specific errors
- [ ] Apply targeted fix from guide above
- [ ] Verify fix with health check

**Step 4: Validate (2 minutes)**
- [ ] Run `./verify_system.sh` again
- [ ] Test actual bot functionality
- [ ] Monitor for recurring issues
- [ ] Document any new issues found

### **Escalation Criteria**
Contact system administrator if:
- Multiple restart attempts fail
- Memory usage exceeds 600MB
- Error rate >10 errors/hour
- Security-related errors in logs
- Data corruption suspected

---

## 📞 QUICK REFERENCE COMMANDS

```bash
# System Status
./verify_system.sh
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Service Restart
docker-compose restart telegram-bot
docker-compose restart market-data
docker-compose down && docker-compose up -d

# Log Analysis
docker logs --tail=50 crypto-telegram-bot
docker logs --tail=50 crypto-market-data
docker logs --follow crypto-telegram-bot

# Health Tests
curl -f http://localhost:8001/health
curl -f http://localhost:8080/health

# Resource Monitoring
docker stats --no-stream
watch docker stats

# Emergency Reset
docker-compose down
docker system prune -f
docker-compose up -d --build
```

---

**For comprehensive system protection, see `SYSTEM_PROTECTION_GUIDE.md`**