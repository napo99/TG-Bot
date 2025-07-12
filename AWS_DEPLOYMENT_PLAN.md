# AWS Deployment Plan - Enhanced Features

## 🎯 OBJECTIVE
Deploy enhanced Market Intelligence features to AWS production while maintaining stability and constraints.

## 📊 CURRENT AWS STATUS
- ✅ **Infrastructure**: EC2 t3.micro (i-0be83d48202d03ef1) running
- ✅ **Services**: 3 Docker containers operational (telegram-bot, market-data, redis)
- ✅ **Bot Response**: Working but with OLD features (no Market Intelligence)
- ✅ **Performance**: Sub-2 second response times, <400MB memory usage
- ❌ **Features**: Missing enhanced price command with L/S ratios

## 🔍 AWS CONSTRAINTS & REQUIREMENTS

### **Memory Constraints (Critical)**
- **Instance**: t3.micro with 1GB RAM total
- **Current Usage**: ~400MB (safe margin maintained)
- **Enhanced Features Impact**: Additional memory for new calculations
- **Requirement**: Must stay under 800MB total usage

### **Performance Requirements**
- **Response Time**: Must maintain <2 second responses
- **Stability**: 99.9% uptime requirement
- **Error Rate**: <0.1% error rate for price commands

### **Production Safety**
- **Zero Downtime**: Deploy during low-traffic hours
- **Rollback Plan**: Immediate revert capability
- **Health Checks**: Verify bot responds after deployment
- **Monitoring**: Watch memory/CPU during deployment

## 🚀 DEPLOYMENT STRATEGY

### **Phase 1: Pre-Deployment Validation**
1. **Local Testing**: Verify enhanced features work in clean environment
2. **Memory Testing**: Monitor memory usage of enhanced functions
3. **Performance Testing**: Ensure response times remain optimal
4. **Code Review**: Validate all enhanced functions are production-ready

### **Phase 2: Safe Deployment Process**
1. **Backup Current State**: Create deployment snapshot
2. **Deploy During Low Traffic**: Schedule for optimal time
3. **Gradual Rollout**: Deploy to AWS with health monitoring
4. **Real-time Monitoring**: Watch memory, CPU, response times
5. **Feature Validation**: Test enhanced `/price` command functionality

### **Phase 3: Post-Deployment Verification**
1. **Feature Testing**: Verify Market Intelligence displays correctly
2. **Performance Monitoring**: Confirm response times <2 seconds
3. **Memory Monitoring**: Ensure usage stays under 800MB
4. **Error Rate Monitoring**: Verify <0.1% error rate maintained

## 📦 FILES TO DEPLOY

### **Enhanced Core Files**
- ✅ `services/telegram-bot/formatting_utils.py` - New intelligence functions
- ✅ `services/telegram-bot/main_webhook.py` - Enhanced price command
- ⚠️ **AWS Dockerfile**: Already configured for gunicorn (keep as-is)

### **Configuration Files** 
- ✅ `docker-compose.aws.yml` - No changes needed
- ✅ `Dockerfile.aws` - Already optimized for production

## 🧪 TESTING REQUIREMENTS

### **Local Environment Tests**
```bash
# 1. Container Build Test
docker-compose build --no-cache telegram-bot
docker-compose up -d

# 2. Enhanced Features Test  
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "/price BTC-USDT", "chat": {"id": 123}}}'

# 3. Memory Usage Test
docker stats crypto-telegram-bot --no-stream

# 4. Response Time Test
time curl -X POST http://localhost:8001/combined_price \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'
```

### **AWS Environment Tests**
```bash
# 1. Deployment Test
docker-compose -f docker-compose.aws.yml build --no-cache
docker-compose -f docker-compose.aws.yml up -d

# 2. Health Check Test
curl -f http://13.239.14.166:8080/health

# 3. Bot Response Test
# Send /price BTC-USDT via Telegram and verify enhanced format

# 4. Performance Monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## ⚠️ CRITICAL SUCCESS CRITERIA

### **Must Have (Deployment Blockers)**
- [ ] **Memory Usage**: <800MB total across all containers
- [ ] **Response Time**: Price command responds in <2 seconds
- [ ] **Feature Functionality**: Market Intelligence section displays
- [ ] **L/S Ratios**: Show correctly formatted (e.g., "L/S: 1.56x")
- [ ] **No Regressions**: All existing commands still work

### **Nice to Have (Post-Deployment)**
- [ ] **Activity Context**: Volume activity shows (e.g., "HIGH (2.1x)")
- [ ] **Market Summary**: Actionable signals display
- [ ] **Error Handling**: Graceful degradation if API fails

## 🚨 ROLLBACK PLAN

### **If Deployment Fails**
```bash
# 1. Immediate Rollback
git checkout [previous-working-commit]
docker-compose -f docker-compose.aws.yml down
docker-compose -f docker-compose.aws.yml build --no-cache  
docker-compose -f docker-compose.aws.yml up -d

# 2. Verify Rollback
curl -f http://13.239.14.166:8080/health
# Test basic /price command functionality

# 3. Investigate Issue
docker logs crypto-telegram-bot
docker stats --no-stream
```

### **Rollback Triggers**
- Memory usage >900MB sustained for >5 minutes
- Response time >5 seconds for >3 consecutive requests
- Error rate >1% for price commands
- Bot stops responding to any commands

## 📊 MONITORING CHECKLIST

### **During Deployment**
- [ ] Monitor memory usage every 30 seconds
- [ ] Test bot response every 2 minutes
- [ ] Check Docker container health status
- [ ] Verify network connectivity

### **Post-Deployment (First Hour)**
- [ ] Memory usage trending under 800MB
- [ ] Response times consistently <2 seconds
- [ ] Enhanced features displaying correctly
- [ ] No error spikes in logs

### **Long-term Monitoring (24 Hours)**
- [ ] System stability maintained
- [ ] Enhanced features working consistently
- [ ] User feedback positive
- [ ] Performance metrics within targets

## 🎯 DEPLOYMENT TIMELINE

### **Preparation Phase (Before Deployment)**
- **Day -1**: Complete local testing and validation
- **Day 0**: Final code review and AWS scheduling

### **Deployment Phase**
- **T-0**: Begin deployment during low-traffic window
- **T+5min**: Complete container rebuild and startup
- **T+10min**: Verify health checks and basic functionality
- **T+15min**: Test enhanced features thoroughly
- **T+30min**: Complete post-deployment monitoring

### **Validation Phase**
- **T+1hr**: Confirm stability and performance
- **T+24hr**: Long-term stability validation
- **T+1week**: User feedback and optimization

---

**This plan ensures safe deployment of enhanced features while respecting AWS constraints and maintaining production stability.**