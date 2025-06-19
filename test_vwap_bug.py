#!/usr/bin/env python3
"""Test VWAP bug - isolate the exact issue"""

import requests
import json

def test_vwap_logic_bug():
    """Test the exact VWAP comparison issue"""
    
    print("🔍 TESTING VWAP LOGIC BUG")
    print("=" * 40)
    
    # Test the comprehensive analysis endpoint directly
    try:
        payload = {
            'symbol': 'BTC/USDT',
            'timeframe': '15m'
        }
        
        print(f"📡 Sending request: {json.dumps(payload, indent=2)}")
        
        response = requests.post('http://localhost:8001/comprehensive_analysis', 
                               json=payload, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        
        if not data['success']:
            print(f"❌ API Error: {data['error']}")
            return
        
        # Extract the key data
        tech_indicators = data['data']['technical_indicators']
        price_data = data['data']['price_data']
        
        current_price = price_data['current_price']
        vwap = tech_indicators['vwap']
        
        print(f"\n💰 EXTRACTED DATA:")
        print(f"   Current Price: ${current_price:,.2f}")
        print(f"   VWAP: ${vwap:,.2f}")
        print(f"   Difference: ${current_price - vwap:,.2f}")
        
        # Test the comparison logic (same as telegram bot)
        is_above_vwap = current_price > vwap
        
        print(f"\n🔍 LOGIC TEST:")
        print(f"   current_price > vwap: {current_price} > {vwap} = {is_above_vwap}")
        
        if is_above_vwap:
            expected_message = "Above VWAP ✅"
        else:
            expected_message = "Below VWAP ❌"
        
        print(f"   Expected message: '{expected_message}'")
        
        # User's reported values
        user_price = 105076
        user_vwap = 105184.70
        user_logic = user_price > user_vwap
        
        print(f"\n👤 USER'S REPORTED DATA:")
        print(f"   User Price: ${user_price:,.2f}")
        print(f"   User VWAP: ${user_vwap:,.2f}")
        print(f"   User Logic: {user_price} > {user_vwap} = {user_logic}")
        print(f"   User Expected: 'Below VWAP ❌'")
        print(f"   User Saw: 'Above VWAP ✅' (WRONG!)")
        
        # Check if our data matches user's pattern
        if abs(current_price - user_price) < 1000 and abs(vwap - user_vwap) < 1000:
            print(f"\n✅ DATA PATTERN MATCHES USER'S REPORT")
            if is_above_vwap != user_logic:
                print(f"🚨 LOGIC DISCREPANCY CONFIRMED!")
            else:
                print(f"ℹ️  Logic is consistent")
        else:
            print(f"\n📊 Different data than user's report")
        
        # Test if there might be a data type issue
        print(f"\n🔍 DATA TYPE CHECK:")
        print(f"   current_price type: {type(current_price)}")
        print(f"   vwap type: {type(vwap)}")
        print(f"   Both are numeric: {isinstance(current_price, (int, float)) and isinstance(vwap, (int, float))}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_symbol_parsing():
    """Test if there's a symbol/timeframe parsing issue"""
    
    print(f"\n🔍 TESTING SYMBOL PARSING")
    print("=" * 30)
    
    # Test different formats
    test_cases = [
        {'symbol': 'BTC/USDT', 'timeframe': '15m'},
        {'symbol': 'BTC-USDT', 'timeframe': '15m'},
        {'symbol': 'btc/usdt', 'timeframe': '15m'},
        {'symbol': 'btc-usdt', 'timeframe': '15m'},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case}")
        
        try:
            response = requests.post('http://localhost:8001/comprehensive_analysis', 
                                   json=test_case, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    symbol_result = data['data']['symbol']
                    timeframe_result = data['data']['timeframe']
                    print(f"   ✅ Success - Symbol: {symbol_result}, Timeframe: {timeframe_result}")
                else:
                    print(f"   ❌ API Error: {data['error']}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_vwap_logic_bug()
    test_symbol_parsing()