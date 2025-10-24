# Testing Guide - Hyperliquid Blockchain Liquidation Tracker

## Quick Start (1 minute)

### Prerequisites

```bash
# Install dependencies
pip install aiohttp loguru

# Or from requirements
pip install -r services/market-data/requirements.txt
```

### Run Quick Test

```bash
cd /home/user/TG-Bot
python3 tests/quick_test.py
```

**Expected output:**
```
🚀 Quick Test - Hyperliquid Liquidation Tracker

1. Initializing tracker...
   ✅ Tracker initialized

2. Scanning BTC liquidations (this may take 5-10 seconds)...
   ✅ Scan complete!

📊 Results:
   Found 15 BTC liquidations

   Most recent liquidations:
   1. LONG liquidation
      Value: $125,000
      User: 0x1234567890abcdef...
   ...

📈 Statistics:
   Total: 15 liquidations
   Volume: $2,450,000
   Longs: 10
   Shorts: 5

✅ Test PASSED - Tracker is working!
```

## Comprehensive Testing (5 minutes)

### Run Full Test Suite

```bash
python3 tests/test_hyperliquid_tracker_local.py
```

**Tests included:**
1. ✅ API Connectivity - Verifies connection to Hyperliquid API
2. ✅ Liquidation Detection - Tests detection logic with mock data
3. ✅ Live Scan - Scans real BTC trades for liquidations
4. ✅ Statistics - Validates aggregation calculations
5. ✅ Timeframes - Tests time-based queries
6. ✅ Multi-Coin - Scans BTC, ETH, SOL simultaneously

**Expected output:**
```
🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪
  HYPERLIQUID BLOCKCHAIN TRACKER - LOCAL TESTING
🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪 🧪

============================================================
  TEST 1: API Connectivity
============================================================
✅ Connected to Hyperliquid API
ℹ️  Retrieved 2000 recent BTC trades

============================================================
  TEST 2: Liquidation Detection Logic
============================================================
✅ Liquidation detection works!
✅ Side detection correct (HLP buying = SHORT liquidation)

... (more tests)

============================================================
  TEST SUMMARY
============================================================
✅ API Connectivity
✅ Liquidation Detection
✅ Live Scan
✅ Statistics
✅ Timeframes
✅ Multi-Coin

============================================================
  PASSED: 6/6 tests
============================================================

🎉 All tests passed! Implementation is working correctly.
```

## Manual Testing

### Test 1: Simple Import

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from services.market_data.hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker
print('✅ Import successful')
"
```

### Test 2: API Connectivity

```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.market_data.hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def test():
    tracker = HyperliquidBlockchainLiquidationTracker()
    trades = await tracker.query_recent_trades('BTC')
    print(f'✅ API works! Got {len(trades)} trades')
    await tracker.close()

asyncio.run(test())
"
```

### Test 3: Find Liquidations

```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.market_data.hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def test():
    tracker = HyperliquidBlockchainLiquidationTracker()
    liquidations = await tracker.scan_recent_liquidations(['BTC'])
    print(f'✅ Found {len(liquidations)} liquidations')
    for liq in liquidations[:3]:
        print(f'  - {liq.coin} {liq.liquidation_side}: \${liq.value_usd:,.0f}')
    await tracker.close()

asyncio.run(test())
"
```

### Test 4: Real-Time Monitoring (30 seconds)

```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.market_data.hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def test():
    tracker = HyperliquidBlockchainLiquidationTracker()
    print('Monitoring for 30 seconds...')

    async def timeout():
        await asyncio.sleep(30)
        return None

    count = 0
    async for liq in tracker.monitor_realtime(interval=5):
        count += 1
        print(f'{count}. {liq.coin} {liq.liquidation_side}: \${liq.value_usd:,.0f}')
        if count >= 5:
            break

    await tracker.close()
    print(f'✅ Monitoring works! Found {count} new liquidations')

asyncio.run(test())
"
```

## Unit Tests

### Create Test File

```python
# tests/test_liquidation_detection.py
import pytest
from services.market_data.hyperliquid_blockchain_liquidation_tracker import (
    HyperliquidBlockchainLiquidationTracker,
    HLP_LIQUIDATOR_ADDRESS
)

def test_liquidation_detection_short():
    """Test SHORT liquidation detection (HLP buying)"""
    tracker = HyperliquidBlockchainLiquidationTracker()

    trade = {
        "coin": "BTC",
        "side": "B",
        "users": [HLP_LIQUIDATOR_ADDRESS, "0xuser123"]
    }

    is_liq, user = tracker.is_liquidation_trade(trade)

    assert is_liq == True
    assert user == "0xuser123"

def test_liquidation_detection_long():
    """Test LONG liquidation detection (HLP selling)"""
    tracker = HyperliquidBlockchainLiquidationTracker()

    trade = {
        "coin": "ETH",
        "side": "A",
        "users": ["0xuser456", HLP_LIQUIDATOR_ADDRESS]
    }

    is_liq, user = tracker.is_liquidation_trade(trade)

    assert is_liq == True
    assert user == "0xuser456"

