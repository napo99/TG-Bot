#!/bin/bash
# 🔄 EMERGENCY ROLLBACK SCRIPTS

echo "🚨 CRYPTO BOT ROLLBACK SCRIPTS"
echo "==============================="

show_menu() {
    echo ""
    echo "Choose rollback option:"
    echo "1) Quick Fly.io rollback (2 minutes)"
    echo "2) Code rollback to backup files"  
    echo "3) Remove webhook completely"
    echo "4) Check current system status"
    echo "5) Exit"
    echo ""
}

quick_flyio_rollback() {
    echo "🔄 Rolling back Fly.io deployment..."
    
    # Show available releases
    echo "📋 Available releases:"
    flyctl app releases --app crypto-assistant-prod
    
    echo ""
    read -p "Enter release number to rollback to (or press Enter for previous): " release
    
    if [ -z "$release" ]; then
        echo "🔄 Rolling back to previous release..."
        flyctl app rollback --app crypto-assistant-prod
    else
        echo "🔄 Rolling back to release $release..."
        flyctl app rollback $release --app crypto-assistant-prod
    fi
    
    echo "✅ Rollback complete. Checking status..."
    sleep 5
    flyctl status --app crypto-assistant-prod
}

code_rollback() {
    echo "🔄 Rolling back code changes..."
    
    if [ -f "services/telegram-bot/main.py.backup" ]; then
        cp services/telegram-bot/main.py.backup services/telegram-bot/main.py
        echo "✅ Restored main.py from backup"
    else
        echo "❌ No backup file found!"
        return 1
    fi
    
    # Remove Flask from requirements if added
    if grep -q "Flask" services/telegram-bot/requirements.txt; then
        sed -i '' '/Flask/d' services/telegram-bot/requirements.txt
        echo "✅ Removed Flask from requirements.txt"
    fi
    
    echo "✅ Code rollback complete"
    echo "💡 Run 'flyctl deploy --app crypto-assistant-prod' to deploy restored version"
}

remove_webhook() {
    echo "🔄 Removing Telegram webhook..."
    
    # Remove webhook using bot token
    BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
    
    echo "📞 Calling Telegram API to delete webhook..."
    response=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook")
    
    echo "📋 Response: $response"
    
    # Check webhook status
    echo "📋 Checking current webhook info..."
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
    
    echo ""
    echo "✅ Webhook removal complete"
    echo "💡 Bot should automatically return to polling mode"
}

check_status() {
    echo "🔍 Checking current system status..."
    
    echo ""
    echo "📊 Fly.io Status:"
    flyctl status --app crypto-assistant-prod
    
    echo ""
    echo "🌐 API Health Check:"
    curl -s -w "Time: %{time_total}s\n" "https://crypto-assistant-prod.fly.dev/health"
    
    echo ""
    echo "🤖 Webhook Info:"
    BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
    
    echo ""
    echo "🧪 Quick Bot Test:"
    echo "💡 Send '/price BTC-USDT' to @napo_crypto_prod_bot to test"
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice [1-5]: " choice
    
    case $choice in
        1)
            quick_flyio_rollback
            ;;
        2)
            code_rollback
            ;;
        3)
            remove_webhook
            ;;
        4)
            check_status
            ;;
        5)
            echo "👋 Exiting rollback scripts"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please choose 1-5."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done