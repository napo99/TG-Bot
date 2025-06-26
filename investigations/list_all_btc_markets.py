#!/usr/bin/env python3
"""
COMPREHENSIVE BTC MARKETS LISTING AGENT
Lists ALL BTC markets across all exchanges with detailed breakdowns
"""

import aiohttp
import asyncio
import json

class BTCMarketsAnalyzer:
    
    async def get_detailed_btc_markets(self):
        """Get detailed breakdown of ALL BTC markets"""
        print("📊 COMPREHENSIVE BTC MARKETS ANALYSIS")
        print("=" * 45)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
                    data = await response.json()
            
            if not data.get('success'):
                print("❌ Failed to fetch BTC market data")
                return
            
            total_oi_usd = data.get('aggregated_oi', {}).get('total_usd', 0)
            total_oi_tokens = data.get('aggregated_oi', {}).get('total_tokens', 0)
            
            print(f"🎯 TOTAL BTC OPEN INTEREST ACROSS ALL EXCHANGES:")
            print(f"  Total: {total_oi_tokens:,.0f} BTC (${total_oi_usd/1e9:.2f}B)")
            print(f"  Exchanges: {len(data.get('exchange_breakdown', []))}")
            print(f"  Markets: {data.get('total_markets', 0)}")
            print("")
            
            # Analyze each exchange in detail
            market_counter = 1
            all_markets = []
            
            for exchange_data in data.get('exchange_breakdown', []):
                exchange = exchange_data['exchange'].upper()
                exchange_oi_tokens = exchange_data['oi_tokens']
                exchange_oi_usd = exchange_data['oi_usd']
                exchange_pct = exchange_data['oi_percentage']
                exchange_markets = exchange_data['markets']
                
                print(f"🏢 {exchange} EXCHANGE:")
                print(f"  Total: {exchange_oi_tokens:,.0f} BTC (${exchange_oi_usd/1e9:.2f}B) - {exchange_pct:.1f}%")
                print(f"  Markets: {exchange_markets}")
                print("")
                print(f"  📋 INDIVIDUAL MARKETS:")
                
                # List individual markets
                for market in exchange_data.get('market_breakdown', []):
                    symbol = market.get('symbol', 'Unknown')
                    market_type = market.get('type', 'Unknown')
                    oi_tokens = market.get('oi_tokens', 0)
                    oi_usd = market.get('oi_usd', 0)
                    price = market.get('price', 0)
                    funding_rate = market.get('funding_rate', 0)
                    volume_24h = market.get('volume_24h', 0)
                    volume_24h_usd = market.get('volume_24h_usd', 0)
                    
                    # Calculate percentage of total market
                    market_pct_total = (oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
                    market_pct_exchange = (oi_usd / exchange_oi_usd * 100) if exchange_oi_usd > 0 else 0
                    
                    # Determine settlement currency info
                    if market_type == 'USDT':
                        settlement_info = "USDT-Margined (Linear)"
                        category = "STABLE"
                    elif market_type == 'USDC':
                        settlement_info = "USDC-Margined (Linear)"  
                        category = "STABLE"
                    elif market_type == 'USD':
                        settlement_info = "USD-Margined (Inverse)"
                        category = "INVERSE"
                    else:
                        settlement_info = f"{market_type}-Margined"
                        category = "UNKNOWN"
                    
                    print(f"    {market_counter:2d}. {symbol}")
                    print(f"        Type: {settlement_info} ({category})")
                    print(f"        OI: {oi_tokens:,.0f} BTC")
                    print(f"        USD Value: ${oi_usd/1e6:.1f}M")
                    print(f"        Price: ${price:,.2f}")
                    print(f"        Market Share: {market_pct_total:.2f}% (of total) | {market_pct_exchange:.1f}% (of {exchange})")
                    print(f"        Funding: {funding_rate*100:+.4f}%")
                    print(f"        Volume 24h: {volume_24h:,.0f} BTC (${volume_24h_usd/1e6:.1f}M)")
                    print("")
                    
                    # Store for summary analysis
                    all_markets.append({
                        'rank': market_counter,
                        'exchange': exchange,
                        'symbol': symbol,
                        'type': market_type,
                        'category': category,
                        'oi_tokens': oi_tokens,
                        'oi_usd': oi_usd,
                        'market_pct_total': market_pct_total,
                        'price': price,
                        'funding_rate': funding_rate,
                        'volume_24h': volume_24h,
                        'volume_24h_usd': volume_24h_usd
                    })
                    
                    market_counter += 1
                
                print("-" * 50)
                print("")
            
            # Summary analysis
            await self.analyze_market_summary(all_markets, total_oi_usd, total_oi_tokens)
            
        except Exception as e:
            print(f"❌ Error analyzing BTC markets: {e}")
            import traceback
            traceback.print_exc()
    
    async def analyze_market_summary(self, all_markets, total_oi_usd, total_oi_tokens):
        """Analyze summary statistics of all markets"""
        print("📊 MARKET SUMMARY ANALYSIS")
        print("=" * 30)
        
        # Sort by OI USD value
        sorted_markets = sorted(all_markets, key=lambda x: x['oi_usd'], reverse=True)
        
        print(f"🏆 TOP 10 BTC MARKETS BY OPEN INTEREST:")
        print("")
        for i, market in enumerate(sorted_markets[:10], 1):
            print(f"  {i:2d}. {market['exchange']} {market['symbol']}")
            print(f"      {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e9:.2f}B) - {market['market_pct_total']:.1f}% - {market['category']}")
            print(f"      Funding: {market['funding_rate']*100:+.4f}% | Vol: {market['volume_24h']/1000:.0f}K BTC")
            print("")
        
        # Category analysis
        stable_markets = [m for m in all_markets if m['category'] == 'STABLE']
        inverse_markets = [m for m in all_markets if m['category'] == 'INVERSE']
        
        stable_oi_usd = sum(m['oi_usd'] for m in stable_markets)
        inverse_oi_usd = sum(m['oi_usd'] for m in inverse_markets)
        stable_oi_tokens = sum(m['oi_tokens'] for m in stable_markets)
        inverse_oi_tokens = sum(m['oi_tokens'] for m in inverse_markets)
        
        print("📊 MARKET TYPE BREAKDOWN:")
        print(f"  STABLECOIN-MARGINED ({len(stable_markets)} markets):")
        print(f"    Total: {stable_oi_tokens:,.0f} BTC (${stable_oi_usd/1e9:.2f}B)")
        print(f"    Percentage: {stable_oi_usd/total_oi_usd*100:.1f}% of total OI")
        print("")
        
        # Break down stablecoin markets
        usdt_markets = [m for m in stable_markets if m['type'] == 'USDT']
        usdc_markets = [m for m in stable_markets if m['type'] == 'USDC']
        
        if usdt_markets:
            usdt_oi_usd = sum(m['oi_usd'] for m in usdt_markets)
            usdt_oi_tokens = sum(m['oi_tokens'] for m in usdt_markets)
            print(f"    📋 USDT Markets ({len(usdt_markets)}):")
            print(f"      Total: {usdt_oi_tokens:,.0f} BTC (${usdt_oi_usd/1e9:.2f}B)")
            for market in sorted(usdt_markets, key=lambda x: x['oi_usd'], reverse=True):
                print(f"        {market['exchange']} {market['symbol']}: {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e6:.0f}M)")
            print("")
        
        if usdc_markets:
            usdc_oi_usd = sum(m['oi_usd'] for m in usdc_markets)
            usdc_oi_tokens = sum(m['oi_tokens'] for m in usdc_markets)
            print(f"    📋 USDC Markets ({len(usdc_markets)}):")
            print(f"      Total: {usdc_oi_tokens:,.0f} BTC (${usdc_oi_usd/1e9:.2f}B)")
            for market in sorted(usdc_markets, key=lambda x: x['oi_usd'], reverse=True):
                print(f"        {market['exchange']} {market['symbol']}: {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e6:.0f}M)")
            print("")
        
        print(f"  COIN-MARGINED/INVERSE ({len(inverse_markets)} markets):")
        print(f"    Total: {inverse_oi_tokens:,.0f} BTC (${inverse_oi_usd/1e9:.2f}B)")
        print(f"    Percentage: {inverse_oi_usd/total_oi_usd*100:.1f}% of total OI")
        print("")
        for market in sorted(inverse_markets, key=lambda x: x['oi_usd'], reverse=True):
            print(f"      {market['exchange']} {market['symbol']}: {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e6:.0f}M)")
        print("")
        
        # Exchange dominance
        print("🏢 EXCHANGE MARKET DOMINANCE:")
        exchange_totals = {}
        for market in all_markets:
            exchange = market['exchange']
            if exchange not in exchange_totals:
                exchange_totals[exchange] = {'oi_usd': 0, 'oi_tokens': 0, 'markets': 0}
            exchange_totals[exchange]['oi_usd'] += market['oi_usd']
            exchange_totals[exchange]['oi_tokens'] += market['oi_tokens']
            exchange_totals[exchange]['markets'] += 1
        
        for exchange, totals in sorted(exchange_totals.items(), key=lambda x: x[1]['oi_usd'], reverse=True):
            pct = totals['oi_usd'] / total_oi_usd * 100
            print(f"  {exchange}: {totals['oi_tokens']:,.0f} BTC (${totals['oi_usd']/1e9:.2f}B) - {pct:.1f}% - {totals['markets']} markets")
        
        print("")
        print("🎯 COMPREHENSIVE ANALYSIS COMPLETE")
        print(f"✅ Total Markets Analyzed: {len(all_markets)}")
        print(f"✅ Total Open Interest: {total_oi_tokens:,.0f} BTC (${total_oi_usd/1e9:.2f}B)")
        print(f"✅ Exchange Coverage: {len(exchange_totals)} exchanges")

async def main():
    analyzer = BTCMarketsAnalyzer()
    await analyzer.get_detailed_btc_markets()

if __name__ == "__main__":
    asyncio.run(main())