def test_not_liquidation():
    """Test non-liquidation trade"""
    tracker = HyperliquidBlockchainLiquidationTracker()

    trade = {
        "coin": "SOL",
        "side": "B",
        "users": ["0xuser1", "0xuser2"]
    }

    is_liq, user = tracker.is_liquidation_trade(trade)

    assert is_liq == False
    assert user is None
```

**Run unit tests:**
```bash
pytest tests/test_liquidation_detection.py -v
```

## Integration Tests

### Test with Different Networks

```python
# Test mainnet
tracker_main = HyperliquidBlockchainLiquidationTracker(
    api_base="https://api.hyperliquid.xyz"
)

# Test testnet
tracker_test = HyperliquidBlockchainLiquidationTracker(
    api_base="https://api.hyperliquid-testnet.xyz"
)
```

### Test Different Coins

```python
# Test major coins
liquidations = await tracker.scan_recent_liquidations([
    "BTC", "ETH", "SOL", "ARB", "AVAX"
])

# Test altcoins
liquidations = await tracker.scan_recent_liquidations([
    "DOGE", "PEPE", "WIF", "BONK"
])
```

## Troubleshooting

### Issue 1: No liquidations found

**Problem:** `Found 0 liquidations`

**Possible causes:**
1. ✅ **Market is quiet** (no liquidations happening) - This is NORMAL
2. ❌ API connection issues
3. ❌ Wrong liquidator address

**Solution:**
```python
# Check if trades are being retrieved
trades = await tracker.query_recent_trades("BTC")
print(f"Got {len(trades)} trades")  # Should be > 0

# Check if HLP Liquidator is in any trades
for trade in trades:
    if HLP_LIQUIDATOR_ADDRESS.lower() in [u.lower() for u in trade.get('users', [])]:
        print(f"Found HLP Liquidator in trade: {trade}")
```

### Issue 2: API connection errors

**Problem:** `Connection refused` or `Timeout`

**Solutions:**
1. Check internet connection
2. Verify Hyperliquid API is up: https://api.hyperliquid.xyz/info
3. Check firewall/proxy settings

```bash
# Test API manually
curl -X POST https://api.hyperliquid.xyz/info \
  -H "Content-Type: application/json" \
  -d '{"type":"meta"}'
```

### Issue 3: Import errors

**Problem:** `ModuleNotFoundError: No module named 'services'`

**Solution:**
```bash
# Add project root to Python path
cd /home/user/TG-Bot
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 tests/quick_test.py
```

### Issue 4: Rate limiting

**Problem:** API returns 429 errors

**Solution:**
```python
# Increase polling interval
async for liq in tracker.monitor_realtime(interval=30):  # 30s instead of 10s
    print(liq)
```

## Validation Checklist

Before deploying to production, verify:

- [ ] ✅ Quick test passes
- [ ] ✅ Full test suite passes (6/6 tests)
- [ ] ✅ API connectivity confirmed
- [ ] ✅ Liquidations are being detected
- [ ] ✅ Statistics are calculated correctly
- [ ] ✅ Side detection works (LONG vs SHORT)
- [ ] ✅ Multi-coin scanning works
- [ ] ✅ No memory leaks during long runs
- [ ] ✅ Error handling works (disconnect/reconnect)

## Performance Testing

### Test Memory Usage

```python
import asyncio
import tracemalloc

async def test_memory():
    tracemalloc.start()

    tracker = HyperliquidBlockchainLiquidationTracker()

    # Scan 10 times
    for i in range(10):
        await tracker.scan_recent_liquidations(["BTC", "ETH", "SOL"])
        current, peak = tracemalloc.get_traced_memory()
        print(f"Scan {i+1}: Current={current/1024/1024:.2f}MB, Peak={peak/1024/1024:.2f}MB")

    await tracker.close()
    tracemalloc.stop()

asyncio.run(test_memory())
```

### Test API Rate Limiting

```python
import time

async def test_rate_limit():
    tracker = HyperliquidBlockchainLiquidationTracker()

    start = time.time()
    for i in range(10):
        await tracker.query_recent_trades("BTC")
        print(f"Request {i+1} completed")

    elapsed = time.time() - start
    print(f"10 requests took {elapsed:.2f}s ({10/elapsed:.2f} req/s)")

    await tracker.close()

asyncio.run(test_rate_limit())
```

## Next Steps

After local validation:

1. **Add persistence** (database integration)
2. **Add monitoring** (Prometheus metrics)
3. **Add alerting** (Telegram/Discord)
4. **Deploy to staging**
5. **Monitor for 24 hours**
6. **Deploy to production**

---

**Quick Reference:**

```bash
# Quick test (1 min)
python3 tests/quick_test.py

# Full tests (5 min)
python3 tests/test_hyperliquid_tracker_local.py

# Unit tests
pytest tests/test_liquidation_detection.py

# Manual API test
python3 -c "import asyncio; from services.market_data.hyperliquid_blockchain_liquidation_tracker import *; asyncio.run(HyperliquidBlockchainLiquidationTracker().scan_recent_liquidations(['BTC']))"
```
