# Liquidation API Quick Reference Guide
**Fast lookup for implementing liquidation data collection**

---

## 🚀 Quick Start - WebSocket Connections

### 1. BINANCE (Easiest - Already Implemented)
```python
import websockets
import json

async def binance_liquidations():
    uri = "wss://fstream.binance.com/ws/!forceOrder@arr"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            liq = data['o']
            print(f"{liq['s']}: {liq['S']} {liq['q']} @ ${liq['ap']}")
```

### 2. BYBIT (Simple)
```python
async def bybit_liquidations(symbol='BTCUSDT'):
    uri = "wss://stream.bybit.com/v5/public/linear"
    subscription = {
        "op": "subscribe",
        "args": [f"allLiquidation.{symbol}"]
    }
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(subscription))
        async for message in ws:
            data = json.loads(message)
            if data.get('topic', '').startswith('allLiquidation'):
                for liq in data['data']:
                    print(f"{liq['s']}: {liq['S']} {liq['v']} @ ${liq['p']}")
```

### 3. BITFINEX
```python
async def bitfinex_liquidations():
    uri = "wss://api-pub.bitfinex.com/ws/2"
    subscription = {
        "event": "subscribe",
        "channel": "status",
        "key": "liq:global"
    }
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(subscription))
        async for message in ws:
            data = json.loads(message)
            if isinstance(data, list) and len(data) > 1:
                if data[1] and isinstance(data[1], list):
                    for liq in data[1]:
                        if liq[0] == 'pos':  # liquidation message
                            print(f"{liq[3]}: {liq[4]} @ ${liq[5]}")
```

### 4. BITMEX
```python
async def bitmex_liquidations(symbol='XBTUSD'):
    uri = f"wss://www.bitmex.com/realtime?subscribe=liquidation:{symbol}"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            if data.get('table') == 'liquidation':
                for liq in data.get('data', []):
                    print(f"{liq['symbol']}: {liq['side']} @ ${liq['price']}")
```

### 5. GATE.IO
```python
async def gateio_liquidations(settle='usdt'):
    uri = f"wss://fx-ws.gateio.ws/v4/ws/{settle}"
    subscription = {
        "time": int(time.time()),
        "channel": "futures.public_liquidates",
        "event": "subscribe",
        "payload": ["BTCUSDT"]
    }
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(subscription))
        async for message in ws:
            data = json.loads(message)
            if data.get('channel') == 'futures.public_liquidates':
                liq = data['result']
                print(f"{liq['contract']}: {liq['size']} @ ${liq['fill_price']}")
```

---

## 📊 REST API - Historical Data

### 1. BINANCE (7 days max)
```python
import requests

def binance_historical_liquidations(symbol='BTCUSDT', limit=100):
    url = "https://fapi.binance.com/fapi/v1/allForceOrders"
    params = {'symbol': symbol, 'limit': limit}
    response = requests.get(url, params=params)
    return response.json()

# Example
liquidations = binance_historical_liquidations('BTCUSDT', 500)
for liq in liquidations:
    print(f"{liq['symbol']}: {liq['side']} {liq['origQty']} @ ${liq['averagePrice']}")
```

### 2. BITFINEX (Unlimited)
```python
def bitfinex_historical_liquidations(start=None, end=None):
    url = "https://api-pub.bitfinex.com/v2/liquidations/hist"
    params = {}
    if start:
        params['start'] = start
    if end:
        params['end'] = end
    response = requests.get(url, params=params)
    return response.json()

# Example - last 24 hours
import time
end_time = int(time.time() * 1000)
start_time = end_time - (24 * 60 * 60 * 1000)
liquidations = bitfinex_historical_liquidations(start_time, end_time)

for liq in liquidations:
    symbol = liq[4]
    amount = liq[5]
    price = liq[6]
    side = 'LONG' if amount > 0 else 'SHORT'
    print(f"{symbol}: {side} {abs(amount)} @ ${price}")
```

