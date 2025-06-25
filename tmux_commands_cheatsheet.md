# TMUX Commands Cheatsheet - Essential for Agent Work

## 🔑 **KEY CONCEPTS**
- **Session**: Collection of windows (like a workspace)
- **Window**: Like a tab (can have multiple panes)  
- **Pane**: Split section within a window
- **Prefix**: Default is `Ctrl-b` (your key to access tmux commands)

## 📱 **SESSION MANAGEMENT**

### **Create Sessions**
```bash
# Create new session with name
tmux new-session -s session-name

# Create detached session (runs in background)
tmux new-session -d -s agents

# Create session in specific directory
tmux new-session -s agents -c /path/to/directory
```

### **List Sessions**
```bash
# List all sessions
tmux list-sessions
# or short form:
tmux ls
```

### **Attach to Sessions**
```bash
# Attach to specific session
tmux attach-session -t agents
# or short form:
tmux a -t agents

# Attach to last session
tmux attach
```

### **Switch Between Sessions (Without Detaching)**
```bash
# From within tmux:
Prefix + s                 # Show session list, use arrows to select
Prefix + (                 # Switch to previous session  
Prefix + )                 # Switch to next session

# From command line (while in another session):
tmux switch-client -t agents    # Switch to 'agents' session
```

### **Detach vs Close**
```bash
# DETACH (session keeps running)
Prefix + d                 # Detach current session (GOOD)
Ctrl-d or exit             # Close pane/window (CAREFUL)

# Kill session (DANGEROUS - loses work)
tmux kill-session -t agents
```

## 💾 **SAVE & RESTORE (Your Setup)**

### **Manual Save/Restore**
```bash
# Save current session state
Prefix + Ctrl-s           # Manual save

# Restore last saved state  
Prefix + Ctrl-r           # Manual restore
```

### **Automatic Saves (Your Config)**
- ✅ **Auto-saves every 15 minutes** (tmux-continuum)
- ✅ **Auto-restores on tmux start** (@continuum-restore 'on')
- ✅ **Captures pane contents** (@resurrect-capture-pane-contents 'on')

## 🎯 **PANE NAVIGATION**

### **Move Between Panes**
```bash
Prefix + arrow keys       # Move to pane in direction
Prefix + o               # Move to next pane
Prefix + q               # Show pane numbers, then type number
Prefix + ;               # Move to last active pane
```

### **Pane Layout**
```bash
Prefix + space           # Cycle through layouts
Prefix + !               # Break pane to new window
Prefix + z               # Zoom/unzoom current pane
```

## 🪟 **WINDOW MANAGEMENT**

### **Create/Navigate Windows**
```bash
Prefix + c               # Create new window
Prefix + ,               # Rename current window
Prefix + n               # Next window
Prefix + p               # Previous window  
Prefix + 0-9             # Go to window number
Prefix + w               # List windows
```

## 🆘 **EMERGENCY RECOVERY**

### **If Session Appears Lost**
```bash
# 1. List all sessions
tmux ls

# 2. Try to attach to any session
tmux attach -t session-name

# 3. If sessions exist but seem empty, restore
tmux new-session
# Then inside tmux: Prefix + Ctrl-r

# 4. Check saved sessions
ls -la ~/.local/share/tmux/resurrect/
```

### **Session Recovery Workflow**
```bash
# 1. Check what exists
tmux ls

# 2. Create temporary session if needed
tmux new-session -d -s temp

# 3. Attach and try restore
tmux attach -t temp
# Press: Prefix + Ctrl-r

# 4. If restore works, rename session
Prefix + $                # Rename session
```

## 🔄 **WORKFLOW FOR AGENT WORK**

### **Starting Agent Work**
```bash
# 1. Attach to agents session
tmux attach -t agents

# 2. IMMEDIATELY save after setup
Prefix + Ctrl-s

# 3. Work in panes, save periodically
Prefix + Ctrl-s           # Save after major progress
```

### **Switching Between Projects**
```bash
# From within tmux session:
Prefix + s                # Show all sessions
# Use arrows to select, Enter to switch

# To go back to previous session:
Prefix + (                # Previous session
```

### **Taking Breaks**
```bash
# ALWAYS detach (don't close terminal)
Prefix + d                # Detach session (keeps running)

# When returning:
tmux attach -t agents     # Attach back to session
```

## ⚠️ **CRITICAL DO's and DON'Ts**

### **✅ DO:**
- **Save frequently**: `Prefix + Ctrl-s` after progress
- **Detach properly**: `Prefix + d` when done
- **Use session names**: Easy to find later
- **Check session list**: `tmux ls` to see what's running

### **❌ DON'T:**
- **Close terminal**: Use detach instead
- **Kill sessions unnecessarily**: `tmux kill-session` loses work
- **Forget to save**: Auto-save is every 15min, but manual is better
- **Use exit/Ctrl-d**: Closes panes permanently

## 🎯 **YOUR AGENT SESSION COMMANDS**

### **Connect to Agent Session**
```bash
tmux attach -t agents
```

### **Navigate Agent Panes**
```bash
Prefix + q               # Show pane numbers (0,1,2,3)
# Then press the number for the agent you want:
# 0 = Agent 1 (Binance+Bybit)
# 1 = Agent 2 (OKX+Performance)  
# 2 = Agent 3 (Gate.io+Bitget)
# 3 = Agent 4 (Integration)
```

### **Save Agent Progress**
```bash
Prefix + Ctrl-s          # Save immediately after agent completes work
```

### **Switch to Other Work**
```bash
Prefix + s               # Show all sessions, select different one
Prefix + d               # Detach agents session (keeps running)
```

---
**Remember: Tmux sessions persist until you explicitly kill them or restart your computer. Always detach, never close!**