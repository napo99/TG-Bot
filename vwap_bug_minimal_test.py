#!/usr/bin/env python3
"""Minimal test to confirm VWAP logic bug"""

import requests

# Test the exact user scenario
payload = {'symbol': 'BTC/USDT', 'timeframe': '15m'}
response = requests.post('http://localhost:8001/comprehensive_analysis', json=payload)

if response.json()['success']:
    data = response.json()['data']
    current_price = data['price_data']['current_price']
    vwap = data['technical_indicators']['vwap']
    
    print(f"Current Price: ${current_price:,.2f}")
    print(f"VWAP: ${vwap:,.2f}")
    print(f"Price > VWAP: {current_price > vwap}")
    
    # This is the exact logic from telegram bot main.py:751
    vwap_status = "Above VWAP ✅" if current_price > vwap else "Below VWAP ❌"
    print(f"Should display: '{vwap_status}'")
    
    # Check user's reported issue
    if current_price < vwap:
        print(f"BUG CONFIRMED: Price is below VWAP but logic might be wrong")
    else:
        print(f"No bug in current data")
else:
    print(f"Error: {response.json()['error']}")