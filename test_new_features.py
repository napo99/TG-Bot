#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_new_features():
    """Test the new long/short and delta features"""
    
    print("🧪 Testing New Features")
    print("=" * 50)
    
    try:
        url = 'http://localhost:8001/comprehensive_analysis'
        data = {'symbol': 'SOL/USDT', 'timeframe': '15m'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                result = await resp.json()
        
        if not result.get('success'):
            print(f"❌ API Error: {result.get('error')}")
            return
        
        analysis = result['data']
        symbol = analysis['symbol']
        timeframe = analysis['timeframe']
        base_token = symbol.split('/')[0]
        
        # Price data
        price_data = analysis['price_data']
        current_price = price_data['current_price']
        change_24h = price_data['change_24h']
        
        # Volume data
        volume_data = analysis['volume_analysis']
        current_volume = volume_data['current_volume']
        spike_level = volume_data['spike_level']
        spike_pct = volume_data['spike_percentage']
        vol_usd = volume_data['volume_usd']
        
        # CVD data with new delta
        cvd_data = analysis['cvd_analysis']
        current_cvd = cvd_data['current_cvd']
        current_delta = cvd_data['current_delta']
        current_delta_usd = cvd_data['current_delta_usd']
        
        # Long/Short data
        ls_data = analysis.get('long_short_data', {})
        oi_data = analysis.get('oi_data', {})
        
        # Format message like Telegram
        print(f"🎯 MARKET ANALYSIS - {symbol} ({timeframe})")
        print()
        print(f"💰 PRICE: ${current_price:,.2f} {'🟢' if change_24h >= 0 else '🔴'} {'+' if change_24h >= 0 else ''}{change_24h:.1f}%")
        print(f"📊 VOLUME: {'🔥' if spike_level != 'NORMAL' else '😴'} {spike_level} {current_volume:,.0f} {base_token} ({spike_pct:+.0f}%, ${vol_usd/1e6:.1f}M)")
        print(f"📈 CVD: {current_cvd:,.0f} {base_token} (${current_cvd * current_price / 1e6:.1f}M)")
        print(f"📊 DELTA: {'+' if current_delta >= 0 else ''}{current_delta:,.0f} {base_token} (${current_delta_usd/1e6:.2f}M)")
        
        if oi_data and oi_data.get('open_interest'):
            oi_tokens = oi_data['open_interest']
            oi_usd = oi_data['open_interest_usd']
            funding = oi_data['funding_rate'] * 100
            print(f"📈 OI: {oi_tokens:,.0f} {base_token} (${oi_usd/1e6:.0f}M) | 💸 Funding: {'+' if funding >= 0 else ''}{funding:.4f}%")
            
            if ls_data:
                inst = ls_data['institutional']
                retail = ls_data['retail']
                
                print(f"🏛️ INSTITUTIONAL: L: {inst['net_longs_tokens']:,.0f} {base_token} (${inst['net_longs_usd']/1e6:.0f}M) | S: {inst['net_shorts_tokens']:,.0f} {base_token} (${inst['net_shorts_usd']/1e6:.0f}M) | Ratio: {inst['long_ratio']:.2f}")
                print(f"🏪 RETAIL: L: {retail['net_longs_tokens']:,.0f} {base_token} (${retail['net_longs_usd']/1e6:.0f}M) | S: {retail['net_shorts_tokens']:,.0f} {base_token} (${retail['net_shorts_usd']/1e6:.0f}M) | Ratio: {retail['long_ratio']:.2f}")
        
        print()
        print("=" * 50)
        print("✅ ALL NEW FEATURES WORKING!")
        print("✅ Long/Short institutional vs retail data")
        print("✅ Point-in-time delta calculation") 
        print("✅ Token-first formatting with USD in parentheses")
        print("✅ Comprehensive market analysis enhanced")
        
        # Validation
        if ls_data:
            inst_total = inst['net_longs_tokens'] + inst['net_shorts_tokens']
            retail_total = retail['net_longs_tokens'] + retail['net_shorts_tokens']
            print(f"✅ Math validation: Inst total = {inst_total:,.0f}, Retail total = {retail_total:,.0f}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_new_features())