### 3. BITMEX (Unlimited)
```python
def bitmex_historical_liquidations(symbol='XBTUSD', count=100):
    url = "https://www.bitmex.com/api/v1/liquidation"
    params = {
        'symbol': symbol,
        'count': count,
        'reverse': True  # newest first
    }
    response = requests.get(url, params=params)
    return response.json()

# Example
liquidations = bitmex_historical_liquidations('XBTUSD', 500)
for liq in liquidations:
    print(f"{liq['symbol']}: {liq['side']} @ ${liq['price']}")
```

### 4. GATE.IO
```python
def gateio_historical_liquidations(settle='usdt', contract=None, limit=100):
    url = f"https://api.gateio.ws/api/v4/futures/{settle}/liq_orders"
    params = {'limit': limit}
    if contract:
        params['contract'] = contract
    response = requests.get(url, params=params)
    return response.json()

# Example
liquidations = gateio_historical_liquidations('usdt', 'BTCUSDT', 500)
for liq in liquidations:
    print(f"{liq['contract']}: {liq['size']} @ ${liq['fill_price']}")
```

---

## 🔄 Data Normalization Helpers

### Unified Data Model
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class NormalizedLiquidation:
    """Unified liquidation data structure"""
    exchange: str
    symbol: str  # Normalized to BTCUSDT format
    side: Literal['LONG', 'SHORT']
    quantity: float
    price: float
    value_usd: float
    timestamp: datetime
    raw_data: dict

def normalize_binance(data: dict) -> NormalizedLiquidation:
    """Normalize Binance liquidation data"""
    o = data['o']
    return NormalizedLiquidation(
        exchange='binance',
        symbol=o['s'],
        side='LONG' if o['S'] == 'SELL' else 'SHORT',
        quantity=float(o['q']),
        price=float(o['ap']),
        value_usd=float(o['q']) * float(o['ap']),
        timestamp=datetime.fromtimestamp(o['T'] / 1000),
        raw_data=data
    )

def normalize_bybit(data: dict) -> list[NormalizedLiquidation]:
    """Normalize Bybit liquidation data"""
    results = []
    for liq in data['data']:
        results.append(NormalizedLiquidation(
            exchange='bybit',
            symbol=liq['s'],
            side='SHORT' if liq['S'] == 'Buy' else 'LONG',
            quantity=float(liq['v']),
            price=float(liq['p']),
            value_usd=float(liq['v']) * float(liq['p']),
            timestamp=datetime.fromtimestamp(liq['T'] / 1000),
            raw_data=liq
        ))
    return results

def normalize_bitfinex(liq: list) -> NormalizedLiquidation:
    """Normalize Bitfinex liquidation data"""
    return NormalizedLiquidation(
        exchange='bitfinex',
        symbol=liq[4].replace('tBTCF0:USTF0', 'BTCUSDT'),  # Map symbols
        side='LONG' if liq[5] > 0 else 'SHORT',
        quantity=abs(float(liq[5])),
        price=float(liq[6]),
        value_usd=abs(float(liq[5])) * float(liq[6]),
        timestamp=datetime.fromtimestamp(liq[2] / 1000),
        raw_data=liq
    )

def normalize_bitmex(liq: dict) -> NormalizedLiquidation:
    """Normalize Bitmex liquidation data"""
    return NormalizedLiquidation(
        exchange='bitmex',
        symbol=liq['symbol'].replace('XBT', 'BTC'),  # XBTUSD -> BTCUSD
        side='SHORT' if liq['side'] == 'Buy' else 'LONG',
        quantity=float(liq.get('leavesQty', 0)),
        price=float(liq['price']),
        value_usd=0,  # Calculate based on inverse contracts
        timestamp=datetime.fromisoformat(liq['timestamp'].replace('Z', '+00:00')),
        raw_data=liq
    )

