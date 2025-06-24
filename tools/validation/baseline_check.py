#!/usr/bin/env python3
"""Baseline validation - ensure system is healthy before development"""

import asyncio
import requests
import time

async def main():
    print("🔍 Running Baseline Validation...")
    
    # 1. Check market data service
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        assert response.status_code == 200
        print("✅ Market data service: HEALTHY")
    except:
        print("❌ Market data service: DOWN")
        return False
    
    # 2. Check current analysis works
    try:
        response = requests.post(
            'http://localhost:8001/comprehensive_analysis',
            json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        print("✅ Analysis command: WORKING")
    except Exception as e:
        print(f"❌ Analysis command: FAILED - {e}")
        return False
    
    # 3. Check Bybit inverse current status
    try:
        response = requests.post(
            'http://localhost:8001/oi_analysis',
            json={'symbol': 'BTC'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if 'bybit' in str(data).lower():
                print("✅ OI analysis: API responding")
            else:
                print("⚠️  OI analysis: API responding but no Bybit data")
        else:
            print("❌ OI analysis: API not working")
    except:
        print("❌ OI analysis: Service not available")
    
    print("\n🎯 Baseline validation complete!")
    return True

if __name__ == "__main__":
    asyncio.run(main())
