# PRE-YOLO EXECUTION CHECKLIST - January 17, 2025

## 🚀 CLAUDE CLI COMMAND & SETUP

### Correct Claude CLI Command
```bash
# Navigate to project directory
cd /Users/screener-m3/projects/crypto-assistant

# Start Claude with skip permissions (if needed)
claude --skip-permissions

# OR standard Claude CLI start
claude
```

### Session Setup Verification
```bash
# 1. Verify you're in the correct directory
pwd
# Should show: /Users/screener-m3/projects/crypto-assistant

# 2. Verify git status
git status
# Should be clean or only show untracked plan files

# 3. Verify Docker containers are running
docker-compose ps
# All should show "Up" status

# 4. Verify system health
curl -f http://localhost:8001/health
curl -f http://localhost:8080/health
```

## 📋 PRE-EXECUTION SYSTEM VERIFICATION

### Critical System Checks
```bash
# 1. Container Health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep crypto

# Expected output:
# crypto-telegram-bot    Up X minutes    
# crypto-market-data     Up X minutes    0.0.0.0:8001->8001/tcp

# 2. API Health
curl -f http://localhost:8001/health
# Expected: {"status": "healthy", "timestamp": "..."}

curl -f http://localhost:8080/health  
# Expected: {"status": "healthy", "timestamp": "..."}

# 3. Memory Baseline
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"
# Expected: crypto-telegram-bot should be under 400MB

# 4. Git State
git log --oneline -3
git branch
# Should be on main branch
```

### Create Backup Point
```bash
# 1. Commit any pending changes
git add .
git commit -m "🛡️ Pre-YOLO backup - $(date +%Y%m%d-%H%M%S)"

# 2. Create tagged backup
git tag backup-before-yolo-$(date +%Y%m%d-%H%M%S)

# 3. Verify backup exists
git tag | grep backup-before-yolo
```

### Initialize Coordination Files
```bash
# Create YOLO coordination directory
mkdir -p /tmp/yolo_20250117/

# Initialize logging files
touch /tmp/yolo_20250117/coordination.json
touch /tmp/yolo_20250117/activity_log.txt
touch /tmp/yolo_20250117/signals.txt

# Set permissions
chmod 666 /tmp/yolo_20250117/*
```

## ✅ VERIFICATION CHECKLIST

Before starting new session, confirm:

- [ ] All Docker containers are running and healthy
- [ ] API endpoints respond correctly (8001 and 8080)
- [ ] Git is on main branch with clean status
- [ ] Backup tag created: backup-before-yolo-YYYYMMDD-HHMMSS
- [ ] Coordination files created in /tmp/yolo_20250117/
- [ ] Current working directory: /Users/screener-m3/projects/crypto-assistant

## 🚨 EMERGENCY PROCEDURES

If anything goes wrong during YOLO mode:

### Immediate Rollback
```bash
# In case of emergency, run this in terminal:
cd /Users/screener-m3/projects/crypto-assistant
git checkout $(git tag | grep backup-before-yolo | tail -1)
docker-compose down && docker-compose up -d
```

### System Recovery
```bash
# If containers won't start:
docker-compose down
docker system prune -f
docker-compose up -d --build
```

---

**STATUS**: ✅ Template for Future YOLO Sessions  
**Usage**: Reference for pre-execution setup  
**Last Validated**: January 17, 2025