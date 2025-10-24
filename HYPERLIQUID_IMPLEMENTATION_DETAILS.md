# Hyperliquid Blockchain Tracker - Implementation Details

## 🏗️ Architecture Overview

### What It Is

**Python Class-Based Library** - Not a standalone service, but a reusable component you instantiate and integrate.

```python
# You create an instance
tracker = HyperliquidBlockchainLiquidationTracker()

# You call its methods
liquidations = await tracker.scan_recent_liquidations(["BTC", "ETH"])
stats = tracker.get_statistics()
```

### What It Is NOT

❌ **NOT a WebSocket server** - Does not create a WebSocket endpoint
❌ **NOT a REST API server** - Does not expose HTTP endpoints
❌ **NOT a standalone daemon** - Must be integrated into your code
❌ **NOT a database** - Does not persist data to disk

## 📡 Connection Type: REST API Polling (Not WebSocket)

### How It Works

```python
# Makes HTTP POST requests to Hyperliquid's REST API
async def query_recent_trades(self, coin: str):
    payload = {"type": "recentTrades", "coin": coin}
    response = await session.post("https://api.hyperliquid.xyz/info", json=payload)
    trades = await response.json()  # Returns up to 2000 recent trades
    return trades
```

**Connection Method:**
- ✅ **REST API** via `aiohttp` (HTTP POST requests)
- ✅ **Polling-based** (queries every N seconds)
- ❌ **NOT WebSocket** (no persistent connection)

**Why Not WebSocket?**

The Hyperliquid WebSocket API does NOT have a public "all liquidations" feed. It only has:
- `trades` - All trades (need to filter manually)
- `userEvents` - User-specific (requires auth)

So we use REST API polling instead, which is simpler and works without authentication.

## 💾 Data Storage: In-Memory (Volatile)

### Storage Location

**Everything is stored in Python class instance variables (RAM):**

```python
class HyperliquidBlockchainLiquidationTracker:
    def __init__(self):
        # All data stored here (in memory)
        self.liquidations: List[BlockchainLiquidation] = []
        self.total_liquidations = 0
        self.total_value_usd = 0.0
        self.liquidations_by_coin: Dict[str, int] = {}
        # ... etc
```

### What Happens to Data

| Scenario | What Happens |
|----------|--------------|
| **Script running** | Data accumulates in memory |
| **Script restarts** | ❌ All data is lost |
| **Process crashes** | ❌ All data is lost |
| **Server reboot** | ❌ All data is lost |

### Data Lifecycle

```
Start Script → Data accumulates → Stop Script → Data LOST
```

**Data is ephemeral** - Only exists while the Python process is running.

### Why No Persistence?

The current implementation is designed for **real-time monitoring**, not historical analysis. If you need persistence, you must add it yourself:

```python
# Option 1: Save to database
async def save_to_db(liquidation):
    await db.execute(
        "INSERT INTO liquidations VALUES (?, ?, ?)",
        (liquidation.tx_hash, liquidation.coin, liquidation.value_usd)
    )

# Option 2: Save to file
def save_to_json():
    with open('liquidations.json', 'w') as f:
        json.dump([liq.__dict__ for liq in tracker.liquidations], f)
```

## ⚙️ Default Parameters

### Constructor Parameters

```python
def __init__(self, api_base: str = "https://api.hyperliquid.xyz"):
```

**Default:** `https://api.hyperliquid.xyz` (Mainnet)

**Change to testnet:**
```python
tracker = HyperliquidBlockchainLiquidationTracker(
    api_base="https://api.hyperliquid-testnet.xyz"
)
```

### scan_recent_liquidations() Parameters

```python
async def scan_recent_liquidations(self, coins: List[str] = None)
```

**Defaults:**
- `coins = None` → Uses `["BTC", "ETH", "SOL"]`

**Customizable:**
```python
# Scan only BTC
liquidations = await tracker.scan_recent_liquidations(["BTC"])

# Scan all major coins
liquidations = await tracker.scan_recent_liquidations([
    "BTC", "ETH", "SOL", "ARB", "AVAX", "DOGE", "MATIC"
])

# Scan single altcoin
liquidations = await tracker.scan_recent_liquidations(["PEPE"])
```

### monitor_realtime() Parameters

```python
async def monitor_realtime(self, coins: List[str] = None, interval: int = 10)
```

**Defaults:**
- `coins = None` → Uses `["BTC", "ETH", "SOL"]`
- `interval = 10` → Poll every 10 seconds

