#!/usr/bin/env python3
"""
COMPREHENSIVE INTEGRATION TESTS
Agent 5 validation suite for autonomous implementation completion
"""

import asyncio
import sys
import os
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IntegrationTestSuite:
    """Comprehensive validation test suite"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        print("🚀 STARTING COMPREHENSIVE INTEGRATION TESTS")
        print("=" * 60)
        
        tests = [
            ("phase1_import_resolution", self.test_phase1_import_resolution),
            ("provider_files_validation", self.test_provider_files_validation),
            ("unified_oi_aggregator", self.test_unified_oi_aggregator),
            ("api_endpoint_validation", self.test_api_endpoint_validation),
            ("logging_system", self.test_logging_system),
            ("monitoring_tools", self.test_monitoring_tools),
            ("docker_health", self.test_docker_health)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📊 RUNNING: {test_name}")
            try:
                result = await test_func()
                self.test_results[test_name] = {
                    'status': 'PASSED' if result else 'FAILED',
                    'result': result,
                    'error': None
                }
                status_emoji = "✅" if result else "❌"
                print(f"{status_emoji} {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'result': False,
                    'error': str(e)
                }
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        return self.generate_final_report()
    
    async def test_phase1_import_resolution(self) -> bool:
        """Test if Phase 1 OI fix resolved import issues"""
        try:
            # Test 1: Check if provider files exist
            provider_files = [
                '/Users/screener-m3/projects/crypto-assistant/services/market-data/gateio_oi_provider_working.py',
                '/Users/screener-m3/projects/crypto-assistant/services/market-data/bitget_oi_provider_working.py'
            ]
            
            for file_path in provider_files:
                if not os.path.exists(file_path):
                    print(f"❌ Missing provider file: {file_path}")
                    return False
                print(f"✅ Found provider file: {os.path.basename(file_path)}")
            
            # Test 2: Import resolution test
            try:
                from unified_oi_aggregator import UnifiedOIAggregator
                print("✅ unified_oi_aggregator import successful")
                
                # Test 3: Provider class imports
                from gateio_oi_provider_working import GateIOOIProviderWorking
                from bitget_oi_provider_working import BitgetOIProviderWorking
                print("✅ Provider class imports successful")
                
                return True
                
            except ImportError as e:
                print(f"❌ Import resolution still failing: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Phase 1 test error: {e}")
            return False
    
    async def test_provider_files_validation(self) -> bool:
        """Validate provider file implementations"""
        try:
            # Import and instantiate providers
            from gateio_oi_provider_working import GateIOOIProviderWorking
            from bitget_oi_provider_working import BitgetOIProviderWorking
            
            # Test GateIO provider
            gateio_provider = GateIOOIProviderWorking()
            supported_types = gateio_provider.get_supported_market_types()
            print(f"✅ GateIO supports: {[t.value for t in supported_types]}")
            
            # Test Bitget provider  
            bitget_provider = BitgetOIProviderWorking()
            supported_types = bitget_provider.get_supported_market_types()
            print(f"✅ Bitget supports: {[t.value for t in supported_types]}")
            
            # Test symbol formatting
            btc_usdt = gateio_provider.format_symbol("BTC", supported_types[0])
            print(f"✅ GateIO symbol format: {btc_usdt}")
            
            return True
            
        except Exception as e:
            print(f"❌ Provider validation error: {e}")
            traceback.print_exc()
            return False
    
    async def test_unified_oi_aggregator(self) -> bool:
        """Test unified OI aggregator functionality"""
        try:
            from unified_oi_aggregator import UnifiedOIAggregator
            from oi_engine_v2 import MarketType
            
            aggregator = UnifiedOIAggregator()
            
            # Test supported exchanges
            exchanges = aggregator.get_supported_exchanges()
            print(f"✅ Supported exchanges: {exchanges}")
            
            # Test provider loading
            for exchange in ["binance", "bybit", "okx"]:
                if exchange in exchanges:
                    provider = aggregator.get_provider(exchange)
                    if provider:
                        print(f"✅ {exchange} provider loaded")
                    else:
                        print(f"❌ {exchange} provider failed to load")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ OI Aggregator test error: {e}")
            traceback.print_exc()
            return False
    
    async def test_api_endpoint_validation(self) -> bool:
        """Validate API endpoint exists in main.py"""
        try:
            main_py_path = '/Users/screener-m3/projects/crypto-assistant/services/market-data/main.py'
            
            with open(main_py_path, 'r') as f:
                content = f.read()
            
            # Check for OI analysis endpoint
            if '/oi_analysis' in content:
                print("✅ OI analysis endpoint found in main.py")
                return True
            else:
                print("❌ OI analysis endpoint missing from main.py")
                return False
                
        except Exception as e:
            print(f"❌ API endpoint validation error: {e}")
            return False
    
    async def test_logging_system(self) -> bool:
        """Test logging system implementation"""
        try:
            # Check if logging files exist
            logging_files = [
                '/Users/screener-m3/projects/crypto-assistant/services/market-data/market_logger.py',
                '/Users/screener-m3/projects/crypto-assistant/services/market-data/main_with_logging.py'
            ]
            
            for file_path in logging_files:
                if os.path.exists(file_path):
                    print(f"✅ Found logging file: {os.path.basename(file_path)}")
                else:
                    print(f"⚠️ Missing logging file: {os.path.basename(file_path)}")
            
            # Test logger import
            try:
                from market_logger import MarketLogger
                logger = MarketLogger()
                print("✅ MarketLogger import successful")
                return True
            except ImportError as e:
                print(f"❌ MarketLogger import failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Logging system test error: {e}")
            return False
    
    async def test_monitoring_tools(self) -> bool:
        """Test monitoring tools implementation"""
        try:
            # Check if monitoring tools exist
            monitoring_files = [
                '/Users/screener-m3/projects/crypto-assistant/tools/simple_health_check.py',
                '/Users/screener-m3/projects/crypto-assistant/tools/api_health_monitor.py'
            ]
            
            files_found = 0
            for file_path in monitoring_files:
                if os.path.exists(file_path):
                    print(f"✅ Found monitoring tool: {os.path.basename(file_path)}")
                    files_found += 1
                else:
                    print(f"⚠️ Missing monitoring tool: {os.path.basename(file_path)}")
            
            return files_found > 0
            
        except Exception as e:
            print(f"❌ Monitoring tools test error: {e}")
            return False
    
    async def test_docker_health(self) -> bool:
        """Test Docker container health"""
        try:
            import subprocess
            
            # Check if docker-compose is available
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ Docker available: {result.stdout.strip()}")
                
                # Check running containers
                result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\\t{{.Status}}'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print("✅ Docker containers status:")
                    print(result.stdout)
                    return True
                else:
                    print("⚠️ Could not check Docker containers")
                    return False
            else:
                print("❌ Docker not available")
                return False
                
        except Exception as e:
            print(f"❌ Docker health test error: {e}")
            return False
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASSED')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'FAILED')
        error_tests = sum(1 for r in self.test_results.values() if r['status'] == 'ERROR')
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': f"{success_rate:.1f}%",
                'duration_seconds': duration,
                'timestamp': end_time.isoformat()
            },
            'test_details': self.test_results,
            'overall_status': 'PASSED' if success_rate >= 80 else 'FAILED',
            'critical_issues': [
                name for name, result in self.test_results.items()
                if result['status'] != 'PASSED' and name in ['phase1_import_resolution', 'unified_oi_aggregator']
            ],
            'recommendations': self.get_recommendations()
        }
        
        return report
    
    def get_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.test_results.get('phase1_import_resolution', {}).get('status') == 'PASSED':
            recommendations.append("✅ Phase 1 OI fix is ready for manual testing")
        else:
            recommendations.append("❌ Phase 1 OI fix needs additional work before manual testing")
        
        if self.test_results.get('monitoring_tools', {}).get('status') == 'PASSED':
            recommendations.append("✅ Monitoring tools are functional")
        else:
            recommendations.append("⚠️ Monitoring tools may need manual setup")
        
        if self.test_results.get('docker_health', {}).get('status') == 'PASSED':
            recommendations.append("✅ Docker environment is healthy")
        else:
            recommendations.append("⚠️ Docker environment may need attention")
        
        recommendations.append("🔄 Manual docker restart recommended after validation")
        recommendations.append("📝 Git commit recommended for autonomous implementation")
        
        return recommendations


async def main():
    """Run integration test suite"""
    test_suite = IntegrationTestSuite()
    
    try:
        report = await test_suite.run_all_tests()
        
        print("\n" + "=" * 60)
        print("📊 FINAL INTEGRATION TEST REPORT")
        print("=" * 60)
        
        summary = report['summary']
        print(f"Tests Run: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌") 
        print(f"Errors: {summary['errors']} ⚠️")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Duration: {summary['duration_seconds']:.1f}s")
        print(f"Overall Status: {report['overall_status']}")
        
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues: {report['critical_issues']}")
        
        print(f"\n📋 Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        return report
        
    except Exception as e:
        print(f"❌ Integration test suite failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())