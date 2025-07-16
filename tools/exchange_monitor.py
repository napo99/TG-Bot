#!/usr/bin/env python3
"""
Exchange Monitor - Simple connectivity test for external APIs
Lightweight check for exchange APIs used by crypto-assistant
"""

import requests
import time

class ExchangeMonitor:
    """Simple exchange connectivity testing"""
    
    def __init__(self):
        # Core exchanges with simple test endpoints
        self.exchanges = {
            "binance": "https://api.binance.com/api/v3/ping",
            "bybit": "https://api.bybit.com/v2/public/time", 
            "okx": "https://www.okx.com/api/v5/public/time",
            "kucoin": "https://api.kucoin.com/api/v1/timestamp"
        }
    
    def test_exchange(self, name, url):
        """Test single exchange connectivity"""
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            time_ms = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                return {"status": "ok", "time_ms": time_ms}
            else:
                return {"status": "failed", "code": response.status_code}
                
        except requests.exceptions.ConnectionError:
            return {"status": "down", "error": "Connection failed"}
        except requests.exceptions.Timeout:
            return {"status": "slow", "error": "Timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def test_all_exchanges(self):
        """Test all exchange connections"""
        print("🌐 Testing Exchange APIs")
        results = {}
        
        for name, url in self.exchanges.items():
            result = self.test_exchange(name, url)
            icon = self._status_icon(result)
            time_info = f" {result.get('time_ms', '?')}ms" if result.get('time_ms') else ""
            print(f"  {name}: {icon}{time_info}")
            results[name] = result
            
        return results
    
    def get_issues(self, results):
        """Simple issue reporting"""
        issues = []
        
        down_exchanges = [name for name, r in results.items() if r.get("status") == "down"]
        if down_exchanges:
            issues.append(f"❌ Exchanges down: {', '.join(down_exchanges)}")
            issues.append("→ Check internet connection")
        
        slow_exchanges = [name for name, r in results.items() if r.get("status") == "slow"]
        if slow_exchanges:
            issues.append(f"⏰ Slow exchanges: {', '.join(slow_exchanges)}")
            issues.append("→ Exchange may be under maintenance")
        
        if not issues:
            issues.append("✅ All exchanges responding normally")
            
        return issues
    
    def _status_icon(self, result):
        """Simple status icon"""
        status = result.get("status", "error")
        return {"ok": "✅", "failed": "❌", "down": "🔌", "slow": "⏰", "error": "🚨"}.get(status, "❓")

def main():
    """Simple CLI"""
    monitor = ExchangeMonitor()
    results = monitor.test_all_exchanges()
    
    # Summary
    working = sum(1 for r in results.values() if r.get("status") == "ok")
    total = len(results)
    print(f"\n📊 Result: {working}/{total} exchanges reachable")
    
    # Issues
    if working < total:
        issues = monitor.get_issues(results)
        print("\n🔧 Issues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ All exchange APIs operational")

if __name__ == "__main__":
    main()