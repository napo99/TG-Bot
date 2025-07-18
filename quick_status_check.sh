#!/bin/bash

# Quick Status Check for Crypto Assistant
# This script provides a quick overview of the current Docker state

echo "🔍 QUICK STATUS CHECK - CRYPTO ASSISTANT"
echo "========================================"
echo ""

PROJECT_DIR="/Users/screener-m3/projects/crypto-assistant"
cd "$PROJECT_DIR"

echo "📁 Working directory: $PROJECT_DIR"
echo ""

echo "🐳 Docker System Status:"
echo "========================"
if command -v docker > /dev/null 2>&1; then
    echo "✅ Docker is available"
    docker system df 2>/dev/null || echo "❌ Docker system not accessible"
else
    echo "❌ Docker is not available"
fi

echo ""
echo "📊 Current Containers:"
echo "====================="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null || echo "No containers found"

echo ""
echo "🔍 Health Check Status:"
echo "======================"

# Check for health status in containers
if docker ps --format "{{.Status}}" | grep -i "health" > /dev/null 2>&1; then
    echo "❌ Containers with health status detected:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -i "health"
else
    echo "✅ No containers with health status (Good!)"
fi

echo ""
echo "📄 Configuration Health Checks:"
echo "==============================="

# Quick check for health checks in main files
HEALTH_FOUND=false

if [ -f "docker-compose.yml" ]; then
    if grep -q "healthcheck" docker-compose.yml; then
        echo "❌ Health checks found in docker-compose.yml"
        HEALTH_FOUND=true
    else
        echo "✅ docker-compose.yml is clean"
    fi
fi

if [ -f "services/market-data/Dockerfile" ]; then
    if grep -q "HEALTHCHECK" services/market-data/Dockerfile; then
        echo "❌ Health checks found in market-data Dockerfile"
        HEALTH_FOUND=true
    else
        echo "✅ market-data Dockerfile is clean"
    fi
fi

if [ -f "services/telegram-bot/Dockerfile" ]; then
    if grep -q "HEALTHCHECK" services/telegram-bot/Dockerfile; then
        echo "❌ Health checks found in telegram-bot Dockerfile"
        HEALTH_FOUND=true
    else
        echo "✅ telegram-bot Dockerfile is clean"
    fi
fi

echo ""
echo "🎯 SUMMARY:"
echo "==========="

if [ "$HEALTH_FOUND" = true ]; then
    echo "❌ HEALTH CHECKS STILL PRESENT"
    echo ""
    echo "🔧 Recommended actions:"
    echo "   1. Run: ./remove_health_checks.sh"
    echo "   2. Run: ./complete_docker_cleanup.sh"
    echo "   3. Run: ./clean_rebuild.sh"
else
    echo "✅ HEALTH CHECKS REMOVED"
    echo ""
    echo "🎯 Ready for production deployment"
fi

echo ""
echo "🚀 Available Scripts:"
echo "===================="
echo "   • ./remove_health_checks.sh - Remove health checks from configs"
echo "   • ./complete_docker_cleanup.sh - Complete Docker cleanup"
echo "   • ./verify_health_checks_removed.sh - Verify cleanup"
echo "   • ./clean_rebuild.sh - Clean rebuild process"
echo "   • ./quick_status_check.sh - This script"
echo ""
echo "📚 For complete guide: cat COMPLETE_CLEANUP_GUIDE.md"