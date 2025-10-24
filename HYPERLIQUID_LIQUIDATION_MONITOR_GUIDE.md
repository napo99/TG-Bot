# Hyperliquid Liquidation Monitor - Implementation Guide

## Overview

Real-time blockchain-based liquidation tracking for Hyperliquid DEX. This implementation monitors all liquidations on the Hyperliquid L1 blockchain via WebSocket and alerts on significant events.

## Architecture

### Components

1. **HyperliquidLiquidationProvider** (`services/market-data/hyperliquid_liquidation_provider.py`)
   - WebSocket connection to Hyperliquid DEX
   - Real-time trade stream monitoring
   - Liquidation filtering and parsing
   - Multi-asset support (BTC, ETH, SOL, etc.)

2. **MultiExchangeLiquidationMonitor** (`services/telegram-bot/multi_exchange_liquidation_monitor.py`)
   - Orchestrates multiple exchange monitors
   - Unified alert system
   - Cross-exchange cascade detection
   - Health monitoring per exchange

3. **CompactLiquidation Model** (`shared/models/compact_liquidation.py`)
   - Memory-optimized liquidation storage (18 bytes per record)
   - Hyperliquid data parsing
   - Efficient ring buffer implementation

4. **Configuration** (`shared/config/alert_thresholds.py`)
   - Environment-based configuration
   - Exchange-specific thresholds
   - WebSocket settings

## Features

### Hyperliquid-Specific Features

- **On-Chain Liquidation Tracking**: Direct monitoring of blockchain liquidations
- **Real-Time WebSocket**: Sub-second latency via `wss://api.hyperliquid.xyz/ws`
- **Multi-Asset Support**: Monitor all perpetual markets (BTC, ETH, SOL, etc.)
- **Institutional Filtering**: Focus on significant liquidations ($100K+ default)
- **Cascade Detection**: Identify liquidation cascades across assets
- **Exchange Tagging**: Alerts clearly identify Hyperliquid liquidations

### Data Structure

#### Hyperliquid Trade/Liquidation Format
```json
{
  "channel": "trades",
  "data": [
    {
      "coin": "BTC",
      "side": "A",           // "A" = Ask/Sell (long liquidation)
                             // "B" = Bid/Buy (short liquidation)
      "px": "45000.5",       // Price
      "sz": "0.5",           // Size
      "time": 1702000000000, // Timestamp (ms)
      "hash": "0x...",       // Transaction hash
      "tid": 12345678,       // Trade ID
      "liquidation": true    // Liquidation flag
    }
  ]
}
```

## Installation

### 1. Install Dependencies

```bash
# Market data service
cd services/market-data
pip install -r requirements.txt

# Telegram bot service
cd services/telegram-bot
pip install -r requirements.txt
```

### 2. Environment Configuration

Add to your `.env` file:

```bash
# Hyperliquid Liquidation Monitoring
ENABLE_HYPERLIQUID_LIQUIDATION_ALERTS=true
LIQUIDATION_EXCHANGES=binance,hyperliquid
HYPERLIQUID_SYMBOLS=BTC,ETH,SOL

# Hyperliquid-specific thresholds
HYPERLIQUID_THRESHOLD_BTC=100000    # $100K minimum for BTC
HYPERLIQUID_THRESHOLD_ETH=50000     # $50K minimum for ETH
HYPERLIQUID_THRESHOLD_SOL=25000     # $25K minimum for SOL

# Telegram alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Integration Options

#### Option A: Use Multi-Exchange Monitor (Recommended)

```python
from services.telegram_bot.multi_exchange_liquidation_monitor import MultiExchangeLiquidationMonitor

# Initialize
monitor = MultiExchangeLiquidationMonitor(
    bot_instance=bot,
    market_data_url="http://localhost:8001",
    enabled_exchanges=["binance", "hyperliquid"]
)

# Start monitoring
await monitor.start_monitoring()

# Get status
status = monitor.get_status()
print(f"Total liquidations: {status['total_liquidations']}")
print(f"Exchanges: {status['exchange_stats']}")
```

#### Option B: Use Hyperliquid Provider Directly

```python
from services.market_data.hyperliquid_liquidation_provider import HyperliquidLiquidationProvider

# Initialize
provider = HyperliquidLiquidationProvider(symbols=["BTC", "ETH", "SOL"])

# Monitor liquidations
async for liquidation in provider.start_monitoring():
    print(f"Liquidation: {liquidation.actual_value_usd:,.0f} USD")
    print(f"  Symbol: {liquidation.symbol_hash}")
    print(f"  Side: {liquidation.side_str}")
    print(f"  Price: ${liquidation.actual_price:,.2f}")
