#!/usr/bin/env python3
"""
Fetch the latest HyperLiquid liquidation fills via the registry and optionally
verify that a synthetic trade is classified correctly.

Usage:
    python -m scripts.check_hyperliquid_registry
"""

import asyncio
import pprint
import time

from dex.hyperliquid_liquidation_registry import HyperLiquidLiquidationRegistry


async def main() -> None:
    registry = HyperLiquidLiquidationRegistry(poll_interval=30.0)
    await registry.start()

    snapshot = registry.snapshot()
    print("Registry snapshot:")
    pprint.pprint(snapshot)

    if snapshot.get("vaults"):
        print("\nPer-vault status:")
        for vault in snapshot["vaults"]:
            address = vault.get("address", "")
            cached = vault.get("cached_fills", 0)
            last_success = vault.get("last_success")
            last_fill = vault.get("last_fill_epoch")
            last_error = vault.get("last_error")

            if last_fill:
                age = max(0, time.time() - last_fill)
                age_str = f"last fill {age:.0f}s ago"
            else:
                age_str = "no fills yet"

            if last_error:
                status = f"ERROR: {last_error}"
            elif last_success:
                status = age_str
            else:
                status = "initializing"

            short_addr = f"{address[:6]}…{address[-4:]}" if len(address) > 10 else address
            print(f"  - {short_addr}: {cached} fills ({status})")

    if snapshot.get("all_vaults_stale"):
        print("\n⚠️  Warning: all tracked vaults are stale. HyperLiquid might be rotating vaults or experiencing downtime.")

    fills = registry.recent_fills(limit=5)
    if not fills:
        print("No fills cached yet. Keep the registry running during active hours.")
    else:
        print("\nLatest fills:")
        for fill in fills:
            print(
                f"tid={fill.tid} coin={fill.coin} side={fill.liquidation_side} "
                f"price={fill.price:.6f} size={fill.size:.4f} value=${fill.value:,.2f}"
            )

        sample = fills[0]
        trade = {
            "coin": sample.coin,
            "px": str(sample.price),
            "sz": str(sample.size),
            "time": sample.timestamp_ms,
            "tid": sample.tid,
            "users": ["0xdead", "0xbeef"],
        }
        classified = await registry.classify_trade(trade)
        print("\nClassification result for latest fill:")
        pprint.pprint(classified)

    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
