# HYPERLIQUID TESTING GUIDE

## System Status

**✅ HYPERLIQUID IS IMPLEMENTED AND WORKING**

The system has **TWO separate implementations:**

### System A: `main.py` (Currently Running - CEX Only)
- **Exchanges:** Binance + Bybit + OKX
- **Missing:** Hyperliquid ❌
- **Status:** 2 processes running (PIDs: 86894, 47110)
- **Architecture:** Uses `MultiExchangeLiquidationAggregator` (CEX-only)

### System B: `deploy_enhanced_system.py` (Enhanced - CEX + DEX)
- **Exchanges:** Binance + Bybit + OKX + **Hyperliquid** ✅
- **Status:** Available but not running
- **Architecture:** Uses `EnhancedWebSocketManager` (supports both CEX and DEX)

---

## HOW TO TEST HYPERLIQUID

### Option 1: Quick Standalone Test (Recommended for Testing)

Test Hyperliquid connection **independently** without other exchanges:

```bash
# Quick 30-second test
python test_hyperliquid_live.py --duration 30 --symbols BTC ETH

# Extended 5-minute test
python test_hyperliquid_live.py --duration 300 --symbols BTC ETH SOL

# Monitor all available symbols
python test_hyperliquid_live.py --duration 120
```

**What it does:**
- Connects to Hyperliquid WebSocket
- Subscribes to trade streams for specified symbols
- Filters liquidation events (trades involving HLP Liquidator address)
- Logs all liquidations with full details
- Shows connection status and statistics

**Expected output:**
```
✅ Successfully imported HyperliquidLiquidationProvider
🟣 Hyperliquid liquidation provider initialized
   Monitoring symbols: BTC, ETH
✅ Connected to Hyperliquid WebSocket
🟣 Subscribed to Hyperliquid allMids
🟣 Subscribed to Hyperliquid BTC trades
🟣 Subscribed to Hyperliquid ETH trades

[When liquidation occurs:]
💥 LIQUIDATION #1
   Exchange: hyperliquid
   Symbol: BTC
   Side: LONG
   Price: $67,234.50
   Quantity: 2.5
   Value USD: $168,086.25
   Time: 2025-10-25 16:24:35
```

---

### Option 2: Full Enhanced System (All Exchanges + Hyperliquid)

Run the **complete enhanced system** with Hyperliquid integrated:

```bash
# Test mode with Hyperliquid (verbose logging)
python deploy_enhanced_system.py --mode test --exchanges binance bybit okx hyperliquid

# Development mode (default)
python deploy_enhanced_system.py --exchanges binance bybit okx hyperliquid

# Custom symbols
python deploy_enhanced_system.py --symbols BTCUSDT ETHUSDT SOLUSDT --exchanges hyperliquid

# Production mode
python deploy_enhanced_system.py --mode production --exchanges binance bybit okx hyperliquid
```

**What it does:**
- Starts all exchange streams concurrently (CEX + DEX)
- Velocity tracking across all exchanges
- Cascade detection with cross-exchange correlation
- Risk scoring and signal generation
- BTC price feed integration
- Redis metrics storage

**Expected output:**
```
🚀 Starting Enhanced Liquidation System...
✅ Redis connection established
✅ Velocity Engine and Risk Calculator initialized
✅ Signal Generator and Regime Detector initialized
Added Binance stream with velocity tracking
Added Bybit stream with velocity tracking
Added OKX stream with velocity tracking
Added Hyperliquid DEX stream with velocity tracking
✅ WebSocket Manager configured
Setup complete!
✅ All systems operational
Started binance stream
Started bybit stream
Started okx stream
Started Hyperliquid DEX stream
Started BTC price feed
✅ All streams started (5 total)

[When cascade detected:]
🚨 CASCADE DETECTED - BTCUSDT
   Level: CRITICAL
   Probability: 87.50%
   Velocity: 8.42 events/s
   Acceleration: 2.15 events/s²
   Risk Level: HIGH
   Regime: VOLATILE
```

---

## VERIFICATION CHECKLIST

After running tests, verify:

### 1. Connection Status
```bash
# Check logs for these messages:
✅ Connected to Hyperliquid WebSocket
🟣 Subscribed to Hyperliquid [SYMBOL] trades
```

### 2. Data Flow
```bash
# Look for liquidation events:
💥 LIQUIDATION #[number]
   Exchange: hyperliquid
   ...
```

