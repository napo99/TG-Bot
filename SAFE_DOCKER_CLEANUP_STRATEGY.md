# 🛡️ SAFE DOCKER CLEANUP STRATEGY

**CRITICAL WARNING**: Aggressive Docker cleanup will BREAK your current working system!

---

## 🚨 **CURRENT SYSTEM DEPENDENCY ANALYSIS**

### **ACTIVELY USED IMAGES (DO NOT DELETE)**
```
REQUIRED FOR CURRENT WORKING SYSTEM:
├─ crypto-intelligence-v2-crypto-v2-orchestrator  708MB  (crypto-v2-orchestrator)
├─ crypto-intelligence-v2-cascade-detector        711MB  (crypto-v2-cascade)
├─ crypto-intelligence-v2-aggressor-analyzer      707MB  (crypto-v2-aggressor)
├─ crypto-intelligence-v2-enhanced-alerts         707MB  (crypto-v2-alerts)
├─ crypto-intelligence-v2-oi-monitor              711MB  (crypto-v2-oi)
├─ crypto-intelligence-v2-liquidation-collector   707MB  (crypto-v2-liquidations)
├─ crypto-intelligence-v2-volume-analyzer         707MB  (crypto-v2-volume)
├─ crypto-assistant-telegram-bot                  371MB  (crypto-telegram-bot)
├─ crypto-assistant-market-data                   425MB  (crypto-market-data)
├─ redis:alpine                                    99MB   (redis-v2, redis-coordinator)
└─ python:3.11-slim                               ~200MB  (4 containers using it)
───────────────────────────────────────────────────────────────────────
TOTAL REQUIRED: ~6.5GB (11 unique images)
```

### **POTENTIAL GARBAGE (SAFE TO DELETE)**
```
UNUSED/OLD IMAGES:
├─ crypto-v2-scheduler                            1.19GB  ❓ (not in docker ps)
├─ crypto-intelligence-v2-v2-telegram-bot        725MB   ❓ (redundant?)
├─ crypto-intelligence-v2-trade-collector-*      1.4GB   ❓ (not running)
├─ crypto-assistant-monitoring-*                 1.2GB   ❓ (old monitoring system)
└─ Other build artifacts                         ~4GB    ❓ (build cache, layers)
───────────────────────────────────────────────────────────────────────
POTENTIAL GARBAGE: ~8.5GB
```

---

## 🎯 **SAFE OPTIMIZATION APPROACH**

### **OPTION 1: Keep Current System + AWS Optimization (RECOMMENDED)**
```
STRATEGY: Don't touch local dev, optimize for AWS separately
├─ Local Development: Keep everything as-is (15.6GB, works perfectly)
├─ AWS Deployment: Build new optimized containers specifically for AWS
├─ Risk Level: ZERO (no impact on working system)
└─ Timeline: Phase 2.1 focuses only on AWS deployment optimization
```

### **OPTION 2: Selective Cleanup (MODERATE RISK)**
```bash
# Only remove images NOT used by running containers
docker image ls --format "table {{.ID}}\t{{.Repository}}\t{{.Tag}}" | \
grep -E "(crypto-v2-scheduler|trade-collector|monitoring)" | \
awk '{print $1}' | xargs docker rmi

# Expected savings: ~4GB, keeps working system intact
```

### **OPTION 3: Aggressive Cleanup + Rebuild (HIGH RISK)**
```bash
# This WILL break your current system
docker system prune -a -f
# Then rebuild everything from scratch
# Risk: System downtime, potential data loss, rebuild complexity
```

---

## 💡 **RECOMMENDED PHASE 2.1 STRATEGY**

### **AWS-First Optimization (Zero Local Risk)**
```
APPROACH: Build AWS-optimized containers separately
├─ Create new Dockerfiles with Alpine base + multi-stage builds
├─ Build AWS-specific images with consolidated services
├─ Test AWS deployment without affecting local development
├─ Keep local 15.6GB system as fallback and development environment
└─ Only optimize local system AFTER AWS deployment succeeds
```

### **Container Consolidation for AWS Only**
```
AWS DEPLOYMENT ARCHITECTURE:
├─ crypto-aws-unified:        ~400MB (consolidates 10 intelligence services)
├─ crypto-aws-market-data:    ~150MB (optimized market data service)
├─ redis:alpine:              ~99MB  (unchanged)
───────────────────────────────────────────────────────────────
TOTAL AWS FOOTPRINT:          ~650MB (vs current 6.5GB required images)
AWS STORAGE:                  ~800MB (vs current 15.6GB)
```

### **Development Environment Strategy**
```
LOCAL DEV (UNCHANGED):        15.6GB Docker images, 1.4GB memory
AWS PRODUCTION (OPTIMIZED):   800MB total footprint, 500MB memory
BENEFIT:                      Zero risk to working system
```

---

## 🚀 **IMPLEMENTATION PLAN**

### **Phase 2.1 Corrected Approach:**
1. **Preserve Local System**: No Docker cleanup on development machine
2. **AWS-Specific Optimization**: Create new optimized containers for AWS only
3. **Parallel Development**: Local dev continues unaffected
4. **Validated Success**: Only after AWS deployment succeeds, consider local optimization

### **Commands to AVOID (Will Break System):**
```bash
# ❌ DANGEROUS - Will break your current working system
docker system prune -a -f
docker image prune -a -f
docker container prune -f
```

### **Safe Commands (Minimal Cleanup):**
```bash
# ✅ SAFE - Only removes unused build cache
docker builder prune -f

# ✅ SAFE - Only removes stopped containers (if any)
docker container prune -f

# ✅ SAFE - Only removes unused volumes
docker volume prune -f
```

---

## 🎯 **CORRECTED PHASE 2.1 OBJECTIVES**

### **PRIMARY GOAL**: AWS Deployment Optimization
- Create AWS-specific optimized containers (650MB total)
- Preserve local development environment (15.6GB, fully functional)
- Zero risk to current working intelligence system
- Focus on consolidation and multi-stage builds for AWS only

### **SUCCESS METRICS**:
- ✅ AWS deployment under 1GB total footprint
- ✅ Local development system continues working unchanged  
- ✅ All TG commands functional in both environments
- ✅ Zero downtime or data loss during optimization

**CONCLUSION**: Keep your local system exactly as is. Phase 2.1 optimizes for AWS deployment separately, ensuring zero risk to your working intelligence system.