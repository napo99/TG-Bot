#!/bin/bash

# Complete Docker Cleanup Script for Crypto Assistant
# This script removes ALL Docker cache, containers, images, and networks
# Use with caution - this will completely reset your Docker environment

echo "🧹 COMPLETE DOCKER CLEANUP - CRYPTO ASSISTANT"
echo "==============================================="
echo ""
echo "⚠️  WARNING: This will completely clean your Docker environment"
echo "   - All containers will be stopped and removed"
echo "   - All images will be removed"
echo "   - All networks will be removed"
echo "   - All build cache will be cleared"
echo ""
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo "🔄 Starting complete Docker cleanup..."
echo ""

# 1. Stop all running containers
echo "1️⃣ Stopping all containers..."
docker stop $(docker ps -q) 2>/dev/null || echo "   No running containers to stop"

# 2. Remove ALL containers (running and stopped)
echo "2️⃣ Removing all containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || echo "   No containers to remove"

# 3. Remove ALL images
echo "3️⃣ Removing all images..."
docker rmi -f $(docker images -q) 2>/dev/null || echo "   No images to remove"

# 4. Remove ALL networks (except defaults)
echo "4️⃣ Removing all networks..."
docker network prune -f 2>/dev/null || echo "   No networks to remove"

# 5. Remove ALL volumes
echo "5️⃣ Removing all volumes..."
docker volume prune -f 2>/dev/null || echo "   No volumes to remove"

# 6. Clean build cache
echo "6️⃣ Cleaning build cache..."
docker builder prune -af 2>/dev/null || echo "   No build cache to clear"

# 7. System-wide cleanup
echo "7️⃣ System-wide cleanup..."
docker system prune -af --volumes 2>/dev/null || echo "   System already clean"

echo ""
echo "✅ Complete Docker cleanup finished!"
echo ""
echo "📊 Current Docker status:"
echo "========================"
docker system df 2>/dev/null || echo "Docker system info not available"
echo ""
echo "🔍 Remaining containers:"
docker ps -a 2>/dev/null || echo "No containers found"
echo ""
echo "🖼️  Remaining images:"
docker images 2>/dev/null || echo "No images found"
echo ""
echo "🌐 Remaining networks:"
docker network ls 2>/dev/null || echo "No networks found"
echo ""
echo "💾 Remaining volumes:"
docker volume ls 2>/dev/null || echo "No volumes found"

echo ""
echo "🎯 CLEANUP COMPLETE - Ready for fresh Docker build!"
echo "   Next steps:"
echo "   1. Run health check verification script"
echo "   2. Rebuild containers with clean configuration"
echo "   3. Verify no health checks remain"