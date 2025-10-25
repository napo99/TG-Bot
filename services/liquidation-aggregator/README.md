# 🚀 Multi-Exchange Liquidation Aggregator

**Phase 1:** Binance + Bybit | BTCUSDT | Multi-Level Storage Architecture

## 📋 Overview

Real-time liquidation tracking system with intelligent multi-level data storage:

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: In-Memory Ring Buffers (<100 µs latency)         │
│  • Last 60 seconds of events                                │
│  • Ultra-fast cascade detection                             │
│  • ~18KB per symbol                                         │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 2: Redis Aggregation (<1 ms latency)                │
│  • Price-level clusters ($100 levels for BTC)               │
│  • Time-bucketed aggregations (1-min buckets)               │
│  • Cascade status flags                                     │
│  • TTL: 1 hour auto-expire                                  │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 3: TimescaleDB Significant Events (50-100ms batch)  │
│  • Only institutional liquidations (>$100K)                 │
│  • Cascade events with risk scoring                         │
│  • Compression: 10x after 7 days                            │
│  • Retention: 90 days auto-delete                           │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 4: TimescaleDB Continuous Aggregates                │
│  • Hourly rollups                                           │
│  • Price-level heatmaps                                     │
│  • Exchange comparison                                      │
│  • Cascade analysis                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### **Core Capabilities:**
- ✅ **Multi-Exchange Support:** Binance + Bybit (Phase 1)
- ✅ **Real-Time Processing:** <100 microsecond hot path
- ✅ **Price-Level Aggregation:** $100 levels for BTC
- ✅ **Cross-Exchange Cascade Detection:** 6-factor risk analysis
- ✅ **Intelligent Storage:** Only meaningful events stored
- ✅ **Auto-Compression:** 10x space savings after 7 days
- ✅ **Auto-Retention:** 90-day auto-delete policy

### **Intelligence:**
- **6-Factor Cascade Risk Scoring:**
  1. Volume concentration
  2. Time compression (events per minute)
  3. Price clustering
  4. Side imbalance
  5. Institutional ratio
  6. Cross-exchange correlation

- **Institutional Filtering:**
  - Only tracks liquidations ≥$100K
  - Eliminates 99.9% of retail noise
  - Focuses on market-moving events

---

## 🛠️ Setup Instructions

### **Prerequisites:**
- Python 3.11+
- Redis
- PostgreSQL 17 + TimescaleDB 2.22+

### **1. Install Dependencies**

```bash
cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator

# Install Python dependencies
pip install -r requirements.txt
```

### **2. Verify Database Setup**

TimescaleDB should already be configured. Verify:

```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Verify TimescaleDB extension
psql liquidations -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';"
```

Expected output:
```
  extname   | extversion
------------+------------
 timescaledb | 2.22.1
```

### **3. Verify Redis**

```bash
# Check Redis is running
brew services list | grep redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG
```

### **4. Environment Configuration (Optional)**

Create `.env` file if you need custom configuration:

```bash
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_LIQ_DB=1  # Use DB 1 for liquidations (avoids conflicts)

# TimescaleDB configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=liquidations
DB_USER=screener-m3
DB_PASSWORD=

# Tracking configuration
TRACKED_SYMBOLS=BTCUSDT
INSTITUTIONAL_THRESHOLD_USD=100000
```

---

## 🚀 Running the Aggregator

### **Start the Aggregator:**

```bash
cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator

# Run the aggregator
python main.py
```

Expected output:
```
================================================================================
LIQUIDATION AGGREGATOR - PHASE 1
Exchanges: Binance + Bybit | Symbol: BTCUSDT
Multi-Level Storage: In-Memory → Redis → TimescaleDB
================================================================================
2025-10-21 10:30:00 - main - INFO - 🚀 Initializing Liquidation Aggregator...
2025-10-21 10:30:00 - main - INFO - ✅ Redis connected (DB 1, prefix: liq:)
2025-10-21 10:30:00 - main - INFO - ✅ TimescaleDB connected
2025-10-21 10:30:00 - main - INFO - ✅ Background database writer started
2025-10-21 10:30:00 - main - INFO - 🎯 Liquidation Aggregator ready!
2025-10-21 10:30:00 - aggregator - INFO - Starting 2 exchange streams...
2025-10-21 10:30:01 - binance - INFO - ✅ Connected to Binance liquidation stream
2025-10-21 10:30:01 - bybit - INFO - ✅ Connected to Bybit liquidation stream
2025-10-21 10:30:01 - bybit - INFO - Subscribed to Bybit liquidations for BTCUSDT
```

