# HyperLiquid Liquidation Detection - Current Plan  

Some questions remain unanswered (e.g., why they don't crash it), but here's the real-world approach:

### 1. Hard-coded wallet is NOT enough
- The single wallet (`0x2e3d…`), labeled “HLP Liquidator,” only holds capital; it doesn’t send every liquidation.
- Live trade feed (`type="trades"`) shows dozens of different addresses executing liquidations. Most are sub-accounts or delegated agents to `0x162c…` (the master clearinghouse account).
- "**Assumption:** HyperLiquid uses multiple agent addresses to execute the same logic, cycling addresses as needed."

### 2. How to detect **all** liquidation events now

The initial plan relied on discovering the rotating liquidation agents via
`extraAgents`. In practice, that endpoint now returns an empty list for the HLP
vault and most active sub-accounts. We pivoted to a more reliable signal that
is still publicly exposed: the vault's *fills*.

1. **Poll `userFills` for the HLP vault**:
   - `POST /info` with `{"type":"userFills","user":"0x2e3d..."}` returns the most
     recent liquidation fills executed by the vault, regardless of which agent
     submitted them.
   - Each fill includes a unique `tid`, `coin`, `dir` ("Close Long"/"Close Short"),
     and price/size information.

2. **Watch the trade stream**:
   - Subscribe to `{"method":"subscribe","subscription":{"type":"trades","coin":"<SYMBOL>"}}`.
   - When a trade arrives, match its `tid` against the cached vault fills. If the
     `tid` is present, classify it as a liquidation.
   - Classification:
     - `dir` contains `"Close Long"` → LONG liquidation (long forced to sell)
     - `dir` contains `"Close Short"` → SHORT liquidation (short forced to buy)

3. **Keep the cache fresh**:
   - Poll `userFills` every few seconds to keep a rolling window (500 entries by
     default).
   - If the response comes back empty or malformed, log an error and keep the
     previous cache so the monitor degrades gracefully instead of flapping.

4. **Backfill/validation**:
   - Periodically cross-check `userFills` against replayed websocket trades. If a
     fill never appears in the live stream, trigger an alert—the websocket may be
     lagging or filtered.

### 3. Failure cases to monitor
- **Agent rotation**: no longer a primary concern—the `userFills` approach is agent-agnostic.
- **API endpoint change**: if `userFills` stops returning data, fail fast with logging and mark HyperLiquid ingestion as `DEGRADED`.
- **Real-time speed bumps**: real-time stream gets behind. Cross-check by occasionally hitting `userFills` for the main agent and verifying the most recent fill timestamp is within ~60 seconds of current time.
- **Protocol changes**: If HyperLiquid moves liquidations to a dedicated channel or adds a flag; we should watch release notes or set up canary monitors to detect format changes (e.g., new fields in `trade` messages).

### 4. Implementation checklist (next steps)
1. Build a small utility to fetch, cache, and periodically refresh the `userFills`
   data. ✅ Implemented in `dex/hyperliquid_liquidation_registry.py`.
2. Update `monitor_liquidations_live.py` (and the professional monitor) to use the
   registry for detection. ✅ Live monitor and liquidation provider now share the registry.
3. Add metrics/logging to alert when no liquidations are seen for X minutes while
   `userFills` still reports new entries. ➡️ TODO (hook into monitoring once Grafana/alerts are scheduled).
4. Document this flow in the README and schedule a manual verification every few weeks. ✅ This doc now reflects the current implementation.

When the registry is running, the CLI displays real liquidation counts/values
again. If `userFills` stops updating or returns inconsistent data, the monitor
falls back to showing a warning so we can investigate before treating the feed
as authoritative.
