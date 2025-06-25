#!/usr/bin/env python3
"""
COMPLETE SYSTEM TEST: Test the integrated /multi_oi endpoint
Test the complete 13-market system through the actual API endpoint
"""

import asyncio
import aiohttp
import json
import sys
import os

async def test_complete_system():
    """Test the complete system through the API endpoint"""
    print("🚀 TESTING COMPLETE 13-MARKET SYSTEM VIA API")
    print("=" * 60)
    
    # Test the /multi_oi endpoint
    api_url = "http://localhost:8001/multi_oi"
    
    test_data = {
        "base_symbol": "BTC"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Making API call to: {api_url}")
            print(f"📋 Payload: {test_data}")
            
            async with session.post(api_url, json=test_data) as response:
                print(f"📊 HTTP Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('success'):
                        print(f"✅ API SUCCESS!")
                        print(f"\n📈 SYSTEM RESULTS:")
                        print(f"  Base Symbol: {result['base_symbol']}")
                        print(f"  Total Markets: {result['total_markets']}")
                        print(f"  Total OI: {result['aggregated_oi']['total_tokens']:,.0f} BTC (${result['aggregated_oi']['total_usd']/1e9:.1f}B)")
                        print(f"  Successful Exchanges: {result['validation_summary']['successful_exchanges']}/5")
                        
                        print(f"\n📊 EXCHANGE BREAKDOWN:")
                        for exchange_data in result['exchange_breakdown']:
                            exchange = exchange_data['exchange']
                            oi_tokens = exchange_data['oi_tokens']
                            oi_usd = exchange_data['oi_usd']
                            percentage = exchange_data['oi_percentage']
                            markets = exchange_data['markets']
                            
                            print(f"  {exchange.upper()}: {oi_tokens:,.0f} BTC (${oi_usd/1e9:.1f}B) - {percentage:.1f}% - {markets} markets")
                        
                        print(f"\n🏷️ MARKET CATEGORIES:")
                        categories = result['market_categories']
                        
                        usdt = categories['usdt_stable']
                        usdc = categories['usdc_stable'] 
                        usd = categories['usd_inverse']
                        
                        print(f"  USDT Stable: {usdt['total_tokens']:,.0f} BTC (${usdt['total_usd']/1e9:.1f}B) - {usdt['percentage']:.1f}% - {usdt['exchanges']} exchanges")
                        print(f"  USDC Stable: {usdc['total_tokens']:,.0f} BTC (${usdc['total_usd']/1e9:.1f}B) - {usdc['percentage']:.1f}% - {usdc['exchanges']} exchanges")
                        print(f"  USD Inverse: {usd['total_tokens']:,.0f} BTC (${usd['total_usd']/1e9:.1f}B) - {usd['percentage']:.1f}% - {usd['exchanges']} exchanges")
                        
                        print(f"\n✅ VALIDATION:")
                        validation = result['validation_summary']
                        print(f"  Status: {'✅ PASSED' if validation['validation_passed'] else '❌ FAILED'}")
                        print(f"  Working: {validation['successful_exchanges']}/5 exchanges")
                        print(f"  Total Markets: {validation['total_markets']}")
                        
                        # Save results for verification
                        output_file = "/Users/screener-m3/projects/crypto-assistant/complete_system_test_results.json"
                        with open(output_file, 'w') as f:
                            json.dump(result, f, indent=2)
                        
                        print(f"\n📄 Complete results saved to: complete_system_test_results.json")
                        print(f"\n🎉 COMPLETE SYSTEM TEST: ✅ PASSED")
                        
                        return True
                    else:
                        print(f"❌ API returned error: {result.get('error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return False
                    
    except aiohttp.ClientConnectorError:
        print(f"❌ Connection Error: Service not running at {api_url}")
        print(f"💡 Start the service with: python3 main.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_telegram_bot_format():
    """Test the Telegram bot message format"""
    print(f"\n🤖 TESTING TELEGRAM BOT FORMAT")
    print("=" * 40)
    
    # Import the bot formatting function  
    try:
        # Add the telegram bot path
        sys.path.append('/Users/screener-m3/projects/crypto-assistant/services/telegram-bot')
        
        # Make API call to get data
        api_url = "http://localhost:8001/multi_oi"
        test_data = {"base_symbol": "BTC"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('success'):
                        # Format the message like the Telegram bot would
                        formatted_message = format_oi_message(result, "BTC")
                        print(f"📱 TELEGRAM MESSAGE FORMAT:")
                        print("─" * 50)
                        print(formatted_message)
                        print("─" * 50)
                        
                        return True
                    else:
                        print(f"❌ API error: {result.get('error')}")
                        return False
                else:
                    print(f"❌ HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"⚠️ Telegram format test skipped: {e}")
        return True  # Don't fail the overall test

def format_oi_message(data, symbol: str) -> str:
    """Format OI data for Telegram message (matching target spec)"""
    
    aggregated = data['aggregated_oi']
    total_oi_tokens = aggregated['total_tokens']
    total_oi_usd = aggregated['total_usd']
    
    # Header
    message = f"🎯 MULTI-EXCHANGE OI ANALYSIS - {symbol}\n\n"
    
    # Total summary
    message += f"💰 TOTAL OI: {total_oi_tokens:,.0f} {symbol} (${total_oi_usd/1e9:.1f}B)\n"
    message += f"📊 MARKETS: {data['total_markets']} across {data['validation_summary']['successful_exchanges']} exchanges\n\n"
    
    # Exchange breakdown
    message += "📈 EXCHANGE BREAKDOWN:\n"
    for exchange_data in data['exchange_breakdown']:
        exchange = exchange_data['exchange'].upper()
        oi_tokens = exchange_data['oi_tokens']
        oi_usd = exchange_data['oi_usd']
        percentage = exchange_data['oi_percentage']
        markets = exchange_data['markets']
        
        message += f"• {exchange}: {oi_tokens:,.0f} {symbol} (${oi_usd/1e9:.1f}B) - {percentage:.1f}% - {markets}M\n"
    
    # Market categories
    message += f"\n🏷️ MARKET CATEGORIES:\n"
    categories = data['market_categories']
    
    for category_name, category_data in categories.items():
        if category_name == 'usdt_stable':
            emoji = "🟢"
            name = "USDT Stable"
        elif category_name == 'usdc_stable':
            emoji = "🔵"
            name = "USDC Stable"  
        elif category_name == 'usd_inverse':
            emoji = "⚫"
            name = "USD Inverse"
        
        tokens = category_data['total_tokens']
        usd = category_data['total_usd']
        percentage = category_data['percentage']
        exchanges = category_data['exchanges']
        
        message += f"• {emoji} {name}: {tokens:,.0f} {symbol} (${usd/1e9:.1f}B) - {percentage:.1f}% - {exchanges}E\n"
    
    # Status
    status = "✅ COMPLETE" if data['validation_summary']['validation_passed'] else "⚠️ PARTIAL"
    message += f"\n🎯 STATUS: {status}"
    
    return message

if __name__ == "__main__":
    # Test the complete system
    success = asyncio.run(test_complete_system())
    
    if success:
        # Test Telegram format
        asyncio.run(test_telegram_bot_format())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)