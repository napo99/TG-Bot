#!/usr/bin/env python3
"""
Test DST transition logic for session boundaries
"""

from datetime import datetime
import sys
sys.path.append('/Users/screener-m3/projects/crypto-assistant/services/market-data')

from session_volume import SessionVolumeEngine

def test_dst_logic():
    """Test DST detection and session boundary adjustments"""
    
    # Create engine instance (without exchange manager for testing)
    engine = SessionVolumeEngine(None)
    
    # Test current time
    print("🕐 CURRENT TIME DST TEST")
    print("=" * 50)
    
    current_dt = datetime.utcnow()
    is_dst, adjustment = engine._is_dst_active(current_dt)
    
    print(f"Current UTC Time: {current_dt}")
    print(f"DST Active: {is_dst}")
    print(f"Adjustment: {adjustment}")
    
    # Get session boundaries for both DST and non-DST
    print("\n📊 SESSION BOUNDARIES")
    print("=" * 50)
    
    standard_sessions = engine._get_session_boundaries(is_dst=False)
    dst_sessions = engine._get_session_boundaries(is_dst=True)
    
    print("STANDARD TIME (No DST):")
    for name, config in standard_sessions.items():
        print(f"  {name.replace('_', ' ').title()}: {config['start']} - {config['end']} ({config['hours']}h)")
    
    print("\nDST TIME (+1 hour):")
    for name, config in dst_sessions.items():
        print(f"  {name.replace('_', ' ').title()}: {config['start']} - {config['end']} ({config['hours']}h)")
    
    # Test current session detection
    print("\n🎯 CURRENT SESSION DETECTION")
    print("=" * 50)
    
    session_name, session_data = engine._get_current_session(current_dt)
    
    print(f"Current Session: {session_name.replace('_', ' ').title()}")
    print(f"Session Hours: {session_data.start_time} - {session_data.end_time}")
    print(f"Progress: {session_data.session_progress:.1%}")
    print(f"Hour {session_data.current_hour} of {session_data.total_hours}")
    
    # Test specific times during the year
    print("\n📅 SEASONAL DST TESTS")
    print("=" * 50)
    
    test_dates = [
        datetime(2025, 1, 15, 14, 30),  # January (Standard Time)
        datetime(2025, 3, 29, 14, 30),  # Just before DST
        datetime(2025, 3, 31, 14, 30),  # Just after DST starts  
        datetime(2025, 7, 15, 14, 30),  # July (DST active)
        datetime(2025, 10, 25, 14, 30), # Just before DST ends
        datetime(2025, 10, 27, 14, 30), # Just after DST ends
        datetime(2025, 12, 15, 14, 30)  # December (Standard Time)
    ]
    
    for test_dt in test_dates:
        is_dst, adj = engine._is_dst_active(test_dt)
        session_name, session_info = engine._get_current_session(test_dt)
        
        print(f"{test_dt.strftime('%Y-%m-%d %H:%M')}: DST={is_dst}, Session={session_name.title()}, Hours={session_info.start_time}-{session_info.end_time}")
    
    print("\n✅ DST Logic Test Complete")

if __name__ == "__main__":
    test_dst_logic()