### **Monitor Real-Time Events:**

When liquidations occur, you'll see:
```
2025-10-21 10:35:15 - main - INFO - 💰 INSTITUTIONAL: BINANCE BTCUSDT LONG $168,086 @ $67,234.50
2025-10-21 10:35:20 - cascade_detector - WARNING - 🚨 CROSS-EXCHANGE CASCADE DETECTED: BTCUSDT | 7 liquidations | $875,200 | Risk: 1.45 | Exchanges: binance, bybit
2025-10-21 10:36:00 - main - INFO - 📊 STATS: Processed: 145 | Institutional: 12 | Cascades: 2 | Events/sec: 2.42 | Price levels: 8 | DB writes: 12
```

---

## 📊 Data Analysis & Visualization

### **Option 1: Real-Time Terminal Dashboard (NEW!)**

```bash
# Visual real-time monitoring in terminal
python3 visual_monitor.py
```

Shows **live updating charts** in your terminal:
- ⏱️ **Timeline**: 10-minute buckets showing volume evolution
- 📊 **Latest 10 liquidations**: Real-time event stream with timestamps
- 🏦 **Exchange comparison**: Bar charts comparing Binance vs Bybit
- 📈 **Statistics**: Total events, USD volume, cascade count

**Updates every 10 seconds** with beautiful colored terminal output!

---

### **Option 2: Interactive Jupyter Notebooks**

**A) Time-Series Visual Analysis (NEW!):**
```bash
# Beautiful interactive charts showing evolution over time
jupyter notebook analysis_visual.ipynb
```

Provides **7 interactive visualizations**:
1. 💰 **Volume Evolution**: Line charts showing liquidation volume over time
2. 🔥 **Daily Heatmap**: When liquidations happen (day × hour)
3. ⚡ **Cascade Timeline**: Scatter plot of cascade events with risk scores
4. 📉 **Long vs Short**: Comparison of liquidation sides over time
5. 🏦 **Market Share**: Exchange dominance evolution
6. 📅 **Daily Summary**: Multi-panel view (USD, BTC, event count)
7. 📈 **Cumulative Volume**: Total liquidations accumulated over time

**B) Data Analysis (Original):**
```bash
# Detailed data exploration
jupyter notebook analysis.ipynb
```

Provides:
- Price-level heatmaps
- Cascade analysis
- Exchange comparison
- Time series visualizations
- Real-time cascade status

---

### **Option 3: Direct Database Queries**

```bash
# Connect to database
psql liquidations

# Get recent significant liquidations
SELECT time, exchange, symbol, side, value_usd, is_cascade, risk_score
FROM liquidations_significant
WHERE time >= NOW() - INTERVAL '1 hour'
ORDER BY value_usd DESC
LIMIT 10;

# Get price level clusters
SELECT * FROM get_price_level_clusters('BTCUSDT', 4);

# Get hourly rollups
SELECT * FROM liquidations_hourly
WHERE hour >= NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;

# Get cascade events
SELECT * FROM liquidation_cascades
WHERE hour >= NOW() - INTERVAL '24 hours'
ORDER BY total_value_usd DESC;
```

### **Option 3: Redis Inspection**

```bash
# Connect to Redis
redis-cli -n 1

# List all liquidation keys
KEYS liq:*

# Get price level cluster
HGETALL liq:levels:BTCUSDT:67200:LONG

# Get time bucket aggregation
HGETALL liq:agg:BTCUSDT:60s:1729512000000

# Get cascade status
HGETALL liq:cascade:status:BTCUSDT
```

---

## 🎯 What Gets Stored

### **Level 1 (In-Memory):**
- **All events** (last 60 seconds only)
- Automatically dropped after 60s
- Used for real-time cascade detection

