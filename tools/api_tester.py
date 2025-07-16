#!/usr/bin/env python3
"""
Simple API Tester - Lightweight endpoint testing for crypto-assistant
Focus: Fast, practical, minimal resource usage
"""

import requests
import time

class SimpleAPITester:
    """Lightweight API testing - no bloat, just essentials"""
    
    def __init__(self):
        self.local_url = "http://localhost:8001"
        self.prod_url = "http://13.239.14.166:8001"
        
        # Essential endpoints only
        self.endpoints = {
            "health": "/health",
            "price": "/combined_price", 
            "oi": "/multi_oi",
            "analysis": "/comprehensive_analysis"
        }
    
    def test_endpoint(self, url, payload=None):
        """Test single endpoint - simple and fast"""
        start = time.time()
        try:
            if payload:
                response = requests.post(url, json=payload, timeout=10)
            else:
                response = requests.get(url, timeout=5)
            
            time_ms = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                return {"status": "ok", "time_ms": time_ms}
            else:
                return {"status": "failed", "code": response.status_code, "time_ms": time_ms}
                
        except requests.exceptions.ConnectionError:
            return {"status": "down", "error": "Connection failed"}
        except requests.exceptions.Timeout:
            return {"status": "slow", "error": "Timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def test_core_endpoints(self, base_url=None):
        """Test essential endpoints"""
        if not base_url:
            base_url = self.local_url
            
        print(f"🧪 Testing {base_url}")
        results = {}
        
        # Health check
        result = self.test_endpoint(f"{base_url}/health")
        print(f"  Health: {self._status_icon(result)} {result.get('time_ms', '?')}ms")
        results["health"] = result
        
        # Price endpoint
        result = self.test_endpoint(f"{base_url}/combined_price", {"symbol": "BTC-USDT"})
        print(f"  Price: {self._status_icon(result)} {result.get('time_ms', '?')}ms")
        results["price"] = result
        
        # OI endpoint  
        result = self.test_endpoint(f"{base_url}/multi_oi", {"symbol": "BTC-USDT"})
        print(f"  OI: {self._status_icon(result)} {result.get('time_ms', '?')}ms")
        results["oi"] = result
        
        # Analysis endpoint
        result = self.test_endpoint(f"{base_url}/comprehensive_analysis", 
                                  {"symbol": "BTC/USDT", "timeframe": "15m"})
        print(f"  Analysis: {self._status_icon(result)} {result.get('time_ms', '?')}ms")
        results["analysis"] = result
        
        return results
    
    def test_production(self):
        """Test AWS production"""
        print("☁️ Testing AWS Production")
        return self.test_core_endpoints(self.prod_url)
    
    def quick_fixes(self, results):
        """Simple fix suggestions"""
        fixes = []
        down_count = sum(1 for r in results.values() if r.get("status") == "down")
        
        if down_count > 0:
            fixes.append("❌ Services down → docker-compose restart")
            fixes.append("🔍 Check status → docker ps")
        
        slow_count = sum(1 for r in results.values() if r.get("status") == "slow")
        if slow_count > 0:
            fixes.append("⏰ Slow responses → Check external APIs")
            fixes.append("📊 Monitor resources → docker stats")
        
        failed_count = sum(1 for r in results.values() if r.get("status") == "failed")
        if failed_count > 0:
            fixes.append("❌ API errors → docker logs crypto-market-data")
        
        if not fixes:
            fixes.append("✅ All good - no issues detected")
            
        return fixes
    
    def _status_icon(self, result):
        """Simple status icon"""
        status = result.get("status", "error")
        return {"ok": "✅", "failed": "❌", "down": "🔌", "slow": "⏰", "error": "🚨"}.get(status, "❓")

def main():
    """Simple CLI - minimal options"""
    import sys
    
    tester = SimpleAPITester()
    
    # Simple argument handling
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        results = tester.test_production()
    else:
        results = tester.test_core_endpoints()
    
    # Show summary
    working = sum(1 for r in results.values() if r.get("status") == "ok")
    total = len(results)
    print(f"\n📊 Result: {working}/{total} endpoints working")
    
    # Show fixes if needed
    if working < total:
        fixes = tester.quick_fixes(results)
        print("\n🔧 Quick Fixes:")
        for fix in fixes:
            print(f"  {fix}")
    else:
        print("✅ All systems operational")

if __name__ == "__main__":
    main()