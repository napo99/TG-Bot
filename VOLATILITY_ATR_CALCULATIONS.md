# Volatility and ATR Calculations Explained

## 📊 **15-Minute Volatility Calculation**

### **What It Measures**
The 15-minute volatility measures **price movement within the current 15-minute candle only** - showing how much the price fluctuated during that specific timeframe.

### **Calculation Method**
```python
def calculate_current_volatility(ohlcv_data):
    current_candle = ohlcv_data[-1]  # Get the latest 15m candle
    timestamp, open_price, high, low, close, volume = current_candle
    
    # Calculate volatility as percentage of price range relative to open
    volatility = ((high - low) / open_price) * 100
    return round(volatility, 2)
```

### **Formula Breakdown**
```
Volatility = ((High - Low) / Open) × 100

Example with BTC:
- Open: $104,000
- High: $104,500  
- Low: $103,800
- Volatility = ((104,500 - 103,800) / 104,000) × 100 = 0.67%
```

### **Time Period: SINGLE 15-MINUTE CANDLE**
- **Data Source**: Current 15-minute candle only
- **Real-time**: Updates every 15 minutes with new candle data
- **Purpose**: Shows immediate price action volatility within the timeframe

## 📈 **ATR (Average True Range) Calculation**

### **What It Measures**
ATR measures **average price movement over multiple periods** - showing typical price range you can expect over recent trading sessions.

### **Calculation Method**
```python
def calculate_atr(high, low, close, period=14):
    true_ranges = []
    
    # Calculate True Range for each candle
    for i in range(1, len(close)):
        tr1 = high[i] - low[i]                    # Current H-L
        tr2 = abs(high[i] - close[i-1])          # Current H - Previous Close  
        tr3 = abs(low[i] - close[i-1])           # Current L - Previous Close
        
        true_range = max(tr1, tr2, tr3)          # Take the largest
        true_ranges.append(true_range)
    
    # Average the last 14 True Ranges
    atr = np.mean(true_ranges[-period:])
    return atr
```

### **True Range Components**
For each candle, True Range is the **maximum** of:
1. **Current High - Current Low** (normal range)
2. **Current High - Previous Close** (gap up scenarios)
3. **Current Low - Previous Close** (gap down scenarios)

### **Example ATR Calculation**
```
Period: 14 candles (default)
Recent True Ranges: [450, 380, 520, 290, 410, 350, 480, 320, 390, 430, 370, 460, 340, 400]
ATR = Average of these 14 values = $399

This means: "On average, price moves $399 in a 15-minute period"
```

### **Time Period: 14 CANDLES (3.5 HOURS)**
- **Data Source**: Last 14 × 15-minute candles = 3.5 hours of data
- **Rolling Window**: Updates with each new candle, dropping the oldest
- **Purpose**: Shows typical price movement magnitude over recent sessions

## 🔄 **Key Differences**

| Metric | Time Scope | Purpose | Example Value |
|--------|------------|---------|---------------|
| **15m Volatility** | Single candle (15 min) | Current price action | 0.47% |
| **ATR** | 14 candles (3.5 hours) | Average movement | $399 |

## 📊 **Practical Applications**

### **15m Volatility Usage**
- **Scalping**: Higher volatility = more trading opportunities
- **Entry/Exit**: Low volatility may signal consolidation
- **Risk Assessment**: High volatility = increased position risk

### **ATR Usage**  
- **Stop Loss Placement**: Set stops at 1-2× ATR from entry
- **Position Sizing**: Larger ATR = smaller position size
- **Profit Targets**: Expected move distance for swing trades

## 🎯 **Real-Time Example**

### **Current BTC Analysis**
```
Price: $104,400.10
15m Volatility: 0.47%
ATR: $399

Interpretation:
• Current 15m candle shows 0.47% price movement
• Typical price movement averages $399 over 3.5 hours  
• Relatively low current volatility vs average movement
• Suggests consolidation phase within normal range
```

## ⚙️ **Technical Implementation**

### **Data Requirements**
- **15m Volatility**: Needs current OHLC candle data
- **ATR**: Needs minimum 15 candles (14 for calculation + 1 for previous close)

### **Update Frequency**
- **15m Volatility**: Updates every 15 minutes with new candle
- **ATR**: Updates every 15 minutes but reflects 3.5-hour average

### **Accuracy Considerations**
- **Market Hours**: More accurate during active trading sessions
- **Weekend/Holiday**: May show reduced volatility during low liquidity
- **News Events**: Volatility spikes during major announcements

## 📈 **Comparison with Other Timeframes**

| Timeframe | Volatility Scope | ATR Period (14 candles) |
|-----------|------------------|-------------------------|
| **1m** | 1 minute | 14 minutes |
| **5m** | 5 minutes | 70 minutes (1.2 hours) |
| **15m** | 15 minutes | 210 minutes (3.5 hours) |
| **1h** | 1 hour | 14 hours |
| **4h** | 4 hours | 56 hours (2.3 days) |

The 15-minute timeframe provides a good balance between:
- **Responsiveness**: Captures intraday price action
- **Stability**: Smooths out noise from very short timeframes
- **Relevance**: Useful for both scalping and swing trading strategies

This combination gives traders both **immediate volatility context** (current 15m) and **historical movement baseline** (14-period ATR) for informed decision-making.