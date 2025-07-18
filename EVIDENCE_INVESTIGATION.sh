#!/bin/bash

echo "=== 🔍 EVIDENCE INVESTIGATION: July 4 vs Current Health Check ==="
echo

# July 4 deployment commit (from git log analysis)
JULY4_COMMIT="f9f1882b5e40d6dc34744575bf2565df84a61607"
echo "📅 July 4 AWS Deployment Commit: $JULY4_COMMIT"
echo

echo "1️⃣ CHECKING: Did July 4 deployment have health check in Dockerfile.aws?"
echo "---"
git show $JULY4_COMMIT:services/telegram-bot/Dockerfile.aws | grep -A 3 -B 3 "HEALTHCHECK\|health\|curl" || echo "❌ No health check found in July 4 deployment"
echo

echo "2️⃣ CHECKING: Current rollback state (c182b71f) health check"
echo "---"
git show c182b71f:services/telegram-bot/Dockerfile.aws | grep -A 3 -B 3 "HEALTHCHECK\|health\|curl" || echo "❌ No health check found in current rollback state"
echo

echo "3️⃣ CHECKING: When was health check added to Dockerfile.aws?"
echo "---"
git log --oneline --follow -p -- services/telegram-bot/Dockerfile.aws | grep -B 5 -A 5 "HEALTHCHECK" | head -20
echo

echo "4️⃣ CHECKING: Git blame for health check lines"
echo "---"
git blame services/telegram-bot/Dockerfile.aws | grep -A 3 -B 3 "HEALTHCHECK\|health\|curl" || echo "❌ No health check lines found"
echo

echo "5️⃣ CHECKING: Does July 4 main_webhook.py have /health endpoint?"
echo "---"
git show $JULY4_COMMIT:services/telegram-bot/main_webhook.py | grep -A 5 -B 5 "route.*health\|def health" || echo "❌ No health endpoint found in July 4 main_webhook.py"
echo

echo "=== 📋 EVIDENCE SUMMARY ==="
echo "This investigation will show:"
echo "- ✅ Whether July 4 deployment had health check in Dockerfile.aws"
echo "- ✅ Whether current rollback state has health check"
echo "- ✅ When health check was added (git history)"
echo "- ✅ Whether July 4 had Flask /health endpoint"
echo "- ✅ How the bot worked before without health check failing"