# Exchange Liquidation Data API Research
## Comprehensive Analysis of REST and WebSocket Endpoints

**Research Date**: 2025-10-20
**Purpose**: Determine liquidation data availability across major cryptocurrency exchanges
**Scope**: REST API historical data + WebSocket real-time streams

---

## Executive Summary

| Exchange | REST API | WebSocket | Historical Data | Real-Time Stream | Status |
|----------|----------|-----------|-----------------|------------------|--------|
| **Binance** | ✅ Limited | ✅ Full | 7 days | ✅ Real-time | **Best Support** |
| **Bybit** | ❌ None | ✅ Full | ❌ No | ✅ Real-time | **WebSocket Only** |
| **Bitfinex** | ✅ Full | ✅ Full | ✅ Unlimited | ✅ Real-time | **Best Support** |
| **Bitmex** | ✅ Full | ✅ Full | ✅ Unlimited | ✅ Real-time | **Best Support** |
| **Deribit** | ❌ None* | ❓ Unclear | ❌ No | ❓ Unknown | **Limited/None** |
| **OKX** | ❓ Unclear | ✅ Exists | ❓ Unknown | ✅ Real-time | **Partial Support** |
| **Gate.io** | ✅ Full | ✅ Full | ✅ Yes | ✅ Real-time | **Good Support** |
| **Bitget** | ✅ Margin Only | ❌ None | ✅ Limited | ❌ No Public | **Limited Support** |

**Key Findings**:
- ✅ **4 exchanges with full support**: Binance, Bitfinex, Bitmex, Gate.io
- ⚠️ **3 exchanges with partial support**: Bybit (WS only), OKX (unclear docs), Bitget (margin only)
- ❌ **1 exchange with no/unclear support**: Deribit

---

## 1. BINANCE (Best Overall Support)

### ✅ WebSocket - Real-Time Liquidations
**Stream URL**: `wss://fstream.binance.com/ws/!forceOrder@arr`

**Channel Format**:
- Individual symbol: `<symbol>@forceOrder` (e.g., `btcusdt@forceOrder`)
- All markets: `!forceOrder@arr`

**Response Structure**:
```json
{
  "e": "forceOrder",
  "E": 1568014460893,
  "o": {
    "s": "BTCUSDT",
    "S": "SELL",
    "o": "MARKET",
    "f": "IOC",
    "q": "0.014",
    "p": "9910",
    "ap": "9910",
    "X": "FILLED",
    "l": "0.014",
    "z": "0.014",
    "T": 1568014460893
  }
}
```

**Key Fields**:
- `s`: Symbol
- `S`: Side (SELL = long liquidation, BUY = short liquidation)
- `q`: Quantity
- `p`: Price
- `ap`: Average Price
- `T`: Trade timestamp

**Rate Limits**:
- Max 1024 streams per connection
- Max 10 incoming messages per second per connection
- Connection weight: 2

### ✅ REST API - Historical Liquidations (Limited)
**Endpoint**: `GET /fapi/v1/allForceOrders`

**Base URL**: `https://fapi.binance.com`

**Parameters**:
- `symbol` (optional): Trading pair
- `startTime` (optional): Start timestamp
- `endTime` (optional): End timestamp
- `limit` (optional): Max 1000

**Limitations**:
- ⚠️ **Only 7 days of historical data**
- Must query within recent 7-day window
- Returns all symbols if symbol not specified

**Response Structure**:
```json
[
  {
    "symbol": "BTCUSDT",
    "price": "9910",
    "origQty": "0.014",
    "executedQty": "0.014",
    "averagePrice": "9910",
    "status": "FILLED",
    "timeInForce": "IOC",
    "side": "SELL",
    "time": 1568014460893
  }
]
```

---

## 2. BYBIT (WebSocket Only)

### ✅ WebSocket - Real-Time Liquidations
**Stream URL**: `wss://stream.bybit.com/v5/public/linear`

**Channel Format**: `allLiquidation.{symbol}` (e.g., `allLiquidation.BTCUSDT`)

**Response Structure**:
```json
{
  "topic": "allLiquidation.BTCUSDT",
  "type": "snapshot",
  "ts": 1739502303204,
  "data": [
    {
      "T": 1739502303204,
      "s": "BTCUSDT",
      "S": "Buy",
      "v": "0.014",
      "p": "9910"
    }
  ]
}
```