```

## Usage Examples

### Example 1: Basic Integration

```python
import asyncio
from services.telegram_bot.multi_exchange_liquidation_monitor import MultiExchangeLiquidationMonitor

async def main():
    # Create bot instance (your existing bot)
    from telegram.ext import Application
    bot = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Initialize monitor
    monitor = MultiExchangeLiquidationMonitor(
        bot_instance=bot,
        enabled_exchanges=["hyperliquid"]  # Hyperliquid only
    )

    # Start monitoring
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Custom Symbol Filtering

```python
# Monitor specific symbols only
provider = HyperliquidLiquidationProvider(symbols=["BTC", "ETH"])

# Or monitor all symbols
provider = HyperliquidLiquidationProvider(symbols=None)
```

### Example 3: Get Provider Statistics

```python
# Get detailed stats
stats = provider.get_stats()
print(f"Liquidations tracked: {stats['liquidation_count']}")
print(f"Total trades seen: {stats['total_trade_count']}")
print(f"Connection errors: {stats['connection_errors']}")
print(f"Monitored symbols: {stats['symbols']}")
```

### Example 4: Health Monitoring

```python
# Get comprehensive status
status = monitor.get_status()

for exchange, stats in status['exchange_stats'].items():
    print(f"{exchange}:")
    print(f"  Status: {stats['status']}")
    print(f"  Liquidations: {stats['liquidations_processed']}")
    print(f"  Last event: {stats['last_liquidation']}")
    print(f"  Errors: {stats['errors']}")
```

## Alert Format

### Hyperliquid Liquidation Alert

```
🟣 HYPERLIQUID

🚨 BTC LIQUIDATION - 🐋 WHALE
📉 LONG liquidated
💰 $1.2M (25.5 BTC)
📊 Price: $47,058.82 | Leverage: ~3-5x
🎯 Impact: HIGH - Watch cascade
🕐 14:23:45
```

### Alert Classifications

- **🐋 WHALE**: $1M+ liquidation
- **🦈 INSTITUTIONAL**: $500K - $1M liquidation
- **🐟 LARGE TRADER**: $100K - $500K liquidation
- **📊 TRADER**: Below $100K (usually filtered)

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_HYPERLIQUID_LIQUIDATION_ALERTS` | `true` | Enable/disable Hyperliquid alerts |
| `LIQUIDATION_EXCHANGES` | `binance,hyperliquid` | Comma-separated list of exchanges |
| `HYPERLIQUID_SYMBOLS` | `BTC,ETH,SOL` | Symbols to monitor (empty = all) |
| `HYPERLIQUID_THRESHOLD_BTC` | `100000` | BTC liquidation threshold (USD) |
| `HYPERLIQUID_THRESHOLD_ETH` | `50000` | ETH liquidation threshold (USD) |
| `HYPERLIQUID_THRESHOLD_SOL` | `25000` | SOL liquidation threshold (USD) |

### Threshold Configuration

```python
# In shared/config/alert_thresholds.py
HYPERLIQUID_CONFIG = {
    "thresholds": {
        "BTC": {
            "single_large": 100000,   # $100K minimum
            "cascade_count": 5,       # 5+ liquidations
            "cascade_value": 500000   # $500K total
        },
        "ETH": {
            "single_large": 50000,
            "cascade_count": 5,
            "cascade_value": 250000
        },
        "default": {
            "single_large": 10000,
            "cascade_count": 3,
            "cascade_value": 50000
        }
    }
}
```

## Monitoring & Health Checks

### Health Check Endpoint

The monitoring coordinator tracks Hyperliquid health:

```python
from services.monitoring.coordinator import MonitoringCoordinator

coordinator = MonitoringCoordinator()

# Check Hyperliquid status
status = coordinator.get_service_status("hyperliquid_liquidation_monitor")
print(f"Healthy: {status['healthy']}")
print(f"Failures: {status['failures']}")
```

### Logging

Hyperliquid-specific logs are prefixed with 🟣:

```
[INFO] 🟣 Hyperliquid liquidation provider initialized
[INFO] 🟣 Subscribed to Hyperliquid BTC trades
[INFO] 🟣 Subscribed to Hyperliquid ETH trades
[INFO] 🟣 Subscribed to Hyperliquid SOL trades
```

## Performance Considerations

### Memory Usage

- **CompactLiquidation**: 18 bytes per record
- **1000 liquidation buffer**: ~18 KB
- **Per exchange overhead**: ~5 MB

### WebSocket Connection

- **Ping interval**: 20 seconds
- **Reconnect delays**: Exponential backoff (1, 2, 4, 8, 16 seconds)
- **Maximum reconnect delay**: 16 seconds
- **Rate limiting**: Implemented per Hyperliquid API guidelines

### Alert Rate Limiting

- **Alert cooldown**: 2 minutes between alerts for same symbol
- **Max alerts per hour**: 10 (configurable)
- **Deduplication window**: 5 minutes

## Troubleshooting

### Common Issues

#### 1. No Liquidations Detected

**Problem**: Monitor running but no alerts
**Solutions**:
- Check threshold settings (may be too high)
- Verify symbols are correct: `HYPERLIQUID_SYMBOLS=BTC,ETH,SOL`
- Check WebSocket connection: Look for connection logs
- Verify liquidation activity on Hyperliquid (check stats.hyperliquid.xyz)

#### 2. WebSocket Connection Errors

**Problem**: Frequent disconnections
**Solutions**:
- Check network connectivity
- Verify Hyperliquid API is accessible: `curl https://api.hyperliquid.xyz/info`
- Check firewall rules
- Review connection error logs

