# Open Interest (OI) System Architecture Analysis

## 📍 Command Location
**File**: `services/telegram-bot/main.py:947`
```python
async def oi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open Interest analysis command with exact target formatting"""
```

## 🏗️ Core Architecture

### 1. **Telegram Bot Layer** (`services/telegram-bot/main.py`)
- Handles `/oi <symbol>` commands
- Calls `market_client.get_oi_analysis(symbol)`
- Formats and displays results to user

### 2. **Aggregator Layer** (`services/market-data/unified_oi_aggregator.py`)
- **Class**: `UnifiedOIAggregator`
- **Purpose**: Orchestrates data collection from all 6 exchanges
- **Key Method**: `get_unified_oi_data(base_symbol: str)`
- Fetches data from all providers in parallel
- Aggregates results into unified format
- Performs validation

### 3. **Data Models** (`services/market-data/oi_engine_v2.py`)
- `MarketType` enum: USDT, USDC, USD (inverse)
- `MarketOIData`: Single market OI data
- `ExchangeOIResult`: Complete OI result for one exchange
- `BaseExchangeOIProvider`: Abstract base class for providers

### 4. **Exchange Providers** (`services/market-data/*_oi_provider.py`)
All implement `BaseExchangeOIProvider` interface:
- **binance_oi_provider.py**: 3 markets (USDT, USDC, USD)
- **bybit_oi_provider.py**: 3 markets (USDT, USDC, USD)
- **okx_oi_provider.py**: 3 markets (USDT, USDC, USD)
- **gateio_oi_provider_working.py**: USDT market
- **bitget_oi_provider_working.py**: 2 markets (USDT, USD)
- **hyperliquid_oi_provider.py**: Single market

## 🔄 Data Flow

```
User: /oi BTC
    ↓
TelegramBot.oi_command()
    ↓
MarketDataClient.get_oi_analysis("BTC")
    ↓
Market Data Service /multi_oi endpoint
    ↓
UnifiedOIAggregator.get_unified_oi_data("BTC")
    ↓ (parallel fetches)
    ├─ BinanceOIProvider.get_oi_data("BTC")
    ├─ BybitOIProvider.get_oi_data("BTC")
    ├─ OKXOIProvider.get_oi_data("BTC")
    ├─ GateIOOIProvider.get_oi_data("BTC")
    ├─ BitgetOIProvider.get_oi_data("BTC")
    └─ HyperliquidOIProvider.get_oi_data("BTC")
    ↓
Aggregation & Validation
    ↓
UnifiedOIResponse
    ↓
Formatted message back to user
```

## 📊 Data Collected Per Exchange

For each exchange, the provider fetches:
- **Open Interest** (in tokens and USD)
- **Price** (current mark price)
- **Funding Rate** (for perpetuals)
- **24h Volume** (in tokens and USD)
- **Market Type** (USDT, USDC, or USD inverse)

## 🎯 Current Exchanges Supported

1. **Binance** (3 markets)
   - BTCUSDT (linear)
   - BTCUSDC (linear)
   - BTCUSD_PERP (inverse)

2. **Bybit** (3 markets)
   - BTCUSDT (linear)
   - BTCUSDC (linear)
   - BTCUSD (inverse)

3. **OKX** (3 markets)
   - BTCUSDT (linear)
   - BTCUSDC (linear)
   - BTCUSD (inverse)

4. **Gate.io** (1 market)
   - BTC_USDT (linear)

5. **Bitget** (2 markets)
   - BTCUSDT (linear)
   - BTCUSD (inverse)

6. **Hyperliquid** (1 market)
   - BTC (native)

**Total**: Up to 13 markets aggregated

## 🔑 Key Code Patterns

### Provider Interface
```python
class BaseExchangeOIProvider(ABC):
    @abstractmethod
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        pass
    
    @abstractmethod
    def get_supported_market_types(self) -> List[MarketType]:
        pass
    
    @abstractmethod
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        pass
```

### Each Provider Implements
1. Format symbol for exchange API
2. Fetch OI data from exchange REST API
3. Parse response into `MarketOIData` objects
4. Calculate USD values (linear vs inverse contracts)
5. Return `ExchangeOIResult` with validation

## 🛠️ Testing Functions

Each provider has built-in test functions:
```python
async def test_binance_provider():
    provider = BinanceOIProvider()
    result = await provider.get_oi_data("BTC")
    # ... displays results
    await provider.close()
```

The unified aggregator also has testing:
```python
async def test_unified_system():
    aggregator = UnifiedOIAggregator()
    result = await aggregator.get_unified_oi_data("BTC")
    # ... displays aggregated results
    await aggregator.close()
```