**Key Fields**:
- `T`: Event timestamp (milliseconds)
- `s`: Symbol
- `S`: Position direction ("Buy" or "Sell")
- `v`: Liquidated quantity
- `p`: Bankruptcy price

**Coverage**: USDT contracts, USDC contracts, Inverse contracts

**Push Frequency**: Every 500ms

**Rate Limits**:
- Max 500 connections per 5 minutes to stream.bybit.com
- Max 1,000 connections per IP for market data
- Max 60 subscriptions per connection
- Max 100 private WebSocket connections per API key

**Important Notes**:
- ✅ New `allLiquidation` pushes ALL liquidations (recommended)
- ❌ Old `liquidation` channel (deprecated) - only 1 liquidation per second

### ❌ REST API - Not Available
**No REST endpoint** for historical liquidation data.

---

## 3. BITFINEX (Excellent Support)

### ✅ REST API - Historical Liquidations (Unlimited)
**Endpoint**: `GET /v2/liquidations/hist`

**Base URL**: `https://api-pub.bitfinex.com`

**Parameters**:
- `start` (optional): Start timestamp (milliseconds)
- `end` (optional): End timestamp (milliseconds)
- Default: Returns most recent liquidations

**Rate Limits**: 3 requests per minute

**Response Structure**:
```json
[
  [
    123456,              // [1] POS_ID
    1580020000000,       // [2] MTS (timestamp)
    null,                // [3]
    "tBTCUSD",           // [4] SYMBOL
    0.5,                 // [5] AMOUNT (positive=long, negative=short)
    9910.0,              // [6] BASE_PRICE (entry price)
    null,                // [7]
    0,                   // [8] IS_MATCH (0=trigger, 1=execution)
    0,                   // [9] IS_MARKET_SOLD
    null,                // [10]
    9900.0               // [11] PRICE_ACQUIRED
  ]
]
```

**Key Fields**:
- `[1]` POS_ID: Position identifier
- `[2]` MTS: Millisecond timestamp
- `[4]` SYMBOL: Trading pair (e.g., tBTCUSD)
- `[5]` AMOUNT: Position size (positive = long, negative = short)
- `[6]` BASE_PRICE: Entry price
- `[8]` IS_MATCH: 0 = initial trigger, 1 = market execution
- `[9]` IS_MARKET_SOLD: 0 = system acquisition, 1 = direct market sale
- `[11]` PRICE_ACQUIRED: Acquisition price

### ✅ WebSocket - Real-Time Liquidations
**Stream URL**:
- Public: `wss://api-pub.bitfinex.com/ws/2`
- Authenticated: `wss://api.bitfinex.com/ws/2`

**Subscription Format**:
```json
{
  "event": "subscribe",
  "channel": "status",
  "key": "liq:global"
}
```

**Response Structure**:
```json
{
  "event": "subscribed",
  "channel": "status",
  "chanId": 91684,
  "key": "liq:global"
}
```

**Data Format**:
```json
[
  "pos",              // MSG_TYPE
  123456,             // POS_ID
  1580020000000,      // TIME_MS
  "tBTCUSD",          // SYMBOL
  0.5,                // AMOUNT
  9910.0,             // BASE_PRICE
  0,                  // IS_MATCH
  0,                  // IS_MARKET_SOLD
  9900.0              // LIQUIDATION_PRICE
]
```

**Rate Limits**:
- Public: 20 connections per minute
- Authenticated: 5 connections per 15 seconds

---

## 4. BITMEX (Excellent Support)

### ✅ REST API - Historical Liquidations (Unlimited)
**Endpoint**: `GET /api/v1/liquidation`

**Base URL**: `https://www.bitmex.com`

**Parameters**:
- `symbol` (optional): Trading pair (e.g., XBTUSD)
- `filter` (optional): JSON filter
- `columns` (optional): Columns to return
- `count` (optional): Number of results (default 100, max 500)
- `start` (optional): Starting point
- `reverse` (optional): Reverse order (newest first)
- `startTime` (optional): Start timestamp
- `endTime` (optional): End timestamp

**Rate Limits**:
- Token bucket mechanism
- 1 request per second refill rate
- 1-minute interval
- Headers returned: `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-reset`
- 429 error if exceeded with `retry-after` header

**Response Structure**:
```json
[
  {
    "symbol": "XBTUSD",
    "side": "Buy",
    "price": 9910,
    "leavesQty": 0,
    "orderID": "abc123",
    "timestamp": "2020-01-26T12:00:00.000Z"
  }
]
```

