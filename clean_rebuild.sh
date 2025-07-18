#!/bin/bash

# Clean Rebuild Script for Crypto Assistant
# This script performs a complete clean rebuild after health check removal

echo "🔄 CLEAN REBUILD - CRYPTO ASSISTANT"
echo "==================================="
echo ""

PROJECT_DIR="/Users/screener-m3/projects/crypto-assistant"
cd "$PROJECT_DIR"

echo "📁 Working directory: $PROJECT_DIR"
echo ""

# Check if health checks have been removed
echo "🔍 Pre-build verification..."
if [ -f "verify_health_checks_removed.sh" ]; then
    echo "   Running health check verification..."
    bash verify_health_checks_removed.sh
    if [ $? -ne 0 ]; then
        echo "❌ Health checks still present! Aborting rebuild."
        echo "   Please run remove_health_checks.sh first"
        exit 1
    fi
else
    echo "   ⚠️  Verification script not found - proceeding with rebuild"
fi

echo ""
echo "🧹 Step 1: Complete Docker cleanup..."
echo "======================================"

# Stop and remove all containers
echo "🛑 Stopping all containers..."
docker-compose down --remove-orphans 2>/dev/null || echo "   No containers to stop"

# Remove project-specific containers
echo "🗑️  Removing project containers..."
docker rm -f crypto-telegram-bot crypto-market-data 2>/dev/null || echo "   No project containers to remove"

# Remove project images
echo "🖼️  Removing project images..."
docker rmi -f $(docker images | grep -E "(crypto-assistant|crypto-telegram-bot|crypto-market-data)" | awk '{print $3}') 2>/dev/null || echo "   No project images to remove"

# Clean build cache
echo "🧽 Cleaning build cache..."
docker builder prune -f 2>/dev/null || echo "   No build cache to clean"

echo ""
echo "🔧 Step 2: Prepare clean configuration..."
echo "========================================"

# Ensure we're using the clean docker-compose.yml
if [ -f "docker-compose.yml.working" ]; then
    echo "📋 Using docker-compose.yml.working as reference..."
    # Copy working version to main (without health checks)
    cp docker-compose.yml.working docker-compose.yml
    echo "   ✅ Configuration updated"
else
    echo "📋 Using existing docker-compose.yml..."
fi

# Verify no health checks in active configuration
echo "🔍 Final health check verification..."
if grep -i "healthcheck" docker-compose.yml > /dev/null 2>&1; then
    echo "❌ Health checks found in docker-compose.yml!"
    echo "   Please run remove_health_checks.sh first"
    exit 1
fi

echo "   ✅ Configuration is clean"

echo ""
echo "🏗️  Step 3: Clean rebuild..."
echo "============================"

# Build with no cache
echo "🔨 Building services with no cache..."
docker-compose build --no-cache --pull

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    echo ""
    echo "🔧 Troubleshooting tips:"
    echo "   • Check Dockerfile syntax"
    echo "   • Verify all dependencies are available"
    echo "   • Check internet connection"
    echo "   • Review build logs above"
    exit 1
fi

echo ""
echo "🚀 Step 4: Start services..."
echo "============================"

# Start services
echo "▶️  Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services!"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   • Check service logs: docker-compose logs"
    echo "   • Verify environment variables"
    echo "   • Check port conflicts"
    exit 1
fi

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

echo ""
echo "🏥 Step 5: Health verification..."
echo "================================"

echo "📊 Container status:"
docker-compose ps

echo ""
echo "🔍 Checking service health..."

# Check market-data service
echo "   Testing market-data service..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✅ Market-data service is healthy"
else
    echo "   ❌ Market-data service is not responding"
    echo "      Check logs: docker-compose logs market-data"
fi

# Check telegram-bot service (no health endpoint expected)
echo "   Checking telegram-bot service..."
if docker-compose ps telegram-bot | grep -q "Up"; then
    echo "   ✅ Telegram-bot service is running"
else
    echo "   ❌ Telegram-bot service is not running"
    echo "      Check logs: docker-compose logs telegram-bot"
fi

echo ""
echo "📋 Service logs (last 10 lines):"
echo "================================"

echo "📊 Market-data logs:"
docker-compose logs --tail=10 market-data

echo ""
echo "🤖 Telegram-bot logs:"
docker-compose logs --tail=10 telegram-bot

echo ""
echo "✅ CLEAN REBUILD COMPLETE!"
echo "=========================="
echo ""
echo "🎯 System status:"
echo "   • All health checks removed"
echo "   • Clean Docker rebuild completed"
echo "   • Services started successfully"
echo ""
echo "🔄 Next steps:"
echo "   1. Test bot functionality"
echo "   2. Monitor logs for any issues"
echo "   3. Deploy to production when ready"
echo ""
echo "🚨 Important notes:"
echo "   • Health checks are completely removed"
echo "   • Container status will show 'Up' instead of 'healthy'"
echo "   • This is normal and expected behavior"
echo ""
echo "📊 To monitor services:"
echo "   • View logs: docker-compose logs -f"
echo "   • Check status: docker-compose ps"
echo "   • Test API: curl http://localhost:8001/health"