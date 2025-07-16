#!/bin/bash
# Phase 1 Docker Service Restart Script

set -e  # Exit on any error

echo "🔄 PHASE 1: DOCKER SERVICE RESTART"
echo "=================================="

# Navigate to project directory
cd /Users/screener-m3/projects/crypto-assistant

echo "📊 Current Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "🔄 Restarting market-data service..."
docker-compose restart market-data
echo "✅ Market-data service restart initiated"
echo ""

echo "⏳ Waiting 15 seconds for service to be ready..."
sleep 15
echo ""

echo "📊 Post-restart Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "🧪 Testing market-data health endpoint..."
curl -f http://localhost:8001/health || echo "❌ Health check failed"
echo ""

echo "🎯 DOCKER RESTART COMPLETE!"
echo "Market-data service should now have the updated provider files."