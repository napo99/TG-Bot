# TMUX-Resurrect Agent Coordination Protocol
**The RIGHT way to prevent agent session loss**

## 🎯 **WHY TMUX-RESURRECT IS PERFECT FOR AGENTS**

### **Problem It Solves:**
- ❌ Accidental session closure = Lost agent work
- ❌ No way to recover Claude agent instances  
- ❌ Lost terminal history and state
- ❌ Coordination breakdown

### **Solution:**
- ✅ Complete session restoration
- ✅ Preserves working directories
- ✅ Maintains pane layouts
- ✅ Saves command history
- ✅ Automatic or manual saves

## 🔧 **SETUP FOR AGENT COORDINATION**

### **1. Configure Tmux-Resurrect for Agents**
Add to `~/.tmux.conf`:

```bash
# Enhanced resurrect settings for agent work
set -g @resurrect-save-bash-history 'on'
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-strategy-vim 'session'

# Save every 15 minutes automatically (optional)
set -g @continuum-restore 'on'
set -g @continuum-save-interval '15'

# Restore programs (careful with this)
set -g @resurrect-processes 'ssh psql mysql sqlite3 python3'
```

### **2. Agent Session Template**
```bash
# Create named session for agents
tmux new-session -d -s crypto-agents -c ~/projects/crypto-assistant-oi
tmux rename-window -t crypto-agents:0 'Agents'

# Split into 4 agent panes
tmux split-window -h -t crypto-agents:0 -c ~/projects/crypto-assistant-perf
tmux split-window -v -t crypto-agents:0.0 -c ~/projects/crypto-assistant-symbols  
tmux split-window -v -t crypto-agents:0.1 -c ~/projects/crypto-assistant-testing

# Label each pane clearly
tmux select-pane -t crypto-agents:0.0 -T "Agent 1: Binance+Bybit"
tmux select-pane -t crypto-agents:0.1 -T "Agent 2: OKX+Performance"
tmux select-pane -t crypto-agents:0.2 -T "Agent 3: Gate.io+Bitget"  
tmux select-pane -t crypto-agents:0.3 -T "Agent 4: Integration"

# CRITICAL: Save immediately after setup
tmux send-keys -t crypto-agents:0.0 'echo "Agent 1 ready in $(pwd)"' C-m
# ... setup other panes ...

# Save the session layout
echo "Press Prefix + Ctrl-s to save this agent session layout"
```

## 💾 **SAVE STRATEGY FOR AGENTS**

### **When to Save:**
```bash
# 1. IMMEDIATELY after agent setup
Prefix + Ctrl-s

# 2. After each agent makes progress  
Prefix + Ctrl-s

# 3. Before switching tasks
Prefix + Ctrl-s

# 4. At end of each work session
Prefix + Ctrl-s
```

### **Save Triggers:**
- ✅ Agent reports completing a phase
- ✅ Before taking breaks
- ✅ After significant progress
- ✅ When switching between projects
- ✅ Before system shutdown

## 🔄 **RECOVERY WORKFLOW**

### **If Session Lost:**
```bash
# 1. Start any tmux session
tmux new-session

# 2. Restore saved state
Prefix + Ctrl-r

# 3. Verify restoration
tmux list-sessions
tmux list-windows
tmux list-panes

# 4. Check agent states
# Navigate to each pane and check what was preserved
```

### **What Gets Restored:**
- ✅ **Pane Layout**: All 4 agent panes in correct positions
- ✅ **Working Directories**: Each agent in their workspace  
- ✅ **Command History**: Previous commands available
- ✅ **Pane Contents**: Terminal output preserved
- ❓ **Claude Sessions**: May need manual restart (but context preserved)

## 📊 **ENHANCED AGENT COORDINATION**

### **Combined Approach (Best Practice):**

**1. Tmux-Resurrect** (Technical Recovery)
- Saves session layout and terminal state
- Restores working directories
- Preserves command history

**2. Agent Status Files** (Work Recovery)  
- Documents actual progress made
- Shows completion status
- Provides work continuation points

**3. Git Commits** (Code Recovery)
- Preserves actual implementation work
- Shows file changes made
- Enables work verification

### **Recovery Sequence:**
```bash
# 1. Restore tmux session
Prefix + Ctrl-r

# 2. Check agent status files
for dir in crypto-assistant-*; do
    echo "=== $dir ==="
    cat $dir/.agent_status 2>/dev/null || echo "No status"
done

# 3. Verify git commits
git log --oneline --all -10

# 4. Test what's actually working
curl http://localhost:8001/health

# 5. Resume agents where they left off
```

## 🎯 **IMMEDIATE SETUP**

### **Create Recoverable Agent Session:**
```bash
# 1. Create the session
tmux new-session -d -s crypto-agents-v2

# 2. Set up 4 panes (as shown above)

# 3. IMMEDIATELY save
# In tmux: Prefix + Ctrl-s

# 4. Verify save worked
ls -la ~/.tmux/resurrect/
```

### **Test Recovery:**
```bash
# 1. Kill session
tmux kill-session -t crypto-agents-v2

# 2. Start new session  
tmux new-session

# 3. Restore
# In tmux: Prefix + Ctrl-r

# 4. Verify agents workspace restored
```

---
**TMUX-RESURRECT + AGENT STATUS FILES = BULLETPROOF COORDINATION**