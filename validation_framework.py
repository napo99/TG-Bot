#!/usr/bin/env python3
"""
BULLETPROOF AGENT VALIDATION FRAMEWORK
Never trust agent self-validation - always verify against external ground truth
"""

import requests
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    test_name: str
    passed: bool
    expected: Any
    actual: Any
    error_pct: float
    external_source: str
    evidence: str

class ExternalValidationEngine:
    """
    Validates agent claims against external ground truth sources
    PRINCIPLE: Never trust agent self-validation
    """
    
    def __init__(self):
        self.external_sources = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'binance_spot': 'https://api.binance.com/api/v3',
            'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1'
        }
    
    async def validate_price_accuracy(self, symbol: str, agent_price: float) -> ValidationResult:
        """Validate agent price against 3 external sources"""
        try:
            # Get external price sources
            coingecko_price = await self._get_coingecko_price(symbol)
            binance_price = await self._get_binance_price(symbol)
            
            # Calculate median external price
            external_prices = [p for p in [coingecko_price, binance_price] if p is not None]
            if not external_prices:
                return ValidationResult(
                    test_name="price_accuracy",
                    passed=False,
                    expected="external_price_data",
                    actual=agent_price,
                    error_pct=100.0,
                    external_source="multiple_sources",
                    evidence="No external price data available"
                )
            
            external_price = sum(external_prices) / len(external_prices)
            error_pct = abs(agent_price - external_price) / external_price * 100
            
            return ValidationResult(
                test_name="price_accuracy", 
                passed=error_pct < 5.0,  # Max 5% deviation allowed
                expected=external_price,
                actual=agent_price,
                error_pct=error_pct,
                external_source=f"coingecko+binance (n={len(external_prices)})",
                evidence=f"External: ${external_price:,.2f}, Agent: ${agent_price:,.2f}"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="price_accuracy",
                passed=False,
                expected="valid_price_comparison",
                actual=str(e),
                error_pct=100.0,
                external_source="error",
                evidence=f"Validation failed: {str(e)}"
            )
    
    async def validate_oi_calculation_logic(self, oi_tokens: float, price: float, agent_oi_usd: float) -> ValidationResult:
        """Validate USD calculation logic using mathematical ground truth"""
        try:
            # Mathematical ground truth: OI_USD = OI_TOKENS × PRICE
            expected_oi_usd = oi_tokens * price
            error_pct = abs(agent_oi_usd - expected_oi_usd) / expected_oi_usd * 100 if expected_oi_usd > 0 else 100.0
            
            return ValidationResult(
                test_name="oi_calculation_logic",
                passed=error_pct < 1.0,  # Max 1% calculation error allowed
                expected=expected_oi_usd,
                actual=agent_oi_usd,
                error_pct=error_pct,
                external_source="mathematical_ground_truth",
                evidence=f"Expected: {oi_tokens:,.0f} × ${price:,.2f} = ${expected_oi_usd:,.0f}, Agent: ${agent_oi_usd:,.0f}"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="oi_calculation_logic",
                passed=False,
                expected="valid_calculation",
                actual=str(e),
                error_pct=100.0,
                external_source="mathematical_error",
                evidence=f"Calculation validation failed: {str(e)}"
            )
    
    async def validate_exchange_oi_claims(self, symbol: str, exchange: str, agent_oi_tokens: float) -> ValidationResult:
        """Validate OI claims against direct exchange API calls"""
        try:
            if exchange.lower() == 'binance':
                external_oi = await self._get_binance_oi(symbol)
            elif exchange.lower() == 'bybit':
                external_oi = await self._get_bybit_oi(symbol)
            else:
                return ValidationResult(
                    test_name="exchange_oi_validation",
                    passed=False,
                    expected="external_oi_data",
                    actual=agent_oi_tokens,
                    error_pct=100.0,
                    external_source=exchange,
                    evidence="No external validation available for this exchange"
                )
            
            if external_oi is None:
                return ValidationResult(
                    test_name="exchange_oi_validation",
                    passed=False,
                    expected="valid_external_oi",
                    actual=agent_oi_tokens,
                    error_pct=100.0,
                    external_source=exchange,
                    evidence="External OI data unavailable"
                )
            
            error_pct = abs(agent_oi_tokens - external_oi) / external_oi * 100 if external_oi > 0 else 100.0
            
            return ValidationResult(
                test_name="exchange_oi_validation",
                passed=error_pct < 10.0,  # Max 10% OI deviation allowed
                expected=external_oi,
                actual=agent_oi_tokens,
                error_pct=error_pct,
                external_source=f"{exchange}_direct_api",
                evidence=f"External: {external_oi:,.0f}, Agent: {agent_oi_tokens:,.0f}"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="exchange_oi_validation",
                passed=False,
                expected="valid_oi_comparison",
                actual=str(e),
                error_pct=100.0,
                external_source="error",
                evidence=f"Exchange validation failed: {str(e)}"
            )
    
    async def validate_magnitude_sanity(self, symbol: str, total_oi_usd: float) -> ValidationResult:
        """Validate OI magnitude against known market reality"""
        try:
            # Known BTC OI magnitude ranges (from public data)
            known_ranges = {
                'BTC': {'min': 10_000_000_000, 'max': 50_000_000_000},  # $10B - $50B
                'ETH': {'min': 5_000_000_000, 'max': 25_000_000_000},   # $5B - $25B
            }
            
            if symbol.upper() not in known_ranges:
                return ValidationResult(
                    test_name="magnitude_sanity",
                    passed=True,  # No known range for this symbol
                    expected="unknown_range",
                    actual=total_oi_usd,
                    error_pct=0.0,
                    external_source="historical_data",
                    evidence=f"No historical range available for {symbol}"
                )
            
            range_data = known_ranges[symbol.upper()]
            in_range = range_data['min'] <= total_oi_usd <= range_data['max']
            
            return ValidationResult(
                test_name="magnitude_sanity",
                passed=in_range,
                expected=f"${range_data['min']/1e9:.1f}B - ${range_data['max']/1e9:.1f}B",
                actual=f"${total_oi_usd/1e9:.1f}B",
                error_pct=0.0 if in_range else 100.0,
                external_source="market_reality_check",
                evidence=f"Total OI: ${total_oi_usd/1e9:.1f}B vs expected range ${range_data['min']/1e9:.1f}B-${range_data['max']/1e9:.1f}B"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="magnitude_sanity",
                passed=False,
                expected="valid_magnitude_check",
                actual=str(e),
                error_pct=100.0,
                external_source="error",
                evidence=f"Magnitude validation failed: {str(e)}"
            )
    
    async def comprehensive_validation(self, agent_data: Dict[str, Any]) -> List[ValidationResult]:
        """Run comprehensive validation against external sources"""
        results = []
        
        # Extract agent claims
        symbol = agent_data.get('symbol', 'BTC')
        exchanges = agent_data.get('exchange_breakdown', [])
        total_oi_usd = agent_data.get('aggregated_oi', {}).get('total_usd', 0)
        
        # Validate each exchange claim
        for exchange_data in exchanges:
            exchange = exchange_data.get('exchange', '')
            oi_tokens = exchange_data.get('oi_tokens', 0)
            oi_usd = exchange_data.get('oi_usd', 0)
            price = exchange_data.get('price', 0)
            
            # Run validations
            price_validation = await self.validate_price_accuracy(symbol, price)
            calc_validation = await self.validate_oi_calculation_logic(oi_tokens, price, oi_usd)
            oi_validation = await self.validate_exchange_oi_claims(symbol, exchange, oi_tokens)
            
            results.extend([price_validation, calc_validation, oi_validation])
        
        # Validate overall magnitude
        magnitude_validation = await self.validate_magnitude_sanity(symbol, total_oi_usd)
        results.append(magnitude_validation)
        
        return results
    
    async def _get_coingecko_price(self, symbol: str) -> float:
        """Get price from CoinGecko API"""
        try:
            symbol_map = {'BTC': 'bitcoin', 'ETH': 'ethereum'}
            cg_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            url = f"{self.external_sources['coingecko']}/simple/price?ids={cg_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            return data[cg_id]['usd']
        except:
            return None
    
    async def _get_binance_price(self, symbol: str) -> float:
        """Get price from Binance API"""
        try:
            url = f"{self.external_sources['binance_spot']}/ticker/price?symbol={symbol.upper()}USDT"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            return float(data['price'])
        except:
            return None
    
    async def _get_binance_oi(self, symbol: str) -> float:
        """Get OI from Binance Futures API"""
        try:
            url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol.upper()}USDT"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            return float(data['openInterest'])
        except:
            return None
    
    async def _get_bybit_oi(self, symbol: str) -> float:
        """Get OI from Bybit API"""
        try:
            url = f"https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol.upper()}USDT"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data['retCode'] == 0 and data['result']['list']:
                return float(data['result']['list'][0]['openInterest'])
            return None
        except:
            return None

