#!/usr/bin/env python3
"""
Bot Tester - Simple validation for Telegram bot functionality
Tests underlying API endpoints that the bot uses
"""

import requests
from api_tester import SimpleAPITester

class BotTester:
    """Test bot functionality via API endpoints"""
    
    def __init__(self):
        self.api_tester = SimpleAPITester()
        self.local_url = "http://localhost:8001"
    
    def test_bot_commands(self):
        """Test the API endpoints that bot commands use"""
        print("🤖 Testing Bot Command APIs")
        
        # Test /price command (uses combined_price endpoint)
        result = self.api_tester.test_endpoint(f"{self.local_url}/combined_price", {"symbol": "BTC-USDT"})
        print(f"  /price command: {self._status_icon(result)}")
        
        # Test /oi command (uses oi_analysis endpoint) 
        result = self.api_tester.test_endpoint(f"{self.local_url}/oi_analysis", {"symbol": "BTC"})
        print(f"  /oi command: {self._status_icon(result)}")
        
        # Test /analysis command (uses comprehensive_analysis endpoint)
        result = self.api_tester.test_endpoint(f"{self.local_url}/comprehensive_analysis", 
                                              {"symbol": "BTC/USDT", "timeframe": "15m"})
        print(f"  /analysis command: {self._status_icon(result)}")
        
        # Test health endpoint
        result = self.api_tester.test_endpoint(f"{self.local_url}/health")
        print(f"  Health check: {self._status_icon(result)}")
        
        return {"status": "API endpoints tested", "note": "Bot commands tested via underlying APIs"}
    
    def _status_icon(self, result):
        """Simple status icon"""
        status = result.get("status", "error")
        return {"ok": "✅", "failed": "❌", "down": "🔌", "slow": "⏰", "error": "🚨"}.get(status, "❓")

def main():
    """Simple CLI"""
    tester = BotTester()
    tester.test_bot_commands()
    print("\n📋 Bot testing complete")
    print("💡 Note: Direct Telegram testing requires bot token access")

if __name__ == "__main__":
    main()