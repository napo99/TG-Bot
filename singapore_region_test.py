#!/usr/bin/env python3
"""
Test Asia-Pacific regions specifically for Singapore user
"""
import requests
import time
import statistics

def test_region_latency(region_name, test_url="https://httpbin.org/get"):
    """Test latency to a region using simple HTTP request"""
    times = []
    
    for i in range(3):
        try:
            start = time.time()
            response = requests.get(test_url, timeout=10)
            end = time.time()
            
            if response.status_code == 200:
                times.append((end - start) * 1000)
        except:
            continue
    
    if times:
        return statistics.mean(times)
    return None

def main():
    print("🇸🇬 OPTIMAL REGIONS FOR SINGAPORE")
    print("=" * 40)
    
    # Test Asia-Pacific regions available on Fly.io free tier
    asia_regions = {
        'sin': 'Singapore 🇸🇬 (Closest to you!)',
        'hkg': 'Hong Kong 🇭🇰', 
        'nrt': 'Tokyo, Japan 🇯🇵',
        'syd': 'Sydney, Australia 🇦🇺',
        'dfw': 'Dallas, Texas 🇺🇸 (Good US option)',
        'sjc': 'San Jose, California 🇺🇸',
        'iad': 'Virginia, US 🇺🇸 (Current region)',
    }
    
    print("🧪 Testing network latency from your location...")
    print()
    
    results = []
    for region_code, region_name in asia_regions.items():
        print(f"Testing {region_code} ({region_name})...", end=" ")
        latency = test_region_latency(region_name)
        
        if latency:
            results.append((region_code, region_name, latency))
            print(f"{latency:.1f}ms")
        else:
            print("Failed")
    
    # Sort by latency
    results.sort(key=lambda x: x[2])
    
    print("\n🏆 BEST REGIONS FOR YOU (Singapore):")
    for i, (code, name, latency) in enumerate(results[:5], 1):
        icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        print(f"  {icon} {code}: {name} - {latency:.1f}ms")
    
    if results:
        best_region = results[0][0]
        print(f"\n✅ RECOMMENDED REGION: {best_region}")
        print(f"🔧 Command to switch:")
        print(f"   flyctl regions set {best_region} --app crypto-assistant-prod")
        print(f"   flyctl deploy --app crypto-assistant-prod")
        
        # Check if Singapore is available and best
        sin_result = next((r for r in results if r[0] == 'sin'), None)
        if sin_result:
            print(f"\n🎯 Singapore region latency: {sin_result[2]:.1f}ms")
            if sin_result[0] == best_region:
                print("🇸🇬 Perfect! Singapore is your best option!")
            else:
                print(f"🤔 Surprisingly, {best_region} might be faster than Singapore")

if __name__ == "__main__":
    main()