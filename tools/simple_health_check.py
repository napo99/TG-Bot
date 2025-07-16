#!/usr/bin/env python3
"""
Simple Health Check - Combined dashboard for crypto-assistant
Integrates API testing, exchange monitoring, and basic system checks
"""

import time
from datetime import datetime
from api_tester import SimpleAPITester
from exchange_monitor import ExchangeMonitor

class SimpleHealthDashboard:
    """Combined health monitoring - minimal and practical"""
    
    def __init__(self):
        self.api_tester = SimpleAPITester()
        self.exchange_monitor = ExchangeMonitor()
    
    def run_complete_check(self, production=False):
        """Run all health checks"""
        print("🔍 CRYPTO-ASSISTANT HEALTH CHECK")
        print("=" * 40)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test APIs
        if production:
            api_results = self.api_tester.test_production()
        else:
            api_results = self.api_tester.test_core_endpoints()
        
        # Test exchanges
        exchange_results = self.exchange_monitor.test_all_exchanges()
        
        # Summary
        api_working = sum(1 for r in api_results.values() if r.get("status") == "ok")
        api_total = len(api_results)
        
        exchange_working = sum(1 for r in exchange_results.values() if r.get("status") == "ok")
        exchange_total = len(exchange_results)
        
        print(f"\n📊 SUMMARY")
        print("-" * 20)
        print(f"APIs: {api_working}/{api_total} working")
        print(f"Exchanges: {exchange_working}/{exchange_total} working")
        
        # Overall status
        if api_working == api_total and exchange_working == exchange_total:
            print("🟢 Overall Status: HEALTHY")
        elif api_working > 0:
            print("🟡 Overall Status: DEGRADED")
        else:
            print("🔴 Overall Status: CRITICAL")
        
        # Combined fixes
        all_fixes = []
        
        if api_working < api_total:
            api_fixes = self.api_tester.quick_fixes(api_results)
            all_fixes.extend(api_fixes)
        
        if exchange_working < exchange_total:
            exchange_fixes = self.exchange_monitor.get_issues(exchange_results)
            all_fixes.extend(exchange_fixes)
        
        if all_fixes:
            print(f"\n🔧 ACTION ITEMS")
            print("-" * 20)
            for fix in all_fixes:
                print(f"  {fix}")
        
        return {
            "api_results": api_results,
            "exchange_results": exchange_results,
            "api_status": f"{api_working}/{api_total}",
            "exchange_status": f"{exchange_working}/{exchange_total}",
            "fixes": all_fixes
        }
    
    def quick_test(self, production=False):
        """Super quick test - just essentials"""
        print("⚡ Quick Health Test")
        
        # Test just health endpoint
        if production:
            health_result = self.api_tester.test_endpoint(f"{self.api_tester.prod_url}/health")
        else:
            health_result = self.api_tester.test_endpoint(f"{self.api_tester.local_url}/health")
        
        # Test just one exchange
        binance_result = self.exchange_monitor.test_exchange("binance", self.exchange_monitor.exchanges["binance"])
        
        api_ok = health_result.get("status") == "ok"
        exchange_ok = binance_result.get("status") == "ok"
        
        if api_ok and exchange_ok:
            print("✅ System appears healthy")
        elif api_ok:
            print("⚠️ API working, exchange issues")
        elif exchange_ok:
            print("⚠️ Exchange working, API issues")
        else:
            print("❌ Multiple issues detected")
        
        return {"api_ok": api_ok, "exchange_ok": exchange_ok}

def main():
    """CLI interface"""
    import sys
    
    dashboard = SimpleHealthDashboard()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--production":
            dashboard.run_complete_check(production=True)
        elif sys.argv[1] == "--quick":
            dashboard.quick_test()
        elif sys.argv[1] == "--prod-quick":
            dashboard.quick_test(production=True)
        else:
            print("Usage: python simple_health_check.py [--production|--quick|--prod-quick]")
    else:
        dashboard.run_complete_check()

if __name__ == "__main__":
    main()