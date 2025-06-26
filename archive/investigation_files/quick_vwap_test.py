#!/usr/bin/env python3
"""Quick VWAP test to check current issue"""

import requests

def quick_test():
    try:
        response = requests.post('http://localhost:8001/comprehensive_analysis', 
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'})
        data = response.json()
        
        if data['success']:
            tech = data['data']['technical_indicators']
            price_data = data['data']['price_data']
            
            current_price = price_data['current_price']
            vwap = tech['vwap']
            
            print(f"Current BTC Price: ${current_price:,.2f}")
            print(f"VWAP (15m): ${vwap:,.2f}")
            print(f"Price > VWAP: {current_price > vwap}")
            print(f"Difference: ${current_price - vwap:,.2f}")
            
            if current_price > vwap:
                print("Should display: 'Above VWAP ✅'")
            else:
                print("Should display: 'Below VWAP ❌'")
        else:
            print(f"Error: {data['error']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    quick_test()