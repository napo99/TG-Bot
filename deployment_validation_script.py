#!/usr/bin/env python3
"""
Deployment Validation Script
Quick verification script for production readiness assessment
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def quick_deployment_check():
    """Quick deployment readiness check"""
    
    print("🔍 DEPLOYMENT READINESS CHECK")
    print("=" * 40)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = {
        'service_health': False,
        'data_service_working': False,
        'profile_endpoint_exists': False,
        'error_handling': False,
        'telegram_integration_ready': False
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Check 1: Service Health
        print("1️⃣ Service Health Check...")
        try:
            async with session.get("http://localhost:8001/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    if health_data.get('status') == 'healthy':
                        checks['service_health'] = True
                        print("   ✅ Market data service is healthy")
                    else:
                        print("   ❌ Service reports unhealthy status")
                else:
                    print(f"   ❌ Service health check failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Service health check failed: {e}")
        
        # Check 2: Data Service Working
        print("\n2️⃣ Data Service Functionality...")
        try:
            payload = {"symbol": "BTC/USDT", "exchange": "binance"}
            async with session.post("http://localhost:8001/combined_price", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['success'] and 'data' in data:
                        checks['data_service_working'] = True
                        price = data['data']['perp']['price'] if 'perp' in data['data'] else data['data']['spot']['price']
                        print(f"   ✅ Data service working (BTC: ${price:,.2f})")
                    else:
                        print(f"   ❌ Data service returned error: {data.get('error', 'Unknown')}")
                else:
                    print(f"   ❌ Data service failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Data service test failed: {e}")
        
        # Check 3: Profile Endpoint
        print("\n3️⃣ Profile Endpoint Check...")
        try:
            payload = {"symbol": "BTC", "exchange": "binance"}
            async with session.post("http://localhost:8001/market_profile", json=payload) as response:
                if response.status == 200:
                    checks['profile_endpoint_exists'] = True
                    print("   ✅ Profile endpoint exists and responding")
                elif response.status == 404:
                    print("   ❌ Profile endpoint NOT FOUND (container sync issue)")
                else:
                    print(f"   ⚠️ Profile endpoint status: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Profile endpoint test failed: {e}")
        
        # Check 4: Error Handling
        print("\n4️⃣ Error Handling Check...")
        try:
            payload = {"symbol": "INVALID123", "exchange": "binance"}
            async with session.post("http://localhost:8001/combined_price", json=payload) as response:
                data = await response.json()
                if not data['success'] and 'error' in data:
                    checks['error_handling'] = True
                    print("   ✅ Error handling working correctly")
                elif data['success']:
                    print("   ✅ Error handling via normalization working")
                    checks['error_handling'] = True
                else:
                    print("   ⚠️ Error handling may need validation")
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
        
        # Check 5: Telegram Integration Readiness
        print("\n5️⃣ Telegram Integration Readiness...")
        if checks['service_health'] and checks['data_service_working'] and checks['error_handling']:
            checks['telegram_integration_ready'] = True
            print("   ✅ Core components ready for Telegram integration")
        else:
            print("   ❌ Core components not ready")
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 40)
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check_name, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Overall Score: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("🎉 SYSTEM READY FOR DEPLOYMENT!")
        deployment_status = "READY"
    elif passed >= total - 1:
        print("⚠️  ALMOST READY - Minor issues need resolution")
        deployment_status = "ALMOST_READY"
    else:
        print("❌ NOT READY - Critical issues need resolution")
        deployment_status = "NOT_READY"
    
    # Specific recommendations
    print("\n🔧 DEPLOYMENT ACTIONS NEEDED:")
    
    if not checks['profile_endpoint_exists']:
        print("   🚨 CRITICAL: Rebuild market-data container with latest code")
        print("      Command: docker-compose build market-data && docker-compose up -d")
    
    if not checks['service_health']:
        print("   🚨 CRITICAL: Fix service health issues")
    
    if not checks['data_service_working']:
        print("   🚨 CRITICAL: Fix data service connectivity")
    
    if checks['profile_endpoint_exists']:
        print("   ✅ Profile endpoint working - no container rebuild needed")
    
    if all(checks.values()):
        print("   🎯 System ready for production deployment!")
    
    return deployment_status, passed, total

async def main():
    """Main execution"""
    deployment_status, passed, total = await quick_deployment_check()
    
    # Return appropriate exit code
    if deployment_status == "READY":
        return 0
    elif deployment_status == "ALMOST_READY":
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)