**Customizable:**
```python
# Poll every 5 seconds
async for liq in tracker.monitor_realtime(interval=5):
    print(liq)

# Monitor more coins, poll every 30 seconds
async for liq in tracker.monitor_realtime(
    coins=["BTC", "ETH", "SOL", "ARB", "AVAX"],
    interval=30
):
    print(liq)

# High-frequency monitoring (every 2 seconds)
async for liq in tracker.monitor_realtime(interval=2):
    print(liq)
```

### query_recent_trades() Parameters

```python
async def query_recent_trades(self, coin: str, limit: int = 2000)
```

**Defaults:**
- `limit = 2000` (Hyperliquid API max)

**Not customizable** (API limitation) - Always returns up to 2000 trades

### get_liquidations_by_timeframe() Parameters

```python
def get_liquidations_by_timeframe(self, seconds: int)
```

**No defaults** - You must specify timeframe

**Examples:**
```python
# Last 5 minutes
recent = tracker.get_liquidations_by_timeframe(300)

# Last hour
hourly = tracker.get_liquidations_by_timeframe(3600)

# Last 24 hours
daily = tracker.get_liquidations_by_timeframe(86400)
```

## 🔧 Configuration Options

### Hardcoded Constants (Can Modify Source)

```python
# Line 23 - HLP Liquidator address
HLP_LIQUIDATOR_ADDRESS = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"
```

**To change:** Edit source file (not recommended unless Hyperliquid changes liquidator)

### Runtime Configurable

| Parameter | Method | Default | Change At |
|-----------|--------|---------|-----------|
| `api_base` | `__init__()` | Mainnet | Initialization |
| `coins` | `scan_recent_liquidations()` | ["BTC","ETH","SOL"] | Each call |
| `coins` | `monitor_realtime()` | ["BTC","ETH","SOL"] | Each call |
| `interval` | `monitor_realtime()` | 10 seconds | Each call |
| `limit` | `query_recent_trades()` | 2000 | Each call |
| `seconds` | `get_liquidations_by_timeframe()` | No default | Each call |

## 🚀 Running the Tracker

### Option 1: Standalone Script

```python
# script.py
import asyncio
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def main():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # One-time scan
    liquidations = await tracker.scan_recent_liquidations(["BTC", "ETH"])
    print(f"Found {len(liquidations)} liquidations")

    # Print stats
    stats = tracker.get_statistics()
    print(f"Total USD: ${stats['total_value_usd']:,.0f}")

    await tracker.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**
```bash
python3 services/market-data/script.py
```

### Option 2: Real-Time Monitoring

```python
# monitor.py
import asyncio
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def main():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # Monitor continuously
    async for liquidation in tracker.monitor_realtime(
        coins=["BTC", "ETH", "SOL"],
        interval=10
    ):
        print(f"💥 {liquidation.coin} {liquidation.liquidation_side}")
        print(f"   ${liquidation.value_usd:,.0f}")
        print(f"   User: {liquidation.liquidated_user}")

        # Do something with the liquidation
        if liquidation.value_usd > 100_000:
            await send_telegram_alert(liquidation)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**
```bash
python3 services/market-data/monitor.py
```

**Note:** This runs forever (infinite loop). Press Ctrl+C to stop.

### Option 3: Background Task in Existing Service

```python
# In your existing bot/service
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

class MyBot:
    def __init__(self):
        self.tracker = HyperliquidBlockchainLiquidationTracker()

    async def start(self):
        # Start liquidation monitoring as background task
        asyncio.create_task(self._monitor_liquidations())

        # Your other bot logic
        await self.run_bot()

    async def _monitor_liquidations(self):
        async for liq in self.tracker.monitor_realtime(interval=15):
            await self.handle_liquidation(liq)

    async def handle_liquidation(self, liq):
        # Your custom logic
        if liq.value_usd > 50_000:
            await self.send_alert(f"Large liquidation: ${liq.value_usd:,.0f}")
```

### Option 4: Scheduled Job (Cron)

