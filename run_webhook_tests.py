#!/usr/bin/env python3
"""
Manual webhook test execution
"""
import subprocess
import sys
import os

def run_webhook_tests():
    """Run webhook tests manually"""
    
    os.chdir('/Users/screener-m3/projects/crypto-assistant')
    
    # Test 1: Set HTTP webhook
    print("=== Test 1: Attempting to set HTTP webhook ===")
    cmd1 = [
        'curl', '-X', 'POST',
        'https://api.telegram.org/bot8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8/setWebhook',
        '-d', 'url=http://13.239.14.166:8080/webhook'
    ]
    
    try:
        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=30)
        print(f"Exit code: {result1.returncode}")
        print(f"Output: {result1.stdout}")
        if result1.stderr:
            print(f"Error: {result1.stderr}")
    except Exception as e:
        print(f"Error running test 1: {e}")
    
    print("\n=== Test 2: Testing webhook endpoint reachability ===")
    cmd2 = [
        'curl', '-X', 'POST',
        'http://13.239.14.166:8080/webhook',
        '-H', 'Content-Type: application/json',
        '-d', '{"test": "webhook_reachability"}'
    ]
    
    try:
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
        print(f"Exit code: {result2.returncode}")
        print(f"Output: {result2.stdout}")
        if result2.stderr:
            print(f"Error: {result2.stderr}")
    except Exception as e:
        print(f"Error running test 2: {e}")
    
    print("\n=== Test 3: Checking current webhook status ===")
    cmd3 = [
        'curl', '-s',
        'https://api.telegram.org/bot8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8/getWebhookInfo'
    ]
    
    try:
        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
        print(f"Exit code: {result3.returncode}")
        print(f"Output: {result3.stdout}")
        if result3.stderr:
            print(f"Error: {result3.stderr}")
    except Exception as e:
        print(f"Error running test 3: {e}")

if __name__ == "__main__":
    run_webhook_tests()