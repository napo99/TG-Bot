# 🚀 Session-Based Profile Implementation Plan

## 📋 EXECUTIVE SUMMARY

**Current Issue:** Our `/profile` command uses arbitrary rolling periods while TradingView uses session-based calculations.
**Solution:** Implement 08:00 UTC session reset for VWAP, Volume Profile (VAH/POC/VAL), and TPO calculations.
**Scope:** ONLY `/profile` command - no changes to existing `/analysis` or other commands.

## 🎯 CURRENT STATE (Pre-Implementation)

### **Current Rolling Period Approach:**
```python
# ProfileCalculator - Volume Profile periods
'1m': 60 candles (1 hour)
'15m': 96 candles (24 hours)  
'1h': 168 candles (7 days)
'4h': 84 candles (14 days)
'1d': 30 candles (30 days)

# ProfileCalculator - VWAP periods  
'1m': 30 candles (30 minutes)
'15m': 32 candles (8 hours)
'1h': 24 candles (1 day)
'4h': 6 candles (1 day)
'1d': 7 candles (1 week)
```

### **TradingView Values (Target):**
- **VWAP across timeframes**: ~$4,257-$4,277 (similar values = session-based)
- **Volume Profile levels**: Consistent with session boundaries
- **TPO distribution**: 30-minute periods within same session

## 🔍 ROOT CAUSE ANALYSIS

### **Why Our Values Differ:**
1. **Rolling periods ignore session boundaries**
2. **Different data windows for each timeframe**
3. **No alignment between VWAP and Volume Profile sessions**
4. **TPO uses arbitrary periods instead of session-based 30m blocks**

### **TradingView Approach (Discovered):**
- **08:00 UTC reset** for intraday sessions (matches our testing: $4,268.94 vs TradingView ~$4,267)
- **All intraday timeframes use same session data**
- **Daily timeframe uses 24-hour session (00:00 UTC reset)**
- **TPO uses 30-minute periods within session boundaries**

## 🎯 IMPLEMENTATION PLAN

### **Phase 1: Session-Based Data Fetching**

#### **1.1 Add Session Time Utilities**
```python
class SessionManager:
    @staticmethod
    def get_session_start_timestamp():
        """Get 08:00 UTC session start timestamp"""
        
    @staticmethod  
    def calculate_candles_since_session(interval: str) -> int:
        """Calculate candles needed from session start"""
        
    @staticmethod
    def is_daily_timeframe(timeframe: str) -> bool:
        """Check if timeframe should use daily session (00:00 UTC)"""
```

#### **1.2 Modify ProfileCalculator**
```python
# New session-based approach
async def _fetch_session_candles(self, symbol: str, interval: str, timeframe: str):
    """Fetch candles from session start instead of fixed lookback"""
    
    if self._is_daily_timeframe(timeframe):
        # Daily: Reset at 00:00 UTC  
        session_start = get_daily_session_start()
    else:
        # Intraday: Reset at 08:00 UTC
        session_start = get_intraday_session_start()
    
    candles_needed = calculate_candles_since_session(interval, session_start)
    return await self._fetch_candles(symbol, interval, candles_needed)
```

### **Phase 2: Unified Session Calculations**

#### **2.1 VWAP Session Alignment**
- **Intraday timeframes** (1m, 15m, 1h, 4h): Use session data from 08:00 UTC
- **Daily timeframe**: Use 24-hour session from 00:00 UTC
- **Result**: All intraday VWAPs show similar values (~$4,267)

#### **2.2 Volume Profile Session Alignment**  
- **Same session data as VWAP** for consistency
- **VAH/POC/VAL calculated from session start**
- **Maintains TradingView-like behavior**

#### **2.3 TPO Session Alignment**
- **30-minute TPO periods within session boundaries**
- **Session start at 08:00 UTC for intraday**
- **Proper TPO distribution matching institutional standards**

### **Phase 3: Display Updates**

#### **3.1 Updated Labels**
```python
# Clear session-based labeling
tf_periods = {
    '1m': 'Session',     # Since 08:00 UTC
    '15m': 'Session',    # Since 08:00 UTC  
    '1h': 'Session',     # Since 08:00 UTC
    '4h': 'Session',     # Since 08:00 UTC
    '1d': 'Daily'        # Since 00:00 UTC
}
```

