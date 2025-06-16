#!/usr/bin/env python3
"""
Integration test for volume analysis features
Tests volume spike detection, CVD calculation, and volume scanning
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_market_data_api():
    """Test the market data API endpoints"""
    print("🧪 Testing Volume Analysis Integration")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("\n1️⃣ Testing health endpoint...")
        async with session.get(f"{base_url}/health") as resp:
            health = await resp.json()
            print(f"✅ Health: {health}")
        
        # Test 2: Volume spike detection
        print("\n2️⃣ Testing volume spike detection...")
        async with session.post(f"{base_url}/volume_spike", json={
            "symbol": "BTC/USDT",
            "timeframe": "15m"
        }) as resp:
            volume_data = await resp.json()
            if volume_data['success']:
                data = volume_data['data']
                print(f"✅ Volume Spike Analysis for BTC/USDT:")
                print(f"   📊 Current Volume: {data['current_volume']:,.0f} BTC")
                print(f"   💰 USD Value: ${data['volume_usd']/1e6:.1f}M")
                print(f"   📈 Spike Level: {data['spike_level']}")
                print(f"   📊 Change: {data['spike_percentage']:+.1f}%")
                print(f"   🔍 Significant: {data['is_significant']}")
            else:
                print(f"❌ Volume spike test failed: {volume_data['error']}")
        
        # Test 3: CVD calculation - this might have issues
        print("\n3️⃣ Testing CVD calculation...")
        try:
            async with session.post(f"{base_url}/cvd", json={
                "symbol": "BTC/USDT", 
                "timeframe": "15m"
            }) as resp:
                if resp.status == 200:
                    cvd_data = await resp.json()
                    if cvd_data['success']:
                        data = cvd_data['data']
                        print(f"✅ CVD Analysis for BTC/USDT:")
                        print(f"   📈 Current CVD: {data['current_cvd']:,.0f}")
                        print(f"   📊 24h Change: {data['cvd_change_24h']:+.0f}")
                        print(f"   🔍 Trend: {data['cvd_trend']}")
                        print(f"   ⚠️ Divergence: {data['divergence_detected']}")
                    else:
                        print(f"❌ CVD test failed: {cvd_data['error']}")
                else:
                    error_text = await resp.text()
                    print(f"❌ CVD endpoint returned {resp.status}: {error_text}")
        except Exception as e:
            print(f"❌ CVD test exception: {e}")
        
        # Test 4: Volume scanning
        print("\n4️⃣ Testing volume scanning...")
        async with session.post(f"{base_url}/volume_scan", json={
            "timeframe": "15m",
            "min_spike": 150  # Lower threshold to find some results
        }) as resp:
            scan_data = await resp.json()
            if scan_data['success']:
                data = scan_data['data']
                print(f"✅ Volume Scan Results:")
                print(f"   🔍 Spikes Found: {data['spikes_found']}")
                print(f"   📊 Threshold: >{data['min_spike_threshold']}%")
                for i, spike in enumerate(data['spikes'][:3], 1):  # Show top 3
                    symbol = spike['symbol'].split('/')[0]
                    print(f"   {i}. {symbol}: +{spike['spike_percentage']:.0f}% (${spike['volume_usd']/1e6:.1f}M)")
            else:
                print(f"❌ Volume scan test failed: {scan_data['error']}")
        
        # Test 5: Top symbols to verify basic functionality still works
        print("\n5️⃣ Testing top symbols (perps)...")
        async with session.post(f"{base_url}/top_symbols", json={
            "market_type": "perp",
            "limit": 3
        }) as resp:
            top_data = await resp.json()
            if top_data['success']:
                symbols = top_data['data']['symbols']
                print(f"✅ Top 3 Perpetuals:")
                for i, symbol in enumerate(symbols, 1):
                    name = symbol['symbol'].split('/')[0].replace(':USDT', '')
                    volume_usd = symbol['volume_24h'] * symbol['price']
                    print(f"   {i}. {name}: ${symbol['price']:,.2f} (${volume_usd/1e6:.0f}M vol)")
            else:
                print(f"❌ Top symbols test failed: {top_data['error']}")
    
    print("\n" + "=" * 50)
    print("🎯 Integration Test Complete!")

async def test_data_accuracy():
    """Test volume data accuracy - token vs USD values"""
    print("\n🔍 Testing Data Accuracy (Token vs USD)")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        # Get combined price data for BTC
        async with session.post(f"{base_url}/combined_price", json={
            "symbol": "BTC/USDT"
        }) as resp:
            price_data = await resp.json()
            
            if price_data['success']:
                data = price_data['data']
                
                # Check spot data
                if 'spot' in data:
                    spot = data['spot']
                    price = spot['price']
                    volume_native = spot['volume_24h']
                    volume_usd = volume_native * price
                    
                    print(f"📊 BTC/USDT Spot Data Validation:")
                    print(f"   💰 Price: ${price:,.2f}")
                    print(f"   📊 Volume: {volume_native:,.2f} BTC")
                    print(f"   💵 Volume USD: ${volume_usd/1e6:.1f}M")
                    print(f"   🔍 Sanity Check: {volume_usd/1e6:.1f}M USD volume for BTC")
                    
                    # Sanity checks
                    if 90000 <= price <= 120000:
                        print("   ✅ Price range looks reasonable")
                    else:
                        print(f"   ⚠️ Price ${price:,.2f} seems unusual")
                    
                    if volume_usd/1e6 >= 100:  # At least $100M daily volume for BTC
                        print("   ✅ Volume looks reasonable for BTC")
                    else:
                        print(f"   ⚠️ Volume ${volume_usd/1e6:.1f}M seems low for BTC")
                
                # Check perp data
                if 'perp' in data:
                    perp = data['perp']
                    price = perp['price']
                    volume_native = perp['volume_24h']
                    volume_usd = volume_native * price
                    oi = perp.get('open_interest')
                    
                    print(f"\n📊 BTC/USDT Perp Data Validation:")
                    print(f"   💰 Price: ${price:,.2f}")
                    print(f"   📊 Volume: {volume_native:,.2f} BTC")
                    print(f"   💵 Volume USD: ${volume_usd/1e6:.1f}M")
                    if oi:
                        oi_usd = oi * price
                        print(f"   📈 OI: {oi:,.0f} BTC (${oi_usd/1e6:.0f}M)")

if __name__ == "__main__":
    print("🚀 Starting Volume Analysis Integration Tests")
    asyncio.run(test_market_data_api())
    asyncio.run(test_data_accuracy())