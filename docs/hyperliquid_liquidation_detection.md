# HyperLiquid Liquidation Monitoring Overview

The HyperLiquid liquidation registry now discovers active vaults dynamically and
keeps downstream dashboards alive through HyperLiquid’s frequent vault rotations.

Key behaviours:

* `dex/hyperliquid_liquidation_registry.py` queries `POST /info` with
  `{"type":"vaults"}` (falling back to `{"type":"meta"}`) to learn the active
  liquidation vault set. Each vault is polled concurrently via `userFills` and
  the results are merged into a single cache of liquidation trade ids.
* Telemetry exposes per-vault health in `snapshot()`, including the last fill
  timestamp and whether every vault feed has gone stale for more than five
  minutes. The live dashboard prints this information inline so operators can
  react quickly when HyperLiquid rotates addresses or experiences downtime.
* Updated tooling:
  - `services/liquidation-aggregator/monitor_liquidations_live.py` shows per-vault
    diagnostics and warns when the cache goes stale.
  - `services/liquidation-aggregator/scripts/check_hyperliquid_registry.py`
    provides a quick smoke check with human-readable vault statuses.
  - Unit tests under `services/liquidation-aggregator/tests/` cover vault
    discovery, rotation handling, and stale detection.

For the deep dive—including verification commands—see
`services/liquidation-aggregator/docs/hyperliquid_liquidation_detection.md`.
