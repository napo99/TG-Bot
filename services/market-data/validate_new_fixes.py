#!/usr/bin/env python3
"""
EXTERNAL VALIDATION: New fixes validation
Validate the 3 new fixes: Bybit USDC, Gate.io USDT/USD, Bitget USDT/USD
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ValidationResult:
    provider: str
    market: str  
    expected_range: tuple
    actual_value: float
    status: str
    details: str

class NewFixesValidator:
    """External validation for the 3 new fixes"""
    
    async def validate_all_new_fixes(self) -> Dict[str, Any]:
        """Validate all new fixes externally"""
        print("🔍 EXTERNAL VALIDATION - NEW FIXES")
        print("=" * 50)
        
        results = []
        
        # 1. Validate Bybit USDC fix (BTCPERP symbol)
        bybit_usdc = await self.validate_bybit_usdc()
        results.append(bybit_usdc)
        
        # 2. Validate Gate.io fixes (total_size field usage)
        gateio_usdt = await self.validate_gateio_usdt()
        gateio_usd = await self.validate_gateio_usd()
        results.extend([gateio_usdt, gateio_usd])
        
        # 3. Validate Bitget fixes (amount field usage)
        bitget_usdt = await self.validate_bitget_usdt()
        bitget_usd = await self.validate_bitget_usd()
        results.extend([bitget_usdt, bitget_usd])
        
        # Generate summary
        passed = [r for r in results if r.status == "PASS"]
        failed = [r for r in results if r.status == "FAIL"]
        
        summary = {
            "total_validations": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "success_rate": len(passed) / len(results) * 100,
            "all_passed": len(failed) == 0,
            "results": results
        }
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"  Total: {summary['total_validations']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Overall: {'✅ ALL PASSED' if summary['all_passed'] else '❌ SOME FAILED'}")
        
        return summary
    
    async def validate_bybit_usdc(self) -> ValidationResult:
        """Validate Bybit USDC fix (BTCPERP symbol)"""
        print("\n🟣 Validating Bybit USDC (BTCPERP) fix...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Direct API call to verify BTCPERP exists and has OI
                url = "https://api.bybit.com/v5/market/tickers"
                params = {"category": "linear", "symbol": "BTCPERP"}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    ticker = data['result']['list'][0]
                    oi = float(ticker.get('openInterest', 0))
                    price = float(ticker.get('lastPrice', 0))
                    
                    # Reasonable range: 100 - 10,000 BTC for USDC perp
                    expected_range = (100, 10000)
                    
                    if expected_range[0] <= oi <= expected_range[1]:
                        status = "PASS"
                        details = f"BTCPERP found with {oi:,.0f} BTC OI at ${price:,.2f}"
                    else:
                        status = "FAIL"
                        details = f"OI {oi:,.0f} outside expected range {expected_range}"
                    
                    return ValidationResult("bybit", "USDC", expected_range, oi, status, details)
                else:
                    return ValidationResult("bybit", "USDC", (0, 0), 0, "FAIL", "BTCPERP symbol not found")
                    
        except Exception as e:
            return ValidationResult("bybit", "USDC", (0, 0), 0, "FAIL", f"API error: {e}")
    
    async def validate_gateio_usdt(self) -> ValidationResult:
        """Validate Gate.io USDT fix (total_size field)"""
        print("🟢 Validating Gate.io USDT (total_size) fix...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.gateio.ws/api/v4/futures/usdt/tickers"
                
                async with session.get(url) as response:
                    data = await response.json()
                
                # Find BTC_USDT ticker
                btc_ticker = None
                for ticker in data:
                    if ticker.get('contract') == 'BTC_USDT':
                        btc_ticker = ticker
                        break
                
                if btc_ticker:
                    total_size = float(btc_ticker.get('total_size', 0))
                    price = float(btc_ticker.get('last', 0))
                    oi_btc = total_size / price if price > 0 else 0
                    
                    # Reasonable range: 1,000 - 50,000 BTC for Gate.io USDT
                    expected_range = (1000, 50000)
                    
                    if expected_range[0] <= oi_btc <= expected_range[1]:
                        status = "PASS"
                        details = f"total_size ${total_size:,.0f} = {oi_btc:,.0f} BTC at ${price:,.2f}"
                    else:
                        status = "FAIL" 
                        details = f"OI {oi_btc:,.0f} BTC outside expected range {expected_range}"
                    
                    return ValidationResult("gateio", "USDT", expected_range, oi_btc, status, details)
                else:
                    return ValidationResult("gateio", "USDT", (0, 0), 0, "FAIL", "BTC_USDT not found")
                    
        except Exception as e:
            return ValidationResult("gateio", "USDT", (0, 0), 0, "FAIL", f"API error: {e}")
    
    async def validate_gateio_usd(self) -> ValidationResult:
        """Validate Gate.io USD fix (total_size field)"""
        print("🟢 Validating Gate.io USD (total_size) fix...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.gateio.ws/api/v4/futures/btc/tickers"
                
                async with session.get(url) as response:
                    data = await response.json()
                
                # Find BTC_USD ticker
                btc_ticker = None
                for ticker in data:
                    if ticker.get('contract') == 'BTC_USD':
                        btc_ticker = ticker
                        break
                
                if btc_ticker:
                    total_size = float(btc_ticker.get('total_size', 0))
                    price = float(btc_ticker.get('last', 0))
                    oi_btc = total_size / price if price > 0 else 0
                    
                    # Reasonable range: 50 - 5,000 BTC for Gate.io USD inverse
                    expected_range = (50, 5000)
                    
                    if expected_range[0] <= oi_btc <= expected_range[1]:
                        status = "PASS"
                        details = f"total_size ${total_size:,.0f} = {oi_btc:,.0f} BTC at ${price:,.2f}"
                    else:
                        status = "FAIL"
                        details = f"OI {oi_btc:,.0f} BTC outside expected range {expected_range}"
                    
                    return ValidationResult("gateio", "USD", expected_range, oi_btc, status, details)
                else:
                    return ValidationResult("gateio", "USD", (0, 0), 0, "FAIL", "BTC_USD not found")
                    
        except Exception as e:
            return ValidationResult("gateio", "USD", (0, 0), 0, "FAIL", f"API error: {e}")
    
    async def validate_bitget_usdt(self) -> ValidationResult:
        """Validate Bitget USDT fix (amount field)"""
        print("🟡 Validating Bitget USDT (amount) fix...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.bitget.com/api/mix/v1/market/open-interest"
                params = {"symbol": "BTCUSDT_UMCBL"}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                
                if data.get('code') == '00000':
                    oi_data = data.get('data', {})
                    amount = float(oi_data.get('amount', 0))
                    
                    # Reasonable range: 10,000 - 100,000 BTC for Bitget USDT
                    expected_range = (10000, 100000)
                    
                    if expected_range[0] <= amount <= expected_range[1]:
                        status = "PASS"
                        details = f"amount field: {amount:,.0f} BTC"
                    else:
                        status = "FAIL"
                        details = f"amount {amount:,.0f} BTC outside expected range {expected_range}"
                    
                    return ValidationResult("bitget", "USDT", expected_range, amount, status, details)
                else:
                    return ValidationResult("bitget", "USDT", (0, 0), 0, "FAIL", f"API error: {data.get('msg')}")
                    
        except Exception as e:
            return ValidationResult("bitget", "USDT", (0, 0), 0, "FAIL", f"API error: {e}")
    
    async def validate_bitget_usd(self) -> ValidationResult:
        """Validate Bitget USD fix (amount field)"""
        print("🟡 Validating Bitget USD (amount) fix...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.bitget.com/api/mix/v1/market/open-interest"
                params = {"symbol": "BTCUSD_DMCBL"}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                
                if data.get('code') == '00000':
                    oi_data = data.get('data', {})
                    amount = float(oi_data.get('amount', 0))
                    
                    # Reasonable range: 5,000 - 50,000 BTC for Bitget USD inverse
                    expected_range = (5000, 50000)
                    
                    if expected_range[0] <= amount <= expected_range[1]:
                        status = "PASS"
                        details = f"amount field: {amount:,.0f} BTC"
                    else:
                        status = "FAIL"
                        details = f"amount {amount:,.0f} BTC outside expected range {expected_range}"
                    
                    return ValidationResult("bitget", "USD", expected_range, amount, status, details)
                else:
                    return ValidationResult("bitget", "USD", (0, 0), 0, "FAIL", f"API error: {data.get('msg')}")
                    
        except Exception as e:
            return ValidationResult("bitget", "USD", (0, 0), 0, "FAIL", f"API error: {e}")

async def main():
    """Main validation function"""
    validator = NewFixesValidator()
    summary = await validator.validate_all_new_fixes()
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in summary['results']:
        status_emoji = "✅" if result.status == "PASS" else "❌"
        print(f"  {status_emoji} {result.provider.upper()} {result.market}: {result.details}")
    
    return summary

if __name__ == "__main__":
    asyncio.run(main())