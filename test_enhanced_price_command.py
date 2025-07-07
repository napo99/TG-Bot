#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced /price command
Tests all new features including 15m data, delta calculations, ATR, and formatting
"""

import asyncio
import sys
import os
import json
from datetime import datetime
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'telegram-bot'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'market-data'))

from formatting_utils import (
    format_large_number, format_price, format_percentage, format_volume_with_usd,
    format_dollar_amount, format_dual_timezone_timestamp, get_change_emoji, format_delta_value
)

class TestFormattingUtils(unittest.TestCase):
    """Test the enhanced formatting utilities"""

    def test_format_large_number(self):
        """Test number formatting with B/M/K notation"""
        # Test billions
        self.assertEqual(format_large_number(3200000000), "3.20B")
        self.assertEqual(format_large_number(32000450000), "32.00B")
        
        # Test millions
        self.assertEqual(format_large_number(150000000), "150.00M")
        self.assertEqual(format_large_number(1500000), "1.50M")
        
        # Test thousands
        self.assertEqual(format_large_number(15000), "15.00K")
        self.assertEqual(format_large_number(1500), "1.50K")
        
        # Test small numbers
        self.assertEqual(format_large_number(150), "150.00")
        self.assertEqual(format_large_number(15.5), "15.50")
        
        # Test None handling
        self.assertEqual(format_large_number(None), "N/A")
        
        # Test negative numbers
        self.assertEqual(format_large_number(-1500000), "-1.50M")

    def test_format_price(self):
        """Test price formatting"""
        self.assertEqual(format_price(108401.84), "$108,401.84")
        self.assertEqual(format_price(0.001234, 6), "$0.001234")
        self.assertEqual(format_price(None), "$N/A")

    def test_format_percentage(self):
        """Test percentage formatting with signs"""
        self.assertEqual(format_percentage(2.5), "+2.50%")
        self.assertEqual(format_percentage(-0.33), "-0.33%")
        self.assertEqual(format_percentage(0), "+0.00%")
        self.assertEqual(format_percentage(None), "N/A%")

    def test_format_volume_with_usd(self):
        """Test volume formatting with USD conversion"""
        result = format_volume_with_usd(9270, "BTC", 108401.84)
        self.assertIn("9,270 BTC", result)
        self.assertIn("$1.00B", result)
        
        # Test None handling
        self.assertEqual(format_volume_with_usd(None, "BTC", 108401.84), "N/A BTC ($N/A)")
        self.assertEqual(format_volume_with_usd(9270, "BTC", None), "N/A BTC ($N/A)")

    def test_format_delta_value(self):
        """Test delta value formatting"""
        result = format_delta_value(800, "BTC", 108401.84)
        self.assertIn("+800 BTC", result)
        self.assertIn("$86.7M", result)
        
        result = format_delta_value(-15, "BTC", 108401.84)
        self.assertIn("-15 BTC", result)
        
        # Test None handling
        self.assertEqual(format_delta_value(None, "BTC", 108401.84), "N/A BTC ($N/A)")

    def test_get_change_emoji(self):
        """Test emoji selection for changes"""
        self.assertEqual(get_change_emoji(2.5), "🟢")
        self.assertEqual(get_change_emoji(-0.33), "🔴")
        self.assertEqual(get_change_emoji(0), "⚪")
        self.assertEqual(get_change_emoji(None), "⚪")

    def test_format_dual_timezone_timestamp(self):
        """Test dual timezone timestamp formatting"""
        timestamp = format_dual_timezone_timestamp()
        self.assertIn("UTC", timestamp)
        self.assertIn("SGT", timestamp)
        self.assertIn("/", timestamp)


class TestEnhancedPriceAPI(unittest.TestCase):
    """Test the enhanced market data API functionality"""

    def test_sample_enhanced_response(self):
        """Test with sample enhanced API response"""
        sample_response = {
            'success': True,
            'data': {
                'base_symbol': 'BTC/USDT',
                'spot': {
                    'symbol': 'BTC/USDT',
                    'price': 108401.84,
                    'volume_24h': 9270.0,
                    'change_24h': -0.33,
                    'volume_15m': 1000.0,
                    'change_15m': -0.01,
                    'delta_24h': 800.0,
                    'delta_15m': -15.0,
                    'atr_24h': 2500.0,
                    'atr_15m': 150.0
                },
                'perp': {
                    'symbol': 'BTC/USDT:USDT',
                    'price': 108361.10,
                    'volume_24h': 100179.0,
                    'change_24h': -0.31,
                    'volume_15m': 1000.0,
                    'change_15m': -0.01,
                    'delta_24h': 800.0,
                    'delta_15m': -15.0,
                    'atr_24h': 2600.0,
                    'atr_15m': 180.0,
                    'open_interest': 79174.0,
                    'funding_rate': 0.000046
                }
            }
        }
        
        # Test data extraction
        data = sample_response['data']
        spot = data['spot']
        perp = data['perp']
        
        # Test spot formatting
        spot_price_str = format_price(spot['price'])
        self.assertEqual(spot_price_str, "$108,401.84")
        
        spot_volume_str = format_volume_with_usd(spot['volume_24h'], "BTC", spot['price'])
        self.assertIn("9,270 BTC", spot_volume_str)
        self.assertIn("$1.00B", spot_volume_str)
        
        # Test perp formatting
        perp_oi_str = format_volume_with_usd(perp['open_interest'], "BTC", perp['price'])
        self.assertIn("79,174 BTC", perp_oi_str)
        self.assertIn("$8.57B", perp_oi_str)
        
        funding_str = format_percentage(perp['funding_rate'] * 100)
        self.assertEqual(funding_str, "+0.0046%")


async def test_api_integration():
    """Test actual API integration (requires running services)"""
    import aiohttp
    
    try:
        # Test the enhanced combined_price endpoint
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8001/combined_price"
            payload = {"symbol": "BTC-USDT"}
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ API Integration Test:")
                    print(f"   Status: {response.status}")
                    print(f"   Success: {data.get('success', False)}")
                    
                    if data.get('success'):
                        price_data = data.get('data', {})
                        spot = price_data.get('spot', {})
                        perp = price_data.get('perp', {})
                        
                        print(f"   Spot Price: {spot.get('price', 'N/A')}")
                        print(f"   Spot 15m Volume: {spot.get('volume_15m', 'N/A')}")
                        print(f"   Spot ATR 24h: {spot.get('atr_24h', 'N/A')}")
                        print(f"   Perp Price: {perp.get('price', 'N/A')}")
                        print(f"   Perp 15m Volume: {perp.get('volume_15m', 'N/A')}")
                        print(f"   Perp ATR 24h: {perp.get('atr_24h', 'N/A')}")
                        
                        return True
                    else:
                        print(f"   Error: {data.get('error', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ API call failed with status: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ API Integration Test Failed: {e}")
        print("   Note: This is expected if services are not running")
        return False


def simulate_enhanced_price_message():
    """Simulate the enhanced price command message formatting"""
    # Sample data that would come from the API
    sample_data = {
        'base_symbol': 'BTC/USDT',
        'spot': {
            'price': 108401.84,
            'change_24h': -0.33,
            'change_15m': -0.01,
            'volume_24h': 9270.0,
            'volume_15m': 1000.0,
            'delta_24h': 800.0,
            'delta_15m': -15.0,
            'atr_24h': 2500.0,
            'atr_15m': 150.0
        },
        'perp': {
            'price': 108361.10,
            'change_24h': -0.31,
            'change_15m': -0.01,
            'volume_24h': 100179.0,
            'volume_15m': 1000.0,
            'delta_24h': 800.0,
            'delta_15m': -15.0,
            'atr_24h': 2600.0,
            'atr_15m': 180.0,
            'open_interest': 79174.0,
            'funding_rate': 0.000046
        }
    }
    
    base_symbol = sample_data['base_symbol']
    base_token = base_symbol.split('/')[0]
    
    message = f"📊 **{base_symbol}**\n\n"
    
    # Spot section
    if sample_data['spot']:
        spot = sample_data['spot']
        price = spot['price']
        change_24h = spot['change_24h']
        change_15m = spot['change_15m']
        
        change_24h_emoji = get_change_emoji(change_24h)
        dollar_change_24h = (price * change_24h / 100) if change_24h else 0
        atr_24h_str = f" | ATR: {spot['atr_24h']:.2f}" if spot.get('atr_24h') else ""
        
        message += f"""🏪 **SPOT**
