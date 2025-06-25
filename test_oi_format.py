#!/usr/bin/env python3
"""Test the OI formatting fix"""

import requests
import json
from datetime import datetime

# Test the API response format
api_response = {
    "success": True,
    "data": {
        "symbol": "BTC",
        "timestamp": "2025-06-25T05:33:08.560730",
        "aggregated_oi": {
            "total_tokens": 2504617.502439915,
            "total_usd": 38893.128000000084,
            "vs_normal_pct": 0.0,
            "alert_level": "NORMAL"
        },
        "exchange_breakdown": [
            {
                "exchange": "okx",
                "oi_tokens": 2490629.800000008,
                "oi_usd": 24906.298000000083,
                "oi_percentage": 64.03778580113183,
                "funding_rate": 4.77039658027e-05,
                "volume_24h": 7591718.03,
                "volume_24h_usd": 75917.1803
            },
            {
                "exchange": "bybit",
                "oi_tokens": 13987.702439906836,
                "oi_usd": 13986.83,
                "oi_percentage": 35.96221419886817,
                "funding_rate": -7.62e-06,
                "volume_24h": 503202917.0,
                "volume_24h_usd": 4762.6828
            }
        ]
    }
}

def format_oi_analysis(data, symbol: str) -> str:
    """Format OI analysis with exact target output specification"""
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

# Test the formatting
result = format_oi_analysis(api_response['data'], 'BTC')
print("✅ FORMATTED OI ANALYSIS:")
print(result)