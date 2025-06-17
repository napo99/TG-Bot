#!/usr/bin/env python3
"""
Comprehensive Validation Test for Crypto Trading Assistant
Tests all endpoints and validates data accuracy
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any
import sys

BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint: str, payload: Dict[str, Any], description: str) -> Dict[str, Any]:
    """Test a single endpoint"""
    print(f"Testing {description}...")
    try:
        response = requests.post(f"{BASE_URL}/{endpoint}", json=payload, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ {description} - SUCCESS")
            return result
        else:
            print(f"❌ {description} - FAILED: {result.get('error', 'Unknown error')}")
            return result
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return {'success': False, 'error': str(e)}

def validate_price_data(price_data: Dict[str, Any], symbol: str) -> bool:
    """Validate price data accuracy"""
    price = price_data.get('price', 0)
    volume_24h = price_data.get('volume_24h', 0)
    
    print(f"  📊 {symbol}: ${price:,.2f}, Volume: {volume_24h:,.0f}")
    
    # Basic validation
    if price <= 0:
        print(f"  ❌ Invalid price: {price}")
        return False
    
    if volume_24h < 0:
        print(f"  ❌ Invalid volume: {volume_24h}")
        return False
    
    # BTC price sanity check
    if symbol.startswith('BTC') and (price < 20000 or price > 200000):
        print(f"  ⚠️  BTC price seems unusual: ${price:,.2f}")
    
    # ETH price sanity check  
    if symbol.startswith('ETH') and (price < 500 or price > 10000):
        print(f"  ⚠️  ETH price seems unusual: ${price:,.2f}")
    
    return True

def validate_volume_analysis(vol_data: Dict[str, Any], symbol: str) -> bool:
    """Validate volume analysis data"""
    current_vol = vol_data.get('current_volume', 0)
    avg_vol = vol_data.get('average_volume', 0)
    vol_usd = vol_data.get('volume_usd', 0)
    spike_pct = vol_data.get('spike_percentage', 0)
    
    print(f"  📊 Volume: {current_vol:,.0f}, Avg: {avg_vol:,.0f}, USD: ${vol_usd/1e6:.1f}M, Spike: {spike_pct:+.0f}%")
    
    # Basic validation
    if current_vol < 0 or avg_vol < 0:
        print(f"  ❌ Invalid volume values")
        return False
    
    if vol_usd < 0:
        print(f"  ❌ Invalid USD volume: {vol_usd}")
        return False
    
    # Spike percentage validation
    expected_spike = ((current_vol / avg_vol) - 1) * 100 if avg_vol > 0 else 0
    if abs(spike_pct - expected_spike) > 1:  # Allow 1% tolerance
        print(f"  ⚠️  Spike calculation seems off: {spike_pct:.1f}% vs expected {expected_spike:.1f}%")
    
    return True

def validate_cvd_analysis(cvd_data: Dict[str, Any], symbol: str) -> bool:
    """Validate CVD analysis data"""
    current_cvd = cvd_data.get('current_cvd', 0)
    cvd_change = cvd_data.get('cvd_change_24h', 0)
    cvd_trend = cvd_data.get('cvd_trend', 'NEUTRAL')
    
    print(f"  📈 CVD: {current_cvd:,.0f}, Change: {cvd_change:+,.0f}, Trend: {cvd_trend}")
    
    # Basic validation
    if cvd_trend not in ['BULLISH', 'BEARISH', 'NEUTRAL']:
        print(f"  ❌ Invalid CVD trend: {cvd_trend}")
        return False
    
    return True

def main():
    """Run comprehensive validation tests"""
    print("🚀 Starting Crypto Trading Assistant Validation Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Basic Price Data
    print("\n1. PRICE DATA VALIDATION")
    print("-" * 30)
    
    symbols_to_test = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    for symbol in symbols_to_test:
        tests_total += 1
        result = test_endpoint('price', {'symbol': symbol}, f"Price for {symbol}")
        if result.get('success'):
            if validate_price_data(result['data'], symbol):
                tests_passed += 1
    
    # Test 2: Volume Analysis
    print("\n2. VOLUME ANALYSIS VALIDATION")
    print("-" * 30)
    
    for symbol in symbols_to_test[:2]:  # Test fewer symbols for volume
        tests_total += 1
        result = test_endpoint('volume_spike', {
            'symbol': symbol, 
            'timeframe': '15m'
        }, f"Volume analysis for {symbol}")
        if result.get('success'):
            if validate_volume_analysis(result['data'], symbol):
                tests_passed += 1
    
    # Test 3: CVD Analysis
    print("\n3. CVD ANALYSIS VALIDATION")
    print("-" * 30)
    
    tests_total += 1
    result = test_endpoint('cvd', {
        'symbol': 'BTC/USDT', 
        'timeframe': '15m'
    }, "CVD analysis for BTC/USDT")
    if result.get('success'):
        if validate_cvd_analysis(result['data'], 'BTC/USDT'):
            tests_passed += 1
    
    # Test 4: Volume Scanning
    print("\n4. VOLUME SCANNING VALIDATION")
    print("-" * 30)
    
    tests_total += 1
    result = test_endpoint('volume_scan', {
        'timeframe': '15m', 
        'min_spike': 200
    }, "Volume spike scanning")
    if result.get('success'):
        spikes = result['data']['spikes']
        print(f"  📊 Found {len(spikes)} volume spikes > 200%")
        for spike in spikes[:3]:  # Show top 3
            print(f"  🔥 {spike['symbol']}: +{spike['spike_percentage']:.0f}% (${spike['volume_usd']/1e6:.1f}M)")
        tests_passed += 1
    
    # Test 5: Top Symbols (Critical Fix)
    print("\n5. TOP SYMBOLS VALIDATION (Critical Fix)")
    print("-" * 30)
    
    for market_type in ['spot', 'perp']:
        tests_total += 1
        result = test_endpoint('top_symbols', {
            'market_type': market_type, 
            'limit': 5
        }, f"Top 5 {market_type} symbols")
        if result.get('success'):
            symbols = result['data']['symbols']
            print(f"  📊 Top {market_type} symbols:")
            for i, sym in enumerate(symbols[:3], 1):
                symbol = sym['symbol']
                price = sym['price']
                volume = sym.get('volume_24h', 0)
                print(f"  {i}. {symbol}: ${price:,.2f}, Vol: {volume:,.0f}")
            tests_passed += 1
    
    # Test 6: Comprehensive Analysis
    print("\n6. COMPREHENSIVE ANALYSIS VALIDATION")
    print("-" * 30)
    
    tests_total += 1
    result = test_endpoint('comprehensive_analysis', {
        'symbol': 'BTC/USDT', 
        'timeframe': '15m'
    }, "Comprehensive analysis for BTC/USDT")
    if result.get('success'):
        data = result['data']
        print(f"  💰 Price: ${data['price_data']['current_price']:,.2f}")
        print(f"  📊 Volume: ${data['volume_analysis']['volume_usd']/1e6:.1f}M")
        print(f"  📈 CVD: {data['cvd_analysis']['current_cvd']:,.0f}")
        print(f"  🎯 RSI: {data['technical_indicators']['rsi_14']:.1f}")
        print(f"  🎮 Market Control: {data['market_sentiment']['market_control']}")
        tests_passed += 1
    
    # Final Results
    print("\n" + "=" * 60)
    print("🎯 VALIDATION RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 ALL TESTS PASSED! System is ready for production.")
        return 0
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Review issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)