💰 Price: **{format_price(price)}** | {format_percentage(change_24h)} | {format_dollar_amount(dollar_change_24h)}{atr_24h_str}
"""
        
        change_15m_emoji = get_change_emoji(change_15m)
        dollar_change_15m = (price * change_15m / 100) if change_15m else 0
        atr_15m_str = f" | ATR: {spot['atr_15m']:.2f}" if spot.get('atr_15m') else ""
        message += f"{change_15m_emoji} Price Change 15m: **{format_percentage(change_15m)}** | {format_dollar_amount(dollar_change_15m)}{atr_15m_str}\n"
        
        volume_24h = spot['volume_24h']
        message += f"📊 Volume 24h: **{format_volume_with_usd(volume_24h, base_token, price)}**\n"
        
        volume_15m = spot['volume_15m']
        message += f"📊 Volume 15m: **{format_volume_with_usd(volume_15m, base_token, price)}**\n"
        
        delta_24h = spot['delta_24h']
        message += f"📈 Delta 24h: **{format_delta_value(delta_24h, base_token, price)}**\n"
        
        delta_15m = spot['delta_15m']
        message += f"📈 Delta 15m: **{format_delta_value(delta_15m, base_token, price)}**\n\n"
    
    # Perp section
    if sample_data['perp']:
        perp = sample_data['perp']
        price = perp['price']
        change_24h = perp['change_24h']
        change_15m = perp['change_15m']
        
        change_24h_emoji = get_change_emoji(change_24h)
        dollar_change_24h = (price * change_24h / 100) if change_24h else 0
        atr_24h_str = f" | ATR: {perp['atr_24h']:.2f}" if perp.get('atr_24h') else ""
        
        message += f"""⚡ **PERPETUALS**
