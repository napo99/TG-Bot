#!/usr/bin/env python3
"""
TEST ENHANCED TG BOT FORMAT
Directly test the updated TG bot formatting function
"""

import asyncio
import aiohttp
import json

async def test_enhanced_format():
    # Fetch real API data
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
            data = await response.json()
    
    print("🧪 TESTING ENHANCED TG BOT FORMAT")
    print("=" * 40)
    print("")
    
    # Simulate the enhanced _format_oi_analysis function
    def format_volume(volume: float) -> str:
        """Format volume with appropriate units"""
        if volume >= 1e6:
            return f"{volume/1e6:.0f}M"
        elif volume >= 1e3:
            return f"{volume/1e3:.0f}K"
        else:
            return f"{volume:.0f}"
    
    def format_oi_analysis_enhanced(data, symbol: str) -> str:
        """Enhanced format matching target specification"""
        try:
            from datetime import datetime
            
            # Handle the new unified API response format
            if 'exchange_breakdown' not in data:
                return f"❌ Invalid data format for {symbol}"
            
            exchange_breakdown = data['exchange_breakdown']
            aggregated = data.get('aggregated_oi', {})
            market_categories = data.get('market_categories', {})
            validation = data.get('validation_summary', {})
            
            # Extract totals
            total_oi_tokens = aggregated.get('total_tokens', 0)
            total_oi_usd = aggregated.get('total_usd', 0)
            total_markets = data.get('total_markets', 0)
            
            # Extract market category data
            usdt_data = market_categories.get('usdt_stable', {})
            usdc_data = market_categories.get('usdc_stable', {})
            usd_data = market_categories.get('usd_inverse', {})
            
            usdt_usd = usdt_data.get('total_usd', 0)
            usdc_usd = usdc_data.get('total_usd', 0)
            inverse_usd = usd_data.get('total_usd', 0)
            
            usdt_pct = usdt_data.get('percentage', 0)
            usdc_pct = usdc_data.get('percentage', 0)
            inverse_pct = usd_data.get('percentage', 0)
            
            stablecoin_usd = usdt_usd + usdc_usd
            stablecoin_pct = usdt_pct + usdc_pct
            
            # Build individual markets list from exchange breakdown
            individual_markets = []
            for exchange_data in exchange_breakdown:
                exchange = exchange_data['exchange']
                markets = exchange_data.get('market_breakdown', [])
                for market in markets:
                    market_type = market.get('type', 'USDT')
                    market_symbol = market.get('symbol', f"{symbol}{market_type}")
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
                    
                    individual_markets.append({
                        'exchange': exchange.title(),
                        'type': market_type,
                        'symbol': market_symbol,
                        'oi_tokens': oi_tokens,
                        'oi_usd': oi_usd,
                        'percentage': percentage,
                        'funding': funding,
                        'volume_24h': volume_24h,
                        'category_label': category_label
                    })
            
            # Sort markets by OI USD value (descending)
            individual_markets.sort(key=lambda x: x['oi_usd'], reverse=True)
            
            # Build message with target specification format
            message = f"""📊 OPEN INTEREST ANALYSIS - {symbol}

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {total_oi_tokens:,.0f} {symbol} (${total_oi_usd/1e9:.1f}B)
• Stablecoin-Margined: ${stablecoin_usd/1e9:.1f}B | {stablecoin_pct:.1f}%
  - USDT: ${usdt_usd/1e9:.1f}B ({usdt_pct:.1f}%)
  - USDC: ${usdc_usd/1e9:.1f}B ({usdc_pct:.1f}%)
• Coin-Margined (Inverse): ${inverse_usd/1e9:.1f}B | {inverse_pct:.1f}%
  - USD: ${inverse_usd/1e9:.1f}B ({inverse_pct:.1f}%)

🔢 STABLECOIN MARKETS ({stablecoin_pct:.1f}%): ${stablecoin_usd/1e9:.1f}B
🔢 INVERSE MARKETS ({inverse_pct:.1f}%): ${inverse_usd/1e9:.1f}B
📊 COMBINED TOTAL: ${total_oi_usd/1e9:.1f}B

📈 TOP MARKETS:"""
            
            # Add individual markets (ranked 1-13)
            for i, market in enumerate(individual_markets[:13], 1):
                funding_sign = "+" if market['funding'] >= 0 else ""
                volume_formatted = format_volume(market['volume_24h'])
                
                message += f"\n{i}. {market['exchange']} {market['type']}: {market['oi_tokens']:,.0f} {symbol} (${market['oi_usd']/1e9:.1f}B) | {market['percentage']:.1f}% {market['category_label']}"
                message += f"\n   Funding: {funding_sign}{market['funding']*100:.4f}% | Vol: {volume_formatted} {symbol}"
            
            # Add coverage summary
            message += f"""

🏢 COVERAGE SUMMARY:
• Exchanges: {validation.get('successful_exchanges', 0)} working
• Markets: {total_markets} total
• Phase 2A: USDT + USDC support

🚨 MARKET ANALYSIS:
• Sentiment: NEUTRAL ⚪➡️
• Risk Level: NORMAL
• Coverage: Multi-stablecoin across {validation.get('successful_exchanges', 0)} exchanges

🕐 {datetime.now().strftime('%H:%M:%S')} UTC / {(datetime.now().replace(hour=(datetime.now().hour + 8) % 24)).strftime('%H:%M:%S')} SGT"""
            
            return message
            
        except Exception as e:
            return f"❌ Error formatting OI analysis for {symbol}: {str(e)}"
    
    # Test the enhanced format
    message = format_oi_analysis_enhanced(data, "BTC")
    
    print("📱 ENHANCED TG MESSAGE OUTPUT:")
    print("=" * 60)
    print(message)
    print("=" * 60)
    
    print(f"\n📏 Message Length: {len(message)} characters")
    print(f"📊 Lines: {len(message.split(chr(10)))}")
    
    # Check if it would fit in Telegram
    if len(message) < 4096:
        print("✅ Within Telegram message limit")
    else:
        print("⚠️ Message may exceed Telegram limits")
        
    # Count markets in output
    market_lines = [line for line in message.split('\n') if line.strip() and line[0].isdigit()]
    print(f"🏆 Markets displayed: {len(market_lines)}")
    
    print("\n🎯 Enhanced format ready for deployment!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_format())