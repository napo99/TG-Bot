# 🚀 LIQUIDATION TRACKER - QUICK REFERENCE CARD

## ⚡ COMMANDS

| Command | What It Does | Updates |
|---------|--------------|---------|
| `python3 main.py` | **Start data collection** | Continuous |
| `python3 visual_monitor.py` | **Real-time dashboard** (60 min snapshot) | Every 10s |
| `python3 accumulated_stats.py` | **All-time totals** (cumulative) | On demand |
| `python3 tradingview_style.py` | **TradingView chart** (price + liq bars) | On demand |
| `jupyter notebook analysis_visual.ipynb` | **7 interactive charts** | On demand |

---

## 📊 WHAT EACH TOOL SHOWS

### **visual_monitor.py** (Real-Time Snapshot)
```
📈 LAST 60 MINUTES
├─ Total events, BTC, USD
├─ LONG vs SHORT breakdown (%, BTC, USD)
├─ Exchange breakdown (Binance vs Bybit, %)
├─ Timeline (10-min buckets)
└─ Latest 10 liquidations (YYYYMMDD, UTC)
```
**Use when:** Watching market in real-time

---

### **accumulated_stats.py** (All-Time Cumulative)
```
🌍 SINCE SYSTEM STARTED
├─ Grand totals (events, BTC, USD)
├─ LONG vs SHORT (accumulated %)
├─ Exchange breakdown (accumulated %)
├─ Duration (days, hours)
└─ Average rates (per hour)
```
**Use when:** Checking total volumes

---

### **tradingview_style.py** (Interactive Chart)
```
📊 TRADINGVIEW-STYLE CHART
├─ Top: BTC price line
├─ Middle: Volume bars
└─ Bottom: Liquidation bars
    ├─ 🔴 Red DOWN = LONG liquidations
    └─ 🟢 Green UP = SHORT liquidations
```
**Use when:** Visual analysis, presentations

**Time periods:**
```bash
python3 tradingview_style.py 24   # Last 24 hours
python3 tradingview_style.py 168  # Last 7 days (default)
python3 tradingview_style.py 720  # Last 30 days
```

---

## 🎯 DATA TRACKED (ALL TOOLS)

| Data Point | Format | Example |
|------------|--------|---------|
| **Date** | YYYYMMDD | 20250121 |
| **Time** | HH:MM:SS UTC | 17:45:23 |
| **Exchange** | binance/bybit | binance |
| **Side** | LONG/SHORT | LONG |
| **BTC Amount** | Float | 1.0050 BTC |
| **USD Value** | Float | $107,836 |
| **Price** | Float | $107,299 |

---

## 📁 FILE LOCATIONS

```
/Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator/
├── main.py                   ← Data collection
├── visual_monitor.py         ← Real-time dashboard
├── accumulated_stats.py      ← Cumulative totals
├── tradingview_style.py      ← TradingView chart
├── analysis_visual.ipynb     ← 7 interactive charts
└── *.html                    ← Saved charts (auto-generated)
```

---

## 🔍 SQL QUICK QUERIES

```bash
psql liquidations
```

**Recent liquidations (last hour):**
```sql
SELECT time, exchange, side, quantity, value_usd, price
FROM liquidations_significant
WHERE time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC LIMIT 20;
```

**Accumulated by exchange:**
```sql
SELECT
    exchange,
    COUNT(*) as events,
    SUM(quantity) as btc,
    SUM(value_usd) as usd,
    COUNT(*) FILTER (WHERE side = 'LONG') as long_count,
    COUNT(*) FILTER (WHERE side = 'SHORT') as short_count
FROM liquidations_significant
GROUP BY exchange;
```

**Daily totals:**
```sql
SELECT
    DATE(time) as day,
    COUNT(*) as events,
    SUM(quantity) as btc,
    SUM(value_usd) as usd
FROM liquidations_significant
GROUP BY day
ORDER BY day DESC;
```

---

## 📊 REDIS INSPECTION

```bash
redis-cli -n 1  # Connect to DB 1
```

**Check liquidation data:**
```
KEYS liq:*                                  # List all liquidation keys
HGETALL liq:levels:BTCUSDT:107200:LONG     # Get price level cluster
HGETALL liq:agg:BTCUSDT:60s:1737479400000  # Get time bucket
HGETALL liq:cascade:status:BTCUSDT         # Get cascade status
```

---

## 🎨 CHART TYPES

| Visualization | Tool | Interactive | Saved |
|---------------|------|-------------|-------|
| **Terminal Dashboard** | `visual_monitor.py` | No | No |
| **TradingView Bars** | `tradingview_style.py` | Yes | HTML |
| **7 Time-Series Charts** | `analysis_visual.ipynb` | Yes | Notebook |
| **Custom Analysis** | SQL/Jupyter | Varies | Yes |

---

## ⚙️ SYSTEM STATUS CHECKS

**Check if data collection is running:**
```bash
ps aux | grep main.py
```

**Check database:**
```bash
psql liquidations -c "SELECT COUNT(*) FROM liquidations_significant;"
```

**Check Redis:**
```bash
redis-cli -n 1 KEYS liq:* | wc -l
```

**Check services:**
```bash
brew services list | grep -E 'postgresql|redis'
```

---

## 🔧 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| **No data showing** | Wait for liquidations (≥$100K only) |
| **Database connection error** | `brew services restart postgresql@17` |
| **Redis connection error** | `brew services start redis` |
| **No recent data** | Check if `main.py` is running |
| **Import errors** | `pip3 install -r requirements.txt` |

---

## 💡 PRO TIPS

1. **Leave `main.py` running 24/7** for continuous data collection
2. **Use `tradingview_style.py`** for best visualization
3. **Check `accumulated_stats.py`** daily for totals
4. **Run Jupyter notebooks** for deep analysis
5. **Only ≥$100K liquidations** are stored (institutional only)

---

## 🎯 QUICK WORKFLOWS

### **Daily Check:**
```bash
python3 accumulated_stats.py
python3 tradingview_style.py 24
```

### **Real-Time Monitoring:**
```bash
# Terminal 1
python3 main.py

# Terminal 2
python3 visual_monitor.py
```

### **Analysis Session:**
```bash
python3 tradingview_style.py 168
jupyter notebook analysis_visual.ipynb
```

---

**Keep this card handy for quick reference! 📋**