#### **3.2 Expected Output Format**
```
1H Profile
- VAH: $4,468 ✅
- VWAP (Session): $4,267 ↓ (-1.7%)  # Now matches TradingView
- POC: $4,303  
- VAL: $4,137

Daily Profile  
- VAH: $4,329 ✅
- VWAP (Daily): $4,257 ↓ (-2.8%)    # 24-hour session
- POC: $3,713
- VAL: $3,412
TPO 30m: POC: $3,716 | VAL: $3,354 | VAH: $4,310
```

## ⚙️ TECHNICAL IMPLEMENTATION DETAILS

### **Session Boundary Logic**
```python
def get_session_boundaries():
    """Calculate session start times"""
    utc_now = datetime.now(timezone.utc)
    
    # Intraday session: 08:00 UTC daily reset
    intraday_reset_hour = 8
    if utc_now.hour >= intraday_reset_hour:
        # Current session started today at 08:00
        session_start = utc_now.replace(hour=intraday_reset_hour, minute=0, second=0, microsecond=0)
    else:
        # Current session started yesterday at 08:00  
        yesterday = utc_now - timedelta(days=1)
        session_start = yesterday.replace(hour=intraday_reset_hour, minute=0, second=0, microsecond=0)
    
    return session_start
```

### **Candle Calculation**
```python
def calculate_session_candles(interval: str, session_start: datetime) -> int:
    """Calculate candles needed from session start"""
    utc_now = datetime.now(timezone.utc)
    time_diff = utc_now - session_start
    hours_elapsed = time_diff.total_seconds() / 3600
    
    interval_minutes = {
        '1m': 1, '5m': 5, '15m': 15, 
        '30m': 30, '1h': 60, '4h': 240, '1d': 1440
    }
    
    candles = int((hours_elapsed * 60) / interval_minutes[interval])
    return max(1, min(candles, 1000))  # Binance API limits
```

## 🧪 TESTING PLAN

### **Validation Checkpoints:**
1. **VWAP Alignment**: All intraday timeframes show ~$4,267 (matches TradingView)
2. **Volume Profile Consistency**: VAH/POC/VAL levels align with session data
3. **TPO Distribution**: 30-minute periods within session boundaries
4. **Session Boundaries**: Correct reset at 08:00 UTC for intraday
5. **Daily Session**: Correct reset at 00:00 UTC for daily timeframe

### **Test Commands:**
```bash
# Test session-based calculations
curl -X POST http://localhost:8001/market_profile -H "Content-Type: application/json" -d '{"symbol": "ETH"}'

# Compare with TradingView values
# Expected: VWAP ~$4,267 across all intraday timeframes
```

## 📊 EXPECTED IMPROVEMENTS

### **Before (Current Rolling Periods):**
- **1H VWAP**: $4,296 (arbitrary 1-day rolling)
- **4H VWAP**: $4,291 (arbitrary 1-day rolling)  
- **Values inconsistent** with TradingView

### **After (Session-Based):**
- **1H VWAP**: ~$4,267 (session-based, matches TradingView)
- **4H VWAP**: ~$4,267 (same session, matches TradingView)
- **All intraday timeframes aligned** with institutional standards

## 🔒 SAFETY CONSTRAINTS

### **What WILL Change:**
- ✅ `/profile` command calculations (VWAP, VAH/POC/VAL, TPO)
- ✅ ProfileCalculator session logic
- ✅ Display labels for session context

### **What WILL NOT Change:**
- ❌ TechnicalIndicators service (used by `/analysis` command)
- ❌ Any other existing commands or modules
- ❌ External API interfaces
- ❌ Database schemas or configurations

## 🎯 SUCCESS CRITERIA

1. **VWAP values match TradingView** (~$4,267 across intraday timeframes)
2. **Volume Profile levels consistent** with session boundaries  
3. **TPO distribution proper** (30-minute session-based periods)
4. **All existing commands unchanged** (zero breaking changes)
5. **Clear session-based labeling** (users understand the timeframe context)

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Create SessionManager utility class
- [ ] Modify ProfileCalculator to use session boundaries
- [ ] Update VWAP calculation for session-based approach  
- [ ] Update Volume Profile calculation for session-based approach
- [ ] Update TPO calculation for session-based approach
- [ ] Update telegram bot labels to show session context
- [ ] Test session boundary calculations
- [ ] Validate VWAP values match TradingView
- [ ] Verify no existing functionality broken
- [ ] Document session reset times and rationale

---

**🎯 OBJECTIVE: Make `/profile` command calculations match TradingView institutional standards while preserving all existing functionality.**