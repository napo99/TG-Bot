#!/bin/bash

# Start Monitoring Services Script
# Starts all proactive alert monitoring services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Starting Crypto Assistant Proactive Monitoring System"
echo "=================================================="

# Check if main services are running
echo "📋 Checking existing services..."
if ! docker ps --format "table {{.Names}}" | grep -q "crypto-market-data"; then
    echo "❌ Main market-data service not running. Please start main services first:"
    echo "   cd $PROJECT_ROOT && docker-compose up -d"
    exit 1
fi

if ! docker ps --format "table {{.Names}}" | grep -q "crypto-telegram-bot"; then
    echo "❌ Main telegram-bot service not running. Please start main services first:"
    echo "   cd $PROJECT_ROOT && docker-compose up -d"
    exit 1
fi

echo "✅ Main services are running"

# Check environment variables
echo "🔧 Checking environment variables..."
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ TELEGRAM_CHAT_ID not set"
    exit 1
fi

echo "✅ Required environment variables are set"

# Create required directories
echo "📁 Creating required directories..."
mkdir -p "$PROJECT_ROOT/shared/alerts"
mkdir -p "$PROJECT_ROOT/data"
chmod 755 "$PROJECT_ROOT/shared/alerts"
chmod 755 "$PROJECT_ROOT/data"

# Check if monitoring services are already running
echo "🔍 Checking if monitoring services are already running..."
if docker ps --format "table {{.Names}}" | grep -q "crypto-.*-monitor\|crypto-.*-detector\|crypto-.*-dispatcher"; then
    echo "⚠️  Monitoring services appear to be running. Stopping them first..."
    bash "$SCRIPT_DIR/stop_monitoring.sh"
    sleep 3
fi

# Start monitoring services
echo "🚀 Starting monitoring services..."
cd "$PROJECT_ROOT"

# Use the monitoring docker-compose file
export COMPOSE_FILE="scripts/monitoring/docker-compose.monitoring.yml"

# Start all monitoring services
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
SERVICES=(
    "crypto-liquidation-monitor"
    "crypto-oi-detector" 
    "crypto-alert-dispatcher"
    "crypto-monitoring-coordinator"
)

ALL_HEALTHY=true
for service in "${SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running properly"
        ALL_HEALTHY=false
    fi
done

if [ "$ALL_HEALTHY" = true ]; then
    echo ""
    echo "🎉 All monitoring services started successfully!"
    echo ""
    echo "📊 Monitoring Dashboard: http://localhost:8002/status"
    echo "🏥 Health Check: http://localhost:8002/health" 
    echo "📈 Metrics: http://localhost:8002/metrics"
    echo ""
    echo "Services running:"
    echo "  • Liquidation Monitor: Real-time liquidation cascade detection"
    echo "  • OI Explosion Detector: Open interest surge monitoring"
    echo "  • Alert Dispatcher: Telegram notification system"
    echo "  • Monitoring Coordinator: Health monitoring and coordination"
    echo ""
    echo "🔗 View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "🛑 Stop services: bash $SCRIPT_DIR/stop_monitoring.sh"
else
    echo ""
    echo "❌ Some services failed to start properly"
    echo "📋 Check logs: docker-compose -f $COMPOSE_FILE logs"
    echo "🔄 Retry: bash $SCRIPT_DIR/start_monitoring.sh"
    exit 1
fi