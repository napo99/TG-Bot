#!/bin/bash

echo "🧹 Executing Local Cleanup - Removing Webhook Remnants"
echo "======================================================="

# Remove webhook test files
echo "Removing webhook test files..."
rm -f run_webhook_tests.py
rm -f webhook_test_results.py
rm -f services/telegram-bot/verify_webhook_conversion.py
rm -f services/telegram-bot/deploy_webhook.sh

# Remove webhook documentation
echo "Removing webhook documentation..."
rm -f WEBHOOK_ARCHITECTURE.md
rm -f services/telegram-bot/WEBHOOK_MIGRATION_GUIDE.md

# Remove Flask health template
echo "Removing Flask health template..."
rm -f services/telegram-bot/health.py

# Remove webhook cache files
echo "Removing webhook cache files..."
rm -f services/telegram-bot/__pycache__/main_webhook.cpython-312.pyc

# Remove this cleanup script
echo "Removing cleanup script..."
rm -f execute_cleanup.sh

echo "✅ Cleanup complete!"
echo "Next steps:"
echo "1. Test: docker-compose down && docker-compose up -d --build"
echo "2. Verify: docker ps (should show healthy containers)"
echo "3. Test bot functionality"