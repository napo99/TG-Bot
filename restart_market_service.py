#!/usr/bin/env python3
"""Restart market data service to apply VWAP fix"""

import subprocess
import time
import requests
import signal
import os

def restart_service():
    print("🔄 Restarting Market Data Service for VWAP Fix")
    print("=" * 50)
    
    # Kill existing service
    print("1. Stopping existing service...")
    try:
        subprocess.run(["pkill", "-f", "python.*main.py"], check=False)
        subprocess.run(["lsof", "-ti:8001"], stdout=subprocess.PIPE, text=True, check=False)
        result = subprocess.run(["lsof", "-ti:8001"], stdout=subprocess.PIPE, text=True, check=False)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"   Killed process {pid}")
                except:
                    pass
        time.sleep(3)
        print("   ✅ Service stopped")
    except Exception as e:
        print(f"   ⚠️ Stop error (may not be running): {e}")
    
    # Start new service
    print("2. Starting service with VWAP fix...")
    try:
        os.chdir("/Users/screener-m3/projects/crypto-assistant/services/market-data")
        
        # Start in background
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"   Started process PID: {process.pid}")
        time.sleep(5)
        
        # Test if service is running
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Service started successfully")
                return True
            else:
                print(f"   ❌ Service health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Service not responding: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Start error: {e}")
        return False

def test_vwap_fix():
    print("\n3. Testing VWAP fix...")
    try:
        response = requests.post('http://localhost:8001/comprehensive_analysis',
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                vwap = data['data']['technical_indicators']['vwap']
                current_price = data['data']['price_data']['current_price']
                
                print(f"   📊 New VWAP: ${vwap:,.2f}")
                print(f"   💰 Current Price: ${current_price:,.2f}")
                
                # Compare with target
                target_vwap = 104812
                diff = abs(vwap - target_vwap)
                
                if diff < 100:
                    print(f"   🎯 EXCELLENT! Only ${diff:,.2f} from trading app")
                elif diff < 300:
                    print(f"   ✅ GOOD! ${diff:,.2f} from trading app")
                else:
                    print(f"   ⚠️ Still ${diff:,.2f} from trading app")
                
                return True
            else:
                print(f"   ❌ API Error: {data['error']}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
    
    return False

if __name__ == "__main__":
    if restart_service():
        test_vwap_fix()
        print("\n🎉 Market Data Service restarted with VWAP fix!")
        print("Now test: /analysis btc-usdt 15m in Telegram")
    else:
        print("\n❌ Service restart failed. Please restart manually:")
        print("cd /Users/screener-m3/projects/crypto-assistant/services/market-data")
        print("python main.py")