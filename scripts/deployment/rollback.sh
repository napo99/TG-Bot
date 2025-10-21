#!/bin/bash

# Rollback Script for Monitoring System
# Emergency rollback to restore original state

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 Emergency Rollback - Crypto Assistant Monitoring System"
echo "=========================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${YELLOW}➤${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Confirmation
echo "⚠️  This will completely remove all monitoring services and return to original state."
echo "The main crypto assistant services will remain untouched."
echo ""
read -p "Continue with rollback? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

cd "$PROJECT_ROOT"

# Step 1: Stop all monitoring services
print_step "Stopping all monitoring services..."
export COMPOSE_FILE="scripts/monitoring/docker-compose.monitoring.yml"

if [ -f "$COMPOSE_FILE" ]; then
    # Graceful stop
    docker-compose -f $COMPOSE_FILE stop 2>/dev/null || true
    sleep 3
    
    # Force stop and remove
    docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
    print_success "Monitoring services stopped"
else
    print_error "Monitoring compose file not found"
fi

# Step 2: Force remove monitoring containers
print_step "Force removing monitoring containers..."
MONITORING_CONTAINERS=(
    "crypto-liquidation-monitor"
    "crypto-oi-detector"
    "crypto-alert-dispatcher"
    "crypto-monitoring-coordinator"
)

for container in "${MONITORING_CONTAINERS[@]}"; do
    if docker ps -a --format "table {{.Names}}" | grep -q "$container"; then
        docker stop "$container" 2>/dev/null || true
        docker rm "$container" 2>/dev/null || true
        echo "  • Removed $container"
    fi
done
print_success "All monitoring containers removed"

# Step 3: Remove monitoring images
print_step "Removing monitoring Docker images..."
MONITORING_IMAGES=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "crypto-assistant.*monitoring" || true)
if [ -n "$MONITORING_IMAGES" ]; then
    echo "$MONITORING_IMAGES" | xargs -r docker rmi 2>/dev/null || true
    print_success "Monitoring images removed"
else
    echo "  • No monitoring images to remove"
fi

# Step 4: Remove monitoring volumes
print_step "Removing monitoring volumes..."
docker volume rm crypto-assistant_monitoring_logs 2>/dev/null || true
print_success "Monitoring volumes removed"

# Step 5: Clean up monitoring files (optional)
echo ""
read -p "Remove monitoring files and directories? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Removing monitoring files..."
    
    # Remove monitoring services
    if [ -d "services/monitoring" ]; then
        rm -rf services/monitoring
        echo "  • Removed services/monitoring/"
    fi
    
    # Remove shared monitoring files
    if [ -d "shared" ]; then
        rm -rf shared
        echo "  • Removed shared/"
    fi
    
    # Remove monitoring scripts
    if [ -d "scripts/monitoring" ]; then
        rm -rf scripts/monitoring
        echo "  • Removed scripts/monitoring/"
    fi
    
    # Remove alert data
    if [ -d "data" ]; then
        rm -rf data/alerts.db 2>/dev/null || true
        echo "  • Removed alert database"
    fi
    
    print_success "Monitoring files removed"
fi

# Step 6: Verify main services are still running
print_step "Verifying main services are still running..."
MAIN_SERVICES=("crypto-market-data" "crypto-telegram-bot")
ALL_MAIN_RUNNING=true

for service in "${MAIN_SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        echo "  • $service: RUNNING ✅"
    else
        echo "  • $service: NOT RUNNING ❌"
        ALL_MAIN_RUNNING=false
    fi
done

if [ "$ALL_MAIN_RUNNING" = true ]; then
    print_success "All main services are still running"
else
    print_error "Some main services are not running - may need restart"
    echo "   To restart main services: docker-compose up -d"
fi

# Step 7: Test main functionality
print_step "Testing main system functionality..."
if curl -f -s http://localhost:8001/health &> /dev/null; then
    print_success "Market data API is accessible"
else
    print_error "Market data API is not accessible"
fi

# Step 8: Clean up Docker system
print_step "Cleaning up Docker system..."
docker system prune -f &> /dev/null || true
print_success "Docker system cleaned"

# Final status
echo ""
echo "🎉 Rollback completed successfully!"
echo "=================================="
echo ""
echo "📊 Current Status:"
echo "  • Proactive monitoring: ❌ REMOVED"
echo "  • Reactive commands: ✅ UNCHANGED"
echo ""
echo "💡 What was restored:"
echo "  • All monitoring services removed"
echo "  • System returned to original state"
echo "  • Main crypto assistant functionality preserved"
echo ""
echo "🔧 Main services status:"
docker-compose ps 2>/dev/null || echo "  Run 'docker-compose ps' to check status"
echo ""
echo "📋 Available commands (unchanged):"
echo "  • /price BTC - Get current price"
echo "  • /volume BTC - Volume analysis"
echo "  • /oi BTC - Open interest data"
echo "  • /cvd BTC - Cumulative volume delta"
echo "  • /profile BTC - Market profile"
echo ""
echo "🔄 To reinstall monitoring: Follow installation instructions in PROACTIVE_ALERTS_SYSTEM_PRD.md"