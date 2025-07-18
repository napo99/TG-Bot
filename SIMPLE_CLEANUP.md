# Simple Cleanup Plan

## Execute These Commands:

```bash
cd /Users/screener-m3/projects/crypto-assistant

# Remove webhook remnants
rm -f run_webhook_tests.py webhook_test_results.py
rm -f services/telegram-bot/verify_webhook_conversion.py
rm -f services/telegram-bot/deploy_webhook.sh
rm -f WEBHOOK_ARCHITECTURE.md
rm -f services/telegram-bot/WEBHOOK_MIGRATION_GUIDE.md
rm -f services/telegram-bot/health.py
rm -f services/telegram-bot/__pycache__/main_webhook.cpython-312.pyc

# Test
docker-compose down
docker-compose up -d --build
docker ps

# Commit
git add -A
git commit -m "cleanup: Remove webhook remnants from polling-only bot"
```

## What This Does:
- Removes unused webhook files
- Fixes "unhealthy" container status
- Keeps polling bot functionality intact
- Cleans up codebase for production

## Rollback If Needed:
```bash
git checkout HEAD~1
docker-compose up -d --build
```