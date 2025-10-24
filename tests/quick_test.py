#!/usr/bin/env python3
"""
Quick Test - Hyperliquid Liquidation Tracker

Simple 1-minute test to verify everything works.

Usage:
    python3 tests/quick_test.py
"""

import asyncio
import sys
import os

project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'services', 'market-data'))

from hyperliquid_blockchain_liquidation_tracker import (
    HyperliquidBlockchainLiquidationTracker
)


async def main():
    print("🚀 Quick Test - Hyperliquid Liquidation Tracker\n")

    # Initialize
    print("1. Initializing tracker...")
    tracker = HyperliquidBlockchainLiquidationTracker()
    print("   ✅ Tracker initialized\n")

    # Scan BTC
    print("2. Scanning BTC liquidations (this may take 5-10 seconds)...")
    try:
        liquidations = await tracker.scan_recent_liquidations(["BTC"])
        print(f"   ✅ Scan complete!\n")

        # Show results
        print(f"📊 Results:")
        print(f"   Found {len(liquidations)} BTC liquidations")

        if len(liquidations) > 0:
            print(f"\n   Most recent liquidations:")
            for i, liq in enumerate(liquidations[:3]):
                print(f"   {i+1}. {liq.liquidation_side} liquidation")
                print(f"      Value: ${liq.value_usd:,.0f}")
                print(f"      User: {liq.liquidated_user[:20]}...")
        else:
            print(f"   (No liquidations in recent BTC trades)")
            print(f"   (This is normal if market is quiet)")

        # Show stats
        print(f"\n📈 Statistics:")
        stats = tracker.get_statistics()
        print(f"   Total: {stats['total_liquidations']} liquidations")
        print(f"   Volume: ${stats['total_value_usd']:,.0f}")
        print(f"   Longs: {stats['long_liquidations']}")
        print(f"   Shorts: {stats['short_liquidations']}")

        print(f"\n✅ Test PASSED - Tracker is working!")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"\n❌ Test FAILED")
        return 1
    finally:
        await tracker.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
