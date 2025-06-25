#!/usr/bin/env python3
"""Test fixed Binance provider"""

import asyncio
from binance_oi_provider import BinanceOIProvider

async def test_fixed_binance():
    provider = BinanceOIProvider()
    try:
        print("🧪 Testing Fixed Binance Provider")
        result = await provider.get_oi_data('BTC')
        
        print(f'✅ SUCCESS: {len(result.markets)} markets')
        for market in result.markets:
            print(f'  {market.market_type.value}: {market.oi_tokens:,.0f} BTC (${market.oi_usd/1e9:.1f}B)')
        print(f'🎯 Total: {result.total_oi_tokens:,.0f} BTC (${result.total_oi_usd/1e9:.1f}B)')
        
        return result
        
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
        return None
    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(test_fixed_binance())