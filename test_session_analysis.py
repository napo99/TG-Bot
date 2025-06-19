#!/usr/bin/env python3
"""
Test script to simulate Telegram bot message formatting with session volume analysis
"""

import asyncio
import aiohttp
import json
import pytz
from datetime import datetime

async def test_session_analysis():
    """Test the session volume analysis and message formatting"""
    
    async with aiohttp.ClientSession() as session:
        # Get comprehensive analysis data
        async with session.post('http://localhost:8001/comprehensive_analysis', 
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'}) as resp:
            result = await resp.json()
    
    if not result['success']:
        print(f"❌ Analysis failed: {result['error']}")
        return
    
    data = result['data']
    
    # Extract all the data like the bot does
    price_data = data.get('price_data', {})
    volume_data = data.get('volume_analysis', {})
    cvd_data = data.get('cvd_analysis', {})
    tech_data = data.get('technical_indicators', {})
    sentiment = data.get('market_sentiment', {})
    oi_data = data.get('oi_data', {})
    long_short_data = data.get('long_short_data', {})
    session_data = data.get('session_analysis', {})
    
    # Format like the bot
    symbol = 'BTC/USDT'
    timeframe = '15m'
    
    # Price info
    current_price = price_data.get('current_price', 0)
    change_24h = price_data.get('change_24h', 0)
    change_emoji = "🟢" if change_24h >= 0 else "🔴"
    change_sign = "+" if change_24h >= 0 else ""
    
    # Volume info
    spike_level = volume_data.get('spike_level', 'NORMAL')
    spike_pct = volume_data.get('spike_percentage', 0)
    vol_usd = volume_data.get('volume_usd', 0)
    current_volume_tokens = volume_data.get('current_volume', 0)
    rel_volume = volume_data.get('relative_volume', 1)
    
    vol_emoji = "🔥🔥🔥" if spike_level == 'EXTREME' else "🔥🔥" if spike_level == 'HIGH' else "🔥" if spike_level == 'MODERATE' else "😴"
    
    # CVD info
    cvd_trend = cvd_data.get('cvd_trend', 'NEUTRAL')
    cvd_change = cvd_data.get('cvd_change_24h', 0)
    current_delta = cvd_data.get('current_delta', 0)
    current_delta_usd = cvd_data.get('current_delta_usd', 0)
    
    cvd_emoji = "🟢📈" if cvd_trend == 'BULLISH' else "🔴📉" if cvd_trend == 'BEARISH' else "⚪➡️"
    delta_sign = "+" if current_delta >= 0 else ""
    
    base_token = symbol.split('/')[0]
    
    # Start building the message
    message = f"""🎯 MARKET ANALYSIS - {symbol} ({timeframe})

• PRICE: ${current_price:,.2f} {change_emoji} {change_sign}{change_24h:.1f}%
• VOLUME: {vol_emoji} {spike_level} {current_volume_tokens:,.0f} {base_token} ({spike_pct:+.0f}%, ${vol_usd/1e6:.1f}M)
• CVD: {cvd_emoji} {cvd_trend} {cvd_change:,.0f} {base_token} (${cvd_change * current_price / 1e6:.1f}M)
• DELTA: {delta_sign}{current_delta:,.0f} {base_token} (${current_delta_usd/1e6:.2f}M)
"""

    # Add session volume analysis (this is the new feature)
    if session_data:
        current_session_info = session_data.get('current_session', {})
        session_metrics = session_data.get('session_metrics', {})
        daily_context = session_data.get('daily_context', {})
        
        session_name = current_session_info.get('name', 'unknown')
        session_hour = current_session_info.get('current_hour', 1)
        session_total = current_session_info.get('total_hours', 1)
        session_vol = current_session_info.get('current_volume', 0)
        session_rel = session_metrics.get('session_rel_volume', 1)
        session_rate = session_metrics.get('session_hourly_rate', 0)
        session_rate_rel = session_metrics.get('session_hourly_rel', 1)
        session_share = session_metrics.get('session_share_current', 0)
        session_typical = session_metrics.get('session_share_typical', 0)
        
        daily_vol = daily_context.get('current_daily_volume', 0)
        daily_avg = daily_context.get('daily_avg_7day', 0)
        daily_progress = daily_context.get('daily_progress_pct', 0)
        sessions_done = daily_context.get('sessions_completed', 0)
        
        # Format session name for display
        session_display = session_name.replace('_', ' ').title()
        
        # Calculate average volumes for display (avoid division by zero)
        session_avg = session_vol / session_rel if session_rel > 0 else 0
        rate_avg = session_rate / session_rate_rel if session_rate_rel > 0 else 0
        
        message += f"""
📊 SESSION ANALYSIS:
• Current: {session_display} (Hour {session_hour} of {session_total})
• Session Vol: {session_vol:,.0f} {base_token} ({session_rel:.1f}x vs {session_avg:,.0f} avg)
• Session Rate: {session_rate:,.0f} {base_token}/hr ({session_rate_rel:.1f}x vs {rate_avg:,.0f} avg)
• Session Share: {session_share:.0f}% of daily (vs {session_typical:.0f}% typical)

📈 DAILY CONTEXT:
• Day Volume: {daily_vol:,.0f} {base_token} ({sessions_done} sessions tracked)
• Daily Average: {daily_avg:,.0f} {base_token} (7-day baseline)
• Progress: {daily_progress:.0f}% vs {100*(daily_vol/daily_avg) if daily_avg > 0 else 0:.0f}% typical at this hour"""

    # Add technical indicators
    rsi = tech_data.get('rsi_14')
    vwap = tech_data.get('vwap')
    volatility_15m = tech_data.get('volatility_15m', 0)
    atr_usd = tech_data.get('atr_usd', 0)
    
    message += f"""

📉 TECHNICAL:"""
    
    if rsi:
        rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        message += f"\n• RSI: {rsi:.0f} ({rsi_status})"
    
    if vwap and current_price:
        vwap_status = "Above VWAP ✅" if current_price > vwap else "Below VWAP ❌"
        message += f"\n• VWAP: ${vwap:,.2f} ({vwap_status})"
    
    if volatility_15m and atr_usd:
        message += f"\n• Volatility: {volatility_15m:.1f}% | ATR: ${atr_usd:,.0f}"
    
    rel_volume_pct = int(rel_volume * 100)
    message += f"\n• Rel Volume: {rel_volume:.1f}x ({rel_volume_pct}% of normal)"

    # Add market control
    control = sentiment.get('market_control', 'NEUTRAL')
    control_strength = sentiment.get('control_strength', 50)
    aggression = sentiment.get('aggression_level', 'LOW')
    
    message += f"""

🎯 MARKET CONTROL:
• {control} IN CONTROL ({control_strength:.0f}% confidence)
• Aggression: {aggression}"""

    # Add timestamp
    utc_time = datetime.now(pytz.UTC)
    sgt_time = utc_time.astimezone(pytz.timezone('Asia/Singapore'))
    
    message += f"\n\n🕐 {utc_time.strftime('%H:%M:%S')} UTC / {sgt_time.strftime('%H:%M:%S')} SGT"

    # Print the complete message
    print("=" * 80)
    print("📱 TELEGRAM BOT MESSAGE PREVIEW")
    print("=" * 80)
    print(message)
    print("=" * 80)
    print(f"✅ Session analysis integration: {'SUCCESS' if session_data else 'MISSING'}")
    if session_data:
        dst_info = session_data.get('dst_info', {})
        print(f"🕐 DST Status: {dst_info.get('dst_adjustment', 'unknown')}")
        print(f"📊 Session: {session_data['current_session']['name'].title()}")
        print(f"📈 Session Progress: Hour {session_data['current_session']['current_hour']} of {session_data['current_session']['total_hours']}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_session_analysis())