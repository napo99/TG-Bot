# 🎯 TARGETED CLEANUP: Keep V2 Intelligence, Backup AWS-Deployed Images

**Strategy: Keep crypto-intelligence-v2-* for local development, backup crypto-assistant-* since they're in AWS production**

---

## 🔍 **REFINED CLEANUP ANALYSIS**

### **KEEP FOR LOCAL DEVELOPMENT (crypto-intelligence-v2-*)**
```
REQUIRED FOR LOCAL V2 INTELLIGENCE DEVELOPMENT:
├─ crypto-intelligence-v2-crypto-v2-orchestrator    708MB ✅ KEEP
├─ crypto-intelligence-v2-cascade-detector          711MB ✅ KEEP  
├─ crypto-intelligence-v2-oi-monitor                711MB ✅ KEEP
├─ crypto-intelligence-v2-aggressor-analyzer        707MB ✅ KEEP
├─ crypto-intelligence-v2-volume-analyzer           707MB ✅ KEEP
├─ crypto-intelligence-v2-market-delta              707MB ✅ KEEP
├─ crypto-intelligence-v2-enhanced-alerts           707MB ✅ KEEP
├─ crypto-intelligence-v2-liquidation-collector     707MB ✅ KEEP
├─ crypto-intelligence-v2-trade-collector-binance   707MB ✅ KEEP
├─ crypto-intelligence-v2-trade-collector-bybit     707MB ✅ KEEP
├─ crypto-v2-orchestrator                           704MB ✅ KEEP
├─ crypto-intelligence-v2-v2-telegram-bot           725MB ✅ KEEP
├─ crypto-v2-scheduler                              1.19GB ❓ VERIFY IF NEEDED
───────────────────────────────────────────────────────────────────────
TOTAL V2 INTELLIGENCE SYSTEM:                      9.2GB (ESSENTIAL FOR DEV)
```

### **BACKUP & REMOVE (AWS-Deployed crypto-assistant-*)**
```
ALREADY DEPLOYED IN AWS PRODUCTION - SAFE TO BACKUP/REMOVE:
├─ crypto-assistant-telegram-bot                    371MB 💾 BACKUP & REMOVE
├─ crypto-assistant-market-data                     425MB 💾 BACKUP & REMOVE  
├─ crypto-assistant-monitoring-coordinator          288MB 💾 BACKUP & REMOVE
├─ crypto-assistant-oi-detector                     288MB 💾 BACKUP & REMOVE
├─ crypto-assistant-alert-dispatcher                288MB 💾 BACKUP & REMOVE
├─ crypto-assistant-liquidation-monitor             288MB 💾 BACKUP & REMOVE
───────────────────────────────────────────────────────────────────────
TOTAL BACKUP CANDIDATES:                           1.95GB (IMMEDIATE SAVINGS!)
```

---

## 🚀 **IMMEDIATE CLEANUP COMMANDS**

### **Step 1: Stop AWS-Deployed Containers (Running Locally)**
```bash
# Stop local containers that are redundant with AWS production
docker stop crypto-telegram-bot crypto-market-data

# Verify they're stopped
docker ps | grep crypto-assistant
# Should show no results
```

### **Step 2: Backup crypto-assistant Images**
```bash
#!/bin/bash
# Create backup directory with timestamp
BACKUP_DIR=~/docker-backups/$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR

echo "🔄 Backing up crypto-assistant images..."

# Backup all crypto-assistant images
docker save crypto-assistant-telegram-bot:latest | gzip > $BACKUP_DIR/telegram-bot.tar.gz
docker save crypto-assistant-market-data:latest | gzip > $BACKUP_DIR/market-data.tar.gz
docker save crypto-assistant-monitoring-coordinator:latest | gzip > $BACKUP_DIR/monitoring-coordinator.tar.gz
docker save crypto-assistant-oi-detector:latest | gzip > $BACKUP_DIR/oi-detector.tar.gz
docker save crypto-assistant-alert-dispatcher:latest | gzip > $BACKUP_DIR/alert-dispatcher.tar.gz
docker save crypto-assistant-liquidation-monitor:latest | gzip > $BACKUP_DIR/liquidation-monitor.tar.gz

echo "✅ Backup complete in: $BACKUP_DIR"
ls -lh $BACKUP_DIR/
```

