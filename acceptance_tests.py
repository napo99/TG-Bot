#!/usr/bin/env python3
"""
Acceptance Tests for Crypto Trading Assistant
Tests user scenarios and enhanced features
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AcceptanceTestResult:
    scenario_name: str
    status: str  # PASS, FAIL
    execution_time_ms: float
    details: str
    user_story: str
    error: str = None

class AcceptanceTestSuite:
    def __init__(self, market_data_url: str = "http://localhost:8001"):
        self.market_data_url = market_data_url
        self.session = None
        self.results: List[AcceptanceTestResult] = []
    
    async def setup(self):
        """Setup test environment"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        print("🎭 Acceptance Test Suite initialized")
    
    async def teardown(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        print("🧹 Acceptance Test Suite cleaned up")
    
    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> Dict[str, Any]:
        """Make HTTP request to market data service"""
        url = f"{self.market_data_url}{endpoint}"
        
        if method.upper() == "GET":
            async with self.session.get(url) as response:
                return await response.json()
        elif method.upper() == "POST":
            async with self.session.post(url, json=data or {}) as response:
                return await response.json()
    
    def _record_result(self, scenario_name: str, user_story: str, start_time: float, 
                      status: str, details: str, error: str = None):
        """Record acceptance test result"""
        duration = (time.time() - start_time) * 1000
        result = AcceptanceTestResult(
            scenario_name=scenario_name,
            user_story=user_story,
            status=status,
            execution_time_ms=duration,
            details=details,
            error=error
        )
        self.results.append(result)
        
        # Print immediate result
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {scenario_name} ({duration:.1f}ms)")
        print(f"   📝 User Story: {user_story}")
        print(f"   📊 Result: {details}")
        if error:
            print(f"   🚨 Error: {error}")
        print()

    # =================== USER SCENARIO TESTS ===================
    
    async def test_user_requests_btc_price(self):
        """User sends /price BTC-USDT → receives spot + perp data"""
        start_time = time.time()
        scenario_name = "User Requests BTC Price"
        user_story = "As a user, I want to see both spot and perpetual prices for BTC when I send /price BTC-USDT"
        
        try:
            # Simulate user command: /price BTC-USDT
            result = await self._make_request("POST", "/combined_price", {"symbol": "BTC-USDT"})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                
                # Verify we get both spot and perp data
                has_spot = "spot" in data and data["spot"] is not None
                has_perp = "perp" in data and data["perp"] is not None
                
                if has_spot and has_perp:
                    spot_price = data["spot"]["price"]
                    perp_price = data["perp"]["price"]
                    
                    # Verify enhanced data
                    enhanced_features = []
                    if data["perp"].get("open_interest"):
                        enhanced_features.append(f"OI: {data['perp']['open_interest']:,.0f} BTC")
                    
                    if data["perp"].get("funding_rate") is not None:
                        funding = data["perp"]["funding_rate"] * 100
                        enhanced_features.append(f"Funding: {funding:.4f}%")
                    
                    # Check volume data for USD conversion
                    spot_volume = data["spot"].get("volume_24h", 0) or 0
                    perp_volume = data["perp"].get("volume_24h", 0) or 0
                    
                    details = f"Spot: ${spot_price:,.2f}, Perp: ${perp_price:,.2f}"
                    if enhanced_features:
                        details += f", Enhanced data: {', '.join(enhanced_features)}"
                    if spot_volume > 0 and perp_volume > 0:
                        details += f", Volume data available for USD conversion"
                    
                    self._record_result(scenario_name, user_story, start_time, "PASS", details)
                else:
                    missing = []
                    if not has_spot:
                        missing.append("spot")
                    if not has_perp:
                        missing.append("perp")
                    self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                      f"Missing data: {', '.join(missing)}")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  f"API error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self._record_result(scenario_name, user_story, start_time, "FAIL", 
                              "Request failed", str(e))
    
    async def test_user_requests_top10_spot(self):
        """User sends /top10 spot → receives top 10 spot markets with MCap"""
        start_time = time.time()
        scenario_name = "User Requests Top 10 Spot Markets"
        user_story = "As a user, I want to see the top 10 spot markets ranked by market cap proxy with volume in both native tokens and USD"
        
        try:
            # Simulate user command: /top10 spot
            result = await self._make_request("POST", "/top_symbols", {
                "market_type": "spot",
                "limit": 10
            })
            
            if result.get("success") and "data" in result:
                symbols = result["data"]["symbols"]
                
                if len(symbols) >= 10:
                    # Verify ranking by market cap proxy
                    market_caps = []
                    valid_symbols = 0
                    volume_data_available = 0
                    
                    for symbol in symbols:
                        price = symbol.get("price", 0)
                        volume = symbol.get("volume_24h", 0) or 0
                        
                        if price > 0 and volume > 0:
                            valid_symbols += 1
                            volume_data_available += 1
                            market_cap = price * volume
                            market_caps.append(market_cap)
                        else:
                            market_caps.append(0)
                    
                    # Check if properly sorted (descending)
                    is_sorted = all(market_caps[i] >= market_caps[i+1] for i in range(len(market_caps)-1))
                    
                    # Check symbol filtering
                    proper_symbols = sum(1 for s in symbols if s["symbol"].endswith("/USDT") and ":" not in s["symbol"])
                    
                    details = f"Got {len(symbols)} symbols, {valid_symbols} with valid data, "
                    details += f"{volume_data_available} with volume data for USD conversion"
                    
                    if is_sorted and proper_symbols == len(symbols) and volume_data_available >= 8:
                        top_mcap = market_caps[0] / 1e6 if market_caps[0] > 0 else 0
                        details += f", Top market cap: ${top_mcap:.1f}M, Properly sorted and filtered"
                        self._record_result(scenario_name, user_story, start_time, "PASS", details)
                    else:
                        issues = []
                        if not is_sorted:
                            issues.append("not sorted by market cap")
                        if proper_symbols != len(symbols):
                            issues.append("improper symbol filtering")
                        if volume_data_available < 8:
                            issues.append("insufficient volume data")
                        details += f", Issues: {', '.join(issues)}"
                        self._record_result(scenario_name, user_story, start_time, "FAIL", details)
                else:
                    self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                      f"Only got {len(symbols)} symbols, expected 10")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  f"API error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self._record_result(scenario_name, user_story, start_time, "FAIL", 
                              "Request failed", str(e))
    
    async def test_user_requests_top10_perps(self):
        """User sends /top10 perps → receives perp data with OI + funding"""
        start_time = time.time()
        scenario_name = "User Requests Top 10 Perpetual Markets"
        user_story = "As a user, I want to see the top 10 perpetual markets with Open Interest and Funding Rates data"
        
        try:
            # Simulate user command: /top10 perps
            result = await self._make_request("POST", "/top_symbols", {
                "market_type": "perp",
                "limit": 10
            })
            
            if result.get("success") and "data" in result:
                symbols = result["data"]["symbols"]
                
                if len(symbols) > 0:
                    # Check enhanced perp features
                    symbols_with_oi = sum(1 for s in symbols if s.get("open_interest") is not None)
                    symbols_with_funding = sum(1 for s in symbols if s.get("funding_rate") is not None)
                    
                    # Check proper perp symbol format
                    proper_perp_symbols = sum(1 for s in symbols if s["symbol"].endswith(":USDT") and "/USDT:" in s["symbol"])
                    
                    # Check volume data for USD conversion
                    symbols_with_volume = sum(1 for s in symbols if s.get("volume_24h", 0) and s.get("volume_24h") > 0)
                    
                    # Verify market type
                    perp_market_types = sum(1 for s in symbols if s.get("market_type") == "perp")
                    
                    details = f"Got {len(symbols)} perp symbols, "
                    details += f"{symbols_with_oi} with OI data, "
                    details += f"{symbols_with_funding} with funding rates, "
                    details += f"{symbols_with_volume} with volume data, "
                    details += f"{proper_perp_symbols} with correct format"
                    
                    # Success criteria: most symbols have enhanced data and proper format
                    success_criteria = (
                        symbols_with_oi >= len(symbols) * 0.5 and  # At least 50% have OI
                        symbols_with_funding >= len(symbols) * 0.3 and  # At least 30% have funding
                        proper_perp_symbols == len(symbols) and  # All have correct format
                        perp_market_types == len(symbols) and  # All marked as perp
                        symbols_with_volume >= len(symbols) * 0.8  # At least 80% have volume
                    )
                    
                    if success_criteria:
                        # Show example data
                        example = symbols[0]
                        example_details = f"Example: {example['symbol']}, Price: ${example['price']:,.4f}"
                        if example.get("open_interest"):
                            example_details += f", OI: {example['open_interest']:,.0f}"
                        if example.get("funding_rate") is not None:
                            fr = example["funding_rate"] * 100
                            example_details += f", Funding: {fr:.4f}%"
                        
                        details += f". {example_details}"
                        self._record_result(scenario_name, user_story, start_time, "PASS", details)
                    else:
                        issues = []
                        if symbols_with_oi < len(symbols) * 0.5:
                            issues.append("insufficient OI data")
                        if symbols_with_funding < len(symbols) * 0.3:
                            issues.append("insufficient funding data")
                        if proper_perp_symbols != len(symbols):
                            issues.append("incorrect symbol format")
                        if perp_market_types != len(symbols):
                            issues.append("incorrect market type")
                        if symbols_with_volume < len(symbols) * 0.8:
                            issues.append("insufficient volume data")
                        
                        details += f". Issues: {', '.join(issues)}"
                        self._record_result(scenario_name, user_story, start_time, "FAIL", details)
                else:
                    self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                      "No perpetual symbols returned")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  f"API error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self._record_result(scenario_name, user_story, start_time, "FAIL", 
                              "Request failed", str(e))
    
    async def test_user_requests_invalid_symbol(self):
        """User sends invalid symbol → receives proper error message"""
        start_time = time.time()
        scenario_name = "User Requests Invalid Symbol"
        user_story = "As a user, I want to receive a clear error message when I request an invalid symbol"
        
        try:
            # Simulate user command: /price INVALID-SYMBOL
            result = await self._make_request("POST", "/combined_price", {"symbol": "INVALID-SYMBOL"})
            
            # Should either return success=False or have empty data
            if not result.get("success"):
                self._record_result(scenario_name, user_story, start_time, "PASS", 
                                  f"Properly handled invalid symbol with error: {result.get('error', 'Unknown error')}")
            elif result.get("success") and "data" in result:
                data = result["data"]
                has_any_data = (
                    ("spot" in data and data["spot"] is not None) or 
                    ("perp" in data and data["perp"] is not None)
                )
                
                if not has_any_data:
                    self._record_result(scenario_name, user_story, start_time, "PASS", 
                                      "Properly handled invalid symbol with empty data")
                else:
                    self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                      "Invalid symbol returned data unexpectedly")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  "Unexpected response format")
        except Exception as e:
            # Exception is acceptable for invalid symbol
            self._record_result(scenario_name, user_story, start_time, "PASS", 
                              "Properly threw exception for invalid symbol")
    
    async def test_volume_display_calculation(self):
        """Test volume display shows both native token and USD equivalent"""
        start_time = time.time()
        scenario_name = "Volume Display Calculation"
        user_story = "As a user, I want to see trading volume in both native tokens and USD equivalent"
        
        try:
            # Get BTC data which should have good volume
            result = await self._make_request("POST", "/combined_price", {"symbol": "BTC-USDT"})
            
            if result.get("success") and "data" in result:
                data = result["data"]
                calculations = []
                
                # Check spot volume calculation
                if "spot" in data and data["spot"]:
                    spot = data["spot"]
                    price = spot["price"]
                    volume_native = spot.get("volume_24h", 0) or 0
                    
                    if price > 0 and volume_native > 0:
                        volume_usd = volume_native * price
                        calculations.append(f"Spot: {volume_native:,.0f} BTC = ${volume_usd/1e6:.1f}M")
                
                # Check perp volume calculation
                if "perp" in data and data["perp"]:
                    perp = data["perp"]
                    price = perp["price"]
                    volume_native = perp.get("volume_24h", 0) or 0
                    
                    if price > 0 and volume_native > 0:
                        volume_usd = volume_native * price
                        calculations.append(f"Perp: {volume_native:,.0f} BTC = ${volume_usd/1e6:.1f}M")
                
                if len(calculations) >= 1:
                    self._record_result(scenario_name, user_story, start_time, "PASS", 
                                      f"Volume calculations possible: {', '.join(calculations)}")
                else:
                    self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                      "No volume data available for USD conversion")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  f"API error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self._record_result(scenario_name, user_story, start_time, "FAIL", 
                              "Volume calculation test failed", str(e))
    
    async def test_funding_rate_display(self):
        """Test funding rate display for perpetuals"""
        start_time = time.time()
        scenario_name = "Funding Rate Display"
        user_story = "As a user, I want to see current funding rates for perpetual contracts"
        
        try:
            # Test with multiple symbols to find funding rate data
            test_symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
            funding_rates_found = []
            
            for symbol in test_symbols:
                result = await self._make_request("POST", "/combined_price", {"symbol": symbol})
                
                if result.get("success") and "data" in result:
                    data = result["data"]
                    
                    if "perp" in data and data["perp"] and data["perp"].get("funding_rate") is not None:
                        funding_rate = data["perp"]["funding_rate"] * 100  # Convert to percentage
                        funding_rates_found.append(f"{symbol}: {funding_rate:.4f}%")
            
            if len(funding_rates_found) > 0:
                self._record_result(scenario_name, user_story, start_time, "PASS", 
                                  f"Funding rates available: {', '.join(funding_rates_found)}")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  "No funding rate data available for tested symbols")
        except Exception as e:
            self._record_result(scenario_name, user_story, start_time, "FAIL", 
                              "Funding rate test failed", str(e))
    
    async def test_open_interest_display(self):
        """Test open interest display for perpetuals"""
        start_time = time.time()
        scenario_name = "Open Interest Display"
        user_story = "As a user, I want to see open interest data for perpetual contracts"
        
        try:
            # Test with multiple symbols to find OI data
            test_symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
            oi_data_found = []
            
            for symbol in test_symbols:
                result = await self._make_request("POST", "/combined_price", {"symbol": symbol})
                
                if result.get("success") and "data" in result:
                    data = result["data"]
                    
                    if "perp" in data and data["perp"] and data["perp"].get("open_interest"):
                        oi = data["perp"]["open_interest"]
                        oi_usd = oi * data["perp"]["price"]
                        base_token = symbol.split('-')[0]
                        oi_data_found.append(f"{symbol}: {oi:,.0f} {base_token} (${oi_usd/1e6:.0f}M)")
            
            if len(oi_data_found) > 0:
                self._record_result(scenario_name, user_story, start_time, "PASS", 
                                  f"Open Interest data available: {', '.join(oi_data_found)}")
            else:
                self._record_result(scenario_name, user_story, start_time, "FAIL", 
                                  "No open interest data available for tested symbols")
        except Exception as e:
            self._record_result(scenario_name, user_story, start_time, "FAIL", 
                              "Open interest test failed", str(e))
    
    # =================== MAIN TEST RUNNER ===================
    
    async def run_all_acceptance_tests(self):
        """Run all acceptance tests"""
        print("🎭 Starting Acceptance Tests for Crypto Trading Assistant")
        print("Testing User Stories and Enhanced Features")
        print("=" * 80)
        
        await self.setup()
        
        # Core User Scenarios
        print("\n👤 CORE USER SCENARIOS")
        print("-" * 50)
        await self.test_user_requests_btc_price()
        await self.test_user_requests_top10_spot()
        await self.test_user_requests_top10_perps()
        await self.test_user_requests_invalid_symbol()
        
        # Enhanced Features
        print("\n✨ ENHANCED FEATURES VALIDATION")
        print("-" * 50)
        await self.test_volume_display_calculation()
        await self.test_funding_rate_display()
        await self.test_open_interest_display()
        
        await self.teardown()
        
        # Generate summary report
        self.generate_acceptance_report()
    
    def generate_acceptance_report(self):
        """Generate acceptance test summary report"""
        print("\n" + "=" * 80)
        print("🎯 ACCEPTANCE TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Scenarios: {total_tests}")
        print(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"   Failed: {failed_tests}")
        
        # User Stories Results
        print(f"\n📖 USER STORIES RESULTS:")
        for result in self.results:
            status_emoji = "✅" if result.status == "PASS" else "❌"
            print(f"   {status_emoji} {result.scenario_name}")
            print(f"      Story: {result.user_story}")
            print(f"      Result: {result.details}")
            if result.error:
                print(f"      Error: {result.error}")
            print()
        
        # Critical Features Assessment
        critical_features = {
            "Combined Price Display": any("BTC Price" in r.scenario_name for r in self.results if r.status == "PASS"),
            "Top Spot Markets": any("Top 10 Spot" in r.scenario_name for r in self.results if r.status == "PASS"),
            "Top Perp Markets": any("Top 10 Perpetual" in r.scenario_name for r in self.results if r.status == "PASS"),
            "Volume USD Conversion": any("Volume Display" in r.scenario_name for r in self.results if r.status == "PASS"),
            "Funding Rates": any("Funding Rate" in r.scenario_name for r in self.results if r.status == "PASS"),
            "Open Interest": any("Open Interest" in r.scenario_name for r in self.results if r.status == "PASS"),
            "Error Handling": any("Invalid Symbol" in r.scenario_name for r in self.results if r.status == "PASS")
        }
        
        print(f"\n🎯 CRITICAL FEATURES STATUS:")
        for feature, working in critical_features.items():
            status = "✅ WORKING" if working else "❌ ISSUES"
            print(f"   {feature:.<25} {status}")
        
        # Enhanced Features Assessment
        enhancement_score = sum(1 for working in critical_features.values() if working)
        total_features = len(critical_features)
        
        print(f"\n🚀 ENHANCEMENT IMPLEMENTATION SCORE:")
        print(f"   {enhancement_score}/{total_features} features working ({enhancement_score/total_features*100:.1f}%)")
        
        if enhancement_score == total_features:
            print(f"   🎉 All enhanced features are fully functional!")
        elif enhancement_score >= total_features * 0.8:
            print(f"   ✅ Most enhanced features are working well")
        else:
            print(f"   ⚠️  Several enhanced features need attention")
        
        # Recommendations
        failed_scenarios = [r for r in self.results if r.status == "FAIL"]
        if failed_scenarios:
            print(f"\n🔧 RECOMMENDATIONS:")
            for result in failed_scenarios:
                print(f"   • Fix {result.scenario_name}: {result.details}")
        
        print("\n" + "=" * 80)

# Run the acceptance test suite
async def main():
    suite = AcceptanceTestSuite()
    await suite.run_all_acceptance_tests()

if __name__ == "__main__":
    asyncio.run(main())