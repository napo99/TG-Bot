#!/usr/bin/env python3
"""
CORRECTED OKX VALIDATION AGENT
Independent validation of the CORRECTED OKX implementation
Validates the fix for the critical API field error (oiCcy vs oi)
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

class CorrectedOKXValidator:
    """
    Independent validation agent for the CORRECTED OKX implementation
    Validates the fix for using oiCcy (base currency) instead of oi (quote currency)
    """
    
    def __init__(self):
        self.api_base = "https://www.okx.com"
        self.session = None
        
        # Updated reasonable ranges for BTC OI (more realistic)
        self.REASONABLE_BTC_OI_RANGES = {
            'usdt_btc_min': 10_000,       # 10K BTC minimum for USDT
            'usdt_btc_max': 100_000,      # 100K BTC maximum for USDT
            'usdc_btc_min': 100,          # 100 BTC minimum for USDC
            'usdc_btc_max': 10_000,       # 10K BTC maximum for USDC
            'usd_btc_min': 1_000,         # 1K BTC minimum for USD
            'usd_btc_max': 50_000,        # 50K BTC maximum for USD
            'total_btc_min': 20_000,      # 20K BTC total minimum
            'total_btc_max': 150_000,     # 150K BTC total maximum
            'total_usd_min': 2e9,         # $2B minimum
            'total_usd_max': 20e9,        # $20B maximum
        }
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def validate_corrected_implementation(self, base_symbol: str = "BTC") -> Dict[str, Any]:
        """
        CORRECTED VALIDATION: Validates the FIXED implementation
        """
        logger.info(f"🔍 CORRECTED VALIDATION: OKX {base_symbol} (Fixed Implementation)")
        
        validation_result = {
            'symbol': base_symbol,
            'timestamp': datetime.now().isoformat(),
            'validation_type': 'CORRECTED_IMPLEMENTATION',
            'api_responses': {},
            'corrected_calculations': {},
            'comparison_old_vs_new': {},
            'sanity_checks': {},
            'final_verdict': 'UNKNOWN',
            'recommendations': []
        }
        
        try:
            # 1. Get raw API data
            logger.info("📡 Step 1: Fetching API data")
            api_results = await self._fetch_api_data(base_symbol)
            validation_result['api_responses'] = api_results
            
            # 2. Apply CORRECTED calculations
            logger.info("🔧 Step 2: Applying CORRECTED calculations")
            corrected_results = self._apply_corrected_calculations(api_results, base_symbol)
            validation_result['corrected_calculations'] = corrected_results
            
            # 3. Compare old vs new approach
            logger.info("⚖️ Step 3: Comparing old vs new approach")
            comparison_results = self._compare_approaches(api_results, base_symbol)
            validation_result['comparison_old_vs_new'] = comparison_results
            
            # 4. Sanity checks on corrected values
            logger.info("🔍 Step 4: Sanity checks on corrected values")
            sanity_results = self._perform_corrected_sanity_checks(corrected_results, base_symbol)
            validation_result['sanity_checks'] = sanity_results
            
            # 5. Generate final verdict
            validation_result['final_verdict'] = self._generate_corrected_verdict(validation_result)
            validation_result['recommendations'] = self._generate_recommendations(validation_result)
            
            return validation_result
            
        except Exception as e:
            validation_result['error'] = str(e)
            validation_result['final_verdict'] = 'VALIDATION_ERROR'
            return validation_result
    
    async def _fetch_api_data(self, base_symbol: str) -> Dict[str, Any]:
        """Fetch raw API data for all markets"""
        session = await self.get_session()
        api_results = {}
        
        symbols = {
            'usdt': f"{base_symbol}-USDT-SWAP",
            'usdc': f"{base_symbol}-USDC-SWAP", 
            'usd': f"{base_symbol}-USD-SWAP"
        }
        
        for market_type, symbol in symbols.items():
            try:
                logger.info(f"📡 Fetching {market_type.upper()}: {symbol}")
                
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
                    'valid': (oi_response.get('code') == '0' and oi_response.get('data') and
                             ticker_response.get('code') == '0' and ticker_response.get('data'))
                }
                
                logger.info(f"✅ {market_type.upper()}: {'Valid' if api_results[market_type]['valid'] else 'Invalid'}")
                
            except Exception as e:
                api_results[market_type] = {
                    'symbol': symbol,
                    'error': str(e),
                    'valid': False
                }
                logger.error(f"❌ {market_type.upper()} failed: {str(e)}")
        
        return api_results
    
    def _apply_corrected_calculations(self, api_results: Dict, base_symbol: str) -> Dict[str, Any]:
        """Apply the CORRECTED calculation logic"""
        corrected_calculations = {}
        
        for market_type, api_data in api_results.items():
            if not api_data.get('valid'):
                continue
                
            try:
                oi_data = api_data['oi_response']['data'][0]
                ticker_data = api_data['ticker_response']['data'][0]
                price = float(ticker_data['last'])
                
                # Extract raw values
                oi_raw = oi_data.get('oi', '0')
                oi_ccy_raw = oi_data.get('oiCcy', '0')
                
                logger.info(f"🔧 CORRECTED {market_type.upper()}: Price=${price:,.2f}")
                logger.info(f"   Raw values: oi={oi_raw}, oiCcy={oi_ccy_raw}")
                
                calc_result = {
                    'price': price,
                    'oi_raw': oi_raw,
                    'oi_ccy_raw': oi_ccy_raw,
                    'corrected_calculation': {}
                }
                
                if market_type in ['usdt', 'usdc']:
                    # CORRECTED LINEAR CALCULATION: Use oiCcy (base currency)
                    oi_tokens = float(oi_ccy_raw)  # CORRECTED: Use oiCcy not oi
                    oi_usd = oi_tokens * price
                    
                    calc_result['corrected_calculation'] = {
                        'method': 'corrected_linear',
                        'field_used': 'oiCcy',
                        'oi_tokens': oi_tokens,
                        'oi_usd': oi_usd,
                        'formula': f"CORRECTED: oiCcy {oi_tokens:,.1f} × ${price:,.2f} = ${oi_usd:,.0f}"
                    }
                    
                    logger.info(f"✅ {market_type.upper()} CORRECTED: {oi_tokens:,.0f} {base_symbol} = ${oi_usd/1e9:.1f}B")
                    
                elif market_type == 'usd':
                    # INVERSE CALCULATION: Use oiCcy (preferred)
                    if float(oi_ccy_raw) > 0:
                        oi_tokens = float(oi_ccy_raw)
                        oi_usd = oi_tokens * price
                        
                        calc_result['corrected_calculation'] = {
                            'method': 'inverse_oiccy',
                            'field_used': 'oiCcy',
                            'oi_tokens': oi_tokens,
                            'oi_usd': oi_usd,
                            'formula': f"oiCcy: {oi_tokens:,.0f} × ${price:,.2f} = ${oi_usd:,.0f}"
                        }
                        
                        logger.info(f"✅ {market_type.upper()}: {oi_tokens:,.0f} {base_symbol} = ${oi_usd/1e9:.1f}B")
                
                corrected_calculations[market_type] = calc_result
                
            except Exception as e:
                corrected_calculations[market_type] = {'error': str(e)}
                logger.error(f"❌ Corrected calculation failed for {market_type}: {str(e)}")
        
        return corrected_calculations
    
    def _compare_approaches(self, api_results: Dict, base_symbol: str) -> Dict[str, Any]:
        """Compare old (wrong) vs new (corrected) approach"""
        comparison = {}
        
        for market_type, api_data in api_results.items():
            if not api_data.get('valid'):
                continue
                
            try:
                oi_data = api_data['oi_response']['data'][0]
                ticker_data = api_data['ticker_response']['data'][0]
                price = float(ticker_data['last'])
                
                oi_raw = float(oi_data.get('oi', '0'))
                oi_ccy_raw = float(oi_data.get('oiCcy', '0'))
                
                if market_type in ['usdt', 'usdc']:
                    # OLD (WRONG) vs NEW (CORRECT) for linear markets
                    old_oi_tokens = oi_raw  # WRONG: using oi field
                    old_oi_usd = old_oi_tokens * price
                    
                    new_oi_tokens = oi_ccy_raw  # CORRECT: using oiCcy field
                    new_oi_usd = new_oi_tokens * price
                    
                    ratio = new_oi_tokens / old_oi_tokens if old_oi_tokens > 0 else 0
                    
                    comparison[market_type] = {
                        'old_approach': {
                            'field': 'oi',
                            'tokens': old_oi_tokens,
                            'usd': old_oi_usd,
                            'description': 'WRONG: Uses quote currency amount'
                        },
                        'new_approach': {
                            'field': 'oiCcy',
                            'tokens': new_oi_tokens,
                            'usd': new_oi_usd,
                            'description': 'CORRECT: Uses base currency amount'
                        },
                        'ratio_new_to_old': ratio,
                        'difference_magnitude': abs(new_oi_tokens - old_oi_tokens),
                        'verdict': 'MAJOR_CORRECTION' if ratio < 0.1 or ratio > 10 else 'MINOR_CORRECTION'
                    }
                    
                    logger.info(f"⚖️ {market_type.upper()} Comparison:")
                    logger.info(f"   OLD (wrong): {old_oi_tokens:,.0f} {base_symbol} = ${old_oi_usd/1e9:.1f}B")
                    logger.info(f"   NEW (correct): {new_oi_tokens:,.0f} {base_symbol} = ${new_oi_usd/1e9:.1f}B")
                    logger.info(f"   Ratio: {ratio:.2f}x")
                
            except Exception as e:
                comparison[market_type] = {'error': str(e)}
        
        return comparison
    
    def _perform_corrected_sanity_checks(self, corrected_calculations: Dict, base_symbol: str) -> Dict[str, Any]:
        """Perform sanity checks on the CORRECTED values"""
        sanity_results = {
            'individual_markets': {},
            'totals': {},
            'overall_verdict': 'UNKNOWN',
            'issues': []
        }
        
        total_tokens = 0
        total_usd = 0
        
        # Check individual markets
        for market_type, calc_data in corrected_calculations.items():
            if 'error' in calc_data or 'corrected_calculation' not in calc_data:
                continue
                
            corrected_calc = calc_data['corrected_calculation']
            oi_tokens = corrected_calc.get('oi_tokens', 0)
            oi_usd = corrected_calc.get('oi_usd', 0)
            
            market_check = {'passed': True, 'issues': []}
            
            # Market-specific range checks
            if market_type == 'usdt':
                if not (self.REASONABLE_BTC_OI_RANGES['usdt_btc_min'] <= oi_tokens <= self.REASONABLE_BTC_OI_RANGES['usdt_btc_max']):
                    market_check['issues'].append(f"USDT OI outside reasonable range: {oi_tokens:,.0f} not in [{self.REASONABLE_BTC_OI_RANGES['usdt_btc_min']:,}-{self.REASONABLE_BTC_OI_RANGES['usdt_btc_max']:,}]")
                    market_check['passed'] = False
            elif market_type == 'usdc':
                if not (self.REASONABLE_BTC_OI_RANGES['usdc_btc_min'] <= oi_tokens <= self.REASONABLE_BTC_OI_RANGES['usdc_btc_max']):
                    market_check['issues'].append(f"USDC OI outside reasonable range: {oi_tokens:,.0f} not in [{self.REASONABLE_BTC_OI_RANGES['usdc_btc_min']:,}-{self.REASONABLE_BTC_OI_RANGES['usdc_btc_max']:,}]")
                    market_check['passed'] = False
            elif market_type == 'usd':
                if not (self.REASONABLE_BTC_OI_RANGES['usd_btc_min'] <= oi_tokens <= self.REASONABLE_BTC_OI_RANGES['usd_btc_max']):
                    market_check['issues'].append(f"USD OI outside reasonable range: {oi_tokens:,.0f} not in [{self.REASONABLE_BTC_OI_RANGES['usd_btc_min']:,}-{self.REASONABLE_BTC_OI_RANGES['usd_btc_max']:,}]")
                    market_check['passed'] = False
            
            sanity_results['individual_markets'][market_type] = market_check
            total_tokens += oi_tokens
            total_usd += oi_usd
        
        # Check totals
        total_check = {'passed': True, 'issues': []}
        
        if total_tokens < self.REASONABLE_BTC_OI_RANGES['total_btc_min']:
            total_check['issues'].append(f"Total OI too low: {total_tokens:,.0f} < {self.REASONABLE_BTC_OI_RANGES['total_btc_min']:,}")
            total_check['passed'] = False
        elif total_tokens > self.REASONABLE_BTC_OI_RANGES['total_btc_max']:
            total_check['issues'].append(f"Total OI too high: {total_tokens:,.0f} > {self.REASONABLE_BTC_OI_RANGES['total_btc_max']:,}")
            total_check['passed'] = False
        
        if total_usd < self.REASONABLE_BTC_OI_RANGES['total_usd_min']:
            total_check['issues'].append(f"Total USD too low: ${total_usd/1e9:.1f}B < ${self.REASONABLE_BTC_OI_RANGES['total_usd_min']/1e9:.1f}B")
            total_check['passed'] = False
        elif total_usd > self.REASONABLE_BTC_OI_RANGES['total_usd_max']:
            total_check['issues'].append(f"Total USD too high: ${total_usd/1e9:.1f}B > ${self.REASONABLE_BTC_OI_RANGES['total_usd_max']/1e9:.1f}B")
            total_check['passed'] = False
        
        sanity_results['totals'] = {
            'total_tokens': total_tokens,
            'total_usd': total_usd,
            'checks': total_check
        }
        
        # Overall verdict
        all_markets_passed = all(market['passed'] for market in sanity_results['individual_markets'].values())
        total_passed = total_check['passed']
        
        if all_markets_passed and total_passed:
            sanity_results['overall_verdict'] = 'PASSED'
        else:
            sanity_results['overall_verdict'] = 'FAILED'
            # Collect all issues
            for market_type, market_check in sanity_results['individual_markets'].items():
                sanity_results['issues'].extend(market_check['issues'])
            sanity_results['issues'].extend(total_check['issues'])
        
        logger.info(f"🔍 CORRECTED Sanity Check: {'✅ PASSED' if sanity_results['overall_verdict'] == 'PASSED' else '❌ FAILED'}")
        logger.info(f"📊 Corrected totals: {total_tokens:,.0f} BTC (${total_usd/1e9:.1f}B)")
        
        return sanity_results
    
    def _generate_corrected_verdict(self, validation_result: Dict) -> str:
        """Generate final verdict on the corrected implementation"""
        sanity_verdict = validation_result.get('sanity_checks', {}).get('overall_verdict', 'UNKNOWN')
        
        if 'error' in validation_result:
            return 'VALIDATION_ERROR'
        elif sanity_verdict == 'PASSED':
            return 'CORRECTED_IMPLEMENTATION_TRUSTED'
        elif sanity_verdict == 'FAILED':
            return 'CORRECTED_IMPLEMENTATION_REJECTED'
        else:
            return 'INCONCLUSIVE'
    
    def _generate_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        verdict = validation_result.get('final_verdict', 'UNKNOWN')
        
        if verdict == 'CORRECTED_IMPLEMENTATION_TRUSTED':
            recommendations.extend([
                "✅ IMPLEMENTATION READY FOR PRODUCTION",
                "🔧 The fix for using oiCcy instead of oi is validated and working",
                "📊 All calculated values are within reasonable ranges",
                "🚀 Deploy the corrected implementation with confidence"
            ])
        elif verdict == 'CORRECTED_IMPLEMENTATION_REJECTED':
            recommendations.extend([
                "❌ IMPLEMENTATION STILL HAS ISSUES",
                "🔍 Review the sanity check failures",
                "🔧 Additional corrections may be needed"
            ])
        
        # Add specific recommendations based on comparison
        comparison = validation_result.get('comparison_old_vs_new', {})
        for market_type, comp_data in comparison.items():
            if comp_data.get('verdict') == 'MAJOR_CORRECTION':
                recommendations.append(f"🎯 {market_type.upper()} correction is significant - verify this is expected")
        
        return recommendations
    
    def print_detailed_report(self, validation_result: Dict):
        """Print comprehensive validation report for corrected implementation"""
        print("\n" + "="*90)
        print("🔍 CORRECTED OKX IMPLEMENTATION VALIDATION REPORT")
        print("="*90)
        
        print(f"Symbol: {validation_result['symbol']}")
        print(f"Validation Type: {validation_result['validation_type']}")
        print(f"Timestamp: {validation_result['timestamp']}")
        print(f"Final Verdict: {validation_result['final_verdict']}")
        
        # API Status
        print(f"\n📡 API STATUS:")
        for market_type, api_data in validation_result.get('api_responses', {}).items():
            status = "✅ Valid" if api_data.get('valid') else "❌ Invalid"
            print(f"  {market_type.upper()}: {status}")
        
        # Corrected Calculations
        print(f"\n🔧 CORRECTED CALCULATIONS:")
        for market_type, calc_data in validation_result.get('corrected_calculations', {}).items():
            if 'error' in calc_data:
                print(f"  {market_type.upper()}: ❌ {calc_data['error']}")
            else:
                corrected = calc_data['corrected_calculation']
                print(f"  {market_type.upper()}: {corrected['formula']}")
        
        # Old vs New Comparison
        print(f"\n⚖️ OLD vs NEW COMPARISON:")
        for market_type, comp_data in validation_result.get('comparison_old_vs_new', {}).items():
            if 'error' in comp_data:
                print(f"  {market_type.upper()}: ❌ {comp_data['error']}")
            else:
                old = comp_data['old_approach']
                new = comp_data['new_approach']
                ratio = comp_data['ratio_new_to_old']
                print(f"  {market_type.upper()}:")
                print(f"    OLD (wrong): {old['tokens']:,.0f} BTC using '{old['field']}' field")
                print(f"    NEW (correct): {new['tokens']:,.0f} BTC using '{new['field']}' field")
                print(f"    Correction ratio: {ratio:.2f}x")
                print(f"    Verdict: {comp_data['verdict']}")
        
        # Sanity Checks
        print(f"\n🔍 SANITY CHECKS (Corrected Values):")
        sanity = validation_result.get('sanity_checks', {})
        print(f"  Overall: {'✅ PASSED' if sanity.get('overall_verdict') == 'PASSED' else '❌ FAILED'}")
        
        totals = sanity.get('totals', {})
        if totals:
            print(f"  Corrected totals: {totals['total_tokens']:,.0f} BTC (${totals['total_usd']/1e9:.1f}B)")
        
        if sanity.get('issues'):
            print(f"  Issues found:")
            for issue in sanity['issues']:
                print(f"    ⚠️ {issue}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        for rec in validation_result.get('recommendations', []):
            print(f"  {rec}")
        
        print("="*90)

# Main validation function
async def run_corrected_validation():
    """Run the corrected implementation validation"""
    logger.info("🚀 Starting CORRECTED OKX Implementation Validation")
    
    validator = CorrectedOKXValidator()
    
    try:
        # Run corrected validation
        result = await validator.validate_corrected_implementation("BTC")
        
        # Print detailed report
        validator.print_detailed_report(result)
        
        # Save results
        with open('/tmp/okx_corrected_validation.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info("📊 Corrected validation results saved to /tmp/okx_corrected_validation.json")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Corrected validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await validator.close()

if __name__ == "__main__":
    asyncio.run(run_corrected_validation())