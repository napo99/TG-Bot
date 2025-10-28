# HyperLiquid Liquidation Detection – Dynamic Vault Discovery

HyperLiquid recently rotated away from the long-lived `0x2e3d…` liquidation
vault. The old logic—polling that single account via `userFills`—quietly stopped
seeing new trade ids, and every downstream monitor reported zero activity. The
new pipeline discovers the active vault set automatically and keeps the
registry healthy even when HyperLiquid rotates addresses mid-session.

## 1. Vault discovery

1. **Discover candidates via `/info`**  
   Every refresh first queries `POST /info` with `{"type":"vaults"}` and then
   `{"type":"meta"}` as a fallback. The payloads contain one or more liquidation
   vault addresses depending on the day. We walk the nested structures and
   normalize any `0x…` strings into a deduplicated list.

2. **Fallback behaviour**  
   If the public metadata endpoints fail or return nothing, we keep using the
   last known vault list. When no prior list exists we fall back to the historic
   HLP address (`0x2e3d…`) so the registry never fails completely.

3. **Rotation support**  
   Discovery runs at least once per minute (`DISCOVERY_INTERVAL`). When the API
   advertises a new set, the registry starts polling those vaults immediately
   and evicts caches for the ones that vanished. Consumers do not need to restart
   to pick up the rotation.
4. **Websocket-driven discovery**  
   When the public metadata does not expose fresh vaults, the registry now probes
   websocket participants on-demand. If a trade arrives with an unknown `tid`,
   the participating addresses are treated as candidates: the registry fetches
   their `userFills` once (with cooldowns) and, if liquidation records are found,
   promotes the address to the active vault set. This keeps dashboards live even
   when HyperLiquid rotates vaults without updating the metadata endpoint.

## 2. Multi-vault polling & cache merge

* Each active vault is polled concurrently via `userFills`. The registry keeps a
  per-vault cache (`VaultCache`) with metadata such as the last successful
  refresh, last error, and latest fill timestamp.
* Responses are filtered down to liquidation-only fills (direction string must
  include “Close Long” / “Close Short”).
* Successful results are merged into a single `tid → fill` lookup table.
* Empty responses keep the previous cache in place—HyperLiquid occasionally
  returns an empty array during quiet periods and we do not want to thrash the
  downstream monitors.

## 3. Telemetry & stale detection

`HyperLiquidLiquidationRegistry.snapshot()` now returns:

```json
{
  "cached_fills": 200,
  "active_vaults": ["0xb83d…", "0xc6ac…"],
  "vaults": [
    {"address": "0xb83d…", "cached_fills": 120, "last_fill_epoch": 1716482134.2},
    {"address": "0xc6ac…", "cached_fills": 80,  "last_error": null}
  ],
  "all_vaults_stale": false
}
```

If every tracked vault has gone more than five minutes without a new fill the
registry raises `all_vaults_stale = True` and emits a log warning. The live
terminal monitor displays the warning inline so operators know when HyperLiquid
is rotating or degraded.

## 4. Consumer updates

* **`monitor_liquidations_live.py`** now prints per-vault health, including how
  long ago each vault produced a fill and whether any request failed.
* **`professional_liquidation_monitor.py`** consumes the refreshed stream via the
  shared registry embedded in the HyperLiquid provider; telemetry is exposed via
  the Global Pulse / Flow panes.
* **`scripts/check_hyperliquid_registry.py`** prints a human-readable per-vault
  status block, making smoke checks easy when rotating vaults are suspected.

## 5. Verification checklist

* Run the smoke script to inspect cache state:

  ```bash
  cd services/liquidation-aggregator
  python -m scripts.check_hyperliquid_registry
  ```

* (Optional) Verify on-demand discovery by replaying a recent trade:

  ```python
  python - <<'PY'
  import asyncio, aiohttp
  from dex.hyperliquid_liquidation_registry import HyperLiquidLiquidationRegistry

  async def main():
      address = "0xc6ac58a7a63339898aeda32499a8238a46d88e84"
      async with aiohttp.ClientSession() as session:
          async with session.post('https://api.hyperliquid.xyz/info', json={'type': 'userFills', 'user': address}) as resp:
              fill = next(f for f in await resp.json() if 'Close' in f.get('dir', ''))
      registry = HyperLiquidLiquidationRegistry()
      await registry.start()
      await registry.classify_trade({**fill, 'users': [address]})
      print(registry.active_vaults())
      await registry.close()

  asyncio.run(main())
  PY
  ```

  The registry promotes the address to the active vault set on the first match.

* Launch the lightweight live monitor and observe non-zero liquidation counts
  during active hours:

  ```bash
  python monitor_liquidations_live.py
  ```

* Run the multi-exchange dashboard (Redis at `redis://localhost:6380/0`):

  ```bash
  python professional_liquidation_monitor.py --exchanges hyperliquid binance --symbols BTCUSDT ETHUSDT
  ```

* Automated coverage: `poetry run pytest services/liquidation-aggregator/tests/test_hyperliquid_liquidation_registry.py`

With the dynamic registry in place, HyperLiquid rotations no longer cause the
dashboards to flatline. The telemetry surfaces stale feeds quickly so operators
can escalate if HyperLiquid experiences broader issues.