def normalize_gateio(liq: dict) -> NormalizedLiquidation:
    """Normalize Gate.io liquidation data"""
    return NormalizedLiquidation(
        exchange='gateio',
        symbol=liq['contract'],
        side='LONG',  # Determine from data if available
        quantity=float(liq['size']),
        price=float(liq['fill_price']),
        value_usd=float(liq['size']) * float(liq['fill_price']),
        timestamp=datetime.now(),  # Use event timestamp if available
        raw_data=liq
    )
```

---

## 📋 Symbol Mapping

### Exchange Symbol Formats
```python
SYMBOL_MAPPINGS = {
    'binance': {
        'BTCUSDT': 'BTCUSDT',
        'ETHUSDT': 'ETHUSDT',
        'format': '{base}{quote}'
    },
    'bybit': {
        'BTCUSDT': 'BTCUSDT',
        'ETHUSDT': 'ETHUSDT',
        'format': '{base}{quote}'
    },
    'bitfinex': {
        'BTCUSDT': 'tBTCF0:USTF0',
        'ETHUSDT': 'tETHF0:USTF0',
        'format': 't{base}F0:USTF0'
    },
    'bitmex': {
        'BTCUSDT': 'XBTUSD',
        'ETHUSDT': 'ETHUSD',
        'format': 'XBT{quote}'  # Special: BTC -> XBT
    },
    'gateio': {
        'BTCUSDT': 'BTC_USDT',
        'ETHUSDT': 'ETH_USDT',
        'format': '{base}_{quote}'
    }
}

def normalize_symbol(exchange: str, symbol: str) -> str:
    """Convert exchange-specific symbol to standard format"""
    conversions = {
        'tBTCF0:USTF0': 'BTCUSDT',
        'XBTUSD': 'BTCUSDT',
        'BTC_USDT': 'BTCUSDT',
        'tETHF0:USTF0': 'ETHUSDT',
        'ETHUSD': 'ETHUSDT',
        'ETH_USDT': 'ETHUSDT',
    }
    return conversions.get(symbol, symbol)

def exchange_symbol(standard: str, exchange: str) -> str:
    """Convert standard symbol to exchange-specific format"""
    if exchange == 'bitfinex' and standard == 'BTCUSDT':
        return 'tBTCF0:USTF0'
    elif exchange == 'bitmex' and standard == 'BTCUSDT':
        return 'XBTUSD'
    elif exchange == 'gateio':
        return standard.replace('USDT', '_USDT')
    return standard
