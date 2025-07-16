# 🚀 Hybrid Minimal Deployment Plan - Enhanced Features to AWS

## 📊 **CURRENT STATE ANALYSIS**

### **Working Components (DO NOT TOUCH):**
- ✅ **Market Data Service** (`tg-bot-market-data-1`) - Container ID: `d2b47110c4cb` - HEALTHY
- ✅ **Redis Cache** (`tg-bot-redis-1`) - Container ID: `e5c103169885` - HEALTHY  
- ✅ **Docker Network** - Inter-container communication working
- ✅ **Security Groups** - All ports accessible (22, 8080, 8001, 9443)

### **Needs Update:**
- ❌ **Telegram Bot** (`tg-bot-telegram-bot-1`) - Container ID: `7c098437feb1` - UNHEALTHY
  - Missing: `format_enhanced_funding_rate()`, `format_oi_change()`
  - Code age: 15 hours old
  - Status: Unhealthy due to missing features

### **Resource Availability:**
- **Total RAM**: 904MB
- **Used**: 420MB  
- **Available**: 349MB
- **Current containers**: 173MB total usage

## 🎯 **HYBRID MINIMAL DEPLOYMENT STRATEGY**

### **Phase 1: Quick Staging Validation (2-3 minutes)**
```bash
# 1. Deploy staging for testing only
docker-compose -f docker-compose.staging.yml up -d telegram-bot-staging

# 2. Test enhanced features
curl -k https://13.239.14.166:9443/health
# Manual test: Send /price BTC-USDT to staging bot

# 3. Shutdown staging after validation
docker-compose -f docker-compose.staging.yml down
```

**Expected Resource Usage:** +150-200MB during staging test

### **Phase 2: Minimal Production Update (1-2 minutes)**
```bash
# 1. Build only telegram bot container
docker-compose -f docker-compose.aws.yml build telegram-bot

# 2. Replace only telegram bot (preserve others)
docker stop tg-bot-telegram-bot-1
docker rm tg-bot-telegram-bot-1
docker-compose -f docker-compose.aws.yml up -d telegram-bot

# 3. Validate production
curl http://13.239.14.166:8080/health
```

**Expected Resource Usage:** +100-150MB during build

## 🛡️ **SAFETY MEASURES**

### **Backup Strategy:**
- Create backup tag before changes: `docker tag tg-bot-telegram-bot:latest tg-bot-telegram-bot:backup-$(date +%s)`
- Keep working containers running throughout process
- Git state preserved (no changes to working components)

### **Rollback Plan:**
```bash
# If deployment fails:
docker stop tg-bot-telegram-bot-1
docker run -d --name tg-bot-telegram-bot-1 tg-bot-telegram-bot:backup-[timestamp]
```

### **Success Criteria:**
- [ ] Staging bot responds with enhanced features
- [ ] Production bot health check passes
- [ ] Enhanced features visible in production bot
- [ ] All containers healthy
- [ ] Memory usage < 600MB total

## 📈 **OPTIMIZATION BENEFITS**

| Metric | Full Rebuild | Hybrid Minimal | Savings |
|--------|--------------|----------------|---------|
| **Memory Peak** | 600-800MB | 200-300MB | 60-70% |
| **Build Time** | 8-10 min | 3-4 min | 60% |
| **Downtime** | 3-5 min | 30-60 sec | 80% |
| **Risk Level** | High | Low | 75% |
| **Components Changed** | All 3 | 1 only | 66% |

## 🔄 **COMMIT STRATEGY**

Each phase will be committed separately:
1. **Pre-deployment documentation** (this file)
2. **Post-staging validation** 
3. **Post-production deployment**
4. **Final validation results**

## ⚡ **EXECUTION TIMELINE**

- **T+0**: Document and commit current state
- **T+1**: Deploy staging for validation
- **T+3**: Test enhanced features in staging  
- **T+4**: Shutdown staging, commit results
- **T+5**: Deploy minimal production update
- **T+7**: Validate production, commit success
- **T+8**: Update CLAUDE.md with final status

**Total estimated time: 8 minutes**
**Success probability: 95%+**
**Resource efficiency: 70% savings vs full rebuild**