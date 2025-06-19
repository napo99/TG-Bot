#!/usr/bin/env python3
"""
VWAP Period Comparison - Test different periods to match trading apps
"""

import ccxt
from datetime import datetime, timedelta
import requests

def test_all_vwap_periods():
    """Test different VWAP periods to find which matches trading apps"""
    
    print("📊 VWAP PERIOD COMPARISON ANALYSIS")
    print("=" * 50)
    
    # Trading platform VWAP behavior research
    print("🔍 TRADING PLATFORM VWAP BEHAVIOR:")
    print("-" * 40)
    print("📱 TradingView: Session-based (market session, NOT UTC 0:00)")
    print("📱 Binance Spot: Anchored VWAP (user can set anchor point)")
    print("📱 Binance Futures: Rolling period or session-based")
    print("📱 MT4/MT5: Period-based (configurable)")
    print("📱 Coinigy: Various (session, period, or custom)")
    print("📱 3Commas: Usually 24h rolling")
    print()
    
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        
        print("🧮 TESTING DIFFERENT VWAP PERIODS:")
        print("=" * 45)
        
        # Test periods matching your specification
        test_periods = {
            '1m_1h': {'timeframe': '1m', 'limit': 60, 'description': '1m × 60 = 1 hour'},
            '5m_8h': {'timeframe': '5m', 'limit': 96, 'description': '5m × 96 = 8 hours'},
            '15m_12h': {'timeframe': '15m', 'limit': 48, 'description': '15m × 48 = 12 hours'},
            '1h_24h': {'timeframe': '1h', 'limit': 24, 'description': '1h × 24 = 24 hours'},
            '4h_24h': {'timeframe': '4h', 'limit': 6, 'description': '4h × 6 = 24 hours'},
            '1d_1d': {'timeframe': '1d', 'limit': 1, 'description': '1d × 1 = 1 day'},
            
            # Additional common periods for comparison
            'current_15m': {'timeframe': '15m', 'limit': 100, 'description': '15m × 100 = 25 hours (CURRENT)'},
            '15m_24h': {'timeframe': '15m', 'limit': 96, 'description': '15m × 96 = 24 hours'},
            '15m_6h': {'timeframe': '15m', 'limit': 24, 'description': '15m × 24 = 6 hours'},
            '1m_8h': {'timeframe': '1m', 'limit': 480, 'description': '1m × 480 = 8 hours'},
        }
        
        vwap_results = {}
        
        for period_name, config in test_periods.items():
            try:
                print(f"\n📊 Testing: {config['description']}")
                
                # Fetch OHLCV data
                ohlcv = exchange.fetch_ohlcv('BTC/USDT', config['timeframe'], limit=config['limit'])
                
                if len(ohlcv) == 0:
                    print(f"   ❌ No data available")
                    continue
                
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
                current_price = ohlcv[-1][4]  # Last close price
                
                # Calculate actual time span
                start_time = datetime.fromtimestamp(ohlcv[0][0] / 1000)
                end_time = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
                actual_duration = end_time - start_time
                
                vwap_results[period_name] = {
                    'vwap': vwap,
                    'current_price': current_price,
                    'candles': len(ohlcv),
                    'duration': actual_duration,
                    'description': config['description']
                }
                
                print(f"   ✅ VWAP: ${vwap:,.2f}")
                print(f"   📊 Current: ${current_price:,.2f}")
                print(f"   📈 Diff: ${current_price - vwap:,.2f}")
                print(f"   🕐 Duration: {actual_duration}")
                print(f"   📝 Candles: {len(ohlcv)}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        # Compare with user's trading app value
        user_trading_app_vwap = 104812
        
        print(f"\n🎯 COMPARISON WITH TRADING APP VWAP (${user_trading_app_vwap:,.2f}):")
        print("=" * 65)
        
        closest_matches = []
        
        for period_name, result in vwap_results.items():
            diff = abs(result['vwap'] - user_trading_app_vwap)
            percentage_diff = (diff / user_trading_app_vwap) * 100
            
            match_quality = "🎯 EXCELLENT" if diff < 50 else "✅ GOOD" if diff < 200 else "⚠️ MODERATE" if diff < 500 else "❌ POOR"
            
            print(f"\n{match_quality} - {result['description']}")
            print(f"   VWAP: ${result['vwap']:,.2f}")
            print(f"   Difference: ${diff:,.2f} ({percentage_diff:.2f}%)")
            
            if diff < 200:  # Good matches
                closest_matches.append((period_name, result, diff))
        
        # Sort by closest match
        closest_matches.sort(key=lambda x: x[2])
        
        print(f"\n🏆 BEST MATCHES (Closest to Trading App):")
        print("-" * 45)
        
        for i, (period_name, result, diff) in enumerate(closest_matches[:3], 1):
            print(f"{i}. {result['description']}")
            print(f"   VWAP: ${result['vwap']:,.2f} (${diff:,.2f} difference)")
            print(f"   Duration: {result['duration']}")
        
        # Session analysis
        print(f"\n🕐 SESSION ANALYSIS:")
        print("-" * 20)
        
        now = datetime.utcnow()
        session_start_utc = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hours_since_utc_start = (now - session_start_utc).total_seconds() / 3600
        
        print(f"Current UTC Time: {now}")
        print(f"Hours since UTC 0:00: {hours_since_utc_start:.2f}")
        
        # Common trading session starts
        sessions = {
            'UTC 0:00': session_start_utc,
            'London Open (8:00 UTC)': now.replace(hour=8, minute=0, second=0, microsecond=0),
            'NY Open (13:00 UTC)': now.replace(hour=13, minute=0, second=0, microsecond=0),
            'Asia Open (22:00 UTC prev day)': (now.replace(hour=22, minute=0, second=0, microsecond=0) - timedelta(days=1)),
        }
        
        for session_name, session_start in sessions.items():
            if session_start <= now:
                hours_elapsed = (now - session_start).total_seconds() / 3600
                print(f"{session_name}: {hours_elapsed:.2f} hours ago")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def trading_platform_vwap_research():
    """Research actual VWAP behavior in trading platforms"""
    
    print(f"\n📚 TRADING PLATFORM VWAP RESEARCH:")
    print("=" * 45)
    
    platforms = {
        "TradingView": {
            "default": "Session-based (depends on market)",
            "crypto": "Usually 24h or custom anchor",
            "reset": "Market session start OR custom anchor point",
            "notes": "User can set custom anchor point"
        },
        "Binance Spot App": {
            "default": "Anchored VWAP",
            "crypto": "Usually intraday or 24h",
            "reset": "User-defined anchor OR market session",
            "notes": "Highly customizable"
        },
        "Binance Futures": {
            "default": "Period-based",
            "crypto": "Often 24h rolling",
            "reset": "Varies by implementation",
            "notes": "May differ from spot"
        },
        "MT4/MT5": {
            "default": "Period-based VWAP",
            "crypto": "Configurable period",
            "reset": "Based on period setting",
            "notes": "Very customizable"
        },
        "3Commas/Crypto Apps": {
            "default": "24h rolling",
            "crypto": "Usually 24h or session",
            "reset": "Continuous rolling",
            "notes": "Focused on crypto trading"
        }
    }
    
    for platform, info in platforms.items():
        print(f"\n📱 {platform}:")
        print(f"   Default: {info['default']}")
        print(f"   Crypto: {info['crypto']}")
        print(f"   Reset: {info['reset']}")
        print(f"   Notes: {info['notes']}")

def recommend_timeframe_periods():
    """Recommend optimal periods for each timeframe"""
    
    print(f"\n🎯 RECOMMENDED TIMEFRAME PERIODS:")
    print("=" * 40)
    
    recommendations = {
        '1m': {
            'period': 240,  # 4 hours
            'reasoning': '4h provides good intraday context without too much noise'
        },
        '5m': {
            'period': 96,   # 8 hours  
            'reasoning': '8h covers major trading sessions'
        },
        '15m': {
            'period': 48,   # 12 hours
            'reasoning': '12h provides half-day context, good for intraday'
        },
        '1h': {
            'period': 24,   # 24 hours
            'reasoning': '24h standard daily VWAP'
        },
        '4h': {
            'period': 6,    # 24 hours
            'reasoning': '24h equivalent for longer timeframes'
        },
        '1d': {
            'period': 7,    # 1 week
            'reasoning': 'Weekly context for daily charts'
        }
    }
    
    for timeframe, config in recommendations.items():
        duration_hours = {
            '1m': config['period'] / 60,
            '5m': config['period'] * 5 / 60,
            '15m': config['period'] * 15 / 60,
            '1h': config['period'],
            '4h': config['period'] * 4,
            '1d': config['period'] * 24
        }[timeframe]
        
        print(f"\n⏰ {timeframe} timeframe:")
        print(f"   Recommended period: {config['period']} candles")
        print(f"   Duration: {duration_hours:.1f} hours")
        print(f"   Reasoning: {config['reasoning']}")

if __name__ == "__main__":
    test_all_vwap_periods()
    trading_platform_vwap_research()
    recommend_timeframe_periods()