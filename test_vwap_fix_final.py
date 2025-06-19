#!/usr/bin/env python3
"""Test the final VWAP fix with 15m × 24 = 6 hours"""

import requests
import ccxt

def test_vwap_fix():
    print("🔧 TESTING VWAP FIX - 15m × 24 (6 hours)")
    print("=" * 45)
    
    user_trading_app_vwap = 104812
    print(f"🎯 Target (Trading App): ${user_trading_app_vwap:,.2f}")
    print()
    
    try:
        # Test manual calculation first
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=24)
        
        total_pv = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv)
        total_volume = sum(v for _, _, _, _, _, v in ohlcv)
        manual_vwap = total_pv / total_volume
        manual_diff = abs(manual_vwap - user_trading_app_vwap)
        
        print(f"📊 MANUAL CALCULATION (15m × 24):")
        print(f"   VWAP: ${manual_vwap:,.2f}")
        print(f"   Difference: ${manual_diff:,.2f}")
        print(f"   Match: {'🎯 EXCELLENT' if manual_diff < 50 else '✅ GOOD' if manual_diff < 200 else '⚠️ MODERATE'}")
        print()
        
        # Test via API
        response = requests.post('http://localhost:8001/comprehensive_analysis', 
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'})
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                api_vwap = data['data']['technical_indicators']['vwap']
                current_price = data['data']['price_data']['current_price']
                api_diff = abs(api_vwap - user_trading_app_vwap)
                
                print(f"📡 API RESULT (After Fix):")
                print(f"   Current Price: ${current_price:,.2f}")
                print(f"   VWAP: ${api_vwap:,.2f}")
                print(f"   Difference from trading app: ${api_diff:,.2f}")
                
                # Test the comparison logic
                is_above_vwap = current_price > api_vwap
                expected_message = "Above VWAP ✅" if is_above_vwap else "Below VWAP ❌"
                
                print(f"   Price vs VWAP: {current_price:,.2f} {'>' if is_above_vwap else '<'} {api_vwap:,.2f}")
                print(f"   Display: '{expected_message}'")
                print(f"   Logic: {'✅ CORRECT' if abs(api_diff) < 200 else '⚠️ CHECK'}")
                
                # Compare manual vs API
                api_manual_diff = abs(api_vwap - manual_vwap)
                print(f"\n🔍 CONSISTENCY CHECK:")
                print(f"   Manual VWAP: ${manual_vwap:,.2f}")
                print(f"   API VWAP: ${api_vwap:,.2f}")
                print(f"   Difference: ${api_manual_diff:,.2f}")
                print(f"   Consistency: {'✅ MATCH' if api_manual_diff < 10 else '⚠️ SLIGHT DIFF' if api_manual_diff < 100 else '❌ MISMATCH'}")
                
            else:
                print(f"❌ API Error: {data['error']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def compare_before_after():
    print(f"\n📊 BEFORE vs AFTER COMPARISON:")
    print("-" * 35)
    
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        
        # Old method (15m × 100 = 25 hours)
        ohlcv_old = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
        total_pv_old = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv_old)
        total_volume_old = sum(v for _, _, _, _, _, v in ohlcv_old)
        old_vwap = total_pv_old / total_volume_old
        
        # New method (15m × 24 = 6 hours)
        ohlcv_new = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=24)
        total_pv_new = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv_new)
        total_volume_new = sum(v for _, _, _, _, _, v in ohlcv_new)
        new_vwap = total_pv_new / total_volume_new
        
        user_app_vwap = 104812
        
        print(f"❌ OLD (15m × 100 = 25h): ${old_vwap:,.2f}")
        print(f"   Diff from trading app: ${abs(old_vwap - user_app_vwap):,.2f}")
        print()
        print(f"✅ NEW (15m × 24 = 6h):  ${new_vwap:,.2f}")
        print(f"   Diff from trading app: ${abs(new_vwap - user_app_vwap):,.2f}")
        print()
        print(f"🎯 IMPROVEMENT: ${abs(old_vwap - user_app_vwap) - abs(new_vwap - user_app_vwap):,.2f} closer!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_vwap_fix()
    compare_before_after()