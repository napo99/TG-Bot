#!/bin/bash

# Deploy Webhook Version of Telegram Bot
# This script deploys the webhook version to the test app

set -e

APP_NAME="crypto-assistant-webhook-test"
WEBHOOK_URL="https://${APP_NAME}.fly.dev/webhook"

echo "🚀 Deploying Webhook Telegram Bot to Fly.io..."
echo "================================="

# Check if we're in the correct directory
if [ ! -f "main_webhook.py" ]; then
    echo "❌ Error: main_webhook.py not found. Please run from telegram-bot directory."
    exit 1
fi

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Error: Fly CLI not installed. Please install it first."
    exit 1
fi

# Check if logged into Fly
if ! fly auth whoami &> /dev/null; then
    echo "❌ Error: Not logged into Fly. Run 'fly auth login' first."
    exit 1
fi

echo "📦 Building and deploying webhook version..."

# Deploy using the webhook configuration
fly deploy --config fly.webhook.toml --dockerfile Dockerfile.webhook

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🔧 Next steps:"
    echo "1. Set your environment variables:"
    echo "   fly secrets set TELEGRAM_BOT_TOKEN=your_token_here --app ${APP_NAME}"
    echo "   fly secrets set TELEGRAM_CHAT_ID=your_chat_id_here --app ${APP_NAME}"
    echo ""
    echo "2. Set the webhook URL:"
    echo "   curl -X POST https://${APP_NAME}.fly.dev/setWebhook \\"
    echo "        -H 'Content-Type: application/json' \\"
    echo "        -d '{\"url\": \"${WEBHOOK_URL}\"}'"
    echo ""
    echo "3. Test the health endpoint:"
    echo "   curl https://${APP_NAME}.fly.dev/health"
    echo ""
    echo "🌐 Webhook URL: ${WEBHOOK_URL}"
    echo "📊 App URL: https://${APP_NAME}.fly.dev"
    echo ""
    echo "🧪 Test with your bot once secrets are set!"
else
    echo "❌ Deployment failed!"
    exit 1
fi