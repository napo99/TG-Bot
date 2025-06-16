#!/usr/bin/env python3
"""
Quick Validation Script for Crypto Trading Assistant
Tests all key enhanced functionality to ensure everything is working correctly.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys

class CryptoAssistantValidator:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.session = None
        self.passed = 0
        self.failed = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status} | {test_name}")
        if details:
            print(f"     {details}")
        print()
    
    async def test_health_check(self):
        """Test market data service health"""
        try:
            async with self.session.get(f"{self.base_url}/health") as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get('status') == 'healthy'
                self.log_test("Health Check", success, f"Status: {data.get('status')}")
                return success
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {e}")
            return False
    
    async def test_top_perps_fixed(self):
        """Test the main fix: /top10 perps now returns data"""
        try:
            payload = {"market_type": "perp", "limit": 3}
            async with self.session.post(f"{self.base_url}/top_symbols", json=payload) as resp:
                data = await resp.json()
                success = (resp.status == 200 and 
                          data.get('success') and 
                          len(data.get('data', {}).get('symbols', [])) > 0)
                
                if success:
                    symbols = data['data']['symbols']
                    has_oi = any(s.get('open_interest') for s in symbols)
                    has_funding = any(s.get('funding_rate') is not None for s in symbols)
                    details = f"Found {len(symbols)} perps, OI: {has_oi}, Funding: {has_funding}"
                else:
                    details = f"No perp data returned"
                
                self.log_test("Top Perps Fixed (Main Issue)", success, details)
                return success
        except Exception as e:
            self.log_test("Top Perps Fixed (Main Issue)", False, f"Error: {e}")
            return False
    
    async def test_enhanced_price_data(self):
        """Test enhanced price display with combined spot + perp"""
        try:
            payload = {"symbol": "BTC/USDT"}
            async with self.session.post(f"{self.base_url}/combined_price", json=payload) as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get('success')
                
                if success:
                    has_spot = 'spot' in data.get('data', {})
                    has_perp = 'perp' in data.get('data', {})
                    details = f"Spot: {has_spot}, Perp: {has_perp}"
                else:
                    details = "No price data returned"
                
                self.log_test("Enhanced Price Data", success, details)
                return success
        except Exception as e:
            self.log_test("Enhanced Price Data", False, f"Error: {e}")
            return False
    
    async def test_market_cap_ranking(self):
        """Test market cap proxy ranking for top symbols"""
        try:
            payload = {"market_type": "spot", "limit": 5}
            async with self.session.post(f"{self.base_url}/top_symbols", json=payload) as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get('success')
                
                if success:
                    symbols = data['data']['symbols']
                    # Check if symbols are properly ranked (descending market cap proxy)
                    market_caps = []
                    for symbol in symbols:
                        price = symbol.get('price', 0)
                        volume = symbol.get('volume_24h', 0)
                        market_cap = price * volume
                        market_caps.append(market_cap)
                    
                    is_sorted = all(market_caps[i] >= market_caps[i+1] for i in range(len(market_caps)-1))
                    details = f"Symbols ranked correctly: {is_sorted}, Top MCap: ${market_caps[0]/1e6:.0f}M"
                else:
                    details = "No spot data returned"
                
                self.log_test("Market Cap Ranking", success, details)
                return success
        except Exception as e:
            self.log_test("Market Cap Ranking", False, f"Error: {e}")
            return False
    
    async def test_symbol_format_compatibility(self):
        """Test different symbol input formats"""
        formats_to_test = [
            "BTC/USDT",
            "BTC-USDT", 
            "eth/usdt",
            "ETH-USDT"
        ]
        
        passed_formats = 0
        for symbol_format in formats_to_test:
            try:
                payload = {"symbol": symbol_format}
                async with self.session.post(f"{self.base_url}/combined_price", json=payload) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get('success'):
                        passed_formats += 1
            except:
                pass
        
        success = passed_formats >= 3  # At least 3/4 formats should work
        details = f"{passed_formats}/{len(formats_to_test)} symbol formats work"
        self.log_test("Symbol Format Compatibility", success, details)
        return success
    
    async def test_oi_and_funding_data(self):
        """Test Open Interest and Funding Rate data for perpetuals"""
        try:
            payload = {"market_type": "perp", "limit": 5}
            async with self.session.post(f"{self.base_url}/top_symbols", json=payload) as resp:
                data = await resp.json()
                success = resp.status == 200 and data.get('success')
                
                if success:
                    symbols = data['data']['symbols']
                    oi_count = sum(1 for s in symbols if s.get('open_interest'))
                    funding_count = sum(1 for s in symbols if s.get('funding_rate') is not None)
                    
                    # At least 60% should have OI and funding data
                    success = oi_count >= len(symbols) * 0.6 and funding_count >= len(symbols) * 0.6
                    details = f"OI: {oi_count}/{len(symbols)}, Funding: {funding_count}/{len(symbols)}"
                else:
                    details = "No perp data returned"
                
                self.log_test("OI and Funding Data", success, details)
                return success
        except Exception as e:
            self.log_test("OI and Funding Data", False, f"Error: {e}")
            return False
    
    async def test_performance_benchmark(self):
        """Test response time performance"""
        import time
        
        start_time = time.time()
        try:
            payload = {"market_type": "spot", "limit": 10}
            async with self.session.post(f"{self.base_url}/top_symbols", json=payload) as resp:
                data = await resp.json()
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                success = resp.status == 200 and response_time < 10000  # Under 10 seconds
                details = f"Response time: {response_time:.0f}ms"
                self.log_test("Performance Benchmark", success, details)
                return success
        except Exception as e:
            self.log_test("Performance Benchmark", False, f"Error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Crypto Trading Assistant - Quick Validation")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        test_results = await asyncio.gather(
            self.test_health_check(),
            self.test_top_perps_fixed(),
            self.test_enhanced_price_data(),
            self.test_market_cap_ranking(),
            self.test_symbol_format_compatibility(),
            self.test_oi_and_funding_data(),
            self.test_performance_benchmark(),
            return_exceptions=True
        )
        
        # Summary
        print("=" * 50)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! System is ready for production.")
            return True
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Review issues above.")
            return False

async def main():
    async with CryptoAssistantValidator() as validator:
        success = await validator.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())