#!/bin/bash
# Simple monitoring script for crypto-assistant
# Focus: Quick health checks and problem detection

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🔍 Crypto Assistant Health Monitor${NC}"
echo "=================================="

# Function to check if docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker is not running${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
    return 0
}

# Function to check containers
check_containers() {
    echo -e "\n${BLUE}📦 Checking containers...${NC}"
    
    # Expected containers
    local expected_containers=("crypto-telegram-bot" "crypto-market-data")
    local all_healthy=true
    
    for container in "${expected_containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            # Container is running, check health
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
            
            if [ "$health_status" = "healthy" ]; then
                echo -e "   ${GREEN}✅ $container: running and healthy${NC}"
            elif [ "$health_status" = "no-health-check" ]; then
                echo -e "   ${YELLOW}⚠️  $container: running (no health check)${NC}"
            else
                echo -e "   ${RED}❌ $container: running but unhealthy${NC}"
                all_healthy=false
            fi
        else
            echo -e "   ${RED}❌ $container: not running${NC}"
            all_healthy=false
        fi
    done
    
    return $all_healthy
}

# Function to check API endpoints
check_apis() {
    echo -e "\n${BLUE}🌐 Checking API endpoints...${NC}"
    
    local all_apis_ok=true
    
    # Telegram Bot Health
    if curl -s -f "http://localhost:8080/health" &> /dev/null; then
        echo -e "   ${GREEN}✅ Telegram Bot API: responding${NC}"
    else
        echo -e "   ${RED}❌ Telegram Bot API: not responding${NC}"
        all_apis_ok=false
    fi
    
    # Market Data Health
    if curl -s -f "http://localhost:8001/health" &> /dev/null; then
        echo -e "   ${GREEN}✅ Market Data API: responding${NC}"
    else
        echo -e "   ${RED}❌ Market Data API: not responding${NC}"
        all_apis_ok=false
    fi
    
    # Market Data Function Test
    if curl -s -f -X POST "http://localhost:8001/comprehensive_analysis" \
        -H "Content-Type: application/json" \
        -d '{"symbol": "BTC/USDT", "timeframe": "15m"}' &> /dev/null; then
        echo -e "   ${GREEN}✅ Market Data Function: working${NC}"
    else
        echo -e "   ${RED}❌ Market Data Function: not working${NC}"
        all_apis_ok=false
    fi
    
    return $all_apis_ok
}

# Function to check system resources
check_resources() {
    echo -e "\n${BLUE}🖥️  Checking system resources...${NC}"
    
    # Memory check
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local memory_available=$(free -m | grep Mem | awk '{print $7}')
    
    if (( $(echo "$memory_usage > 85" | bc -l) )); then
        echo -e "   ${RED}❌ Memory: ${memory_usage}% used (${memory_available}MB available)${NC}"
    elif (( $(echo "$memory_usage > 70" | bc -l) )); then
        echo -e "   ${YELLOW}⚠️  Memory: ${memory_usage}% used (${memory_available}MB available)${NC}"
    else
        echo -e "   ${GREEN}✅ Memory: ${memory_usage}% used (${memory_available}MB available)${NC}"
    fi
    
    # Disk check
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    local disk_available=$(df -h / | tail -1 | awk '{print $4}')
    
    if (( disk_usage > 90 )); then
        echo -e "   ${RED}❌ Disk: ${disk_usage}% used (${disk_available} available)${NC}"
    elif (( disk_usage > 80 )); then
        echo -e "   ${YELLOW}⚠️  Disk: ${disk_usage}% used (${disk_available} available)${NC}"
    else
        echo -e "   ${GREEN}✅ Disk: ${disk_usage}% used (${disk_available} available)${NC}"
    fi
}

# Function to show quick fixes
show_fixes() {
    echo -e "\n${BLUE}🔧 Quick fixes:${NC}"
    echo "   Start services:     docker-compose up -d"
    echo "   Restart services:   docker-compose restart"
    echo "   View logs:          docker-compose logs -f"
    echo "   Check status:       docker-compose ps"
    echo "   Clean up:           docker system prune"
    echo "   Full restart:       docker-compose down && docker-compose up -d"
}

# Function to run Python monitor
run_python_monitor() {
    echo -e "\n${BLUE}🐍 Running detailed Python monitor...${NC}"
    
    if [ -f "$PROJECT_DIR/tools/simple_monitor.py" ]; then
        cd "$PROJECT_DIR"
        python3 tools/simple_monitor.py --fixes
    else
        echo -e "${YELLOW}⚠️  Python monitor not found${NC}"
    fi
}

# Main health check function
run_health_check() {
    local overall_status=0
    
    # Check Docker
    if ! check_docker; then
        overall_status=1
    fi
    
    # Check containers
    if ! check_containers; then
        overall_status=1
    fi
    
    # Check APIs
    if ! check_apis; then
        overall_status=1
    fi
    
    # Check resources
    check_resources
    
    # Overall status
    echo -e "\n${BLUE}📊 Overall Status:${NC}"
    if [ $overall_status -eq 0 ]; then
        echo -e "${GREEN}✅ System is healthy${NC}"
    else
        echo -e "${RED}❌ Issues detected${NC}"
        show_fixes
    fi
    
    return $overall_status
}

# Parse command line arguments
case "${1:-health}" in
    "health"|"check"|"")
        run_health_check
        ;;
    "detailed"|"python")
        run_python_monitor
        ;;
    "watch")
        echo -e "${BLUE}👀 Starting continuous monitoring...${NC}"
        echo "Press Ctrl+C to stop"
        while true; do
            clear
            run_health_check
            echo -e "\n⏰ Next check in 30 seconds..."
            sleep 30
        done
        ;;
    "start")
        echo -e "${BLUE}🚀 Starting crypto-assistant services...${NC}"
        cd "$PROJECT_DIR"
        docker-compose up -d
        sleep 5
        run_health_check
        ;;
    "stop")
        echo -e "${BLUE}🛑 Stopping crypto-assistant services...${NC}"
        cd "$PROJECT_DIR"
        docker-compose down
        ;;
    "restart")
        echo -e "${BLUE}🔄 Restarting crypto-assistant services...${NC}"
        cd "$PROJECT_DIR"
        docker-compose restart
        sleep 5
        run_health_check
        ;;
    "logs")
        echo -e "${BLUE}📋 Showing recent logs...${NC}"
        cd "$PROJECT_DIR"
        docker-compose logs --tail=50
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  health, check    - Run health check (default)"
        echo "  detailed, python - Run detailed Python monitor"
        echo "  watch           - Continuous monitoring"
        echo "  start           - Start services and check health"
        echo "  stop            - Stop services"
        echo "  restart         - Restart services and check health"
        echo "  logs            - Show recent logs"
        echo "  help            - Show this help"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac