#!/usr/bin/env python3
"""Quick test of VWAP periods to compare with trading apps"""

import ccxt

def test_vwap_periods():
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # Your specified periods
    periods = {
        '1m': 60,      # 1 hour
        '5m': 96,      # 8 hours  
        '15m': 48,     # 12 hours
        '1h': 24,      # 24 hours
        '4h': 6,       # 24 hours
        '1d': 1        # 1 day
    }
    
    print("📊 VWAP COMPARISON - Option 3 Periods")
    print("=" * 45)
    
    user_trading_app_vwap = 104812
    print(f"🎯 Target (Trading App VWAP): ${user_trading_app_vwap:,.2f}")
    print()
    
    results = []
    
    for timeframe, limit in periods.items():
        try:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe, limit=limit)
            
            # Calculate VWAP
            total_pv = 0
            total_volume = 0
            
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                typical_price = (high + low + close) / 3
                pv = typical_price * volume
                total_pv += pv
                total_volume += volume
            
            vwap = total_pv / total_volume if total_volume > 0 else 0
            current_price = ohlcv[-1][4]
            
            # Calculate duration
            if timeframe == '1m':
                duration_hours = limit / 60
            elif timeframe == '5m':
                duration_hours = limit * 5 / 60
            elif timeframe == '15m':
                duration_hours = limit * 15 / 60
            elif timeframe == '1h':
                duration_hours = limit
            elif timeframe == '4h':
                duration_hours = limit * 4
            elif timeframe == '1d':
                duration_hours = limit * 24
            
            diff = abs(vwap - user_trading_app_vwap)
            percentage_diff = (diff / user_trading_app_vwap) * 100
            
            results.append({
                'timeframe': timeframe,
                'limit': limit,
                'duration_hours': duration_hours,
                'vwap': vwap,
                'diff': diff,
                'percentage_diff': percentage_diff
            })
            
            match_quality = "🎯" if diff < 50 else "✅" if diff < 200 else "⚠️" if diff < 500 else "❌"
            
            print(f"{match_quality} {timeframe} × {limit} = {duration_hours:.1f}h")
            print(f"   VWAP: ${vwap:,.2f}")
            print(f"   Diff: ${diff:,.2f} ({percentage_diff:.2f}%)")
            print()
            
        except Exception as e:
            print(f"❌ {timeframe}: Error - {e}")
    
    # Find best match
    if results:
        best_match = min(results, key=lambda x: x['diff'])
        print(f"🏆 BEST MATCH:")
        print(f"   {best_match['timeframe']} × {best_match['limit']} = {best_match['duration_hours']:.1f}h")
        print(f"   VWAP: ${best_match['vwap']:,.2f}")
        print(f"   Only ${best_match['diff']:,.2f} difference!")
    
    # Additional test - current system
    print(f"\n📊 CURRENT SYSTEM (15m × 100 = 25h):")
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
        total_pv = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv)
        total_volume = sum(v for _, _, _, _, _, v in ohlcv)
        current_vwap = total_pv / total_volume
        current_diff = abs(current_vwap - user_trading_app_vwap)
        
        print(f"   Current VWAP: ${current_vwap:,.2f}")
        print(f"   Difference: ${current_diff:,.2f}")
        print(f"   Status: {'❌ Too high' if current_diff > 200 else '✅ Acceptable'}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_vwap_periods()