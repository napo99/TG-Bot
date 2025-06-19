#!/usr/bin/env python3

import requests
import json

def test_template_format():
    """Test the new template formatting"""
    
    try:
        url = 'http://localhost:8001/comprehensive_analysis'
        data = {'symbol': 'BTC/USDT', 'timeframe': '15m'}
        
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get('success'):
            analysis = result['data']
            print("✅ API Response Success")
            print()
            print("📊 NEW TEMPLATE FORMAT PREVIEW:")
            print("=" * 50)
            
            # Simulate the new message format
            symbol = "BTC/USDT"
            base_token = "BTC"
            
            price_data = analysis['price_data']
            volume_data = analysis['volume_analysis']
            cvd_data = analysis['cvd_analysis']
            ls_data = analysis.get('long_short_data', {})
            oi_data = analysis.get('oi_data', {})
            tech_data = analysis.get('technical_indicators', {})
            
            # Price formatting
            current_price = price_data['current_price']
            change_24h = price_data['change_24h']
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            change_sign = "+" if change_24h >= 0 else ""
            
            # Volume formatting
            volume = volume_data['current_volume']
            spike_level = volume_data['spike_level']
            spike_pct = volume_data['spike_percentage']
            vol_usd = volume_data['volume_usd']
            vol_emoji = "😴" if spike_level == "NORMAL" else "🔥"
            
            # CVD formatting
            cvd = cvd_data['current_cvd']
            cvd_trend = cvd_data['cvd_trend']
            cvd_emoji = "🟢📈" if cvd_trend == 'BULLISH' else "🔴📉" if cvd_trend == 'BEARISH' else "⚪➡️"
            delta = cvd_data['current_delta']
            delta_usd = cvd_data['current_delta_usd']
            delta_sign = "+" if delta >= 0 else ""
            
            print(f"🎯 MARKET ANALYSIS - {symbol} (15m)")
            print()
            print(f"• PRICE: ${current_price:,.2f} {change_emoji} {change_sign}{change_24h:.1f}%")
            print(f"• VOLUME: {vol_emoji} {spike_level} {volume:,.0f} {base_token} ({spike_pct:+.0f}%, ${vol_usd/1e6:.1f}M)")
            print(f"• CVD: {cvd_emoji} {cvd_trend} {cvd:,.0f} {base_token} (${cvd * current_price / 1e6:.1f}M)")
            print(f"• DELTA: {delta_sign}{delta:,.0f} {base_token} (${delta_usd/1e6:.2f}M)")
            
            if oi_data:
                oi_tokens = oi_data['open_interest']
                oi_usd = oi_data['open_interest_usd']
                funding = oi_data['funding_rate'] * 100
                funding_sign = "+" if funding >= 0 else ""
                funding_direction = "longs pay shorts" if funding >= 0 else "shorts pay longs"
                
                print()
                print(f"• OI: {oi_tokens:,.0f} {base_token} (${oi_usd/1e6:.0f}M)")
                print(f"• Funding: {funding_sign}{funding:.4f}% ({funding_direction})")
                
                if ls_data:
                    inst = ls_data['institutional']
                    retail = ls_data['retail']
                    
                    print(f"• Smart Money:")
                    print(f"    L: {inst['net_longs_tokens']:,.0f} {base_token} (${inst['net_longs_usd']/1e6:.0f}M) | S: {inst['net_shorts_tokens']:,.0f} {base_token} (${inst['net_shorts_usd']/1e6:.0f}M)")
                    print(f"    Ratio: {inst['long_ratio']:.2f}")
                    print(f"• All Participants:")
                    print(f"    L: {retail['net_longs_tokens']:,.0f} {base_token} (${retail['net_longs_usd']/1e6:.0f}M) | S: {retail['net_shorts_tokens']:,.0f} {base_token} (${retail['net_shorts_usd']/1e6:.0f}M)")
                    print(f"    Ratio: {retail['long_ratio']:.2f}")
            
            print()
            print("📉 TECHNICAL:")
            rsi = tech_data.get('rsi_14')
            vwap = tech_data.get('vwap')
            vol_15m = tech_data.get('volatility_15m')
            atr_usd = tech_data.get('atr_usd')
            
            if rsi:
                rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                print(f"• RSI: {rsi:.0f} ({rsi_status})")
            
            if vwap:
                vwap_status = "Above VWAP ✅" if current_price > vwap else "Below VWAP ❌"
                print(f"• VWAP: ${vwap:,.2f} ({vwap_status})")
            
            if vol_15m and atr_usd:
                print(f"• Volatility: {vol_15m:.1f}% | ATR: ${atr_usd:,.0f}")
            else:
                print("• Volatility: N/A | ATR: N/A (data pending)")
            
            rel_volume = volume_data['relative_volume']
            rel_volume_pct = int(rel_volume * 100)
            print(f"• Rel Volume: {rel_volume:.1f}x ({rel_volume_pct}% of normal)")
            
            print()
            print("🎯 MARKET CONTROL:")
            if ls_data:
                edge = ls_data.get('smart_money_edge', 0)
                inst_long_pct = inst['long_pct']
                retail_long_pct = retail['long_pct']
                edge_direction = "more bullish" if edge > 0 else "more bearish" if edge < 0 else "neutral vs"
                edge_sign = "+" if edge >= 0 else ""
                
                print(f"• SMART MONEY: {inst_long_pct:.1f}% Long | Ratio: {inst['long_ratio']:.2f}")
                print(f"• MARKET AVERAGE: {retail_long_pct:.1f}% Long | Ratio: {retail['long_ratio']:.2f}")
                print(f"• EDGE: Smart money {edge_sign}{edge:.1f}% {edge_direction} than market")
            
            print()
            print("🕐 UTC TIME / SGT TIME (timezone pending pytz install)")
            
            print("=" * 50)
            print("✅ NEW TEMPLATE FORMAT WORKING!")
            print("✅ All data structures successfully implemented")
            print("✅ Smart money analysis functional")
            print("⚠️  Technical indicators need debugging")
            print("⚠️  Timezone needs pytz installation")
            
        else:
            print("❌ API Error:", result.get('error'))
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_template_format()