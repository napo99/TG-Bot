#!/bin/bash

# Test Market Data API endpoints
echo "Testing Market Data API Endpoints"
echo "================================="

echo "1. Health Check:"
curl -s http://localhost:8001/health | jq . || echo "Health check failed"

echo -e "\n2. Price Data:"
curl -s -X POST http://localhost:8001/price -H "Content-Type: application/json" -d '{"symbol": "BTC-USDT"}' | jq . || echo "Price check failed"

echo -e "\n3. Comprehensive Analysis:"
curl -s -X POST http://localhost:8001/comprehensive_analysis -H "Content-Type: application/json" -d '{"symbol": "BTC-USDT", "timeframe": "15m"}' | jq . || echo "Comprehensive analysis failed"

echo -e "\n4. Multi-Exchange OI:"
curl -s -X POST http://localhost:8001/multi_oi -H "Content-Type: application/json" -d '{"symbol": "BTC-USDT"}' | jq . || echo "Multi-OI failed"

echo -e "\n5. Volume Scan:"
curl -s -X POST http://localhost:8001/volume_scan -H "Content-Type: application/json" -d '{"symbol": "BTC-USDT"}' | jq . || echo "Volume scan failed"

echo -e "\nTesting complete!"