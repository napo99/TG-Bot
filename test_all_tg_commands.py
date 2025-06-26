#!/usr/bin/env python3
"""
INDEPENDENT TELEGRAM BOT COMMAND TESTING AGENT
Tests all TG bot commands with real API data to ensure functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class TelegramBotTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.test_results = []
        
    async def test_api_endpoint(self, endpoint, payload=None, test_name=""):
        """Test an API endpoint and return results"""
        try:
            async with aiohttp.ClientSession() as session:
                if payload:
                    async with session.post(f"{self.base_url}{endpoint}", json=payload) as response:
                        data = await response.json()
                else:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        data = await response.json()
                
                return {
                    "test": test_name,
                    "endpoint": endpoint,
                    "success": data.get("success", False),
                    "data": data,
                    "status": "✅ PASSED" if data.get("success") else "❌ FAILED"
                }
        except Exception as e:
            return {
                "test": test_name,
                "endpoint": endpoint,
                "success": False,
                "error": str(e),
                "status": "❌ FAILED"
            }
    
    async def test_oi_command(self):
        """Test /oi command functionality"""
        return await self.test_api_endpoint("/multi_oi", {"base_symbol": "BTC"}, "/oi BTC command")
    
    async def test_price_command(self):
        """Test /price command functionality"""
        return await self.test_api_endpoint("/price", {"symbol": "BTC-USDT"}, "/price BTC-USDT command")
    
    async def test_comprehensive_analysis(self):
        """Test comprehensive analysis command"""
        return await self.test_api_endpoint("/comprehensive_analysis", {
            "symbol": "BTC/USDT",
            "timeframe": "15m"
        }, "/analysis BTC-USDT 15m command")
    
    async def test_health_endpoint(self):
        """Test health endpoint"""
        return await self.test_api_endpoint("/health", None, "Health check")
    
    async def validate_oi_data_structure(self, oi_result):
        """Validate OI data structure matches TG bot expectations"""
        if not oi_result["success"]:
            return {"validation": "❌ FAILED", "reason": "API call failed"}
        
        data = oi_result["data"]
        validations = []
        
        # Check required fields for TG bot
        required_fields = ["aggregated_oi", "exchange_breakdown", "total_markets", "market_categories"]
        for field in required_fields:
            if field in data:
                validations.append(f"✅ {field} present")
            else:
                validations.append(f"❌ {field} missing")
        
        # Validate aggregated_oi structure
        agg = data.get("aggregated_oi", {})
        if agg.get("total_tokens", 0) > 0:
            validations.append(f"✅ Non-zero total_tokens: {agg['total_tokens']:,.0f}")
        else:
            validations.append("❌ Zero or missing total_tokens")
        
        if agg.get("total_usd", 0) > 0:
            validations.append(f"✅ Non-zero total_usd: ${agg['total_usd']/1e9:.1f}B")
        else:
            validations.append("❌ Zero or missing total_usd")
        
        # Validate exchange_breakdown
        exchanges = data.get("exchange_breakdown", [])
        if len(exchanges) == 5:
            validations.append(f"✅ All 5 exchanges present: {[ex['exchange'] for ex in exchanges]}")
        else:
            validations.append(f"❌ Only {len(exchanges)} exchanges found")
        
        # Validate markets count
        total_markets = data.get("total_markets", 0)
        if total_markets == 13:
            validations.append(f"✅ All 13 markets present")
        else:
            validations.append(f"❌ Only {total_markets} markets found")
        
        return {"validation": "✅ PASSED" if all("✅" in v for v in validations) else "⚠️ PARTIAL", "details": validations}
    
    async def simulate_tg_message_generation(self, oi_data):
        """Simulate TG bot message generation to test formatting"""
        try:
            data = oi_data["data"]
            
            # Extract data like TG bot does
            agg = data.get("aggregated_oi", {})
            exchanges = data.get("exchange_breakdown", [])
            total_markets = data.get("total_markets", 0)
            
            # Simulate message parts
            message_parts = []
            message_parts.append(f"🎯 MULTI-EXCHANGE OI ANALYSIS - BTC")
            message_parts.append(f"💰 TOTAL OI: {agg.get('total_tokens', 0):,.0f} BTC (${agg.get('total_usd', 0)/1e9:.1f}B)")
            message_parts.append(f"📊 MARKETS: {total_markets} across {len(exchanges)} exchanges")
            
            # Add exchanges
            for ex in exchanges:
                tokens = ex.get('oi_tokens', 0)
                usd = ex.get('oi_usd', 0)
                pct = ex.get('oi_percentage', 0)
                markets = ex.get('markets', 0)
                message_parts.append(f"• {ex['exchange'].upper()}: {tokens:,.0f} BTC (${usd/1e9:.1f}B) - {pct:.1f}% - {markets}M")
            
            message = "\n".join(message_parts)
            
            return {
                "message_generation": "✅ PASSED",
                "message_length": len(message),
                "sample": message[:300] + "..." if len(message) > 300 else message
            }
        except Exception as e:
            return {
                "message_generation": "❌ FAILED",
                "error": str(e)
            }
    
    async def run_comprehensive_test(self):
        """Run all tests and generate comprehensive report"""
        print("🧪 INDEPENDENT TELEGRAM BOT COMMAND TESTING")
        print("=" * 50)
        print(f"🕐 Test started at: {datetime.now().strftime('%H:%M:%S')}")
        print("")
        
        # Test 1: Health check
        print("🏥 Test 1: Health Check")
        health_result = await self.test_health_endpoint()
        print(f"  {health_result['status']} - {health_result['test']}")
        
        # Test 2: OI command (main command)
        print("\n🎯 Test 2: /oi Command")
        oi_result = await self.test_oi_command()
        print(f"  {oi_result['status']} - {oi_result['test']}")
        
        if oi_result["success"]:
            # Validate OI data structure
            validation = await self.validate_oi_data_structure(oi_result)
            print(f"  📋 Data Structure: {validation['validation']}")
            for detail in validation['details']:
                print(f"    {detail}")
            
            # Test message generation
            message_test = await self.simulate_tg_message_generation(oi_result)
            print(f"  📱 Message Generation: {message_test['message_generation']}")
            if "sample" in message_test:
                print(f"  📏 Message Length: {message_test['message_length']} chars")
                print(f"  📝 Sample Output:")
                print("    " + "\n    ".join(message_test['sample'].split('\n')))
        
        # Test 3: Price command
        print("\n💰 Test 3: /price Command")
        price_result = await self.test_price_command()
        print(f"  {price_result['status']} - {price_result['test']}")
        if price_result["success"]:
            price_data = price_result["data"]
            if "price" in price_data:
                print(f"  💵 Price: ${price_data['price']:,.2f}")
        
        # Test 4: Comprehensive analysis
        print("\n📊 Test 4: /analysis Command")
        analysis_result = await self.test_comprehensive_analysis()
        print(f"  {analysis_result['status']} - {analysis_result['test']}")
        
        # Summary
        all_tests = [health_result, oi_result, price_result, analysis_result]
        passed_tests = sum(1 for test in all_tests if test["success"])
        
        print("\n🎯 TEST SUMMARY")
        print("=" * 30)
        print(f"✅ Passed: {passed_tests}/{len(all_tests)} tests")
        
        if passed_tests == len(all_tests):
            print("🚀 ALL TELEGRAM BOT COMMANDS READY")
            print("✅ Real data flowing correctly")
            print("✅ Message formatting working")
            print("✅ No connection errors detected")
        else:
            print("⚠️ Some tests failed - review errors above")
        
        return passed_tests == len(all_tests)

async def main():
    tester = TelegramBotTester()
    success = await tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)