### **Level 2 (Redis):**
- **Price-level clusters** (e.g., "15 liquidations at $67,200 level")
- **Time-bucketed aggregations** (1-minute summaries)
- **Cascade status flags**
- TTL: 1 hour (auto-expire)

### **Level 3 (TimescaleDB Significant Events):**
- **Only institutional liquidations** (≥$100K)
- **Cascade events** with full context
- Compressed after 7 days (10x savings)
- Auto-deleted after 90 days

### **Level 4 (TimescaleDB Continuous Aggregates):**
- **Hourly rollups** (pre-computed summaries)
- **Price-level heatmaps** (where liquidations cluster)
- **Exchange comparison** (volume breakdown)
- **Cascade analysis** (cascade patterns)
- Retention: 1 year

---

## 📈 Storage Estimates

**For BTCUSDT with typical liquidation activity:**

| Level | Storage | Retention | Notes |
|-------|---------|-----------|-------|
| L1: In-Memory | ~18 KB | 60 seconds | Ring buffer, automatic |
| L2: Redis | ~1-5 MB | 1 hour | TTL auto-expire |
| L3: Significant Events | ~100 MB/month | 90 days | Compressed 10x |
| L4: Continuous Aggregates | ~10 MB/month | 1 year | Pre-computed |

**Result:** ~99.9% storage reduction vs storing all events

---

## 🔧 Troubleshooting

### **Issue: Redis connection refused**
```bash
# Start Redis
brew services start redis

# Verify it's running
redis-cli ping
```

### **Issue: Database connection error**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Restart if needed
brew services restart postgresql@17

# Verify TimescaleDB extension
psql liquidations -c "SELECT extname FROM pg_extension;"
```

### **Issue: No data appearing**
- Check aggregator is running: `ps aux | grep main.py`
- Check logs: `tail -f liquidations.log`
- Verify WebSocket connections are active (check logs for "Connected to...")
- Check if BTCUSDT is actively trading (may be low liquidation periods)

### **Issue: "Module not found" errors**
```bash
# Make sure you're in the correct directory
cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator

# Install dependencies
pip install -r requirements.txt
```

---

## 🎓 Understanding the Data

### **What is a "Price Level"?**
Price levels are rounded price points where liquidations cluster. For BTC, we round to $100 levels.

Example:
- Liquidations at $67,234, $67,245, $67,289 → All counted at $67,200 level
- This reveals "support/resistance" levels where leverage is concentrated

### **What is a "Cascade"?**
A cascade occurs when:
1. **5+ liquidations** in 60 seconds
2. **Total value ≥$100K**
3. Often triggers more liquidations as price moves

**Cross-exchange cascades** (occurring on both Binance AND Bybit simultaneously) indicate systemic risk.

### **What is the "Risk Score"?**
A composite score (0.0 to 2.0+) combining:
- Volume concentration (how much is being liquidated)
- Time compression (how fast)
- Price clustering (how focused)
- Side imbalance (all longs or all shorts)
- Institutional ratio (large liquidations)
- Cross-exchange correlation (systemic risk)

**Risk Score Interpretation:**
- `0.0 - 0.7`: Low risk, normal liquidations
- `0.7 - 1.0`: Moderate risk, watch for continuation
- `1.0 - 1.5`: High risk, cascade likely
- `1.5 - 2.0+`: Extreme risk, major cascade event

---

## 📋 Phase 2 Roadmap

- [ ] Add ETHUSDT tracking
- [ ] Add SOLUSDT tracking
- [ ] Expand to 3 more exchanges (Bitfinex, Bitmex, Gate.io)
- [ ] Add 7 more symbols (BNB, ARB, MATIC, AVAX, OP, LINK, UNI)
- [ ] Web dashboard (optional)
- [ ] Machine learning cascade prediction (optional)

---

## 🤝 Questions?

For issues or questions:
1. Check logs: `tail -f liquidations.log`
2. Verify database schema: `psql liquidations -c "\d liquidations_significant"`
3. Check Redis keys: `redis-cli -n 1 KEYS liq:*`
4. Review Jupyter notebook for data analysis examples

---

## 📄 License

Part of the Crypto Assistant project.

---

**Ready to track institutional liquidations in real-time! 🚀**
