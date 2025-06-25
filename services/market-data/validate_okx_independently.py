#!/usr/bin/env python3
"""
INDEPENDENT OKX VALIDATION AGENT
Critical validation of OKX implementation to identify calculation errors
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

class OKXIndependentValidator:
    """
    Independent validation agent for OKX implementation
    Tests all calculations and API responses independently
    """
    
    def __init__(self):
        self.api_base = "https://www.okx.com"
        self.session = None
        
        # Expected reasonable ranges for BTC OI
        self.REASONABLE_BTC_OI_RANGES = {
            'total_btc_min': 50_000,      # 50K BTC minimum
            'total_btc_max': 500_000,     # 500K BTC maximum  
            'total_usd_min': 2e9,         # $2B minimum
            'total_usd_max': 50e9,        # $50B maximum
            'single_market_max': 200_000  # 200K BTC per market max
        }
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def validate_full_implementation(self, base_symbol: str = "BTC") -> Dict[str, Any]:
        """
        CRITICAL VALIDATION: Full independent verification
        """
        logger.info(f"🔍 INDEPENDENT VALIDATION: OKX {base_symbol}")
        
        validation_result = {
            'symbol': base_symbol,
            'timestamp': datetime.now().isoformat(),
            'api_responses': {},
            'calculations': {},
            'sanity_checks': {},
            'errors': [],
            'warnings': [],
            'verdict': 'UNKNOWN'
        }
        
        try:
            # 1. Direct API validation
            logger.info("📡 Step 1: Direct API validation")
            api_results = await self._validate_direct_apis(base_symbol)
            validation_result['api_responses'] = api_results
            
            # 2. Mathematical validation
            logger.info("🧮 Step 2: Mathematical validation")
            calc_results = await self._validate_calculations(api_results, base_symbol)
            validation_result['calculations'] = calc_results
            
            # 3. Sanity checks
            logger.info("🔍 Step 3: Sanity checks")
            sanity_results = self._perform_sanity_checks(calc_results, base_symbol)
            validation_result['sanity_checks'] = sanity_results
            
            # 4. Cross-validation with external data
            logger.info("🌐 Step 4: Cross-validation")
            cross_val_results = await self._cross_validate_external(base_symbol)
            validation_result['cross_validation'] = cross_val_results
            
            # 5. Final verdict
            validation_result['verdict'] = self._generate_verdict(validation_result)
            
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"Validation failed: {str(e)}")
            validation_result['verdict'] = 'FAILED'
            return validation_result
    
    async def _validate_direct_apis(self, base_symbol: str) -> Dict[str, Any]:
        """Direct API validation - raw responses"""
        session = await self.get_session()
        api_results = {}
        
        # Test all 3 market types
        symbols = {
            'usdt': f"{base_symbol}-USDT-SWAP",
            'usdc': f"{base_symbol}-USDC-SWAP", 
            'usd': f"{base_symbol}-USD-SWAP"
        }
        
        for market_type, symbol in symbols.items():
            try:
                logger.info(f"📡 Testing {market_type.upper()}: {symbol}")
                
                # OI endpoint
                oi_params = {"instType": "SWAP", "instId": symbol}
                async with session.get(f"{self.api_base}/api/v5/public/open-interest", params=oi_params) as response:
                    oi_response = await response.json()
                
                # Ticker endpoint
                ticker_params = {"instId": symbol}
                async with session.get(f"{self.api_base}/api/v5/market/ticker", params=ticker_params) as response:
                    ticker_response = await response.json()
                
                api_results[market_type] = {
                    'symbol': symbol,
                    'oi_response': oi_response,
                    'ticker_response': ticker_response,
                    'oi_valid': oi_response.get('code') == '0' and oi_response.get('data'),
                    'ticker_valid': ticker_response.get('code') == '0' and ticker_response.get('data')
                }
                
                logger.info(f"✅ {market_type.upper()} API: OI={'✅' if api_results[market_type]['oi_valid'] else '❌'} Ticker={'✅' if api_results[market_type]['ticker_valid'] else '❌'}")
                
            except Exception as e:
                api_results[market_type] = {
                    'symbol': symbol,
                    'error': str(e),
                    'oi_valid': False,
                    'ticker_valid': False
                }
                logger.error(f"❌ {market_type.upper()} API failed: {str(e)}")
        
        return api_results
    
    async def _validate_calculations(self, api_results: Dict, base_symbol: str) -> Dict[str, Any]:
        """Mathematical validation of all calculations"""
        calc_results = {}
        
        for market_type, api_data in api_results.items():
            if not api_data.get('oi_valid') or not api_data.get('ticker_valid'):
                continue
                
            try:
                oi_data = api_data['oi_response']['data'][0]
                ticker_data = api_data['ticker_response']['data'][0]
                price = float(ticker_data['last'])
                
                logger.info(f"🧮 Calculating {market_type.upper()}: Price=${price:,.2f}")
                
                # Extract raw OI values
                oi_raw = oi_data.get('oi', '0')
                oi_ccy_raw = oi_data.get('oiCcy', '0')
                
                calc_result = {
                    'price': price,
                    'oi_raw': oi_raw,
                    'oi_ccy_raw': oi_ccy_raw,
                    'calculations': {}
                }
                
                if market_type in ['usdt', 'usdc']:
                    # LINEAR CALCULATION
                    oi_tokens = float(oi_raw)
                    oi_usd = oi_tokens * price
                    
                    calc_result['calculations'] = {
                        'method': 'linear',
                        'oi_tokens': oi_tokens,
                        'oi_usd': oi_usd,
                        'formula': f"{oi_tokens:,.0f} tokens × ${price:,.2f} = ${oi_usd:,.0f}"
                    }
                    
                    logger.info(f"📊 {market_type.upper()} LINEAR: {oi_tokens:,.0f} {base_symbol} = ${oi_usd/1e9:.1f}B")
                    
                elif market_type == 'usd':
                    # INVERSE CALCULATION - Multiple methods
                    calc_result['calculations'] = {}
                    
                    # Method 1: oiCcy (preferred)
                    if float(oi_ccy_raw) > 0:
                        oi_tokens_method1 = float(oi_ccy_raw)
                        oi_usd_method1 = oi_tokens_method1 * price
                        calc_result['calculations']['method1_oiccy'] = {
                            'oi_tokens': oi_tokens_method1,
                            'oi_usd': oi_usd_method1,
                            'formula': f"oiCcy: {oi_tokens_method1:,.0f} {base_symbol} × ${price:,.2f} = ${oi_usd_method1:,.0f}"
                        }
                        logger.info(f"📊 USD Method 1 (oiCcy): {oi_tokens_method1:,.0f} {base_symbol} = ${oi_usd_method1/1e9:.1f}B")
                    
                    # Method 2: contracts conversion
                    if float(oi_raw) > 0:
                        oi_contracts = float(oi_raw)
                        contract_value_usd = 100.0  # $100 per contract
                        oi_usd_from_contracts = oi_contracts * contract_value_usd
                        oi_tokens_method2 = oi_usd_from_contracts / price
                        
                        calc_result['calculations']['method2_contracts'] = {
                            'oi_contracts': oi_contracts,
                            'oi_tokens': oi_tokens_method2,
                            'oi_usd': oi_usd_from_contracts,
                            'formula': f"contracts: {oi_contracts:,.0f} × $100 = ${oi_usd_from_contracts:,.0f}, tokens: ${oi_usd_from_contracts:,.0f} ÷ ${price:,.2f} = {oi_tokens_method2:,.0f}"
                        }
                        logger.info(f"📊 USD Method 2 (contracts): {oi_tokens_method2:,.0f} {base_symbol} = ${oi_usd_from_contracts/1e9:.1f}B")
                
                calc_results[market_type] = calc_result
                
            except Exception as e:
                calc_results[market_type] = {'error': str(e)}
                logger.error(f"❌ Calculation failed for {market_type}: {str(e)}")
        
        return calc_results
    
    def _perform_sanity_checks(self, calc_results: Dict, base_symbol: str) -> Dict[str, Any]:
        """Critical sanity checks against known reasonable ranges"""
        sanity_results = {
            'individual_markets': {},
            'totals': {},
            'flags': [],
            'passed': True
        }
        
        total_tokens = 0
        total_usd = 0
        
        # Check individual markets
        for market_type, calc_data in calc_results.items():
            if 'error' in calc_data:
                continue
                
            market_checks = {'passed': True, 'issues': []}
            
            if market_type in ['usdt', 'usdc']:
                # Linear markets
                oi_tokens = calc_data['calculations']['oi_tokens']
                oi_usd = calc_data['calculations']['oi_usd']
                
                # Check for unrealistic values
                if oi_tokens > self.REASONABLE_BTC_OI_RANGES['single_market_max']:
                    market_checks['issues'].append(f"EXCESSIVE OI: {oi_tokens:,.0f} tokens > {self.REASONABLE_BTC_OI_RANGES['single_market_max']:,.0f} max")
                    market_checks['passed'] = False
                
                if oi_usd > 100e9:  # $100B per market is unrealistic
                    market_checks['issues'].append(f"EXCESSIVE USD: ${oi_usd/1e9:.1f}B > $100B max")
                    market_checks['passed'] = False
                
                total_tokens += oi_tokens
                total_usd += oi_usd
                
            elif market_type == 'usd':
                # Inverse market - check both methods
                for method_name, method_data in calc_data['calculations'].items():
                    if 'oi_tokens' in method_data:
                        oi_tokens = method_data['oi_tokens']
                        oi_usd = method_data['oi_usd']
                        
                        if oi_tokens > self.REASONABLE_BTC_OI_RANGES['single_market_max']:
                            market_checks['issues'].append(f"{method_name} EXCESSIVE OI: {oi_tokens:,.0f} tokens")
                            market_checks['passed'] = False
                        
                        # Use method1 (oiCcy) for totals if available
                        if method_name == 'method1_oiccy':
                            total_tokens += oi_tokens
                            total_usd += oi_usd
                        elif method_name == 'method2_contracts' and 'method1_oiccy' not in calc_data['calculations']:
                            total_tokens += oi_tokens
                            total_usd += oi_usd
            
            sanity_results['individual_markets'][market_type] = market_checks
            if not market_checks['passed']:
                sanity_results['passed'] = False
        
        # Check totals
        total_checks = {'passed': True, 'issues': []}
        
        if total_tokens > self.REASONABLE_BTC_OI_RANGES['total_btc_max']:
            total_checks['issues'].append(f"TOTAL OI EXCESSIVE: {total_tokens:,.0f} BTC > {self.REASONABLE_BTC_OI_RANGES['total_btc_max']:,.0f} max")
            total_checks['passed'] = False
            
        if total_usd > self.REASONABLE_BTC_OI_RANGES['total_usd_max']:
            total_checks['issues'].append(f"TOTAL USD EXCESSIVE: ${total_usd/1e9:.1f}B > ${self.REASONABLE_BTC_OI_RANGES['total_usd_max']/1e9:.1f}B max")
            total_checks['passed'] = False
        
        sanity_results['totals'] = {
            'total_tokens': total_tokens,
            'total_usd': total_usd,
            'checks': total_checks
        }
        
        if not total_checks['passed']:
            sanity_results['passed'] = False
        
        # Generate flags
        if not sanity_results['passed']:
            sanity_results['flags'].append("SANITY_CHECK_FAILED")
            
        logger.info(f"🔍 SANITY CHECK: {'✅ PASSED' if sanity_results['passed'] else '❌ FAILED'}")
        logger.info(f"📊 Calculated totals: {total_tokens:,.0f} BTC (${total_usd/1e9:.1f}B)")
        
        return sanity_results
    
    async def _cross_validate_external(self, base_symbol: str) -> Dict[str, Any]:
        """Cross-validate with external reference data"""
        # For now, return placeholder - could add CoinGlass or other sources
        return {
            'external_sources': [],
            'comparisons': {},
            'notes': 'External validation not implemented - would compare with CoinGlass, etc.'
        }
    
    def _generate_verdict(self, validation_result: Dict) -> str:
        """Generate final verdict based on all validation steps"""
        errors = validation_result.get('errors', [])
        sanity_passed = validation_result.get('sanity_checks', {}).get('passed', False)
        
        if errors:
            return 'FAILED'
        elif not sanity_passed:
            return 'REJECTED_UNREALISTIC'
        else:
            return 'PASSED'
    
    def print_detailed_report(self, validation_result: Dict):
        """Print comprehensive validation report"""
        print("\n" + "="*80)
        print("🔍 INDEPENDENT OKX VALIDATION REPORT")
        print("="*80)
        
        print(f"Symbol: {validation_result['symbol']}")
        print(f"Timestamp: {validation_result['timestamp']}")
        print(f"Verdict: {validation_result['verdict']}")
        
        # API Results
        print(f"\n📡 API VALIDATION:")
        for market_type, api_data in validation_result.get('api_responses', {}).items():
            if 'error' in api_data:
                print(f"  {market_type.upper()}: ❌ {api_data['error']}")
            else:
                print(f"  {market_type.upper()}: OI={'✅' if api_data['oi_valid'] else '❌'} Ticker={'✅' if api_data['ticker_valid'] else '❌'}")
        
        # Calculations
        print(f"\n🧮 CALCULATION VALIDATION:")
        for market_type, calc_data in validation_result.get('calculations', {}).items():
            if 'error' in calc_data:
                print(f"  {market_type.upper()}: ❌ {calc_data['error']}")
            else:
                print(f"  {market_type.upper()}: Price=${calc_data['price']:,.2f}")
                if market_type in ['usdt', 'usdc']:
                    calc = calc_data['calculations']
                    print(f"    {calc['formula']}")
                elif market_type == 'usd':
                    for method_name, method_data in calc_data['calculations'].items():
                        print(f"    {method_name}: {method_data['formula']}")
        
        # Sanity Checks
        print(f"\n🔍 SANITY CHECKS:")
        sanity = validation_result.get('sanity_checks', {})
        print(f"  Overall: {'✅ PASSED' if sanity.get('passed') else '❌ FAILED'}")
        
        totals = sanity.get('totals', {})
        if totals:
            print(f"  Total calculated: {totals['total_tokens']:,.0f} BTC (${totals['total_usd']/1e9:.1f}B)")
            
        for market_type, market_check in sanity.get('individual_markets', {}).items():
            if not market_check['passed']:
                print(f"  {market_type.upper()} issues: {market_check['issues']}")
        
        if not sanity.get('passed'):
            total_issues = totals.get('checks', {}).get('issues', [])
            for issue in total_issues:
                print(f"  ⚠️ {issue}")
        
        # Verdict explanation
        print(f"\n🎯 VERDICT EXPLANATION:")
        if validation_result['verdict'] == 'REJECTED_UNREALISTIC':
            print("  ❌ IMPLEMENTATION REJECTED: Values exceed realistic ranges")
            print("  💡 Likely issues: Calculation errors in linear market handling")
            print("  🔧 Recommendation: Review OI calculation logic, especially for USDT/USDC markets")
        elif validation_result['verdict'] == 'FAILED':
            print("  ❌ VALIDATION FAILED: Technical errors in implementation")
        elif validation_result['verdict'] == 'PASSED':
            print("  ✅ VALIDATION PASSED: Implementation appears correct")
        
        print("="*80)

# Main validation function
async def run_independent_validation():
    """Run complete independent validation"""
    logger.info("🚀 Starting Independent OKX Validation")
    
    validator = OKXIndependentValidator()
    
    try:
        # Run full validation
        result = await validator.validate_full_implementation("BTC")
        
        # Print detailed report
        validator.print_detailed_report(result)
        
        # Save results
        with open('/tmp/okx_validation_results.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info("📊 Validation results saved to /tmp/okx_validation_results.json")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await validator.close()

if __name__ == "__main__":
    asyncio.run(run_independent_validation())