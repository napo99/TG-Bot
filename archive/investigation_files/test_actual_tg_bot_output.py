#!/usr/bin/env python3
"""
TEST ACTUAL TG BOT OUTPUT
Tests the exact message the TG bot generates to see ranking order
"""

import asyncio
import aiohttp
import json

async def test_tg_bot_ranking():
    """Test what the TG bot actually shows vs API data"""
    print("🤖 TESTING ACTUAL TG BOT OUTPUT vs API DATA")
    print("="*50)
    
    # Step 1: Check raw market data API
    print("📊 RAW MARKET DATA API:")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8001/multi_oi", 
                                  json={"base_symbol": "BTC"}) as response:
                api_data = await response.json()
        
        # Sort by OI tokens descending  
        exchanges = sorted(api_data['exchange_breakdown'], 
                          key=lambda x: x['oi_tokens'], reverse=True)
        
        for i, exchange in enumerate(exchanges, 1):
            print(f"  {i}. {exchange['exchange'].title()}: {exchange['oi_tokens']:,.0f} BTC (${exchange['oi_usd']/1e9:.1f}B)")
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False
    
    print("\n" + "="*50)
    
    # Step 2: Test TG bot comprehensive analysis endpoint
    print("🤖 TG BOT COMPREHENSIVE ANALYSIS:")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8001/comprehensive_analysis", 
                                  json={"symbol": "BTC/USDT", "timeframe": "15m"}) as response:
                if response.status == 200:
                    tg_data = await response.json()
                    
                    # Check if there's OI analysis
                    if 'oi_analysis' in tg_data:
                        oi_data = tg_data['oi_analysis']
                        
                        # Look for exchange breakdown
                        if 'exchange_breakdown' in oi_data:
                            exchanges = sorted(oi_data['exchange_breakdown'], 
                                             key=lambda x: x['oi_tokens'], reverse=True)
                            
                            print("  TG Bot Exchange Ranking:")
                            for i, exchange in enumerate(exchanges, 1):
                                print(f"    {i}. {exchange['exchange'].title()}: {exchange['oi_tokens']:,.0f} BTC")
                        else:
                            print("  ⚠️ No exchange_breakdown in TG bot response")
                    else:
                        print("  ⚠️ No oi_analysis in TG bot response")
                        
                    # Check if TG bot is calling multi_oi internally
                    if 'raw_data_source' in tg_data:
                        print(f"  📡 TG Bot Data Source: {tg_data['raw_data_source']}")
                        
                else:
                    print(f"  ❌ TG Bot API Status: {response.status}")
                    response_text = await response.text()
                    print(f"  Error: {response_text[:200]}")
                    
    except Exception as e:
        print(f"❌ TG Bot Test Error: {e}")
    
    print("\n" + "="*50)
    
    # Step 3: Check if TG bot is using a different endpoint
    print("🔍 TESTING ALL POSSIBLE TG BOT ENDPOINTS:")
    
    endpoints_to_test = [
        ("/multi_oi", {"base_symbol": "BTC"}),
        ("/oi_analysis", {"symbol": "BTC"}),
        ("/market_analysis", {"symbol": "BTC/USDT"}),
        ("/comprehensive_analysis", {"symbol": "BTC/USDT", "timeframe": "15m"})
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, payload in endpoints_to_test:
            try:
                async with session.post(f"http://localhost:8001{endpoint}", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ {endpoint}: Available")
                        
                        # Look for exchange data in any format
                        if 'exchange_breakdown' in data:
                            exchanges = data['exchange_breakdown']
                            bybit_oi = next((e['oi_tokens'] for e in exchanges if e['exchange'] == 'bybit'), 0)
                            gateio_oi = next((e['oi_tokens'] for e in exchanges if e['exchange'] == 'gateio'), 0)
                            print(f"    Bybit: {bybit_oi:,.0f}, Gate.io: {gateio_oi:,.0f}")
                            if gateio_oi > bybit_oi:
                                print(f"    🚨 RANKING BUG: Gate.io ({gateio_oi:,.0f}) > Bybit ({bybit_oi:,.0f})")
                    else:
                        print(f"  ❌ {endpoint}: Status {response.status}")
                        
            except Exception as e:
                print(f"  ❌ {endpoint}: Error {e}")

async def main():
    await test_tg_bot_ranking()
    
    print("\n🎯 SUMMARY:")
    print("This test shows exactly what data the TG bot is working with")
    print("and identifies any discrepancies between API and TG bot rankings.")

if __name__ == "__main__":
    asyncio.run(main())