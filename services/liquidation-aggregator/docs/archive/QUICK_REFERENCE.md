# 📊 QUICK REFERENCE: Liquidation Data Access

## ✅ YES - Everything is Aggregated by Exchange!

### **What You Get:**

For **EACH exchange** (Binance & Bybit), you get:
- ✅ **Coin amounts** (e.g., 2.5 BTC)
- ✅ **USD values** (e.g., $168,086.25)
- ✅ **Per-exchange totals**
- ✅ **Cross-exchange totals**
- ✅ **Price level clustering**

---

## 📈 Data Breakdown by Exchange

### **Example Output When System Runs:**

```
💰 INSTITUTIONAL: BINANCE BTCUSDT LONG $168,086.25 @ $67,234.50
   Coin Amount: 2.5000 BTC
   USD Value: $168,086.25
   Exchange: BINANCE
   Price Level: $67,200

💰 INSTITUTIONAL: BYBIT BTCUSDT LONG $121,050.00 @ $67,250.00
   Coin Amount: 1.8000 BTC
   USD Value: $121,050.00
   Exchange: BYBIT
   Price Level: $67,200

🚨 CROSS-EXCHANGE CASCADE DETECTED:
   Total Coins: 4.3 BTC
   Total USD: $289,136.25
   Exchanges: [binance, bybit]
   Price Level: $67,200
```

---

## 🔍 Query Examples

### **1. Get Recent Liquidations by Exchange:**

```sql
-- Binance only
SELECT time, exchange, side,
       quantity as btc_amount,  -- ← COIN AMOUNT
       value_usd                -- ← USD AMOUNT
FROM liquidations_significant
WHERE exchange = 'binance'
  AND time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC;

-- Bybit only
SELECT time, exchange, side,
       quantity as btc_amount,
       value_usd
FROM liquidations_significant
WHERE exchange = 'bybit'
  AND time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC;
```

**Results:**
```
time                 | exchange | side  | btc_amount | value_usd
---------------------|----------|-------|------------|------------
2025-10-21 10:35:00 | binance  | LONG  |   2.5000   | $168,086.25
2025-10-21 10:34:00 | binance  | SHORT |   1.8000   | $121,050.00
```

---

### **2. Aggregate Totals by Exchange:**

```sql
SELECT
    exchange,
    COUNT(*) as liquidations,
    SUM(quantity) as total_btc,      -- ← TOTAL COINS
    SUM(value_usd) as total_usd,     -- ← TOTAL USD
    AVG(value_usd) as avg_usd
FROM liquidations_significant
WHERE time >= NOW() - INTERVAL '24 hours'
GROUP BY exchange
ORDER BY total_usd DESC;
```

**Results:**
```
exchange | liquidations | total_btc  | total_usd      | avg_usd
---------|--------------|------------|----------------|------------
binance  |     45       | 125.50 BTC | $8,435,250.00 | $187,450.00
bybit    |     28       |  78.20 BTC | $5,260,340.00 | $187,869.29
```

---

### **3. Price Level Clusters (from Redis):**

```python
import redis
r = redis.Redis(host='localhost', port=6379, db=1)

# Get all price levels
for key in r.scan_iter(match='liq:levels:BTCUSDT:*:*'):
    data = r.hgetall(key)
    price_level = key.decode().split(':')[2]
    side = key.decode().split(':')[3]
    exchanges_key = f"{key.decode()}:exchanges"
    exchanges = r.smembers(exchanges_key)

    print(f"\nPrice Level: ${price_level} ({side})")
    print(f"  Count: {data[b'count'].decode()}")
    print(f"  Total BTC: {float(data[b'total_quantity']):.4f}")     # ← COINS
    print(f"  Total USD: ${float(data[b'total_value']):,.2f}")      # ← USD
    print(f"  Exchanges: {[e.decode() for e in exchanges]}")
```

**Output:**
```
Price Level: $67200 (LONG)
  Count: 5
  Total BTC: 13.2000          ← COIN AMOUNT
  Total USD: $875,431.25      ← USD AMOUNT
  Exchanges: ['binance', 'bybit']
```

---

### **4. Compare Exchanges (Continuous Aggregate):**

```sql
SELECT
    period,
    exchange,
    event_count,
    total_value_usd,    -- ← USD by exchange
    long_count,
    short_count
FROM liquidation_exchange_comparison
WHERE period >= NOW() - INTERVAL '24 hours'
ORDER BY period DESC, total_value_usd DESC;
```

**Results:**
```
period               | exchange | event_count | total_value_usd | long_count | short_count
---------------------|----------|-------------|-----------------|------------|------------
2025-10-21 12:00:00 | binance  |     12      |  $1,420,500.00 |      8     |      4
2025-10-21 12:00:00 | bybit    |      8      |    $890,250.00 |      5     |      3
2025-10-21 08:00:00 | binance  |     15      |  $1,875,000.00 |     10     |      5
2025-10-21 08:00:00 | bybit    |     10      |  $1,125,500.00 |      6     |      4
```

---

## 🎯 Storage Levels Summary

| Level | Exchange Tracking | Coin Amount | USD Amount | Retention |
|-------|-------------------|-------------|------------|-----------|
| **L1: In-Memory** | Per exchange | ✅ Yes | ✅ Yes | 60 seconds |
| **L2: Redis** | Per exchange + aggregated | ✅ Yes | ✅ Yes | 1 hour |
| **L3: TimescaleDB** | Per exchange + aggregated | ✅ Yes | ✅ Yes | 90 days |
| **L4: Aggregates** | Per exchange + aggregated | ✅ Yes | ✅ Yes | 1 year |

---

## 🚀 Run the Live System

```bash
cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator

# Start collecting real data
python3 main.py
```

**You'll see:**
```
✅ Connected to Binance liquidation stream
✅ Connected to Bybit liquidation stream
Subscribed to Bybit liquidations for BTCUSDT

💰 INSTITUTIONAL: BINANCE BTCUSDT LONG $168,086.25 @ $67,234.50
💰 INSTITUTIONAL: BYBIT BTCUSDT SHORT $245,120.00 @ $67,180.00

📊 STATS: Processed: 145 | Institutional: 12 | Cascades: 2 | Events/sec: 2.42
```

---

## 📊 Analyze the Data

### **Jupyter Notebook:**
```bash
jupyter notebook analysis.ipynb
```

### **Direct SQL:**
```bash
psql liquidations -c "
SELECT exchange,
       COUNT(*) as events,
       SUM(quantity) as total_btc,
       SUM(value_usd) as total_usd
FROM liquidations_significant
WHERE time >= NOW() - INTERVAL '1 hour'
GROUP BY exchange;
"
```

### **Redis CLI:**
```bash
redis-cli -n 1

# List all liquidation data
KEYS liq:*

# Get price level
HGETALL liq:levels:BTCUSDT:67200:LONG
```

---

## ✅ Summary

**YES, everything is aggregated by exchange:**

1. ✅ **Binance liquidations** - separate tracking
2. ✅ **Bybit liquidations** - separate tracking
3. ✅ **Coin amounts** (BTC) - tracked separately
4. ✅ **USD values** - tracked separately
5. ✅ **Cross-exchange aggregations** - combined view
6. ✅ **Per-exchange aggregations** - individual view
7. ✅ **Price level clustering** - $100 levels for BTC
8. ✅ **Cascade detection** - single exchange + cross-exchange

**All data available in:**
- Real-time (in-memory + Redis)
- Historical (TimescaleDB)
- Aggregated (continuous aggregates)
- Per-exchange breakdowns
- Cross-exchange comparisons

**Ready to track institutional liquidations! 🚀**
