#!/bin/bash

# Verify Health Checks Removal Script for Crypto Assistant
# This script verifies that all health checks have been completely removed

echo "🔍 VERIFYING HEALTH CHECKS REMOVAL"
echo "=================================="
echo ""

PROJECT_DIR="/Users/screener-m3/projects/crypto-assistant"
HEALTH_CHECK_FOUND=false

echo "📁 Checking Docker configuration files..."
echo ""

# Function to check for health checks in a file
check_health_checks() {
    local file="$1"
    local file_display="$2"
    
    if [ -f "$file" ]; then
        echo "🔍 Checking $file_display..."
        
        # Check for various health check patterns
        local healthcheck_patterns=(
            "healthcheck:"
            "HEALTHCHECK"
            "health-check"
            "health_check"
            "curl -f.*health"
            "test:.*health"
            "interval:"
            "timeout:"
            "retries:"
            "start_period:"
            "start-period:"
        )
        
        local found_issues=false
        
        for pattern in "${healthcheck_patterns[@]}"; do
            if grep -i "$pattern" "$file" > /dev/null 2>&1; then
                if [ "$found_issues" = false ]; then
                    echo "   ❌ Health check references found:"
                    found_issues=true
                    HEALTH_CHECK_FOUND=true
                fi
                echo "      • Pattern: $pattern"
                grep -n -i "$pattern" "$file" | sed 's/^/        /'
            fi
        done
        
        if [ "$found_issues" = false ]; then
            echo "   ✅ No health checks found"
        fi
        
        echo ""
    else
        echo "🔍 $file_display - File not found (OK)"
        echo ""
    fi
}

# Check all Docker configuration files
check_health_checks "$PROJECT_DIR/docker-compose.yml" "docker-compose.yml"
check_health_checks "$PROJECT_DIR/docker-compose.yml.working" "docker-compose.yml.working"
check_health_checks "$PROJECT_DIR/services/telegram-bot/docker-compose.production.yml" "docker-compose.production.yml"
check_health_checks "$PROJECT_DIR/services/market-data/Dockerfile" "market-data Dockerfile"
check_health_checks "$PROJECT_DIR/services/telegram-bot/Dockerfile" "telegram-bot Dockerfile"
check_health_checks "$PROJECT_DIR/services/telegram-bot/Dockerfile.aws" "telegram-bot Dockerfile.aws"

echo "🌐 Checking for any other Docker files..."
echo ""

# Find any other Docker files
find "$PROJECT_DIR" -name "docker-compose*.yml" -o -name "Dockerfile*" | while read -r file; do
    # Skip files we already checked
    case "$file" in
        "$PROJECT_DIR/docker-compose.yml"|"$PROJECT_DIR/docker-compose.yml.working"|"$PROJECT_DIR/services/telegram-bot/docker-compose.production.yml"|"$PROJECT_DIR/services/market-data/Dockerfile"|"$PROJECT_DIR/services/telegram-bot/Dockerfile"|"$PROJECT_DIR/services/telegram-bot/Dockerfile.aws")
            continue
            ;;
        *)
            echo "📄 Additional Docker file found: $file"
            check_health_checks "$file" "$(basename "$file")"
            ;;
    esac
done

echo ""
echo "🏥 Checking for health endpoint files..."
echo ""

# Check for health endpoint implementation files
find "$PROJECT_DIR" -name "*.py" -exec grep -l "health" {} \; | while read -r file; do
    if grep -i "health.*endpoint\|/health\|health.*check" "$file" > /dev/null 2>&1; then
        echo "🔍 Health endpoint found in: $file"
        grep -n -i "health.*endpoint\|/health\|health.*check" "$file" | head -3 | sed 's/^/   /'
        echo ""
    fi
done

echo ""
echo "🐳 Checking Docker containers for health status..."
echo ""

# Check if any containers are running with health checks
if command -v docker > /dev/null 2>&1; then
    echo "📊 Current container health status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null || echo "   No containers running"
    echo ""
    
    # Check for any containers showing health status
    if docker ps --format "{{.Status}}" | grep -i "health" > /dev/null 2>&1; then
        echo "❌ Containers with health status detected:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -i "health" | sed 's/^/   /'
        HEALTH_CHECK_FOUND=true
    else
        echo "✅ No containers with health status"
    fi
else
    echo "⚠️  Docker not available - cannot check container status"
fi

echo ""
echo "📋 VERIFICATION SUMMARY"
echo "======================"

if [ "$HEALTH_CHECK_FOUND" = true ]; then
    echo "❌ HEALTH CHECKS STILL PRESENT"
    echo ""
    echo "🔧 Required actions:"
    echo "   1. Remove remaining health check references"
    echo "   2. Run complete Docker cleanup"
    echo "   3. Rebuild containers from scratch"
    echo "   4. Run this verification script again"
    echo ""
    echo "🚨 DO NOT DEPLOY TO PRODUCTION until all health checks are removed!"
    exit 1
else
    echo "✅ ALL HEALTH CHECKS SUCCESSFULLY REMOVED"
    echo ""
    echo "🎯 Ready for clean Docker rebuild:"
    echo "   • No health check configurations found"
    echo "   • No containers with health status"
    echo "   • Safe to proceed with production deployment"
    echo ""
    echo "🔄 Next steps:"
    echo "   1. Run complete Docker cleanup"
    echo "   2. Rebuild containers: docker-compose up -d --build"
    echo "   3. Test functionality without health checks"
    echo "   4. Deploy to production"
fi