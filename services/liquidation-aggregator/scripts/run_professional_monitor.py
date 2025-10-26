#!/usr/bin/env python3
"""
Wrapper that forwards CLI arguments to the professional cascade monitor.

Usage:
    python -m scripts.run_professional_monitor --symbols BTCUSDT ETHUSDT
"""

import asyncio

from professional_liquidation_monitor import main as professional_main


def run() -> None:
    asyncio.run(professional_main())


if __name__ == "__main__":
    run()
