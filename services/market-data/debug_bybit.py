#!/usr/bin/env python3
"""Debug Bybit API calls to understand data format"""

import asyncio
import aiohttp
import json

async def debug_bybit_apis():
    """Debug each Bybit API call individually"""
    base_url = "https://api.bybit.com"
    
    test_cases = [
        {
            "name": "Linear USDT OI",
            "url": f"{base_url}/v5/market/open-interest",
            "params": {"category": "linear", "symbol": "BTCUSDT"}
        },
        {
            "name": "Linear USDT Ticker", 
            "url": f"{base_url}/v5/market/tickers",
            "params": {"category": "linear", "symbol": "BTCUSDT"}
        },
        {
            "name": "Inverse USD OI",
            "url": f"{base_url}/v5/market/open-interest", 
            "params": {"category": "inverse", "symbol": "BTCUSD"}
        },
        {
            "name": "Inverse USD Ticker",
            "url": f"{base_url}/v5/market/tickers",
            "params": {"category": "inverse", "symbol": "BTCUSD"}
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test in test_cases:
            try:
                print(f"\n🔍 Testing {test['name']}:")
                print(f"URL: {test['url']}")
                print(f"Params: {test['params']}")
                
                async with session.get(test['url'], params=test['params']) as response:
                    data = await response.json()
                    print(f"Status: {response.status}")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    # Check for data
                    if data.get('retCode') == 0:
                        result_list = data.get('result', {}).get('list', [])
                        if result_list:
                            print(f"✅ Data found: {len(result_list)} items")
                            if 'openInterest' in result_list[0]:
                                print(f"OI: {result_list[0]['openInterest']}")
                            if 'lastPrice' in result_list[0]:
                                print(f"Price: {result_list[0]['lastPrice']}")
                        else:
                            print("❌ No data in result.list")
                    else:
                        print(f"❌ API Error: {data.get('retMsg', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error with {test['name']}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_bybit_apis())