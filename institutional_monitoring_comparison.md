# 🏦 Institutional Monitoring Systems vs Our Implementation

## 📍 Current Threshold Locations

### **Hardcoded Thresholds (Current Implementation)**

1. **services/telegram-bot/liquidation_monitor.py** (Lines 41-48)
   ```python
   self.thresholds = {
       'BTC': 100000,  # $100k+ for BTC
       'ETH': 50000,   # $50k+ for ETH  
       'SOL': 25000,   # $25k+ for SOL
       'default': 10000  # $10k+ for others
   }
   ```

2. **services/telegram-bot/oi_monitor.py** (Lines 29-34)
   ```python
   self.thresholds = {
       'BTC': {'change_pct': 15.0, 'min_oi': 50_000_000},
       'ETH': {'change_pct': 18.0, 'min_oi': 25_000_000},
       'SOL': {'change_pct': 25.0, 'min_oi': 10_000_000},
       'default': {'change_pct': 30.0, 'min_oi': 5_000_000}
   }
   ```

3. **shared/config/alert_thresholds.py** (Centralized config with ENV support)
   - Supports environment variables: `LIQUIDATION_THRESHOLD_BTC`, `OI_THRESHOLD_ETH`, etc.
   - Currently NOT used by telegram-bot monitors (they use hardcoded values)

## 🚨 Critical Gaps vs Institutional Systems

### **1. Market Regime Awareness ❌**

**Our System:**
- Static thresholds regardless of market conditions
- Same alerts on weekends vs weekdays
- No volatility adjustment

**Institutional Systems:**
- **Dynamic thresholds** based on:
  - VIX/Volatility index
  - Trading session (Asia/Europe/US)
  - Weekend/Holiday adjustments
  - Market capitalization changes

**Example - Bloomberg Terminal:**
```python
# Institutional approach
def get_dynamic_threshold(symbol, base_threshold):
    volatility_multiplier = get_current_volatility() / historical_avg_volatility()
    session_multiplier = {
        'asian': 0.7,    # Lower volume
        'european': 0.9,
        'us': 1.0,       # Highest volume
        'weekend': 0.5   # Very low volume
    }[current_session()]
    
    return base_threshold * volatility_multiplier * session_multiplier
```

### **2. Volume-Adjusted Thresholds ❌**

**Our System:**
- Fixed $100k alert for BTC regardless of daily volume

**Institutional Systems:**
- Thresholds as **percentage of daily volume**
- Example: Alert when liquidation > 0.1% of 24h volume

```python
# Better approach
liquidation_threshold = daily_volume * 0.001  # 0.1% of daily volume
```

### **3. Contextual Intelligence ❌**

**Our System:**
- No consideration of:
  - Major news events
  - FOMC meetings
  - Options expiry
  - Futures rollover

**Institutional (Refinitiv, Bloomberg):**
```python
context_multipliers = {
    'fomc_day': 2.0,        # Double thresholds on Fed days
    'options_expiry': 1.5,  # 50% higher on expiry
    'quarter_end': 1.3,     # Month/Quarter end volatility
    'normal_day': 1.0
}
```

### **4. Machine Learning Adaptation ❌**

**Our System:**
- Static rules-based

**Institutional (Jump Trading, Citadel):**
- ML models that learn normal vs abnormal patterns
- Adaptive thresholds based on recent history
- Anomaly detection using isolation forests

```python
# Institutional ML approach
from sklearn.ensemble import IsolationForest

def is_anomalous_liquidation(value, recent_liquidations):
    model = IsolationForest(contamination=0.05)
    model.fit(recent_liquidations)
    return model.predict([[value]])[0] == -1
```

### **5. Cross-Asset Correlation ❌**

**Our System:**
- Each asset monitored independently

**Institutional:**
- Correlation matrices between assets
- If BTC has major liquidation, adjust ETH thresholds
- Risk contagion modeling

### **6. User Customization ❌**

**Our System:**
- No per-user settings
- No risk profiles

**Institutional (TradingView, Coinigy):**
```python
user_profiles = {
    'conservative': {'multiplier': 2.0},    # Less alerts
    'moderate': {'multiplier': 1.0},        # Normal
    'aggressive': {'multiplier': 0.5},      # More alerts
    'custom': {'btc': 50000, 'eth': 25000} # User-defined
}
```

## 📈 Recommended Improvements (Priority Order)

### **Phase 1: Quick Wins** (1 week)
1. **Use centralized config** - Point monitors to `alert_thresholds.py`
2. **Add session awareness:**
   ```python
   def get_session():
       hour_utc = datetime.utcnow().hour
       if 0 <= hour_utc < 8: return 'asian'
       elif 8 <= hour_utc < 16: return 'european'
       else: return 'us'
   ```

3. **Weekend adjustment:**
   ```python
   if datetime.utcnow().weekday() >= 5:  # Sat/Sun
       threshold *= 0.5  # Lower thresholds for weekends
   ```

### **Phase 2: Volume-Based** (2 weeks)
```python
class DynamicThresholds:
    def __init__(self):
        self.volume_cache = {}
        
    async def get_threshold(self, symbol):
        volume_24h = await self.get_24h_volume(symbol)
        base_pct = 0.001  # 0.1% of volume
        
        # Adjust for market cap
        if symbol == 'BTC':
            base_pct = 0.0005  # Lower for high cap
        elif symbol in ['PEPE', 'SHIB']:
            base_pct = 0.002   # Higher for meme coins
            
        return volume_24h * base_pct
```

### **Phase 3: ML-Based** (1 month)
```python
import numpy as np
from scipy import stats

class AdaptiveThresholds:
    def __init__(self, window=100):
        self.history = []
        self.window = window
        
    def should_alert(self, value):
        if len(self.history) < 30:
            return value > 100000  # Fallback
            
        # Z-score based anomaly
        mean = np.mean(self.history[-self.window:])
        std = np.std(self.history[-self.window:])
        z_score = (value - mean) / std
        
        return abs(z_score) > 3  # 3 standard deviations
```

### **Phase 4: User Customization** (2 months)
```python
# Database schema
user_settings = {
    'user_id': {
        'risk_profile': 'moderate',
        'custom_thresholds': {
            'BTC': {'liquidation': 75000, 'oi': 12},
            'ETH': {'liquidation': 40000, 'oi': 15}
        },
        'quiet_hours': {'start': 22, 'end': 7},
        'session_preferences': {
            'asian': False,  # No alerts during Asian session
            'european': True,
            'us': True
        }
    }
}
```

## 🎯 Institutional Features We're Missing

1. **Rate of Change Alerts** - Alert on acceleration, not just absolute values
2. **Composite Indicators** - Combine liquidation + OI + funding for signal
3. **Market Microstructure** - Order book imbalance detection
4. **Smart Money Tracking** - Separate retail vs institutional flows
5. **Predictive Alerts** - "Liquidation cascade likely in next 5 minutes"
6. **Risk Scoring** - Overall market risk score (1-10)
7. **Backtesting Framework** - Test threshold effectiveness historically

## 💡 Implementation Priority

**Immediate (This Week):**
- Fix monitors to use `alert_thresholds.py`
- Add weekend/session multipliers
- Add environment variable support for all thresholds

**Short Term (This Month):**
- Volume-based dynamic thresholds
- Basic user customization via commands
- Historical average comparisons

**Long Term (Quarter):**
- ML-based anomaly detection
- Cross-asset correlation
- Full user preference system with persistence

The current system is a **good MVP** but lacks the sophistication of institutional-grade monitoring that adapts to market conditions and user needs.