### **Step 3: Remove Backed-Up Images**
```bash
#!/bin/bash
echo "🗑️  Removing crypto-assistant images (already backed up)..."

docker rmi crypto-assistant-telegram-bot:latest
docker rmi crypto-assistant-market-data:latest  
docker rmi crypto-assistant-monitoring-coordinator:latest
docker rmi crypto-assistant-oi-detector:latest
docker rmi crypto-assistant-alert-dispatcher:latest
docker rmi crypto-assistant-liquidation-monitor:latest

echo "✅ Cleanup complete!"
docker images | grep crypto-assistant
# Should show no results

echo "📊 Space freed:"
docker system df
```

---

## 📊 **CLEANUP IMPACT ANALYSIS**

### **Before Cleanup:**
```
TOTAL DOCKER IMAGES: 15.6GB
├─ crypto-intelligence-v2-*: 9.2GB (KEEPING)
├─ crypto-assistant-*:       1.95GB (REMOVING)  
├─ Other images:             4.45GB (KEEPING)
└─ Running containers:       15 containers
```

### **After Cleanup:**
```
TOTAL DOCKER IMAGES: 13.65GB (-1.95GB, 12.5% reduction)
├─ crypto-intelligence-v2-*: 9.2GB (ESSENTIAL FOR DEV)
├─ crypto-assistant-*:       0GB (BACKED UP & REMOVED)
├─ Other images:             4.45GB (UNCHANGED)
└─ Running containers:       13 containers (-2)

BACKUP ARCHIVE SIZE: ~1GB compressed (50% compression)
NET STORAGE IMPACT: -950MB (accounting for backups)
```

### **Local Development Impact:**
```
INTELLIGENCE DEVELOPMENT CAPABILITIES:
✅ Full crypto-intelligence-v2 system intact
✅ All monitoring containers working  
✅ Complete development environment preserved
✅ Zero functionality loss for V2 development

AWS PRODUCTION IMPACT:
✅ Zero impact (crypto-assistant services still running in AWS)
✅ Local backups available if needed for debugging
✅ Full restoration capability maintained
```

---

## 🔄 **RESTORATION PROCESS (If Ever Needed)**

```bash
#!/bin/bash
# Restore crypto-assistant images from backup
BACKUP_DIR=~/docker-backups/YYYYMMDD-HHMMSS

echo "🔄 Restoring crypto-assistant images..."
cd $BACKUP_DIR

docker load < telegram-bot.tar.gz
docker load < market-data.tar.gz  
docker load < monitoring-coordinator.tar.gz
docker load < oi-detector.tar.gz
docker load < alert-dispatcher.tar.gz
docker load < liquidation-monitor.tar.gz

echo "✅ Restoration complete!"
docker images | grep crypto-assistant
```

---

## 🎯 **FINAL OPTIMIZATION SUMMARY**

### **Immediate Benefits:**
- **🗑️ 1.95GB freed** from Docker images
- **📦 ~1GB backup archive** (full restoration capability)  
- **🧪 Full V2 intelligence development** environment preserved
- **☁️ Zero AWS production impact**

### **Updated Phase 2.1 Targets:**
```
DOCKER STORAGE:
├─ Before: 15.6GB total images
├─ After cleanup: 13.65GB (-1.95GB)
├─ Still large, but V2 intelligence preserved
└─ Ready for V2 development and testing

MEMORY USAGE (unchanged):
├─ crypto-intelligence-v2 containers: ~1.2GB
├─ Phase 2.1 memory optimization still needed
└─ AWS deployment optimization separate from this cleanup
```

**🎯 READY TO EXECUTE**: This cleanup gives you immediate space savings while preserving everything needed for crypto-intelligence-v2 development and testing.