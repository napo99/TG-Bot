# Cleanup Checklist - Temporary Files to Remove Before Production

## 🧹 FILES CREATED THIS SESSION (FOR TESTING/VALIDATION ONLY)

### **Documentation Files (Delete)**
- `TRADING_SYSTEM_ARCHITECTURE.md` - Architecture specification (move to docs/)
- `PHASE1_CLEANUP_LOG.md` - Phase 1 cleanup log (delete)
- `ENHANCED_PA_ANALYSIS.md` - PA analysis implementation plan (delete)
- `IMPROVED_PRICE_FORMAT.md` - Price format ideas (delete)
- `BEFORE_AFTER_COMPARISON.md` - Format comparison (delete)
- `PRICE_COMMAND_MOCKUPS.md` - Visual mockups (delete)
- `ENHANCED_CURRENT_FORMAT.md` - Enhanced format proposal (delete)
- `CLEANUP_CHECKLIST.md` - This file (delete after cleanup)

### **Test Scripts (Delete)**
- `verify_calculations.py` - Delta calculation verification script (delete)

### **Backup Files (Keep for rollback)**
- Git stash: `Pre-Phase1-cleanup-backup-20250710_142036` (keep temporarily)
- Git tag: `pre-refactor-backup-20250710_142036` (keep temporarily)

### **Log Files (Delete)**
- `/tmp/current-logs-20250710_142149.txt` - System logs backup (delete)

## 🚨 CRITICAL: PRODUCTION SAFETY CHECKLIST

### **Before Any Deployment:**
```bash
# 1. Remove all temporary files
rm ENHANCED_PA_ANALYSIS.md
rm IMPROVED_PRICE_FORMAT.md
rm BEFORE_AFTER_COMPARISON.md
rm PRICE_COMMAND_MOCKUPS.md
rm ENHANCED_CURRENT_FORMAT.md
rm PHASE1_CLEANUP_LOG.md
rm verify_calculations.py
rm CLEANUP_CHECKLIST.md
rm /tmp/current-logs-*.txt

# 2. Move architecture docs to proper location
mkdir -p docs/architecture/
mv TRADING_SYSTEM_ARCHITECTURE.md docs/architecture/

# 3. Remove debug logs from production code
# IMPORTANT: Remove these debug lines before deployment:
#   - Line 468: logger.info(f"🔍 DEBUG: Created PerpData...")
#   - Line 1064: logger.info(f"🔍 DEBUG: price_data keys...")
#   - Line 1226: logger.info(f"🔍 DEBUG: Perp data has...")
#   - Line 1230: logger.info(f"🔍 DEBUG: Spot data has...")

# 4. Verify clean git status
git status

# 5. Verify Docker containers work without temp files
docker-compose restart
curl -s http://localhost:8001/health
```

## 📁 WHAT SHOULD REMAIN IN PRODUCTION:

### **Core Code Changes (Keep)**
- `services/market-data/main.py` - Enhanced delta calculation (KEEP)
- `services/telegram-bot/formatting_utils.py` - If enhanced (KEEP)
- `services/telegram-bot/main_webhook.py` - If enhanced (KEEP)

### **Configuration Files (Keep)**
- `docker-compose.yml` - Core compose file (KEEP)
- `docker-compose.aws.yml` - AWS deployment config (KEEP)
- `.github/workflows/deploy-aws.yml` - CI/CD workflow (KEEP)
- `CLAUDE.md` - Project instructions (KEEP)

### **Infrastructure (Keep)**
- All Dockerfile configurations (KEEP)
- All requirements.txt files (KEEP)
- All service directories and core code (KEEP)

## 🔍 DEBUG LOGS TO REMOVE FROM PRODUCTION CODE:

### **In `services/market-data/main.py`:**
```python
# REMOVE THESE LINES BEFORE PRODUCTION:

# Line ~468:
logger.info(f"🔍 DEBUG: Created PerpData with delta_15m={delta_15m}, delta_24h={delta_24h}")

# Line ~1064:
logger.info(f"🔍 DEBUG: price_data keys: {list(price_data.keys())}")

# Line ~1226:
logger.info(f"🔍 DEBUG: Perp data has delta_15m={getattr(price_data, 'delta_15m', 'MISSING')}, delta_24h={getattr(price_data, 'delta_24h', 'MISSING')}")

# Line ~1230:
logger.info(f"🔍 DEBUG: Spot data has delta_15m={getattr(price_data, 'delta_15m', 'MISSING')}, delta_24h={getattr(price_data, 'delta_24h', 'MISSING')}")
```

## 🚀 FINAL PRODUCTION DEPLOYMENT STEPS:

1. **Clean up temporary files**
2. **Remove debug logs**
3. **Test locally without temp files**
4. **Commit only core changes**
5. **Deploy to production**
6. **Verify production works**
7. **Clean up git stashes/tags after successful deployment**

## ⚠️ NEVER COMMIT TO VERSION CONTROL:
- Documentation drafts and mockups
- Test scripts and verification tools
- Debug logs and temporary analysis files
- Backup files and logs
- This cleanup checklist

## ✅ SAFE TO COMMIT:
- Core algorithm improvements (delta calculation)
- Enhanced API responses (if implemented)
- New features (OI 15m, market intelligence)
- Updated data models and classes
- Production configuration files