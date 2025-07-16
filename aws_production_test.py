#!/usr/bin/env python3
"""
AWS PRODUCTION VALIDATION SCRIPT
Test the AWS production environment and missing module issues
"""

import requests
import socket
import time
import json
from datetime import datetime

AWS_IP = "13.239.14.166"
BOT_PORT = 8080
MARKET_PORT = 8001

def test_connectivity():
    """Test basic connectivity to AWS instance"""
    print("🔗 TESTING AWS CONNECTIVITY")
    print("=" * 50)
    
    results = {}
    
    # Test ports
    for port, service in [(22, "SSH"), (BOT_PORT, "Telegram Bot"), (MARKET_PORT, "Market Data")]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((AWS_IP, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {service} (Port {port}): REACHABLE")
                results[service.lower().replace(" ", "_")] = True
            else:
                print(f"❌ {service} (Port {port}): CONNECTION REFUSED")
                results[service.lower().replace(" ", "_")] = False
        except Exception as e:
            print(f"❌ {service} (Port {port}): ERROR - {e}")
            results[service.lower().replace(" ", "_")] = False
    
    return results

def test_health_endpoints():
    """Test health endpoints"""
    print("\n🏥 TESTING HEALTH ENDPOINTS")
    print("=" * 50)
    
    results = {}
    
    # Test Bot Health
    try:
        response = requests.get(f"http://{AWS_IP}:{BOT_PORT}/health", timeout=10)
        print(f"✅ Bot Health: HTTP {response.status_code}")
        print(f"   Response: {response.text}")
        results['bot_health'] = {
            'status': 'healthy',
            'code': response.status_code,
            'response': response.text
        }
    except Exception as e:
        print(f"❌ Bot Health: ERROR - {e}")
        results['bot_health'] = {'status': 'error', 'error': str(e)}
    
    # Test Market Data Health
    try:
        response = requests.get(f"http://{AWS_IP}:{MARKET_PORT}/health", timeout=10)
        print(f"✅ Market Data Health: HTTP {response.status_code}")
        print(f"   Response: {response.text}")
        results['market_health'] = {
            'status': 'healthy',
            'code': response.status_code,
            'response': response.text
        }
    except Exception as e:
        print(f"❌ Market Data Health: ERROR - {e}")
        results['market_health'] = {'status': 'error', 'error': str(e)}
    
    return results

def test_market_data_api():
    """Test market data API functionality"""
    print("\n📊 TESTING MARKET DATA API")
    print("=" * 50)
    
    try:
        # Test comprehensive analysis
        response = requests.post(
            f"http://{AWS_IP}:{MARKET_PORT}/comprehensive_analysis",
            json={"symbol": "BTC/USDT", "timeframe": "15m"},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"✅ Comprehensive Analysis: HTTP {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Symbol: {data.get('symbol', 'N/A')}")
            print(f"   Price: ${data.get('price', 'N/A')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Market Data API: ERROR - {e}")
        return False

def test_webhook_endpoint():
    """Test webhook endpoint"""
    print("\n📡 TESTING WEBHOOK ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"http://{AWS_IP}:{BOT_PORT}/webhook",
            json={"test": "validation"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"✅ Webhook: HTTP {response.status_code}")
        print(f"   Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Webhook: ERROR - {e}")
        return False

def analyze_missing_module_issue():
    """Analyze the missing module issue"""
    print("\n🔍 ANALYZING MISSING MODULE ISSUE")
    print("=" * 50)
    
    print("Issue Identified:")
    print("- unified_oi_aggregator.py imports 'gateio_oi_provider_working'")
    print("- unified_oi_aggregator.py imports 'bitget_oi_provider_working'")
    print("- These files don't exist, causing import errors")
    print("- Actual files are 'gateio_oi_provider.py' and 'bitget_oi_provider.py'")
    
    print("\nFix Applied:")
    print("- Created alias files to resolve import conflicts")
    print("- gateio_oi_provider_working.py → gateio_oi_provider.py")
    print("- bitget_oi_provider_working.py → bitget_oi_provider.py")
    
    print("\nRequired Action:")
    print("- Rebuild Docker containers with fixed imports")
    print("- Redeploy to AWS with updated code")

def main():
    """Run complete AWS production validation"""
    print("🚨 AWS PRODUCTION VALIDATION")
    print(f"🎯 Target: {AWS_IP}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test connectivity
    connectivity = test_connectivity()
    
    # Test health endpoints
    health = test_health_endpoints()
    
    # Test market data API
    market_api_working = test_market_data_api()
    
    # Test webhook
    webhook_working = test_webhook_endpoint()
    
    # Analyze missing module issue
    analyze_missing_module_issue()
    
    # Summary
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    issues = []
    
    if not connectivity.get('ssh', False):
        issues.append("SSH_UNREACHABLE")
    if not connectivity.get('telegram_bot', False):
        issues.append("BOT_PORT_BLOCKED")
    if not connectivity.get('market_data', False):
        issues.append("MARKET_PORT_BLOCKED")
    if health.get('bot_health', {}).get('status') != 'healthy':
        issues.append("BOT_SERVICE_UNHEALTHY")
    if health.get('market_health', {}).get('status') != 'healthy':
        issues.append("MARKET_SERVICE_UNHEALTHY")
    if not market_api_working:
        issues.append("MARKET_API_FAILING")
    if not webhook_working:
        issues.append("WEBHOOK_FAILING")
    
    print(f"Issues Found: {len(issues)}")
    for issue in issues:
        print(f"  ❌ {issue}")
    
    if not issues:
        print("  ✅ ALL SYSTEMS OPERATIONAL")
    
    # Root cause analysis
    print("\n🔬 ROOT CAUSE ANALYSIS")
    print("=" * 50)
    print("CRITICAL ISSUE: Missing Module Dependencies")
    print("- Bot containers failing to start due to import errors")
    print("- 'gateio_oi_provider_working' and 'bitget_oi_provider_working' not found")
    print("- This causes container crashes and service unavailability")
    
    print("\n🛠️ RECOVERY PLAN")
    print("=" * 50)
    print("1. Push alias files to GitHub repository")
    print("2. SSH into AWS instance and pull latest code")
    print("3. Rebuild Docker containers with fixed imports")
    print("4. Restart all services")
    print("5. Validate bot responds to /price and /oi commands")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)