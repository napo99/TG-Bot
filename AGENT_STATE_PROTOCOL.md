# Agent State Persistence Protocol
**Prevents coordination failures from session loss**

## 📋 **MANDATORY AGENT REQUIREMENTS**

### **1. Status File Updates (Every 15 minutes)**
Each agent MUST maintain `.agent_status` in their workspace:

```bash
# Template for .agent_status file:
AGENT_ID=Agent_1_Binance_Bybit
STATUS=IN_PROGRESS|COMPLETE|BLOCKED|ERROR
CURRENT_TASK=Implementing Bybit inverse fix
COMPLETION_PCT=75
LAST_UPDATE=2025-06-25_00:45:00
FILES_MODIFIED=binance_bybit_oi_service.py,validation_test.py
NEXT_TASK=Integration testing
ESTIMATED_COMPLETION=2025-06-25_01:30:00
BLOCKER_DESCRIPTION=None
LAST_SUCCESSFUL_TEST=Bybit inverse showing 14,218 BTC
```

### **2. Work Log Updates (After each major step)**
```bash
# Template for .agent_work_log
echo "$(date): Started Binance FAPI implementation" >> .agent_work_log
echo "$(date): Completed USDT market - tested OK" >> .agent_work_log
echo "$(date): CRITICAL SUCCESS: Bybit inverse fix working" >> .agent_work_log
echo "$(date): AGENT COMPLETE: All 6 markets implemented" >> .agent_work_log
```

### **3. Deliverable Documentation**
```bash
# Template for .agent_deliverables
FILES_CREATED:
- binance_bybit_oi_service.py (30KB) - Main implementation
- tools/validation/quick_test.py - Testing framework
- debug_bybit_inverse.py - Debugging tools

ENDPOINTS_IMPLEMENTED:
- /binance_oi - Binance OI data
- /bybit_oi - Bybit OI data  
- /binance_bybit_combined - Combined 6 markets

TESTS_PASSING:
- Binance USDT: ✅ 52,862 BTC
- Bybit USD: ✅ 14,218 BTC (was 0)
- Performance: ✅ <2 seconds

INTEGRATION_READY: YES
```

## 🔄 **SESSION RECOVERY WORKFLOW**

### **Step 1: Check Session Exists**
```bash
./tmux_session_manager.sh status
```

### **Step 2: Recover Session**
```bash
./tmux_session_manager.sh recover
```

### **Step 3: Assess Agent States**
```bash
# Check what each agent accomplished
for workspace in crypto-assistant-*; do
    echo "=== $workspace ==="
    cat $workspace/.agent_status 2>/dev/null || echo "No status"
    echo ""
done
```

### **Step 4: Resume Work**
- **COMPLETE agents**: Verify and integrate
- **IN_PROGRESS agents**: Resume from last checkpoint  
- **BLOCKED agents**: Resolve blockers
- **ERROR agents**: Debug and restart

## 🛡️ **PREVENTION STRATEGIES**

### **1. Auto-Save Session State**
```bash
# Run this every 10 minutes
./tmux_session_manager.sh save

# Add to crontab for automatic saving
*/10 * * * * /path/to/tmux_session_manager.sh save
```

### **2. Git Auto-Commit**
```bash
# Each agent commits frequently
git add .agent_status .agent_work_log .agent_deliverables
git commit -m "Agent 1 checkpoint: $(cat .agent_status | grep STATUS)"
```

### **3. Recovery Instructions**
```bash
# If session lost, follow this recovery sequence:
1. ./tmux_session_manager.sh list
2. ./tmux_session_manager.sh status  
3. ./tmux_session_manager.sh recover
4. Review .agent_status files
5. Resume work from documented checkpoints
```

## 📊 **COORDINATION DASHBOARD**

### **Status Overview Command**
```bash
./tmux_session_manager.sh status

# Output shows:
# ✅ Agent 1: COMPLETE (6 markets implemented)
# ❓ Agent 2: IN_PROGRESS (OKX 60% complete)  
# ❌ Agent 3: BLOCKED (Gate.io API issues)
# ⏳ Agent 4: WAITING (for Agents 2,3)
```

---
**This protocol ensures NO WORK IS EVER LOST due to session failures.**