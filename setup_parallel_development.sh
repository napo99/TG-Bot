#!/bin/bash

echo "🚀 Setting Up Parallel Development Environment"
echo "============================================="

# 1. Create Git Worktrees for Parallel Development
echo "📁 Creating Git Worktrees..."

git worktree add ../crypto-assistant-oi feature/oi-analysis
git worktree add ../crypto-assistant-perf feature/performance-opt
git worktree add ../crypto-assistant-symbols feature/symbol-mapping
git worktree add ../crypto-assistant-testing feature/oi-testing

echo "✅ Worktrees created:"
git worktree list

# 2. Set up validation tools directory
echo "🛠️ Setting up validation framework..."
mkdir -p tools/validation

# 3. Create baseline validation script
cat > tools/validation/baseline_check.py << 'EOF'
#!/usr/bin/env python3
"""Baseline validation - ensure system is healthy before development"""

import asyncio
import requests
import time

async def main():
    print("🔍 Running Baseline Validation...")
    
    # 1. Check market data service
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        assert response.status_code == 200
        print("✅ Market data service: HEALTHY")
    except:
        print("❌ Market data service: DOWN")
        return False
    
    # 2. Check current analysis works
    try:
        response = requests.post(
            'http://localhost:8001/comprehensive_analysis',
            json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        print("✅ Analysis command: WORKING")
    except Exception as e:
        print(f"❌ Analysis command: FAILED - {e}")
        return False
    
    # 3. Check Bybit inverse current status
    try:
        response = requests.post(
            'http://localhost:8001/oi_analysis',
            json={'symbol': 'BTC'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if 'bybit' in str(data).lower():
                print("✅ OI analysis: API responding")
            else:
                print("⚠️  OI analysis: API responding but no Bybit data")
        else:
            print("❌ OI analysis: API not working")
    except:
        print("❌ OI analysis: Service not available")
    
    print("\n🎯 Baseline validation complete!")
    return True

if __name__ == "__main__":
    asyncio.run(main())
EOF

# 4. Create quick test script for agents
cat > tools/validation/quick_test.py << 'EOF'
#!/usr/bin/env python3
"""Quick test for agents to validate their changes"""

import sys
import requests
import json
import time

def test_oi_analysis():
    """Test OI analysis endpoint"""
    try:
        start = time.time()
        response = requests.post(
            'http://localhost:8001/oi_analysis',
            json={'symbol': 'BTC'},
            timeout=15
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OI Analysis: Response in {duration:.1f}s")
            
            # Check for Bybit inverse data
            response_text = json.dumps(data)
            if 'bybit' in response_text.lower() and '"oi_tokens": 0' not in response_text:
                print("✅ Bybit Inverse: Data present")
            else:
                print("❌ Bybit Inverse: Still showing 0 or missing")
            
            return True
        else:
            print(f"❌ OI Analysis: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OI Analysis: {e}")
        return False

def test_analysis_regression():
    """Ensure sophisticated analysis still works"""
    try:
        start = time.time()
        response = requests.post(
            'http://localhost:8001/comprehensive_analysis',
            json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
            timeout=10
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Analysis Regression: Working in {duration:.1f}s")
                return True
        
        print("❌ Analysis Regression: Failed")
        return False
    except Exception as e:
        print(f"❌ Analysis Regression: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Quick Validation Tests...")
    
    oi_ok = test_oi_analysis()
    analysis_ok = test_analysis_regression()
    
    if oi_ok and analysis_ok:
        print("\n🎯 Quick Test: PASSED ✅")
        sys.exit(0)
    else:
        print("\n❌ Quick Test: FAILED")
        sys.exit(1)
EOF

# 5. Make scripts executable
chmod +x tools/validation/*.py

# 6. Create agent assignment file
cat > AGENT_ASSIGNMENTS.md << 'EOF'
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
EOF

echo ""
echo "✅ Parallel Development Environment Ready!"
echo ""
echo "📋 Next Steps:"
echo "1. Each agent goes to their assigned workspace"
echo "2. Run baseline validation: python3 tools/validation/baseline_check.py"
echo "3. Start development with built-in validation"
echo "4. Use quick_test.py after each change"
echo ""
echo "🎯 Target: Working OI analysis with Bybit inverse showing >10K BTC"
echo ""
echo "📁 Workspaces created:"
echo "   Agent 1 (Bybit): ../crypto-assistant-oi/"
echo "   Agent 2 (Perf):  ../crypto-assistant-perf/"
echo "   Agent 3 (Symbols): ../crypto-assistant-symbols/"
echo "   Agent 4 (Testing): ../crypto-assistant-testing/"