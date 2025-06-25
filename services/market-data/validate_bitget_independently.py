#!/usr/bin/env python3
"""
BITGET INDEPENDENT VALIDATION AGENT
Critical mission: Analyze and fix Bitget implementation showing 0 BTC (no data)
Root cause analysis for API endpoint and symbol format issues
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class BitgetValidationAgent:
    """Independent validation agent for Bitget API analysis"""
    
    def __init__(self):
        self.name = "Bitget-ValidationAgent"
        self.api_base = "https://api.bitget.com"
        self.session = None
        
        # Test multiple API versions and endpoints
        self.test_endpoints = {
            # V2 Mix API (current implementation)
            'v2_ticker': f"{self.api_base}/api/v2/mix/market/ticker",
            'v2_funding': f"{self.api_base}/api/v2/mix/market/current-fund-rate",
            'v2_contracts': f"{self.api_base}/api/v2/mix/market/contracts",
            
            # V1 Mix API (fallback)
            'v1_ticker': f"{self.api_base}/api/mix/v1/market/ticker",
            'v1_contracts': f"{self.api_base}/api/mix/v1/market/contracts",
            
            # Spot API (for comparison)
            'spot_ticker': f"{self.api_base}/api/spot/v1/market/ticker",
            
            # Public market data
            'public_symbols': f"{self.api_base}/api/v2/mix/market/contracts"
        }
        
        # Test various symbol formats
        self.test_symbol_formats = {
            'v2_umcbl': ['BTCUSDT_UMCBL', 'ETHUSDT_UMCBL'],      # Linear USDT
            'v2_dmcbl': ['BTCUSD_DMCBL', 'ETHUSD_DMCBL'],        # Inverse USD
            'v2_simple': ['BTCUSDT', 'ETHUSDT'],                 # Simple format
            'v2_spbl': ['BTCUSDT_SPBL', 'ETHUSDT_SPBL'],        # Spot-like
            'v1_format': ['BTCUSDT_UMCBL', 'BTCUSD_DMCBL']       # V1 format
        }
        
        # Product types to test
        self.product_types = [
            'USDT-FUTURES',   # Linear USDT
            'COIN-FUTURES',   # Inverse 
            'UMCBL',          # Alternative linear
            'DMCBL',          # Alternative inverse
            'mix'             # Generic mix
        ]
        
    async def get_session(self):
        """Get HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            
    async def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validate all Bitget API endpoints and discover working configurations"""
        print(f"🔍 {self.name}: Starting comprehensive Bitget API validation")
        
        validation_results = {
            'endpoint_discovery': {},
            'symbol_format_discovery': {},
            'product_type_discovery': {},
            'working_configurations': [],
            'oi_field_discovery': {},
            'api_corrections': {}
        }
        
        session = await self.get_session()
        
        # Step 1: Test all endpoints for basic accessibility
        await self._test_endpoint_accessibility(session, validation_results)
        
        # Step 2: Discover available symbols and contracts
        await self._discover_available_symbols(session, validation_results)
        
        # Step 3: Test symbol formats with different product types
        await self._test_symbol_formats(session, validation_results)
        
        # Step 4: Test working configurations for OI data
        await self._test_oi_data_extraction(session, validation_results)
        
        # Step 5: Generate corrections
        self._generate_api_corrections(validation_results)
        
        return validation_results
    
    async def _test_endpoint_accessibility(self, session, results):
        """Test basic endpoint accessibility"""
        print(f"\n📡 Testing endpoint accessibility")
        
        for endpoint_name, url in self.test_endpoints.items():
            try:
                # Test without parameters first
                async with session.get(url) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = await response.text()
                    
                    results['endpoint_discovery'][endpoint_name] = {
                        'url': url,
                        'status': status,
                        'accessible': status in [200, 400],  # 400 might mean missing params
                        'response_type': type(data).__name__,
                        'response_sample': str(data)[:200] if data else None
                    }
                    
                    print(f"{'✅' if status in [200, 400] else '❌'} {endpoint_name}: {status}")
                    
            except Exception as e:
                results['endpoint_discovery'][endpoint_name] = {
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                }
                print(f"❌ {endpoint_name}: {str(e)}")
    
    async def _discover_available_symbols(self, session, results):
        """Discover what symbols are actually available"""
        print(f"\n🔍 Discovering available symbols/contracts")
        
        # Test contracts endpoint without parameters
        working_endpoints = [name for name, data in results['endpoint_discovery'].items() 
                           if data.get('accessible', False) and 'contracts' in name]
        
        for endpoint_name in working_endpoints:
            url = self.test_endpoints[endpoint_name]
            try:
                # Try different parameter combinations
                test_params = [
                    {},  # No params
                    {'productType': 'USDT-FUTURES'},
                    {'productType': 'COIN-FUTURES'},
                    {'symbol': 'BTCUSDT_UMCBL'},
                    {'symbol': 'BTCUSD_DMCBL'}
                ]
                
                for params in test_params:
                    try:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data and data.get('code') == '00000' and data.get('data'):
                                    symbols_found = []
                                    contracts = data['data']
                                    
                                    if isinstance(contracts, list):
                                        symbols_found = [c.get('symbol', 'unknown') for c in contracts[:10]]
                                    
                                    results['symbol_format_discovery'][f'{endpoint_name}_{str(params)}'] = {
                                        'endpoint': endpoint_name,
                                        'params': params,
                                        'symbols_found': symbols_found,
                                        'total_contracts': len(contracts) if isinstance(contracts, list) else 1,
                                        'sample_contract': contracts[0] if isinstance(contracts, list) and contracts else contracts
                                    }
                                    
                                    print(f"✅ {endpoint_name} + {params}: Found {len(symbols_found)} symbols")
                                    if symbols_found:
                                        print(f"   Sample symbols: {symbols_found[:5]}")
                                    
                                    break  # Success, no need to try more params
                                    
                    except Exception as e:
                        continue  # Try next param combination
                        
            except Exception as e:
                print(f"❌ Error discovering symbols for {endpoint_name}: {str(e)}")
    
    async def _test_symbol_formats(self, session, results):
        """Test different symbol formats with working endpoints"""
        print(f"\n🎯 Testing symbol formats")
        
        # Get working endpoints
        working_endpoints = [
            name for name, data in results['endpoint_discovery'].items()
            if data.get('accessible', False) and 'ticker' in name
        ]
        
        for endpoint_name in working_endpoints:
            url = self.test_endpoints[endpoint_name]
            
            # Test each symbol format category
            for format_name, symbols in self.test_symbol_formats.items():
                for symbol in symbols:
                    # Test with different product types
                    for product_type in self.product_types:
                        try:
                            params = {'symbol': symbol, 'productType': product_type}
                            
                            async with session.get(url, params=params) as response:
                                status = response.status
                                
                                if status == 200:
                                    data = await response.json()
                                    
                                    if data and data.get('code') == '00000' and data.get('data'):
                                        ticker_data = data['data']
                                        
                                        # Extract key information
                                        config_key = f"{endpoint_name}_{format_name}_{symbol}_{product_type}"
                                        results['product_type_discovery'][config_key] = {
                                            'endpoint': endpoint_name,
                                            'symbol': symbol,
                                            'product_type': product_type,
                                            'format_category': format_name,
                                            'working': True,
                                            'price': ticker_data.get('lastPr', ticker_data.get('last', 0)),
                                            'available_fields': list(ticker_data.keys()),
                                            'sample_data': ticker_data
                                        }
                                        
                                        print(f"✅ {symbol} + {product_type} on {endpoint_name}: WORKING")
                                        
                                        # Add to working configurations
                                        results['working_configurations'].append({
                                            'endpoint': endpoint_name,
                                            'symbol': symbol,
                                            'product_type': product_type,
                                            'api_url': url,
                                            'params': params
                                        })
                                        
                        except Exception as e:
                            continue  # Silent fail for non-working combinations
    
    async def _test_oi_data_extraction(self, session, results):
        """Test OI data extraction from working configurations"""
        print(f"\n📊 Testing OI data extraction from working configurations")
        
        # Test top working configurations
        working_configs = results.get('working_configurations', [])[:10]  # Test top 10
        
        for config in working_configs:
            try:
                url = config['api_url']
                params = config['params']
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and data.get('code') == '00000' and data.get('data'):
                            ticker_data = data['data']
                            
                            # Look for OI-related fields
                            oi_fields = {}
                            for key, value in ticker_data.items():
                                if any(keyword in key.lower() for keyword in 
                                      ['open', 'interest', 'holding', 'position']):
                                    try:
                                        oi_fields[key] = float(value)
                                    except:
                                        oi_fields[key] = value
                            
                            # Analyze realistic values
                            price = float(ticker_data.get('lastPr', ticker_data.get('last', 100000)))
                            
                            realistic_oi_fields = {}
                            for field, value in oi_fields.items():
                                if isinstance(value, (int, float)) and value > 0:
                                    # Check if realistic for BTC
                                    if 'BTC' in config['symbol']:
                                        value_as_btc = value
                                        value_as_usd = value * price
                                        
                                        # Realistic ranges
                                        is_realistic = (10_000 <= value_as_btc <= 100_000 or 
                                                      1e9 <= value_as_usd <= 10e9)
                                        
                                        realistic_oi_fields[field] = {
                                            'raw_value': value,
                                            'as_btc': value_as_btc,
                                            'as_usd': value_as_usd,
                                            'is_realistic': is_realistic
                                        }
                            
                            config_key = f"{config['symbol']}_{config['product_type']}"
                            results['oi_field_discovery'][config_key] = {
                                'config': config,
                                'all_oi_fields': oi_fields,
                                'realistic_oi_fields': realistic_oi_fields,
                                'price': price,
                                'ticker_data': ticker_data
                            }
                            
                            print(f"📊 {config['symbol']} ({config['product_type']}): Found {len(realistic_oi_fields)} realistic OI fields")
                            for field, analysis in realistic_oi_fields.items():
                                status = "✅" if analysis['is_realistic'] else "❌"
                                print(f"   {field}: {analysis['as_btc']:,.0f} BTC (${analysis['as_usd']/1e9:.1f}B) {status}")
                            
            except Exception as e:
                print(f"❌ Error testing OI extraction for {config.get('symbol', 'unknown')}: {str(e)}")
    
    def _generate_api_corrections(self, results):
        """Generate specific API corrections needed"""
        corrections = {
            'root_cause_analysis': [],
            'working_endpoints': [],
            'correct_symbol_formats': [],
            'correct_product_types': [],
            'oi_field_mappings': {},
            'implementation_fixes': [],
            'go_no_go_recommendation': 'NO_GO'
        }
        
        # Analyze working configurations
        working_configs = results.get('working_configurations', [])
        oi_discoveries = results.get('oi_field_discovery', {})
        
        if not working_configs:
            corrections['root_cause_analysis'].append("No working API endpoint configurations found")
            corrections['root_cause_analysis'].append("API endpoints may be incorrect or require authentication")
        else:
            corrections['working_endpoints'] = list(set(config['endpoint'] for config in working_configs))
            corrections['correct_symbol_formats'] = list(set(config['symbol'] for config in working_configs))
            corrections['correct_product_types'] = list(set(config['product_type'] for config in working_configs))
        
        # Analyze OI field discoveries
        realistic_oi_found = False
        for config_key, discovery in oi_discoveries.items():
            realistic_fields = discovery.get('realistic_oi_fields', {})
            if realistic_fields:
                realistic_oi_found = True
                
                # Find best OI field
                best_field = None
                best_score = 0
                
                for field, analysis in realistic_fields.items():
                    score = 0
                    if analysis['is_realistic']:
                        score += 10
                    if 'open' in field.lower() and 'interest' in field.lower():
                        score += 15
                    elif 'holding' in field.lower():
                        score += 8
                    
                    if score > best_score:
                        best_score = score
                        best_field = field
                
                if best_field:
                    corrections['oi_field_mappings'][config_key] = {
                        'recommended_field': best_field,
                        'field_analysis': realistic_fields[best_field],
                        'config': discovery['config']
                    }
        
        # Generate implementation fixes
        if working_configs and realistic_oi_found:
            corrections['go_no_go_recommendation'] = 'GO'
            corrections['implementation_fixes'].extend([
                f"Use working endpoints: {corrections['working_endpoints']}",
                f"Correct symbol formats: {corrections['correct_symbol_formats']}",
                f"Correct product types: {corrections['correct_product_types']}",
                "Implement discovered OI field mappings",
                "Add proper error handling for API response validation"
            ])
        else:
            if not working_configs:
                corrections['root_cause_analysis'].append("Critical: No working API configurations")
            if not realistic_oi_found:
                corrections['root_cause_analysis'].append("Critical: No realistic OI data found")
        
        results['api_corrections'] = corrections
    
    async def run_comprehensive_validation(self):
        """Run complete validation and generate report"""
        print(f"🚀 {self.name}: Starting comprehensive Bitget validation")
        
        try:
            # Run API validation
            validation_results = await self.validate_api_endpoints()
            
            # Generate final report
            report = self._generate_final_report(validation_results)
            
            return report
            
        except Exception as e:
            print(f"❌ Validation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await self.close()
    
    def _generate_final_report(self, results) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        corrections = results.get('api_corrections', {})
        
        report = {
            'exchange': 'Bitget',
            'validation_timestamp': datetime.now().isoformat(),
            'validation_agent': self.name,
            'root_cause_analysis': corrections.get('root_cause_analysis', []),
            'working_configurations_found': len(results.get('working_configurations', [])),
            'oi_fields_discovered': len(results.get('oi_field_discovery', {})),
            'go_no_go': corrections.get('go_no_go_recommendation', 'NO_GO'),
            'api_corrections': corrections,
            'detailed_analysis': results
        }
        
        # Add specific fixes needed
        if corrections.get('implementation_fixes'):
            report['required_implementation_changes'] = corrections['implementation_fixes']
        
        return report

async def main():
    """Main validation execution"""
    print("🔍 Bitget Independent Validation Agent")
    print("=" * 50)
    
    agent = BitgetValidationAgent()
    report = await agent.run_comprehensive_validation()
    
    if report:
        print(f"\n📋 FINAL VALIDATION REPORT")
        print(f"Exchange: {report['exchange']}")
        print(f"Working Configurations: {report['working_configurations_found']}")
        print(f"OI Fields Discovered: {report['oi_fields_discovered']}")
        print(f"Decision: {report['go_no_go']}")
        
        if report['root_cause_analysis']:
            print(f"\n🔍 Root Cause Analysis:")
            for issue in report['root_cause_analysis']:
                print(f"  • {issue}")
        
        if report.get('required_implementation_changes'):
            print(f"\n🔧 Required Implementation Changes:")
            for fix in report['required_implementation_changes']:
                print(f"  • {fix}")
        
        # Save detailed report
        with open('/Users/screener-m3/projects/crypto-assistant/services/market-data/BITGET_VALIDATION_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to BITGET_VALIDATION_REPORT.json")
        
        return report
    else:
        print("❌ Validation failed to complete")
        return None

if __name__ == "__main__":
    asyncio.run(main())