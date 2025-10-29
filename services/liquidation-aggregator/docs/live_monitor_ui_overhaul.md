# Live Monitor UI Overhaul - October 2025

## Highlights
- Rebuilt `monitor_liquidations_live.py` around Rich layouts for a stable dashboard:
  - Left column: `Live Market Activity` above the `Registry / Vault` block.
  - Right column: new `Liquidation Summary` cards (15m + 1h windows) and an expanded `Recent Alerts` tape.
- Added command-line flags for coin selection, watchlists, refresh cadence, and registry polling.
- Introduced structured logging (console vs. rotating file) so the terminal stays noise-free while diagnostics persist on disk.

## Usage Notes
- Run with majors only: `python monitor_liquidations_live.py --majors-only`.
- Cap subscriptions: `--max-coins 20` keeps feed lightweight.
- Reduce registry load: `--registry-poll 6` backs the REST cadence off to six seconds.
- Adjust UI cadence: `--refresh-interval 1.0` for a 1 Hz redraw.

## Follow-Up Items
- [ ] Mirror the same Rich-pane quiet logging pattern inside `professional_liquidation_monitor.py`.
- [ ] Surface a 5m liquidation card when spike detection is enabled.
- [ ] Add per-exchange breakdowns (Binance / Bybit / HyperLiquid) for desks that run multi-feed setups.
- [ ] Gate the alert deque length via CLI so power users can widen the tape without editing code.
