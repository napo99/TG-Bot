#!/bin/bash
# TMUX Session Manager for Agent Coordination
# Prevents coordination failures from session loss

SESSION_NAME="crypto-agents"
WORKSPACES=(
    "/Users/screener-m3/projects/crypto-assistant-oi"
    "/Users/screener-m3/projects/crypto-assistant-perf"  
    "/Users/screener-m3/projects/crypto-assistant-symbols"
    "/Users/screener-m3/projects/crypto-assistant-testing"
)
AGENT_NAMES=(
    "Agent 1: Binance+Bybit"
    "Agent 2: OKX+Performance"
    "Agent 3: Gate.io+Bitget"
    "Agent 4: Integration"
)

create_session() {
    echo "🚀 Creating persistent agent session: $SESSION_NAME"
    
    # Create main session
    tmux new-session -d -s $SESSION_NAME -c "${WORKSPACES[0]}"
    
    # Split into 4 panes
    tmux split-window -h -t $SESSION_NAME -c "${WORKSPACES[1]}"
    tmux split-window -v -t $SESSION_NAME:0.0 -c "${WORKSPACES[2]}"  
    tmux split-window -v -t $SESSION_NAME:0.1 -c "${WORKSPACES[3]}"
    
    # Label panes
    for i in {0..3}; do
        tmux select-pane -t $SESSION_NAME:0.$i -T "${AGENT_NAMES[$i]}"
    done
    
    # Show status in each pane
    for i in {0..3}; do
        tmux send-keys -t $SESSION_NAME:0.$i "echo 'Ready for ${AGENT_NAMES[$i]}'" C-m
        tmux send-keys -t $SESSION_NAME:0.$i "pwd" C-m
    done
    
    echo "✅ Session created. Attach with: tmux attach-session -t $SESSION_NAME"
}

check_session() {
    tmux has-session -t $SESSION_NAME 2>/dev/null
}

attach_session() {
    if check_session; then
        echo "📎 Attaching to existing session: $SESSION_NAME"
        tmux attach-session -t $SESSION_NAME
    else
        echo "❌ Session $SESSION_NAME not found. Creating new session..."
        create_session
        tmux attach-session -t $SESSION_NAME
    fi
}

list_sessions() {
    echo "📋 Available tmux sessions:"
    tmux list-sessions 2>/dev/null || echo "No sessions found"
}

check_agent_status() {
    echo "🔍 Checking agent status across workspaces..."
    for i in {0..3}; do
        workspace="${WORKSPACES[$i]}"
        agent="${AGENT_NAMES[$i]}"
        
        if [ -f "$workspace/.agent_status" ]; then
            echo "✅ $agent:"
            cat "$workspace/.agent_status" | sed 's/^/   /'
        else
            echo "❌ $agent: No status file found"
        fi
        echo ""
    done
}

save_session_state() {
    echo "💾 Saving session state..."
    
    # Capture pane contents
    for i in {0..3}; do
        tmux capture-pane -t $SESSION_NAME:0.$i -p > "/tmp/agent_${i}_session.txt"
        echo "Saved Agent $((i+1)) session to /tmp/agent_${i}_session.txt"
    done
    
    # Save agent status
    check_agent_status > "/tmp/agent_status_$(date +%Y%m%d_%H%M%S).txt"
    echo "Saved agent status to /tmp/agent_status_$(date +%Y%m%d_%H%M%S).txt"
}

case "$1" in
    "create")
        create_session
        ;;
    "attach")
        attach_session
        ;;
    "list")
        list_sessions
        ;;
    "status")
        check_agent_status
        ;;
    "save")
        save_session_state
        ;;
    "recover")
        echo "🔄 Attempting session recovery..."
        attach_session
        ;;
    *)
        echo "Usage: $0 {create|attach|list|status|save|recover}"
        echo ""
        echo "Commands:"
        echo "  create  - Create new agent session"
        echo "  attach  - Attach to existing session (or create if missing)"
        echo "  list    - List all tmux sessions"
        echo "  status  - Check agent status files"
        echo "  save    - Save current session state"
        echo "  recover - Attempt to recover lost session"
        ;;
esac