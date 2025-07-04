#!/usr/bin/env python3
"""
Comprehensive Testing Script for Crypto Trading Bot
Tests all functionality including API endpoints, Telegram bot commands, and performance.
"""
import asyncio
import aiohttp
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoTradingBotTester:
    def __init__(self):
        # Bot configuration
        self.bot_token = "8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
        self.webhook_url = "http://13.239.14.166:8080"
        self.market_data_url = "http://13.239.14.166:8001"
        
        # Test results storage
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": {},
            "bot_tests": {},
            "performance_tests": {},
            "errors": []
        }
        
        # Test symbols and parameters
        self.test_symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "BTC", "ETH"]
        self.test_timeframes = ["15m", "1h", "4h"]
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Starting Comprehensive Bot Testing")
        print("=" * 50)
        
        # 1. Test API endpoints
        await self.test_api_endpoints()
        
        # 2. Test basic bot functionality
        await self.test_bot_health()
        
        # 3. Test market data commands
        await self.test_market_commands()
        
        # 4. Test advanced features
        await self.test_advanced_features()
        
        # 5. Test error handling
        await self.test_error_handling()
        
        # 6. Performance testing
        await self.test_performance()
        
        # 7. Generate report
        self.generate_report()
        
    async def test_api_endpoints(self):
        """Test market data API endpoints directly"""
        print("\n🔌 Testing API Endpoints")
        print("-" * 30)
        
        # Test health endpoint
        await self._test_endpoint("health", "GET", {}, expected_status=200)
        
        # Test price endpoint
        await self._test_endpoint("price", "POST", {"symbol": "BTC-USDT"})
        
        # Test combined price endpoint
        await self._test_endpoint("combined_price", "POST", {"symbol": "BTC-USDT"})
        
        # Test comprehensive analysis
        await self._test_endpoint("comprehensive_analysis", "POST", {
            "symbol": "BTC-USDT",
            "timeframe": "15m"
        })
        
        # Test volume analysis
        await self._test_endpoint("volume_spike", "POST", {
            "symbol": "BTC-USDT",
            "timeframe": "15m"
        })
        
        # Test CVD analysis
        await self._test_endpoint("cvd", "POST", {
            "symbol": "BTC-USDT",
            "timeframe": "1h"
        })
        
        # Test OI analysis
        await self._test_endpoint("multi_oi", "POST", {"base_symbol": "BTC"})
        
        # Test volume scan
        await self._test_endpoint("volume_scan", "POST", {
            "timeframe": "15m",
            "min_spike": 200
        })
        
        # Test top symbols
        await self._test_endpoint("top_symbols", "POST", {
            "market_type": "spot",
            "limit": 10
        })
        
    async def test_bot_health(self):
        """Test basic bot functionality"""
        print("\n🤖 Testing Bot Health")
        print("-" * 30)
        
        # Test webhook health
        await self._test_bot_endpoint("health", "GET")
        
        # Test webhook endpoint
        await self._test_webhook_response()
        
    async def test_market_commands(self):
        """Test market data commands"""
        print("\n📊 Testing Market Commands")
        print("-" * 30)
        
        # Test various symbols and timeframes
        for symbol in self.test_symbols[:3]:  # Test top 3 symbols
            await self._test_market_command("price", symbol)
            await self._test_market_command("volume", symbol, "15m")
            await self._test_market_command("analysis", symbol, "15m")
            
    async def test_advanced_features(self):
        """Test advanced bot features"""
        print("\n🔬 Testing Advanced Features")
        print("-" * 30)
        
        # Test CVD analysis
        await self._test_market_command("cvd", "BTC-USDT", "1h")
        
        # Test OI analysis
        await self._test_market_command("oi", "BTC")
        
        # Test volume scanning
        await self._test_volume_scan()
        
        # Test top10 commands
        await self._test_top10_commands()
        
    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n❌ Testing Error Handling")
        print("-" * 30)
        
        # Test invalid symbols
        await self._test_market_command("price", "INVALID-SYMBOL")
        
        # Test invalid timeframes
        await self._test_market_command("analysis", "BTC-USDT", "invalid")
        
        # Test malformed requests
        await self._test_endpoint("comprehensive_analysis", "POST", {})
        
    async def test_performance(self):
        """Test system performance"""
        print("\n⚡ Testing Performance")
        print("-" * 30)
        
        # Test response times
        await self._test_response_times()
        
        # Test concurrent requests
        await self._test_concurrent_requests()
        
    async def _test_endpoint(self, endpoint: str, method: str, data: dict, expected_status: int = 200):
        """Test individual API endpoint"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = f"{self.market_data_url}/{endpoint}"
                
                if method == "GET":
                    async with session.get(url) as response:
                        response_data = await response.json()
                        status = response.status
                elif method == "POST":
                    async with session.post(url, json=data) as response:
                        response_data = await response.json()
                        status = response.status
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response_time = time.time() - start_time
                
                # Record results
                self.test_results["api_tests"][endpoint] = {
                    "status": "PASS" if status == expected_status else "FAIL",
                    "response_time": response_time,
                    "status_code": status,
                    "has_data": bool(response_data.get("success") if isinstance(response_data, dict) else response_data)
                }
                
                status_icon = "✅" if status == expected_status else "❌"
                print(f"{status_icon} {endpoint}: {status} ({response_time:.2f}s)")
                
                return response_data
                
        except Exception as e:
            response_time = time.time() - start_time
            self.test_results["api_tests"][endpoint] = {
                "status": "ERROR",
                "error": str(e),
                "response_time": response_time
            }
            print(f"❌ {endpoint}: ERROR - {e}")
            return None
            
    async def _test_bot_endpoint(self, endpoint: str, method: str):
        """Test bot webhook endpoint"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                url = f"{self.webhook_url}/{endpoint}"
                
                if method == "GET":
                    async with session.get(url) as response:
                        response_data = await response.json()
                        status = response.status
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response_time = time.time() - start_time
                
                # Record results
                self.test_results["bot_tests"][endpoint] = {
                    "status": "PASS" if status == 200 else "FAIL",
                    "response_time": response_time,
                    "status_code": status,
                    "data": response_data
                }
                
                status_icon = "✅" if status == 200 else "❌"
                print(f"{status_icon} Bot {endpoint}: {status} ({response_time:.2f}s)")
                
                return response_data
                
        except Exception as e:
            response_time = time.time() - start_time
            self.test_results["bot_tests"][endpoint] = {
                "status": "ERROR",
                "error": str(e),
                "response_time": response_time
            }
            print(f"❌ Bot {endpoint}: ERROR - {e}")
            return None
            
    async def _test_webhook_response(self):
        """Test webhook can receive and process updates"""
        print("🔗 Testing webhook response capability...")
        
        # We can't directly test webhook without sending actual Telegram updates
        # But we can test the webhook URL is accessible
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(f"{self.webhook_url}/webhook", json={}) as response:
                    # Expect 400 for empty payload (this is normal)
                    if response.status in [200, 400]:
                        print("✅ Webhook endpoint accessible")
                        self.test_results["bot_tests"]["webhook"] = {"status": "PASS"}
                    else:
                        print(f"❌ Webhook returned {response.status}")
                        self.test_results["bot_tests"]["webhook"] = {"status": "FAIL"}
                        
        except Exception as e:
            print(f"❌ Webhook test failed: {e}")
            self.test_results["bot_tests"]["webhook"] = {"status": "ERROR", "error": str(e)}
            
    async def _test_market_command(self, command: str, symbol: str, timeframe: str = None):
        """Test market command functionality by calling API directly"""
        print(f"📊 Testing {command} command for {symbol}")
        
        # Map commands to API endpoints
        command_map = {
            "price": ("combined_price", {"symbol": symbol}),
            "volume": ("volume_spike", {"symbol": symbol, "timeframe": timeframe or "15m"}),
            "analysis": ("comprehensive_analysis", {"symbol": symbol, "timeframe": timeframe or "15m"}),
            "cvd": ("cvd", {"symbol": symbol, "timeframe": timeframe or "1h"}),
            "oi": ("multi_oi", {"base_symbol": symbol})
        }
        
        if command in command_map:
            endpoint, data = command_map[command]
            result = await self._test_endpoint(endpoint, "POST", data)
            
            # Record command-specific results
            self.test_results["bot_tests"][f"{command}_{symbol}"] = {
                "status": "PASS" if result else "FAIL",
                "symbol": symbol,
                "timeframe": timeframe
            }
            
    async def _test_volume_scan(self):
        """Test volume scanning functionality"""
        print("🔍 Testing volume scan...")
        await self._test_endpoint("volume_scan", "POST", {
            "timeframe": "15m",
            "min_spike": 200
        })
        
    async def _test_top10_commands(self):
        """Test top10 commands"""
        print("🏆 Testing top10 commands...")
        await self._test_endpoint("top_symbols", "POST", {
            "market_type": "spot",
            "limit": 10
        })
        
        await self._test_endpoint("top_symbols", "POST", {
            "market_type": "perp",
            "limit": 10
        })
        
    async def _test_response_times(self):
        """Test response times for critical endpoints"""
        print("⏱️ Testing response times...")
        
        critical_endpoints = [
            ("price", "POST", {"symbol": "BTC-USDT"}),
            ("comprehensive_analysis", "POST", {"symbol": "BTC-USDT", "timeframe": "15m"}),
            ("volume_spike", "POST", {"symbol": "BTC-USDT", "timeframe": "15m"})
        ]
        
        response_times = []
        for endpoint, method, data in critical_endpoints:
            start_time = time.time()
            result = await self._test_endpoint(endpoint, method, data)
            response_time = time.time() - start_time
            response_times.append(response_time)
            
        avg_response_time = sum(response_times) / len(response_times)
        self.test_results["performance_tests"]["average_response_time"] = avg_response_time
        
        print(f"📈 Average response time: {avg_response_time:.2f}s")
        
    async def _test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("🔄 Testing concurrent requests...")
        
        # Create multiple simultaneous requests
        tasks = []
        for i in range(5):
            task = self._test_endpoint("price", "POST", {"symbol": "BTC-USDT"})
            tasks.append(task)
            
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        concurrent_time = time.time() - start_time
        
        successful_requests = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        
        self.test_results["performance_tests"]["concurrent_requests"] = {
            "total_requests": len(tasks),
            "successful_requests": successful_requests,
            "total_time": concurrent_time,
            "success_rate": successful_requests / len(tasks) * 100
        }
        
        print(f"📊 Concurrent test: {successful_requests}/{len(tasks)} successful in {concurrent_time:.2f}s")
        
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📋 TEST REPORT")
        print("=" * 50)
        
        # Summary statistics
        total_api_tests = len(self.test_results["api_tests"])
        passed_api_tests = sum(1 for test in self.test_results["api_tests"].values() if test.get("status") == "PASS")
        
        total_bot_tests = len(self.test_results["bot_tests"])
        passed_bot_tests = sum(1 for test in self.test_results["bot_tests"].values() if test.get("status") == "PASS")
        
        print(f"📊 API Tests: {passed_api_tests}/{total_api_tests} passed")
        print(f"🤖 Bot Tests: {passed_bot_tests}/{total_bot_tests} passed")
        
        # Performance metrics
        if "average_response_time" in self.test_results["performance_tests"]:
            avg_time = self.test_results["performance_tests"]["average_response_time"]
            print(f"⏱️ Average Response Time: {avg_time:.2f}s")
            
        if "concurrent_requests" in self.test_results["performance_tests"]:
            concurrent = self.test_results["performance_tests"]["concurrent_requests"]
            print(f"🔄 Concurrent Success Rate: {concurrent['success_rate']:.1f}%")
        
        # Detailed results
        print("\n📝 DETAILED RESULTS")
        print("-" * 30)
        
        print("\n🔌 API Endpoint Tests:")
        for endpoint, result in self.test_results["api_tests"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            time_info = f"({result['response_time']:.2f}s)" if "response_time" in result else ""
            print(f"{status_icon} {endpoint}: {result['status']} {time_info}")
            
        print("\n🤖 Bot Tests:")
        for test, result in self.test_results["bot_tests"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {test}: {result['status']}")
            
        # Error summary
        if self.test_results["errors"]:
            print("\n❌ ERRORS ENCOUNTERED:")
            for error in self.test_results["errors"]:
                print(f"- {error}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        # Check response times
        if "average_response_time" in self.test_results["performance_tests"]:
            if self.test_results["performance_tests"]["average_response_time"] > 5:
                print("- ⚠️ Response times are slow (>5s). Consider optimizing API calls.")
            else:
                print("- ✅ Response times are acceptable.")
        
        # Check API success rates
        api_success_rate = passed_api_tests / total_api_tests * 100 if total_api_tests > 0 else 0
        if api_success_rate < 80:
            print("- ❌ API success rate is below 80%. Check API connectivity and configurations.")
        else:
            print("- ✅ API success rate is good.")
        
        # Check bot functionality
        if passed_bot_tests < total_bot_tests:
            print("- ⚠️ Some bot tests failed. Check webhook configuration and bot token.")
        else:
            print("- ✅ Bot functionality is working correctly.")
            
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Full results saved to: test_results.json")
        print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main test runner"""
    tester = CryptoTradingBotTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())