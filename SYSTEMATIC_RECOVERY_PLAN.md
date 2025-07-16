# 🎯 SYSTEMATIC RECOVERY PLAN - EVIDENCE-BASED ANALYSIS

## 📊 CURRENT STATE DOCUMENTATION

### **PROBLEM STATEMENT:**
- **Timeline**: 48 hours wasted on assumptions without proof
- **Issue**: AWS production Telegram bot unresponsive to commands
- **Symptoms**: Health endpoints work ✅, Market data API works ✅, Bot commands fail ❌
- **Root Cause**: Unknown - need evidence-based analysis

### **EVIDENCE REQUIRED:**
1. **Exact working state date/commit with proof**
2. **Complete file audit and dependency mapping**
3. **Code pollution identification (Fly.io vs AWS)**
4. **Memory usage analysis with actual measurements**
5. **Step-by-step validation framework**

---

## 🔍 PHASE 1: EVIDENCE COLLECTION

### **Task 1.1: Git History Analysis**
- [ ] Extract ALL commits from July 1-15, 2025 with exact timestamps
- [ ] Identify last confirmed working deployment
- [ ] Document exact code state at each deployment
- [ ] Proof: Git logs + deployment records + user confirmation

### **Task 1.2: File System Audit**
- [ ] Categorize ALL files in repository by purpose
- [ ] Identify Fly.io pollution files
- [ ] Map AWS-specific files and their dependencies
- [ ] Create DELETE/KEEP/REVIEW lists with justification

### **Task 1.3: Docker Configuration Analysis**
- [ ] Document ALL Docker files and their purposes
- [ ] Identify conflicting configurations
- [ ] Map memory limits and resource constraints
- [ ] Document health check configurations

### **Task 1.4: Code Dependencies Mapping**
- [ ] List ALL Python imports and their purposes
- [ ] Identify missing dependencies in requirements.txt
- [ ] Map local vs production environment differences
- [ ] Document ALL environment variables required

---

## 🧹 PHASE 2: SYSTEMATIC CLEANUP

### **Task 2.1: Fly.io Pollution Removal**
Files to DELETE (with evidence):
- [ ] `fly.Dockerfile` - Fly.io specific
- [ ] `fly.toml` - Fly.io configuration
- [ ] `services/telegram-bot/fly.webhook.toml` - Fly.io webhook config
- [ ] Any other Fly.io related files (to be identified)

### **Task 2.2: AWS Configuration Cleanup**
Files to KEEP and validate:
- [ ] `docker-compose.aws.yml` - AWS deployment
- [ ] `services/telegram-bot/Dockerfile.aws` - AWS container
- [ ] `services/telegram-bot/main_webhook.py` - AWS webhook implementation

### **Task 2.3: Test/Debug File Cleanup**
Files to DELETE (development pollution):
- [ ] All `*test*.py` files not in tests/ directory
- [ ] All `*debug*.py` files
- [ ] All `emergency_*.py` files
- [ ] All temporary analysis files

---

## 🎯 PHASE 3: SYSTEMATIC RECOVERY

### **Task 3.1: Baseline Establishment**
- [ ] Checkout confirmed working commit (with evidence)
- [ ] Document EXACT state of all files
- [ ] Create backup tag before any changes
- [ ] Validate all dependencies are present

### **Task 3.2: Local Testing Protocol**
- [ ] Test on local machine with identical constraints
- [ ] Memory profiling with actual measurements
- [ ] Performance benchmarking
- [ ] End-to-end functionality testing

### **Task 3.3: AWS Deployment Protocol**
- [ ] Pre-deployment validation checklist
- [ ] Incremental deployment with rollback points
- [ ] Real-time monitoring during deployment
- [ ] Post-deployment validation

---

## 🔬 VALIDATION FRAMEWORK

### **Architect Validation Points:**
1. **File Audit Complete** - Architect reviews categorization
2. **Cleanup Plan Approved** - Architect validates removal strategy
3. **Recovery Plan Approved** - Architect validates step-by-step approach
4. **Each Phase Complete** - Architect confirms before proceeding

### **Tester Validation Points:**
1. **Local Testing Complete** - Tester validates all functionality
2. **Performance Acceptable** - Tester confirms memory/speed requirements
3. **Deployment Successful** - Tester validates production functionality
4. **End-to-End Working** - Tester confirms all commands work

### **Evidence Requirements:**
- **Screenshots** of working/failing states
- **Log files** with timestamps and error messages
- **Memory usage graphs** with before/after measurements
- **Performance benchmarks** with actual numbers
- **Git commit hashes** with exact changes documented

---

## 📋 NEXT IMMEDIATE ACTIONS

### **ACTION 1: Complete Evidence Collection** (30 minutes)
```bash
# Git history analysis with proof
git log --since="2025-07-01" --until="2025-07-15" --oneline --all > git_history_evidence.txt
git log --graph --pretty=format:'%h %ad %s' --date=iso > git_timeline_evidence.txt

# File audit with categorization
find . -type f -name "*.py" | sort > all_python_files.txt
find . -type f -name "*fly*" > fly_pollution_files.txt
find . -type f -name "*aws*" > aws_specific_files.txt
find . -type f -name "docker-compose*" > docker_configs.txt
```

### **ACTION 2: Systematic File Categorization** (45 minutes)
Create three lists:
1. **KEEP**: Essential AWS production files
2. **DELETE**: Pollution, test, debug files
3. **REVIEW**: Unclear purpose files

### **ACTION 3: Recovery Strategy Validation** (15 minutes)
- Present findings to architect for approval
- Get tester agreement on validation criteria
- Confirm no-code-until-approved policy

---

## 🚨 CRITICAL SUCCESS CRITERIA

### **BEFORE ANY CODE CHANGES:**
- [ ] 100% file audit complete with evidence
- [ ] Architect approval on cleanup plan
- [ ] Tester approval on validation criteria
- [ ] All assumptions replaced with proof
- [ ] Complete dependency mapping
- [ ] Rollback plan documented and tested

### **DEPLOYMENT SUCCESS METRICS:**
- [ ] Bot responds to `/start` within 5 seconds
- [ ] Bot responds to `/price BTC-USDT` within 10 seconds
- [ ] Memory usage < 256MB (container limit)
- [ ] No errors in logs for 1 hour
- [ ] All enhanced features working as designed

---

## 📝 DOCUMENTATION REQUIREMENTS

All work must be documented with:
1. **Exact timestamps** of all actions
2. **Before/after screenshots** of all changes
3. **Command outputs** with full logs
4. **Error messages** with complete stack traces
5. **Performance measurements** with actual numbers
6. **Validation results** from architect and tester

**NO ASSUMPTIONS. ONLY EVIDENCE. SYSTEMATIC APPROACH ONLY.**