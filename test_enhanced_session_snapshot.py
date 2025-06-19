#!/usr/bin/env python3
"""
Test the enhanced SESSION SNAPSHOT format with smart deviation detection
"""

import asyncio
import aiohttp
import json
import pytz
from datetime import datetime

async def test_enhanced_session_snapshot():
    """Test the enhanced SESSION SNAPSHOT format with deviation warnings"""
    
    async with aiohttp.ClientSession() as session:
        # Get comprehensive analysis data
        async with session.post('http://localhost:8001/comprehensive_analysis', 
                               json={'symbol': 'BTC/USDT', 'timeframe': '15m'}) as resp:
            result = await resp.json()
    
    if not result['success']:
        print(f"❌ Analysis failed: {result['error']}")
        return
    
    data = result['data']
    
    # Extract session data
    session_data = data.get('session_analysis', {})
    price_data = data.get('price_data', {})
    volume_data = data.get('volume_analysis', {})
    cvd_data = data.get('cvd_analysis', {})
    tech_data = data.get('technical_indicators', {})
    sentiment = data.get('market_sentiment', {})
    long_short_data = data.get('long_short_data', {})
    
    # Simulate message formatting like the bot
    symbol = 'BTC/USDT'
    timeframe = '15m'
    base_token = symbol.split('/')[0]
    
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
    
    # Start building the message
    message = f"""🎯 MARKET ANALYSIS - {symbol} ({timeframe})

• PRICE: ${current_price:,.2f} {change_emoji} {change_sign}{change_24h:.1f}%
• VOLUME: {vol_emoji} {spike_level} {current_volume_tokens:,.0f} {base_token} ({spike_pct:+.0f}%, ${vol_usd/1e6:.1f}M)
• CVD: {cvd_emoji} {cvd_trend} {cvd_change:,.0f} {base_token} (${cvd_change * current_price / 1e6:.1f}M)
• DELTA: {delta_sign}{current_delta:,.0f} {base_token} (${current_delta_usd/1e6:.2f}M)
"""

    # Add enhanced session volume analysis
    if session_data:
        current_session_info = session_data.get('current_session', {})
        session_metrics = session_data.get('session_metrics', {})
        daily_context = session_data.get('daily_context', {})
        
        session_name = current_session_info.get('name', 'unknown')
        session_hour = current_session_info.get('current_hour', 1)
        session_total = current_session_info.get('total_hours', 1)
        session_start = current_session_info.get('start_time', '00:00')
        session_end = current_session_info.get('end_time', '24:00')
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
        
        # Calculate USD values
        session_vol_usd = session_vol * current_price
        session_rate_usd = session_rate * current_price
        session_avg = session_vol / session_rel if session_rel > 0 else 1
        rate_avg = session_rate / session_rate_rel if session_rate_rel > 0 else 1
        rate_avg_usd = rate_avg * current_price
        
        # Calculate percentage deviation for volume spike
        volume_deviation_pct = ((session_rel - 1) * 100) if session_rel > 0 else 0
        
        # Smart deviation detection with emojis
        # Volume Spike Classification
        if volume_deviation_pct >= 500:  # 6x or higher
            volume_emoji = "🚨🔥"
            volume_label = f"{session_vol:,.0f} {base_token} (${session_vol_usd/1e6:.0f}M) - {volume_deviation_pct:.0f}% above 7-day baseline"
        elif volume_deviation_pct >= 300:  # 4x or higher
            volume_emoji = "🔥🔥"
            volume_label = f"{session_vol:,.0f} {base_token} (${session_vol_usd/1e6:.0f}M) - {volume_deviation_pct:.0f}% above baseline"
        elif volume_deviation_pct >= 100:  # 2x or higher
            volume_emoji = "🔥"
            volume_label = f"{session_vol:,.0f} {base_token} (${session_vol_usd/1e6:.0f}M) - {volume_deviation_pct:.0f}% above baseline"
        elif volume_deviation_pct >= 50:   # 1.5x or higher
            volume_emoji = "⚡"
            volume_label = f"{session_vol:,.0f} {base_token} (${session_vol_usd/1e6:.0f}M) - {volume_deviation_pct:.0f}% above baseline"
        elif volume_deviation_pct >= 0:    # Above baseline
            volume_emoji = "✅"
            volume_label = f"{session_vol:,.0f} {base_token} (${session_vol_usd/1e6:.0f}M) - {volume_deviation_pct:.0f}% above baseline"
        else:  # Below baseline
            volume_emoji = "😴"
            volume_label = f"{session_vol:,.0f} {base_token} (${session_vol_usd/1e6:.0f}M) - {abs(volume_deviation_pct):.0f}% below baseline"
        
        # Market Pace Classification
        if session_rate_rel >= 5.0:
            pace_level = "EXTREME"
            pace_emoji = "🚨"
        elif session_rate_rel >= 3.0:
            pace_level = "HIGH"
            pace_emoji = "🔥"
        elif session_rate_rel >= 1.5:
            pace_level = "ELEVATED"
            pace_emoji = "⚡"
        elif session_rate_rel >= 0.5:
            pace_level = "NORMAL"
            pace_emoji = "✅"
        else:
            pace_level = "LOW"
            pace_emoji = "😴"
        
        # Volume Pattern Classification
        share_deviation = session_share - session_typical
        if share_deviation >= 50:
            pattern_description = "Heavy early activity"
            pattern_emoji = "📈"
        elif share_deviation >= 25:
            pattern_description = "Front-loaded volume"
            pattern_emoji = "⚡"
        elif share_deviation >= -25:
            pattern_description = "Normal distribution"
            pattern_emoji = "✅"
        elif share_deviation >= -50:
            pattern_description = "Back-loaded pattern"
            pattern_emoji = "📉"
        else:
            pattern_description = "Light early activity"
            pattern_emoji = "😴"
        
        message += f"""
📊 SESSION SNAPSHOT:
• {session_display} Trading: Hour {session_hour}/{session_total} ({session_start}-{session_end} UTC) ⏰
• Volume Spike: {volume_label} {volume_emoji}
• Market Pace: {pace_level} at ${session_rate_usd/1e6:.1f}M/hr vs ${rate_avg_usd/1e6:.1f}M/hr normal {pace_emoji}
• Volume Pattern: {pattern_description} ({session_share:.0f}% vs {session_typical:.0f}% typical) {pattern_emoji}

📈 DAILY CONTEXT:
• Day Volume: {daily_vol:,.0f} {base_token} (${daily_vol*current_price/1e6:.0f}M) - {sessions_done} sessions tracked
• Daily Average: {daily_avg:,.0f} {base_token} (${daily_avg*current_price/1e6:.0f}M) - 7-day baseline
• Progress: {daily_progress:.0f}% vs {100*(daily_vol/daily_avg) if daily_avg > 0 else 0:.0f}% typical at this hour"""

    # Add technical section
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

    # Print the complete enhanced message
    print("=" * 80)
    print("📱 ENHANCED SESSION SNAPSHOT PREVIEW")
    print("=" * 80)
    print(message)
    print("=" * 80)
    
    # Show key improvements
    if session_data:
        print("✅ ENHANCEMENTS IMPLEMENTED:")
        
        current_session_info = session_data.get('current_session', {})
        session_metrics = session_data.get('session_metrics', {})
        
        session_rel = session_metrics.get('session_rel_volume', 1)
        session_rate_rel = session_metrics.get('session_hourly_rel', 1)
        session_share = session_metrics.get('session_share_current', 0)
        session_typical = session_metrics.get('session_share_typical', 0)
        
        # Show deviation analysis
        volume_deviation_pct = ((session_rel - 1) * 100) if session_rel > 0 else 0
        share_deviation = session_share - session_typical
        
        print(f"🔥 Volume Deviation Analysis: {volume_deviation_pct:.0f}% above baseline")
        if volume_deviation_pct >= 500:
            print("   ⚠️  EXTREME WARNING: >500% above normal (🚨🔥)")
        elif volume_deviation_pct >= 300:
            print("   🔥 HIGH WARNING: >300% above normal (🔥🔥)")
        elif volume_deviation_pct >= 100:
            print("   ⚡ ELEVATED: >100% above normal (🔥)")
        
        print(f"⏱️  Pace Analysis: {session_rate_rel:.1f}x normal rate")
        if session_rate_rel >= 5.0:
            print("   🚨 EXTREME PACE WARNING")
        elif session_rate_rel >= 3.0:
            print("   🔥 HIGH PACE WARNING")
        
        print(f"📊 Pattern Analysis: {share_deviation:+.0f}% vs typical session share")
        if abs(share_deviation) >= 25:
            print("   📈 SIGNIFICANT DISTRIBUTION PATTERN DETECTED")
        
        print(f"💰 USD Integration: All volume metrics include USD values")
        print(f"🎯 Smart Emojis: Automatic warning system based on thresholds")
        print(f"📋 Human Readable: Technical jargon replaced with action terms")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_enhanced_session_snapshot())