```python
# cron_job.py
import asyncio
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def main():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # Scan and save to database
    liquidations = await tracker.scan_recent_liquidations(["BTC", "ETH", "SOL"])

    # Save to database
    for liq in liquidations:
        await db.save_liquidation(liq)

    # Save stats to file
    stats = tracker.get_statistics()
    with open('/var/log/liquidations_stats.json', 'w') as f:
        json.dump(stats, f)

    await tracker.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Cron:**
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/TG-Bot && python3 services/market-data/cron_job.py
```

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Python Script Starts                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│  tracker = HyperliquidBlockchainLiquidationTracker()        │
│  (Creates empty in-memory storage)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│  scan_recent_liquidations(["BTC", "ETH"])                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│  For each coin:                                              │
│    1. POST /info {"type": "recentTrades", "coin": "BTC"}   │
│    2. Get ~2000 trades                                       │
│    3. Filter for HLP Liquidator address                      │
│    4. Parse liquidations                                     │
│    5. Store in self.liquidations (RAM)                       │
│    6. Update self.total_liquidations, etc. (RAM)            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│  Data exists in memory                                       │
│  - tracker.liquidations = [...]                             │
│  - tracker.total_liquidations = 150                         │
│  - tracker.liquidations_by_coin = {"BTC": 80, "ETH": 70}   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│  get_statistics()                                            │
│  Returns aggregated data from memory                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────┐
│  Script ends / Process terminates                            │
│  ❌ ALL DATA LOST                                            │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Memory Usage

### Typical Memory Footprint

```python
# One BlockchainLiquidation object
sizeof(BlockchainLiquidation) ≈ 300 bytes (Python object overhead)

# 1000 liquidations
1000 * 300 bytes = 300 KB

# Plus aggregation dicts
aggregation_data ≈ 50 KB

# Total for 1000 liquidations
Total ≈ 350 KB
```

**Very lightweight** - Can easily store 10,000+ liquidations in memory.

### Memory Limits

The `self.liquidations` list grows indefinitely. If running for days:

```python
# 10,000 liquidations per day × 7 days = 70,000 liquidations
70,000 * 300 bytes ≈ 21 MB

# Still manageable, but consider clearing old data:
def clear_old_liquidations(self, max_age_hours=24):
    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).timestamp() * 1000
    self.liquidations = [liq for liq in self.liquidations if liq.timestamp > cutoff]
```

## 🔐 Security & Rate Limiting

### No Authentication Required

The Hyperliquid Info API is **public** - no API key needed.

### Rate Limits

**Hyperliquid API Rate Limits:**
- Public endpoint: ~100 requests/minute per IP
- Our tracker: 1 request per coin per interval

**Example calculations:**
```python
# 3 coins, 10-second interval
requests_per_minute = 3 * (60 / 10) = 18 requests/minute
# ✅ Well under 100 limit

# 10 coins, 5-second interval
requests_per_minute = 10 * (60 / 5) = 120 requests/minute
# ⚠️ Over limit - may get rate limited
```

**Recommendation:** Keep `interval >= 10` seconds for 5+ coins.

### Handling Rate Limits

Currently **no retry logic**. If you hit rate limits, API calls fail silently.

**To add retry logic:**
```python
# Modify query_recent_trades()
async def query_recent_trades(self, coin: str):
    for attempt in range(3):
        try:
            # ... make request ...
            if response.status == 429:  # Rate limited
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            return await response.json()
        except:
            await asyncio.sleep(2 ** attempt)
```

## 🎛️ Summary Table

| Aspect | Details |
|--------|---------|
| **Type** | Python class library (not service) |
| **Connection** | REST API polling (HTTP POST) |
| **Persistence** | None (in-memory only) |
| **Default Coins** | BTC, ETH, SOL |
| **Default Interval** | 10 seconds |
| **API Endpoint** | `https://api.hyperliquid.xyz/info` |
| **Authentication** | None required |
| **Rate Limit** | ~100 requests/minute |
| **Memory Usage** | ~300 bytes per liquidation |
| **Data Lifetime** | Until process stops |
| **Configurable** | Coins, interval, API base URL |

## 🎯 Next Steps for Production

### Add Persistence

```python
# SQLite example
import aiosqlite

async def save_liquidation(db, liq):
    await db.execute("""
        INSERT INTO liquidations
        (tx_hash, coin, side, price, size, value_usd, user, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (liq.tx_hash, liq.coin, liq.liquidation_side, liq.price,
          liq.size, liq.value_usd, liq.liquidated_user, liq.timestamp))
    await db.commit()
```

### Add Error Handling

```python
async def monitor_with_retry(self):
    while True:
        try:
            async for liq in self.monitor_realtime():
                yield liq
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            await asyncio.sleep(30)  # Wait before retry
```

### Add Metrics

```python
from prometheus_client import Counter, Gauge

liquidations_total = Counter('hyperliquid_liquidations_total', 'Total liquidations')
liquidations_usd = Gauge('hyperliquid_liquidations_usd', 'Total USD liquidated')

def _update_statistics(self, liq):
    # ... existing code ...
    liquidations_total.inc()
    liquidations_usd.set(self.total_value_usd)
```

---

**In summary:** It's a **polling-based REST API client** stored **in-memory**, with **configurable parameters**, designed to be **integrated into your existing services**.
