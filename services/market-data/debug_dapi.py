#!/usr/bin/env python3
"""Debug DAPI API calls to find exact issue"""

import asyncio
import aiohttp
import json

async def debug_dapi_apis():
    """Debug each DAPI API call individually"""
    symbol = "BTCUSD_PERP"
    
    dapi_base = "https://dapi.binance.com"
    endpoints = {
        'oi': f"{dapi_base}/dapi/v1/openInterest?symbol={symbol}",
        'ticker': f"{dapi_base}/dapi/v1/ticker/24hr?symbol={symbol}",
        'funding': f"{dapi_base}/dapi/v1/premiumIndex?symbol={symbol}"
    }
    
    async with aiohttp.ClientSession() as session:
        for name, url in endpoints.items():
            try:
                print(f"\n🔍 Testing {name.upper()} API:")
                print(f"URL: {url}")
                
                async with session.get(url) as response:
                    data = await response.json()
                    print(f"Status: {response.status}")
                    print(f"Type: {type(data)}")
                    print(f"Data: {json.dumps(data, indent=2)}")
                    
                    # Test data extraction
                    if name == 'oi':
                        print(f"OI extraction: {data['openInterest']}")
                    elif name == 'ticker':
                        if isinstance(data, list):
                            data = data[0]
                        print(f"Price: {data['lastPrice']}")
                        print(f"Volume: {data['volume']}")
                    elif name == 'funding':
                        if isinstance(data, list):
                            data = data[0]
                        print(f"Funding: {data['lastFundingRate']}")
                    
                    print("✅ Extraction successful")
                    
            except Exception as e:
                print(f"❌ Error with {name}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_dapi_apis())