**Historical Data**: Available at `https://public.bitmex.com/`

### ✅ WebSocket - Real-Time Liquidations
**Stream URL**: `wss://www.bitmex.com/realtime`

**Subscription Formats**:
- On connection: `wss://www.bitmex.com/realtime?subscribe=liquidation:XBTUSD`
- After connection: `{"op": "subscribe", "args": ["liquidation:XBTUSD"]}`

**Response Structure**:
```json
{
  "table": "liquidation",
  "action": "insert",
  "data": [
    {
      "orderID": "abc123",
      "symbol": "XBTUSD",
      "side": "Buy",
      "price": 9910,
      "leavesQty": 0
    }
  ]
}
```

**Rate Limits**:
- Connection limit: 20 connections per hour (burst rate)
- 429 error if exceeded
- ✅ Once connected, WebSocket is NOT rate-limited
- Recommended over REST polling

---

## 5. GATE.IO (Good Support)

### ✅ REST API - Historical Liquidations
**Endpoint**: `GET /futures/{settle}/liq_orders`

**Base URL**: `https://api.gateio.ws/api/v4`

**Parameters**:
- `settle`: Settlement currency (e.g., usdt, btc)
- `contract` (optional): Contract name
- `from` (optional): Start timestamp
- `to` (optional): End timestamp
- `limit` (optional): Max results

**Python Example**:
```python
list_liquidated_orders(settle, contract=contract, _from=_from, to=to, limit=limit)
```

### ✅ WebSocket - Real-Time Liquidations
**Stream URL**: `wss://fx-ws.gateio.ws/v4/ws/{settle}`

**Channel**: `futures.public_liquidates`

**Subscription Format**:
```json
{
  "time": 1545404023,
  "channel": "futures.public_liquidates",
  "event": "subscribe",
  "payload": ["BTCUSDT"]
}
```

**Private User Liquidations**: `futures.liquidates` (requires authentication)

**Response Structure**:
```json
{
  "time": 1545404023,
  "channel": "futures.public_liquidates",
  "event": "update",
  "result": {
    "entry_price": 9900,
    "fill_price": 9910,
    "leverage": 10,
    "mark_price": 9915,
    "order_id": 123456,
    "size": 100,
    "contract": "BTCUSDT"
  }
}
```

**Performance**: 30% lower latency in Spot, 40% lower in Futures (vs v3)

---

## 6. OKX (Unclear Documentation)

### ❓ REST API - Unclear
**Documentation states**: API v5 supports liquidation orders in order channel

**Notes**:
- Order channel of API v5 supports private liquidation orders
- "Category" field indicates partial vs full liquidation
- Liquidation/ADL does NOT generate order update (system-owned)

**Endpoints**: Not clearly documented in public resources

### ✅ WebSocket - Exists
**Stream URL**:
- Public: `/ws/v5/public`
- Private: `/ws/v5/private`

**Rate Limits**:
- 3 requests per second (per IP) for public channels
- 480 subscribe/unsubscribe/login requests per hour per connection

**Historical Data**: Available since 2020-12-18 (via third-party like Tardis.dev)

**Notes**:
- WebSocket format matches historical data format
- Liquidation orders available through WebSocket channels
- Documentation not comprehensive for liquidation-specific endpoints

---

## 7. DERIBIT (Limited/Unclear)

### ❌ REST API - Not Found
**No dedicated liquidation endpoint** in official API documentation

**Related Endpoints**:
- `/private/get_positions` - Current positions
- `/private/get_settlement_history_by_instrument` - Settlement events
- User trades subscriptions - Execution activity

### ❓ WebSocket - Unclear
**Subscription System**: `public/subscribe` and `private/subscribe` methods

**Notes**:
- Order objects contain `is_liquidation` boolean field
- Liquidation-related events MAY be tracked through subscription system
- No specific "liquidation" channel documented
- Subscription channels determine event types received

**Possible Channels**:
- `user.portfolio.{currency}` - Portfolio changes (may include liquidations)
- Settlement history - May capture liquidation events

**Third-Party Data**:
- Tardis.dev provides historical liquidation data
- Cryptofeed library supports Deribit liquidations
- Amberdata provides liquidation endpoints (REST + WebSocket)

---

