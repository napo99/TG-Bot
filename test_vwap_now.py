#!/usr/bin/env python3
"""Quick test of current VWAP values"""

import ccxt
import requests

def test_manual_vwap():
    print("🧪 TESTING VWAP VALUES")
    print("=" * 40)
    
    # Manual calculation with new periods
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # Old method (what was causing the issue)
    print("❌ OLD METHOD (15m × 100 = 25 hours):")
    ohlcv_old = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    total_pv_old = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv_old)
    total_volume_old = sum(v for _, _, _, _, _, v in ohlcv_old)
    old_vwap = total_pv_old / total_volume_old
    print(f"   VWAP: ${old_vwap:,.2f}")
    
    # New method (the fix)
    print("\n✅ NEW METHOD (15m × 24 = 6 hours):")
    ohlcv_new = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=24)
    total_pv_new = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv_new)
    total_volume_new = sum(v for _, _, _, _, _, v in ohlcv_new)
    new_vwap = total_pv_new / total_volume_new
    print(f"   VWAP: ${new_vwap:,.2f}")
    
    # Get current price
    ticker = exchange.fetch_ticker('BTC/USDT')
    current_price = ticker['last']
    print(f"   Current Price: ${current_price:,.2f}")
    
    # Trading app comparison
    user_app_vwap = 104812
    old_diff = abs(old_vwap - user_app_vwap)
    new_diff = abs(new_vwap - user_app_vwap)
    
    print(f"\n📊 COMPARISON:")
    print(f"   Trading App VWAP: ${user_app_vwap:,.2f}")
    print(f"   Old Diff: ${old_diff:,.2f}")
    print(f"   New Diff: ${new_diff:,.2f}")
    print(f"   Improvement: ${old_diff - new_diff:,.2f} closer!")
    
    # Test API if running
    print(f"\n🔍 API TEST:")
    try:
        response = requests.post('http://localhost:8001/comprehensive_analysis',
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
                               timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                api_vwap = data['data']['technical_indicators']['vwap']
                print(f"   API VWAP: ${api_vwap:,.2f}")
                if abs(api_vwap - old_vwap) < 10:
                    print("   ❌ SERVICE NOT RESTARTED - Still using old calculation!")
                elif abs(api_vwap - new_vwap) < 10:
                    print("   ✅ SERVICE UPDATED - Using new calculation!")
                else:
                    print(f"   ⚠️ UNEXPECTED VALUE - Manual: ${new_vwap:,.2f}, API: ${api_vwap:,.2f}")
            else:
                print(f"   ❌ API Error: {data['error']}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Service not running: {e}")

if __name__ == "__main__":
    test_manual_vwap()