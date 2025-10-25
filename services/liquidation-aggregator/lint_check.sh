#!/bin/bash

# LIQUIDATION AGGREGATOR - CODE QUALITY CHECK
# Runs basic linting and formatting checks

echo "=================================="
echo "🔍 LIQUIDATION AGGREGATOR - LINT CHECK"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"
echo ""

# Check for syntax errors
echo "──────────────────────────────────"
echo "📝 Checking Python syntax..."
echo "──────────────────────────────────"

FILES=(
    "main.py"
    "core_engine.py"
    "exchanges.py"
    "visual_monitor.py"
    "simple_dashboard.py"
    "check_data.py"
    "test_system.py"
)

SYNTAX_ERRORS=0

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $file"
        else
            echo -e "${RED}✗${NC} $file - Syntax error!"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        fi
    else
        echo -e "${YELLOW}⚠${NC} $file - Not found"
    fi
done

echo ""

# Check for common issues
echo "──────────────────────────────────"
echo "🔍 Checking for common issues..."
echo "──────────────────────────────────"

# Check for print statements (should use logging)
PRINT_COUNT=$(grep -r "print(" *.py 2>/dev/null | grep -v "test_" | grep -v "check_data" | grep -v "visual_monitor" | grep -v "simple_dashboard" | wc -l | tr -d ' ')

if [ "$PRINT_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Found $PRINT_COUNT print() statements in core files (consider using logging)"
else
    echo -e "${GREEN}✓${NC} No print() in core files"
fi

# Check for hardcoded credentials
CRED_CHECK=$(grep -rE "(password|api_key|secret|token)\s*=\s*['\"][^'\"]+" *.py 2>/dev/null | grep -v "test_" | wc -l | tr -d ' ')

if [ "$CRED_CHECK" -gt 0 ]; then
    echo -e "${RED}✗${NC} Found $CRED_CHECK potential hardcoded credentials!"
else
    echo -e "${GREEN}✓${NC} No hardcoded credentials found"
fi

# Check for TODO/FIXME comments
TODO_COUNT=$(grep -rE "(TODO|FIXME)" *.py 2>/dev/null | wc -l | tr -d ' ')

if [ "$TODO_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Found $TODO_COUNT TODO/FIXME comments"
else
    echo -e "${GREEN}✓${NC} No TODO/FIXME comments"
fi

# Check for proper error handling
echo ""
echo "──────────────────────────────────"
echo "🛡️  Checking error handling..."
echo "──────────────────────────────────"

# Count try/except blocks
TRY_COUNT=$(grep -r "try:" *.py 2>/dev/null | grep -v "test_" | wc -l | tr -d ' ')
echo -e "${GREEN}✓${NC} Found $TRY_COUNT try/except blocks"

# Check for bare except
BARE_EXCEPT=$(grep -rE "except\s*:" *.py 2>/dev/null | grep -v "test_" | wc -l | tr -d ' ')

if [ "$BARE_EXCEPT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Found $BARE_EXCEPT bare except: statements (consider specifying exception types)"
else
    echo -e "${GREEN}✓${NC} No bare except: statements"
fi

# Summary
echo ""
echo "=================================="
echo "📊 LINT CHECK SUMMARY"
echo "=================================="

if [ "$SYNTAX_ERRORS" -eq 0 ] && [ "$CRED_CHECK" -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CRITICAL CHECKS PASSED${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ FAILED: $SYNTAX_ERRORS syntax errors, $CRED_CHECK credential issues${NC}"
    echo ""
    exit 1
fi
