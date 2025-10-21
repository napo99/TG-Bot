#!/bin/bash

# Health Check Script for Monitoring System
# Comprehensive health validation for all components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🏥 Crypto Assistant System Health Check"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check results
OVERALL_HEALTH=true

print_status() {
    local status=$1
    local message=$2
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC} - $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC} - $message"
        OVERALL_HEALTH=false
    else
        echo -e "${BLUE}ℹ️  INFO${NC} - $message"
    fi
}

check_docker() {
    echo -e "\n${BLUE}🐳 DOCKER ENVIRONMENT${NC}"
    echo "========================"
    
    if command -v docker &> /dev/null; then
        print_status "PASS" "Docker is installed"
        
        if docker info &> /dev/null; then
            print_status "PASS" "Docker daemon is running"
        else
            print_status "FAIL" "Docker daemon is not running"
        fi
        
        if command -v docker-compose &> /dev/null; then
            print_status "PASS" "Docker Compose is installed"
        else
            print_status "FAIL" "Docker Compose is not installed"
        fi
    else
        print_status "FAIL" "Docker is not installed"
    fi
}

check_main_services() {
    echo -e "\n${BLUE}🔧 MAIN SERVICES${NC}"
    echo "==================="
    
    # Check crypto network
    if docker network ls | grep -q "crypto-network"; then
        print_status "PASS" "Crypto network exists"
    else
        print_status "FAIL" "Crypto network not found"
    fi
    
    # Check main services
    MAIN_SERVICES=("crypto-market-data" "crypto-telegram-bot")
    
    for service in "${MAIN_SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | grep -q "Up"; then
            print_status "PASS" "$service is running"
        else
            print_status "FAIL" "$service is not running"
        fi
    done
    
    # Test market-data API
    if curl -f -s http://localhost:8001/health &> /dev/null; then
        print_status "PASS" "Market data API is accessible"
    else
        print_status "FAIL" "Market data API is not accessible"
    fi
}

check_monitoring_services() {
    echo -e "\n${BLUE}📊 MONITORING SERVICES${NC}"
    echo "========================="
    
    MONITORING_SERVICES=(
        "crypto-liquidation-monitor"
        "crypto-oi-detector"
        "crypto-alert-dispatcher"
        "crypto-monitoring-coordinator"
    )
    
    local running_count=0
    
    for service in "${MONITORING_SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | grep -q "Up"; then
            print_status "PASS" "$service is running"
            ((running_count++))
        else
            print_status "WARN" "$service is not running"
        fi
    done
    
    if [ $running_count -eq ${#MONITORING_SERVICES[@]} ]; then
        print_status "PASS" "All monitoring services are running"
    elif [ $running_count -gt 0 ]; then
        print_status "WARN" "$running_count/${#MONITORING_SERVICES[@]} monitoring services running"
    else
        print_status "INFO" "No monitoring services running (proactive alerts disabled)"
    fi
    
    # Test monitoring coordinator API
    if curl -f -s http://localhost:8002/health &> /dev/null; then
        print_status "PASS" "Monitoring coordinator API is accessible"
    else
        print_status "WARN" "Monitoring coordinator API is not accessible"
    fi
}

check_file_structure() {
    echo -e "\n${BLUE}📁 FILE STRUCTURE${NC}"
    echo "==================="
    
    # Check required directories
    REQUIRED_DIRS=(
        "services/monitoring"
        "shared/alerts"
        "shared/models"
        "scripts/deployment"
        "data"
    )
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            print_status "PASS" "Directory exists: $dir"
        else
            print_status "FAIL" "Directory missing: $dir"
        fi
    done
    
    # Check alert files
    ALERT_FILES=(
        "shared/alerts/liquidation_alerts.json"
        "shared/alerts/oi_alerts.json"
    )
    
    for file in "${ALERT_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            print_status "PASS" "Alert file exists: $file"
        else
            print_status "INFO" "Alert file not yet created: $file"
        fi
    done
}

check_environment() {
    echo -e "\n${BLUE}🔐 ENVIRONMENT VARIABLES${NC}"
    echo "==========================="
    
    # Check required environment variables
    REQUIRED_VARS=(
        "TELEGRAM_BOT_TOKEN"
        "TELEGRAM_CHAT_ID"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -n "${!var}" ]; then
            print_status "PASS" "$var is set"
        else
            print_status "FAIL" "$var is not set"
        fi
    done
    
    # Check optional environment variables
    OPTIONAL_VARS=(
        "ENABLE_LIQUIDATION_ALERTS"
        "ENABLE_OI_ALERTS"
        "LIQUIDATION_THRESHOLD_BTC"
        "OI_THRESHOLD_BTC"
    )
    
    for var in "${OPTIONAL_VARS[@]}"; do
        if [ -n "${!var}" ]; then
            print_status "PASS" "$var is set (${!var})"
        else
            print_status "INFO" "$var using default value"
        fi
    done
}

check_memory_usage() {
    echo -e "\n${BLUE}💾 MEMORY USAGE${NC}"
    echo "=================="
    
    # Get memory usage of all crypto containers
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo "Container memory usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" $(docker ps --format "{{.Names}}" | grep crypto) 2>/dev/null || echo "No crypto containers running"
        
        # Get system memory
        if command -v free &> /dev/null; then
            echo -e "\nSystem memory:"
            free -h
        elif [ -f /proc/meminfo ]; then
            echo -e "\nSystem memory:"
            grep -E "MemTotal|MemFree|MemAvailable" /proc/meminfo
        fi
    else
        print_status "INFO" "Cannot check memory usage - Docker not available"
    fi
}

test_alert_system() {
    echo -e "\n${BLUE}🔔 ALERT SYSTEM TEST${NC}"
    echo "======================"
    
    # Check if we can test alerts
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        read -p "Send test alert to Telegram? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 -c "
import sys, os
sys.path.append('$PROJECT_ROOT')
import asyncio
from shared.utils.telegram_client import TelegramClient

async def test():
    client = TelegramClient()
    async with client:
        success = await client.test_connection()
        print('✅ Test alert sent successfully' if success else '❌ Test alert failed')

asyncio.run(test())
" 2>/dev/null || print_status "WARN" "Could not send test alert"
        fi
    else
        print_status "INFO" "Telegram credentials not configured - skipping alert test"
    fi
}

generate_summary() {
    echo -e "\n${BLUE}📋 HEALTH CHECK SUMMARY${NC}"
    echo "========================="
    
    if [ "$OVERALL_HEALTH" = true ]; then
        echo -e "${GREEN}🎉 OVERALL STATUS: HEALTHY${NC}"
        echo ""
        echo "✅ System is ready for production use"
        echo "✅ All critical components are functional"
        echo ""
        echo "📊 Access monitoring dashboard: http://localhost:8002/status"
    else
        echo -e "${RED}❌ OVERALL STATUS: UNHEALTHY${NC}"
        echo ""
        echo "⚠️  Critical issues found that require attention"
        echo "🔧 Please resolve the FAIL items above"
        echo ""
        echo "💡 Common fixes:"
        echo "   • Start main services: docker-compose up -d"
        echo "   • Start monitoring: bash scripts/deployment/start_monitoring.sh"
        echo "   • Set environment variables in .env file"
    fi
    
    echo ""
    echo "🔍 For detailed logs: docker-compose logs"
    echo "📚 Documentation: README.md"
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    check_docker
    check_environment
    check_file_structure
    check_main_services
    check_monitoring_services
    check_memory_usage
    test_alert_system
    generate_summary
    
    # Exit with error if health check failed
    if [ "$OVERALL_HEALTH" != true ]; then
        exit 1
    fi
}

main "$@"