#### 3. High Memory Usage

**Problem**: Memory consumption increasing
**Solutions**:
- Reduce buffer size in `LiquidationBuffer`
- Limit monitored symbols
- Enable periodic buffer cleanup

#### 4. Missing Alerts

**Problem**: Liquidations not triggering alerts
**Solutions**:
- Check alert cooldown (2-minute minimum)
- Verify thresholds are appropriate
- Check Telegram bot token/chat ID
- Review `get_performance_status()` for alert effectiveness

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in environment
export MONITORING_LOG_LEVEL=DEBUG
```

### Manual Testing

Test Hyperliquid API connectivity:

```python
import asyncio
import aiohttp

async def test_hyperliquid():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "meta"}
        ) as response:
            data = await response.json()
            print(f"Available symbols: {[a['name'] for a in data['universe']]}")

asyncio.run(test_hyperliquid())
```

## API Reference

### HyperliquidLiquidationProvider

```python
class HyperliquidLiquidationProvider:
    def __init__(self, symbols: Optional[List[str]] = None)
    async def start_monitoring(self) -> AsyncIterator[CompactLiquidation]
    async def stop_monitoring(self) -> None
    def get_stats(self) -> dict
    async def get_available_symbols(self) -> List[str]
```

### MultiExchangeLiquidationMonitor

```python
class MultiExchangeLiquidationMonitor:
    def __init__(self, bot_instance, market_data_url: str,
                 enabled_exchanges: Optional[List[str]] = None)
    async def start_monitoring(self) -> None
    def stop_monitoring(self) -> None
    def get_status(self) -> dict
    def get_exchange_stats(self, exchange: str) -> Optional[dict]
```

## Architecture Decisions

### Why WebSocket Instead of Polling?

1. **Real-time updates**: Sub-second latency for liquidation events
2. **Reduced API load**: Single connection vs. repeated polling
3. **On-chain transparency**: Hyperliquid publishes all events to WebSocket
4. **Efficiency**: Lower bandwidth and computational overhead

### Why CompactLiquidation Format?

1. **Memory efficiency**: 18 bytes vs. 200+ bytes for dict
2. **High throughput**: Store 1000s of liquidations efficiently
3. **Fast processing**: Optimized for cascade detection algorithms
4. **Scalability**: Supports multiple exchanges without memory issues

### Why Multi-Exchange Architecture?

1. **Unified cascade detection**: Identify cascades across CEX and DEX
2. **Comprehensive monitoring**: Track institutional flows everywhere
3. **Redundancy**: Continue operation if one exchange fails
4. **Comparative analysis**: Cross-exchange liquidation patterns

## Roadmap

### Planned Enhancements

- [ ] Historical liquidation data archive
- [ ] Liquidation heatmap visualization
- [ ] Cross-exchange correlation analysis
- [ ] Machine learning cascade prediction
- [ ] Additional DEX integrations (dYdX, GMX, etc.)
- [ ] Liquidation replay for backtesting
- [ ] REST API for liquidation data queries

## Support & Resources

### Official Documentation

- **Hyperliquid API**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **WebSocket Subscriptions**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
- **Hyperliquid Explorer**: https://app.hyperliquid.xyz/explorer

### Third-Party Tools

- **CoinGlass**: https://www.coinglass.com/hyperliquid-liquidation-map
- **Coinalyze**: https://coinalyze.net/hyperliquid/liquidations/
- **Hyperliquid Stats**: https://stats.hyperliquid.xyz/

### Community

- **GitHub Issues**: Report bugs or request features
- **Telegram**: Join the community for discussions

## License

This implementation follows the project's existing license.

---

**Last Updated**: 2025-10-24
**Version**: 1.0.0
**Status**: Production Ready
