# 📱 Telegram Commands Architecture & Implementation

## 🏗️ Container Architecture

### **Container 1: crypto-telegram-bot**
- **Role:** Telegram interface, command processing
- **No WebSockets here** - Only HTTP client
- **Connects to:** Market-data service via HTTP (port 8001)

### **Container 2: crypto-market-data**
- **Role:** REST API server for market data
- **No WebSockets here** - Only REST endpoints
- **Exchanges:** Binance, Bybit, OKX, Gate, Bitget (via REST APIs)

## 📊 All Telegram Commands Implementation

### ✅ **IMPLEMENTED COMMANDS**

| Command | Container | Data Flow | Status |
|---------|-----------|-----------|---------|
| `/start` | telegram-bot | Local only | ✅ Working |
| `/help` | telegram-bot | Local only | ✅ Working |
| `/price` | telegram-bot → market-data | HTTP → `/combined_price` | ✅ Working |
| `/volume` | telegram-bot → market-data | HTTP → `/volume_spike` | ✅ Working |
| `/cvd` | telegram-bot → market-data | HTTP → `/cvd` | ✅ Working |
| `/oi` | telegram-bot → market-data | HTTP → `/oi` | ✅ Working |
| `/profile` | telegram-bot → market-data | HTTP → `/market_profile` | ✅ Working |
| `/top10` | telegram-bot → market-data | HTTP → `/top10` | ✅ Working |
| `/analysis` | telegram-bot → market-data | HTTP → `/analysis` | ✅ Working |
| `/volscan` | telegram-bot → market-data | HTTP → `/volume_scan` | ✅ Working |
| `/alerts` | telegram-bot | Local (controls monitoring) | ⚠️ Coded but not active |
| `/liquidations` | telegram-bot | Local (shows buffer) | ⚠️ Coded but no data |
| `/balance` | telegram-bot | Placeholder | ❌ Not implemented |
| `/positions` | telegram-bot | Placeholder | ❌ Not implemented |
| `/pnl` | telegram-bot | Placeholder | ❌ Not implemented |

### ❌ **COMMANDS MENTIONED IN DOCS BUT NOT IMPLEMENTED**
- `/ls` - Long/Short ratios (NOT implemented as standalone)
- `/funding` - Funding rates (NOT implemented as standalone)

## 🔍 Evidence: How Commands Actually Work

### **Example: /price BTC Command Flow**

```python
# 1. User sends to Telegram: /price BTC

# 2. telegram-bot/main.py (line 273):
result = await self.market_client.get_combined_price(symbol)

# 3. HTTP Request to market-data:
POST http://localhost:8001/combined_price
Body: {"symbol": "BTC"}

# 4. market-data/main.py processes:
async def handle_combined_price_request(self, symbol: str, exchange: str = None)
  → Fetches from Binance/Bybit REST APIs
  → Returns JSON response

# 5. Bot formats and sends to Telegram
```

### **Example: /volume ETH Command Flow**

```python
# telegram-bot/main.py (line 758):
result = await self.market_client.get_volume_spike(symbol, timeframe)

# HTTP Request:
POST http://localhost:8001/volume_spike
Body: {"symbol": "ETH", "timeframe": "15m"}

# Returns volume analysis with spike detection
```

## 🚨 WebSocket Status: FACTS

### **Current Reality:**
1. **NO WebSockets are currently running** ❌
2. **WebSocket code exists but NOT activated**
3. **All data comes from REST APIs**

### **Evidence from Logs:**
```bash
# No WebSocket connection logs found
docker logs crypto-telegram-bot | grep -i websocket
# Result: Empty

# WebSocket module installed but unused
docker exec crypto-telegram-bot python -c "import websockets"
# Result: Module exists
```

### **WebSocket Code (Exists but Inactive):**

```python
# services/telegram-bot/liquidation_monitor.py (line 112):
self.websocket_url = "wss://fstream.binance.com/ws/!forceOrder@arr"

# BUT this only activates when user runs:
/alerts start  # <- Never been executed
```

## 📈 Volume & OI Spike Detection

### **Volume Spikes (REACTIVE - Currently Working)**

**Location:** `services/market-data/main.py`
**Trigger:** User command `/volume BTC 15m`
**Detection:**
- **Method:** Compares current vs average volume
- **Threshold:** 200% of average (2x spike)
- **Timeframe:** User-specified (5m, 15m, 1h, 4h)
- **Type:** Percentage-based, not USD

```python
# How it works:
spike_ratio = current_volume / average_volume
if spike_ratio > 2.0:  # 200% spike
    return "Volume spike detected"
```

### **OI Spikes (PROACTIVE - Not Active)**

**Location:** `services/telegram-bot/oi_monitor.py`
**Trigger:** Would be automatic IF monitoring was started
**Detection:**
- **Method:** Polling every 5 minutes (planned)
- **Thresholds:**
  - BTC: 15% change in 15 minutes
  - ETH: 18% change in 15 minutes
  - SOL: 25% change in 15 minutes
- **Type:** BOTH percentage AND minimum USD value
  - BTC: 15% change AND minimum $50M OI
  - ETH: 18% change AND minimum $25M OI

```python
# From oi_monitor.py (line 29-34):
self.thresholds = {
    'BTC': {'change_pct': 15.0, 'min_oi': 50_000_000},  # 15% AND $50M
    'ETH': {'change_pct': 18.0, 'min_oi': 25_000_000},  # 18% AND $25M
    'SOL': {'change_pct': 25.0, 'min_oi': 10_000_000},  # 25% AND $10M
}
self.window_minutes = 15  # Detection window
```

## 🎯 What We're Actually Tracking

### **Currently Active (REACTIVE):**
| Metric | Tracking Method | Timeframe | Threshold |
|--------|----------------|-----------|-----------|
| Price | On-demand REST | User specified | N/A |
| Volume | On-demand REST | 5m/15m/1h/4h | 200% spike |
| CVD | On-demand REST | User specified | N/A |
| OI | On-demand REST | Current snapshot | N/A |

### **Planned but Inactive (PROACTIVE):**
| Metric | Tracking Method | Timeframe | Threshold |
|--------|----------------|-----------|-----------|
| Liquidations | WebSocket stream | Real-time | $100k (BTC) |
| Liquidation Cascades | WebSocket stream | 30 seconds | 5+ events |
| OI Explosions | REST polling | 15 minutes | 15-30% change |

## 💡 Key Findings

1. **No WebSockets Active:** Despite code existing, no WebSocket connections are running
2. **All Data is REST-based:** Every command makes HTTP requests to market-data service
3. **Proactive Monitoring Off:** The `/alerts start` command has never been executed
4. **Volume Spikes:** Only checked when user requests (not proactive)
5. **OI Monitoring:** Code exists but never runs (requires manual activation)

## 🔧 To Activate Proactive Monitoring

```bash
# Send in Telegram:
/alerts start

# This would:
1. Start WebSocket to Binance liquidations
2. Start polling for OI changes every 5 minutes
3. Send automatic alerts when thresholds exceeded
```

## 📊 Resource Impact If Activated

```
Current (All Reactive):
- REST calls: ~100-500/day
- WebSockets: 0
- Memory: ~250MB total

If Proactive Activated:
- REST calls: +288/day (OI polling every 5 min)
- WebSockets: 1 persistent connection
- Memory: +50MB
- Network: ~1KB/sec continuous
```

The system is **designed for proactive monitoring** but currently operates in **reactive mode only**.