```

---

## ⚡ Rate Limit Helpers

### Rate Limiter Implementation
```python
import asyncio
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.allowance = requests_per_second
        self.last_check = datetime.now()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Wait until request is allowed"""
        async with self.lock:
            current = datetime.now()
            time_passed = (current - self.last_check).total_seconds()
            self.last_check = current
            self.allowance += time_passed * self.rate

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) / self.rate
                await asyncio.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0

# Exchange-specific rate limiters
RATE_LIMITERS = {
    'binance': RateLimiter(10),  # 10 messages per second
    'bybit': RateLimiter(2),     # Conservative limit
    'bitfinex': RateLimiter(0.05),  # 3 requests per minute
    'bitmex': RateLimiter(1),    # 1 request per second
    'gateio': RateLimiter(1),    # Conservative estimate
}

async def rate_limited_request(exchange: str, request_func):
    """Make rate-limited API request"""
    limiter = RATE_LIMITERS.get(exchange)
    if limiter:
        await limiter.acquire()
    return await request_func()
```

---

## 🔍 Testing Quick Commands

### Test WebSocket Connections
```bash
# Binance
wscat -c "wss://fstream.binance.com/ws/!forceOrder@arr"

# Bybit
wscat -c "wss://stream.bybit.com/v5/public/linear"
# Then send: {"op":"subscribe","args":["allLiquidation.BTCUSDT"]}

# Bitfinex
wscat -c "wss://api-pub.bitfinex.com/ws/2"
# Then send: {"event":"subscribe","channel":"status","key":"liq:global"}

# Bitmex
wscat -c "wss://www.bitmex.com/realtime?subscribe=liquidation:XBTUSD"
```

### Test REST Endpoints
```bash
# Binance
curl "https://fapi.binance.com/fapi/v1/allForceOrders?symbol=BTCUSDT&limit=10"

# Bitfinex
curl "https://api-pub.bitfinex.com/v2/liquidations/hist"

# Bitmex
curl "https://www.bitmex.com/api/v1/liquidation?symbol=XBTUSD&count=10&reverse=true"

# Gate.io
curl "https://api.gateio.ws/api/v4/futures/usdt/liq_orders?contract=BTC_USDT&limit=10"
```

---

## 🛠️ Production Implementation Template

### Multi-Exchange Manager
```python
import asyncio
from typing import Dict, List, Callable

class MultiExchangeLiquidationMonitor:
    """Manage liquidation monitoring across multiple exchanges"""

    def __init__(self, callback: Callable[[NormalizedLiquidation], None]):
        self.callback = callback
        self.connections: Dict[str, asyncio.Task] = {}
        self.running = False

    async def start(self, exchanges: List[str]):
        """Start monitoring specified exchanges"""
        self.running = True

        for exchange in exchanges:
            if exchange == 'binance':
                task = asyncio.create_task(self._monitor_binance())
            elif exchange == 'bybit':
                task = asyncio.create_task(self._monitor_bybit())
            elif exchange == 'bitfinex':
                task = asyncio.create_task(self._monitor_bitfinex())
            elif exchange == 'bitmex':
                task = asyncio.create_task(self._monitor_bitmex())
            elif exchange == 'gateio':
                task = asyncio.create_task(self._monitor_gateio())
            else:
                continue

            self.connections[exchange] = task

    async def stop(self):
        """Stop all monitors"""
        self.running = False
        for task in self.connections.values():
            task.cancel()
        await asyncio.gather(*self.connections.values(), return_exceptions=True)

    async def _monitor_binance(self):
        """Monitor Binance liquidations"""
        while self.running:
            try:
                async with websockets.connect(
                    "wss://fstream.binance.com/ws/!forceOrder@arr"
                ) as ws:
                    async for message in ws:
                        data = json.loads(message)
                        liq = normalize_binance(data)
                        await self.callback(liq)
            except Exception as e:
                print(f"Binance error: {e}")
                await asyncio.sleep(5)

    # Similar methods for other exchanges...

# Usage
async def handle_liquidation(liq: NormalizedLiquidation):
    """Process normalized liquidation"""
    if liq.value_usd >= 100_000:  # Filter threshold
        print(f"[{liq.exchange.upper()}] {liq.symbol}: "
              f"{liq.side} ${liq.value_usd:,.0f}")

monitor = MultiExchangeLiquidationMonitor(handle_liquidation)
await monitor.start(['binance', 'bybit', 'bitfinex', 'bitmex'])
```

---

## 📈 Recommended Integration Order

1. **Start**: Binance (already implemented)
2. **Add**: Bybit (easy, high volume)
3. **Add**: Bitfinex (best historical data)
4. **Add**: Bitmex (institutional focus)
5. **Add**: Gate.io (additional coverage)

**Total Coverage**: 5 major exchanges, ~70%+ of global liquidation volume

---

## 🔗 Official Documentation Links

- **Binance**: https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams
- **Bybit**: https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
- **Bitfinex**: https://docs.bitfinex.com/reference/rest-public-liquidations
- **Bitmex**: https://www.bitmex.com/app/wsAPI
- **Gate.io**: https://www.gate.com/docs/developers/futures/ws/en/
- **OKX**: https://www.okx.com/docs-v5/en/
- **Deribit**: https://docs.deribit.com/
- **Bitget**: https://www.bitget.com/api-doc/

---

*Quick reference created: 2025-10-20*
*For detailed analysis, see: EXCHANGE_LIQUIDATION_API_RESEARCH.md*
