#!/usr/bin/env python3
"""
Fetch the latest HyperLiquid liquidation fills via the registry and optionally
verify that a synthetic trade is classified correctly.

Usage:
    python -m scripts.check_hyperliquid_registry
"""

import asyncio
import pprint

from dex.hyperliquid_liquidation_registry import HyperLiquidLiquidationRegistry


async def main() -> None:
    registry = HyperLiquidLiquidationRegistry(poll_interval=30.0)
    await registry.start()

    snapshot = registry.snapshot()
    print("Registry snapshot:")
    pprint.pprint(snapshot)

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
