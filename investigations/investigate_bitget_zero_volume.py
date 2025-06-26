#!/usr/bin/env python3
"""
BITGET ZERO VOLUME INVESTIGATION AGENT
Investigates why both Bitget BTC markets show 0 volume despite significant OI
"""

import aiohttp
import asyncio
import json

class BitgetVolumeInvestigator:
    def __init__(self):
        self.bitget_base = "https://api.bitget.com"
        
    async def fetch_bitget_market_data(self):
        """Fetch Bitget market data directly from their API"""
        print("🔍 BITGET VOLUME INVESTIGATION")
        print("=" * 35)
        print("🎯 Issue: Both BTC markets show 0 volume despite $6.67B OI")
        print("📊 Expected: Should have significant volume with that OI")
        print("")
        
        # Bitget API endpoints to test
        endpoints_to_test = [
            ("/api/mix/v1/market/tickers", "Mix V1 Tickers"),
            ("/api/v2/mix/market/tickers", "Mix V2 Tickers"),
            ("/api/spot/v1/market/tickers", "Spot Tickers"),
            ("/api/mix/v1/market/ticker?symbol=BTCUSDT", "BTC USDT Specific"),
            ("/api/mix/v1/market/ticker?symbol=BTCUSD", "BTC USD Specific"),
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints_to_test:
                try:
                    print(f"📊 Testing: {description}")
                    print(f"   Endpoint: {endpoint}")
                    
                    async with session.get(f"{self.bitget_base}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if isinstance(data, dict) and 'data' in data:
                                data = data['data']
                            
                            # Look for BTC contracts
                            btc_items = []
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        symbol = item.get('symbol', '')
                                        if 'BTC' in symbol:
                                            btc_items.append(item)
                            elif isinstance(data, dict):
                                symbol = data.get('symbol', '')
                                if 'BTC' in symbol:
                                    btc_items = [data]
                            
                            print(f"   ✅ Status 200 - Found {len(btc_items)} BTC-related items")
                            
                            for item in btc_items:
                                symbol = item.get('symbol', 'Unknown')
                                
                                # Extract volume fields
                                volume_fields = []
                                for key, value in item.items():
                                    if any(term in key.lower() for term in ['volume', 'vol', 'amount', 'turnover']):
                                        volume_fields.append((key, value))
                                
                                print(f"     📋 {symbol}:")
                                print(f"       Volume fields: {[f[0] for f in volume_fields]}")
                                
                                # Show key volume metrics
                                for field_name, field_value in volume_fields[:5]:  # Top 5 volume fields
                                    try:
                                        if isinstance(field_value, str):
                                            val = float(field_value)
                                        else:
                                            val = field_value
                                        print(f"         {field_name}: {val:,.2f}")
                                    except (ValueError, TypeError):
                                        print(f"         {field_name}: {field_value} (non-numeric)")
                                
                                # Check for specific volume fields
                                vol_24h = item.get('vol24h', item.get('volume24h', item.get('baseVol', 0)))
                                quote_vol = item.get('quoteVol', item.get('quoteVolume', 0))
                                usd_vol = item.get('usdtVol', item.get('usdVolume', 0))
                                
                                print(f"       Key volumes:")
                                print(f"         24h Volume: {vol_24h}")
                                print(f"         Quote Volume: {quote_vol}")
                                print(f"         USD Volume: {usd_vol}")
                                
                                results[symbol] = {
                                    'endpoint': endpoint,
                                    'vol_24h': vol_24h,
                                    'quote_vol': quote_vol,
                                    'usd_vol': usd_vol,
                                    'all_fields': volume_fields
                                }
                        else:
                            print(f"   ❌ Status {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                
                print("")
        
        return results
    
    async def check_our_bitget_implementation(self):
        """Check our current Bitget implementation"""
        print("🔍 CHECKING OUR BITGET IMPLEMENTATION")
        print("=" * 40)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
                    data = await response.json()
            
            # Find Bitget data
            bitget_data = None
            for exchange in data.get('exchange_breakdown', []):
                if exchange['exchange'].lower() == 'bitget':
                    bitget_data = exchange
                    break
            
            if bitget_data:
                print("📊 OUR BITGET DATA:")
                print(f"  Total OI: {bitget_data['oi_tokens']:,.0f} BTC")
                print(f"  Total USD: ${bitget_data['oi_usd']/1e9:.2f}B")
                print(f"  Markets: {bitget_data['markets']}")
                print("")
                
                print("📋 INDIVIDUAL MARKETS:")
                zero_volume_markets = []
                for market in bitget_data.get('market_breakdown', []):
                    symbol = market['symbol']
                    oi_tokens = market['oi_tokens']
                    oi_usd = market['oi_usd']
                    volume_24h = market['volume_24h']
                    volume_24h_usd = market['volume_24h_usd']
                    price = market['price']
                    funding_rate = market['funding_rate']
                    
                    print(f"  {symbol}:")
                    print(f"    OI: {oi_tokens:,.0f} BTC (${oi_usd/1e6:.1f}M)")
                    print(f"    Volume 24h: {volume_24h:,.0f} BTC (${volume_24h_usd/1e6:.1f}M)")
                    print(f"    Price: ${price:,.2f}")
                    print(f"    Funding: {funding_rate*100:+.4f}%")
                    
                    if volume_24h == 0:
                        zero_volume_markets.append(market)
                        print(f"    🚨 ZERO VOLUME DETECTED")
                    
                    print("")
                
                if zero_volume_markets:
                    print(f"🚨 FOUND {len(zero_volume_markets)} MARKETS WITH ZERO VOLUME:")
                    for market in zero_volume_markets:
                        ratio = market['oi_usd'] / 1e9
                        print(f"  ❌ {market['symbol']}: ${ratio:.1f}B OI but 0 volume")
                        print(f"     This is suspicious - markets with OI should have volume")
                    
                    print("")
                    print("🔍 POSSIBLE CAUSES:")
                    print("  1. Wrong volume field in API response")
                    print("  2. Volume reported in different units")
                    print("  3. API endpoint doesn't include volume data")
                    print("  4. Volume calculation error in our code")
                    print("  5. Market is actually illiquid despite OI")
                else:
                    print("✅ All markets show volume data")
                
            else:
                print("❌ No Bitget data found in our system")
                
        except Exception as e:
            print(f"❌ Error checking our implementation: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_specific_bitget_volume_endpoints(self):
        """Test specific Bitget endpoints that should have volume data"""
        print("🔍 TESTING SPECIFIC BITGET VOLUME ENDPOINTS")
        print("=" * 45)
        
        # Test both symbols that show zero volume
        symbols_to_test = [
            "BTCUSDT_UMCBL",  # Our system's symbol format
            "BTCUSD_DMCBL",   # Our system's symbol format
            "BTCUSDT",        # Standard format
            "BTCUSD",         # Standard format
            "BTC-USDT",       # Alternative format
            "BTC-USD"         # Alternative format
        ]
        
        volume_endpoints = [
            "/api/mix/v1/market/ticker",
            "/api/v2/mix/market/ticker",
            "/api/mix/v1/market/candles",
        ]
        
        async with aiohttp.ClientSession() as session:
            for symbol in symbols_to_test:
                print(f"📊 Testing symbol: {symbol}")
                
                for endpoint in volume_endpoints:
                    try:
                        url = f"{self.bitget_base}{endpoint}?symbol={symbol}"
                        print(f"  📋 {endpoint}")
                        
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if isinstance(data, dict) and 'data' in data:
                                    ticker_data = data['data']
                                    
                                    # Extract all volume-related fields
                                    volume_info = {}
                                    for key, value in ticker_data.items():
                                        if any(term in key.lower() for term in ['vol', 'volume', 'amount', 'turnover']):
                                            volume_info[key] = value
                                    
                                    if volume_info:
                                        print(f"    ✅ Found volume data:")
                                        for field, value in volume_info.items():
                                            try:
                                                val = float(value) if isinstance(value, str) else value
                                                print(f"      {field}: {val:,.2f}")
                                            except (ValueError, TypeError):
                                                print(f"      {field}: {value}")
                                    else:
                                        print(f"    ⚠️ No volume fields found")
                                else:
                                    print(f"    ✅ Status 200 but unexpected data format")
                            else:
                                print(f"    ❌ Status {response.status}")
                                
                    except Exception as e:
                        print(f"    ❌ Exception: {e}")
                
                print("")

async def main():
    investigator = BitgetVolumeInvestigator()
    
    print("🚨 BITGET ZERO VOLUME INVESTIGATION")
    print("=" * 40)
    print("📋 Issue: Both Bitget BTC markets show 0 volume")
    print("📋 Context: $6.67B OI but 0 trading volume")
    print("📋 Expected: Markets with OI should have volume")
    print("")
    
    # Step 1: Check our current implementation
    await investigator.check_our_bitget_implementation()
    
    # Step 2: Fetch Bitget market data directly
    await investigator.fetch_bitget_market_data()
    
    # Step 3: Test specific volume endpoints
    await investigator.test_specific_bitget_volume_endpoints()
    
    print("\n🎯 INVESTIGATION COMPLETE")
    print("Use findings above to fix Bitget volume data extraction")

if __name__ == "__main__":
    asyncio.run(main())