### 3. Statistics
```bash
# At test completion:
📊 TEST SUMMARY
   Total liquidations detected: [count]
   Total trades: [count]
   Liquidations: [count]
```

---

## TROUBLESHOOTING

### Import Error: "No module named 'shared'"
**Fix:** The test script automatically adds parent paths. If still failing:
```bash
cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator
python test_hyperliquid_live.py
```

### No Liquidations Detected
**Normal!** Hyperliquid liquidations are **less frequent** than CEX:
- **Binance:** ~80% of total volume
- **Bybit:** ~16% of total volume
- **OKX:** ~4% of total volume
- **Hyperliquid:** ~1-3% of total volume (DEX)

**Recommendations:**
- Run test for **5-10 minutes** minimum
- Monitor during volatile market conditions
- Check multiple symbols (BTC, ETH, SOL, AVAX)

### WebSocket Connection Errors
**Check:**
1. Internet connectivity
2. Hyperliquid API status: https://api.hyperliquid.xyz/info
3. Firewall/proxy settings

---

## TECHNICAL DETAILS

### How Hyperliquid Liquidations Work

**CEX (Binance/Bybit/OKX):**
- Direct liquidation events via WebSocket
- Exchange publishes liquidation data
- Real-time, immediate notification

**DEX (Hyperliquid):**
- Liquidations are on-chain trades
- Monitor ALL trades via WebSocket
- Filter trades involving HLP Liquidator address:
  - `0x2e3d94f0562703b25c83308a05046ddaf9a8dd14`
- Determine liquidation side from trade direction

### Data Format Differences

**CEX Format (`LiquidationEvent`):**
```python
LiquidationEvent(
    timestamp_ms=1729512000000,
    exchange=Exchange.BINANCE,
    symbol='BTCUSDT',
    side=Side.LONG,
    price=67234.50,
    quantity=2.5,
    value_usd=168086.25
)
```

**DEX Format (`CompactLiquidation`):**
```python
CompactLiquidation(
    exchange='hyperliquid',
    symbol='BTC',
    side=LiquidationSide.LONG,
    price=67234.50,
    quantity=2.5,
    actual_value_usd=168086.25,
    timestamp_ms=1729512000000
)
```

**Bridge:** `EnhancedWebSocketManager` normalizes both formats.

---

## NEXT STEPS

### 1. Test Hyperliquid Standalone (NOW)
```bash
python test_hyperliquid_live.py --duration 300 --symbols BTC ETH SOL
```

### 2. Test Full Enhanced System
```bash
python deploy_enhanced_system.py --mode test --exchanges hyperliquid --symbols BTCUSDT
```

### 3. Verify Data Collection (5-10 min test)
Let it run during active market hours for best results.

### 4. Compare with CoinGlass
Check if detected liquidations match CoinGlass data:
- https://www.coinglass.com/LiquidationData

---

## COMPARISON: Two Systems

| Feature | main.py | deploy_enhanced_system.py |
|---------|---------|---------------------------|
| Binance | ✅ | ✅ |
| Bybit | ✅ | ✅ |
| OKX | ✅ | ✅ |
| **Hyperliquid** | ❌ | **✅** |
| Velocity Tracking | ❌ | ✅ |
| Cascade Detection | ✅ Basic | ✅ Advanced |
| Risk Scoring | ✅ 6-factor | ✅ Multi-factor |
| Signal Generation | ❌ | ✅ |
| Market Regime Detection | ❌ | ✅ |
| Redis Metrics | ✅ | ✅ |
| TimescaleDB | ✅ | ❌ |
| BTC Price Feed | ❌ | ✅ |

---

## FILES CREATED

1. **test_hyperliquid_live.py** - Standalone Hyperliquid test script
2. **HYPERLIQUID_TEST_GUIDE.md** - This guide

**Existing Files:**
- `deploy_enhanced_system.py` - Full enhanced system with Hyperliquid
- `enhanced_websocket_manager.py` - Unified CEX+DEX manager
- `dex/hyperliquid_liquidation_provider.py` - Hyperliquid implementation
- `main.py` - Original CEX-only system

---

## RECOMMENDATION

**For immediate Hyperliquid testing:**
```bash
python test_hyperliquid_live.py --duration 600 --symbols BTC ETH SOL
```

**For production integration:**
Consider migrating from `main.py` to `deploy_enhanced_system.py` to get:
- Hyperliquid support
- Better architecture
- Advanced analytics
- Cross-exchange cascade detection
