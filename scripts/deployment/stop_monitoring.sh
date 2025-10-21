#!/bin/bash

# Stop Monitoring Services Script
# Cleanly stops all proactive alert monitoring services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🛑 Stopping Crypto Assistant Monitoring System"
echo "============================================="

cd "$PROJECT_ROOT"

# Use the monitoring docker-compose file
export COMPOSE_FILE="scripts/monitoring/docker-compose.monitoring.yml"

# Check if services are running
echo "🔍 Checking running monitoring services..."
MONITORING_SERVICES=(
    "crypto-liquidation-monitor"
    "crypto-oi-detector"
    "crypto-alert-dispatcher" 
    "crypto-monitoring-coordinator"
)

RUNNING_SERVICES=()
for service in "${MONITORING_SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        RUNNING_SERVICES+=("$service")
        echo "📍 Found running: $service"
    fi
done

if [ ${#RUNNING_SERVICES[@]} -eq 0 ]; then
    echo "ℹ️  No monitoring services are currently running"
    exit 0
fi

# Graceful shutdown
echo "🔄 Gracefully stopping monitoring services..."
docker-compose -f $COMPOSE_FILE stop

# Wait for graceful shutdown
echo "⏳ Waiting for services to stop..."
sleep 5

# Remove containers
echo "🗑️  Removing monitoring containers..."
docker-compose -f $COMPOSE_FILE down

# Verify all services are stopped
echo "✅ Verifying services are stopped..."
STILL_RUNNING=()
for service in "${MONITORING_SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        STILL_RUNNING+=("$service")
    fi
done

if [ ${#STILL_RUNNING[@]} -gt 0 ]; then
    echo "⚠️  Some services are still running. Force stopping..."
    for service in "${STILL_RUNNING[@]}"; do
        echo "🔨 Force stopping $service"
        docker stop "$service" || true
        docker rm "$service" || true
    done
fi

# Clean up monitoring logs volume (optional)
read -p "🗂️  Remove monitoring logs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removing monitoring logs..."
    docker volume rm crypto-assistant_monitoring_logs 2>/dev/null || true
fi

# Verify main services are still running
echo "🔍 Verifying main services are still running..."
MAIN_SERVICES=("crypto-market-data" "crypto-telegram-bot")
for service in "${MAIN_SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        echo "✅ $service is still running (good)"
    else
        echo "⚠️  $service is not running (main service may need restart)"
    fi
done

echo ""
echo "🎉 Monitoring system stopped successfully!"
echo ""
echo "📊 System Status:"
echo "  • Proactive monitoring: ❌ STOPPED"
echo "  • Reactive commands: ✅ RUNNING (unchanged)"
echo ""
echo "🔄 To restart monitoring: bash $SCRIPT_DIR/start_monitoring.sh"
echo "🔍 Check main services: docker-compose ps"