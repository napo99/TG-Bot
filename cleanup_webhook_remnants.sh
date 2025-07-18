#!/bin/bash

echo "🧹 Cleaning up webhook remnants for production safety..."

# Remove webhook test files
echo "Removing webhook test files..."
rm -f run_webhook_tests.py
rm -f webhook_test_results.py  
rm -f services/telegram-bot/verify_webhook_conversion.py
rm -f services/telegram-bot/deploy_webhook.sh

# Remove misleading documentation
echo "Removing outdated webhook documentation..."
rm -f WEBHOOK_ARCHITECTURE.md
rm -f services/telegram-bot/WEBHOOK_MIGRATION_GUIDE.md

# Remove Flask health template (not used by polling)
echo "Removing unused Flask health template..."
rm -f services/telegram-bot/health.py

# Remove webhook cache files
echo "Removing webhook cache files..."
rm -rf services/telegram-bot/__pycache__/main_webhook.*

# Remove other webhook artifacts
echo "Removing other webhook artifacts..."
rm -f services/telegram-bot/Dockerfile.webhook 2>/dev/null || true

echo "✅ Webhook cleanup complete!"
echo "📋 Files removed:"
echo "  - run_webhook_tests.py"
echo "  - webhook_test_results.py"
echo "  - services/telegram-bot/verify_webhook_conversion.py"
echo "  - services/telegram-bot/deploy_webhook.sh"
echo "  - WEBHOOK_ARCHITECTURE.md"
echo "  - services/telegram-bot/WEBHOOK_MIGRATION_GUIDE.md"
echo "  - services/telegram-bot/health.py"
echo "  - services/telegram-bot/__pycache__/main_webhook.*"
echo ""
echo "🎯 Production-safe polling-only codebase ready!"