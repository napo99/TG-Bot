#!/usr/bin/env python3
"""
Test to identify exactly where bot conflicts are coming from
"""
import requests
import time

def test_bot_activity(token, bot_name):
    """Check if a bot token is actively polling"""
    print(f"\n🧪 Testing {bot_name}")
    print(f"Token: {token[:10]}...")
    
    # Check recent updates
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        # Get recent updates (last 5 minutes)
        response = requests.get(url, params={'timeout': 1, 'limit': 1}, timeout=5)
        data = response.json()
        
        if data.get('ok'):
            updates = data.get('result', [])
            print(f"✅ Bot responding, recent updates: {len(updates)}")
            
            # Try to get updates again to see if there's a conflict
            response2 = requests.get(url, params={'timeout': 1, 'limit': 1}, timeout=5)
            data2 = response2.json()
            
            if data2.get('ok'):
                print(f"✅ Second request OK - no active polling conflict")
                return True
            else:
                print(f"❌ Second request failed: {data2.get('description', 'Unknown error')}")
                if "conflict" in str(data2.get('description', '')).lower():
                    print(f"🚨 CONFLICT DETECTED - Another instance is polling this bot!")
                return False
        else:
            print(f"❌ Bot error: {data.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def main():
    print("🔍 BOT CONFLICT DETECTION TEST")
    print("=" * 50)
    
    # Test development bot (should be running locally)
    dev_token = "7792214250:AAHEx5JAzQcVARJWJ7n2d4uD-kypuL_t_hw"
    dev_ok = test_bot_activity(dev_token, "Development Bot (@napo_assistant_bot)")
    
    # Test production bot (might have conflicts)
    prod_token = "8079723149:AAFGirYfAue-6yYTmaCQLw9cuZHImnhokE8"
    prod_ok = test_bot_activity(prod_token, "Production Bot (@napo_crypto_prod_bot)")
    
    print("\n" + "=" * 50)
    print("📋 CONFLICT ANALYSIS:")
    
    if dev_ok and prod_ok:
        print("✅ No conflicts detected - both bots polling independently")
    elif not dev_ok:
        print("⚠️ Development bot has issues (shouldn't happen)")
    elif not prod_ok:
        print("🚨 Production bot has conflicts!")
        print("   Possible sources:")
        print("   1. Multiple Fly.io machines polling same token")
        print("   2. Local environment accidentally using prod token")
        print("   3. Another instance somewhere else")
    
    print(f"\n🎯 CURRENT STATUS:")
    print(f"Local environment: {'✅ Clean' if dev_ok else '❌ Issues'}")
    print(f"Production bot: {'✅ Clean' if prod_ok else '❌ Conflicts'}")

if __name__ == "__main__":
    main()