#!/bin/bash

# Remove Health Checks Script for Crypto Assistant
# This script removes all health checks from Docker configurations

echo "🏥 REMOVING ALL HEALTH CHECKS FROM DOCKER CONFIGURATIONS"
echo "========================================================="
echo ""

PROJECT_DIR="/Users/screener-m3/projects/crypto-assistant"
BACKUP_DIR="$PROJECT_DIR/docker-backup-$(date +%Y%m%d-%H%M%S)"

echo "📁 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo ""
echo "💾 Backing up original Docker files..."

# Backup docker-compose.yml
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_DIR/docker-compose.yml.backup"
    echo "   ✅ Backed up docker-compose.yml"
fi

# Backup docker-compose.yml.working
if [ -f "$PROJECT_DIR/docker-compose.yml.working" ]; then
    cp "$PROJECT_DIR/docker-compose.yml.working" "$BACKUP_DIR/docker-compose.yml.working.backup"
    echo "   ✅ Backed up docker-compose.yml.working"
fi

# Backup production compose file
if [ -f "$PROJECT_DIR/services/telegram-bot/docker-compose.production.yml" ]; then
    cp "$PROJECT_DIR/services/telegram-bot/docker-compose.production.yml" "$BACKUP_DIR/docker-compose.production.yml.backup"
    echo "   ✅ Backed up docker-compose.production.yml"
fi

# Backup market-data Dockerfile
if [ -f "$PROJECT_DIR/services/market-data/Dockerfile" ]; then
    cp "$PROJECT_DIR/services/market-data/Dockerfile" "$BACKUP_DIR/market-data-Dockerfile.backup"
    echo "   ✅ Backed up market-data Dockerfile"
fi

# Backup telegram-bot Dockerfile
if [ -f "$PROJECT_DIR/services/telegram-bot/Dockerfile" ]; then
    cp "$PROJECT_DIR/services/telegram-bot/Dockerfile" "$BACKUP_DIR/telegram-bot-Dockerfile.backup"
    echo "   ✅ Backed up telegram-bot Dockerfile"
fi

echo ""
echo "🔧 Removing health checks from Docker configurations..."

echo ""
echo "1️⃣ Removing health checks from docker-compose.yml..."
# Remove healthcheck section from docker-compose.yml
sed -i '' '/healthcheck:/,/start_period: 30s/d' "$PROJECT_DIR/docker-compose.yml"
echo "   ✅ Health checks removed from docker-compose.yml"

echo ""
echo "2️⃣ Removing health checks from docker-compose.yml.working..."
# Remove healthcheck section from docker-compose.yml.working
sed -i '' '/healthcheck:/,/retries: 3/d' "$PROJECT_DIR/docker-compose.yml.working"
echo "   ✅ Health checks removed from docker-compose.yml.working"

echo ""
echo "3️⃣ Removing health checks from docker-compose.production.yml..."
# Remove healthcheck section from production compose file
sed -i '' '/healthcheck:/,/retries: 3/d' "$PROJECT_DIR/services/telegram-bot/docker-compose.production.yml"
echo "   ✅ Health checks removed from docker-compose.production.yml"

echo ""
echo "4️⃣ Removing health checks from market-data Dockerfile..."
# Remove HEALTHCHECK line from market-data Dockerfile
sed -i '' '/HEALTHCHECK/,/CMD curl -f/d' "$PROJECT_DIR/services/market-data/Dockerfile"
echo "   ✅ Health checks removed from market-data Dockerfile"

echo ""
echo "5️⃣ Removing curl from market-data Dockerfile (no longer needed)..."
# Remove curl from market-data Dockerfile since it's only needed for health checks
sed -i '' 's/curl \\///' "$PROJECT_DIR/services/market-data/Dockerfile"
sed -i '' '/\&\& apt-get clean/i\
    # curl removed - no longer needed without health checks' "$PROJECT_DIR/services/market-data/Dockerfile"
echo "   ✅ curl removed from market-data Dockerfile"

echo ""
echo "6️⃣ Removing curl from telegram-bot Dockerfile..."
# Remove curl from telegram-bot Dockerfile
sed -i '' 's/curl \\///' "$PROJECT_DIR/services/telegram-bot/Dockerfile"
sed -i '' '/\&\& apt-get clean/i\
    # curl removed - no longer needed without health checks' "$PROJECT_DIR/services/telegram-bot/Dockerfile"
echo "   ✅ curl removed from telegram-bot Dockerfile"

echo ""
echo "✅ HEALTH CHECK REMOVAL COMPLETE!"
echo ""
echo "📋 Summary of changes:"
echo "====================="
echo "   • docker-compose.yml - health checks removed"
echo "   • docker-compose.yml.working - health checks removed"
echo "   • docker-compose.production.yml - health checks removed"
echo "   • market-data Dockerfile - HEALTHCHECK removed, curl removed"
echo "   • telegram-bot Dockerfile - curl removed"
echo ""
echo "💾 Backup files saved in: $BACKUP_DIR"
echo ""
echo "🔄 Next steps:"
echo "   1. Run complete Docker cleanup script"
echo "   2. Rebuild containers with clean configuration"
echo "   3. Verify no health checks remain"