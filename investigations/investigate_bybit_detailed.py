#!/usr/bin/env python3
"""
BYBIT DETAILED INVESTIGATION
Shows all BTC trading pairs tracked and not tracked with their OI and volume data
"""

import aiohttp
import asyncio
import json

class BybitDetailedInvestigator:
    def __init__(self):
        self.bybit_base = "https://api.bybit.com"
        
    async def get_current_bybit_tracking(self):
        """Get our current Bybit tracking data"""
        print("📊 OUR CURRENT BYBIT TRACKING")
        print("=" * 35)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
                    data = await response.json()
            
            # Find Bybit data
            bybit_data = None
            for exchange in data.get('exchange_breakdown', []):
                if exchange['exchange'].lower() == 'bybit':
                    bybit_data = exchange
                    break
            
            if bybit_data:
                print(f"✅ CURRENTLY TRACKED:")
                print(f"  Total: {bybit_data['oi_tokens']:,.0f} BTC (${bybit_data['oi_usd']/1e9:.1f}B)")
                print(f"  Markets: {bybit_data['markets']}")
                print("")
                
                tracked_symbols = []
                for market in bybit_data.get('market_breakdown', []):
                    symbol = market['symbol']
                    market_type = market['type']
                    oi_tokens = market['oi_tokens']
                    oi_usd = market['oi_usd']
                    volume_24h = market['volume_24h']
                    volume_24h_usd = market['volume_24h_usd']
                    price = market['price']
                    funding_rate = market['funding_rate']
                    
                    contract_type = "LINEAR" if market_type in ['USDT', 'USDC'] else "INVERSE"
                    
                    print(f"  📋 {symbol} ({market_type} - {contract_type}):")
                    print(f"    OI: {oi_tokens:,.0f} BTC (${oi_usd/1e6:.0f}M)")
                    print(f"    Volume: {volume_24h:,.0f} BTC (${volume_24h_usd/1e6:.0f}M)")
                    print(f"    Price: ${price:,.2f}")
                    print(f"    Funding: {funding_rate*100:+.3f}%")
                    print("")
                    
                    tracked_symbols.append(symbol)
                
                return tracked_symbols
            else:
                print("❌ No Bybit data found in our system")
                return []
                
        except Exception as e:
            print(f"❌ Error getting current data: {e}")
            return []
    
    async def get_all_bybit_btc_instruments(self):
        """Get all BTC instruments from Bybit API"""
        print("🔍 ALL BYBIT BTC INSTRUMENTS FROM API")
        print("=" * 40)
        
        all_btc_instruments = {}
        
        # Categories to check
        categories = [
            ('linear', 'Linear Perpetuals & Futures'),
            ('inverse', 'Inverse Perpetuals & Futures'),
            ('option', 'Options')
        ]
        
        async with aiohttp.ClientSession() as session:
            for category, description in categories:
                try:
                    print(f"📊 {description.upper()} ({category}):")
                    
                    url = f"{self.bybit_base}/v5/market/instruments-info?category={category}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('retCode') == 0:
                                instruments = data.get('result', {}).get('list', [])
                                btc_instruments = [i for i in instruments if i.get('baseCoin') == 'BTC' or 'BTC' in i.get('symbol', '')]
                                
                                print(f"  ✅ Found {len(btc_instruments)} BTC instruments")
                                print("")
                                
                                if btc_instruments:
                                    # Group by contract type
                                    perpetuals = []
                                    futures = []
                                    options = []
                                    
                                    for instrument in btc_instruments:
                                        contract_type = instrument.get('contractType', '')
                                        if 'Perpetual' in contract_type:
                                            perpetuals.append(instrument)
                                        elif 'Future' in contract_type or 'Delivery' in contract_type:
                                            futures.append(instrument)
                                        elif 'Option' in contract_type:
                                            options.append(instrument)
                                        else:
                                            perpetuals.append(instrument)  # Default to perpetual
                                    
                                    # Store in our collection
                                    all_btc_instruments[category] = {
                                        'perpetuals': perpetuals,
                                        'futures': futures,
                                        'options': options
                                    }
                                    
                                    # Show perpetuals
                                    if perpetuals:
                                        print(f"  🔄 PERPETUALS ({len(perpetuals)}):")
                                        for instrument in perpetuals:
                                            symbol = instrument.get('symbol', 'Unknown')
                                            status = instrument.get('status', 'Unknown')
                                            quote_coin = instrument.get('quoteCoin', 'Unknown')
                                            settle_coin = instrument.get('settleCoin', 'Unknown')
                                            print(f"    • {symbol} | Quote: {quote_coin} | Settle: {settle_coin} | Status: {status}")
                                        print("")
                                    
                                    # Show futures
                                    if futures:
                                        print(f"  📅 FUTURES/DELIVERY ({len(futures)}):")
                                        for instrument in futures:
                                            symbol = instrument.get('symbol', 'Unknown')
                                            delivery_time = instrument.get('deliveryTime', 'Unknown')
                                            if delivery_time != 'Unknown' and delivery_time != '0':
                                                # Convert timestamp to readable date
                                                try:
                                                    import datetime
                                                    dt = datetime.datetime.fromtimestamp(int(delivery_time) / 1000)
                                                    delivery_str = dt.strftime('%Y-%m-%d')
                                                except:
                                                    delivery_str = delivery_time
                                            else:
                                                delivery_str = 'No expiry'
                                            
                                            quote_coin = instrument.get('quoteCoin', 'Unknown')
                                            settle_coin = instrument.get('settleCoin', 'Unknown')
                                            status = instrument.get('status', 'Unknown')
                                            print(f"    • {symbol} | Delivery: {delivery_str} | Quote: {quote_coin} | Settle: {settle_coin} | Status: {status}")
                                        print("")
                                    
                                    # Show options (brief)
                                    if options:
                                        print(f"  🎯 OPTIONS ({len(options)}):")
                                        print(f"    • {len(options)} option contracts available")
                                        print("")
                            else:
                                print(f"  ❌ API Error: {data.get('retMsg', 'Unknown error')}")
                        else:
                            print(f"  ❌ HTTP Status {response.status}")
                    
                except Exception as e:
                    print(f"  ❌ Exception: {e}")
                print("")
        
        return all_btc_instruments
    
    async def get_oi_and_volume_for_instruments(self, all_instruments, tracked_symbols):
        """Get OI and volume data for specific instruments"""
        print("📊 OI & VOLUME DATA FOR ALL BTC INSTRUMENTS")
        print("=" * 45)
        
        async with aiohttp.ClientSession() as session:
            for category, instruments_group in all_instruments.items():
                print(f"📋 {category.upper()} CATEGORY:")
                print("")
                
                # Combine perpetuals and futures for data fetching
                all_instruments_in_category = instruments_group['perpetuals'] + instruments_group['futures']
                
                if all_instruments_in_category:
                    for instrument in all_instruments_in_category:
                        symbol = instrument.get('symbol', 'Unknown')
                        contract_type = instrument.get('contractType', 'Unknown')
                        status = instrument.get('status', 'Unknown')
                        
                        # Check if we're currently tracking this
                        is_tracked = symbol in tracked_symbols
                        tracking_status = "✅ TRACKED" if is_tracked else "❌ NOT TRACKED"
                        
                        print(f"  {tracking_status} | {symbol} ({contract_type}):")
                        
                        if status.lower() != 'trading':
                            print(f"    ⚠️ Status: {status} - May not have active trading")
                            print("")
                            continue
                        
                        try:
                            # Get ticker data for this specific symbol
                            ticker_url = f"{self.bybit_base}/v5/market/tickers?category={category}&symbol={symbol}"
                            async with session.get(ticker_url) as response:
                                if response.status == 200:
                                    ticker_data = await response.json()
                                    
                                    if ticker_data.get('retCode') == 0:
                                        tickers = ticker_data.get('result', {}).get('list', [])
                                        if tickers:
                                            ticker = tickers[0]
                                            
                                            # Extract data
                                            last_price = float(ticker.get('lastPrice', 0))
                                            volume_24h = float(ticker.get('volume24h', 0))
                                            turnover_24h = float(ticker.get('turnover24h', 0))
                                            open_interest = float(ticker.get('openInterest', 0))
                                            open_interest_value = float(ticker.get('openInterestValue', 0))
                                            funding_rate = float(ticker.get('fundingRate', 0))
                                            
                                            # Convert to BTC terms
                                            if last_price > 0:
                                                volume_24h_usd = turnover_24h
                                                volume_24h_btc = volume_24h_usd / last_price if last_price > 0 else 0
                                                
                                                # OI conversion depends on contract type
                                                if category == 'linear':
                                                    # Linear: openInterest is in base currency (BTC), openInterestValue in USD
                                                    oi_btc = open_interest
                                                    oi_usd = open_interest_value
                                                elif category == 'inverse':
                                                    # Inverse: openInterest is in contracts, convert to BTC
                                                    # For inverse, openInterest might be in USD terms
                                                    oi_usd = open_interest_value
                                                    oi_btc = oi_usd / last_price if last_price > 0 else 0
                                                else:
                                                    oi_btc = 0
                                                    oi_usd = 0
                                                
                                                print(f"    💰 Price: ${last_price:,.2f}")
                                                print(f"    📊 OI: {oi_btc:,.0f} BTC (${oi_usd/1e6:.1f}M)")
                                                print(f"    📈 Volume 24h: {volume_24h_btc:,.0f} BTC (${volume_24h_usd/1e6:.1f}M)")
                                                if funding_rate != 0:
                                                    print(f"    💸 Funding: {funding_rate*100:+.3f}%")
                                            else:
                                                print(f"    ⚠️ No price data available")
                                        else:
                                            print(f"    ⚠️ No ticker data available")
                                    else:
                                        print(f"    ❌ Ticker API Error: {ticker_data.get('retMsg', 'Unknown')}")
                                else:
                                    print(f"    ❌ Ticker HTTP {response.status}")
                        
                        except Exception as e:
                            print(f"    ❌ Error getting data: {e}")
                        
                        print("")
                
                print("-" * 50)
                print("")
    
    async def summarize_tracking_gaps(self, all_instruments, tracked_symbols):
        """Summarize what we're missing"""
        print("🎯 BYBIT TRACKING GAPS SUMMARY")
        print("=" * 35)
        
        total_perpetuals = 0
        total_futures = 0
        tracked_perpetuals = 0
        untracked_perpetuals = 0
        untracked_futures = 0
        
        print("📊 SUMMARY BY CATEGORY:")
        for category, instruments_group in all_instruments.items():
            perpetuals = instruments_group['perpetuals']
            futures = instruments_group['futures']
            
            total_perpetuals += len(perpetuals)
            total_futures += len(futures)
            
            tracked_perp_count = sum(1 for p in perpetuals if p.get('symbol') in tracked_symbols)
            untracked_perp_count = len(perpetuals) - tracked_perp_count
            
            tracked_perpetuals += tracked_perp_count
            untracked_perpetuals += untracked_perp_count
            untracked_futures += len(futures)
            
            print(f"  {category.upper()}:")
            print(f"    Perpetuals: {len(perpetuals)} total | {tracked_perp_count} tracked | {untracked_perp_count} untracked")
            print(f"    Futures: {len(futures)} total | 0 tracked | {len(futures)} untracked")
        
        print("")
        print("🔍 OVERALL GAPS:")
        print(f"  ✅ Tracked Perpetuals: {tracked_perpetuals}")
        print(f"  ❌ Untracked Perpetuals: {untracked_perpetuals}")
        print(f"  ❌ Untracked Futures: {untracked_futures}")
        print(f"  📊 Total Missing Contracts: {untracked_perpetuals + untracked_futures}")

async def main():
    investigator = BybitDetailedInvestigator()
    
    print("🔍 BYBIT DETAILED INVESTIGATION")
    print("=" * 40)
    print("📋 Goal: List all BTC trading pairs with their OI and volume")
    print("📋 Compare: Currently tracked vs available contracts")
    print("")
    
    # Step 1: Get our current tracking
    tracked_symbols = await investigator.get_current_bybit_tracking()
    
    # Step 2: Get all Bybit BTC instruments
    all_instruments = await investigator.get_all_bybit_btc_instruments()
    
    # Step 3: Get OI and volume data for each
    await investigator.get_oi_and_volume_for_instruments(all_instruments, tracked_symbols)
    
    # Step 4: Summarize gaps
    await investigator.summarize_tracking_gaps(all_instruments, tracked_symbols)
    
    print("\n🎯 BYBIT INVESTIGATION COMPLETE")
    print("All BTC trading pairs listed with their OI/volume data")

if __name__ == "__main__":
    asyncio.run(main())