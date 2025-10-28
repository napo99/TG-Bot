# Crypto Trading Assistant

A modular crypto trading assistant that integrates with Telegram for portfolio tracking, market analysis, and trade management.

## Architecture

- **telegram-bot**: Python service handling Telegram commands and user interaction
- **market-data**: Python service for fetching market data using ccxt
- **Database**: SQLite for Phase 1, PostgreSQL for production

## Phase 1 Features

- `/price <symbol>` - Get current price
- `/balance` - Show account balance
- `/positions` - Show open positions
- `/pnl` - Show P&L summary

## Setup

1. Copy `.env.example` to `.env` and configure:
   - `TELEGRAM_BOT_TOKEN`
   - Exchange API keys

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Development

Each service is independently deployable and testable.


## HyperLiquid Liquidation Monitoring

The liquidation aggregator now auto-discovers HyperLiquid liquidation vaults and
keeps dashboards alive when the protocol rotates addresses. Operator entry
points:

```bash
# Inspect registry health and per-vault status
cd services/liquidation-aggregator
python -m scripts.check_hyperliquid_registry

# Run the lightweight live dashboard (requires Redis at redis://localhost:6380/0)
python monitor_liquidations_live.py

# Launch the professional multi-exchange view
python professional_liquidation_monitor.py --exchanges hyperliquid binance --symbols BTCUSDT ETHUSDT

# Execute automated coverage for the registry
pytest services/liquidation-aggregator/tests/test_hyperliquid_liquidation_registry.py
```

See `docs/hyperliquid_liquidation_detection.md` for the full discovery workflow
and operational notes.
