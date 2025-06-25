#!/usr/bin/env python3
"""
INDEPENDENT VALIDATION OF BINANCE IMPLEMENTATION
Deploy counter-agents to verify my claims - DO NOT TRUST SELF-VALIDATION
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any
from binance_oi_provider import BinanceOIProvider

class BinanceCounterValidator:
    """Independent counter-agent to validate Binance provider claims"""
    
    def __init__(self):
        self.validation_results = []
    
    async def validate_binance_claims(self, binance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy multiple independent validation methods"""
        
        print("🛡️ DEPLOYING INDEPENDENT COUNTER-AGENTS TO VALIDATE BINANCE CLAIMS")
        print("=" * 80)
        
        validation_tasks = [
            self._counter_agent_price_validation(binance_data),
            self._counter_agent_calculation_validation(binance_data), 
            self._counter_agent_api_validation(binance_data),
            self._counter_agent_magnitude_validation(binance_data)
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
    
    async def _counter_agent_price_validation(self, binance_data: Dict[str, Any]) -> Dict[str, Any]:
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
            
            # Check Binance price claims against external reference
            price_validations = []
            
            for market in binance_data['markets']:
                binance_price = market['price']
                deviation_pct = abs(binance_price - external_price) / external_price * 100
                
                if deviation_pct < 5.0:  # Max 5% allowed deviation
                    price_validations.append({
                        'market': market['market_type'],
                        'status': 'PASS',
                        'binance_price': binance_price,
                        'external_price': external_price,
                        'deviation_pct': deviation_pct
                    })
                else:
                    price_validations.append({
                        'market': market['market_type'],
                        'status': 'FAIL',
                        'binance_price': binance_price,
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
    
    async def _counter_agent_calculation_validation(self, binance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 2: Independent mathematical validation"""
        try:
            print("🔍 Counter-Agent 2: Calculation Validation")
            
            calculation_validations = []
            
            for market in binance_data['markets']:
                oi_tokens = market['oi_tokens']
                oi_usd = market['oi_usd']
                price = market['price']
                market_type = market['market_type']
                
                # Independent calculation
                if market_type in ['USDT', 'USDC']:
                    # Linear: OI_USD = OI_TOKENS × PRICE
                    expected_oi_usd = oi_tokens * price
                elif market_type == 'USD':
                    # Inverse: This is more complex, but we can still validate magnitude
                    # For DAPI, contracts × $100 should roughly equal oi_usd
                    expected_oi_usd = oi_tokens * price  # Basic validation
                
                # Check calculation accuracy
                if expected_oi_usd > 0:
                    error_pct = abs(oi_usd - expected_oi_usd) / expected_oi_usd * 100
                    
                    if error_pct < 1.0:  # Max 1% calculation error
                        calculation_validations.append({
                            'market': market_type,
                            'status': 'PASS',
                            'expected_usd': expected_oi_usd,
                            'actual_usd': oi_usd,
                            'error_pct': error_pct
                        })
                    else:
                        calculation_validations.append({
                            'market': market_type,
                            'status': 'FAIL',
                            'expected_usd': expected_oi_usd,
                            'actual_usd': oi_usd,
                            'error_pct': error_pct,
                            'reason': f'Calculation error {error_pct:.2f}% > 1%'
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
    
    async def _counter_agent_api_validation(self, binance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 3: Direct API validation"""
        try:
            print("🔍 Counter-Agent 3: Direct API Validation")
            
            # Validate USDT market directly against Binance API
            usdt_market = next((m for m in binance_data['markets'] if m['market_type'] == 'USDT'), None)
            
            if not usdt_market:
                return {
                    'agent': 'api_validator',
                    'status': 'ERROR',
                    'details': 'No USDT market found in Binance data'
                }
            
            # Get OI directly from Binance FAPI
            external_oi = await self._get_binance_oi_direct('BTCUSDT')
            
            if not external_oi:
                return {
                    'agent': 'api_validator',
                    'status': 'ERROR',
                    'details': 'Could not get external OI reference'
                }
            
            # Compare with Binance provider claim
            provider_oi = usdt_market['oi_tokens']
            deviation_pct = abs(provider_oi - external_oi) / external_oi * 100
            
            if deviation_pct < 10.0:  # Max 10% OI deviation
                status = 'PASS'
                details = f'OI validated: Provider {provider_oi:,.0f} vs API {external_oi:,.0f} ({deviation_pct:.1f}% deviation)'
            else:
                status = 'FAIL'
                details = f'OI mismatch: Provider {provider_oi:,.0f} vs API {external_oi:,.0f} ({deviation_pct:.1f}% deviation > 10%)'
            
            print(f"  Result: {status} - {details}")
            
            return {
                'agent': 'api_validator',
                'status': status,
                'details': details,
                'provider_oi': provider_oi,
                'external_oi': external_oi,
                'deviation_pct': deviation_pct
            }
            
        except Exception as e:
            return {
                'agent': 'api_validator',
                'status': 'ERROR',
                'details': f'API validation error: {str(e)}'
            }
    
    async def _counter_agent_magnitude_validation(self, binance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Counter-agent 4: Magnitude sanity validation"""
        try:
            print("🔍 Counter-Agent 4: Magnitude Validation")
            
            total_oi_usd = binance_data['total_oi_usd']
            
            # Known reasonable range for Binance BTC OI (from market data)
            # Binance typically has $5B-$15B in BTC OI
            min_reasonable = 5_000_000_000   # $5B
            max_reasonable = 25_000_000_000  # $25B
            
            if min_reasonable <= total_oi_usd <= max_reasonable:
                status = 'PASS'
                details = f'Total OI ${total_oi_usd/1e9:.1f}B within reasonable range ${min_reasonable/1e9:.0f}B-${max_reasonable/1e9:.0f}B'
            else:
                status = 'FAIL' 
                if total_oi_usd < min_reasonable:
                    details = f'Total OI ${total_oi_usd/1e9:.1f}B too low (< ${min_reasonable/1e9:.0f}B)'
                else:
                    details = f'Total OI ${total_oi_usd/1e9:.1f}B too high (> ${max_reasonable/1e9:.0f}B)'
            
            print(f"  Result: {status} - {details}")
            
            return {
                'agent': 'magnitude_validator',
                'status': status,
                'details': details,
                'total_oi_usd': total_oi_usd,
                'reasonable_range': f'${min_reasonable/1e9:.0f}B-${max_reasonable/1e9:.0f}B'
            }
            
        except Exception as e:
            return {
                'agent': 'magnitude_validator',
                'status': 'ERROR',
                'details': f'Magnitude validation error: {str(e)}'
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
    
    async def _get_binance_oi_direct(self, symbol: str) -> float:
        """Get OI directly from Binance API as external reference"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    return float(data['openInterest'])
        except:
            return None

async def main():
    """Run independent validation of Binance implementation"""
    print("🚨 INDEPENDENT VALIDATION: Testing Binance Claims")
    print("=" * 80)
    print("⚠️ WARNING: Do NOT trust self-validation - using counter-agents")
    print("=" * 80)
    
    # Get Binance provider data
    provider = BinanceOIProvider()
    
    try:
        result = await provider.get_oi_data('BTC')
        
        # Format data for validation
        binance_claims = {
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
        
        print(f"📊 BINANCE PROVIDER CLAIMS:")
        print(f"Total OI: {result.total_oi_tokens:,.0f} BTC (${result.total_oi_usd/1e9:.1f}B)")
        print(f"Markets: {len(result.markets)}")
        for market in result.markets:
            print(f"  {market.market_type.value}: {market.oi_tokens:,.0f} BTC (${market.oi_usd/1e9:.1f}B)")
        
        print(f"\n🛡️ DEPLOYING COUNTER-AGENTS FOR INDEPENDENT VALIDATION...")
        
        # Deploy counter-agents
        validator = BinanceCounterValidator()
        validation_report = await validator.validate_binance_claims(binance_claims)
        
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
        if validation_report['overall_status'] == 'TRUSTED':
            print(f"\n✅ VERDICT: Binance implementation validated by independent counter-agents")
            print(f"✅ SAFE TO PROCEED to next exchange implementation")
        elif validation_report['overall_status'] == 'CAUTIOUS':
            print(f"\n⚠️ VERDICT: Some issues found but generally acceptable")
            print(f"⚠️ REVIEW validation failures before proceeding")
        else:
            print(f"\n❌ VERDICT: Binance implementation REJECTED by counter-agents")
            print(f"❌ DO NOT PROCEED - Fix issues before continuing")
        
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