## 8. BITGET (Limited Support - Margin Only)

### ✅ REST API - Margin Liquidations Only
**Endpoint**: `GET /api/v2/margin/{marginType}/liquidation-orders`

**Parameters**:
- `marginType`: Type of margin account

**Notes**:
- Only available for margin trading
- NOT available for futures contracts

### ❌ WebSocket - No Public Liquidation Channel
**Available Channels**:
- `futures.account` - Account information
- `futures.positions` - Position updates
- `futures.orders` - Order updates
- `futures.trade` - Public trades
- `futures.ticker` - Market data

**Notes**:
- No dedicated public liquidation channel for futures
- Position channel may show liquidations on own account
- Must monitor through REST API or position updates

**API Versions**:
- V3/UTA (Unified Trading Account) - Recommended for new projects
- V2 - Legacy, if not upgraded to UTA

---

## Rate Limit Summary

| Exchange | REST Rate Limit | WebSocket Connection Limit | WebSocket Message Limit |
|----------|----------------|---------------------------|------------------------|
| **Binance** | Varies by weight | 1024 streams/connection | 10 msgs/second |
| **Bybit** | 600 req/5s per IP | 500 conn/5min, 1000/IP | 60 subscriptions/conn |
| **Bitfinex** | 3 req/min (liquidations) | Public: 20/min, Auth: 5/15s | Not specified |
| **Bitmex** | 1 req/second (refill) | 20 conn/hour (burst) | Unlimited once connected |
| **Gate.io** | Not specified | Not specified | Not specified |
| **OKX** | Not specified | 480 ops/hour/conn | 3 req/sec (public) |
| **Deribit** | Not specified | Not specified | HTTP not supported |
| **Bitget** | Not specified | 4096 bytes/subscription | Not specified |

---

## Data Field Comparison

| Exchange | Timestamp | Symbol | Side/Direction | Quantity | Price | USD Value |
|----------|-----------|--------|----------------|----------|-------|-----------|
| **Binance** | ✅ `T` | ✅ `s` | ✅ `S` (SELL/BUY) | ✅ `q` | ✅ `ap` | ❌ Calculate |
| **Bybit** | ✅ `T` | ✅ `s` | ✅ `S` (Buy/Sell) | ✅ `v` | ✅ `p` | ❌ Calculate |
| **Bitfinex** | ✅ `[2]` | ✅ `[4]` | ✅ `[5]` (+/-) | ✅ `[5]` | ✅ `[6]`/`[11]` | ❌ Calculate |
| **Bitmex** | ✅ `timestamp` | ✅ `symbol` | ✅ `side` | ✅ `leavesQty` | ✅ `price` | ❌ Calculate |
| **Gate.io** | ❌ ? | ✅ `contract` | ❌ ? | ✅ `size` | ✅ `fill_price` | ❌ Calculate |
| **OKX** | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| **Deribit** | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| **Bitget** | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |

---

## Integration Priority Ranking

### Tier 1 - Immediate Integration (Full Support)
1. **Binance** - Already implemented, most volume
2. **Bitmex** - Full REST + WebSocket, unlimited history
3. **Bitfinex** - Full REST + WebSocket, unlimited history

### Tier 2 - High Priority (Good Support)
4. **Gate.io** - Full REST + WebSocket support
5. **Bybit** - WebSocket only but complete real-time data

### Tier 3 - Research Required
6. **OKX** - Unclear documentation, needs investigation
7. **Deribit** - Limited official docs, third-party sources available

### Tier 4 - Low Priority
8. **Bitget** - Limited to margin only, no futures liquidations

---

## Implementation Recommendations

### For Real-Time Monitoring
**Priority Order**:
1. Binance (✅ already implemented)
2. Bybit - High volume, good WebSocket
3. Bitfinex - Clean API, good documentation
4. Bitmex - Institutional focus
5. Gate.io - Additional coverage

### For Historical Analysis
**Priority Order**:
1. Bitfinex - Unlimited history, clean REST API
2. Bitmex - Unlimited history, good filtering
3. Binance - Limited to 7 days but high volume
4. Gate.io - Historical available
5. Third-party (Tardis.dev, Amberdata) for exchanges without native support

### Architecture Considerations

