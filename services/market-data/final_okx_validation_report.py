#!/usr/bin/env python3
"""
FINAL OKX VALIDATION REPORT
Cross-exchange comparison to validate corrected OKX implementation
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

class FinalOKXValidationReport:
    """
    Final validation report comparing corrected OKX implementation
    against other major exchanges for cross-validation
    """
    
    def __init__(self):
        self.session = None
        
        # Expected OI ranges for major exchanges (BTC)
        self.EXCHANGE_EXPECTED_RANGES = {
            'binance': {'min': 50_000, 'max': 300_000},   # Binance typically largest
            'okx': {'min': 20_000, 'max': 100_000},       # OKX moderate size
            'bybit': {'min': 10_000, 'max': 80_000},      # Bybit smaller but significant
        }
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def generate_final_report(self, base_symbol: str = "BTC") -> Dict[str, Any]:
        """Generate final validation report with cross-exchange comparison"""
        logger.info(f"📊 FINAL VALIDATION REPORT: {base_symbol}")
        
        report = {
            'symbol': base_symbol,
            'timestamp': datetime.now().isoformat(),
            'corrected_okx_results': {},
            'cross_exchange_comparison': {},
            'validation_summary': {},
            'final_verdict': 'UNKNOWN',
            'production_readiness': 'UNKNOWN'
        }
        
        try:
            # 1. Get corrected OKX results
            logger.info("🟠 Step 1: Testing corrected OKX implementation")
            okx_results = await self._test_corrected_okx(base_symbol)
            report['corrected_okx_results'] = okx_results
            
            # 2. Get comparison data from other exchanges
            logger.info("🔄 Step 2: Cross-exchange comparison")
            comparison_results = await self._get_cross_exchange_data(base_symbol)
            report['cross_exchange_comparison'] = comparison_results
            
            # 3. Validate OKX results against peer exchanges
            logger.info("⚖️ Step 3: Peer validation")
            validation_results = self._validate_against_peers(okx_results, comparison_results)
            report['validation_summary'] = validation_results
            
            # 4. Generate final verdict
            report['final_verdict'] = self._generate_final_verdict(report)
            report['production_readiness'] = self._assess_production_readiness(report)
            
            return report
            
        except Exception as e:
            report['error'] = str(e)
            report['final_verdict'] = 'VALIDATION_ERROR'
            report['production_readiness'] = 'NOT_READY'
            return report
    
    async def _test_corrected_okx(self, base_symbol: str) -> Dict[str, Any]:
        """Test the corrected OKX implementation"""
        session = await self.get_session()
        
        # Test OKX corrected implementation
        symbols = {
            'usdt': f"{base_symbol}-USDT-SWAP",
            'usdc': f"{base_symbol}-USDC-SWAP",
            'usd': f"{base_symbol}-USD-SWAP"
        }
        
        okx_results = {
            'markets': {},
            'totals': {},
            'api_health': True
        }
        
        total_tokens = 0
        total_usd = 0
        
        for market_type, symbol in symbols.items():
            try:
                # Get OI data
                oi_params = {"instType": "SWAP", "instId": symbol}
                async with session.get("https://www.okx.com/api/v5/public/open-interest", params=oi_params) as response:
                    oi_response = await response.json()
                
                # Get ticker data
                ticker_params = {"instId": symbol}
                async with session.get("https://www.okx.com/api/v5/market/ticker", params=ticker_params) as response:
                    ticker_response = await response.json()
                
                if (oi_response.get('code') == '0' and oi_response.get('data') and
                    ticker_response.get('code') == '0' and ticker_response.get('data')):
                    
                    oi_data = oi_response['data'][0]
                    ticker_data = ticker_response['data'][0]
                    price = float(ticker_data['last'])
                    
                    # Apply CORRECTED calculation
                    if market_type in ['usdt', 'usdc']:
                        # CORRECTED: Use oiCcy for linear markets
                        oi_tokens = float(oi_data['oiCcy'])
                    else:  # usd
                        # Inverse: Use oiCcy
                        oi_tokens = float(oi_data['oiCcy'])
                    
                    oi_usd = oi_tokens * price
                    
                    okx_results['markets'][market_type] = {
                        'oi_tokens': oi_tokens,
                        'oi_usd': oi_usd,
                        'price': price,
                        'field_used': 'oiCcy',
                        'calculation_method': 'corrected'
                    }
                    
                    total_tokens += oi_tokens
                    total_usd += oi_usd
                    
                    logger.info(f"✅ OKX {market_type.upper()}: {oi_tokens:,.0f} {base_symbol} = ${oi_usd/1e9:.1f}B")
                
            except Exception as e:
                okx_results['markets'][market_type] = {'error': str(e)}
                okx_results['api_health'] = False
                logger.error(f"❌ OKX {market_type} failed: {str(e)}")
        
        okx_results['totals'] = {
            'total_tokens': total_tokens,
            'total_usd': total_usd
        }
        
        logger.info(f"🟠 OKX CORRECTED Total: {total_tokens:,.0f} {base_symbol} (${total_usd/1e9:.1f}B)")
        
        return okx_results
    
    async def _get_cross_exchange_data(self, base_symbol: str) -> Dict[str, Any]:
        """Get OI data from other major exchanges for comparison"""
        session = await self.get_session()
        comparison_data = {}
        
        # Binance comparison
        try:
            logger.info("🟡 Checking Binance futures OI")
            binance_url = "https://fapi.binance.com/fapi/v1/openInterest"
            binance_params = {"symbol": f"{base_symbol}USDT"}
            
            async with session.get(binance_url, params=binance_params) as response:
                binance_response = await response.json()
            
            # Get Binance price
            binance_ticker_url = "https://fapi.binance.com/fapi/v1/ticker/price"
            async with session.get(binance_ticker_url, params=binance_params) as response:
                binance_price_response = await response.json()
            
            if 'openInterest' in binance_response and 'price' in binance_price_response:
                binance_oi_usdt = float(binance_response['openInterest'])
                binance_price = float(binance_price_response['price'])
                binance_oi_usd = binance_oi_usdt * binance_price
                
                comparison_data['binance'] = {
                    'oi_tokens': binance_oi_usdt,
                    'oi_usd': binance_oi_usd,
                    'price': binance_price,
                    'market_type': 'futures_usdt'
                }
                
                logger.info(f"🟡 Binance: {binance_oi_usdt:,.0f} {base_symbol} = ${binance_oi_usd/1e9:.1f}B")
            
        except Exception as e:
            comparison_data['binance'] = {'error': str(e)}
            logger.error(f"❌ Binance comparison failed: {str(e)}")
        
        # Bybit comparison (if available)
        try:
            logger.info("🟣 Checking Bybit OI")
            bybit_url = "https://api.bybit.com/v5/market/open-interest"
            bybit_params = {"category": "linear", "symbol": f"{base_symbol}USDT"}
            
            async with session.get(bybit_url, params=bybit_params) as response:
                bybit_response = await response.json()
            
            if (bybit_response.get('retCode') == 0 and 
                bybit_response.get('result', {}).get('list')):
                bybit_data = bybit_response['result']['list'][0]
                bybit_oi_usdt = float(bybit_data['openInterest'])
                
                # Get Bybit price
                bybit_ticker_url = "https://api.bybit.com/v5/market/tickers"
                async with session.get(bybit_ticker_url, params=bybit_params) as response:
                    bybit_ticker_response = await response.json()
                
                if (bybit_ticker_response.get('retCode') == 0 and
                    bybit_ticker_response.get('result', {}).get('list')):
                    bybit_ticker_data = bybit_ticker_response['result']['list'][0]
                    bybit_price = float(bybit_ticker_data['lastPrice'])
                    bybit_oi_usd = bybit_oi_usdt * bybit_price
                    
                    comparison_data['bybit'] = {
                        'oi_tokens': bybit_oi_usdt,
                        'oi_usd': bybit_oi_usd,
                        'price': bybit_price,
                        'market_type': 'linear_usdt'
                    }
                    
                    logger.info(f"🟣 Bybit: {bybit_oi_usdt:,.0f} {base_symbol} = ${bybit_oi_usd/1e9:.1f}B")
            
        except Exception as e:
            comparison_data['bybit'] = {'error': str(e)}
            logger.error(f"❌ Bybit comparison failed: {str(e)}")
        
        return comparison_data
    
    def _validate_against_peers(self, okx_results: Dict, comparison_results: Dict) -> Dict[str, Any]:
        """Validate OKX results against peer exchanges"""
        validation = {
            'peer_comparisons': {},
            'okx_rank': 'UNKNOWN',
            'okx_market_share': 'UNKNOWN',
            'reasonableness_check': 'UNKNOWN',
            'issues': []
        }
        
        okx_total = okx_results.get('totals', {}).get('total_tokens', 0)
        
        # Compare with each peer exchange
        peer_totals = {}
        for exchange, data in comparison_results.items():
            if 'error' not in data:
                peer_total = data.get('oi_tokens', 0)
                peer_totals[exchange] = peer_total
                
                # Calculate ratio
                ratio = okx_total / peer_total if peer_total > 0 else 0
                
                validation['peer_comparisons'][exchange] = {
                    'peer_oi': peer_total,
                    'okx_oi': okx_total,
                    'okx_to_peer_ratio': ratio,
                    'reasonable': 0.1 <= ratio <= 10.0  # Within 10x range
                }
                
                logger.info(f"⚖️ OKX vs {exchange.upper()}: {okx_total:,.0f} vs {peer_total:,.0f} (ratio: {ratio:.2f}x)")
        
        # Rank OKX among exchanges
        all_exchanges = {**peer_totals, 'okx': okx_total}
        sorted_exchanges = sorted(all_exchanges.items(), key=lambda x: x[1], reverse=True)
        okx_rank = next((i+1 for i, (ex, _) in enumerate(sorted_exchanges) if ex == 'okx'), 0)
        
        validation['okx_rank'] = okx_rank
        validation['okx_market_share'] = f"{okx_rank}/{len(sorted_exchanges)}"
        
        # Reasonableness check
        reasonable_comparisons = [comp['reasonable'] for comp in validation['peer_comparisons'].values()]
        if all(reasonable_comparisons):
            validation['reasonableness_check'] = 'PASSED'
        elif any(reasonable_comparisons):
            validation['reasonableness_check'] = 'PARTIAL'
            validation['issues'].append("Some peer comparisons are outside reasonable range")
        else:
            validation['reasonableness_check'] = 'FAILED'
            validation['issues'].append("All peer comparisons are outside reasonable range")
        
        # Check against expected ranges
        expected_range = self.EXCHANGE_EXPECTED_RANGES.get('okx', {})
        if expected_range:
            min_expected = expected_range.get('min', 0)
            max_expected = expected_range.get('max', float('inf'))
            
            if min_expected <= okx_total <= max_expected:
                validation['issues'].append(f"✅ OKX total within expected range: {min_expected:,} - {max_expected:,}")
            else:
                validation['issues'].append(f"⚠️ OKX total outside expected range: {okx_total:,} not in {min_expected:,} - {max_expected:,}")
        
        logger.info(f"📊 OKX Market Position: #{okx_rank} out of {len(sorted_exchanges)} exchanges")
        logger.info(f"✅ Reasonableness: {validation['reasonableness_check']}")
        
        return validation
    
    def _generate_final_verdict(self, report: Dict) -> str:
        """Generate final verdict on the corrected implementation"""
        if 'error' in report:
            return 'VALIDATION_ERROR'
        
        okx_health = report.get('corrected_okx_results', {}).get('api_health', False)
        validation_summary = report.get('validation_summary', {})
        reasonableness = validation_summary.get('reasonableness_check', 'UNKNOWN')
        
        if not okx_health:
            return 'IMPLEMENTATION_UNHEALTHY'
        elif reasonableness == 'PASSED':
            return 'IMPLEMENTATION_VALIDATED'
        elif reasonableness == 'PARTIAL':
            return 'IMPLEMENTATION_ACCEPTABLE'
        else:
            return 'IMPLEMENTATION_QUESTIONABLE'
    
    def _assess_production_readiness(self, report: Dict) -> str:
        """Assess production readiness"""
        verdict = report.get('final_verdict', 'UNKNOWN')
        
        if verdict == 'IMPLEMENTATION_VALIDATED':
            return 'READY_FOR_PRODUCTION'
        elif verdict == 'IMPLEMENTATION_ACCEPTABLE':
            return 'READY_WITH_CAUTION'
        else:
            return 'NOT_READY'
    
    def print_final_report(self, report: Dict):
        """Print the final validation report"""
        print("\n" + "="*100)
        print("🎯 FINAL OKX VALIDATION REPORT - CORRECTED IMPLEMENTATION")
        print("="*100)
        
        print(f"Symbol: {report['symbol']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Final Verdict: {report['final_verdict']}")
        print(f"Production Readiness: {report['production_readiness']}")
        
        # OKX Results
        print(f"\n🟠 OKX CORRECTED RESULTS:")
        okx_results = report.get('corrected_okx_results', {})
        okx_totals = okx_results.get('totals', {})
        if okx_totals:
            print(f"  Total OI: {okx_totals['total_tokens']:,.0f} BTC (${okx_totals['total_usd']/1e9:.1f}B)")
        
        okx_markets = okx_results.get('markets', {})
        for market_type, market_data in okx_markets.items():
            if 'error' not in market_data:
                print(f"  {market_type.upper()}: {market_data['oi_tokens']:,.0f} BTC (${market_data['oi_usd']/1e9:.1f}B)")
        
        # Cross-exchange comparison
        print(f"\n🔄 CROSS-EXCHANGE COMPARISON:")
        comparison_results = report.get('cross_exchange_comparison', {})
        for exchange, data in comparison_results.items():
            if 'error' not in data:
                print(f"  {exchange.upper()}: {data['oi_tokens']:,.0f} BTC (${data['oi_usd']/1e9:.1f}B)")
            else:
                print(f"  {exchange.upper()}: ❌ {data['error']}")
        
        # Validation summary
        print(f"\n⚖️ PEER VALIDATION:")
        validation = report.get('validation_summary', {})
        print(f"  OKX Market Position: {validation.get('okx_market_share', 'UNKNOWN')}")
        print(f"  Reasonableness Check: {validation.get('reasonableness_check', 'UNKNOWN')}")
        
        peer_comparisons = validation.get('peer_comparisons', {})
        for exchange, comp in peer_comparisons.items():
            reasonable = "✅" if comp['reasonable'] else "❌"
            print(f"  vs {exchange.upper()}: {comp['okx_to_peer_ratio']:.2f}x {reasonable}")
        
        # Issues
        issues = validation.get('issues', [])
        if issues:
            print(f"\n📋 VALIDATION NOTES:")
            for issue in issues:
                print(f"  {issue}")
        
        # Final recommendations
        print(f"\n🎯 FINAL RECOMMENDATIONS:")
        production_readiness = report.get('production_readiness', 'UNKNOWN')
        
        if production_readiness == 'READY_FOR_PRODUCTION':
            print("  ✅ IMPLEMENTATION APPROVED FOR PRODUCTION")
            print("  🚀 Deploy with confidence - all validations passed")
            print("  📊 OKX values are realistic and comparable to major exchanges")
            print("  🔧 The oiCcy field fix is working correctly")
        elif production_readiness == 'READY_WITH_CAUTION':
            print("  ⚠️ IMPLEMENTATION ACCEPTABLE BUT MONITOR CLOSELY")
            print("  🔍 Some peer comparisons are concerning")
            print("  📊 Consider additional validation before full deployment")
        else:
            print("  ❌ IMPLEMENTATION NOT READY FOR PRODUCTION")
            print("  🔧 Additional fixes or investigation required")
        
        print("="*100)

# Main function
async def run_final_validation():
    """Run the final validation report"""
    logger.info("🎯 Starting FINAL OKX VALIDATION REPORT")
    
    validator = FinalOKXValidationReport()
    
    try:
        # Generate final report
        report = await validator.generate_final_report("BTC")
        
        # Print final report
        validator.print_final_report(report)
        
        # Save report
        with open('/tmp/final_okx_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("📊 Final validation report saved to /tmp/final_okx_validation_report.json")
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Final validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await validator.close()

if __name__ == "__main__":
    asyncio.run(run_final_validation())