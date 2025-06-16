#!/usr/bin/env python3
"""
Comprehensive Test Suite for Crypto Trading Assistant
Tests all components: Market Data Service, Telegram Bot Integration, and End-to-End scenarios
"""

import asyncio
import aiohttp
import json
import time
import traceback
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    test_name: str
    test_type: str
    status: str  # PASS, FAIL, SKIP
    duration_ms: float
    details: str
    error: Optional[str] = None

class TestSuite:
    def __init__(self, market_data_url: str = "http://localhost:8001"):
        self.market_data_url = market_data_url
        self.session = None
        self.results: List[TestResult] = []
    
    async def setup(self):
        """Setup test environment"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        print("🚀 Test Suite initialized")
    
    async def teardown(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        print("🧹 Test Suite cleaned up")
    
    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> Dict[str, Any]:
        """Make HTTP request to market data service"""
        url = f"{self.market_data_url}{endpoint}"
        
        if method.upper() == "GET":
            async with self.session.get(url) as response:
                return await response.json()
        elif method.upper() == "POST":
            async with self.session.post(url, json=data or {}) as response:
                return await response.json()
    
    def _record_result(self, test_name: str, test_type: str, start_time: float, 
                      status: str, details: str, error: str = None):
        """Record test result"""
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        result = TestResult(
            test_name=test_name,
            test_type=test_type,
            status=status,
            duration_ms=duration,
            details=details,
            error=error
        )
        self.results.append(result)
        
        # Print immediate result
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_emoji} {test_name} ({duration:.1f}ms): {details}")
        if error:
            print(f"   Error: {error}")

    # =================== UNIT TESTS ===================
    
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        start_time = time.time()
        test_name = "Health Endpoint"
        
        try:
            result = await self._make_request("GET", "/health")
            
            if result.get("status") == "healthy" and result.get("service") == "market-data":
                self._record_result(test_name, "UNIT", start_time, "PASS", 
                                  "Health endpoint returns correct status")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  f"Unexpected health response: {result}")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "FAIL", 
                              "Health endpoint failed", str(e))
    
    async def test_price_endpoint_valid_symbol(self):
        """Test price endpoint with valid symbol"""
        start_time = time.time()
        test_name = "Price Endpoint - Valid Symbol"
        
        try:
            result = await self._make_request("POST", "/price", {"symbol": "BTC/USDT"})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                required_fields = ["symbol", "price", "timestamp"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if not missing_fields and data["price"] > 0:
                    self._record_result(test_name, "UNIT", start_time, "PASS", 
                                      f"Price data: ${data['price']:,.2f}")
                else:
                    self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                      f"Missing fields: {missing_fields} or invalid price")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  f"API returned error: {result}")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "FAIL", 
                              "Price endpoint failed", str(e))
    
    async def test_price_endpoint_invalid_symbol(self):
        """Test price endpoint with invalid symbol"""
        start_time = time.time()
        test_name = "Price Endpoint - Invalid Symbol"
        
        try:
            result = await self._make_request("POST", "/price", {"symbol": "INVALID/SYMBOL"})
            
            if not result.get("success"):
                self._record_result(test_name, "UNIT", start_time, "PASS", 
                                  "Correctly rejected invalid symbol")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  "Should have rejected invalid symbol")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "PASS", 
                              "Exception correctly thrown for invalid symbol")
    
    async def test_combined_price_endpoint(self):
        """Test combined price endpoint (spot + perp)"""
        start_time = time.time()
        test_name = "Combined Price Endpoint"
        
        try:
            result = await self._make_request("POST", "/combined_price", {"symbol": "BTC-USDT"})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                
                # Check if we have at least spot or perp data
                has_spot = "spot" in data and data["spot"] is not None
                has_perp = "perp" in data and data["perp"] is not None
                
                if has_spot or has_perp:
                    details = []
                    if has_spot:
                        details.append(f"Spot: ${data['spot']['price']:,.2f}")
                    if has_perp:
                        details.append(f"Perp: ${data['perp']['price']:,.2f}")
                        if data['perp'].get('open_interest'):
                            details.append(f"OI: {data['perp']['open_interest']:,.0f}")
                        if data['perp'].get('funding_rate') is not None:
                            fr = data['perp']['funding_rate'] * 100
                            details.append(f"Funding: {fr:.4f}%")
                    
                    self._record_result(test_name, "UNIT", start_time, "PASS", 
                                      ", ".join(details))
                else:
                    self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                      "No spot or perp data returned")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  f"API returned error: {result}")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "FAIL", 
                              "Combined price endpoint failed", str(e))
    
    async def test_top_symbols_spot(self):
        """Test top symbols endpoint for spot markets"""
        start_time = time.time()
        test_name = "Top Symbols - Spot Markets"
        
        try:
            result = await self._make_request("POST", "/top_symbols", {
                "market_type": "spot",
                "limit": 5
            })
            
            if result.get("success") and "data" in result:
                symbols = result["data"]["symbols"]
                
                if len(symbols) > 0:
                    # Verify all symbols are spot markets
                    spot_symbols = [s for s in symbols if s.get("market_type") == "spot"]
                    
                    if len(spot_symbols) == len(symbols):
                        top_symbol = symbols[0]
                        volume_usd = (top_symbol.get('volume_24h', 0) or 0) * top_symbol['price']
                        self._record_result(test_name, "UNIT", start_time, "PASS", 
                                          f"Got {len(symbols)} spot markets, top: {top_symbol['symbol']} (${volume_usd/1e6:.1f}M)")
                    else:
                        self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                          "Some symbols are not spot markets")
                else:
                    self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                      "No symbols returned")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  f"API returned error: {result}")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "FAIL", 
                              "Top symbols spot endpoint failed", str(e))
    
    async def test_top_symbols_perp(self):
        """Test top symbols endpoint for perpetual markets"""
        start_time = time.time()
        test_name = "Top Symbols - Perpetual Markets"
        
        try:
            result = await self._make_request("POST", "/top_symbols", {
                "market_type": "perp",
                "limit": 5
            })
            
            if result.get("success") and "data" in result:
                symbols = result["data"]["symbols"]
                
                if len(symbols) > 0:
                    # Verify all symbols are perp markets
                    perp_symbols = [s for s in symbols if s.get("market_type") == "perp"]
                    
                    if len(perp_symbols) == len(symbols):
                        top_symbol = symbols[0]
                        details = [f"Got {len(symbols)} perp markets"]
                        details.append(f"Top: {top_symbol['symbol']}")
                        
                        if top_symbol.get('open_interest'):
                            oi_usd = top_symbol['open_interest'] * top_symbol['price']
                            details.append(f"OI: ${oi_usd/1e6:.0f}M")
                        
                        if top_symbol.get('funding_rate') is not None:
                            fr = top_symbol['funding_rate'] * 100
                            details.append(f"Funding: {fr:.4f}%")
                        
                        self._record_result(test_name, "UNIT", start_time, "PASS", 
                                          ", ".join(details))
                    else:
                        self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                          "Some symbols are not perp markets")
                else:
                    self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                      "No symbols returned")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  f"API returned error: {result}")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "FAIL", 
                              "Top symbols perp endpoint failed", str(e))
    
    async def test_debug_tickers_endpoint(self):
        """Test debug tickers endpoint"""
        start_time = time.time()
        test_name = "Debug Tickers Endpoint"
        
        try:
            result = await self._make_request("POST", "/debug_tickers", {
                "market_type": "spot",
                "limit": 10
            })
            
            if result.get("success"):
                total_tickers = result.get("total_tickers", 0)
                sample_symbols = result.get("sample_symbols", [])
                
                self._record_result(test_name, "UNIT", start_time, "PASS", 
                                  f"Got {total_tickers} total tickers, {len(sample_symbols)} samples")
            else:
                self._record_result(test_name, "UNIT", start_time, "FAIL", 
                                  f"Debug endpoint error: {result}")
        except Exception as e:
            self._record_result(test_name, "UNIT", start_time, "FAIL", 
                              "Debug tickers endpoint failed", str(e))
    
    # =================== INTEGRATION TESTS ===================
    
    async def test_symbol_formatting_consistency(self):
        """Test symbol formatting across different endpoints"""
        start_time = time.time()
        test_name = "Symbol Formatting Consistency"
        
        try:
            # Test different symbol formats
            test_symbols = ["BTC-USDT", "BTC/USDT", "btc-usdt"]
            results = []
            
            for symbol in test_symbols:
                result = await self._make_request("POST", "/combined_price", {"symbol": symbol})
                if result.get("success"):
                    results.append(f"{symbol}: OK")
                else:
                    results.append(f"{symbol}: FAIL")
            
            if all("OK" in r for r in results):
                self._record_result(test_name, "INTEGRATION", start_time, "PASS", 
                                  "All symbol formats handled correctly")
            else:
                self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                                  f"Symbol format issues: {results}")
        except Exception as e:
            self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                              "Symbol formatting test failed", str(e))
    
    async def test_exchange_data_fetching(self):
        """Test data fetching from multiple exchanges"""
        start_time = time.time()
        test_name = "Exchange Data Fetching"
        
        try:
            # Test spot data (should use binance)
            spot_result = await self._make_request("POST", "/top_symbols", {
                "market_type": "spot",
                "limit": 3
            })
            
            # Test perp data (should use binance_futures)
            perp_result = await self._make_request("POST", "/top_symbols", {
                "market_type": "perp", 
                "limit": 3
            })
            
            spot_success = spot_result.get("success", False)
            perp_success = perp_result.get("success", False)
            
            if spot_success and perp_success:
                spot_count = len(spot_result["data"]["symbols"])
                perp_count = len(perp_result["data"]["symbols"])
                self._record_result(test_name, "INTEGRATION", start_time, "PASS", 
                                  f"Spot: {spot_count} symbols, Perp: {perp_count} symbols")
            else:
                errors = []
                if not spot_success:
                    errors.append("Spot data failed")
                if not perp_success:
                    errors.append("Perp data failed")
                self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                                  ", ".join(errors))
        except Exception as e:
            self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                              "Exchange data fetching failed", str(e))
    
    async def test_perp_enhanced_data(self):
        """Test enhanced perpetual data (OI, funding rates)"""
        start_time = time.time()
        test_name = "Perpetual Enhanced Data"
        
        try:
            result = await self._make_request("POST", "/combined_price", {"symbol": "BTC-USDT"})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                
                if "perp" in data and data["perp"]:
                    perp = data["perp"]
                    enhancements = []
                    
                    if perp.get("open_interest") is not None:
                        enhancements.append(f"OI: {perp['open_interest']:,.0f}")
                    
                    if perp.get("funding_rate") is not None:
                        fr = perp["funding_rate"] * 100
                        enhancements.append(f"Funding: {fr:.4f}%")
                    
                    if enhancements:
                        self._record_result(test_name, "INTEGRATION", start_time, "PASS", 
                                          f"Enhanced data available: {', '.join(enhancements)}")
                    else:
                        self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                                          "No enhanced data (OI/funding) available")
                else:
                    self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                                      "No perp data available")
            else:
                self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                                  f"API error: {result}")
        except Exception as e:
            self._record_result(test_name, "INTEGRATION", start_time, "FAIL", 
                              "Enhanced perp data test failed", str(e))
    
    # =================== PERFORMANCE TESTS ===================
    
    async def test_response_times(self):
        """Test API response times"""
        start_time = time.time()
        test_name = "Response Times"
        
        try:
            endpoints = [
                ("/health", "GET", {}),
                ("/price", "POST", {"symbol": "BTC/USDT"}),
                ("/combined_price", "POST", {"symbol": "ETH-USDT"}),
                ("/top_symbols", "POST", {"market_type": "spot", "limit": 5})
            ]
            
            times = []
            for endpoint, method, data in endpoints:
                req_start = time.time()
                result = await self._make_request(method, endpoint, data)
                req_time = (time.time() - req_start) * 1000
                times.append(req_time)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            if max_time < 5000:  # 5 seconds threshold
                self._record_result(test_name, "PERFORMANCE", start_time, "PASS", 
                                  f"Avg: {avg_time:.1f}ms, Max: {max_time:.1f}ms")
            else:
                self._record_result(test_name, "PERFORMANCE", start_time, "FAIL", 
                                  f"Slow responses - Max: {max_time:.1f}ms")
        except Exception as e:
            self._record_result(test_name, "PERFORMANCE", start_time, "FAIL", 
                              "Response time test failed", str(e))
    
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        start_time = time.time()
        test_name = "Concurrent Requests"
        
        try:
            # Make 5 concurrent requests
            tasks = []
            for i in range(5):
                task = self._make_request("POST", "/price", {"symbol": "BTC/USDT"})
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            
            if successful == len(tasks):
                self._record_result(test_name, "PERFORMANCE", start_time, "PASS", 
                                  f"All {len(tasks)} concurrent requests succeeded")
            else:
                self._record_result(test_name, "PERFORMANCE", start_time, "FAIL", 
                                  f"Only {successful}/{len(tasks)} requests succeeded")
        except Exception as e:
            self._record_result(test_name, "PERFORMANCE", start_time, "FAIL", 
                              "Concurrent request test failed", str(e))
    
    # =================== FUNCTIONAL REQUIREMENTS TESTS ===================
    
    async def test_volume_display_enhancements(self):
        """Test enhanced volume display (native + USD)"""
        start_time = time.time()
        test_name = "Volume Display Enhancement"
        
        try:
            result = await self._make_request("POST", "/combined_price", {"symbol": "BTC-USDT"})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                issues = []
                
                # Check spot volume
                if "spot" in data and data["spot"]:
                    spot = data["spot"]
                    if spot.get("volume_24h") is None:
                        issues.append("Missing spot volume")
                    elif spot["volume_24h"] <= 0:
                        issues.append("Invalid spot volume")
                
                # Check perp volume
                if "perp" in data and data["perp"]:
                    perp = data["perp"]
                    if perp.get("volume_24h") is None:
                        issues.append("Missing perp volume")
                    elif perp["volume_24h"] <= 0:
                        issues.append("Invalid perp volume")
                
                if not issues:
                    self._record_result(test_name, "FUNCTIONAL", start_time, "PASS", 
                                      "Volume data available for USD conversion")
                else:
                    self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                      f"Volume issues: {', '.join(issues)}")
            else:
                self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                  f"API error: {result}")
        except Exception as e:
            self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                              "Volume display test failed", str(e))
    
    async def test_market_cap_ranking(self):
        """Test market cap proxy for ranking"""
        start_time = time.time()
        test_name = "Market Cap Ranking"
        
        try:
            result = await self._make_request("POST", "/top_symbols", {
                "market_type": "spot",
                "limit": 5
            })
            
            if result.get("success") and "data" in result:
                symbols = result["data"]["symbols"]
                
                if len(symbols) >= 2:
                    # Check if ranking is by market cap proxy (price * volume)
                    market_caps = []
                    for symbol in symbols:
                        price = symbol.get("price", 0)
                        volume = symbol.get("volume_24h", 0) or 0
                        market_cap = price * volume
                        market_caps.append(market_cap)
                    
                    # Check if descending order (highest market cap first)
                    is_sorted = all(market_caps[i] >= market_caps[i+1] for i in range(len(market_caps)-1))
                    
                    if is_sorted:
                        top_mcap = market_caps[0] / 1e6  # Convert to millions
                        self._record_result(test_name, "FUNCTIONAL", start_time, "PASS", 
                                          f"Properly ranked by market cap proxy, top: ${top_mcap:.1f}M")
                    else:
                        self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                          "Symbols not properly ranked by market cap")
                else:
                    self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                      "Not enough symbols to test ranking")
            else:
                self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                  f"API error: {result}")
        except Exception as e:
            self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                              "Market cap ranking test failed", str(e))
    
    async def test_symbol_filtering(self):
        """Test proper symbol filtering logic"""
        start_time = time.time()
        test_name = "Symbol Filtering Logic"
        
        try:
            # Test spot filtering
            spot_result = await self._make_request("POST", "/top_symbols", {
                "market_type": "spot",
                "limit": 10
            })
            
            if spot_result.get("success"):
                spot_symbols = spot_result["data"]["symbols"]
                
                # Check filtering criteria
                issues = []
                for symbol_data in spot_symbols:
                    symbol = symbol_data["symbol"]
                    
                    # Should end with /USDT
                    if not symbol.endswith("/USDT"):
                        issues.append(f"Spot symbol {symbol} doesn't end with /USDT")
                    
                    # Should not contain colon (not perp)
                    if ":" in symbol:
                        issues.append(f"Spot symbol {symbol} contains colon")
                    
                    # Should not contain test tokens
                    test_tokens = ["UP", "DOWN", "BULL", "BEAR"]
                    if any(token in symbol for token in test_tokens):
                        issues.append(f"Spot symbol {symbol} contains test tokens")
                
                if not issues:
                    self._record_result(test_name, "FUNCTIONAL", start_time, "PASS", 
                                      f"Spot filtering correct for {len(spot_symbols)} symbols")
                else:
                    self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                      f"Spot filtering issues: {issues[:3]}")  # Show first 3
            else:
                self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                  f"Spot API error: {spot_result}")
                
        except Exception as e:
            self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                              "Symbol filtering test failed", str(e))
    
    async def test_perp_symbol_format(self):
        """Test perpetual symbol format handling"""
        start_time = time.time()
        test_name = "Perpetual Symbol Format"
        
        try:
            perp_result = await self._make_request("POST", "/top_symbols", {
                "market_type": "perp",
                "limit": 5
            })
            
            if perp_result.get("success"):
                perp_symbols = perp_result["data"]["symbols"]
                
                if perp_symbols:
                    issues = []
                    for symbol_data in perp_symbols:
                        symbol = symbol_data["symbol"]
                        
                        # Should be in format BTC/USDT:USDT for USD-M futures
                        if not symbol.endswith(":USDT"):
                            issues.append(f"Perp symbol {symbol} doesn't end with :USDT")
                        
                        if "/USDT:" not in symbol:
                            issues.append(f"Perp symbol {symbol} not in correct format")
                    
                    if not issues:
                        self._record_result(test_name, "FUNCTIONAL", start_time, "PASS", 
                                          f"Perp format correct for {len(perp_symbols)} symbols")
                    else:
                        self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                          f"Perp format issues: {issues[:3]}")
                else:
                    self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                      "No perp symbols returned")
            else:
                self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                  f"Perp API error: {perp_result}")
        except Exception as e:
            self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                              "Perp symbol format test failed", str(e))
    
    # =================== ERROR HANDLING TESTS ===================
    
    async def test_error_handling(self):
        """Test error handling for various edge cases"""
        start_time = time.time()
        test_name = "Error Handling"
        
        try:
            error_cases = [
                ("Empty symbol", "/price", {"symbol": ""}),
                ("Null symbol", "/price", {"symbol": None}),
                ("Invalid market type", "/top_symbols", {"market_type": "invalid"}),
                ("Negative limit", "/top_symbols", {"market_type": "spot", "limit": -1}),
                ("Missing required field", "/price", {}),
            ]
            
            passed_cases = 0
            total_cases = len(error_cases)
            
            for case_name, endpoint, data in error_cases:
                try:
                    result = await self._make_request("POST", endpoint, data)
                    
                    # Should return success=False for error cases
                    if not result.get("success", True):
                        passed_cases += 1
                except Exception:
                    # Exception is also acceptable for error handling
                    passed_cases += 1
            
            if passed_cases == total_cases:
                self._record_result(test_name, "FUNCTIONAL", start_time, "PASS", 
                                  f"All {total_cases} error cases handled correctly")
            else:
                self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                                  f"Only {passed_cases}/{total_cases} error cases handled")
        except Exception as e:
            self._record_result(test_name, "FUNCTIONAL", start_time, "FAIL", 
                              "Error handling test failed", str(e))
    
    # =================== MAIN TEST RUNNER ===================
    
    async def run_all_tests(self):
        """Run all tests in the suite"""
        print("🧪 Starting Comprehensive Test Suite for Crypto Trading Assistant")
        print("=" * 80)
        
        await self.setup()
        
        # Unit Tests
        print("\n📋 UNIT TESTS")
        print("-" * 40)
        await self.test_health_endpoint()
        await self.test_price_endpoint_valid_symbol()
        await self.test_price_endpoint_invalid_symbol()
        await self.test_combined_price_endpoint()
        await self.test_top_symbols_spot()
        await self.test_top_symbols_perp()
        await self.test_debug_tickers_endpoint()
        
        # Integration Tests
        print("\n🔗 INTEGRATION TESTS")
        print("-" * 40)
        await self.test_symbol_formatting_consistency()
        await self.test_exchange_data_fetching()
        await self.test_perp_enhanced_data()
        
        # Performance Tests
        print("\n⚡ PERFORMANCE TESTS")
        print("-" * 40)
        await self.test_response_times()
        await self.test_concurrent_requests()
        
        # Functional Tests
        print("\n✨ FUNCTIONAL REQUIREMENTS TESTS")
        print("-" * 40)
        await self.test_volume_display_enhancements()
        await self.test_market_cap_ranking()
        await self.test_symbol_filtering()
        await self.test_perp_symbol_format()
        await self.test_error_handling()
        
        await self.teardown()
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive test summary report"""
        print("\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY REPORT")
        print("=" * 80)
        
        # Count results by type and status
        by_type = {}
        by_status = {"PASS": 0, "FAIL": 0, "SKIP": 0}
        total_duration = 0
        
        for result in self.results:
            # By type
            if result.test_type not in by_type:
                by_type[result.test_type] = {"PASS": 0, "FAIL": 0, "SKIP": 0}
            by_type[result.test_type][result.status] += 1
            
            # Overall status
            by_status[result.status] += 1
            total_duration += result.duration_ms
        
        # Overall Statistics
        total_tests = len(self.results)
        pass_rate = (by_status["PASS"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {by_status['PASS']} ({pass_rate:.1f}%)")
        print(f"   Failed: {by_status['FAIL']}")
        print(f"   Skipped: {by_status['SKIP']}")
        print(f"   Total Duration: {total_duration:.1f}ms")
        print(f"   Average Duration: {total_duration/total_tests:.1f}ms per test")
        
        # By Test Type
        print(f"\n📋 RESULTS BY TEST TYPE:")
        for test_type, counts in by_type.items():
            total_type = sum(counts.values())
            pass_rate_type = (counts["PASS"] / total_type * 100) if total_type > 0 else 0
            print(f"   {test_type:12} | Pass: {counts['PASS']:2d} | Fail: {counts['FAIL']:2d} | Rate: {pass_rate_type:5.1f}%")
        
        # Failed Tests Details
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for i, result in enumerate(failed_tests, 1):
                print(f"   {i}. {result.test_name} ({result.test_type})")
                print(f"      Issue: {result.details}")
                if result.error:
                    print(f"      Error: {result.error}")
        
        # Critical Issues Found
        critical_issues = []
        
        # Check for critical failures
        critical_endpoints = ["Health Endpoint", "Price Endpoint - Valid Symbol", "Combined Price Endpoint"]
        for result in self.results:
            if result.test_name in critical_endpoints and result.status == "FAIL":
                critical_issues.append(f"Critical endpoint failure: {result.test_name}")
        
        # Check for performance issues
        slow_tests = [r for r in self.results if r.test_type == "PERFORMANCE" and r.status == "FAIL"]
        if slow_tests:
            critical_issues.append("Performance issues detected")
        
        # Check for functional requirement failures
        functional_failures = [r for r in self.results if r.test_type == "FUNCTIONAL" and r.status == "FAIL"]
        if len(functional_failures) > len(by_type.get("FUNCTIONAL", {}).values()) * 0.5:
            critical_issues.append("Multiple functional requirement failures")
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
            for issue in critical_issues:
                print(f"   • {issue}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if by_status["FAIL"] == 0:
            print("   ✅ All tests passed! System is functioning correctly.")
        else:
            if any("endpoint failed" in r.error or "" for r in failed_tests if r.error):
                print("   • Check service connectivity and configuration")
            
            if any("perp" in r.test_name.lower() for r in failed_tests):
                print("   • Review perpetual futures configuration and Binance futures API")
            
            if any("symbol" in r.test_name.lower() for r in failed_tests):
                print("   • Verify symbol filtering and formatting logic")
            
            if any("performance" in r.test_type.lower() for r in failed_tests):
                print("   • Optimize API response times and concurrent handling")
        
        print("\n" + "=" * 80)
        
        # Set overall test suite status
        if by_status["FAIL"] == 0:
            print("🎉 TEST SUITE STATUS: ALL TESTS PASSED")
        elif len(critical_issues) > 0:
            print("🚨 TEST SUITE STATUS: CRITICAL ISSUES FOUND")
        else:
            print("⚠️  TEST SUITE STATUS: SOME TESTS FAILED")
        
        print("=" * 80)

# Run the test suite
async def main():
    suite = TestSuite()
    await suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())