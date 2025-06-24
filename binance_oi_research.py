#!/usr/bin/env python3
"""
Binance Open Interest Research Script
====================================

This script researches Binance's Open Interest API endpoints to understand:
1. Available endpoints for futures OI data
2. Symbol formats for different margin types
3. Data structure and units returned
4. Proper API calls for BTC futures (USDT, USDC, inverse)

Target symbols to research:
- BTCUSDT (USDT-M futures - linear/stablecoin-margined)
- BTCUSDC (USDC-M futures - linear/stablecoin-margined) 
- BTCUSD_PERP (USD-M futures - inverse/coin-margined)

Expected validation targets:
- Binance USDT: ~78,278 BTC (~$7.9B)
- Binance USD: ~21,949 BTC (~$2.2B)  
- Binance USDC: ~6,377 BTC (~$0.6B)
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class BinanceOIResearcher:
    """Research Binance Open Interest API endpoints and data structure"""
    
    def __init__(self):
        # Binance API base URLs
        self.usdt_futures_base = "https://fapi.binance.com"  # USDT-M Futures
        self.usdc_futures_base = "https://dapi.binance.com"  # USDC-M and Coin-M Futures
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'BinanceOIResearcher/1.0',
            'Accept': 'application/json'
        }
        
        # Potential BTC symbols to test
        self.btc_symbols = {
            'usdt_linear': [
                'BTCUSDT',      # Most common USDT perpetual
                'BTCUSDT_PERP', # Alternative format
                'BTCUSDT-PERP'  # Another potential format
            ],
            'usdc_linear': [
                'BTCUSDC',      # USDC perpetual
                'BTCUSDC_PERP', # Alternative format
                'BTCUSDC-PERP'  # Another potential format
            ],
            'coin_margined': [
                'BTCUSD_PERP',  # Coin-margined perpetual
                'BTCUSD',       # Simple format
                'BTCUSD-PERP',  # Alternative format
                'BTCUSD_240628' # Example quarterly
            ]
        }
        
    def research_api_endpoints(self) -> Dict:
        """Research available OI endpoints on Binance"""
        
        print("🔍 Researching Binance Open Interest API Endpoints...")
        results = {
            'usdt_futures': {},
            'usdc_coin_futures': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # USDT-M Futures endpoints to test
        usdt_endpoints = {
            'openInterest': '/fapi/v1/openInterest',
            'openInterestHist': '/futures/data/openInterestHist',
            'globalLongShortAccountRatio': '/futures/data/globalLongShortAccountRatio',
            'topLongShortAccountRatio': '/futures/data/topLongShortAccountRatio',
            'topLongShortPositionRatio': '/futures/data/topLongShortPositionRatio'
        }
        
        # USDC-M/Coin-M Futures endpoints to test  
        dapi_endpoints = {
            'openInterest': '/dapi/v1/openInterest',
            'openInterestHist': '/futures/data/deliveryOpenInterestHist',
            'globalLongShortAccountRatio': '/futures/data/deliveryAccountRatio',
            'topLongShortAccountRatio': '/futures/data/deliveryTopLongShortAccountRatio',
            'topLongShortPositionRatio': '/futures/data/deliveryTopLongShortPositionRatio'
        }
        
        # Test USDT-M endpoints
        print("\n📊 Testing USDT-M Futures Endpoints...")
        for endpoint_name, endpoint_path in usdt_endpoints.items():
            results['usdt_futures'][endpoint_name] = self._test_endpoint(
                self.usdt_futures_base, endpoint_path, 'BTCUSDT'
            )
            
        # Test USDC-M/Coin-M endpoints
        print("\n📊 Testing USDC-M/Coin-M Futures Endpoints...")
        for endpoint_name, endpoint_path in dapi_endpoints.items():
            results['usdc_coin_futures'][endpoint_name] = self._test_endpoint(
                self.usdc_futures_base, endpoint_path, 'BTCUSD_PERP'
            )
            
        return results
    
    def _test_endpoint(self, base_url: str, endpoint: str, symbol: str) -> Dict:
        """Test a specific endpoint with a symbol"""
        
        url = f"{base_url}{endpoint}"
        params = {'symbol': symbol}
        
        try:
            print(f"  Testing: {url} with symbol={symbol}")
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            result = {
                'url': url,
                'params': params,
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
            
            if response.status_code == 200:
                data = response.json()
                result['data'] = data
                result['data_structure'] = self._analyze_data_structure(data)
                print(f"    ✅ Success: {len(str(data))} chars")
            else:
                result['error'] = response.text
                print(f"    ❌ Failed: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            result = {
                'url': url,
                'params': params,
                'success': False,
                'error': str(e)
            }
            print(f"    ❌ Exception: {str(e)}")
            
        return result
    
    def _analyze_data_structure(self, data) -> Dict:
        """Analyze the structure of returned data"""
        
        if isinstance(data, dict):
            return {
                'type': 'dict',
                'keys': list(data.keys()),
                'sample_values': {k: str(v)[:50] for k, v in list(data.items())[:3]}
            }
        elif isinstance(data, list):
            return {
                'type': 'list',
                'length': len(data),
                'first_item': self._analyze_data_structure(data[0]) if data else None
            }
        else:
            return {
                'type': type(data).__name__,
                'value': str(data)[:100]
            }
    
    def test_symbol_variations(self) -> Dict:
        """Test different BTC symbol variations across endpoints"""
        
        print("\n🧪 Testing BTC Symbol Variations...")
        results = {}
        
        # Test USDT symbols on USDT-M endpoint
        results['usdt_symbols'] = {}
        for symbol in self.btc_symbols['usdt_linear']:
            print(f"\n  Testing USDT symbol: {symbol}")
            results['usdt_symbols'][symbol] = self._test_endpoint(
                self.usdt_futures_base, '/fapi/v1/openInterest', symbol
            )
        
        # Test USDC symbols on USDC-M endpoint  
        results['usdc_symbols'] = {}
        for symbol in self.btc_symbols['usdc_linear']:
            print(f"\n  Testing USDC symbol: {symbol}")
            results['usdc_symbols'][symbol] = self._test_endpoint(
                self.usdc_futures_base, '/dapi/v1/openInterest', symbol
            )
            
        # Test coin-margined symbols on USDC-M/Coin-M endpoint
        results['coin_margined_symbols'] = {}
        for symbol in self.btc_symbols['coin_margined']:
            print(f"\n  Testing Coin-margined symbol: {symbol}")
            results['coin_margined_symbols'][symbol] = self._test_endpoint(
                self.usdc_futures_base, '/dapi/v1/openInterest', symbol
            )
            
        return results
    
    def get_exchange_info(self) -> Dict:
        """Get exchange info to understand available symbols"""
        
        print("\n📋 Getting Exchange Information...")
        results = {}
        
        # USDT-M Futures exchange info
        try:
            url = f"{self.usdt_futures_base}/fapi/v1/exchangeInfo"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Extract BTC symbols
                btc_symbols = [s for s in data.get('symbols', []) if 'BTC' in s.get('symbol', '')]
                results['usdt_futures'] = {
                    'total_symbols': len(data.get('symbols', [])),
                    'btc_symbols': [s['symbol'] for s in btc_symbols[:10]],  # First 10
                    'btc_symbols_count': len(btc_symbols)
                }
                print(f"  USDT-M: {len(btc_symbols)} BTC symbols found")
        except Exception as e:
            results['usdt_futures'] = {'error': str(e)}
            
        # USDC-M/Coin-M Futures exchange info
        try:
            url = f"{self.usdc_futures_base}/dapi/v1/exchangeInfo"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Extract BTC symbols
                btc_symbols = [s for s in data.get('symbols', []) if 'BTC' in s.get('symbol', '')]
                results['usdc_coin_futures'] = {
                    'total_symbols': len(data.get('symbols', [])),
                    'btc_symbols': [s['symbol'] for s in btc_symbols[:10]],  # First 10
                    'btc_symbols_count': len(btc_symbols)
                }
                print(f"  USDC-M/Coin-M: {len(btc_symbols)} BTC symbols found")
        except Exception as e:
            results['usdc_coin_futures'] = {'error': str(e)}
            
        return results
    
    def analyze_oi_data_units(self, oi_data: Dict) -> Dict:
        """Analyze OI data to understand units and calculations"""
        
        print("\n🔬 Analyzing Open Interest Data Units...")
        
        analysis = {
            'raw_data': oi_data,
            'interpretation': {},
            'unit_analysis': {},
            'calculations': {}
        }
        
        if 'openInterest' in oi_data:
            oi_value = oi_data['openInterest']
            
            # Try to interpret the value
            try:
                oi_float = float(oi_value)
                
                # Analyze magnitude to guess units
                if oi_float > 1_000_000:
                    analysis['unit_analysis']['likely_usd'] = f"${oi_float:,.0f}"
                    analysis['unit_analysis']['likely_btc_if_price_100k'] = f"{oi_float/100_000:.2f} BTC"
                    
                if oi_float < 100_000:
                    analysis['unit_analysis']['likely_btc'] = f"{oi_float:.2f} BTC"
                    analysis['unit_analysis']['likely_usd_if_btc_100k'] = f"${oi_float * 100_000:,.0f}"
                    
            except ValueError:
                analysis['unit_analysis']['error'] = f"Could not convert {oi_value} to float"
                
        return analysis
    
    def run_comprehensive_research(self) -> Dict:
        """Run comprehensive Binance OI research"""
        
        print("🚀 Starting Comprehensive Binance Open Interest Research")
        print("=" * 60)
        
        research_results = {
            'timestamp': datetime.now().isoformat(),
            'exchange_info': {},
            'api_endpoints': {},
            'symbol_variations': {},
            'data_analysis': {},
            'recommendations': []
        }
        
        # Step 1: Get exchange info
        research_results['exchange_info'] = self.get_exchange_info()
        
        # Step 2: Test API endpoints
        research_results['api_endpoints'] = self.research_api_endpoints()
        
        # Step 3: Test symbol variations
        research_results['symbol_variations'] = self.test_symbol_variations()
        
        # Step 4: Analyze successful data
        successful_results = []
        for category in research_results['api_endpoints'].values():
            for endpoint_name, result in category.items():
                if result.get('success') and 'data' in result:
                    successful_results.append((endpoint_name, result['data']))
                    
        if successful_results:
            research_results['data_analysis'] = {}
            for name, data in successful_results[:3]:  # Analyze first 3 successful results
                research_results['data_analysis'][name] = self.analyze_oi_data_units(data)
        
        # Step 5: Generate recommendations
        research_results['recommendations'] = self._generate_recommendations(research_results)
        
        return research_results
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate implementation recommendations based on research"""
        
        recommendations = []
        
        # Check which endpoints worked
        working_endpoints = []
        for category, endpoints in results['api_endpoints'].items():
            for name, result in endpoints.items():
                if result.get('success'):
                    working_endpoints.append(f"{category}.{name}")
                    
        if working_endpoints:
            recommendations.append(f"✅ Working endpoints found: {', '.join(working_endpoints)}")
        else:
            recommendations.append("❌ No working endpoints found - may need authentication or different approach")
            
        # Check symbol variations
        working_symbols = []
        for category, symbols in results['symbol_variations'].items():
            for symbol, result in symbols.items():
                if result.get('success'):
                    working_symbols.append(f"{symbol} ({category})")
                    
        if working_symbols:
            recommendations.append(f"✅ Working symbols: {', '.join(working_symbols)}")
            
        # Data structure recommendations
        if 'data_analysis' in results and results['data_analysis']:
            recommendations.append("✅ Data analysis completed - check unit interpretations")
            
        return recommendations

def main():
    """Main execution function"""
    
    researcher = BinanceOIResearcher()
    results = researcher.run_comprehensive_research()
    
    # Save results to file
    output_file = f"binance_oi_research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Print summary
    print("\n📋 RESEARCH SUMMARY")
    print("=" * 40)
    
    for rec in results['recommendations']:
        print(f"  {rec}")
    
    print(f"\n🔍 Total endpoints tested: {len([r for category in results['api_endpoints'].values() for r in category])}")
    print(f"🔍 Total symbols tested: {len([r for category in results['symbol_variations'].values() for r in category])}")
    
    return results

if __name__ == "__main__":
    results = main()