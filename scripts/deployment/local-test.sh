#!/bin/bash
# Test deployment locally

echo "🧪 Testing local deployment..."

# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Test health endpoints
echo "Testing market-data health..."
curl -f http://localhost:8001/health || echo "❌ Market data health check failed"

echo "Testing telegram-bot health..."
curl -f http://localhost:8080/health || echo "❌ Telegram bot health check failed"

# Run tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

# Stop services
docker-compose down

echo "✅ Local deployment test complete"
