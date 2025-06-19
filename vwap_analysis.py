#!/usr/bin/env python3
"""
VWAP Calculation Analysis
Compare our VWAP with standard trading app implementations
"""

import ccxt
from datetime import datetime, timedelta
import requests

def analyze_vwap_calculation():
    """Analyze how our VWAP is calculated vs trading apps"""
    
    print("📊 VWAP CALCULATION ANALYSIS")
    print("=" * 50)
    
    # Our current implementation
    print("🔍 OUR VWAP IMPLEMENTATION:")
    print("-" * 30)
    print("Formula: VWAP = Σ(Typical_Price × Volume) / Σ(Volume)")
    print("Typical_Price = (High + Low + Close) / 3")
    print("Period: 100 candles of user timeframe")
    print("For 15m: 100 × 15m = 25 hours of data")
    print()
    
    # Standard trading app implementations
    print("📱 STANDARD TRADING APP VWAP:")
    print("-" * 35)
    print("TradingView: Session-based VWAP (resets daily)")
    print("Binance App: Intraday VWAP (24h or session)")
    print("MT4/MT5: Period VWAP (configurable)")
    print("Coinigy: Session VWAP (resets at midnight UTC)")
    print()
    
    try:
        # Get current OHLCV data
        exchange = ccxt.binance({'enableRateLimit': True})
        
        print("🧮 LIVE CALCULATION COMPARISON:")
        print("-" * 40)
        
        # Test different periods
        periods = [
            {'timeframe': '15m', 'limit': 100, 'description': 'Our Current (25h)'},
            {'timeframe': '15m', 'limit': 96, 'description': 'Exactly 24h'},
            {'timeframe': '15m', 'limit': 48, 'description': '12h Session'},
            {'timeframe': '15m', 'limit': 24, 'description': '6h Period'},
            {'timeframe': '1h', 'limit': 24, 'description': '24h Hourly'},
        ]
        
        for config in periods:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', config['timeframe'], limit=config['limit'])
            
            if len(ohlcv) > 0:
                # Calculate VWAP
                total_pv = 0
                total_volume = 0
                
                for candle in ohlcv:
                    timestamp, open_price, high, low, close, volume = candle
                    typical_price = (high + low + close) / 3
                    pv = typical_price * volume
                    total_pv += pv
                    total_volume += volume
                
                vwap = total_pv / total_volume if total_volume > 0 else 0
                current_price = ohlcv[-1][4]  # Last close
                
                # Calculate time span
                start_time = datetime.fromtimestamp(ohlcv[0][0] / 1000)
                end_time = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
                duration = end_time - start_time
                
                print(f"\n📊 {config['description']}:")
                print(f"   Timeframe: {config['timeframe']}")
                print(f"   Candles: {len(ohlcv)}")
                print(f"   Duration: {duration}")
                print(f"   VWAP: ${vwap:,.2f}")
                print(f"   Current: ${current_price:,.2f}")
                print(f"   Difference: ${current_price - vwap:,.2f}")
                
                # Compare with user's observation
                user_vwap = 104812
                if abs(vwap - user_vwap) < 500:
                    print(f"   ✅ Close to trading app VWAP (${user_vwap:,.2f})")
                else:
                    print(f"   ❌ Different from trading app VWAP (${user_vwap:,.2f})")
    
    except Exception as e:
        print(f"❌ Error in calculation: {e}")
    
    print(f"\n🎯 TRADING APP VWAP DIFFERENCES:")
    print("-" * 40)
    print("1. SESSION-BASED RESET:")
    print("   - Most apps reset VWAP at session start")
    print("   - Common reset times: 00:00 UTC, market open")
    print("   - Our system: Continuous rolling period")
    print()
    
    print("2. PERIOD LENGTH:")
    print("   - Trading apps: Usually 1 trading session")
    print("   - Our system: 100 candles (varies by timeframe)")
    print("   - 15m × 100 = 25 hours (too long!)")
    print()
    
    print("3. FORMULA DIFFERENCES:")
    print("   - Standard VWAP: Usually (H+L+C)/3 × Volume")
    print("   - Some use: Close × Volume")
    print("   - Some use: (O+H+L+C)/4 × Volume")
    print("   - Our system: (H+L+C)/3 × Volume ✅ Standard")
    print()
    
    print("4. TIME ZONE & SESSION:")
    print("   - Trading apps: Respect market sessions")
    print("   - Our system: Ignores session boundaries")
    print("   - This causes significant differences!")