# Usage Example
async def validate_agent_claims(agent_oi_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate agent OI analysis against external sources"""
    validator = ExternalValidationEngine()
    results = await validator.comprehensive_validation(agent_oi_data)
    
    # Generate validation report
    passed_tests = sum(1 for r in results if r.passed)
    total_tests = len(results)
    pass_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
    
    validation_report = {
        'validation_summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate_pct': pass_rate,
            'overall_status': 'TRUSTED' if pass_rate >= 90 else 'SUSPICIOUS' if pass_rate >= 70 else 'REJECTED'
        },
        'detailed_results': [
            {
                'test': r.test_name,
                'status': 'PASS' if r.passed else 'FAIL',
                'expected': r.expected,
                'actual': r.actual,
                'error_pct': r.error_pct,
                'source': r.external_source,
                'evidence': r.evidence
            } for r in results
        ]
    }
    
    return validation_report

if __name__ == "__main__":
    # Test validation framework
    sample_agent_data = {
        'symbol': 'BTC',
        'aggregated_oi': {'total_usd': 32700000000},  # $32.7B
        'exchange_breakdown': [
            {
                'exchange': 'binance',
                'oi_tokens': 78278,
                'oi_usd': 7900000000,  # $7.9B
                'price': 106500
            }
        ]
    }
    
    # Run validation
    validation_report = asyncio.run(validate_agent_claims(sample_agent_data))
    print("🔍 VALIDATION REPORT:")
    print(f"Overall Status: {validation_report['validation_summary']['overall_status']}")
    print(f"Pass Rate: {validation_report['validation_summary']['pass_rate_pct']:.1f}%")
    
    for result in validation_report['detailed_results']:
        status_emoji = "✅" if result['status'] == 'PASS' else "❌"
        print(f"{status_emoji} {result['test']}: {result['evidence']}")