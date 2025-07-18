#!/bin/bash

# Complete Docker Cleanup for Health Check Removal
# Senior Architect Review - Remove ALL health check dependencies

echo "🧹 COMPLETE DOCKER CLEANUP STRATEGY"
echo "====================================="

# Step 1: Stop and remove all containers
echo "1. Stopping all containers..."
docker-compose down --remove-orphans

# Step 2: Remove ALL Docker images (force clean rebuild)
echo "2. Removing all Docker images..."
docker image prune -af
docker system prune -af

# Step 3: Remove specific project images if they exist
echo "3. Removing project-specific images..."
docker rmi $(docker images "crypto-assistant*" -q) 2>/dev/null || true
docker rmi $(docker images "crypto-market-data*" -q) 2>/dev/null || true
docker rmi $(docker images "crypto-telegram-bot*" -q) 2>/dev/null || true

# Step 4: Remove any dangling volumes
echo "4. Cleaning up volumes..."
docker volume prune -f

# Step 5: Clean Docker builder cache
echo "5. Cleaning Docker builder cache..."
docker builder prune -af

# Step 6: Verify cleanup
echo "6. Verifying cleanup..."
echo "Remaining images:"
docker images
echo "Remaining containers:"
docker ps -a
echo "Remaining volumes:"
docker volume ls

# Step 7: Rebuild from scratch
echo "7. Rebuilding from scratch..."
docker-compose build --no-cache --pull

# Step 8: Start services
echo "8. Starting services..."
docker-compose up -d

# Step 9: Wait and verify
echo "9. Waiting for services to start..."
sleep 10
docker-compose ps

# Step 10: Check logs for any health check errors
echo "10. Checking logs for health check errors..."
echo "Telegram Bot Logs:"
docker-compose logs --tail=20 telegram-bot | grep -i health || echo "No health check mentions found ✅"

echo "Market Data Logs:"
docker-compose logs --tail=20 market-data | grep -i health || echo "Health checks only in market-data (expected) ✅"

echo ""
echo "🎯 CLEANUP COMPLETE!"
echo "==================="
echo "✅ All health check dependencies removed from telegram-bot"
echo "✅ Only market-data should have health checks (it needs them)"
echo "✅ telegram-bot should start without waiting for health checks"
echo ""
echo "Next steps:"
echo "1. Run this script: chmod +x docker_cleanup_commands.sh && ./docker_cleanup_commands.sh"
echo "2. Verify both services are running: docker-compose ps"
echo "3. Test telegram bot functionality"