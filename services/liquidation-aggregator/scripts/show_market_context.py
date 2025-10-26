#!/usr/bin/env python3
"""
CLI helper to pull a consolidated market context snapshot (open interest,
funding, depth) using the MarketDataAggregator module.

Usage examples:
    python -m scripts.show_market_context --symbol BTCUSDT --once
    python -m scripts.show_market_context --symbol ETHUSDT --refresh 15
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import time
from typing import Any, Dict

from market_data_aggregator import MarketDataAggregator, MarketContext


def _format_context(context: MarketContext) -> Dict[str, Any]:
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(context.timestamp)),
        "funding_rate": context.funding_rate,
        "funding_trend": context.funding_trend,
        "funding_max_24h": context.max_funding_24h,
        "open_interest_usd": context.open_interest_usd,
        "oi_change_1m": context.oi_change_1m,
        "oi_change_5m": context.oi_change_5m,
        "oi_change_1h": context.oi_change_1h,
        "book_imbalance": context.book_imbalance,
        "bid_depth_2pct": context.bid_depth_2pct,
        "ask_depth_2pct": context.ask_depth_2pct,
        "spot_price": context.spot_price,
        "perp_price": context.perp_price,
        "premium": context.premium,
        "realized_vol_5m": context.realized_vol_5m,
        "large_trades_1m": context.large_trades_1m,
        "whale_accumulation": context.whale_accumulation,
    }


async def _snapshot(symbol: str) -> MarketContext:
    aggregator = MarketDataAggregator()
    return await aggregator.get_complete_context(symbol=symbol)


async def _loop(symbol: str, refresh: float) -> None:
    while True:
        context = await _snapshot(symbol)
        stats = _format_context(context)
        print(f"\n=== Market Context ({symbol}) ===")
        for key, value in stats.items():
            print(f"{key:>18}: {value}")
        await asyncio.sleep(refresh)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Market context (open-interest / funding / depth) snapshot CLI")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol to query (default BTCUSDT)")
    parser.add_argument("--refresh", type=float, default=0.0, help="If >0, stream updates every N seconds")
    parser.add_argument("--once", action="store_true", help="Fetch a single snapshot and exit")
    args = parser.parse_args()

    if args.once or args.refresh <= 0:
        context = await _snapshot(args.symbol)
        stats = _format_context(context)
        print(f"=== Market Context ({args.symbol}) ===")
        for key, value in stats.items():
            print(f"{key:>18}: {value}")
    else:
        await _loop(args.symbol, args.refresh)


if __name__ == "__main__":
    asyncio.run(main())
