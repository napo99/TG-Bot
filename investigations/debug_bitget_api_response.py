#!/usr/bin/env python3
"""
DEBUG BITGET API RESPONSE
Check the actual field names in Bitget V1 API response
"""

import aiohttp
import asyncio
import json

async def debug_bitget_response():
    """Debug the actual Bitget API response structure"""
    print("🔍 DEBUGGING BITGET API RESPONSE STRUCTURE")
    print("=" * 45)
    
    base_url = "https://api.bitget.com"
    
    # Test both symbols with correct parameters
    test_cases = [
        {
            "symbol": "BTCUSDT_UMCBL",
            "productType": "USDT-FUTURES",
            "endpoint": "/api/mix/v1/market/ticker"
        },
        {
            "symbol": "BTCUSD_DMCBL", 
            "productType": "COIN-FUTURES",
            "endpoint": "/api/mix/v1/market/ticker"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"📊 Testing: {test_case['symbol']} ({test_case['productType']})")
            
            try:
                params = {
                    "symbol": test_case['symbol'],
                    "productType": test_case['productType']
                }
                
                url = f"{base_url}{test_case['endpoint']}"
                print(f"  URL: {url}")
                print(f"  Params: {params}")
                
                async with session.get(url, params=params) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"  Response structure:")
                        print(f"    Type: {type(data)}")
                        print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                        if isinstance(data, dict) and 'data' in data:
                            ticker_data = data['data']
                            print(f"    Data type: {type(ticker_data)}")
                            
                            if isinstance(ticker_data, dict):
                                print(f"    Data keys: {list(ticker_data.keys())}")
                                
                                # Look for price fields
                                price_fields = [k for k in ticker_data.keys() if 'pr' in k.lower() or 'price' in k.lower()]
                                print(f"    Price fields: {price_fields}")
                                for field in price_fields:
                                    print(f"      {field}: {ticker_data.get(field)}")
                                
                                # Look for volume fields
                                volume_fields = [k for k in ticker_data.keys() if 'vol' in k.lower() or 'amount' in k.lower()]
                                print(f"    Volume fields: {volume_fields}")
                                for field in volume_fields:
                                    print(f"      {field}: {ticker_data.get(field)}")
                                
                                # Look for OI fields
                                oi_fields = [k for k in ticker_data.keys() if 'open' in k.lower() or 'interest' in k.lower() or 'hold' in k.lower()]
                                print(f"    OI fields: {oi_fields}")
                                for field in oi_fields:
                                    print(f"      {field}: {ticker_data.get(field)}")
                                
                                # Show all fields for reference
                                print(f"    All fields:")
                                for k, v in ticker_data.items():
                                    print(f"      {k}: {v}")
                        else:
                            print(f"    Full response: {json.dumps(data, indent=2)}")
                    else:
                        error_text = await response.text()
                        print(f"  Error: {error_text}")
                        
            except Exception as e:
                print(f"  Exception: {e}")
            
            print("")

if __name__ == "__main__":
    asyncio.run(debug_bitget_response())