def calculate_session_vwap():
    """Calculate session-based VWAP like trading apps"""
    
    print(f"\n🕐 SESSION-BASED VWAP CALCULATION:")
    print("-" * 45)
    
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        
        # Get current UTC time
        now = datetime.utcnow()
        session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"Current Time: {now}")
        print(f"Session Start: {session_start}")
        
        # Calculate minutes since session start
        minutes_elapsed = int((now - session_start).total_seconds() / 60)
        candles_needed = max(1, minutes_elapsed // 15)  # 15m candles since session start
        
        print(f"Minutes since session start: {minutes_elapsed}")
        print(f"15m candles needed: {candles_needed}")
        
        # Get session data
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=min(candles_needed, 96))
        
        if len(ohlcv) > 0:
            # Calculate session VWAP
            total_pv = 0
            total_volume = 0
            
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                typical_price = (high + low + close) / 3
                pv = typical_price * volume
                total_pv += pv
                total_volume += volume
            
            session_vwap = total_pv / total_volume if total_volume > 0 else 0
            current_price = ohlcv[-1][4]
            
            print(f"\n📊 SESSION VWAP RESULTS:")
            print(f"   Candles used: {len(ohlcv)}")
            print(f"   Session VWAP: ${session_vwap:,.2f}")
            print(f"   Current Price: ${current_price:,.2f}")
            
            # Compare with user's trading app VWAP
            user_app_vwap = 104812
            print(f"\n🔍 COMPARISON:")
            print(f"   Trading App VWAP: ${user_app_vwap:,.2f}")
            print(f"   Our Session VWAP: ${session_vwap:,.2f}")
            print(f"   Difference: ${abs(session_vwap - user_app_vwap):,.2f}")
            
            if abs(session_vwap - user_app_vwap) < 100:
                print(f"   ✅ Very close! Session-based is the answer")
            elif abs(session_vwap - user_app_vwap) < 500:
                print(f"   ✅ Close! Session-based likely correct approach")
            else:
                print(f"   ❌ Still different - may need other adjustments")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def recommend_vwap_fix():
    """Recommend how to fix VWAP to match trading apps"""
    
    print(f"\n🔧 RECOMMENDED VWAP FIXES:")
    print("=" * 35)
    
    print("1. IMPLEMENT SESSION-BASED VWAP:")
    print("   - Reset at 00:00 UTC daily")
    print("   - Use only candles from current session")
    print("   - Matches TradingView, Binance app behavior")
    print()
    
    print("2. FIXED TIMEFRAME APPROACH:")
    print("   - Always use 1-minute candles")
    print("   - Aggregate to session period")
    print("   - More accurate than variable periods")
    print()
    
    print("3. ALTERNATIVE: FIXED 24H VWAP:")
    print("   - Use exactly 24 hours of data")
    print("   - Rolling 24h window")
    print("   - More consistent than current 25h")
    print()
    
    print("CODE IMPLEMENTATION:")
    print("-" * 20)
    print("""
async def calculate_session_vwap(symbol, exchange):
    # Get current UTC time
    now = datetime.utcnow()
    session_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate session duration in minutes
    session_minutes = int((now - session_start).total_seconds() / 60)
    
    # Use 1m candles for accuracy
    candles_needed = min(session_minutes, 1440)  # Max 24h
    
    # Fetch session data
    ohlcv = await exchange.fetch_ohlcv(symbol, '1m', limit=candles_needed)
    
    # Calculate VWAP
    total_pv = sum(((h+l+c)/3) * v for _, _, h, l, c, v in ohlcv)
    total_volume = sum(v for _, _, _, _, _, v in ohlcv)
    
    return total_pv / total_volume if total_volume > 0 else 0
    """)

if __name__ == "__main__":
    analyze_vwap_calculation()
    calculate_session_vwap()
    recommend_vwap_fix()