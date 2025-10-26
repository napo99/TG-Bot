# 📊 SNAPSHOT vs ACCUMULATED DATA

## Understanding the Two Views

### **🔄 SNAPSHOT (Rolling Window)**
- Shows **last 60 minutes** only
- Updates every 10 seconds
- Old data "falls off" as time passes
- **Use case:** See recent activity, detect current cascades

### **📈 ACCUMULATED (Cumulative Totals)**
- Shows **all-time totals** since system started
- Keeps growing as more liquidations occur
- Never "falls off" (stored permanently in database)
- **Use case:** Track long-term trends, total volumes, historical analysis

---

## 🎯 BOTH ARE TRACKED!

**Your system tracks BOTH:**

| View | Where | Time Range | Updates |
|------|-------|------------|---------|
| **Snapshot** | `visual_monitor.py` | Last 60 min | Every 10s |
| **Accumulated** | TimescaleDB + `accumulated_stats.py` | Since start | Permanent |

---

## 📊 HOW TO VIEW EACH

### **SNAPSHOT VIEW (Last 60 Minutes)**

```bash
# Real-time rolling window (last 60 min)
python3 visual_monitor.py
```

**Shows:**
```
📈 LAST 60 MINUTES - TOTAL:
Total Liquidations: 23 events | Total BTC: 8.2450 BTC | Total USD: $883,415
                    ↑ Only last 60 minutes
```

---

### **ACCUMULATED VIEW (All-Time Totals)**

```bash
# Cumulative totals since system started
python3 accumulated_stats.py
```

**Shows:**
```
📊 ACCUMULATED LIQUIDATION STATISTICS (Since System Started)

📅 DATA COLLECTION PERIOD:
First Liquidation: 20250120 10:30:00 UTC
Last Liquidation:  20250121 17:45:00 UTC
Duration:          1 days, 7 hours, 15 minutes

🌍 GRAND TOTALS (ALL EXCHANGES):
Total Liquidations:    1,247 events     ← ACCUMULATED (not rolling)
Total BTC Liquidated:  342.5820 BTC     ← ACCUMULATED
Total USD Liquidated:  $36,742,890      ← ACCUMULATED
Total Cascades:        47

📊 LONG vs SHORT BREAKDOWN (Accumulated):
🔻 LONG Liquidations:
   Events: 797 | BTC: 218.3200 | USD: $23,414,780 | Share: 63.7%

🔺 SHORT Liquidations:
   Events: 450 | BTC: 124.2620 | USD: $13,328,110 | Share: 36.3%

🏦 EXCHANGE BREAKDOWN (Accumulated):
📊 BINANCE:
   Total: 742 events | 203.4520 BTC | $21,820,440 | Share: 59.4%
   ├─ LONG:  485 events | 132.8920 BTC | $14,251,200
   └─ SHORT: 257 events | 70.5600 BTC | $7,569,240

📊 BYBIT:
   Total: 505 events | 139.1300 BTC | $14,922,450 | Share: 40.6%
   ├─ LONG:  312 events | 85.4280 BTC | $9,163,580
   └─ SHORT: 193 events | 53.7020 BTC | $5,758,870
```

---

## 📈 JUPYTER NOTEBOOK (Both Views)

```bash
jupyter notebook analysis_visual.ipynb
```

**Has BOTH:**
1. **Chart 1-6:** Recent trends (last 7 days)
2. **Chart 7:** **Cumulative volume** (accumulated over time)

---

## 🔍 SQL QUERIES

### **Snapshot (Last 60 Minutes):**
```sql
SELECT
    COUNT(*) as events,
    SUM(quantity) as btc,
    SUM(value_usd) as usd
FROM liquidations_significant
WHERE time >= NOW() - INTERVAL '60 minutes';  ← Rolling window
```

### **Accumulated (All-Time):**
```sql
SELECT
    COUNT(*) as events,
    SUM(quantity) as btc,
    SUM(value_usd) as usd
FROM liquidations_significant;  ← No time filter = ALL data
```

### **Accumulated by Date (Daily Cumulative):**
```sql
SELECT
    DATE(time) as date,
    COUNT(*) as daily_events,
    SUM(quantity) as daily_btc,
    SUM(value_usd) as daily_usd,

    -- Running cumulative total
    SUM(COUNT(*)) OVER (ORDER BY DATE(time)) as cumulative_events,
    SUM(SUM(quantity)) OVER (ORDER BY DATE(time)) as cumulative_btc,
    SUM(SUM(value_usd)) OVER (ORDER BY DATE(time)) as cumulative_usd
FROM liquidations_significant
GROUP BY DATE(time)
ORDER BY date;
```

**Result:**
```
date       | daily_events | daily_btc  | daily_usd     | cumulative_events | cumulative_btc | cumulative_usd
-----------|--------------|------------|---------------|-------------------|----------------|----------------
2025-01-20 |     342      |  95.2400   | $10,213,080   |        342        |    95.2400     | $10,213,080
2025-01-21 |     905      | 247.3420   | $26,529,810   |      1,247        |   342.5820     | $36,742,890
                                                         ↑ Keeps growing!    ↑ Accumulates
```

---

## ✅ SUMMARY

**Question: "Are these just snapshots?"**

**Answer: You have BOTH!**

1. **Snapshot view** (rolling 60-min window):
   - Terminal monitor: `python3 visual_monitor.py`
   - Shows recent activity
   - Updates every 10 seconds

2. **Accumulated view** (all-time cumulative):
   - Database: All data in TimescaleDB
   - Script: `python3 accumulated_stats.py`
   - Jupyter: Chart 7 (Cumulative Volume)
   - SQL: No time filter queries

**Both track:**
- ✅ LONG liquidations (separate)
- ✅ SHORT liquidations (separate)
- ✅ Exchange totals (Binance vs Bybit)
- ✅ Percentage shares
- ✅ BTC amounts
- ✅ USD values
- ✅ Date (YYYYMMDD) and Time (UTC)

---

## 🚀 Quick Reference

| What You Want | Command |
|---------------|---------|
| **Recent activity (last 60 min)** | `python3 visual_monitor.py` |
| **All-time totals** | `python3 accumulated_stats.py` |
| **Visual charts** | `jupyter notebook analysis_visual.ipynb` |
| **Custom queries** | `psql liquidations` |

**Both snapshot AND accumulated data are fully tracked! 📊**
