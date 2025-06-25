#!/bin/bash
# Create 4-pane agent session for recovery

SESSION_NAME="agents"
CURRENT_DIR=$(pwd)

echo "🚀 Creating recovery session: $SESSION_NAME"
echo "📁 Base directory: $CURRENT_DIR"

# Check if session already exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "⚠️  Session '$SESSION_NAME' already exists"
    read -p "Kill existing session and create new one? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tmux kill-session -t $SESSION_NAME
        echo "🗑️  Killed existing session"
    else
        echo "❌ Cancelled - attaching to existing session instead"
        tmux attach-session -t $SESSION_NAME
        exit 0
    fi
fi

# Create main session
echo "📝 Creating session '$SESSION_NAME'..."
tmux new-session -d -s $SESSION_NAME -c "$CURRENT_DIR"

# Rename the window  
tmux rename-window -t $SESSION_NAME:0 'Agent-Recovery'

# Split into 4 equal panes (2x2 grid)
echo "🔧 Creating 4-pane layout..."

# Split horizontally (creates top and bottom halves)
tmux split-window -h -t $SESSION_NAME:0 -c "$CURRENT_DIR"

# Split top pane vertically  
tmux split-window -v -t $SESSION_NAME:0.0 -c "$CURRENT_DIR"

# Split bottom pane vertically
tmux split-window -v -t $SESSION_NAME:0.1 -c "$CURRENT_DIR"

# Label each pane clearly
echo "🏷️  Labeling panes..."
tmux select-pane -t $SESSION_NAME:0.0 -T "Agent 1: Binance+Bybit"
tmux select-pane -t $SESSION_NAME:0.1 -T "Agent 2: OKX+Performance"  
tmux select-pane -t $SESSION_NAME:0.2 -T "Agent 3: Gate.io+Bitget"
tmux select-pane -t $SESSION_NAME:0.3 -T "Agent 4: Integration"

# Set up each pane with proper working directory and initial message
echo "📁 Setting up workspaces..."

# Pane 0: Agent 1 (Binance + Bybit)
tmux send-keys -t $SESSION_NAME:0.0 "cd /Users/screener-m3/projects/crypto-assistant-oi" C-m
tmux send-keys -t $SESSION_NAME:0.0 "echo '🤖 Agent 1: Binance + Bybit OI Specialist'" C-m
tmux send-keys -t $SESSION_NAME:0.0 "echo 'Workspace: $(pwd)'" C-m
tmux send-keys -t $SESSION_NAME:0.0 "echo 'Status: Ready for Claude agent or manual work'" C-m

# Pane 1: Agent 2 (OKX + Performance)  
tmux send-keys -t $SESSION_NAME:0.1 "cd /Users/screener-m3/projects/crypto-assistant-perf" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '🤖 Agent 2: OKX + Performance Specialist'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo 'Workspace: $(pwd)'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo 'Status: Ready for Claude agent or manual work'" C-m

# Pane 2: Agent 3 (Gate.io + Bitget)
tmux send-keys -t $SESSION_NAME:0.2 "cd /Users/screener-m3/projects/crypto-assistant-symbols" C-m  
tmux send-keys -t $SESSION_NAME:0.2 "echo '🤖 Agent 3: Gate.io + Bitget Specialist'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo 'Workspace: $(pwd)'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo 'Status: Ready for Claude agent or manual work'" C-m

# Pane 3: Agent 4 (Integration)
tmux send-keys -t $SESSION_NAME:0.3 "cd /Users/screener-m3/projects/crypto-assistant-testing" C-m
tmux send-keys -t $SESSION_NAME:0.3 "echo '🤖 Agent 4: Integration + Bot Specialist'" C-m  
tmux send-keys -t $SESSION_NAME:0.3 "echo 'Workspace: $(pwd)'" C-m
tmux send-keys -t $SESSION_NAME:0.3 "echo 'Status: Ready for Claude agent or manual work'" C-m

# Select first pane
tmux select-pane -t $SESSION_NAME:0.0

echo ""
echo "✅ Session '$SESSION_NAME' created successfully!"
echo ""
echo "📋 To connect:"
echo "   tmux attach-session -t $SESSION_NAME"
echo ""
echo "🎯 Layout: 4 equal panes (2x2 grid)"
echo "   ┌─────────┬─────────┐"
echo "   │ Agent 1 │ Agent 3 │"
echo "   │ Bin+Byb │ Gat+Bit │"
echo "   ├─────────┼─────────┤"  
echo "   │ Agent 2 │ Agent 4 │"
echo "   │ OKX+Prf │ Integr  │"
echo "   └─────────┴─────────┘"
echo ""
echo "💾 Don't forget to save: Prefix + Ctrl-s"