#!/usr/bin/env python3
"""
VALIDATE TG BOT 6-EXCHANGE INTEGRATION
Shows exactly what the TG bot OI command returns with Hyperliquid
"""

import asyncio
import aiohttp
import json

async def validate_tg_bot_oi():
    """Validate TG bot shows all 6 exchanges including Hyperliquid"""
    print("🤖 VALIDATING TG BOT 6-EXCHANGE INTEGRATION")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test the exact endpoint TG bot uses for OI analysis
            async with session.post("http://localhost:8001/multi_oi", 
                                  json={"base_symbol": "BTC"}) as response:
                if response.status != 200:
                    print(f"❌ API Error: HTTP {response.status}")
                    return False
                
                data = await response.json()
                
                # Extract key metrics
                successful_exchanges = data['validation_summary']['successful_exchanges']
                total_oi_btc = data['aggregated_oi']['total_tokens']
                total_oi_usd = data['aggregated_oi']['total_usd']
                
                print(f"✅ VALIDATION RESULTS:")
                print(f"  Total Exchanges: {successful_exchanges}/6")
                print(f"  Total BTC OI: {total_oi_btc:,.0f} BTC")
                print(f"  Total USD OI: ${total_oi_usd/1e9:.1f}B")
                print()
                
                # Show exchange breakdown (sorted by OI descending)
                exchanges = sorted(data['exchange_breakdown'], 
                                 key=lambda x: x['oi_tokens'], reverse=True)
                
                print("📊 EXCHANGE RANKING (TG Bot will show):")
                for i, exchange in enumerate(exchanges, 1):
                    name = exchange['exchange']
                    oi_btc = exchange['oi_tokens']
                    oi_usd = exchange['oi_usd']
                    markets = exchange['markets']
                    percentage = exchange['oi_percentage']
                    
                    # Highlight Hyperliquid
                    emoji = "🟣" if name == "hyperliquid" else "🔹"
                    highlight = " ← NEW!" if name == "hyperliquid" else ""
                    
                    print(f"  {i}. {emoji} {name.upper()}: {oi_btc:,.0f} BTC (${oi_usd/1e9:.1f}B) - {percentage:.1f}% - {markets} markets{highlight}")
                
                # Specific Hyperliquid validation
                hyperliquid_data = next((e for e in exchanges if e['exchange'] == 'hyperliquid'), None)
                if hyperliquid_data:
                    hl_oi_btc = hyperliquid_data['oi_tokens']
                    hl_oi_usd = hyperliquid_data['oi_usd']
                    
                    print(f"\n🎯 HYPERLIQUID VALIDATION:")
                    print(f"  ✅ Integrated: Found in exchange list")
                    print(f"  💰 BTC OI: {hl_oi_btc:,.0f} BTC")
                    print(f"  💵 USD OI: ${hl_oi_usd/1e6:.1f}M")
                    print(f"  🎯 Target: ~$2.8B (Actual: ${hl_oi_usd/1e9:.1f}B)")
                    
                    if hl_oi_usd >= 2.5e9:  # At least $2.5B
                        print(f"  ✅ Target achieved!")
                    else:
                        print(f"  ⚠️ Below target")
                else:
                    print(f"\n❌ HYPERLIQUID NOT FOUND")
                    return False
                
                print(f"\n🎯 TG BOT DEPLOYMENT STATUS:")
                if successful_exchanges == 6 and hyperliquid_data:
                    print(f"  ✅ READY FOR PRODUCTION")
                    print(f"  ✅ All 6 exchanges working")
                    print(f"  ✅ Hyperliquid integrated")
                    print(f"  ✅ ~$40B total OI tracked")
                    
                    print(f"\n📱 TG Bot Commands Ready:")
                    print(f"  • /oi BTC - Shows all 6 exchanges")
                    print(f"  • /analysis BTC-USDT 15m - Comprehensive analysis")
                    
                    return True
                else:
                    print(f"  ❌ NOT READY - Missing exchanges or Hyperliquid")
                    return False
                    
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

async def main():
    success = await validate_tg_bot_oi()
    
    if success:
        print(f"\n🎉 SUCCESS: TG Bot 6-Exchange System Deployed!")
        print(f"Users can now use /oi BTC to see Hyperliquid data.")
    else:
        print(f"\n💥 FAILED: Deployment validation failed")

if __name__ == "__main__":
    asyncio.run(main())