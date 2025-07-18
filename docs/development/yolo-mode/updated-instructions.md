# 🚀 YOLO MODE UPDATED INSTRUCTIONS - Port Verification Required

## 🎯 **OBJECTIVE:**
Deploy cleaned codebase to AWS production with 100% confidence after port verification.

## 🚨 **CRITICAL PRE-DEPLOYMENT VERIFICATION:**

### **PHASE 0: PORT CONFIGURATION VERIFICATION (MANDATORY)**

**Before any deployment, YOLO agent must verify:**

```bash
# SSH to production
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166

# 1. CRITICAL: Check production Dockerfile
echo "=== PRODUCTION DOCKERFILE ==="
cat /home/ec2-user/TG-Bot/services/telegram-bot/Dockerfile

# 2. CRITICAL: Check if main.py has server/port code
echo "=== MAIN.PY PORT ANALYSIS ==="
grep -n "5000\|port\|bind\|server\|flask\|app.run\|listen" /home/ec2-user/TG-Bot/services/telegram-bot/main.py || echo "No server code found"

# 3. CRITICAL: Check container port configuration
echo "=== CONTAINER PORT INSPECTION ==="
docker inspect crypto-telegram-bot | grep -A10 "ExposedPorts\|Healthcheck"
```

### **VERIFICATION DECISION TREE:**

**If production Dockerfile has:**
- `EXPOSE 5000` → Remove it (polling doesn't need exposed ports)
- `HEALTHCHECK` with port 5000 → Remove it (already done locally)
- No port references → Safe to proceed

**If production main.py has:**
- Flask/server code on port 5000 → STOP - different architecture
- No server code → Safe to proceed (polling only)

## 🎯 **PHASE 1: GITHUB DEPLOYMENT**

**Only after port verification passes:**

```bash
cd /Users/screener-m3/projects/crypto-assistant

# Push to GitHub
git push origin main

# Log the push result
echo "GitHub push completed at $(date)"
```

## 🎯 **PHASE 2: AWS PRODUCTION DEPLOYMENT**

**Execute with monitoring:**

```bash
# SSH to AWS production
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166

# Navigate and pull
cd /home/ec2-user/TG-Bot
echo "=== PULLING LATEST CHANGES ==="
git pull origin main

# Stop containers with logging
echo "=== STOPPING CONTAINERS ==="
docker-compose down

# Clean up unused Redis (optional)
echo "=== CLEANING UP UNUSED REDIS ==="
docker stop tg-bot-redis-1 2>/dev/null || echo "Redis container not running"
docker rm tg-bot-redis-1 2>/dev/null || echo "Redis container not found"

# Rebuild with full logging
echo "=== REBUILDING CONTAINERS ==="
docker-compose up -d --build

# Wait for startup
echo "=== WAITING FOR STARTUP ==="
sleep 15

# Verify deployment
echo "=== DEPLOYMENT VERIFICATION ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## 🎯 **PHASE 3: COMPREHENSIVE VERIFICATION**

**Test all functionality:**

```bash
# 1. Container health verification
echo "=== CONTAINER STATUS ==="
docker ps

# 2. Bot startup verification
echo "=== BOT STARTUP LOGS ==="
docker logs crypto-telegram-bot | tail -20

# 3. Market data service verification
echo "=== MARKET DATA HEALTH ==="
curl -f http://localhost:8001/health || echo "Market data service not responding"

# 4. Error detection
echo "=== ERROR DETECTION ==="
docker logs crypto-telegram-bot | grep -i error | tail -10 || echo "No errors found"

# 5. Memory usage verification
echo "=== RESOURCE USAGE ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## 🎯 **PHASE 4: SUCCESS CRITERIA VERIFICATION**

**Deployment successful if ALL criteria met:**

```bash
# Success criteria checklist
echo "=== SUCCESS CRITERIA VERIFICATION ==="

# 1. No unhealthy containers
UNHEALTHY=$(docker ps --format "{{.Status}}" | grep -c "unhealthy" || echo "0")
echo "Unhealthy containers: $UNHEALTHY (should be 0)"

# 2. Both containers running
RUNNING=$(docker ps --format "{{.Names}}" | grep -c "crypto-" || echo "0")
echo "Running containers: $RUNNING (should be 2)"

# 3. No critical errors
ERRORS=$(docker logs crypto-telegram-bot | grep -c "ERROR\|CRITICAL" || echo "0")
echo "Critical errors: $ERRORS (should be 0)"

# 4. Market data responding
MARKET_DATA=$(curl -s http://localhost:8001/health | grep -c "healthy" || echo "0")
echo "Market data healthy: $MARKET_DATA (should be 1)"

# Final success determination
if [ "$UNHEALTHY" -eq 0 ] && [ "$RUNNING" -eq 2 ] && [ "$ERRORS" -eq 0 ] && [ "$MARKET_DATA" -eq 1 ]; then
    echo "🎉 DEPLOYMENT 100% SUCCESSFUL"
else
    echo "🚨 DEPLOYMENT ISSUES DETECTED"
fi
```

## 🛡️ **ROLLBACK PROCEDURE (IF NEEDED)**

**If any verification fails:**

```bash
echo "=== EXECUTING ROLLBACK ==="
git checkout HEAD~1
docker-compose down
docker-compose up -d --build
echo "Rollback completed"
```

## 📊 **EXPECTED RESULTS:**

### **BEFORE DEPLOYMENT:**
```
crypto-telegram-bot (unhealthy)  ❌
crypto-market-data (healthy)     ✅
tg-bot-redis-1 (unused)         ❌
```

### **AFTER DEPLOYMENT:**
```
crypto-telegram-bot Up X minutes  ✅
crypto-market-data (healthy)      ✅
(no redis container)              ✅
```

## 🎯 **YOLO MODE FINAL INSTRUCTIONS:**

**EXECUTE IN THIS ORDER:**
1. **MANDATORY**: Port verification (Phase 0)
2. **PROCEED ONLY IF**: Port verification passes
3. **MONITOR**: All deployment phases with logging
4. **VERIFY**: All success criteria met
5. **REPORT**: Final status (100% success or issues found)

**CONFIDENCE LEVEL**: 100% after port verification
**RISK LEVEL**: ZERO after verification
**PRODUCTION IMPACT**: POSITIVE (fixes unhealthy status)

---

**YOLO MODE AUTHORIZATION: CONDITIONAL**
**CONDITION**: Port verification must pass first
**THEN**: Execute with full confidence 🎯