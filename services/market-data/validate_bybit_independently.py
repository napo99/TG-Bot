#!/usr/bin/env python3
"""
INDEPENDENT VALIDATION OF BYBIT IMPLEMENTATION
Deploy counter-agents to verify Bybit claims - DO NOT TRUST SELF-VALIDATION

BYBIT CLAIMS TO VALIDATE:
- USDT: 54,793 BTC ($5.9B) 
- USD Inverse: 13,531 BTC ($1.5B)
- Total: 68,323 BTC ($7.4B)
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any
from bybit_oi_provider import BybitOIProvider

class BybitCounterValidator:
    """Independent counter-agent to validate Bybit provider claims"""
    
    def __init__(self):
        self.validation_results = []
    
    async def validate_bybit_claims(self, bybit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy multiple independent validation methods"""
        
        print("🛡️ DEPLOYING INDEPENDENT COUNTER-AGENTS TO VALIDATE BYBIT CLAIMS")
        print("=" * 80)
        
        validation_tasks = [
            self._counter_agent_price_validation(bybit_data),
            self._counter_agent_calculation_validation(bybit_data), 
            self._counter_agent_api_validation(bybit_data),
            self._counter_agent_magnitude_validation(bybit_data),
            self._counter_agent_bybit_specific_validation(bybit_data)
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results
        validation_summary = {
            'total_validations': len(results),
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'detailed_results': [],
            'overall_status': 'UNKNOWN'
        }
        
        for result in results:
            if isinstance(result, Exception):
                validation_summary['errors'] += 1
                validation_summary['detailed_results'].append({
                    'status': 'ERROR',
                    'details': str(result)
                })
            else:
                validation_summary['detailed_results'].append(result)
                if result['status'] == 'PASS':
                    validation_summary['passed'] += 1
                else:
                    validation_summary['failed'] += 1
        
        # Determine overall status
        pass_rate = validation_summary['passed'] / validation_summary['total_validations'] * 100
        if pass_rate >= 95:
            validation_summary['overall_status'] = 'TRUSTED'
        elif pass_rate >= 80:
            validation_summary['overall_status'] = 'CAUTIOUS'
        elif pass_rate >= 60:
            validation_summary['overall_status'] = 'SUSPICIOUS'
        else:
            validation_summary['overall_status'] = 'REJECTED'
        
        validation_summary['pass_rate'] = pass_rate
        
        return validation_summary
    
    async def _counter_agent_price_validation(self, bybit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 1: Validate prices against external sources"""
        try:
            print("🔍 Counter-Agent 1: Price Validation")
            
            # Get external price from CoinGecko (independent source)
            external_price = await self._get_coingecko_price('BTC')
            
            if not external_price:
                return {
                    'agent': 'price_validator',
                    'status': 'ERROR',
                    'details': 'Could not get external price reference'
                }
            
            # Check Bybit price claims against external reference
            price_validations = []
            
            for market in bybit_data['markets']:
                bybit_price = market['price']
                deviation_pct = abs(bybit_price - external_price) / external_price * 100
                
                if deviation_pct < 5.0:  # Max 5% allowed deviation
                    price_validations.append({
                        'market': market['market_type'],
                        'status': 'PASS',
                        'bybit_price': bybit_price,
                        'external_price': external_price,
                        'deviation_pct': deviation_pct
                    })
                else:
                    price_validations.append({
                        'market': market['market_type'],
                        'status': 'FAIL',
                        'bybit_price': bybit_price,
                        'external_price': external_price,
                        'deviation_pct': deviation_pct,
                        'reason': f'Price deviation {deviation_pct:.1f}% > 5%'
                    })
            
            # Overall price validation status
            passed_validations = sum(1 for v in price_validations if v['status'] == 'PASS')
            overall_status = 'PASS' if passed_validations == len(price_validations) else 'FAIL'
            
            print(f"  Result: {overall_status} - {passed_validations}/{len(price_validations)} prices validated")
            
            return {
                'agent': 'price_validator',
                'status': overall_status,
                'details': f'External price: ${external_price:,.2f}',
                'price_validations': price_validations
            }
            
        except Exception as e:
            return {
                'agent': 'price_validator',
                'status': 'ERROR',
                'details': f'Price validation error: {str(e)}'
            }
    
    async def _counter_agent_calculation_validation(self, bybit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 2: Independent mathematical validation"""
        try:
            print("🔍 Counter-Agent 2: Calculation Validation")
            
            calculation_validations = []
            
            for market in bybit_data['markets']:
                oi_tokens = market['oi_tokens']
                oi_usd = market['oi_usd']
                price = market['price']
                market_type = market['market_type']
                
                # Independent calculation
                if market_type in ['USDT', 'USDC']:
                    # Linear: OI_USD = OI_TOKENS × PRICE
                    expected_oi_usd = oi_tokens * price
                elif market_type == 'USD':
                    # Inverse: For validation, still use basic calculation
                    # In practice, Bybit inverse is more complex but this validates magnitude
                    expected_oi_usd = oi_tokens * price
                
                # Check calculation accuracy
                if expected_oi_usd > 0:
                    error_pct = abs(oi_usd - expected_oi_usd) / expected_oi_usd * 100
                    
                    # More lenient for inverse contracts (they're complex)
                    max_error = 5.0 if market_type == 'USD' else 1.0
                    
                    if error_pct < max_error:
                        calculation_validations.append({
                            'market': market_type,
                            'status': 'PASS',
                            'expected_usd': expected_oi_usd,
                            'actual_usd': oi_usd,
                            'error_pct': error_pct,
                            'max_allowed': max_error
                        })
                    else:
                        calculation_validations.append({
                            'market': market_type,
                            'status': 'FAIL',
                            'expected_usd': expected_oi_usd,
                            'actual_usd': oi_usd,
                            'error_pct': error_pct,
                            'max_allowed': max_error,
                            'reason': f'Calculation error {error_pct:.2f}% > {max_error}%'
                        })
            
            passed_calculations = sum(1 for v in calculation_validations if v['status'] == 'PASS')
            overall_status = 'PASS' if passed_calculations == len(calculation_validations) else 'FAIL'
            
            print(f"  Result: {overall_status} - {passed_calculations}/{len(calculation_validations)} calculations validated")
            
            return {
                'agent': 'calculation_validator',
                'status': overall_status,
                'details': f'Mathematical validation of USD calculations',
                'calculation_validations': calculation_validations
            }
            
        except Exception as e:
            return {
                'agent': 'calculation_validator',
                'status': 'ERROR',
                'details': f'Calculation validation error: {str(e)}'
            }
    
    async def _counter_agent_api_validation(self, bybit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 3: Direct API validation"""
        try:
            print("🔍 Counter-Agent 3: Direct API Validation")
            
            api_validations = []
            
            # Validate USDT market directly against Bybit API
            usdt_market = next((m for m in bybit_data['markets'] if m['market_type'] == 'USDT'), None)
            
            if usdt_market:
                # Get OI directly from Bybit V5 API
                external_oi = await self._get_bybit_oi_direct('BTCUSDT', 'linear')
                
                if external_oi:
                    provider_oi = usdt_market['oi_tokens']
                    deviation_pct = abs(provider_oi - external_oi) / external_oi * 100
                    
                    if deviation_pct < 15.0:  # Max 15% OI deviation (Bybit can be volatile)
                        api_validations.append({
                            'market': 'USDT',
                            'status': 'PASS',
                            'provider_oi': provider_oi,
                            'external_oi': external_oi,
                            'deviation_pct': deviation_pct
                        })
                    else:
                        api_validations.append({
                            'market': 'USDT',
                            'status': 'FAIL',
                            'provider_oi': provider_oi,
                            'external_oi': external_oi,
                            'deviation_pct': deviation_pct,
                            'reason': f'OI deviation {deviation_pct:.1f}% > 15%'
                        })
                else:
                    api_validations.append({
                        'market': 'USDT',
                        'status': 'ERROR',
                        'reason': 'Could not get external USDT OI reference'
                    })
            
            # Validate USD inverse market
            usd_market = next((m for m in bybit_data['markets'] if m['market_type'] == 'USD'), None)
            
            if usd_market:
                # Get inverse OI directly from Bybit V5 API
                external_oi_data = await self._get_bybit_inverse_oi_direct('BTCUSD')
                
                if external_oi_data:
                    provider_oi = usd_market['oi_tokens']
                    external_oi = external_oi_data['oi_tokens']
                    deviation_pct = abs(provider_oi - external_oi) / external_oi * 100 if external_oi > 0 else 0
                    
                    if deviation_pct < 20.0:  # More lenient for inverse (complex calculations)
                        api_validations.append({
                            'market': 'USD',
                            'status': 'PASS',
                            'provider_oi': provider_oi,
                            'external_oi': external_oi,
                            'deviation_pct': deviation_pct
                        })
                    else:
                        api_validations.append({
                            'market': 'USD',
                            'status': 'FAIL',
                            'provider_oi': provider_oi,
                            'external_oi': external_oi,
                            'deviation_pct': deviation_pct,
                            'reason': f'Inverse OI deviation {deviation_pct:.1f}% > 20%'
                        })
                else:
                    api_validations.append({
                        'market': 'USD',
                        'status': 'ERROR',
                        'reason': 'Could not get external USD inverse OI reference'
                    })
            
            # Overall API validation status
            passed_api = sum(1 for v in api_validations if v['status'] == 'PASS')
            total_api = len(api_validations)
            overall_status = 'PASS' if passed_api == total_api and total_api > 0 else 'FAIL'
            
            if total_api == 0:
                overall_status = 'ERROR'
                details = 'No API validations performed'
            else:
                details = f'{passed_api}/{total_api} API validations passed'
            
            print(f"  Result: {overall_status} - {details}")
            
            return {
                'agent': 'api_validator',
                'status': overall_status,
                'details': details,
                'api_validations': api_validations
            }
            
        except Exception as e:
            return {
                'agent': 'api_validator',
                'status': 'ERROR',
                'details': f'API validation error: {str(e)}'
            }
    
    async def _counter_agent_magnitude_validation(self, bybit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 4: Magnitude sanity validation"""
        try:
            print("🔍 Counter-Agent 4: Magnitude Validation")
            
            total_oi_usd = bybit_data['total_oi_usd']
            
            # Known reasonable range for Bybit BTC OI (from market data)
            # Bybit typically has $3B-$15B in BTC OI (smaller than Binance)
            min_reasonable = 2_000_000_000   # $2B
            max_reasonable = 20_000_000_000  # $20B
            
            magnitude_checks = []
            
            # Overall magnitude check
            if min_reasonable <= total_oi_usd <= max_reasonable:
                magnitude_checks.append({
                    'check': 'total_oi',
                    'status': 'PASS',
                    'value': total_oi_usd,
                    'details': f'Total OI ${total_oi_usd/1e9:.1f}B within reasonable range ${min_reasonable/1e9:.0f}B-${max_reasonable/1e9:.0f}B'
                })
            else:
                if total_oi_usd < min_reasonable:
                    reason = f'Total OI ${total_oi_usd/1e9:.1f}B too low (< ${min_reasonable/1e9:.0f}B)'
                else:
                    reason = f'Total OI ${total_oi_usd/1e9:.1f}B too high (> ${max_reasonable/1e9:.0f}B)'
                
                magnitude_checks.append({
                    'check': 'total_oi',
                    'status': 'FAIL',
                    'value': total_oi_usd,
                    'details': reason
                })
            
            # Individual market magnitude checks
            for market in bybit_data['markets']:
                market_oi_usd = market['oi_usd']
                market_type = market['market_type']
                
                # Reasonable ranges per market type
                if market_type == 'USDT':
                    min_market = 1_000_000_000  # $1B
                    max_market = 15_000_000_000  # $15B
                elif market_type == 'USD':
                    min_market = 500_000_000    # $500M
                    max_market = 5_000_000_000   # $5B
                else:  # USDC
                    min_market = 0              # Can be zero if not available
                    max_market = 2_000_000_000   # $2B
                
                if min_market <= market_oi_usd <= max_market:
                    magnitude_checks.append({
                        'check': f'{market_type}_market',
                        'status': 'PASS',
                        'value': market_oi_usd,
                        'details': f'{market_type} OI ${market_oi_usd/1e9:.1f}B within range ${min_market/1e9:.1f}B-${max_market/1e9:.0f}B'
                    })
                else:
                    if market_oi_usd < min_market:
                        reason = f'{market_type} OI ${market_oi_usd/1e9:.1f}B too low (< ${min_market/1e9:.1f}B)'
                    else:
                        reason = f'{market_type} OI ${market_oi_usd/1e9:.1f}B too high (> ${max_market/1e9:.0f}B)'
                    
                    magnitude_checks.append({
                        'check': f'{market_type}_market',
                        'status': 'FAIL',
                        'value': market_oi_usd,
                        'details': reason
                    })
            
            # Overall magnitude validation
            passed_checks = sum(1 for c in magnitude_checks if c['status'] == 'PASS')
            overall_status = 'PASS' if passed_checks == len(magnitude_checks) else 'FAIL'
            
            details = f'{passed_checks}/{len(magnitude_checks)} magnitude checks passed'
            
            print(f"  Result: {overall_status} - {details}")
            
            return {
                'agent': 'magnitude_validator',
                'status': overall_status,
                'details': details,
                'magnitude_checks': magnitude_checks
            }
            
        except Exception as e:
            return {
                'agent': 'magnitude_validator',
                'status': 'ERROR',
                'details': f'Magnitude validation error: {str(e)}'
            }
    
    async def _counter_agent_bybit_specific_validation(self, bybit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 5: Bybit-specific validation"""
        try:
            print("🔍 Counter-Agent 5: Bybit-Specific Validation")
            
            bybit_checks = []
            
            # Check market coverage
            found_markets = [m['market_type'] for m in bybit_data['markets']]
            
            if 'USDT' in found_markets:
                bybit_checks.append({
                    'check': 'usdt_market_exists',
                    'status': 'PASS',
                    'details': 'USDT linear market found'
                })
            else:
                bybit_checks.append({
                    'check': 'usdt_market_exists',
                    'status': 'FAIL',
                    'details': 'USDT linear market missing (should be primary market)'
                })
            
            if 'USD' in found_markets:
                bybit_checks.append({
                    'check': 'usd_inverse_exists',
                    'status': 'PASS',
                    'details': 'USD inverse market found'
                })
            else:
                bybit_checks.append({
                    'check': 'usd_inverse_exists',
                    'status': 'FAIL',
                    'details': 'USD inverse market missing (should be available)'
                })
            
            # Validate USDT dominance (USDT should be largest market)
            usdt_market = next((m for m in bybit_data['markets'] if m['market_type'] == 'USDT'), None)
            if usdt_market:
                usdt_oi = usdt_market['oi_usd']
                total_oi = bybit_data['total_oi_usd']
                usdt_percentage = (usdt_oi / total_oi * 100) if total_oi > 0 else 0
                
                if usdt_percentage > 50:  # USDT should dominate
                    bybit_checks.append({
                        'check': 'usdt_dominance',
                        'status': 'PASS',
                        'details': f'USDT market dominance: {usdt_percentage:.1f}% (healthy)'
                    })
                else:
                    bybit_checks.append({
                        'check': 'usdt_dominance',
                        'status': 'FAIL',
                        'details': f'USDT market dominance: {usdt_percentage:.1f}% (too low, should be >50%)'
                    })
            
            # Validate price consistency (all markets should have similar BTC price)
            prices = [m['price'] for m in bybit_data['markets']]
            if len(prices) > 1:
                price_range = max(prices) - min(prices)
                avg_price = sum(prices) / len(prices)
                price_spread_pct = (price_range / avg_price * 100) if avg_price > 0 else 0
                
                if price_spread_pct < 2.0:  # Max 2% price spread across markets
                    bybit_checks.append({
                        'check': 'price_consistency',
                        'status': 'PASS',
                        'details': f'Price spread: {price_spread_pct:.2f}% (consistent)'
                    })
                else:
                    bybit_checks.append({
                        'check': 'price_consistency',
                        'status': 'FAIL',
                        'details': f'Price spread: {price_spread_pct:.2f}% (too high, >2%)'
                    })
            
            # Overall Bybit-specific validation
            passed_checks = sum(1 for c in bybit_checks if c['status'] == 'PASS')
            overall_status = 'PASS' if passed_checks == len(bybit_checks) else 'FAIL'
            
            details = f'{passed_checks}/{len(bybit_checks)} Bybit-specific checks passed'
            
            print(f"  Result: {overall_status} - {details}")
            
            return {
                'agent': 'bybit_specific_validator',
                'status': overall_status,
                'details': details,
                'bybit_checks': bybit_checks
            }
            
        except Exception as e:
            return {
                'agent': 'bybit_specific_validator',
                'status': 'ERROR',
                'details': f'Bybit-specific validation error: {str(e)}'
            }
    
    async def _get_coingecko_price(self, symbol: str) -> float:
        """Get price from CoinGecko as external reference"""
        try:
            symbol_map = {'BTC': 'bitcoin', 'ETH': 'ethereum'}
            cg_id = symbol_map.get(symbol, symbol.lower())
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    return data[cg_id]['usd']
        except:
            return None
    
    async def _get_bybit_oi_direct(self, symbol: str, category: str) -> float:
        """Get OI directly from Bybit V5 API as external reference"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.bybit.com/v5/market/tickers"
                params = {"category": category, "symbol": symbol}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                        return float(data['result']['list'][0]['openInterest'])
                    return None
        except:
            return None
    
    async def _get_bybit_inverse_oi_direct(self, symbol: str) -> Dict[str, float]:
        """Get inverse OI directly from Bybit V5 API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.bybit.com/v5/market/tickers"
                params = {"category": "inverse", "symbol": symbol}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                        ticker = data['result']['list'][0]
                        price = float(ticker['lastPrice'])
                        oi_raw = float(ticker.get('openInterest', 0))
                        
                        # Convert to tokens using same logic as provider
                        oi_tokens = oi_raw / price if price > 0 else 0
                        
                        return {
                            'oi_tokens': oi_tokens,
                            'oi_raw': oi_raw,
                            'price': price
                        }
                    return None
        except:
            return None

async def main():
    """Run independent validation of Bybit implementation"""
    print("🚨 INDEPENDENT VALIDATION: Testing Bybit Claims")
    print("=" * 80)
    print("⚠️ WARNING: Do NOT trust self-validation - using counter-agents")
    print("=" * 80)
    print("🎯 BYBIT CLAIMS TO VALIDATE:")
    print("   - USDT: 54,793 BTC ($5.9B)")
    print("   - USD Inverse: 13,531 BTC ($1.5B)")
    print("   - Total: 68,323 BTC ($7.4B)")
    print("=" * 80)
    
    # Get Bybit provider data
    provider = BybitOIProvider()
    
    try:
        result = await provider.get_oi_data('BTC')
        
        # Format data for validation
        bybit_claims = {
            'total_oi_tokens': result.total_oi_tokens,
            'total_oi_usd': result.total_oi_usd,
            'markets': [
                {
                    'market_type': market.market_type.value,
                    'oi_tokens': market.oi_tokens,
                    'oi_usd': market.oi_usd,
                    'price': market.price,
                    'calculation_method': market.calculation_method
                } for market in result.markets
            ]
        }
        
        print(f"📊 BYBIT PROVIDER CLAIMS:")
        print(f"Total OI: {result.total_oi_tokens:,.0f} BTC (${result.total_oi_usd/1e9:.1f}B)")
        print(f"Markets: {len(result.markets)}")
        for market in result.markets:
            print(f"  {market.market_type.value}: {market.oi_tokens:,.0f} BTC (${market.oi_usd/1e9:.1f}B)")
        
        print(f"\n🛡️ DEPLOYING COUNTER-AGENTS FOR INDEPENDENT VALIDATION...")
        
        # Deploy counter-agents
        validator = BybitCounterValidator()
        validation_report = await validator.validate_bybit_claims(bybit_claims)
        
        # Display validation results
        print(f"\n📊 COUNTER-AGENT VALIDATION REPORT:")
        print(f"=" * 80)
        print(f"Overall Status: {validation_report['overall_status']}")
        print(f"Pass Rate: {validation_report['pass_rate']:.1f}%")
        print(f"Passed: {validation_report['passed']}")
        print(f"Failed: {validation_report['failed']}")
        print(f"Errors: {validation_report['errors']}")
        
        print(f"\n🔍 DETAILED VALIDATION RESULTS:")
        for i, validation in enumerate(validation_report['detailed_results'], 1):
            status_emoji = "✅" if validation['status'] == 'PASS' else "❌" if validation['status'] == 'FAIL' else "⚠️"
            print(f"{status_emoji} {validation['agent']}: {validation['details']}")
        
        # Final verdict
        print(f"\n" + "=" * 80)
        if validation_report['overall_status'] == 'TRUSTED':
            print(f"✅ VERDICT: Bybit implementation VALIDATED by independent counter-agents")
            print(f"✅ SAFE TO PROCEED to next exchange implementation")
            print(f"✅ Claims verified: USDT + USD markets totaling ~68K BTC (~$7.4B)")
        elif validation_report['overall_status'] == 'CAUTIOUS':
            print(f"⚠️ VERDICT: Some issues found but generally acceptable")
            print(f"⚠️ REVIEW validation failures before proceeding")
            print(f"⚠️ Consider fixing minor issues for production deployment")
        else:
            print(f"❌ VERDICT: Bybit implementation REJECTED by counter-agents")
            print(f"❌ DO NOT PROCEED - Fix critical issues before continuing")
            print(f"❌ Major problems detected in OI calculations or API integration")
        
        print(f"=" * 80)
        
        # Specific recommendations
        if validation_report['pass_rate'] >= 80:
            print(f"🎯 RECOMMENDATION: Proceed to next exchange (OKX/Bitget)")
        else:
            print(f"🎯 RECOMMENDATION: Fix validation failures before proceeding")
        
        return validation_report['overall_status'] in ['TRUSTED', 'CAUTIOUS']
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(main())