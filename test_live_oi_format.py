#!/usr/bin/env python3
"""Test live OI formatting - shows exact Telegram bot output"""

import json
import requests
from datetime import datetime

def format_oi_analysis(data, symbol: str) -> str:
    """Format OI analysis with exact target output specification - EXACT TELEGRAM BOT CODE"""
    try:
        # Handle the actual API response format from /multi_oi
        if 'exchange_breakdown' not in data:
            return f"❌ Invalid data format for {symbol}"
        
        exchange_breakdown = data['exchange_breakdown']
        aggregated = data.get('aggregated_oi', {})
        
        # Calculate totals
        total_oi_tokens = aggregated.get('total_tokens', 0)
        total_oi_usd = aggregated.get('total_usd', 0)
        
        all_markets = []
        usdt_usd = 0
        usdc_usd = 0
        inverse_usd = 0
        
        for exchange_data in exchange_breakdown:
            market_entry = {
                "name": exchange_data['exchange'].title(),
                "oi_tokens": exchange_data["oi_tokens"],
                "oi_usd": exchange_data["oi_usd"],
                "percentage": exchange_data.get("oi_percentage", 0),
                "category": "STABLE",  # Assume USDT for now
                "funding": exchange_data["funding_rate"],
                "volume": exchange_data["volume_24h"]
            }
            all_markets.append(market_entry)
            
            # For now, assume all are USDT markets since API doesn't specify breakdown
            usdt_usd += exchange_data["oi_usd"]
        
        # Sort by USD value descending
        all_markets.sort(key=lambda x: x["oi_usd"], reverse=True)
        
        stablecoin_usd = usdt_usd + usdc_usd
        stablecoin_pct = (stablecoin_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
        inverse_pct = (inverse_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
        
        # Build message
        message = f"""📊 OPEN INTEREST ANALYSIS - {symbol}

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {total_oi_tokens:,.0f} {symbol} (${total_oi_usd/1e6:.1f}M)
• Stablecoin-Margined: ${stablecoin_usd/1e6:.1f}M | {stablecoin_pct:.1f}%
• Coin-Margined (Inverse): ${inverse_usd/1e6:.1f}M | {inverse_pct:.1f}%

📈 TOP MARKETS:"""
        
        # Add each market
        for i, market in enumerate(all_markets, 1):
            message += f"\n{i}. {market['name']}: {market['oi_tokens']:,.0f} {symbol} (${market['oi_usd']/1e6:.1f}M) | {market['percentage']:.1f}% {market['category']}"
            message += f"\n   Funding: {market['funding']*100:+.4f}% | Vol: {market['volume']:,.0f} {symbol}"
        
        # Add footer
        message += f"""

🏢 COVERAGE SUMMARY:
• Exchanges: {len(exchange_breakdown)} working
• Markets: {len(all_markets)} total

🕐 {datetime.now().strftime('%H:%M:%S')} UTC"""
        
        return message
        
    except Exception as e:
        return f"❌ Error formatting OI analysis for {symbol}: {str(e)}"

# Get live API data
print("🔄 Getting live API data from http://localhost:8001/multi_oi...")
response = requests.post('http://localhost:8001/multi_oi', 
                        json={'base_symbol': 'BTC'},
                        headers={'Content-Type': 'application/json'})

if response.status_code == 200:
    api_data = response.json()
    if api_data.get('success'):
        data = api_data['data']
        
        print("\n📊 LIVE API RESPONSE DATA:")
        print("=" * 50)
        print(json.dumps(data, indent=2))
        
        print("\n" + "=" * 50)
        print("🤖 EXACT TELEGRAM BOT MESSAGE OUTPUT:")
        print("=" * 50)
        
        # Format using exact bot logic
        formatted_message = format_oi_analysis(data, 'BTC')
        print(formatted_message)
        
        print("\n" + "=" * 50)
        print("✅ PROOF: This is the EXACT message a user would see in Telegram when typing `/oi BTC`")
        
    else:
        print(f"❌ API returned error: {api_data}")
else:
    print(f"❌ HTTP error {response.status_code}: {response.text}")