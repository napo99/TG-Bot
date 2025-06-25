#!/usr/bin/env python3
"""Test Unified OI System with Binance Provider"""

import asyncio
from oi_engine_v2 import OIEngineV2
from binance_oi_provider import BinanceOIProvider

async def test_unified_system():
    """Test the unified OI system with Binance provider"""
    print("🚀 Testing Unified OI System V2")
    
    # Create engine and register Binance provider
    engine = OIEngineV2()
    binance_provider = BinanceOIProvider()
    engine.register_provider(binance_provider)
    
    try:
        # Get comprehensive OI analysis
        print("\n📊 Running Comprehensive OI Analysis...")
        result = await engine.get_comprehensive_oi("BTC")
        
        # Display results
        print(f"\n✅ UNIFIED SYSTEM RESULTS:")
        print(f"Symbol: {result.base_symbol}")
        print(f"Total OI: {result.total_oi_tokens:,.0f} BTC (${result.total_oi_usd/1e9:.1f}B)")
        print(f"Exchanges Working: {result.exchanges_working}")
        print(f"Total Markets: {result.total_markets}")
        
        print(f"\n🔢 MARKET TYPE BREAKDOWN:")
        print(f"• Stablecoin-Margined: ${result.stablecoin_oi_usd/1e9:.1f}B ({result.stablecoin_percentage:.1f}%)")
        print(f"  - USDT: ${result.usdt_oi_usd/1e9:.1f}B ({result.usdt_percentage:.1f}%)")
        print(f"  - USDC: ${result.usdc_oi_usd/1e9:.1f}B ({result.usdc_percentage:.1f}%)")
        print(f"• Coin-Margined (Inverse): ${result.inverse_oi_usd/1e9:.1f}B ({result.inverse_percentage:.1f}%)")
        
        print(f"\n📈 TOP MARKETS:")
        for i, market in enumerate(result.top_markets, 1):
            market_type = "STABLE" if market.market_type.value in ["USDT", "USDC"] else "INVERSE"
            print(f"{i}. {market.exchange.title()} {market.market_type.value}: {market.oi_tokens:,.0f} BTC (${market.oi_usd/1e9:.1f}B) | {market.oi_usd/result.total_oi_usd*100:.1f}% {market_type}")
        
        # Test target output formatting
        print(f"\n📋 TARGET FORMAT OUTPUT:")
        print("=" * 80)
        formatted_output = engine.format_target_output(result)
        print(formatted_output)
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await engine.close_all()

if __name__ == "__main__":
    asyncio.run(test_unified_system())