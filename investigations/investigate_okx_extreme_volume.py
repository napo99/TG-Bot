#!/usr/bin/env python3
"""
OKX EXTREME VOLUME INVESTIGATION AGENT
Investigates why OKX shows extremely high volume numbers (8M BTC/day)
"""

import aiohttp
import asyncio
import json

class OKXVolumeInvestigator:
    def __init__(self):
        self.okx_base = "https://www.okx.com"
        
    async def check_our_okx_implementation(self):
        """Check our current OKX implementation volume data"""
        print("🔍 CHECKING OUR OKX IMPLEMENTATION")
        print("=" * 40)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
                    data = await response.json()
            
            # Find OKX data
            okx_data = None
            for exchange in data.get('exchange_breakdown', []):
                if exchange['exchange'].lower() == 'okx':
                    okx_data = exchange
                    break
            
            if okx_data:
                print("📊 OUR OKX DATA:")
                print(f"  Total OI: {okx_data['oi_tokens']:,.0f} BTC")
                print(f"  Total USD: ${okx_data['oi_usd']/1e9:.2f}B")
                print(f"  Markets: {okx_data['markets']}")
                print("")
                
                print("📋 INDIVIDUAL MARKETS:")
                total_volume_btc = 0
                total_volume_usd = 0
                extreme_volume_markets = []
                
                for market in okx_data.get('market_breakdown', []):
                    symbol = market['symbol']
                    oi_tokens = market['oi_tokens']
                    oi_usd = market['oi_usd']
                    volume_24h = market['volume_24h']
                    volume_24h_usd = market['volume_24h_usd']
                    price = market['price']
                    funding_rate = market['funding_rate']
                    
                    total_volume_btc += volume_24h
                    total_volume_usd += volume_24h_usd
                    
                    # Calculate volume to OI ratio (suspicious if >20x)
                    vol_oi_ratio = volume_24h / oi_tokens if oi_tokens > 0 else 0
                    
                    print(f"  {symbol}:")
                    print(f"    OI: {oi_tokens:,.0f} BTC (${oi_usd/1e6:.1f}M)")
                    print(f"    Volume 24h: {volume_24h:,.0f} BTC (${volume_24h_usd/1e6:.1f}M)")
                    print(f"    Vol/OI Ratio: {vol_oi_ratio:.1f}x")
                    print(f"    Price: ${price:,.2f}")
                    print(f"    Funding: {funding_rate*100:+.4f}%")
                    
                    if vol_oi_ratio > 20:
                        extreme_volume_markets.append({
                            'symbol': symbol,
                            'volume_24h': volume_24h,
                            'oi_tokens': oi_tokens,
                            'ratio': vol_oi_ratio
                        })
                        print(f"    🚨 EXTREME VOLUME RATIO (>{vol_oi_ratio:.1f}x)")
                    
                    print("")
                
                print(f"📊 TOTAL OKX VOLUME: {total_volume_btc:,.0f} BTC (${total_volume_usd/1e6:.0f}M)")
                
                # Compare with typical market ratios
                print("\n🔍 VOLUME ANALYSIS:")
                if total_volume_btc > 5_000_000:  # >5M BTC/day
                    print(f"🚨 EXTREMELY HIGH VOLUME: {total_volume_btc/1e6:.1f}M BTC/day")
                    print(f"   This exceeds typical crypto daily volumes")
                    print(f"   Bitcoin's total daily volume across ALL exchanges is typically 1-3M BTC")
                elif total_volume_btc > 1_000_000:  # >1M BTC/day
                    print(f"⚠️ HIGH VOLUME: {total_volume_btc/1e6:.1f}M BTC/day") 
                    print(f"   This is high but within realm of possibility for major exchange")
                else:
                    print(f"✅ NORMAL VOLUME: {total_volume_btc/1e3:.0f}K BTC/day")
                
                if extreme_volume_markets:
                    print(f"\n🚨 MARKETS WITH EXTREME VOL/OI RATIOS:")
                    for market in extreme_volume_markets:
                        print(f"  {market['symbol']}: {market['ratio']:.1f}x ratio")
                        print(f"    Volume: {market['volume_24h']/1e6:.1f}M BTC")
                        print(f"    OI: {market['oi_tokens']/1e3:.0f}K BTC")
                
                return okx_data
                
            else:
                print("❌ No OKX data found in our system")
                return None
                
        except Exception as e:
            print(f"❌ Error checking our implementation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def fetch_okx_market_data_directly(self):
        """Fetch OKX market data directly from their API"""
        print("\n🔍 FETCHING OKX API DATA DIRECTLY")
        print("=" * 40)
        
        # OKX API endpoints to test
        endpoints_to_test = [
            ("/api/v5/market/tickers?instType=SWAP", "Perpetual Swaps"),
            ("/api/v5/public/instruments?instType=SWAP", "Swap Instruments"),
            ("/api/v5/market/ticker?instId=BTC-USDT-SWAP", "BTC-USDT-SWAP Specific"),
            ("/api/v5/market/ticker?instId=BTC-USD-SWAP", "BTC-USD-SWAP Specific"),
            ("/api/v5/market/ticker?instId=BTC-USDC-SWAP", "BTC-USDC-SWAP Specific"),
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints_to_test:
                try:
                    print(f"📊 Testing: {description}")
                    print(f"   Endpoint: {endpoint}")
                    
                    async with session.get(f"{self.okx_base}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if isinstance(data, dict) and 'data' in data:
                                ticker_data = data['data']
                                
                                if isinstance(ticker_data, list):
                                    # Look for BTC instruments
                                    btc_items = []
                                    for item in ticker_data:
                                        if isinstance(item, dict):
                                            inst_id = item.get('instId', '')
                                            if 'BTC' in inst_id:
                                                btc_items.append(item)
                                    
                                    print(f"   ✅ Status 200 - Found {len(btc_items)} BTC instruments")
                                    
                                    for item in btc_items:
                                        inst_id = item.get('instId', 'Unknown')
                                        
                                        # Extract volume fields
                                        volume_fields = []
                                        for key, value in item.items():
                                            if any(term in key.lower() for term in ['vol', 'volume', 'turnover']):
                                                volume_fields.append((key, value))
                                        
                                        print(f"     📋 {inst_id}:")
                                        
                                        # Show key volume metrics
                                        vol24h = item.get('vol24h', 0)
                                        volCcy24h = item.get('volCcy24h', 0)
                                        turnover24h = item.get('turnover24h', 0)
                                        
                                        try:
                                            vol24h_float = float(vol24h)
                                            volCcy24h_float = float(volCcy24h)
                                            turnover24h_float = float(turnover24h)
                                            
                                            print(f"       vol24h: {vol24h_float:,.2f}")
                                            print(f"       volCcy24h: {volCcy24h_float:,.2f}")
                                            print(f"       turnover24h: {turnover24h_float:,.2f}")
                                            
                                            # Check for extreme values
                                            if vol24h_float > 1_000_000:  # >1M
                                                print(f"       🚨 EXTREME vol24h: {vol24h_float/1e6:.1f}M")
                                            if volCcy24h_float > 1_000_000:
                                                print(f"       🚨 EXTREME volCcy24h: {volCcy24h_float/1e6:.1f}M")
                                                
                                        except (ValueError, TypeError):
                                            print(f"       vol24h: {vol24h} (non-numeric)")
                                            print(f"       volCcy24h: {volCcy24h} (non-numeric)")
                                            print(f"       turnover24h: {turnover24h} (non-numeric)")
                                        
                                        results[inst_id] = {
                                            'endpoint': endpoint,
                                            'vol24h': vol24h,
                                            'volCcy24h': volCcy24h,
                                            'turnover24h': turnover24h,
                                            'all_fields': volume_fields
                                        }
                                        
                                elif isinstance(ticker_data, dict):
                                    # Single instrument response
                                    inst_id = ticker_data.get('instId', 'Unknown')
                                    vol24h = ticker_data.get('vol24h', 0)
                                    volCcy24h = ticker_data.get('volCcy24h', 0)
                                    
                                    print(f"   ✅ Status 200 - Single instrument: {inst_id}")
                                    print(f"     vol24h: {vol24h}")
                                    print(f"     volCcy24h: {volCcy24h}")
                            else:
                                print(f"   ✅ Status 200 but unexpected data format")
                        else:
                            print(f"   ❌ Status {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                
                print("")
        
        return results
    
    async def analyze_volume_calculation_method(self):
        """Analyze how we calculate volume from OKX API"""
        print("🔍 ANALYZING VOLUME CALCULATION METHOD")
        print("=" * 40)
        
        print("📋 OKX Volume Field Analysis:")
        print("  vol24h: 24h volume in base currency (BTC for BTC-USDT-SWAP)")
        print("  volCcy24h: 24h volume in quote currency (USDT for BTC-USDT-SWAP)")
        print("  turnover24h: 24h turnover (might be in USD)")
        print("")
        
        print("🔍 POTENTIAL ISSUES:")
        print("  1. Using wrong volume field (volCcy24h instead of vol24h)")
        print("  2. Units confusion (contracts vs base currency)")
        print("  3. Volume reported in different denomination")
        print("  4. API returning cumulative vs daily volume")
        print("  5. Volume includes internal/wash trading")
        print("")
        
        print("📊 VERIFICATION STEPS:")
        print("  1. Check which field we're using in our OKX provider")
        print("  2. Compare with external volume data (CoinGecko, CMC)")
        print("  3. Verify field meanings in OKX API documentation")
        print("  4. Check for unit conversion errors")

async def main():
    investigator = OKXVolumeInvestigator()
    
    print("🚨 OKX EXTREME VOLUME INVESTIGATION")
    print("=" * 40)
    print("📋 Issue: OKX shows extremely high volume (8M+ BTC/day)")
    print("📋 Context: Typical crypto daily volumes are 1-3M BTC total")
    print("📋 Goal: Validate if volume data is realistic")
    print("")
    
    # Step 1: Check our current implementation
    okx_data = await investigator.check_our_okx_implementation()
    
    # Step 2: Fetch OKX market data directly
    await investigator.fetch_okx_market_data_directly()
    
    # Step 3: Analyze calculation method
    await investigator.analyze_volume_calculation_method()
    
    print("\n🎯 INVESTIGATION COMPLETE")
    print("Review findings above to determine if OKX volume data is realistic")

if __name__ == "__main__":
    asyncio.run(main())