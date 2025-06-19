#!/usr/bin/env python3
import ccxt

exchange = ccxt.binance({'enableRateLimit': True})

periods = [
    ('1m', 60, '1 hour'),
    ('5m', 96, '8 hours'),  
    ('15m', 48, '12 hours'),
    ('1h', 24, '24 hours'),
    ('4h', 6, '24 hours'),
    ('15m', 100, '25 hours (current)'),
    ('15m', 96, '24 hours'),
    ('15m', 24, '6 hours'),
]

user_app_vwap = 104812
print(f"Target: ${user_app_vwap:,}")
print("="*40)

for timeframe, limit, desc in periods:
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe, limit=limit)
        total_pv = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv)
        total_volume = sum(v for _, _, _, _, _, v in ohlcv)
        vwap = total_pv / total_volume
        diff = abs(vwap - user_app_vwap)
        match = "🎯" if diff < 50 else "✅" if diff < 200 else "⚠️" if diff < 500 else "❌"
        print(f"{match} {timeframe}×{limit} ({desc}): ${vwap:,.0f} (${diff:,.0f} diff)")
    except Exception as e:
        print(f"❌ {timeframe}×{limit}: Error")