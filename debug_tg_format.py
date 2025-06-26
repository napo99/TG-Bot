#!/usr/bin/env python3
"""
DEBUG TELEGRAM BOT FORMAT ISSUE
Simulates TG bot formatting with real API data to find issues
"""

import json
import aiohttp
import asyncio
from datetime import datetime

async def debug_tg_formatting():
    # Fetch real API data
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
            data = await response.json()
    
    print("🔍 DEBUGGING TG BOT FORMAT ISSUE")
    print("=" * 40)
    print("")
    
    # Simulate the TG bot _format_oi_analysis function logic
    try:
        # Handle the new unified API response format
        if 'exchange_breakdown' not in data:
            print("❌ Missing exchange_breakdown")
            return
        
        exchange_breakdown = data['exchange_breakdown']
        aggregated = data.get('aggregated_oi', {})
        market_categories = data.get('market_categories', {})
        validation = data.get('validation_summary', {})
        
        print(f"✅ Data loaded:")
        print(f"  Exchanges: {len(exchange_breakdown)}")
        print(f"  Total markets: {data.get('total_markets', 0)}")
        print("")
        
        # Extract totals
        total_oi_tokens = aggregated.get('total_tokens', 0)
        total_oi_usd = aggregated.get('total_usd', 0)
        total_markets = data.get('total_markets', 0)
        
        # Extract market category data
        usdt_data = market_categories.get('usdt_stable', {})
        usdc_data = market_categories.get('usdc_stable', {})
        usd_data = market_categories.get('usd_inverse', {})
        
        print("📊 CATEGORY DATA:")
        print(f"  USDT: {usdt_data.get('total_tokens', 0):,.0f} BTC")
        print(f"  USDC: {usdc_data.get('total_tokens', 0):,.0f} BTC") 
        print(f"  USD: {usd_data.get('total_tokens', 0):,.0f} BTC")
        print("")
        
        # Build individual markets list from exchange breakdown
        individual_markets = []
        print("🏗️ BUILDING INDIVIDUAL MARKETS:")
        
        for exchange_data in exchange_breakdown:
            exchange = exchange_data['exchange']
            markets = exchange_data.get('market_breakdown', [])
            print(f"  {exchange}: {len(markets)} markets")
            
            for market in markets:
                market_type = market.get('type', 'USDT')
                market_symbol = market.get('symbol', f"BTC{market_type}")
                oi_tokens = market.get('oi_tokens', 0)
                oi_usd = market.get('oi_usd', 0)
                funding = market.get('funding_rate', 0)
                volume_24h = market.get('volume_24h', 0)
                
                # Calculate percentage of total
                percentage = (oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
                
                # Determine market category label
                if market_type == 'USDT':
                    category_label = 'STABLE'
                elif market_type == 'USDC':
                    category_label = 'STABLE'
                else:  # USD/Inverse
                    category_label = 'INVERSE'
                
                market_info = {
                    'exchange': exchange.title(),
                    'type': market_type,
                    'symbol': market_symbol,
                    'oi_tokens': oi_tokens,
                    'oi_usd': oi_usd,
                    'percentage': percentage,
                    'funding': funding,
                    'volume_24h': volume_24h,
                    'category_label': category_label
                }
                
                individual_markets.append(market_info)
                print(f"    {market_symbol}: {oi_tokens:,.0f} BTC ({category_label})")
        
        print(f"\n✅ Total individual markets: {len(individual_markets)}")
        
        # Sort markets by OI USD value (descending)
        individual_markets.sort(key=lambda x: x['oi_usd'], reverse=True)
        
        print("\n📈 TOP 5 MARKETS (by USD value):")
        for i, market in enumerate(individual_markets[:5], 1):
            print(f"  {i}. {market['exchange']} {market['type']}: {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e9:.1f}B) - {market['percentage']:.1f}% {market['category_label']}")
        
        # Generate test message
        print("\n📱 GENERATING TEST MESSAGE:")
        
        usdt_usd = usdt_data.get('total_usd', 0)
        usdc_usd = usdc_data.get('total_usd', 0)
        inverse_usd = usd_data.get('total_usd', 0)
        
        usdt_pct = usdt_data.get('percentage', 0)
        usdc_pct = usdc_data.get('percentage', 0)
        inverse_pct = usd_data.get('percentage', 0)
        
        stablecoin_usd = usdt_usd + usdc_usd
        stablecoin_pct = usdt_pct + usdc_pct
        
        # Generate sample message
        message = f"""📊 OPEN INTEREST ANALYSIS - BTC

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {total_oi_tokens:,.0f} BTC (${total_oi_usd/1e9:.1f}B)
• Stablecoin-Margined: ${stablecoin_usd/1e9:.1f}B | {stablecoin_pct:.1f}%
  - USDT: ${usdt_usd/1e9:.1f}B ({usdt_pct:.1f}%)
  - USDC: ${usdc_usd/1e9:.1f}B ({usdc_pct:.1f}%)
• Coin-Margined (Inverse): ${inverse_usd/1e9:.1f}B | {inverse_pct:.1f}%
  - USD: ${inverse_usd/1e9:.1f}B ({inverse_pct:.1f}%)

📈 TOP 3 MARKETS:"""
        
        # Add top 3 markets
        for i, market in enumerate(individual_markets[:3], 1):
            funding_sign = "+" if market['funding'] >= 0 else ""
            volume_formatted = f"{market['volume_24h']:,.0f}" if market['volume_24h'] >= 1000 else f"{market['volume_24h']:.0f}"
            
            message += f"\n{i}. {market['exchange']} {market['type']}: {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e9:.1f}B) | {market['percentage']:.1f}% {market['category_label']}"
            message += f"\n   Funding: {funding_sign}{market['funding']*100:.4f}% | Vol: {volume_formatted} BTC"
        
        print(message)
        print("\n" + "=" * 50)
        
        # Validation checks
        print("🔍 VALIDATION CHECKS:")
        
        # Check if totals add up
        calculated_total = sum(market['oi_usd'] for market in individual_markets)
        diff_pct = abs(calculated_total - total_oi_usd) / total_oi_usd * 100 if total_oi_usd > 0 else 0
        
        if diff_pct < 1:
            print(f"✅ Market totals match: ${calculated_total/1e9:.1f}B ≈ ${total_oi_usd/1e9:.1f}B")
        else:
            print(f"❌ Market totals mismatch: ${calculated_total/1e9:.1f}B vs ${total_oi_usd/1e9:.1f}B ({diff_pct:.1f}% diff)")
        
        print(f"✅ Individual markets found: {len(individual_markets)}/13")
        print(f"✅ Expected total markets: {total_markets}")
        
        if len(individual_markets) == total_markets:
            print("✅ All markets accounted for!")
        else:
            print(f"⚠️ Missing {total_markets - len(individual_markets)} markets")
            
    except Exception as e:
        print(f"❌ Error in formatting: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_tg_formatting())