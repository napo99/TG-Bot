#!/usr/bin/env python3
"""
Telegram Bot Verification Script
Tests all endpoints and bot functionality to ensure everything is working properly.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class BotVerifier:
    def __init__(self):
        self.market_data_url = "http://localhost:8001"
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.results = []
    
    def log_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status} {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   🚨 {error}")
    
    async def test_market_data_health(self):
        """Test market data service health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.market_data_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_result("Market Data Health", True, f"Service: {data.get('service')}")
                    else:
                        self.log_result("Market Data Health", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("Market Data Health", False, error=str(e))
    
    async def test_volume_spike_endpoint(self):
        """Test volume spike endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"symbol": "BTCUSDT", "timeframe": "15m"}
                async with session.post(f"{self.market_data_url}/volume_spike", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            spike_data = data['data']
                            self.log_result("Volume Spike Endpoint", True, 
                                          f"BTCUSDT spike: {spike_data.get('spike_level')} ({spike_data.get('spike_percentage', 0):+.1f}%)")
                        else:
                            self.log_result("Volume Spike Endpoint", False, error=data.get('error', 'Unknown error'))
                    else:
                        self.log_result("Volume Spike Endpoint", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("Volume Spike Endpoint", False, error=str(e))
    
    async def test_cvd_endpoint(self):
        """Test CVD endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"symbol": "BTCUSDT", "timeframe": "15m"}
                async with session.post(f"{self.market_data_url}/cvd", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            cvd_data = data['data']
                            self.log_result("CVD Endpoint", True, 
                                          f"BTCUSDT CVD: {cvd_data.get('cvd_trend')} ({cvd_data.get('current_cvd', 0):,.0f})")
                        else:
                            self.log_result("CVD Endpoint", False, error=data.get('error', 'Unknown error'))
                    else:
                        self.log_result("CVD Endpoint", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("CVD Endpoint", False, error=str(e))
    
    async def test_comprehensive_analysis(self):
        """Test comprehensive analysis endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"symbol": "BTCUSDT", "timeframe": "15m"}
                async with session.post(f"{self.market_data_url}/comprehensive_analysis", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            analysis = data['data']
                            price = analysis.get('price_data', {}).get('current_price', 0)
                            sentiment = analysis.get('market_sentiment', {}).get('market_control', 'UNKNOWN')
                            self.log_result("Comprehensive Analysis", True, 
                                          f"BTCUSDT: ${price:,.2f}, Control: {sentiment}")
                        else:
                            self.log_result("Comprehensive Analysis", False, error=data.get('error', 'Unknown error'))
                    else:
                        self.log_result("Comprehensive Analysis", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("Comprehensive Analysis", False, error=str(e))
    
    async def test_bot_token(self):
        """Test bot token validity"""
        if not self.bot_token:
            self.log_result("Bot Token", False, error="TELEGRAM_BOT_TOKEN not found in environment")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            bot_info = data['result']
                            self.log_result("Bot Token", True, 
                                          f"Bot: @{bot_info.get('username')} ({bot_info.get('first_name')})")
                        else:
                            self.log_result("Bot Token", False, error="Bot API returned not ok")
                    else:
                        self.log_result("Bot Token", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("Bot Token", False, error=str(e))
    
    async def test_bot_commands(self):
        """Test bot commands registration"""
        if not self.bot_token:
            self.log_result("Bot Commands", False, error="TELEGRAM_BOT_TOKEN not found")
            return
        
        expected_commands = [
            "start", "help", "price", "top10", "analysis", 
            "volume", "cvd", "volscan", "balance", "positions", "pnl"
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.bot_token}/getMyCommands"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            commands = [cmd['command'] for cmd in data['result']]
                            missing = set(expected_commands) - set(commands)
                            extra = set(commands) - set(expected_commands)
                            
                            if not missing and not extra:
                                self.log_result("Bot Commands", True, 
                                              f"All {len(commands)} commands registered correctly")
                            else:
                                details = []
                                if missing:
                                    details.append(f"Missing: {', '.join(missing)}")
                                if extra:
                                    details.append(f"Extra: {', '.join(extra)}")
                                self.log_result("Bot Commands", False, 
                                              f"Registered: {len(commands)}/{len(expected_commands)}", 
                                              "; ".join(details))
                        else:
                            self.log_result("Bot Commands", False, error="Bot API returned not ok")
                    else:
                        self.log_result("Bot Commands", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("Bot Commands", False, error=str(e))
    
    async def test_send_message(self):
        """Test sending a message to verify bot can communicate"""
        if not self.bot_token or not self.chat_id:
            self.log_result("Send Test Message", False, 
                          error="TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found")
            return
        
        try:
            test_message = f"🤖 Bot Verification Test - {datetime.now().strftime('%H:%M:%S')}"
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": test_message,
                    "parse_mode": "Markdown"
                }
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            self.log_result("Send Test Message", True, 
                                          f"Message sent successfully (ID: {data['result']['message_id']})")
                        else:
                            self.log_result("Send Test Message", False, 
                                          error=f"Telegram API error: {data.get('description', 'Unknown')}")
                    else:
                        self.log_result("Send Test Message", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_result("Send Test Message", False, error=str(e))
    
    async def run_all_tests(self):
        """Run all verification tests"""
        print("🚀 Starting Telegram Bot Verification")
        print("=" * 50)
        
        # Test market data service
        print("\n📊 Testing Market Data Service:")
        await self.test_market_data_health()
        await self.test_volume_spike_endpoint()
        await self.test_cvd_endpoint()
        await self.test_comprehensive_analysis()
        
        # Test bot configuration
        print("\n🤖 Testing Bot Configuration:")
        await self.test_bot_token()
        await self.test_bot_commands()
        
        # Test bot communication
        print("\n💬 Testing Bot Communication:")
        await self.test_send_message()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        for result in self.results:
            print(f"{result['status']} {result['test']}")
            if result['error']:
                print(f"    🚨 {result['error']}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All systems operational! Bot is ready for use.")
        else:
            print("❌ Some issues detected. Please review failed tests above.")
        
        return passed == total

async def main():
    verifier = BotVerifier()
    success = await verifier.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)