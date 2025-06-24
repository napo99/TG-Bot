# Agent Development Assignments

## 🎯 Agent Workspaces

### Agent 1: Bybit Inverse Specialist
- **Location**: `../crypto-assistant-oi/`
- **Branch**: `feature/oi-analysis`
- **Primary Focus**: Fix Bybit inverse (coin-margined) contracts
- **Success Metric**: Bybit USD shows >10K BTC (not 0)

### Agent 2: Performance Optimizer
- **Location**: `../crypto-assistant-perf/`
- **Branch**: `feature/performance-opt`
- **Primary Focus**: Achieve <3 second response time for OI analysis
- **Success Metric**: `/oi btc` completes in <3 seconds

### Agent 3: Symbol Harmonizer
- **Location**: `../crypto-assistant-symbols/`
- **Branch**: `feature/symbol-mapping`
- **Primary Focus**: Solve symbol format mismatches across exchanges
- **Success Metric**: All 13 markets working with correct symbols

### Agent 4: Integration Validator
- **Location**: `../crypto-assistant-testing/`
- **Branch**: `feature/oi-testing`
- **Primary Focus**: End-to-end testing and validation
- **Success Metric**: 95%+ validation success rate

## 🔧 Daily Agent Workflow

```bash
# Start of day - each agent:
cd [your-workspace]/
git pull origin [your-branch]
python3 tools/validation/baseline_check.py

# After each change:
python3 tools/validation/quick_test.py

# End of day:
git add . && git commit -m "Progress: [describe changes]"
git push origin [your-branch]
```

## 📊 Success Criteria
- ✅ Bybit Inverse: Shows 15,000+ BTC (not 0)
- ✅ Response Time: <3 seconds for OI analysis
- ✅ Exchange Coverage: 5+ exchanges working
- ✅ No Regression: Analysis command still works perfectly
