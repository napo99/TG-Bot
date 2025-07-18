#!/bin/bash

# Verification Script - Check for ANY remaining health check dependencies
echo "🔍 HEALTH CHECK DEPENDENCY VERIFICATION"
echo "========================================"

echo "1. Checking docker-compose.yml for health check references..."
grep -n -i "health" /Users/screener-m3/projects/crypto-assistant/docker-compose.yml || echo "✅ No health check references in main docker-compose.yml"

echo ""
echo "2. Checking all Dockerfiles for health check references..."
find /Users/screener-m3/projects/crypto-assistant -name "Dockerfile*" -exec grep -l -i "healthcheck" {} \; || echo "✅ No health check references in Dockerfiles"

echo ""
echo "3. Checking for service_healthy conditions..."
grep -r "service_healthy" /Users/screener-m3/projects/crypto-assistant/ || echo "✅ No service_healthy conditions found"

echo ""
echo "4. Checking for curl health check commands..."
grep -r "curl.*health" /Users/screener-m3/projects/crypto-assistant/ || echo "✅ No curl health check commands found"

echo ""
echo "5. Listing all Docker Compose files..."
find /Users/screener-m3/projects/crypto-assistant -name "docker-compose*.yml" -exec echo "📄 {}" \; -exec grep -n -i "health" {} \; || echo "✅ No health check references in any docker-compose files"

echo ""
echo "6. Checking for any health-related environment variables..."
grep -r "HEALTH" /Users/screener-m3/projects/crypto-assistant/ || echo "✅ No health-related environment variables found"

echo ""
echo "🎯 VERIFICATION COMPLETE"
echo "========================"
echo "Run this script after cleanup to verify all health checks are removed from telegram-bot"