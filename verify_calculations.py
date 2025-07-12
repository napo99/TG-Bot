#!/usr/bin/env python3
"""
Quick verification script to check delta and OI calculations
"""
import asyncio
import json
import sys
sys.path.append('services/market-data')
from main import MarketDataService

async def verify_calculations():
    """Verify delta and OI calculations with raw data"""
    
    print("🔍 DELTA & OI CALCULATION VERIFICATION")
    print("="*50)
    
    service = MarketDataService()
    await service.initialize()
    
    # Get BTC data
    symbol = "BTC/USDT"
    
    try:
        # 1. Get comprehensive analysis (what TG bot uses)
        result = await service.handle_comprehensive_analysis_request(symbol, "15m")
        price_data = result['data']['price_data']
        
        print("📊 TELEGRAM BOT OUTPUT VALUES:")
        print(f"   Volume 15m: {price_data.get('volume_15m', 'N/A')} BTC")
        print(f"   Delta 15m: {price_data.get('delta_15m', 'N/A')} BTC")
        print(f"   Volume 24h: {price_data.get('volume_24h', 'N/A')} BTC")  
        print(f"   Delta 24h: {price_data.get('delta_24h', 'N/A')} BTC")
        print(f"   Current Price: ${price_data.get('current_price', 'N/A')}")
        print()
        
        # 2. Get raw candle data to verify calculations
        print("🔍 RAW DATA VERIFICATION:")
        
        # Get exchange data
        exchange_manager = service.exchange_manager
        spot_ex = exchange_manager.exchanges.get('binance')
        perp_ex = exchange_manager.exchanges.get('binance_futures')
        
        if spot_ex:
            print("\n📈 SPOT DATA:")
            spot_candles = await exchange_manager._fetch_15m_data(spot_ex, "BTC/USDT")
            if spot_candles and len(spot_candles) >= 1:
                last_candle = spot_candles[-1]
                print(f"   Last 15m Candle: Open=${last_candle[1]}, High=${last_candle[2]}, Low=${last_candle[3]}, Close=${last_candle[4]}, Volume={last_candle[5]} BTC")
                
                # Manual delta calculation for last candle
                open_price = float(last_candle[1])
                high_price = float(last_candle[2]) 
                low_price = float(last_candle[3])
                close_price = float(last_candle[4])
                volume = float(last_candle[5])
                
                if high_price != low_price:
                    close_position = (close_price - low_price) / (high_price - low_price)
                    buy_volume = volume * close_position
                    sell_volume = volume * (1 - close_position)
                    manual_delta = buy_volume - sell_volume
                    
                    print(f"   Manual Delta Calc:")
                    print(f"     Close Position in Range: {close_position:.3f} (0=bearish, 1=bullish)")
                    print(f"     Buy Volume: {buy_volume:.2f} BTC")
                    print(f"     Sell Volume: {sell_volume:.2f} BTC") 
                    print(f"     Delta: {manual_delta:.2f} BTC")
                    print(f"     ✓ Matches API: {abs(manual_delta - price_data.get('delta_15m', 0)) < 0.01}")
        
        if perp_ex:
            print("\n⚡ PERPETUALS DATA:")
            perp_candles = await exchange_manager._fetch_15m_data(perp_ex, "BTC/USDT:USDT")
            if perp_candles and len(perp_candles) >= 1:
                last_candle = perp_candles[-1]
                print(f"   Last 15m Candle: Open=${last_candle[1]}, High=${last_candle[2]}, Low=${last_candle[3]}, Close=${last_candle[4]}, Volume={last_candle[5]} BTC")
                
                # Manual delta calculation
                open_price = float(last_candle[1])
                high_price = float(last_candle[2])
                low_price = float(last_candle[3]) 
                close_price = float(last_candle[4])
                volume = float(last_candle[5])
                
                if high_price != low_price:
                    close_position = (close_price - low_price) / (high_price - low_price)
                    buy_volume = volume * close_position
                    sell_volume = volume * (1 - close_position)
                    manual_delta = buy_volume - sell_volume
                    
                    print(f"   Manual Delta Calc:")
                    print(f"     Close Position in Range: {close_position:.3f}")
                    print(f"     Buy Volume: {buy_volume:.2f} BTC") 
                    print(f"     Sell Volume: {sell_volume:.2f} BTC")
                    print(f"     Delta: {manual_delta:.2f} BTC")
        
        # 3. Check OI calculation logic
        print("\n📊 OI CALCULATION VERIFICATION:")
        oi_data = result['data'].get('oi_data', {})
        oi_24h = oi_data.get('open_interest', 'N/A')
        oi_15m = oi_data.get('open_interest_15m', 'N/A')
        
        print(f"   OI 24h: {oi_24h} BTC")
        print(f"   OI 15m: {oi_15m} BTC")
        
        if isinstance(oi_24h, (int, float)) and isinstance(oi_15m, (int, float)):
            ratio = oi_15m / oi_24h
            expected_ratio = 1/96  # 24h / 15m = 96 periods
            print(f"   OI Ratio: {ratio:.6f} (expected ~{expected_ratio:.6f})")
            print(f"   ✓ Reasonable: {0.0001 <= ratio <= 0.2}")
        
        print("\n🎯 VERIFICATION SUMMARY:")
        print("="*30)
        delta_15m = price_data.get('delta_15m', 0)
        volume_15m = price_data.get('volume_15m', 0)
        
        if volume_15m and delta_15m:
            print(f"✓ Delta ≠ Volume: {abs(delta_15m) != abs(volume_15m)} (Bug Fixed)")
            print(f"✓ Delta Range: {abs(delta_15m) < abs(volume_15m)} (Delta < Volume)")
            print(f"✓ Values: Delta={delta_15m:.2f}, Volume={volume_15m:.2f}")
        
        # 4. Quick cross-check with simple math
        print(f"\n🧮 QUICK MATH CHECK:")
        if volume_15m and delta_15m:
            buy_pct = (volume_15m + delta_15m) / (2 * volume_15m) if volume_15m > 0 else 0
            sell_pct = 1 - buy_pct
            print(f"   Implied Buy %: {buy_pct*100:.1f}%")
            print(f"   Implied Sell %: {sell_pct*100:.1f}%") 
            print(f"   ✓ Reasonable: {0.3 <= buy_pct <= 0.7}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_calculations())