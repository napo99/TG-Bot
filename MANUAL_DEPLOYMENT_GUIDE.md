# 🎛️ Manual Deployment Guide - User Controlled AWS Deployment

## 🛡️ **Your Preference Documented**

**Manual-Only CI/CD**: Automation available but requires explicit user trigger for production safety. Never auto-deploys to AWS.

## 🚀 **How to Deploy Enhanced Features to AWS**

### **Step 1: After Local Development & Testing**
```bash
# 1. Ensure your changes are committed
git add .
git commit -m "Your feature description"

# 2. Push to GitHub remote (this is safe - won't auto-deploy)
git push origin enhanced-price-display
```

### **Step 2: When Ready for AWS Deployment**
```bash
# 1. Switch to AWS deployment branch
git checkout aws-deployment

# 2. Merge your enhanced features (safe local operation)
git merge enhanced-price-display --no-ff -m "🚀 Deploy [your-feature] to AWS production"

# 3. Push to GitHub (triggers AWS deployment)
git push origin aws-deployment
```

### **Step 3: AWS Instance Update**
```bash
# SSH to your AWS instance
ssh -i ~/.ssh/your-key.pem ubuntu@13.239.14.166

# Navigate to bot directory and pull latest
cd /path/to/TG-Bot
git pull origin aws-deployment

# Rebuild containers with new features
docker-compose down
docker-compose build  
docker-compose up -d

# Validate deployment
curl http://localhost:8001/health
curl http://localhost:8080/health
```

## 🧪 **Optional: CI/CD Automation (When You Feel Ready)**

### **Manual Trigger Only:**
```bash
# When you want to set up automated staging/testing
./scripts/setup/upgrade-to-level-2.sh --when-ready

# This will give you:
# - Automated staging environment
# - Integration testing pipeline  
# - Rollback automation
# - Deployment tracking
```

### **Current Status:**
```bash
# Check evolution status anytime
./scripts/evolution_detector.py

# Output shows manual-only mode:
# "🛡️ MANUAL_ONLY mode enabled for production safety"
# "Level 2 available but requires explicit user decision"
```

## 📋 **Safe Deployment Checklist**

### **Before AWS Deployment:**
- [ ] ✅ Local testing completed
- [ ] ✅ Docker containers build successfully
- [ ] ✅ Enhanced features tested locally
- [ ] ✅ No breaking changes introduced
- [ ] ✅ Confident in stability

### **During AWS Deployment:**
- [ ] ✅ Merge to aws-deployment branch
- [ ] ✅ Push to GitHub remote
- [ ] ✅ SSH to AWS instance
- [ ] ✅ Pull latest changes
- [ ] ✅ Rebuild containers
- [ ] ✅ Validate health endpoints

### **After AWS Deployment:**
- [ ] ✅ Test enhanced /price command
- [ ] ✅ Verify funding rate precision (+0.0057%)
- [ ] ✅ Check ATR calculations are realistic
- [ ] ✅ Monitor for any errors
- [ ] ✅ Validate service stability

## 🔄 **Current Enhanced Features Ready for Deployment**

### **✅ Production-Ready:**
- **Funding Rate Precision**: `+0.0057%` instead of `+0.00%`
- **ATR Optimization**: 24h ATR(6×4h), 15m ATR(7×15m) 
- **Double Negative Fix**: `$-768.66` instead of `$--768.66`
- **Health Endpoints**: AWS load balancer integration
- **Dependencies**: All critical libraries included (pytz, etc.)

### **📊 Expected Results:**
```
💰 Price: $107,705.03 | -1.21% | $-1.30K | ATR: 718.94
💸 Funding (8h): +0.0057%  ← Fixed precision
```

## 🚨 **Emergency Rollback**

### **If Something Breaks:**
```bash
# Quick rollback to previous working version
git checkout aws-deployment
git reset --hard f9f1882  # Previous stable commit
git push origin aws-deployment --force

# On AWS instance:
git pull origin aws-deployment --force
docker-compose down && docker-compose up -d
```

## 🎯 **Your Workflow Summary**

1. **Develop locally** on `enhanced-price-display` branch
2. **Test thoroughly** with Docker locally  
3. **Push to GitHub** (safe - no auto-deployment)
4. **When ready**: Merge to `aws-deployment` → Push → Deploy
5. **CI/CD automation**: Available when you want it via manual trigger

---

**🛡️ Your production environment stays safe. You control when and what gets deployed to AWS.**