**Multi-Exchange Liquidation Monitor**:
```python
class MultiExchangeLiquidationMonitor:
    """
    Unified liquidation monitor across exchanges
    """

    exchanges = {
        'binance': {
            'websocket': 'wss://fstream.binance.com/ws/!forceOrder@arr',
            'rest': 'https://fapi.binance.com/fapi/v1/allForceOrders',
            'priority': 1,
            'historical_days': 7
        },
        'bybit': {
            'websocket': 'wss://stream.bybit.com/v5/public/linear',
            'channel': 'allLiquidation.{symbol}',
            'rest': None,
            'priority': 2,
            'historical_days': 0
        },
        'bitfinex': {
            'websocket': 'wss://api-pub.bitfinex.com/ws/2',
            'channel': 'status',
            'key': 'liq:global',
            'rest': 'https://api-pub.bitfinex.com/v2/liquidations/hist',
            'priority': 3,
            'historical_days': -1  # unlimited
        },
        'bitmex': {
            'websocket': 'wss://www.bitmex.com/realtime',
            'channel': 'liquidation:{symbol}',
            'rest': 'https://www.bitmex.com/api/v1/liquidation',
            'priority': 4,
            'historical_days': -1  # unlimited
        },
        'gateio': {
            'websocket': 'wss://fx-ws.gateio.ws/v4/ws/{settle}',
            'channel': 'futures.public_liquidates',
            'rest': 'https://api.gateio.ws/api/v4/futures/{settle}/liq_orders',
            'priority': 5,
            'historical_days': -1  # likely available
        }
    }
```

---

## Technical Implementation Notes

### WebSocket Connection Strategy
1. **Parallel Connections**: Connect to multiple exchanges simultaneously
2. **Automatic Reconnection**: Handle disconnections gracefully
3. **Rate Limit Compliance**: Respect per-exchange limits
4. **Health Monitoring**: Ping/pong heartbeat tracking

### Data Normalization
**Unified Liquidation Model**:
```python
@dataclass
class UnifiedLiquidation:
    exchange: str           # Exchange name
    symbol: str            # Normalized symbol (BTCUSDT)
    side: str              # 'LONG' or 'SHORT'
    quantity: float        # Position size
    price: float           # Liquidation price
    value_usd: float       # USD value
    timestamp: datetime    # Event timestamp
    liquidation_type: str  # 'partial' or 'full' (if available)
    raw_data: dict         # Original response for debugging
```

### Aggregation Strategy
1. **Symbol Normalization**: Convert exchange-specific symbols to unified format
2. **Side Standardization**: Map exchange-specific directions to LONG/SHORT
3. **USD Calculation**: Compute USD values from quantity * price
4. **Deduplication**: Handle potential duplicate events across exchanges
5. **Time Synchronization**: Normalize timestamps to UTC

---

## Current System Status

### ✅ Currently Implemented
- **Binance WebSocket**: `wss://fstream.binance.com/ws/!forceOrder@arr`
- **Location**: `/services/telegram-bot/liquidation_monitor.py`
- **Status**: Coded but not activated
- **Features**:
  - Real-time liquidation tracking
  - Cascade detection (6-factor analysis)
  - Dynamic thresholds
  - Institutional filtering ($100K+ minimum)

### 🔄 Ready for Integration
Based on this research, the following exchanges can be added immediately:
1. **Bybit** - WebSocket only, similar to Binance implementation
2. **Bitfinex** - Full support, both REST and WebSocket
3. **Bitmex** - Full support, unlimited historical data

---

## Conclusion

**Best Overall Support**:
- 🥇 **Bitfinex** - Full REST + WebSocket, unlimited history, clean API
- 🥈 **Bitmex** - Full REST + WebSocket, unlimited history, institutional focus
- 🥉 **Binance** - Full support but 7-day REST limit, highest volume

**Recommended Integration Path**:
1. ✅ Keep Binance (already implemented)
2. Add Bybit (high volume, simple WebSocket)
3. Add Bitfinex (best historical data)
4. Add Bitmex (institutional relevance)
5. Add Gate.io (additional coverage)

**Total Potential Coverage**: 5 major exchanges with real-time liquidation monitoring

**Missing Coverage**:
- OKX (needs investigation)
- Deribit (use third-party or indirect methods)
- Bitget (futures not supported)

This research provides a complete foundation for implementing multi-exchange liquidation monitoring with prioritized integration based on data availability and quality.

---

*Research completed: 2025-10-20*
*Exchanges analyzed: 8*
*Documentation sources: Official APIs, community resources, third-party data providers*
