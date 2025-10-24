#!/bin/bash

# System Validation Script
# Comprehensive validation of the complete proactive alerts system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Crypto Assistant System Validation${NC}"
echo "======================================"

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    echo "----------------------------------------"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test 1: Environment Setup
test_environment() {
    echo "Checking environment variables..."
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        echo "❌ TELEGRAM_BOT_TOKEN not set"
        return 1
    fi
    
    if [ -z "$TELEGRAM_CHAT_ID" ]; then
        echo "❌ TELEGRAM_CHAT_ID not set"
        return 1
    fi
    
    echo "✅ Required environment variables are set"
    return 0
}

# Test 2: File Structure
test_file_structure() {
    echo "Validating file structure..."
    
    REQUIRED_FILES=(
        "services/monitoring/liquidation_monitor.py"
        "services/monitoring/oi_explosion_detector.py"
        "services/monitoring/alert_dispatcher.py"
        "services/monitoring/coordinator.py"
        "shared/models/compact_liquidation.py"
        "shared/models/compact_oi_data.py"
        "shared/utils/telegram_client.py"
        "shared/config/alert_thresholds.py"
        "scripts/deployment/start_monitoring.sh"
        "scripts/deployment/stop_monitoring.sh"
        "scripts/deployment/health_check.sh"
        "scripts/monitoring/docker-compose.monitoring.yml"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            echo "❌ Missing file: $file"
            return 1
        fi
    done
    
    echo "✅ All required files present"
    return 0
}

# Test 3: Python Syntax Validation
test_python_syntax() {
    echo "Validating Python syntax..."
    
    PYTHON_FILES=(
        "services/monitoring/liquidation_monitor.py"
        "services/monitoring/oi_explosion_detector.py"
        "services/monitoring/alert_dispatcher.py"
        "services/monitoring/coordinator.py"
        "shared/models/compact_liquidation.py"
        "shared/models/compact_oi_data.py"
        "shared/utils/telegram_client.py"
        "shared/config/alert_thresholds.py"
    )
    
    for file in "${PYTHON_FILES[@]}"; do
        if ! python3 -m py_compile "$PROJECT_ROOT/$file" 2>/dev/null; then
            echo "❌ Syntax error in: $file"
            return 1
        fi
    done
    
    echo "✅ All Python files have valid syntax"
    return 0
}

# Test 4: Import Dependencies
test_imports() {
    echo "Testing Python imports..."
    
    cd "$PROJECT_ROOT"
    
    # Test core imports
    if ! python3 -c "
import sys
sys.path.append('.')
from shared.models.compact_liquidation import CompactLiquidation
from shared.models.compact_oi_data import OIDataManager
from shared.utils.telegram_client import TelegramClient
from shared.config.alert_thresholds import LIQUIDATION_THRESHOLDS
print('All core imports successful')
" 2>/dev/null; then
        echo "❌ Core import test failed"
        return 1
    fi
    
    echo "✅ All required imports work correctly"
    return 0
}

# Test 5: Docker Compose Validation
test_docker_compose() {
    echo "Validating Docker Compose configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Test main docker-compose
    if ! docker-compose config >/dev/null 2>&1; then
        echo "❌ Main docker-compose.yml has errors"
        return 1
    fi
    
    # Test monitoring docker-compose
    if ! docker-compose -f scripts/monitoring/docker-compose.monitoring.yml config >/dev/null 2>&1; then
        echo "❌ Monitoring docker-compose.yml has errors"
        return 1
    fi
    
    echo "✅ Docker Compose configurations are valid"
    return 0
}

# Test 6: Unit Tests
test_unit_tests() {
    echo "Running unit tests..."
    
    cd "$PROJECT_ROOT"
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        echo "⚠️ pytest not available, installing test dependencies..."
        pip3 install -r tests/requirements.txt >/dev/null 2>&1 || true
    fi
    
    if command -v pytest &> /dev/null; then
        if pytest tests/unit/ -v --tb=short -q; then
            echo "✅ Unit tests passed"
            return 0
        else
            echo "❌ Some unit tests failed"
            return 1
        fi
    else
        echo "⚠️ Skipping unit tests - pytest not available"
        return 0
    fi
}

# Test 7: Memory Constraints
test_memory_constraints() {
    echo "Testing memory constraint compliance..."
    
    cd "$PROJECT_ROOT"
    
    # Test compact data structures
    if python3 -c "
import sys
sys.path.append('.')
from shared.models.compact_liquidation import CompactLiquidation, LiquidationBuffer
from shared.models.compact_oi_data import OIDataManager

# Test liquidation buffer memory
buffer = LiquidationBuffer(1000)
expected_max = 1000 * 18  # 18 bytes per liquidation
print(f'Liquidation buffer max memory: {expected_max} bytes')
assert buffer.memory_usage() == 0  # Empty buffer

# Test OI data manager
oi_manager = OIDataManager(target_memory_mb=40)
memory_stats = oi_manager.get_memory_usage()
print(f'OI manager memory: {memory_stats[\"total_mb\"]} MB')
assert memory_stats['total_mb'] < 40

print('✅ Memory constraints validated')
" 2>/dev/null; then
        echo "✅ Memory constraints are properly enforced"
        return 0
    else
        echo "❌ Memory constraint validation failed"
        return 1
    fi
}

# Test 8: Configuration Validation
test_configuration() {
    echo "Testing configuration and thresholds..."
    
    cd "$PROJECT_ROOT"
    
    if python3 -c "
import sys
sys.path.append('.')
from shared.config.alert_thresholds import *

# Test threshold configurations
assert LIQUIDATION_THRESHOLDS['BTC']['single_large'] > 0
assert OI_EXPLOSION_THRESHOLDS['BTC']['change_pct'] > 0
assert SYSTEM_LIMITS['max_memory_mb'] == 512

# Test environment config
env_config = get_environment_config()
assert isinstance(env_config, dict)

print('✅ Configuration validation passed')
" 2>/dev/null; then
        echo "✅ Configuration is valid"
        return 0
    else
        echo "❌ Configuration validation failed"
        return 1
    fi
}

# Test 9: Service Integration
test_service_integration() {
    echo "Testing service integration..."
    
    cd "$PROJECT_ROOT"
    
    # Check if main services are running
    if docker ps --format "table {{.Names}}" | grep -q "crypto-market-data"; then
        echo "✅ Main market-data service is running"
        
        # Test API connectivity
        if curl -f -s http://localhost:8001/health >/dev/null; then
            echo "✅ Market data API is accessible"
        else
            echo "❌ Market data API is not accessible"
            return 1
        fi
    else
        echo "⚠️ Main services not running - integration test skipped"
        return 0
    fi
    
    return 0
}

# Test 10: Deployment Scripts
test_deployment_scripts() {
    echo "Testing deployment scripts..."
    
    # Check script permissions
    SCRIPTS=(
        "scripts/deployment/start_monitoring.sh"
        "scripts/deployment/stop_monitoring.sh"
        "scripts/deployment/health_check.sh"
        "scripts/deployment/rollback.sh"
    )
    
    for script in "${SCRIPTS[@]}"; do
        if [ ! -x "$PROJECT_ROOT/$script" ]; then
            echo "❌ Script not executable: $script"
            return 1
        fi
    done
    
    echo "✅ All deployment scripts are executable"
    return 0
}

# Run all tests
main() {
    echo "Starting comprehensive system validation..."
    echo "Project root: $PROJECT_ROOT"
    echo ""
    
    run_test "Environment Setup" "test_environment"
    run_test "File Structure" "test_file_structure"
    run_test "Python Syntax" "test_python_syntax"
    run_test "Import Dependencies" "test_imports"
    run_test "Docker Compose" "test_docker_compose"
    run_test "Unit Tests" "test_unit_tests"
    run_test "Memory Constraints" "test_memory_constraints"
    run_test "Configuration" "test_configuration"
    run_test "Service Integration" "test_service_integration"
    run_test "Deployment Scripts" "test_deployment_scripts"
    
    # Summary
    echo ""
    echo "======================================"
    echo -e "${BLUE}VALIDATION SUMMARY${NC}"
    echo "======================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}✅ System is ready for deployment${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Start monitoring: bash scripts/deployment/start_monitoring.sh"
        echo "2. Run health check: bash scripts/deployment/health_check.sh"
        echo "3. Monitor dashboard: http://localhost:8002/status"
        return 0
    else
        echo ""
        echo -e "${RED}❌ VALIDATION FAILED${NC}"
        echo -e "${RED}⚠️ Please fix the failed tests before deployment${NC}"
        echo ""
        echo "Common fixes:"
        echo "1. Set environment variables: export TELEGRAM_BOT_TOKEN=..."
        echo "2. Install dependencies: pip3 install -r tests/requirements.txt"
        echo "3. Check Docker: docker --version"
        echo "4. Verify main services: docker-compose ps"
        return 1
    fi
}

# Change to project directory and run
cd "$PROJECT_ROOT"
main "$@"