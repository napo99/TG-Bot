# 📊 TradingView-Style Liquidation Visualization

## ✅ EXACTLY Like Your Image!

Shows liquidations aggregated by time period with:
- **Top:** BTC price chart
- **Middle:** Volume bars
- **Bottom:** **Aggregated liquidation bars**
  - 🔴 **Red bars DOWN** = LONG liquidations (shorts won)
  - 🟢 **Green bars UP** = SHORT liquidations (longs won)

---

## 🚀 Usage

### **Basic Usage (Last 7 Days):**
```bash
python3 tradingview_style.py
```

### **Custom Time Period:**
```bash
# Last 24 hours
python3 tradingview_style.py 24

# Last 3 days
python3 tradingview_style.py 72

# Last 30 days
python3 tradingview_style.py 720
```

---

## 📈 What You'll See

```
================================================================================
📊 TRADINGVIEW-STYLE LIQUIDATION CHART
================================================================================

Time period: Last 168 hours (7 days)

Chart layout:
  📈 Top:    BTC Price
  📊 Middle: Volume
  📉 Bottom: Aggregated Liquidations
             🔴 Red bars = LONG liquidations
             🟢 Green bars = SHORT liquidations

================================================================================

📊 Fetching liquidation data for last 168 hours (7 days)...

✅ Loaded 168 hourly data points

📊 LIQUIDATION SUMMARY (7 days):
────────────────────────────────────────────────────────────
Total LONG liquidations:  $23,414,780 (63.7%)
Total SHORT liquidations: $13,328,110 (36.3%)
Total liquidations:       $36,742,890
────────────────────────────────────────────────────────────

🎨 Opening interactive chart in browser...

💾 Chart saved to: liquidations_tradingview_168h.html
```

**Interactive chart will open in your browser!**

---

## 📊 Chart Features

### **Top Panel: Price Chart**
- White line showing BTC price over time
- Synchronized with liquidation bars below
- Hover to see exact price at any time

### **Middle Panel: Volume**
- Gray bars showing total liquidation volume (BTC)
- Higher bars = more liquidation activity
- Hover to see exact BTC volume

### **Bottom Panel: Aggregated Liquidations** ⭐
**Exactly like TradingView liquidation heatmap!**

- **🔴 Red bars going DOWN:**
  - LONG liquidations (longs got liquidated)
  - Shorts won / Price went down
  - Negative values on Y-axis

- **🟢 Green bars going UP:**
  - SHORT liquidations (shorts got liquidated)
  - Longs won / Price went up
  - Positive values on Y-axis

- **Bar height = Total USD liquidated** in that hour
- **Hover to see:**
  - Exact time
  - USD amount
  - BTC amount
  - Exchange breakdown

---

## 🎯 Reading the Chart

### **Example Scenarios:**

**Scenario 1: Big Red Bar (LONG liquidations)**
```
Price:  📉 $109,000 → $107,000 (dropping)
Volume: 📊 High
Liq:    🔴 Large red bar DOWN (-$5.2M)

Meaning: Price dropped, LONGs got liquidated
         Shorts won, longs lost
```

**Scenario 2: Big Green Bar (SHORT liquidations)**
```
Price:  📈 $107,000 → $109,000 (rising)
Volume: 📊 High
Liq:    🟢 Large green bar UP (+$3.8M)

Meaning: Price rose, SHORTs got liquidated
         Longs won, shorts lost
```

**Scenario 3: Mixed Activity**
```
Price:  📊 Choppy/sideways
Volume: 📊 Medium
Liq:    🔴🟢 Both red and green bars

Meaning: Volatility, both sides getting liquidated
         No clear winner
```

---

## 📅 Aggregation Periods

**Current:** Hourly bars (1 hour per bar)

**To change aggregation period, edit the SQL in `tradingview_style.py`:**

```python
# Change this line:
time_bucket('1 hour', time) AS hour,

# To:
time_bucket('15 minutes', time) AS hour,  # 15-min bars
time_bucket('4 hours', time) AS hour,     # 4-hour bars
time_bucket('1 day', time) AS hour,       # Daily bars
```

---

## 🎨 Interactive Features

**The chart is fully interactive:**

✅ **Hover** - See exact values
✅ **Zoom** - Click and drag to zoom in
✅ **Pan** - Shift + drag to pan
✅ **Reset** - Double-click to reset view
✅ **Legend** - Click to show/hide data series
✅ **Save** - Automatically saved as HTML file

---

## 💡 Pro Tips

### **1. Spot Cascade Events**
Look for **tall bars** (large liquidations):
- Tall red bar = Major LONG cascade
- Tall green bar = Major SHORT cascade
- Multiple tall bars = Extreme volatility

### **2. Market Direction**
- **More red than green** = Downtrend (longs losing)
- **More green than red** = Uptrend (shorts losing)
- **Mixed** = Choppy/ranging market

### **3. Volume Confirmation**
High volume + large liq bar = **Strong move confirmed**

### **4. Time Analysis**
- Compare liquidations across different times
- Identify peak liquidation hours
- Spot recurring patterns

---

## 📊 Data Breakdown

**Each hourly bar shows:**

```json
{
  "time": "2025-01-21 17:00:00 UTC",
  "long_liquidations": -5200000,      // Red bar (negative)
  "short_liquidations": 1800000,      // Green bar (positive)
  "long_btc": 48.5200,                // BTC amount (longs)
  "short_btc": 16.7800,               // BTC amount (shorts)
  "binance_long": -3100000,           // Binance longs
  "bybit_long": -2100000,             // Bybit longs
  "binance_short": 1100000,           // Binance shorts
  "bybit_short": 700000,              // Bybit shorts
  "avg_price": 107234.50              // Avg BTC price
}
```

**All aggregated per hour (or your chosen time period)!**

---

## ✅ Requirements Met

Compared to your TradingView image:

- ✅ **Price at top** - Yes
- ✅ **Volume bars** - Yes
- ✅ **Aggregated liquidations** - Yes
- ✅ **Red = LONG liq (down)** - Yes
- ✅ **Green = SHORT liq (up)** - Yes
- ✅ **For any time period** - Yes
- ✅ **Interactive** - Yes
- ✅ **Hover details** - Yes
- ✅ **YYYYMMDD + UTC time** - Yes
- ✅ **Exchange breakdown** - Yes
- ✅ **BTC + USD values** - Yes

---

## 🚀 Quick Start

```bash
cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator

# Make sure aggregator is running and has collected some data
# (needs at least a few hours of data for meaningful chart)

# Create TradingView-style chart
python3 tradingview_style.py

# Or specify custom period
python3 tradingview_style.py 48  # Last 2 days
```

**Chart will open in your browser automatically! 📊**

---

## 📁 Saved Charts

Charts are automatically saved as HTML files:
- `liquidations_tradingview_168h.html` (7 days)
- `liquidations_tradingview_24h.html` (24 hours)
- etc.

**Open these files anytime in any browser!**

---

**This is EXACTLY the visualization style from your TradingView image! 🎯**