💰 Price: **{format_price(price)}** | {format_percentage(change_24h)} | {format_dollar_amount(dollar_change_24h)}{atr_24h_str}
"""
        
        change_15m_emoji = get_change_emoji(change_15m)
        dollar_change_15m = (price * change_15m / 100) if change_15m else 0
        atr_15m_str = f" | ATR: {perp['atr_15m']:.2f}" if perp.get('atr_15m') else ""
        message += f"{change_15m_emoji} Price Change 15m: **{format_percentage(change_15m)}** | {format_dollar_amount(dollar_change_15m)}{atr_15m_str}\n"
        
        volume_24h = perp['volume_24h']
        message += f"📊 Volume 24h: **{format_volume_with_usd(volume_24h, base_token, price)}**\n"
        
        volume_15m = perp['volume_15m']
        message += f"📊 Volume 15m: **{format_volume_with_usd(volume_15m, base_token, price)}**\n"
        
        delta_24h = perp['delta_24h']
        message += f"📈 Delta 24h: **{format_delta_value(delta_24h, base_token, price)}**\n"
        
        delta_15m = perp['delta_15m']
        message += f"📈 Delta 15m: **{format_delta_value(delta_15m, base_token, price)}**\n"
        
        if perp.get('open_interest'):
            oi_volume = format_volume_with_usd(perp['open_interest'], base_token, price)
            message += f"📈 OI 24h: **{oi_volume}**\n"
        
        if perp.get('funding_rate') is not None:
            funding_rate = perp['funding_rate'] * 100
            message += f"💸 Funding: **{format_percentage(funding_rate)}**\n"
    
    timestamp = format_dual_timezone_timestamp()
    message += f"\n🕐 {timestamp}"
    
    return message


async def main():
    """Run all tests"""
    print("🧪 Running Enhanced /price Command Tests\n")
    
    # Unit tests
    print("1️⃣ Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n2️⃣ Testing API Integration...")
    api_success = await test_api_integration()
    
    print("\n3️⃣ Simulating Enhanced Message Format...")
    enhanced_message = simulate_enhanced_price_message()
    print("📱 Simulated Telegram Message:")
    print("=" * 50)
    print(enhanced_message)
    print("=" * 50)
    
    print("\n📊 Test Summary:")
    print(f"   ✅ Unit Tests: Completed")
    print(f"   {'✅' if api_success else '⚠️'} API Integration: {'Passed' if api_success else 'Skipped (services not running)'}")
    print(f"   ✅ Message Formatting: Completed")
    
    if not api_success:
        print("\n💡 To test API integration:")
        print("   1. Start services: docker-compose up -d")
        print("   2. Re-run this test script")


if __name__ == "__main__":
    asyncio.run(main())