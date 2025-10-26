#!/usr/bin/env python3
"""
CLI wrapper for the cascade backtesting framework.
Usage example:

    python backtest.py --source csv --start 2024-10-01 --end 2024-10-31 \
        --symbols BTCUSDT,ETHUSDT --export results/october_report.json
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from cascade_backtest_framework import run_comprehensive_backtest


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid ISO date '{value}'") from exc


def _parse_symbols(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    symbols = [item.strip().upper() for item in value.split(",") if item.strip()]
    return symbols or None


async def _async_main(args: argparse.Namespace) -> None:
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    symbols = _parse_symbols(args.symbols)

    export_path = Path(args.export or "backtest_results.json")
    export_path.parent.mkdir(parents=True, exist_ok=True)

    print("🚀 Cascade Backtesting CLI")
    print("──────────────────────────")
    print(f"Source:  {args.source}")
    if start and end:
        print(f"Window: {start.isoformat()} → {end.isoformat()}")
    if symbols:
        print(f"Symbols: {', '.join(symbols)}")
    print(f"Output:  {export_path}")

    try:
        await run_comprehensive_backtest(
            source=args.source,
            start_date=start,
            end_date=end,
            symbols=symbols,
            export_path=str(export_path),
        )
    except Exception as exc:  # noqa: BLE001 - present exception to operator
        print(f"\n❌ Backtest failed: {exc}")
        raise SystemExit(1) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Run liquidation cascade backtests.")
    parser.add_argument(
        "--source",
        choices=("timescale", "csv", "mock"),
        default="timescale",
        help="Data source priority (default: timescale, falls back to mock).",
    )
    parser.add_argument(
        "--start",
        metavar="ISO_DATE",
        help="Inclusive start date (YYYY-MM-DD or ISO format).",
    )
    parser.add_argument(
        "--end",
        metavar="ISO_DATE",
        help="Inclusive end date (YYYY-MM-DD or ISO format).",
    )
    parser.add_argument(
        "--symbols",
        metavar="CSV",
        help="Comma separated symbols filter (e.g. BTCUSDT,ETHUSDT).",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Where to write the JSON report (default: backtest_results.json).",
    )

    args = parser.parse_args()
    asyncio.run(_async_main(args))


if __name__ == "__main__":
    main()
