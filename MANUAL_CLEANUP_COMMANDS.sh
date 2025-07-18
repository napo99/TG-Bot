#!/bin/bash

echo "🧹 Manual Cleanup Commands - Execute in Terminal"
echo "================================================"

cd /Users/screener-m3/projects/crypto-assistant

echo "1. Remove webhook test files..."
rm -f run_webhook_tests.py
rm -f webhook_test_results.py
rm -f services/telegram-bot/verify_webhook_conversion.py
rm -f services/telegram-bot/deploy_webhook.sh

echo "2. Remove webhook documentation..."
rm -f WEBHOOK_ARCHITECTURE.md
rm -f services/telegram-bot/WEBHOOK_MIGRATION_GUIDE.md

echo "3. Remove Flask health template..."
rm -f services/telegram-bot/health.py

echo "4. Remove webhook cache files..."
rm -f services/telegram-bot/__pycache__/main_webhook.cpython-312.pyc

echo "5. Remove cleanup scripts..."
rm -f execute_cleanup.sh
rm -f cleanup_webhook_remnants.sh

echo "✅ Cleanup complete!"
echo ""
echo "Next steps:"
echo "docker-compose down"
echo "docker-compose up -d --build"
echo "docker ps  # Should show healthy containers"