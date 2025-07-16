#!/bin/bash
# Phase 1 Comprehensive Validation Script

set -e  # Exit on any error

echo "🧪 PHASE 1: COMPREHENSIVE VALIDATION"
echo "===================================="

# Navigate to project directory
cd /Users/screener-m3/projects/crypto-assistant

echo "📁 Verifying working provider files exist..."
if [[ -f "services/market-data/gateio_oi_provider_working.py" ]]; then
    echo "✅ gateio_oi_provider_working.py exists"
else
    echo "❌ gateio_oi_provider_working.py missing"
    exit 1
fi

if [[ -f "services/market-data/bitget_oi_provider_working.py" ]]; then
    echo "✅ bitget_oi_provider_working.py exists"
else
    echo "❌ bitget_oi_provider_working.py missing"
    exit 1
fi
echo ""

echo "🔍 Testing import validation..."
cd services/market-data
python3 test_imports.py
cd ../..
echo ""

echo "🧪 Testing OI endpoint..."
curl -X POST http://localhost:8001/multi_oi \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USDT"}' \
  --max-time 30 \
  --fail-with-body || echo "❌ OI endpoint test failed"
echo ""

echo "🧪 Testing price endpoint (regression test)..."
curl -X POST http://localhost:8001/combined_price \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC-USDT"}' \
  --max-time 30 \
  --fail-with-body || echo "❌ Price endpoint test failed"
echo ""

echo "📊 Docker container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "📋 Service logs (last 10 lines):"
echo "Market-data logs:"
docker logs crypto-market-data --tail 10
echo ""

echo "🎯 PHASE 1 VALIDATION COMPLETE!"
echo "If all tests passed, the OI import fix is working correctly."