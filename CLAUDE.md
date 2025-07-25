# Crypto Assistant - Enhanced Market Analysis System

## Project Overview
Advanced cryptocurrency market analysis platform with institutional-grade features including volume analysis, cumulative volume delta (CVD), technical indicators, and comprehensive long/short position tracking.

## 🔒 MANDATORY SECURITY PROTOCOLS (NEVER VIOLATE)

### 🛡️ CORE SECURITY PRINCIPLES
**Claude and all external agents MUST enforce these rules at ALL times:**

#### **1. CREDENTIAL SECURITY (ZERO TOLERANCE)**
- **NEVER hardcode credentials** in any file (test, prod, scripts, docs)
- **ALWAYS use environment variables** with placeholder examples
- **ALWAYS verify no tokens/keys before any commit**
- **IMMEDIATELY revoke any exposed credentials**

#### **2. PRODUCTION DEPLOYMENT RULES**
- **NO test files in production** - tests stay in `tests/` directory only
- **NO debugging scripts in production** - keep in `scripts/dev/` only
- **NO hardcoded values in deployment scripts**
- **ALWAYS use parameterized configurations**

#### **3. ENVIRONMENT SEPARATION**
```
REQUIRED STRUCTURE:
├── src/production/          # Production code only
├── tests/                   # Test files (never deployed)
├── scripts/dev/             # Development scripts  
├── scripts/deployment/      # Production scripts (env vars only)
├── .env.example            # Templates with placeholders
├── .env                    # Real values (MUST be gitignored)
└── .gitignore              # Excludes sensitive files
```

#### **4. CODE REVIEW CHECKPOINTS**
Before ANY commit, Claude MUST verify:
- [ ] No hardcoded credentials anywhere
- [ ] No test files mixed with production code
- [ ] All sensitive values use environment variables
- [ ] `.gitignore` properly configured
- [ ] No temporary/debug files included

#### **5. DEPLOYMENT SAFETY**
- **ALWAYS backup before changes**
- **ALWAYS test in isolated environment first**
- **NEVER deploy untested code to production**
- **ALWAYS validate post-deployment**

#### **6. EMERGENCY PROTOCOLS**
If credentials are exposed:
1. **IMMEDIATELY revoke compromised credentials**
2. **Generate new credentials**
3. **Clean all files containing old credentials**
4. **Update production with new credentials**
5. **Document incident and prevention measures**

### ⚠️ VIOLATION CONSEQUENCES
**Any violation of these principles is considered a CRITICAL security incident.**
**Claude must REFUSE to proceed if any security principle is violated.**

### 🎯 SECURITY VALIDATION COMMANDS
```bash
# Pre-commit security check
grep -r "token\|key\|secret" . --exclude-dir=.git --exclude="*.example"
find . -name "test*.py" -not -path "./tests/*"
git status --porcelain | grep -E "\.(env|key|pem)$"
```

## 🎯 MANDATORY DEPLOYMENT WORKFLOW (NEVER VIOLATE)

### **CRITICAL: PROFESSIONAL GIT WORKFLOW**
**Claude MUST enforce these practices and prevent violations:**

#### **MANDATORY 3-STEP DEPLOYMENT PROCESS**
```
FEATURE BRANCH → MERGE TO MAIN → GITHUB MAIN → PRODUCTION DEPLOYMENT
```

#### **BRANCH WORKFLOW ENFORCEMENT**
**Claude MUST enforce:**
1. **NEVER deploy from feature branches** - Always merge to main first
2. **NEVER deploy directly from local** - GitHub main is source of truth  
3. **ALWAYS merge branches to main** before any production deployment
4. **ALWAYS push to GitHub** before AWS deployment
5. **AWS pulls from GitHub main ONLY** - never local, never branches

#### **DEPLOYMENT SEQUENCE (MANDATORY)**
```bash
# Step 1: Merge any feature branch to main locally
git checkout main
git merge feature/branch-name
git push origin main

# Step 2: Verify GitHub has latest
git log origin/main --oneline -3

# Step 3: Deploy from GitHub main to AWS
ssh aws-instance
git checkout main  
git pull origin main  # GitHub main is source of truth
docker-compose up -d --build
```

#### **VIOLATIONS CLAUDE MUST PREVENT**
- ❌ Direct deployment from feature branches to production
- ❌ Deployment from local without GitHub sync
- ❌ Skipping the main branch merge step
- ❌ AWS pulling from non-main branches
- ❌ Any deployment that bypasses GitHub main

#### **ENFORCEMENT RULES**
**Claude MUST:**
1. **REFUSE deployment commands** from non-main branches
2. **REQUIRE GitHub sync** before any AWS deployment
3. **VALIDATE branch status** across all environments
4. **PREVENT shortcuts** that bypass proper workflow
5. **DOCUMENT violations** and guide to correct process

### **BRANCH STATUS VALIDATION**
Before any deployment, Claude MUST verify:
```bash
# Local main is latest
git checkout main && git pull origin main

# GitHub main matches local  
git log origin/main --oneline -1

# AWS will pull from GitHub main
# Never deploy from local branches directly
```

**⚠️ CRITICAL: Any violation of this workflow is a MAJOR process violation and MUST be prevented.**