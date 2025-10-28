#!/usr/bin/env python3
"""
Quick validation test for HyperLiquid liquidation detection.

This script performs a fast sanity check:
1. Tests API connectivity
2. Discovers active vaults
3. Fetches recent liquidations
4. Displays summary

Usage:
    python -m scripts.quick_validation
"""

import asyncio
import sys
import os

# Add parent directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SERVICE_DIR)

try:
    from dex.hyperliquid_liquidation_registry import HyperLiquidLiquidationRegistry
    import aiohttp
    import time
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please run: pip install aiohttp loguru")
    sys.exit(1)


async def quick_test():
    """Run a quick validation test."""
    print("=" * 70)
    print("HYPERLIQUID LIQUIDATION DETECTION - QUICK VALIDATION")
    print("=" * 70)

    # Test 1: API Connectivity
    print("\n[1/4] Testing API connectivity...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "meta"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    print("  ✅ HyperLiquid API is reachable")
                else:
                    print(f"  ⚠️  HyperLiquid API returned status {response.status}")
    except Exception as e:
        print(f"  ❌ API connectivity failed: {e}")
        return False

    # Test 2: Initialize Registry
    print("\n[2/4] Initializing liquidation registry...")
    try:
        registry = HyperLiquidLiquidationRegistry(poll_interval=5.0)
        await registry.start()
        print("  ✅ Registry initialized")
    except Exception as e:
        print(f"  ❌ Registry initialization failed: {e}")
        return False

    # Test 3: Discover Vaults
    print("\n[3/4] Discovering active liquidation vaults...")
    try:
        await registry.refresh(force=True)
        snapshot = registry.snapshot()

        vaults = snapshot.get("vaults", [])
        if not vaults:
            print("  ⚠️  No vaults discovered (may need to check implementation)")
        else:
            print(f"  ✅ Discovered {len(vaults)} vault(s)")

            for vault in vaults:
                address = vault.get("address", "unknown")
                cached_fills = vault.get("cached_fills", 0)
                last_fill_epoch = vault.get("last_fill_epoch", 0)
                last_error = vault.get("last_error")

                short_addr = f"{address[:8]}...{address[-6:]}" if len(address) > 14 else address

                if last_error:
                    print(f"    ⚠️  {short_addr}: ERROR - {last_error}")
                else:
                    age_seconds = time.time() - last_fill_epoch if last_fill_epoch else 0
                    print(f"    • {short_addr}: {cached_fills} fills (last: {age_seconds:.0f}s ago)")

        if snapshot.get("all_vaults_stale"):
            print("  ⚠️  Warning: All vaults are stale (>5 min without fills)")
            print("     This may indicate:")
            print("       - Low liquidation activity period")
            print("       - HyperLiquid API issues")
            print("       - Vault rotation in progress")

    except Exception as e:
        print(f"  ❌ Vault discovery failed: {e}")
        await registry.close()
        return False

    # Test 4: Check Recent Liquidations
    print("\n[4/4] Checking recent liquidations...")
    try:
        fills = registry.recent_fills(limit=10)

        if not fills:
            print("  ℹ️  No liquidations in cache yet")
            print("     This is normal if:")
            print("       - Just started monitoring")
            print("       - Low market volatility")
            print("       - Quiet trading period")
        else:
            print(f"  ✅ Found {len(fills)} recent liquidation(s)")
            print("\n  Latest liquidations:")

            for i, fill in enumerate(fills[:5], 1):
                side = fill.liquidation_side or "?"
                age = (time.time() - (fill.timestamp_ms / 1000))
                print(
                    f"    {i}. {fill.coin} {side} liquidation: "
                    f"{fill.size:.4f} @ ${fill.price:.2f} "
                    f"(${fill.value:,.2f}) - {age:.0f}s ago"
                )

    except Exception as e:
        print(f"  ⚠️  Error checking liquidations: {e}")

    # Cleanup
    await registry.close()

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if vaults and not snapshot.get("all_vaults_stale"):
        print("✅ PASS: System is operational")
        print("\nNext steps:")
        print("  1. Run extended validation:")
        print("     python -m scripts.validate_liquidation_accuracy --duration 10")
        print("  2. Start live monitoring:")
        print("     python monitor_liquidations_live.py")
        print("  3. Compare with CoinGlass (requires API key):")
        print("     python -m scripts.validate_liquidation_accuracy --coinglass-api-key YOUR_KEY")
    elif vaults:
        print("⚠️  PARTIAL: Vaults discovered but stale")
        print("\nRecommendations:")
        print("  - Check during high volatility periods")
        print("  - Verify HyperLiquid API status")
        print("  - Run extended monitoring to capture activity")
    else:
        print("❌ FAIL: No vaults discovered")
        print("\nTroubleshooting:")
        print("  - Check internet connectivity")
        print("  - Verify HyperLiquid API is accessible")
        print("  - Review implementation in dex/hyperliquid_liquidation_registry.py")

    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
