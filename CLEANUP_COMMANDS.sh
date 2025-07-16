#!/bin/bash
# 🧹 SYSTEMATIC CLEANUP - PHASE 3
# Remove pollution files and prepare clean deployment

echo "🧹 PHASE 3: CLEANING LOCAL ENVIRONMENT"
echo "======================================"
echo ""

echo "📂 Step 1: Removing pollution files..."

# Remove emergency/debug files
echo "Removing emergency and debug files..."
rm -f emergency_*.py
rm -f simple_aws_test.py
rm -f test_aws_production.py
rm -f aws_diagnostics.py

# Remove research files
echo "Removing research files..."
rm -f binance_oi_research.py
rm -f bybit_oi_research.py
rm -f vwap_analysis.py
rm -f vwap_period_comparison.py

# Remove analysis and validation files
echo "Removing analysis files..."
rm -f validation_framework.py
rm -f evidence_requirements.py
rm -f monitoring_setup.py
rm -f network_diagnosis.py

# Remove temporary files
echo "Removing temporary files..."
rm -f check_*.py
rm -f verify_*.py
rm -f simulate_*.py

# Remove staging compose files (pollution)
echo "Removing staging pollution..."
rm -f docker-compose.staging*.yml

echo ""
echo "📋 Step 2: Checking git status..."
git status

echo ""
echo "✅ PHASE 3 COMPLETE - Local environment cleaned"
echo ""
echo "🔄 Next: Execute PHASE 4 local validation..."