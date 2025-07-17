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

## 📄 EXACT NEW SESSION PROMPT

Copy this exact prompt into your new Claude session:

```
# YOLO MODE EXECUTION: Strategic Cleanup + Feature Foundation

Execute comprehensive cleanup and optimization of crypto trading bot using YOLO mode (high-speed development with maximum safety).

## PROJECT CONTEXT
- **Current State**: Working crypto trading bot on AWS EC2 (polling mode)
- **Architecture**: Docker containers (telegram-bot, market-data, redis)
- **Memory Usage**: 359MB/904MB (safe headroom)
- **Problem**: Technical debt and experimental webhook files need removal
- **Goal**: Clean codebase and prepare foundation for feature development

## EXECUTION PLAN (PRE-APPROVED)
Executing **Option A: Strategic Cleanup** based on senior architect analysis:
1. Remove webhook experiment files and technical debt
2. Optimize Docker configurations and performance  
3. Prepare foundation for advanced trading features
4. Maintain 100% system functionality throughout

## YOLO MODE SPECIFICATIONS
- **Duration Target**: 2.5 hours with 95% confidence
- **Multi-Agent Coordination**: 4 specialized agents working in parallel
- **Central Logging**: All activities tracked in /tmp/yolo_20250117/
- **Branch Strategy**: Keep main clean, use feature branches
- **Rollback Mechanisms**: Automated rollback on any system failure
- **Safety First**: Docker-only development, continuous validation

## AGENT ASSIGNMENTS
- **Agent 1**: Cleanup Specialist (remove technical debt)
- **Agent 2**: System Validator (continuous monitoring)  
- **Agent 3**: Foundation Optimizer (performance improvements)
- **Agent 4**: Quality Assurance (testing & validation)

## CRITICAL SAFETY PROTOCOLS
- Automated backup: backup-before-yolo-20250117-1445
- Health checks every 30 seconds
- Rollback triggers on container failures
- Continuous API validation
- Memory usage monitoring (<450MB threshold)

## WORKING DIRECTORY
/Users/screener-m3/projects/crypto-assistant

## FILES TO REMOVE (CONFIRMED SAFE)
- services/telegram-bot/main_webhook.py (experimental)
- services/telegram-bot/Dockerfile.webhook (experimental)
- fly.webhook.toml (failed deployment attempt)
- investigations/ directory (old test files)
- archive/investigation_files/ (legacy files)

## REQUEST
Execute YOLO mode implementation with:
1. Multi-agent coordination and central logging
2. Branch-based development with rollback safety
3. Continuous validation and health monitoring
4. Real-time progress reporting
5. Automated rollback on any failures

Start with initialization phase and agent coordination setup. Maintain maximum speed with maximum safety protocols.

Plan reference: YOLO_MODE_IMPLEMENTATION_PLAN_20250117.md

Ready to begin YOLO mode execution?
```

## ✅ VERIFICATION CHECKLIST

Before starting new session, confirm:

- [ ] All Docker containers are running and healthy
- [ ] API endpoints respond correctly (8001 and 8080)
- [ ] Git is on main branch with clean status
- [ ] Backup tag created: backup-before-yolo-YYYYMMDD-HHMMSS
- [ ] Coordination files created in /tmp/yolo_20250117/
- [ ] Plan saved: YOLO_MODE_IMPLEMENTATION_PLAN_20250117.md
- [ ] Current working directory: /Users/screener-m3/projects/crypto-assistant
- [ ] You have the exact prompt ready to copy/paste

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

### Return to This Session
If you need to return to this planning session, the conversation context and all planning work is preserved here.

---

**STATUS**: ✅ Ready for YOLO Mode Launch  
**NEXT STEP**: Start new Claude session and paste the prompt above  
**ESTIMATED COMPLETION**: 2.5 hours from start  

**All systems GO for YOLO mode execution! 🚀**