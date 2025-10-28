# Operational Scripts

All operator-facing entry points for the liquidation aggregator now live under `services/liquidation-aggregator/scripts`. Each helper forwards into the production modules so you can run the same code paths with a single command.

## Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`
- Redis running on `localhost:6380` when using the professional monitor (configurable with `--redis-url`)

## Quick Start

```bash
# 1. Quick system validation (2 minutes)
python -m scripts.quick_validation

# 2. Live monitoring
python -m scripts.run_liquidation_monitor

# 3. Extended validation with CoinGlass comparison (optional)
python -m scripts.validate_liquidation_accuracy --duration 10 --coinglass-api-key YOUR_KEY
```

## Validation & Testing

### Quick Validation (2 minutes)
```bash
python -m scripts.quick_validation
```
Fast sanity check that validates:
- API connectivity
- Vault discovery
- Recent liquidations
- Registry health

### Extended Validation (5-30 minutes)
```bash
# Basic validation
python -m scripts.validate_liquidation_accuracy --duration 10

# With CoinGlass comparison (requires API key)
python -m scripts.validate_liquidation_accuracy --duration 10 --coinglass-api-key YOUR_KEY

# Export detailed report
python -m scripts.validate_liquidation_accuracy --duration 10 --export report.json
```
Comprehensive validation including:
- Vault discovery accuracy
- Real-time liquidation tracking
- CoinGlass comparison (optional)
- Statistical analysis

**See `docs/VALIDATION_GUIDE.md` for complete validation documentation.**

## Liquidation Monitoring

### HyperLiquid Live CLI
```
python -m scripts.run_liquidation_monitor
```
Shows live HyperLiquid trades, liquidation tallies, and registry health. Leave the screen open during volatile sessions; if the registry cache remains at 0 fills, no liquidations are being published yet.

### Full Multi-Exchange Monitor
```
python -m scripts.run_professional_monitor --symbols BTCUSDT ETHUSDT --exchanges binance hyperliquid
```
Wraps `professional_liquidation_monitor.py` with the same CLI flags. Add exchanges or change the Redis URL as needed.
The compact Rich dashboard is now the default; pass `--full-dashboard` if you prefer
the legacy full-screen layout.

## HyperLiquid Diagnostics
```
python -m scripts.check_hyperliquid_registry
```
Refreshes the registry, prints the latest `userFills`, and validates that the newest fill is classified as a liquidation when matched against a websocket trade payload.

## Market Context / Open Interest Snapshot
```
# One-shot snapshot
python -m scripts.show_market_context --symbol BTCUSDT --once

# Continuous updates every 15 seconds
python -m scripts.show_market_context --symbol ETHUSDT --refresh 15
```
Pulls funding, open interest deltas, order-book depth, and volatility via `MarketDataAggregator` so you can correlate liquidation surges with broader market posture.

## Where to Go Next
- Need automated alerting once Grafana/Prometheus land? Hook into the registry snapshot (exposed via `HyperLiquidLiquidationRegistry.snapshot()`).
- Want to script deployments? Combine these entry points inside CI/CD or tmux sessions—each script stays import-safe.
