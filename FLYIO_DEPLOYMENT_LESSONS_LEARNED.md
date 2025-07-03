# 🚁 Fly.io Deployment: Lessons Learned & Best Practices

## 📊 **Performance Results Summary**

### **Before Optimization (Virginia, 2 machines):**
- **Health Check:** 5+ seconds (TIMEOUT)
- **Bot Commands:** Never completed
- **Resource Split:** 2 × 256MB = resources divided
- **Region:** `iad` (Virginia) - suboptimal for Singapore user

### **After Optimization (Hong Kong, 1 machine):**
- **Health Check:** 90ms ⚡ (55x faster!)
- **Bot Commands:** Expected to work normally
- **Resource Concentrated:** 1 × 256MB = full resources to one instance
- **Region:** `hkg` (Hong Kong) - optimal for Singapore user

## 🔧 **Critical Fly.io Commands & Fixes**

### **1. Scaling Commands (Modern Syntax)**

**❌ DEPRECATED (Don't Use):**
```bash
flyctl regions set hkg --app crypto-assistant-prod
```

**✅ CORRECT (Modern Syntax):**
```bash
# Scale to specific region
flyctl scale count 1 --region hkg --app crypto-assistant-prod --yes

# Remove from old region
flyctl scale count 0 --region iad --app crypto-assistant-prod --yes

# Scale machine count
flyctl scale count 1 --app crypto-assistant-prod --yes
```

### **2. Resource Management**

**Memory Scaling:**
```bash
# Upgrade memory (costs money)
flyctl scale memory 512 --app crypto-assistant-prod
flyctl scale memory 1024 --app crypto-assistant-prod
```

**VM Type Scaling:**
```bash
# Upgrade CPU (costs money)
flyctl scale vm shared-cpu-2x --app crypto-assistant-prod
```

### **3. Monitoring & Debugging Commands**

**Status Checking:**
```bash
flyctl status --app crypto-assistant-prod
flyctl machine list --app crypto-assistant-prod
flyctl logs --app crypto-assistant-prod | tail -20
```

**Health Testing:**
```bash
curl -s -w "Time: %{time_total}s\n" "https://crypto-assistant-prod.fly.dev/health"
```

## 🎯 **Key Performance Discoveries**

### **Resource Allocation Truth:**
- **256MB per machine** (NOT divided between machines)
- **But:** Each machine runs ALL services (market-data + telegram-bot)
- **Problem:** Services compete within each 256MB allocation
- **Solution:** 1 machine = concentrated resources = better performance

### **Region Selection Impact:**
- **Virginia (iad) to Singapore:** 1052ms latency
- **Hong Kong (hkg) to Singapore:** ~40ms faster
- **But:** Region change had minimal impact vs resource concentration

### **Telegram Bot Conflicts:**
- **Multiple machines = Multiple bot instances**
- **Same token = Conflicts:** "terminated by other getUpdates request"
- **Solution:** Single machine eliminates conflicts

## 🚨 **Common Pitfalls & Solutions**

### **1. Resource Starvation Symptoms**
**Symptoms:**
- Health checks taking 5+ seconds
- Bot commands timing out
- APIs responding but extremely slowly

**Diagnosis:**
```bash
# Test basic connectivity
curl -s -w "Time: %{time_total}s\n" "https://example.com"

# Test your deployment
curl -s -w "Time: %{time_total}s\n" "https://your-app.fly.dev/health"
```

**Solutions:**
1. Scale to 1 machine (concentrate resources)
2. Upgrade memory (512MB minimum for Python apps)
3. Move to closer region

### **2. Command Syntax Changes**
**Problem:** Fly.io deprecated many commands without clear migration docs

**Old vs New:**
```bash
# OLD (deprecated)
flyctl regions set hkg

# NEW (current)
flyctl scale count 1 --region hkg --yes
```

### **3. Interactive vs Non-Interactive Execution**
**Problem:** Commands fail in scripts/automation

**Solution:** Always use `--yes` flag:
```bash
flyctl scale count 1 --app crypto-assistant-prod --yes
flyctl deploy --app crypto-assistant-prod --yes
```

## 🌍 **Region Selection Guide**

### **For Singapore Users:**
1. **Best:** `hkg` (Hong Kong) - ~40ms faster than Virginia
2. **Alternative:** `sin` (Singapore) - if available and performs well
3. **Fallback:** `nrt` (Tokyo), `syd` (Sydney)

### **Testing Region Performance:**
```python
# Use this script to test from your location
python3 region_speed_test.py
```

### **Region Migration Process:**
```bash
# 1. Add machine in new region
flyctl scale count 1 --region hkg --app your-app --yes

# 2. Remove machine from old region  
flyctl scale count 0 --region iad --app your-app --yes

# 3. Verify
flyctl status --app your-app
```

## 💰 **Free Tier Optimization Strategies**

### **Maximize Free Resources:**
1. **Single Machine:** Concentrate all resources
2. **Optimal Region:** Choose closest to your users
3. **Remove Unused Services:** Minimize resource competition
4. **Efficient Code:** Async operations, memory optimization

### **When to Upgrade:**
- **256MB insufficient:** Upgrade to 512MB ($10/month)
- **High traffic:** Add more machines
- **Global users:** Multi-region deployment

### **Cost Optimization:**
- **Start small:** Optimize before scaling
- **Monitor usage:** Use Fly.io metrics
- **Scale incrementally:** Don't over-provision

## 🧪 **Testing & Validation Process**

### **Performance Testing Script:**
```python
python3 monitoring_setup.py  # Check overall health
python3 network_diagnosis.py  # Diagnose network issues
```

### **Bot Testing Protocol:**
1. **Health Check:** `curl https://your-app.fly.dev/health`
2. **Simple Command:** Send `/price BTC` to bot
3. **Complex Command:** Send `/analysis BTC-USDT 15m` to bot
4. **Load Test:** Multiple concurrent commands

### **Performance Expectations:**
- **Health Check:** < 500ms
- **Simple Bot Command:** 2-5 seconds
- **Complex Analysis:** 5-15 seconds
- **If slower:** Resource upgrade needed

## 🔧 **Troubleshooting Checklist**

### **Bot Not Responding:**
1. Check `flyctl status --app your-app`
2. Check `flyctl logs --app your-app`
3. Test health endpoint
4. Verify bot token in secrets
5. Check for machine conflicts

### **Slow Performance:**
1. Test network latency to region
2. Check memory usage patterns
3. Scale to single machine
4. Consider memory upgrade
5. Optimize code if needed

### **Deployment Failures:**
1. Check `fly.toml` syntax
2. Verify Dockerfile builds locally
3. Check secret configuration
4. Use `--verbose` flags for debugging

## 📈 **Scaling Roadmap**

### **Phase 1: Free Tier Optimization (Current)**
- ✅ Single machine in optimal region
- ✅ Resource concentration
- ✅ Basic monitoring

### **Phase 2: Paid Optimization ($10-20/month)**
- 512MB-1GB RAM
- 2 vCPUs
- Enhanced monitoring

### **Phase 3: Production Scale ($20-50/month)**
- Multi-region deployment
- Load balancing
- Auto-scaling
- Advanced monitoring

## 🎯 **Key Takeaways**

1. **Resource concentration > Resource distribution** for small apps
2. **Region matters less than resource availability**
3. **Fly.io syntax changes frequently** - always check current docs
4. **256MB is too small** for most Python applications in production
5. **Single machine eliminates many conflict issues**
6. **Performance testing is essential** before declaring success

## 🔗 **Useful Resources**

- **Fly.io Scale Docs:** https://fly.io/docs/launch/scale-count/
- **Fly.io Regions:** https://fly.io/docs/reference/regions/
- **Performance Monitoring:** Use built-in Fly.io metrics
- **Community:** Fly.io Discord for real-time help

---

**Last Updated:** 2025-07-03  
**Performance Result:** 90ms health checks after optimization (55x improvement)  
**Status:** Ready for production testing with optimized free tier setup