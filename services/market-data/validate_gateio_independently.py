#!/usr/bin/env python3
"""
GATE.IO INDEPENDENT VALIDATION AGENT
Critical mission: Analyze and fix Gate.io implementation showing unrealistic 56.9M BTC ($6.1T)
Root cause analysis and API endpoint/field corrections
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class GateIOValidationAgent:
    """Independent validation agent for Gate.io API analysis"""
    
    def __init__(self):
        self.name = "GateIO-ValidationAgent"
        self.api_base = "https://api.gateio.ws/api/v4"
        self.session = None
        
        # Test endpoints to validate
        self.test_endpoints = {
            'usdt_tickers': f"{self.api_base}/futures/usdt/tickers",
            'usdt_contracts': f"{self.api_base}/futures/usdt/contracts", 
            'usdt_positions': f"{self.api_base}/futures/usdt/positions",
            'btc_tickers': f"{self.api_base}/futures/btc/tickers",
            'btc_contracts': f"{self.api_base}/futures/btc/contracts"
        }
        
        # Test symbols to validate
        self.test_symbols = {
            'usdt': ['BTC_USDT', 'ETH_USDT'],
            'btc': ['BTC_USD', 'ETH_USD']
        }
        
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
        """Validate all Gate.io API endpoints and identify correct OI fields"""
        print(f"🔍 {self.name}: Starting comprehensive API validation")
        
        validation_results = {
            'endpoint_status': {},
            'field_analysis': {},
            'oi_field_discovery': {},
            'realistic_values': {},
            'api_corrections': {}
        }
        
        session = await self.get_session()
        
        # Test all endpoints
        for endpoint_name, url in self.test_endpoints.items():
            try:
                print(f"📡 Testing endpoint: {endpoint_name}")
                
                # Test basic endpoint
                async with session.get(url) as response:
                    status = response.status
                    data = await response.json()
                    
                    validation_results['endpoint_status'][endpoint_name] = {
                        'status': status,
                        'accessible': status == 200,
                        'data_structure': type(data).__name__,
                        'data_length': len(data) if isinstance(data, list) else 1
                    }
                    
                    # Analyze data structure for OI fields
                    if status == 200 and data:
                        sample_item = data[0] if isinstance(data, list) else data
                        validation_results['field_analysis'][endpoint_name] = list(sample_item.keys())
                        
                        print(f"✅ {endpoint_name}: {status} - {len(data) if isinstance(data, list) else 1} items")
                        print(f"   Fields: {list(sample_item.keys())[:10]}...")  # First 10 fields
                        
            except Exception as e:
                validation_results['endpoint_status'][endpoint_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"❌ {endpoint_name}: {str(e)}")
        
        # Test specific symbols for OI data
        await self._test_specific_symbols(session, validation_results)
        
        # Identify correct OI fields
        await self._identify_oi_fields(session, validation_results)
        
        return validation_results
    
    async def _test_specific_symbols(self, session, results):
        """Test specific symbols to find OI data"""
        print(f"\n🎯 Testing specific symbols for OI data")
        
        # Test USDT contracts
        for symbol in self.test_symbols['usdt']:
            try:
                url = f"{self.test_endpoints['usdt_tickers']}?contract={symbol}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            item = data[0] if isinstance(data, list) else data
                            
                            # Look for OI-related fields
                            oi_fields = {}
                            for key, value in item.items():
                                if any(keyword in key.lower() for keyword in ['open', 'interest', 'size', 'volume', 'holding']):
                                    try:
                                        oi_fields[key] = float(value)
                                    except:
                                        oi_fields[key] = value
                            
                            results['oi_field_discovery'][f'usdt_{symbol}'] = {
                                'symbol': symbol,
                                'price': float(item.get('last', 0)),
                                'potential_oi_fields': oi_fields,
                                'all_fields': list(item.keys())
                            }
                            
                            print(f"📊 {symbol}: Found {len(oi_fields)} potential OI fields")
                            for field, value in oi_fields.items():
                                print(f"   {field}: {value}")
                                
            except Exception as e:
                print(f"❌ Error testing {symbol}: {str(e)}")
        
        # Test BTC inverse contracts
        for symbol in self.test_symbols['btc']:
            try:
                url = f"{self.test_endpoints['btc_tickers']}?contract={symbol}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            item = data[0] if isinstance(data, list) else data
                            
                            # Look for OI-related fields
                            oi_fields = {}
                            for key, value in item.items():
                                if any(keyword in key.lower() for keyword in ['open', 'interest', 'size', 'volume', 'holding']):
                                    try:
                                        oi_fields[key] = float(value)
                                    except:
                                        oi_fields[key] = value
                            
                            results['oi_field_discovery'][f'btc_{symbol}'] = {
                                'symbol': symbol,
                                'price': float(item.get('last', 0)),
                                'potential_oi_fields': oi_fields,
                                'all_fields': list(item.keys())
                            }
                            
                            print(f"📊 {symbol}: Found {len(oi_fields)} potential OI fields")
                            for field, value in oi_fields.items():
                                print(f"   {field}: {value}")
                                
            except Exception as e:
                print(f"❌ Error testing {symbol}: {str(e)}")
    
    async def _identify_oi_fields(self, session, results):
        """Identify the correct OI fields and validate realistic values"""
        print(f"\n🔬 Analyzing OI fields for realistic values")
        
        # Expected realistic ranges for BTC
        realistic_ranges = {
            'btc_oi_tokens': (10_000, 100_000),  # 10K-100K BTC
            'btc_oi_usd': (1e9, 10e9)           # $1B-10B USD
        }
        
        field_recommendations = {}
        
        for discovery_key, data in results['oi_field_discovery'].items():
            symbol = data['symbol']
            price = data['price']
            potential_fields = data['potential_oi_fields']
            
            print(f"\n🔍 Analyzing {symbol} (Price: ${price:,.2f})")
            
            field_analysis = {}
            for field, value in potential_fields.items():
                if isinstance(value, (int, float)) and value > 0:
                    # Calculate what this would mean in BTC and USD
                    if 'BTC' in symbol:
                        # For BTC pairs
                        value_as_btc = value
                        value_as_usd = value * price
                        
                        # Check if realistic
                        is_realistic_btc = realistic_ranges['btc_oi_tokens'][0] <= value_as_btc <= realistic_ranges['btc_oi_tokens'][1]
                        is_realistic_usd = realistic_ranges['btc_oi_usd'][0] <= value_as_usd <= realistic_ranges['btc_oi_usd'][1]
                        
                        field_analysis[field] = {
                            'raw_value': value,
                            'interpreted_as_btc': value_as_btc,
                            'interpreted_as_usd': value_as_usd,
                            'realistic_as_btc': is_realistic_btc,
                            'realistic_as_usd': is_realistic_usd,
                            'likely_oi_field': is_realistic_btc or is_realistic_usd
                        }
                        
                        status = "✅ REALISTIC" if (is_realistic_btc or is_realistic_usd) else "❌ UNREALISTIC"
                        print(f"   {field}: {value:,.0f} → {value_as_btc:,.0f} BTC (${value_as_usd/1e9:.1f}B) {status}")
            
            field_recommendations[discovery_key] = field_analysis
            
        results['realistic_values'] = field_recommendations
        
        # Generate API corrections
        self._generate_api_corrections(results)
    
    def _generate_api_corrections(self, results):
        """Generate specific API corrections needed"""
        corrections = {
            'critical_issues_found': [],
            'endpoint_corrections': {},
            'field_corrections': {},
            'implementation_fixes': []
        }
        
        # Analyze field discovery results
        for discovery_key, field_analysis in results['realistic_values'].items():
            symbol = results['oi_field_discovery'][discovery_key]['symbol']
            
            # Find the best OI field
            best_oi_field = None
            best_score = 0
            
            for field, analysis in field_analysis.items():
                score = 0
                if analysis['likely_oi_field']:
                    score += 10
                if analysis['realistic_as_btc']:
                    score += 5
                if analysis['realistic_as_usd']:
                    score += 3
                if 'open' in field.lower() and 'interest' in field.lower():
                    score += 15  # Perfect match
                elif 'size' in field.lower():
                    score += 2   # Size fields often OI
                elif 'volume' in field.lower():
                    score -= 5   # Volume is NOT OI
                
                if score > best_score:
                    best_score = score
                    best_oi_field = field
            
            if best_oi_field:
                corrections['field_corrections'][symbol] = {
                    'recommended_oi_field': best_oi_field,
                    'confidence_score': best_score,
                    'field_analysis': field_analysis[best_oi_field]
                }
                print(f"🎯 {symbol}: Recommend using '{best_oi_field}' field (score: {best_score})")
            else:
                corrections['critical_issues_found'].append(f"No suitable OI field found for {symbol}")
                print(f"⚠️ {symbol}: No suitable OI field identified")
        
        # Check for volume vs OI confusion
        for discovery_key, data in results['oi_field_discovery'].items():
            potential_fields = data['potential_oi_fields']
            if any('volume' in field.lower() for field in potential_fields.keys()):
                if any(val > 1_000_000 for val in potential_fields.values() if isinstance(val, (int, float))):
                    corrections['critical_issues_found'].append(
                        f"High volume values detected in {data['symbol']} - may be confusing volume with OI"
                    )
        
        # Generate implementation fixes
        if corrections['field_corrections']:
            corrections['implementation_fixes'].append("Update field extraction logic to use recommended OI fields")
            corrections['implementation_fixes'].append("Add validation to reject volume fields as OI")
            corrections['implementation_fixes'].append("Implement realistic value range checks")
        
        results['api_corrections'] = corrections
    
    async def run_comprehensive_validation(self):
        """Run complete validation and generate report"""
        print(f"🚀 {self.name}: Starting comprehensive Gate.io validation")
        
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
        report = {
            'exchange': 'Gate.io',
            'validation_timestamp': datetime.now().isoformat(),
            'validation_agent': self.name,
            'critical_issues': [],
            'api_status': 'unknown',
            'recommended_fixes': [],
            'go_no_go': 'NO_GO',  # Default to no-go until proven otherwise
            'detailed_analysis': results
        }
        
        # Analyze results
        corrections = results.get('api_corrections', {})
        critical_issues = corrections.get('critical_issues_found', [])
        field_corrections = corrections.get('field_corrections', {})
        
        # Determine API status
        working_endpoints = sum(1 for status in results['endpoint_status'].values() 
                              if status.get('accessible', False))
        total_endpoints = len(results['endpoint_status'])
        
        if working_endpoints >= total_endpoints * 0.6:  # 60% working
            report['api_status'] = 'FUNCTIONAL'
        else:
            report['api_status'] = 'BROKEN'
            critical_issues.append("Majority of API endpoints not accessible")
        
        # Check for realistic OI values
        has_realistic_oi = any(
            any(analysis.get('likely_oi_field', False) for analysis in field_data.values())
            for field_data in results.get('realistic_values', {}).values()
        )
        
        if has_realistic_oi:
            report['go_no_go'] = 'GO'
            report['recommended_fixes'].extend([
                "Implement recommended OI field mappings",
                "Add realistic value range validation",
                "Remove volume field confusion"
            ])
        else:
            report['critical_issues'].extend([
                "No realistic OI fields identified",
                "Current implementation likely confusing volume with OI",
                "API endpoints may not provide proper OI data"
            ])
        
        # Add specific issues
        report['critical_issues'].extend(critical_issues)
        
        return report

async def main():
    """Main validation execution"""
    print("🔍 Gate.io Independent Validation Agent")
    print("=" * 50)
    
    agent = GateIOValidationAgent()
    report = await agent.run_comprehensive_validation()
    
    if report:
        print(f"\n📋 FINAL VALIDATION REPORT")
        print(f"Exchange: {report['exchange']}")
        print(f"API Status: {report['api_status']}")
        print(f"Decision: {report['go_no_go']}")
        print(f"Critical Issues: {len(report['critical_issues'])}")
        
        if report['critical_issues']:
            print(f"\n❌ Critical Issues:")
            for issue in report['critical_issues']:
                print(f"  • {issue}")
        
        if report['recommended_fixes']:
            print(f"\n🔧 Recommended Fixes:")
            for fix in report['recommended_fixes']:
                print(f"  • {fix}")
        
        # Save detailed report
        with open('/Users/screener-m3/projects/crypto-assistant/services/market-data/GATEIO_VALIDATION_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to GATEIO_VALIDATION_REPORT.json")
        
        return report
    else:
        print("❌ Validation failed to complete")
        return None

if __name__ == "__main__":
    asyncio.run(main())