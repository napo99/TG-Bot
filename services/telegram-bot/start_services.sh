#!/bin/bash

# Service Startup Script for AWS Deployment
# This script should be run on the EC2 instance

set -e

echo "=== Starting Crypto Assistant Services ==="
echo "Timestamp: $(date)"
echo ""

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    echo "This script should be run with sudo"
    echo "Usage: sudo ./start_services.sh"
    exit 1
fi

# Navigate to project directory
PROJECT_DIR="/home/ec2-user/crypto-assistant"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"
echo "Working directory: $(pwd)"
echo ""

# Check Docker installation
echo "Checking Docker installation..."
docker --version || {
    echo "❌ Docker not installed"
    exit 1
}

docker-compose --version || {
    echo "❌ Docker Compose not installed"
    exit 1
}

# Check Docker service status
echo "Checking Docker service..."
systemctl status docker --no-pager || {
    echo "Starting Docker service..."
    systemctl start docker
    systemctl enable docker
}
echo ""

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down --remove-orphans
echo ""

# Pull latest images (if needed)
echo "Building/pulling Docker images..."
docker-compose build --no-cache
echo ""

# Start services
echo "Starting services..."
docker-compose up -d
echo ""

# Wait for services to start
echo "Waiting for services to start..."
sleep 15

# Check service status
echo "Checking service status..."
docker-compose ps
echo ""

# Check logs
echo "Recent logs:"
echo "--- Market Data Service ---"
docker-compose logs --tail=20 market-data
echo ""
echo "--- Telegram Bot Service ---"
docker-compose logs --tail=20 telegram-bot
echo ""

# Check port bindings
echo "Checking port bindings..."
netstat -tlnp | grep -E "(8080|8001)" || echo "No services found on ports 8080/8001"
echo ""

# Test health endpoints
echo "Testing health endpoints..."
sleep 5

echo "Testing Market Data Service (port 8001)..."
curl -f http://localhost:8001/health || echo "❌ Market Data Service health check failed"

echo "Testing Telegram Bot Service (port 8080)..."
curl -f http://localhost:8080/health || echo "❌ Telegram Bot Service health check failed"

echo ""
echo "=== Service startup completed ==="
echo "Check the output above for any errors"
echo ""
echo "To check service status: docker-compose ps"
echo "To view logs: docker-compose logs -f [service-name]"
echo "To stop services: docker-compose down"