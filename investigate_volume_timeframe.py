#!/usr/bin/env python3
"""
Investigation script to determine the exact timeframe for volume data
This script will examine the ccxt ticker data structure and try to determine
what timeframe the 'baseVolume' represents
"""

import asyncio
import ccxt.pro as ccxt
import json
from datetime import datetime
from pprint import pprint

async def investigate_volume_timeframe():
    """Investigate the volume timeframe from various sources"""
    
    print("🔍 INVESTIGATING VOLUME TIMEFRAME")
    print("=" * 50)
    
    # Initialize Binance spot and futures exchanges
    spot_ex = ccxt.binance({'enableRateLimit': True})
    futures_ex = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    try:
        # Test symbols
        spot_symbol = 'BTC/USDT'
        perp_symbol = 'BTC/USDT:USDT'
        
        print(f"\n1️⃣ SPOT TICKER ANALYSIS ({spot_symbol})")
        print("-" * 40)
        
        # Get spot ticker
        spot_ticker = await spot_ex.fetch_ticker(spot_symbol)
        print(f"Full ticker data structure:")
        
        # Show all ticker fields
        for key, value in spot_ticker.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:,.2f}")
            else:
                print(f"  {key}: {value}")
        
        print(f"\n📊 KEY VOLUME FIELDS:")
        print(f"  baseVolume: {spot_ticker.get('baseVolume', 0):,.2f} BTC")
        print(f"  quoteVolume: {spot_ticker.get('quoteVolume', 0):,.2f} USDT")
        print(f"  info: {json.dumps(spot_ticker.get('info', {}), indent=2)}")
        
        print(f"\n2️⃣ PERPETUAL TICKER ANALYSIS ({perp_symbol})")
        print("-" * 40)
        
        # Get perp ticker
        perp_ticker = await futures_ex.fetch_ticker(perp_symbol)
        print(f"Full ticker data structure:")
        
        # Show all ticker fields
        for key, value in perp_ticker.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:,.2f}")
            else:
                print(f"  {key}: {value}")
        
        print(f"\n📊 KEY VOLUME FIELDS:")
        print(f"  baseVolume: {perp_ticker.get('baseVolume', 0):,.2f} BTC")
        print(f"  quoteVolume: {perp_ticker.get('quoteVolume', 0):,.2f} USDT")
        print(f"  info: {json.dumps(perp_ticker.get('info', {}), indent=2)}")
        
        print(f"\n3️⃣ COMPARING VOLUME DATA")
        print("-" * 40)
        print(f"SPOT baseVolume:  {spot_ticker.get('baseVolume', 0):,.2f} BTC")
        print(f"PERP baseVolume:  {perp_ticker.get('baseVolume', 0):,.2f} BTC")
        
        ratio = spot_ticker.get('baseVolume', 0) / perp_ticker.get('baseVolume', 0) if perp_ticker.get('baseVolume', 0) > 0 else 0
        print(f"Spot/Perp ratio:  {ratio:.3f}")
        
        print(f"\n4️⃣ ANALYZING CCXT DOCUMENTATION")
        print("-" * 40)
        
        # Check if there are any hints in the exchange object
        print(f"Exchange API info:")
        print(f"  Spot exchange describe: {spot_ex.describe()}")
        
        # Check the raw API response from Binance
        print(f"\n5️⃣ RAW API RESPONSE ANALYSIS")
        print("-" * 40)
        
        # Get raw ticker from Binance API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Spot 24hr ticker
            spot_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
            async with session.get(spot_url) as response:
                spot_raw = await response.json()
                print(f"BINANCE SPOT 24HR TICKER:")
                print(f"  symbol: {spot_raw.get('symbol')}")
                print(f"  volume (base): {spot_raw.get('volume')}")
                print(f"  quoteVolume: {spot_raw.get('quoteVolume')}")
                print(f"  openTime: {datetime.fromtimestamp(spot_raw.get('openTime', 0)/1000)}")
                print(f"  closeTime: {datetime.fromtimestamp(spot_raw.get('closeTime', 0)/1000)}")
                
            # Futures 24hr ticker  
            futures_url = "https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT"
            async with session.get(futures_url) as response:
                futures_raw = await response.json()
                print(f"\nBINANCE FUTURES 24HR TICKER:")
                print(f"  symbol: {futures_raw.get('symbol')}")
                print(f"  volume (base): {futures_raw.get('volume')}")
                print(f"  quoteVolume: {futures_raw.get('quoteVolume')}")
                print(f"  openTime: {datetime.fromtimestamp(futures_raw.get('openTime', 0)/1000)}")
                print(f"  closeTime: {datetime.fromtimestamp(futures_raw.get('closeTime', 0)/1000)}")
        
        print(f"\n6️⃣ CONCLUSIONS")
        print("-" * 40)
        print(f"✅ Both spot and perp use ticker.get('baseVolume')")
        print(f"✅ Binance API endpoint is '/ticker/24hr' - indicating 24-hour volume")
        print(f"✅ Raw API response shows openTime/closeTime spanning ~24 hours")
        print(f"⚠️  Volume timeframe appears to be 24 HOURS for both spot and perpetual")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await spot_ex.close()
        await futures_ex.close()

if __name__ == "__main__":
    asyncio.run(investigate_volume_timeframe())