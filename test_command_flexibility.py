#!/usr/bin/env python3
"""
Test Command Flexibility Script
Tests actual command flexibility with different symbols and timeframes
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any
from datetime import datetime

class CommandFlexibilityTester:
    def __init__(self, market_data_url: str = "http://localhost:8001"):
        self.market_data_url = market_data_url
        self.test_results = {}
        
    async def test_symbol_formats(self):
        """Test different symbol format handling"""
        test_symbols = [
            # Standard formats
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT',
            # Less common but valid
            'ATOM/USDT', 'FTM/USDT', 'AVAX/USDT', 'NEAR/USDT',
            # Different quote currencies (if supported)
            'BTC/BUSD', 'ETH/BTC',
            # Alternative formats (should be normalized)
            'BTC-USDT', 'ETH-USDT'
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for symbol in test_symbols:
                try:
                    # Test price endpoint
                    async with session.post(f"{self.market_data_url}/price", 
                                          json={'symbol': symbol}) as response:
                        if response.status == 200:
                            data = await response.json()
                            success = data.get('success', False)
                        else:
                            success = False
                            data = {'error': f'HTTP {response.status}'}
                        
                        results.append({
                            'symbol': symbol,
                            'endpoint': 'price',
                            'success': success,
                            'response': data
                        })
                except Exception as e:
                    results.append({
                        'symbol': symbol,
                        'endpoint': 'price',
                        'success': False,
                        'error': str(e)
                    })
        
        self.test_results['symbol_formats'] = results
        return results
    
    async def test_timeframe_support(self):
        """Test timeframe support across commands"""
        test_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        test_symbol = 'BTC/USDT'  # Use stable symbol
        
        endpoints_to_test = [
            'volume_spike',
            'cvd', 
            'comprehensive_analysis'
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints_to_test:
                endpoint_results = []
                
                for timeframe in test_timeframes:
                    try:
                        payload = {
                            'symbol': test_symbol,
                            'timeframe': timeframe
                        }
                        
                        async with session.post(f"{self.market_data_url}/{endpoint}", 
                                              json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                success = data.get('success', False)
                            else:
                                success = False
                                data = {'error': f'HTTP {response.status}'}
                            
                            endpoint_results.append({
                                'timeframe': timeframe,
                                'success': success,
                                'response_preview': {
                                    'success': data.get('success'),
                                    'has_data': 'data' in data,
                                    'error': data.get('error', 'None')[:100] if data.get('error') else None
                                }
                            })
                    except Exception as e:
                        endpoint_results.append({
                            'timeframe': timeframe,
                            'success': False,
                            'error': str(e)
                        })
                
                results[endpoint] = endpoint_results
        
        self.test_results['timeframe_support'] = results
        return results
    
    async def test_volume_scan_flexibility(self):
        """Test volume scan command with different parameters"""
        test_cases = [
            {'timeframe': '15m', 'min_spike': 200},
            {'timeframe': '1h', 'min_spike': 150},
            {'timeframe': '5m', 'min_spike': 300},
            {'timeframe': '4h', 'min_spike': 100},
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for case in test_cases:
                try:
                    async with session.post(f"{self.market_data_url}/volume_scan", 
                                          json=case) as response:
                        if response.status == 200:
                            data = await response.json()
                            success = data.get('success', False)
                            
                            # Extract useful info
                            response_info = {
                                'success': success,
                                'spikes_found': len(data.get('data', {}).get('spikes', [])) if success else 0,
                                'error': data.get('error')
                            }
                        else:
                            success = False
                            response_info = {'error': f'HTTP {response.status}'}
                        
                        results.append({
                            'test_case': case,
                            'success': success,
                            'response': response_info
                        })
                except Exception as e:
                    results.append({
                        'test_case': case,
                        'success': False,
                        'error': str(e)
                    })
        
        self.test_results['volume_scan_flexibility'] = results
        return results
    
    async def test_exotic_symbols(self):
        """Test less common cryptocurrency symbols"""
        exotic_symbols = [
            'ALGO/USDT', 'VET/USDT', 'CHZ/USDT', 'SAND/USDT', 'MANA/USDT',
            'ONE/USDT', 'THETA/USDT', 'XTZ/USDT', 'EOS/USDT', 'COMP/USDT'
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for symbol in exotic_symbols:
                try:
                    # Test comprehensive analysis (most complete test)
                    async with session.post(f"{self.market_data_url}/comprehensive_analysis", 
                                          json={'symbol': symbol, 'timeframe': '1h'}) as response:
                        if response.status == 200:
                            data = await response.json()
                            success = data.get('success', False)
                            
                            if success:
                                analysis_data = data.get('data', {})
                                response_info = {
                                    'has_price_data': 'price_data' in analysis_data,
                                    'has_volume_analysis': 'volume_analysis' in analysis_data,
                                    'has_cvd_analysis': 'cvd_analysis' in analysis_data,
                                    'has_technical_indicators': 'technical_indicators' in analysis_data,
                                }
                            else:
                                response_info = {'error': data.get('error')}
                        else:
                            success = False
                            response_info = {'error': f'HTTP {response.status}'}
                        
                        results.append({
                            'symbol': symbol,
                            'success': success,
                            'analysis_completeness': response_info
                        })
                except Exception as e:
                    results.append({
                        'symbol': symbol,
                        'success': False,
                        'error': str(e)
                    })
        
        self.test_results['exotic_symbols'] = results
        return results
    
    async def check_service_health(self):
        """Check if market data service is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.market_data_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'healthy': True, 'response': data}
                    else:
                        return {'healthy': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def run_all_tests(self):
        """Run comprehensive flexibility tests"""
        print("🧪 Testing Crypto Trading Bot Command Flexibility")
        print("=" * 55)
        
        # Check service health first
        print("🔍 Checking market data service health...")
        health = await self.check_service_health()
        
        if not health['healthy']:
            print(f"❌ Market data service not available: {health['error']}")
            print("💡 Start the service with: docker-compose up market-data")
            return self.test_results
        
        print("✅ Market data service is healthy")
        
        # Run tests
        test_functions = [
            ('Symbol Format Support', self.test_symbol_formats),
            ('Timeframe Support', self.test_timeframe_support),
            ('Volume Scan Flexibility', self.test_volume_scan_flexibility),
            ('Exotic Symbol Support', self.test_exotic_symbols),
        ]
        
        for test_name, test_func in test_functions:
            print(f"\n🔍 Running {test_name} tests...")
            try:
                await test_func()
                print(f"✅ {test_name} tests completed")
            except Exception as e:
                print(f"❌ {test_name} tests failed: {e}")
        
        return self.test_results
    
    def generate_flexibility_report(self):
        """Generate detailed flexibility report"""
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'service_url': self.market_data_url,
            'results': self.test_results,
            'summary': self._calculate_summary()
        }
        return report
    
    def _calculate_summary(self):
        """Calculate test summary statistics"""
        summary = {}
        
        # Symbol format tests
        if 'symbol_formats' in self.test_results:
            symbol_tests = self.test_results['symbol_formats']
            summary['symbol_format_tests'] = {
                'total': len(symbol_tests),
                'successful': len([t for t in symbol_tests if t['success']]),
                'failed': len([t for t in symbol_tests if not t['success']])
            }
        
        # Timeframe tests
        if 'timeframe_support' in self.test_results:
            timeframe_tests = self.test_results['timeframe_support']
            summary['timeframe_tests'] = {}
            
            for endpoint, tests in timeframe_tests.items():
                summary['timeframe_tests'][endpoint] = {
                    'total': len(tests),
                    'successful': len([t for t in tests if t['success']]),
                    'failed': len([t for t in tests if not t['success']])
                }
        
        # Volume scan tests
        if 'volume_scan_flexibility' in self.test_results:
            volscan_tests = self.test_results['volume_scan_flexibility']
            summary['volume_scan_tests'] = {
                'total': len(volscan_tests),
                'successful': len([t for t in volscan_tests if t['success']]),
                'failed': len([t for t in volscan_tests if not t['success']])
            }
        
        # Exotic symbol tests
        if 'exotic_symbols' in self.test_results:
            exotic_tests = self.test_results['exotic_symbols']
            summary['exotic_symbol_tests'] = {
                'total': len(exotic_tests),
                'successful': len([t for t in exotic_tests if t['success']]),
                'failed': len([t for t in exotic_tests if not t['success']])
            }
        
        return summary
    
    def print_flexibility_report(self, report):
        """Print formatted flexibility report"""
        print("\n🎯 COMMAND FLEXIBILITY TEST REPORT")
        print("=" * 45)
        
        summary = report['summary']
        
        # Symbol format results
        if 'symbol_format_tests' in summary:
            symbol_stats = summary['symbol_format_tests']
            print(f"\n📊 SYMBOL FORMAT SUPPORT:")
            print(f"  • Total Tested: {symbol_stats['total']}")
            print(f"  • Successful: {symbol_stats['successful']}")
            print(f"  • Failed: {symbol_stats['failed']}")
            print(f"  • Success Rate: {(symbol_stats['successful']/symbol_stats['total']*100):.1f}%")
        
        # Timeframe results  
        if 'timeframe_tests' in summary:
            print(f"\n⏰ TIMEFRAME SUPPORT:")
            for endpoint, stats in summary['timeframe_tests'].items():
                print(f"  {endpoint}:")
                print(f"    • Successful: {stats['successful']}/{stats['total']}")
                print(f"    • Success Rate: {(stats['successful']/stats['total']*100):.1f}%")
        
        # Volume scan results
        if 'volume_scan_tests' in summary:
            volscan_stats = summary['volume_scan_tests']
            print(f"\n🔍 VOLUME SCAN FLEXIBILITY:")
            print(f"  • Parameter Combinations Tested: {volscan_stats['total']}")
            print(f"  • Successful: {volscan_stats['successful']}")
            print(f"  • Success Rate: {(volscan_stats['successful']/volscan_stats['total']*100):.1f}%")
        
        # Exotic symbol results
        if 'exotic_symbol_tests' in summary:
            exotic_stats = summary['exotic_symbol_tests']
            print(f"\n🦄 EXOTIC SYMBOL SUPPORT:")
            print(f"  • Symbols Tested: {exotic_stats['total']}")
            print(f"  • Successful: {exotic_stats['successful']}")
            print(f"  • Success Rate: {(exotic_stats['successful']/exotic_stats['total']*100):.1f}%")
        
        # Overall assessment
        all_tests = [v for v in summary.values() if isinstance(v, dict) and 'successful' in v]
        if all_tests:
            total_success = sum(t['successful'] for t in all_tests)
            total_tests = sum(t['total'] for t in all_tests)
            overall_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
            
            print(f"\n🎯 OVERALL FLEXIBILITY SCORE: {overall_rate:.1f}%")
            
            if overall_rate >= 90:
                print("✅ Excellent flexibility - supports wide range of symbols and timeframes")
            elif overall_rate >= 75:
                print("🟡 Good flexibility - minor limitations in some areas")
            elif overall_rate >= 50:
                print("🟠 Moderate flexibility - several hardcoded limitations")
            else:
                print("🔴 Limited flexibility - significant hardcoded constraints")
        
        print(f"\n🕐 Report Generated: {report['test_timestamp']}")

async def main():
    """Main test execution"""
    tester = CommandFlexibilityTester()
    
    # Run all tests
    await tester.run_all_tests()
    
    # Generate and print report
    report = tester.generate_flexibility_report()
    tester.print_flexibility_report(report)
    
    # Save detailed results
    with open('command_flexibility_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: command_flexibility_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())