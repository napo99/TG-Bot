#!/usr/bin/env python3
"""
BYBIT SUMMARY WITH OI/VOLUME DATA
Focused summary of Bybit BTC contracts with their actual OI and volume numbers
"""

import aiohttp
import asyncio
import json

class BybitOISummary:
    def __init__(self):
        self.bybit_base = "https://api.bybit.com"
        
    async def get_oi_data_for_key_contracts(self):
        """Get OI data for key Bybit BTC contracts"""
        print("📊 BYBIT BTC CONTRACTS - OI & VOLUME DATA")
        print("=" * 50)
        
        # Key contracts to check (perpetuals and main futures)
        key_contracts = [
            # PERPETUALS (what we track)
            ('linear', 'BTCUSDT', '✅ TRACKED'),
            ('linear', 'BTCPERP', '✅ TRACKED'),  
            ('inverse', 'BTCUSD', '✅ TRACKED'),
            
            # ADDITIONAL PERPETUALS (not tracked)
            ('linear', 'ETHBTCUSDT', '❌ NOT TRACKED'),
            ('linear', 'PUMPBTCUSDT', '❌ NOT TRACKED'),
            
            # KEY FUTURES (not tracked)
            ('linear', 'BTC-27JUN25', '❌ NOT TRACKED'),
            ('linear', 'BTC-26SEP25', '❌ NOT TRACKED'),
            ('linear', 'BTC-26DEC25', '❌ NOT TRACKED'),
            ('linear', 'BTCUSDT-27JUN25', '❌ NOT TRACKED'),
            ('linear', 'BTCUSDT-26SEP25', '❌ NOT TRACKED'),
            ('linear', 'BTCUSDT-26DEC25', '❌ NOT TRACKED'),
            
            ('inverse', 'BTCUSDM25', '❌ NOT TRACKED'),
            ('inverse', 'BTCUSDU25', '❌ NOT TRACKED'),
            ('inverse', 'BTCUSDZ25', '❌ NOT TRACKED'),
        ]
        
        async with aiohttp.ClientSession() as session:
            print("🔄 PERPETUAL CONTRACTS:")
            print("")
            
            perpetual_total_oi = 0
            futures_total_oi = 0
            
            for category, symbol, status in key_contracts:
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
                                            oi_btc = open_interest
                                            oi_usd = open_interest_value
                                        else:  # inverse
                                            oi_usd = open_interest_value
                                            oi_btc = oi_usd / last_price if last_price > 0 else 0
                                        
                                        # Categorize
                                        if any(term in symbol for term in ['-27JUN25', '-26SEP25', '-26DEC25', 'M25', 'U25', 'Z25']):
                                            contract_type = "FUTURES"
                                            futures_total_oi += oi_btc
                                        else:
                                            contract_type = "PERPETUAL"
                                            perpetual_total_oi += oi_btc
                                        
                                        settlement = "LINEAR" if category == 'linear' else "INVERSE"
                                        
                                        print(f"  {status} | {symbol} ({settlement} {contract_type}):")
                                        print(f"    💰 Price: ${last_price:,.2f}")
                                        print(f"    📊 OI: {oi_btc:,.0f} BTC (${oi_usd/1e6:.1f}M)")
                                        print(f"    📈 Volume 24h: {volume_24h_btc:,.0f} BTC (${volume_24h_usd/1e6:.1f}M)")
                                        if funding_rate != 0:
                                            print(f"    💸 Funding: {funding_rate*100:+.3f}%")
                                        print("")
                                    else:
                                        print(f"  {status} | {symbol}: ⚠️ No price data")
                                        print("")
                                else:
                                    print(f"  {status} | {symbol}: ⚠️ No ticker data")
                                    print("")
                            else:
                                print(f"  {status} | {symbol}: ❌ API Error - {ticker_data.get('retMsg', 'Unknown')}")
                                print("")
                        else:
                            print(f"  {status} | {symbol}: ❌ HTTP {response.status}")
                            print("")
                
                except Exception as e:
                    print(f"  {status} | {symbol}: ❌ Exception - {e}")
                    print("")
            
            print("🎯 BYBIT SUMMARY:")
            print(f"  ✅ Tracked Perpetual OI: {perpetual_total_oi:,.0f} BTC")
            print(f"  ❌ Untracked Futures OI: {futures_total_oi:,.0f} BTC")
            print(f"  📊 Potential Additional OI: {futures_total_oi:,.0f} BTC")
            print("")
            
            print("📋 MAIN FINDINGS:")
            print("  • Linear perpetuals: BTCUSDT, BTCPERP (USDC)")
            print("  • Inverse perpetuals: BTCUSD")
            print("  • Additional perpetuals: ETHBTCUSDT, PUMPBTCUSDT")
            print("  • Quarterly futures: Multiple contracts with various expiries")
            print("  • Options: 500+ contracts (not shown - complex structure)")

async def main():
    summary = BybitOISummary()
    
    print("🔍 BYBIT KEY CONTRACTS SUMMARY")
    print("=" * 40)
    print("📋 Focus: Show actual OI/volume for important contracts")
    print("📋 Goal: Understand what we're tracking vs missing")
    print("")
    
    await summary.get_oi_data_for_key_contracts()
    
    print("\n✅ BYBIT ANALYSIS COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())