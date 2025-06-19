#!/usr/bin/env python3
"""
Debug VWAP Calculation Issue
Analyze the reported problem where VWAP comparison logic seems incorrect
"""

import requests
import json
from datetime import datetime

def test_vwap_issue():
    """Test the VWAP calculation and comparison logic"""
    
    print("🔍 VWAP Issue Analysis")
    print("=" * 50)
    
    # Test with different timeframes
    timeframes = ['15m', '1h', '4h']
    
    for timeframe in timeframes:
        print(f"\n📊 Testing {timeframe} timeframe:")
        print("-" * 30)
        
        try:
            # Get comprehensive analysis
            response = requests.post('http://localhost:8001/comprehensive_analysis', 
                                   json={'symbol': 'BTC/USDT', 'timeframe': timeframe})
            
            if response.status_code != 200:
                print(f"❌ HTTP Error: {response.status_code}")
                continue
                
            data = response.json()
            
            if not data['success']:
                print(f"❌ API Error: {data['error']}")
                continue
            
            # Extract key data
            tech = data['data']['technical_indicators']
            price_data = data['data']['price_data']
            
            current_price = price_data['current_price']
            vwap = tech['vwap']
            
            print(f"💰 Current BTC Price: ${current_price:,.2f}")
            print(f"📈 VWAP ({timeframe}): ${vwap:,.2f}")
            print(f"📊 Price - VWAP: ${current_price - vwap:,.2f}")
            
            # Test the comparison logic
            is_above_vwap = current_price > vwap
            print(f"🔍 Price > VWAP: {is_above_vwap}")
            
            if is_above_vwap:
                print(f"✅ Should show: 'Above VWAP ✅'")
            else:
                print(f"❌ Should show: 'Below VWAP ❌'")
            
            # User reported issue check
            user_btc_price = 104855
            user_vwap = 105216
            
            if timeframe == '15m':
                print(f"\n🚨 User Reported Issue:")
                print(f"   User BTC Price: ${user_btc_price:,.2f}")
                print(f"   User VWAP: ${user_vwap:,.2f}")
                print(f"   User Price > User VWAP: {user_btc_price > user_vwap}")
                print(f"   Expected message: 'Below VWAP ❌'")
                print(f"   But showed: 'Above VWAP ✅' (INCORRECT)")
                
                # Check if our current data matches the issue
                if current_price < vwap:
                    print(f"✅ Current data reproduces the issue pattern")
                else:
                    print(f"ℹ️  Current data shows different pattern")
        
        except Exception as e:
            print(f"❌ Error testing {timeframe}: {str(e)}")
    
    print(f"\n🔍 VWAP Calculation Analysis:")
    print("-" * 40)
    
    # Test raw VWAP calculation
    try:
        # Get raw OHLCV data to verify calculation
        import ccxt
        
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
        
        if len(ohlcv) >= 1:
            # Calculate VWAP manually
            total_pv = 0
            total_volume = 0
            
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                typical_price = (high + low + close) / 3
                pv = typical_price * volume
                total_pv += pv
                total_volume += volume
            
            manual_vwap = total_pv / total_volume if total_volume > 0 else 0
            current_price = ohlcv[-1][4]  # Last close price
            
            print(f"📊 Manual VWAP Calculation:")
            print(f"   Candles used: {len(ohlcv)}")
            print(f"   Manual VWAP: ${manual_vwap:,.2f}")
            print(f"   Last Close Price: ${current_price:,.2f}")
            print(f"   Manual Price > VWAP: {current_price > manual_vwap}")
            
            # Compare with API result
            api_response = requests.post('http://localhost:8001/comprehensive_analysis', 
                                       json={'symbol': 'BTC/USDT', 'timeframe': '15m'})
            if api_response.json()['success']:
                api_vwap = api_response.json()['data']['technical_indicators']['vwap']
                api_price = api_response.json()['data']['price_data']['current_price']
                
                print(f"\n📡 API VWAP Calculation:")
                print(f"   API VWAP: ${api_vwap:,.2f}")
                print(f"   API Price: ${api_price:,.2f}")
                print(f"   API Price > VWAP: {api_price > api_vwap}")
                
                print(f"\n🔍 Comparison:")
                print(f"   VWAP Difference: ${abs(manual_vwap - api_vwap):,.2f}")
                print(f"   Price Difference: ${abs(current_price - api_price):,.2f}")
                
                if abs(manual_vwap - api_vwap) > 10:
                    print(f"⚠️  VWAP calculation discrepancy detected!")
                if abs(current_price - api_price) > 10:
                    print(f"⚠️  Price discrepancy detected!")
    
    except Exception as e:
        print(f"❌ Error in manual calculation: {str(e)}")
    
    print(f"\n🎯 POTENTIAL ISSUES TO INVESTIGATE:")
    print("-" * 45)
    print("1. ✅ Timeframe: VWAP uses user-specified timeframe (15m, 1h, etc.)")
    print("2. ❓ Price Source: Check if VWAP uses different price than display price")
    print("3. ❓ Data Synchronization: API vs real-time price discrepancy")
    print("4. ❓ Exchange Differences: Spot vs Perp price comparison")
    print("5. ❓ Calculation Method: Typical price vs close price")
    print("6. ❓ Display Logic: Telegram bot formatting logic")

if __name__ == "__main__":
    test_vwap_issue()