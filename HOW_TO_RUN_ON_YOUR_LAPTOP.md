# How to Run Hyperliquid Tracker on Your Laptop

## Step 1: Pull the Code from GitHub

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/napo99/TG-Bot.git
cd TG-Bot

# Or pull latest changes (if you already have it)
cd TG-Bot
git checkout main
git pull origin main

# Switch to the feature branch
git fetch origin
git checkout claude/implement-blockchain-liquidation-monitor-011CURpyAwNPMWBkjavievsE
```

## Step 2: Install Python Dependencies

### Option A: Using pip (Recommended)

```bash
# Install only required dependencies
pip install aiohttp loguru

# Or install all market-data dependencies
pip install -r services/market-data/requirements.txt
```

### Option B: Using virtual environment (Best practice)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install aiohttp loguru
```

## Step 3: Run Quick Test (1 minute)

```bash
# From project root
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

📈 Statistics:
   Total: 15 liquidations
   Volume: $2,450,000
   Longs: 10
   Shorts: 5

✅ Test PASSED - Tracker is working!
```

## Step 4: Run Full Test Suite (5 minutes)

```bash
python3 tests/test_hyperliquid_tracker_local.py
```

This runs 6 comprehensive tests.

## Step 5: Try Manual Testing

### Simple Scan

```bash
python3 << 'EOF'
import asyncio
import sys
sys.path.insert(0, 'services/market-data')

from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def main():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # Scan BTC
    liquidations = await tracker.scan_recent_liquidations(["BTC"])

    print(f"Found {len(liquidations)} liquidations")
    for liq in liquidations[:5]:
        print(f"  - {liq.coin} {liq.liquidation_side}: ${liq.value_usd:,.0f}")

    await tracker.close()

asyncio.run(main())
EOF
```

### Real-Time Monitoring (Ctrl+C to stop)

```bash
python3 << 'EOF'
import asyncio
import sys
sys.path.insert(0, 'services/market-data')

from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def main():
    tracker = HyperliquidBlockchainLiquidationTracker()

    print("Monitoring for liquidations (Ctrl+C to stop)...")

    async for liq in tracker.monitor_realtime(coins=["BTC", "ETH"], interval=10):
        print(f"💥 {liq.coin} {liq.liquidation_side} liquidation")
        print(f"   Value: ${liq.value_usd:,.0f}")
        print(f"   User: {liq.liquidated_user[:20]}...")

asyncio.run(main())
EOF
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'aiohttp'`

**Solution:**
```bash
pip install aiohttp loguru
```

### Issue: `ModuleNotFoundError: No module named 'hyperliquid_blockchain_liquidation_tracker'`

**Solution:**
```bash
# Make sure you're in the project root
cd /path/to/TG-Bot

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/services/market-data"
```

### Issue: Connection errors to Hyperliquid API

**Solution:**
1. Check internet connection
2. Verify Hyperliquid is accessible:
   ```bash
   curl -X POST https://api.hyperliquid.xyz/info \
     -H "Content-Type: application/json" \
     -d '{"type":"meta"}'
   ```
3. Check if behind proxy/firewall

### Issue: No liquidations found

**This is NORMAL!** If the market is quiet, there may be no recent liquidations. Try:
- Scanning multiple coins: `["BTC", "ETH", "SOL", "ARB", "AVAX"]`
- Waiting during high volatility periods
- Checking against CoinGlass to confirm: https://www.coinglass.com/hyperliquid-liquidation-map

## What to Test

### ✅ Checklist

- [ ] Quick test passes
- [ ] Full test suite passes (6/6)
- [ ] Can scan BTC liquidations
- [ ] Can scan multiple coins
- [ ] Statistics are calculated
- [ ] Real-time monitoring works
- [ ] Can detect LONG vs SHORT
- [ ] API connectivity confirmed

## File Locations

```
TG-Bot/
├── services/
│   └── market-data/
│       └── hyperliquid_blockchain_liquidation_tracker.py  ← Main tracker
├── tests/
│   ├── quick_test.py                                      ← Quick 1-min test
│   └── test_hyperliquid_tracker_local.py                  ← Full 5-min test
├── TESTING_GUIDE.md                                        ← Detailed testing docs
├── HYPERLIQUID_IMPLEMENTATION_DETAILS.md                   ← Architecture guide
└── HYPERLIQUID_BLOCKCHAIN_TRACKER_README.md               ← Usage guide
```

## Configuration Options

### Change Coins

```python
# Scan only BTC
liquidations = await tracker.scan_recent_liquidations(["BTC"])

# Scan major coins
liquidations = await tracker.scan_recent_liquidations([
    "BTC", "ETH", "SOL", "ARB", "AVAX"
])
```

### Change Polling Interval

```python
# Poll every 5 seconds (fast)
async for liq in tracker.monitor_realtime(interval=5):
    print(liq)

# Poll every 30 seconds (slow, less API calls)
async for liq in tracker.monitor_realtime(interval=30):
    print(liq)
```

### Use Testnet

```python
tracker = HyperliquidBlockchainLiquidationTracker(
    api_base="https://api.hyperliquid-testnet.xyz"
)
```

## Next Steps

After validating locally:

1. **Integrate into your bot/service**
   ```python
   from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

   # In your bot
   self.liquidation_tracker = HyperliquidBlockchainLiquidationTracker()
   ```

2. **Add database persistence** (if needed)
   ```python
   async def save_liquidation(liq):
       await db.execute(
           "INSERT INTO liquidations VALUES (?, ?, ?, ?)",
           (liq.tx_hash, liq.coin, liq.value_usd, liq.timestamp)
       )
   ```

3. **Add Telegram alerts** (if needed)
   ```python
   async for liq in tracker.monitor_realtime():
       if liq.value_usd > 100_000:
           await bot.send_message(f"Large liquidation: ${liq.value_usd:,.0f}")
   ```

## Quick Commands Reference

```bash
# Pull latest code
git pull origin claude/implement-blockchain-liquidation-monitor-011CURpyAwNPMWBkjavievsE

# Install deps
pip install aiohttp loguru

# Quick test
python3 tests/quick_test.py

# Full tests
python3 tests/test_hyperliquid_tracker_local.py

# Check docs
cat TESTING_GUIDE.md
cat HYPERLIQUID_IMPLEMENTATION_DETAILS.md
```

---

**Ready to run!** Start with `python3 tests/quick_test.py` 🚀
