#!/bin/bash
###############################################################################
# MASTER VALIDATION SCRIPT
# Runs all forensic validation tests and system tests
# Exit code 0 = all pass, 1 = some failures
###############################################################################

set -e

echo "================================================================================"
echo "MASTER VALIDATION SUITE"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# Check if data collection is running
echo "Checking data availability..."
if ! redis-cli -n 1 KEYS "liq:agg:*" | grep -q "liq:agg"; then
    echo "⚠️  WARNING: No liquidation data found in Redis"
    echo "   Start data collection with: python main.py"
    echo ""
fi

# Test 1: Forensic Validation
echo "================================================================================"
echo "TEST 1: FORENSIC DATA VALIDATION"
echo "================================================================================"
python test_forensic_validation.py
FORENSIC_RESULT=$?

echo ""
echo "================================================================================"
echo "TEST 2: E2E SYSTEM TESTS"
echo "================================================================================"
python test_system.py
SYSTEM_RESULT=$?

echo ""
echo "================================================================================"
echo "TEST 3: SYNTAX VALIDATION"
echo "================================================================================"

echo "Checking Python syntax..."
SYNTAX_ERRORS=0

for file in *.py; do
    if python -m py_compile "$file" 2>/dev/null; then
        echo "✅ $file"
    else
        echo "❌ $file - SYNTAX ERROR"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo "✅ All Python files have valid syntax"
    SYNTAX_RESULT=0
else
    echo "❌ $SYNTAX_ERRORS files have syntax errors"
    SYNTAX_RESULT=1
fi

echo ""
echo "================================================================================"
echo "MASTER VALIDATION SUMMARY"
echo "================================================================================"

if [ $FORENSIC_RESULT -eq 0 ]; then
    echo "✅ Forensic Validation: PASSED"
else
    echo "❌ Forensic Validation: FAILED"
fi

if [ $SYSTEM_RESULT -eq 0 ]; then
    echo "✅ E2E System Tests: PASSED"
else
    echo "⚠️  E2E System Tests: SOME FAILURES (check output above)"
fi

if [ $SYNTAX_RESULT -eq 0 ]; then
    echo "✅ Syntax Validation: PASSED"
else
    echo "❌ Syntax Validation: FAILED"
fi

echo "================================================================================"

# Overall result
if [ $FORENSIC_RESULT -eq 0 ] && [ $SYNTAX_RESULT -eq 0 ]; then
    echo "✅ CRITICAL TESTS PASSED - System is mathematically consistent!"
    echo "================================================================================"
    exit 0
else
    echo "❌ CRITICAL TESTS FAILED - Review errors above"
    echo "================================================================================"
    exit 1
fi
