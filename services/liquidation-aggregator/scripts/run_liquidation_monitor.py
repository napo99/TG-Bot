#!/usr/bin/env python3
"""
Convenience entry point for the live HyperLiquid liquidation CLI monitor.

Usage:
    python -m scripts.run_liquidation_monitor
"""

import asyncio

from monitor_liquidations_live import main as monitor_main


def run() -> None:
    asyncio.run(monitor_main())


if __name__ == "__main__":
    run()
