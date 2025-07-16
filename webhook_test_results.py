#!/usr/bin/env python3
"""
Direct webhook test results - running the exact tests requested
"""

import requests
import json
from datetime import datetime

def run_tests():
    """Run the exact webhook tests requested"""
    
    TOKEN = "8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
    AWS_IP = "13.239.14.166"
    
    print("🔍 TELEGRAM WEBHOOK FEASIBILITY TESTS")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Token: {TOKEN}")
    print(f"AWS IP: {AWS_IP}")
    print("=" * 60)
    
    # Test 1: Set HTTP webhook
    print("\n=== Test 1: Attempting to set HTTP webhook ===")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        data = {"url": f"http://{AWS_IP}:8080/webhook"}
        response = requests.post(url, data=data, timeout=10)
        
        print(f"Request: POST {url}")
        print(f"Data: {data}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        webhook_result = response.json()
        test1_success = webhook_result.get('ok', False)
        
    except Exception as e:
        print(f"ERROR: {e}")
        test1_success = False
        webhook_result = None
    
    # Test 2: Check endpoint reachability
    print("\n=== Test 2: Testing webhook endpoint reachability ===")
    try:
        url = f"http://{AWS_IP}:8080/webhook"
        headers = {"Content-Type": "application/json"}
        data = {"test": "webhook_reachability"}
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Request: POST {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        test2_success = response.status_code == 200
        
    except Exception as e:
        print(f"ERROR: {e}")
        test2_success = False
    
    # Test 3: Get webhook info
    print("\n=== Test 3: Checking current webhook status ===")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        print(f"Request: GET {url}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        webhook_info = response.json()
        test3_success = webhook_info.get('ok', False)
        
    except Exception as e:
        print(f"ERROR: {e}")
        test3_success = False
        webhook_info = None
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Test 1 (HTTP webhook): {'✅ SUCCESS' if test1_success else '❌ FAILED'}")
    if webhook_result:
        if webhook_result.get('ok'):
            print("   → HTTP webhook ACCEPTED by Telegram")
        else:
            print("   → HTTP webhook REJECTED by Telegram")
            print(f"   → Error: {webhook_result.get('description', 'Unknown error')}")
    
    print(f"Test 2 (Endpoint reach): {'✅ SUCCESS' if test2_success else '❌ FAILED'}")
    print(f"Test 3 (Webhook info): {'✅ SUCCESS' if test3_success else '❌ FAILED'}")
    
    if webhook_info and webhook_info.get('ok'):
        current_url = webhook_info['result'].get('url', 'None')
        pending_updates = webhook_info['result'].get('pending_update_count', 0)
        print(f"Current webhook URL: {current_url}")
        print(f"Pending updates: {pending_updates}")
    
    print("\n🎯 FINAL CONCLUSION:")
    if webhook_result and not webhook_result.get('ok'):
        print("   → Telegram REQUIRES HTTPS webhooks (HTTP rejected)")
        print("   → Need SSL/TLS implementation")
    elif webhook_result and webhook_result.get('ok'):
        print("   → HTTP webhooks ACCEPTED (unexpected!)")
        print("   → Can proceed with current setup")
    else:
        print("   → Test inconclusive - check network/token")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    run_tests()