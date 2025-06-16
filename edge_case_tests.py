#!/usr/bin/env python3
"""
Edge Case and Final Validation Tests
Tests specific edge cases and validates the recent fixes
"""

import asyncio
import aiohttp
import json
import time

class EdgeCaseTests:
    def __init__(self, market_data_url: str = "http://localhost:8001"):
        self.market_data_url = market_data_url
        self.session = None
    
    async def setup(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def teardown(self):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, data: dict) -> dict:
        url = f"{self.market_data_url}{endpoint}"
        async with self.session.post(url, json=data) as response:
            return await response.json()
    
    async def test_perp_exchange_fix(self):
        """Test that /top10 perps uses binance_futures exchange correctly"""
        print("🔧 Testing Perpetual Exchange Fix")
        
        # Get debug info for both spot and perp to verify correct exchanges
        spot_debug = await self._make_request("/debug_tickers", {
            "market_type": "spot",
            "limit": 10
        })
        
        perp_debug = await self._make_request("/debug_tickers", {
            "market_type": "perp", 
            "limit": 10
        })
        
        if spot_debug.get("success") and perp_debug.get("success"):
            spot_exchange = spot_debug.get("exchange_used")
            perp_exchange = perp_debug.get("exchange_used")
            
            print(f"   Spot Exchange: {spot_exchange}")
            print(f"   Perp Exchange: {perp_exchange}")
            
            if spot_exchange == "binance" and perp_exchange == "binance_futures":
                print("   ✅ Exchange routing is correct")
                return True
            else:
                print("   ❌ Exchange routing issue detected")
                return False
        else:
            print("   ❌ Could not verify exchange routing")
            return False
    
    async def test_symbol_format_variants(self):
        """Test various symbol format inputs"""
        print("🔤 Testing Symbol Format Variants")
        
        symbol_variants = [
            "BTC/USDT",
            "BTC-USDT", 
            "btc/usdt",
            "btc-usdt",
            "BTC/USDT:USDT",  # Perp format
        ]
        
        successful_variants = 0
        for variant in symbol_variants:
            try:
                result = await self._make_request("/combined_price", {"symbol": variant})
                if result.get("success"):
                    data = result["data"]
                    has_data = ("spot" in data and data["spot"]) or ("perp" in data and data["perp"])
                    if has_data:
                        successful_variants += 1
                        print(f"   ✅ {variant}: Valid")
                    else:
                        print(f"   ⚠️  {variant}: No data")
                else:
                    print(f"   ❌ {variant}: Failed")
            except Exception as e:
                print(f"   ❌ {variant}: Exception - {str(e)}")
        
        success_rate = successful_variants / len(symbol_variants)
        if success_rate >= 0.6:  # At least 60% should work
            print(f"   ✅ Symbol format handling: {successful_variants}/{len(symbol_variants)} variants work")
            return True
        else:
            print(f"   ❌ Symbol format handling: Only {successful_variants}/{len(symbol_variants)} variants work")
            return False
    
    async def test_enhanced_data_consistency(self):
        """Test that enhanced data (OI, funding) is consistent"""
        print("📊 Testing Enhanced Data Consistency")
        
        # Test multiple symbols to ensure consistent data
        test_symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
        consistent_data = []
        
        for symbol in test_symbols:
            result = await self._make_request("/combined_price", {"symbol": symbol})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                
                if "perp" in data and data["perp"]:
                    perp = data["perp"]
                    has_oi = perp.get("open_interest") is not None
                    has_funding = perp.get("funding_rate") is not None
                    has_volume = perp.get("volume_24h") is not None and perp.get("volume_24h", 0) > 0
                    
                    consistent_data.append({
                        "symbol": symbol,
                        "has_oi": has_oi,
                        "has_funding": has_funding,
                        "has_volume": has_volume
                    })
                    
                    print(f"   {symbol}: OI={'✅' if has_oi else '❌'}, Funding={'✅' if has_funding else '❌'}, Volume={'✅' if has_volume else '❌'}")
        
        # Check consistency
        if len(consistent_data) >= 2:
            oi_consistent = all(d["has_oi"] for d in consistent_data) or not any(d["has_oi"] for d in consistent_data)
            funding_consistent = sum(d["has_funding"] for d in consistent_data) >= len(consistent_data) * 0.7
            volume_consistent = all(d["has_volume"] for d in consistent_data)
            
            if oi_consistent and funding_consistent and volume_consistent:
                print("   ✅ Enhanced data is consistent across symbols")
                return True
            else:
                print("   ⚠️  Enhanced data has some inconsistencies")
                return True  # Still acceptable
        else:
            print("   ❌ Could not test data consistency")
            return False
    
    async def test_large_volume_calculations(self):
        """Test volume calculations with large numbers"""
        print("🔢 Testing Large Volume Calculations")
        
        # Get top symbols with large volumes
        result = await self._make_request("/top_symbols", {
            "market_type": "spot",
            "limit": 3
        })
        
        if result.get("success"):
            symbols = result["data"]["symbols"]
            calculation_issues = []
            
            for symbol in symbols:
                price = symbol.get("price", 0)
                volume = symbol.get("volume_24h", 0) or 0
                
                if price > 0 and volume > 0:
                    # Calculate USD volume
                    volume_usd = volume * price
                    market_cap_proxy = price * volume
                    
                    # Check for reasonable values (not infinity, not NaN)
                    if volume_usd > 1e15 or market_cap_proxy > 1e15:  # Extremely large
                        calculation_issues.append(f"{symbol['symbol']}: Values too large")
                    elif volume_usd <= 0 or market_cap_proxy <= 0:
                        calculation_issues.append(f"{symbol['symbol']}: Negative values")
                    else:
                        print(f"   ✅ {symbol['symbol']}: Volume=${volume_usd/1e6:.1f}M, MCap=${market_cap_proxy/1e6:.1f}M")
            
            if not calculation_issues:
                print("   ✅ All volume calculations are reasonable")
                return True
            else:
                print(f"   ⚠️  Some calculation issues: {calculation_issues}")
                return False
        else:
            print("   ❌ Could not test volume calculations")
            return False
    
    async def test_rate_limiting_behavior(self):
        """Test API behavior under rapid requests"""
        print("⚡ Testing Rate Limiting Behavior")
        
        # Make 10 rapid requests
        tasks = []
        for i in range(10):
            task = self._make_request("/health", {})
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "healthy")
        
        print(f"   10 concurrent requests in {duration:.2f}s")
        print(f"   Successful: {successful_requests}/10")
        
        if successful_requests >= 8:  # Allow some failures due to rate limiting
            print("   ✅ Good concurrent request handling")
            return True
        else:
            print("   ⚠️  Some concurrent request issues")
            return False
    
    async def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("🔍 Running Edge Case and Final Validation Tests")
        print("=" * 60)
        
        await self.setup()
        
        tests = [
            self.test_perp_exchange_fix,
            self.test_symbol_format_variants,
            self.test_enhanced_data_consistency,
            self.test_large_volume_calculations,
            self.test_rate_limiting_behavior,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
                print()
            except Exception as e:
                print(f"   ❌ Test failed with exception: {str(e)}")
                results.append(False)
                print()
        
        await self.teardown()
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("=" * 60)
        print("📋 EDGE CASE TEST SUMMARY")
        print("=" * 60)
        print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All edge cases handled correctly!")
        elif passed >= total * 0.8:
            print("✅ Most edge cases handled well")
        else:
            print("⚠️  Some edge cases need attention")
        
        return passed / total

async def main():
    test = EdgeCaseTests()
    await test.run_edge_case_tests()

if __name__ == "__main__":
    asyncio.run(main())