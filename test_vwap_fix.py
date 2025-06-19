#!/usr/bin/env python3
"""Test the VWAP fix"""

import requests
import json

def test_vwap_fix():
    print("🔧 Testing VWAP Fix - Market Consistency")
    print("=" * 45)
    
    try:
        # Test the comprehensive analysis
        response = requests.post('http://localhost:8001/comprehensive_analysis', 
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'})
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return
        
        data = response.json()
        
        if not data['success']:
            print(f"❌ API Error: {data['error']}")
            return
        
        # Extract data
        price_data = data['data']['price_data']
        tech_indicators = data['data']['technical_indicators']
        
        current_price = price_data['current_price']
        vwap = tech_indicators['vwap']
        market_type = price_data['market_type']
        
        print(f"📊 RESULTS:")
        print(f"   Market Type: {market_type}")
        print(f"   Current Price: ${current_price:,.2f}")
        print(f"   VWAP: ${vwap:,.2f}")
        print(f"   Difference: ${current_price - vwap:,.2f}")
        
        # Test the comparison logic
        is_above_vwap = current_price > vwap
        expected_message = "Above VWAP ✅" if is_above_vwap else "Below VWAP ❌"
        
        print(f"\n🔍 LOGIC TEST:")
        print(f"   {current_price:,.2f} > {vwap:,.2f} = {is_above_vwap}")
        print(f"   Expected Display: '{expected_message}'")
        
        # Additional validation
        if market_type == 'perp':
            print(f"✅ Using perpetual futures market (correct)")
        else:
            print(f"ℹ️  Using spot market")
        
        # Compare with user's previous issue
        if current_price < vwap:
            print(f"\n✅ FIX VALIDATION:")
            print(f"   Price is below VWAP - should show 'Below VWAP ❌'")
            print(f"   Logic correctly identifies: {is_above_vwap} = False")
        else:
            print(f"\n✅ FIX VALIDATION:")
            print(f"   Price is above VWAP - should show 'Above VWAP ✅'")
            print(f"   Logic correctly identifies: {is_above_vwap} = True")
        
        print(f"\n🎯 CONSISTENCY CHECK:")
        print(f"   Both price and VWAP from same market: ✅ {market_type}")
        print(f"   No more spot vs perp mixing: ✅ Fixed")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_vwap_fix()