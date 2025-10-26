# Monitoring & Visualization Guide

## 🖥️ **Three Ways to Monitor Liquidations**

### 1. **Simple Dashboard** (Recommended for Quick View)
```bash
python simple_dashboard.py
```

**Shows:**
- ✅ **Works immediately** (uses Redis, not database)
- 📊 Overall statistics (count, value, averages)
- 🔴🟢 Long vs Short breakdown
- 🏦 Exchange comparison (Binance vs Bybit)
- ⏱️ Recent activity timeline (last 10 minutes)
- 💰 Top price level clusters

**Refreshes:** Every 5 seconds

**Purpose:** Quick real-time overview without database dependency

---

### 2. **Visual Monitor** (Detailed Real-Time View)
```bash
python visual_monitor.py
```

**Shows:**
- ✅ Real-time data from TimescaleDB
- 📊 Last 60 minutes aggregated stats
- 🔴🟢 Long vs Short with BTC amounts
- 🏦 Exchange breakdown with percentages
- ⏱️ Timeline by 10-minute buckets
- 📋 Latest 10 individual liquidations with full details
  - Date, Time, Exchange, Side, Amount, USD Value, Price

**Refreshes:** Every 10 seconds

**Purpose:** Detailed monitoring with individual event tracking

**Requirements:** TimescaleDB with data

---

### 3. **TradingView-Style Chart** (Historical Analysis)
```bash
python tradingview_style.py [hours]
```

**Examples:**
```bash
python tradingview_style.py 24    # Last 24 hours
python tradingview_style.py 168   # Last 7 days (default)
```

**Shows:**
- ✅ Interactive Plotly chart in browser
- 📈 Price chart (top panel)
- 📊 Volume chart (middle panel)
- 📉 Liquidation bars (bottom panel)
  - 🔴 Red bars = LONG liquidations (downward)
  - 🟢 Green bars = SHORT liquidations (upward)

**Refreshes:** On-demand (not real-time)

**Purpose:** Historical analysis and backtesting

**Requirements:** TimescaleDB with historical data

---

## 📊 **Data Inspection Tool**

```bash
python check_data.py
```

**Shows:**
- ✅ Works with Redis data
- 📊 Aggregated liquidations by 60-second windows
- 💰 Price level accumulation
- 📈 Overall statistics
- ⏰ Recent activity check

**Purpose:** Quick data verification and debugging

---

## 🔧 **Monitoring Setup Recommendations**

### **Terminal Layout (4 terminals):**

```
┌─────────────────────────┬─────────────────────────┐
│                         │                         │
│  Terminal 1:            │  Terminal 2:            │
│  python main.py         │  python visual_monitor  │
│  (Data Collection)      │  (Detailed View)        │
│                         │                         │
├─────────────────────────┼─────────────────────────┤
│                         │                         │
│  Terminal 3:            │  Terminal 4:            │
│  python simple_dash.py  │  python check_data.py   │
│  (Quick Overview)       │  (On-demand checks)     │
│                         │                         │
└─────────────────────────┴─────────────────────────┘
```

**Or simplified 3-terminal setup:**
```
┌─────────────────────────┬─────────────────────────┐
│                         │                         │
│  Terminal 1:            │  Terminal 2:            │
│  python main.py         │  python simple_dash.py  │
│  (Data Collection)      │  (Dashboard)            │
│                         │                         │
│                         │                         │
└─────────────────────────┴─────────────────────────┘
```

---

## 🎯 **Which Monitor to Use?**

| Scenario | Recommended Tool |
|----------|------------------|
| **Quick check** | `simple_dashboard.py` |
| **Detailed monitoring** | `visual_monitor.py` |
| **Historical analysis** | `tradingview_style.py` |
| **Data verification** | `check_data.py` |
| **First-time setup** | `simple_dashboard.py` (works immediately) |
| **Production monitoring** | `visual_monitor.py` |

---

## ⚠️ **Current Issues & Fixes**

### **Issue 1: visual_monitor.py KeyError: 'price'** ✅ FIXED
- **Problem:** Query didn't SELECT price field
- **Fix:** Added `price` to SELECT statement
- **Status:** ✅ Fixed in latest version

### **Issue 2: tradingview_style.py "No data available"**
- **Problem:** Requires historical data in TimescaleDB
- **Solution:** Wait for data to accumulate OR use `simple_dashboard.py`
- **Note:** System now saves ALL liquidations (not just $100K+)

### **Issue 3: Redis WRONGTYPE errors** ✅ FIXED
- **Problem:** Key type mismatch in cluster query
- **Fix:** Simplified cluster counting in main.py
- **Status:** ✅ Won't see these errors anymore

---

## 📝 **Data Flow**

```
Exchange WebSocket
        ↓
   main.py (core_engine.py)
        ↓
   ┌────┴────┬──────────┬────────────┐
   ↓         ↓          ↓            ↓
In-Memory  Redis   TimescaleDB   Logging
(buffer)  (cache)  (permanent)  (console)
   ↓         ↓          ↓
   └────┬────┴──────────┘
        ↓
  Visualization Tools
  - simple_dashboard.py → Redis
  - visual_monitor.py → TimescaleDB
  - tradingview_style.py → TimescaleDB
  - check_data.py → Redis
```

---

## 🚀 **Quick Start**

1. **Start data collection:**
   ```bash
   python main.py
   ```

2. **Open dashboard in new terminal:**
   ```bash
   python simple_dashboard.py
   ```

3. **Wait for data to appear** (~30 seconds)

4. **Check data anytime:**
   ```bash
   python check_data.py
   ```

---

## 📊 **Example Outputs**

### simple_dashboard.py:
```
📈 OVERALL STATISTICS
─────────────────────────────────────────
Total Liquidations: 82 events
Total Value:        $425,161.13
Average Size:       $5,184.89
─────────────────────────────────────────

📊 LONG vs SHORT
─────────────────────────────────────────
🔻 LONGS:  ██████████████████████████       37 (45.1%)
🔺 SHORTS: ████████████████████████████████ 45 (54.9%)
```

### visual_monitor.py:
```
📋 LATEST 10 LIQUIDATIONS (Real-Time from Exchanges):
─────────────────────────────────────────────────────
Date       | Time (UTC) | Exchange | Side  | Amount (BTC)  | USD Value       | Price
20251021   | 23:29:15   | BINANCE  | LONG  |     0.9000    | $102,258        | $113,620.00 | 🚨
20251021   | 23:29:10   | BYBIT    | SHORT |     0.4500    | $51,129         | $113,620.00 |
```

---

Generated: 2025-10-21
