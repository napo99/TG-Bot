#!/usr/bin/env python3
"""Quick test for agents to validate their changes"""

import sys
import requests
import json
import time

def test_oi_analysis():
    """Test OI analysis endpoint"""
    try:
        start = time.time()
        response = requests.post(
            'http://localhost:8001/oi_analysis',
            json={'symbol': 'BTC'},
            timeout=15
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OI Analysis: Response in {duration:.1f}s")
            
            # Check for Bybit inverse data
            response_text = json.dumps(data)
            if 'bybit' in response_text.lower() and '"oi_tokens": 0' not in response_text:
                print("✅ Bybit Inverse: Data present")
            else:
                print("❌ Bybit Inverse: Still showing 0 or missing")
            
            return True
        else:
            print(f"❌ OI Analysis: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OI Analysis: {e}")
        return False

def test_analysis_regression():
    """Ensure sophisticated analysis still works"""
    try:
        start = time.time()
        response = requests.post(
            'http://localhost:8001/comprehensive_analysis',
            json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
            timeout=10
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Analysis Regression: Working in {duration:.1f}s")
                return True
        
        print("❌ Analysis Regression: Failed")
        return False
    except Exception as e:
        print(f"❌ Analysis Regression: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Quick Validation Tests...")
    
    oi_ok = test_oi_analysis()
    analysis_ok = test_analysis_regression()
    
    if oi_ok and analysis_ok:
        print("\n🎯 Quick Test: PASSED ✅")
        sys.exit(0)
    else:
        print("\n❌ Quick Test: FAILED")
        sys.exit(1)
