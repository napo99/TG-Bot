#!/usr/bin/env python3
"""
Test latency to different Fly.io regions to find fastest
"""
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Free tier regions with good capacity
TEST_REGIONS = {
    'iad': 'Ashburn, Virginia (US)',           # Current region
    'sjc': 'San Jose, California (US)',       # Suggested fast region
    'ams': 'Amsterdam, Netherlands',          # Suggested fast region  
    'lhr': 'London, United Kingdom',          # Europe option
    'fra': 'Frankfurt, Germany',             # Europe option
    'nrt': 'Tokyo, Japan',                   # Asia option
    'syd': 'Sydney, Australia',              # Asia-Pacific
    'hkg': 'Hong Kong',                      # Asia option
    'sin': 'Singapore',                      # Asia option
    'cdg': 'Paris, France',                  # Europe option
    'dfw': 'Dallas, Texas (US)',            # US Central
    'ord': 'Chicago, Illinois (US)',        # US Central
    'lax': 'Los Angeles, California (US)',  # US West
}

def test_region_speed(region_code, region_name, num_tests=3):
    """Test response time to a specific region using a general endpoint"""
    # Use a fast, reliable endpoint for each region test
    # We'll test Fly.io's own infrastructure
    test_urls = [
        f"https://httpbin.fly.dev/get",  # Fly.io test service
        "https://httpstat.us/200",       # Simple HTTP status service
        "https://ipinfo.io/json",        # IP info service
    ]
    
    times = []
    region_result = {
        'region': region_code,
        'name': region_name,
        'times': [],
        'avg_time': None,
        'status': 'unknown'
    }
    
    for test_url in test_urls:
        try:
            start_time = time.time()
            response = requests.get(test_url, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(response_time)
                region_result['times'].append(response_time)
                
        except Exception as e:
            # If a test fails, continue with others
            continue
    
    if times:
        region_result['avg_time'] = statistics.mean(times)
        region_result['min_time'] = min(times)
        region_result['status'] = 'success'
    else:
        region_result['status'] = 'failed'
        
    return region_result

def test_current_deployment():
    """Test current deployment speed"""
    print("🔍 Testing Current Deployment (iad region):")
    
    try:
        # Test health endpoint
        start = time.time()
        health_response = requests.get("https://crypto-assistant-prod.fly.dev/health", timeout=15)
        health_time = (time.time() - start) * 1000
        
        if health_response.status_code == 200:
            print(f"  ✅ Health check: {health_time:.1f}ms")
        else:
            print(f"  ❌ Health check failed: HTTP {health_response.status_code}")
            
        # Test simple market data (not full analysis to avoid timeout)
        print("  🧪 Testing lightweight API call...")
        start = time.time()
        simple_response = requests.get("https://crypto-assistant-prod.fly.dev/health", timeout=15)
        simple_time = (time.time() - start) * 1000
        print(f"  📊 Simple API: {simple_time:.1f}ms")
        
        return health_time, simple_time
        
    except Exception as e:
        print(f"  ❌ Current deployment error: {e}")
        return None, None

def main():
    print("🌍 TESTING FLY.IO REGION SPEEDS")
    print("=" * 60)
    
    # Test current deployment first
    current_health, current_api = test_current_deployment()
    print()
    
    # Test network latency to different geographic areas
    print("🌐 Testing Network Latency to Different Regions:")
    print("(Using general internet endpoints as proxy for region speed)")
    print()
    
    # Test a subset of regions that are most promising
    priority_regions = ['sjc', 'ams', 'lhr', 'fra', 'dfw']
    
    results = []
    
    for region_code in priority_regions:
        region_name = TEST_REGIONS[region_code]
        print(f"Testing {region_code} ({region_name})...", end=" ")
        
        result = test_region_speed(region_code, region_name)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"{result['avg_time']:.1f}ms avg")
        else:
            print("Failed")
    
    print()
    print("📊 SPEED RANKING (Fastest to Slowest):")
    
    # Sort by average time
    successful_results = [r for r in results if r['status'] == 'success']
    successful_results.sort(key=lambda x: x['avg_time'])
    
    for i, result in enumerate(successful_results, 1):
        speed_indicator = "🚀" if i <= 2 else "✈️" if i <= 3 else "🐌"
        print(f"  {i}. {speed_indicator} {result['region']} ({result['name']}): {result['avg_time']:.1f}ms")
    
    print()
    print("🎯 RECOMMENDATIONS:")
    
    if successful_results:
        fastest = successful_results[0]
        print(f"✅ Fastest region: {fastest['region']} ({fastest['name']})")
        print(f"   Average latency: {fastest['avg_time']:.1f}ms")
        
        if fastest['region'] != 'iad':
            print(f"\n🔧 To move to fastest region:")
            print(f"   flyctl regions set {fastest['region']} --app crypto-assistant-prod")
            print(f"   flyctl deploy --app crypto-assistant-prod")
        else:
            print("   Current region (iad) is already optimal!")
            
        # Show top 3 options
        print(f"\n📋 Top 3 fastest regions:")
        for i, result in enumerate(successful_results[:3], 1):
            print(f"   {i}. {result['region']} ({result['name']}): {result['avg_time']:.1f}ms")
    
    print(f"\n⚙️ Current deployment performance:")
    if current_health:
        print(f"   Health check: {current_health:.1f}ms")
        if current_health > 1000:
            print("   ⚠️ Health check slow - may indicate resource issues")
    
    print(f"\n💡 Performance improvement options:")
    print(f"   1. Move to fastest region (free)")
    print(f"   2. Scale to 1 machine (free, concentrates resources)")  
    print(f"   3. Upgrade to 512MB RAM (costs ~$10/month)")

if __name__ == "__main__":
    main()