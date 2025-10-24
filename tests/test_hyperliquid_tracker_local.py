#!/usr/bin/env python3
"""
Local Testing Script for Hyperliquid Blockchain Liquidation Tracker

Run this to validate the implementation works with live Hyperliquid API data.

Usage:
    python3 tests/test_hyperliquid_tracker_local.py

What it tests:
    1. API connectivity to Hyperliquid
    2. Trade data retrieval
    3. Liquidation detection logic
    4. Data parsing and aggregation
    5. Statistics calculation
"""

import asyncio
import sys
import os

# Add paths
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'services', 'market-data'))

from hyperliquid_blockchain_liquidation_tracker import (
    HyperliquidBlockchainLiquidationTracker,
    BlockchainLiquidation,
    HLP_LIQUIDATOR_ADDRESS
)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


async def test_api_connectivity(tracker):
    """Test 1: API connectivity"""
    print_header("TEST 1: API Connectivity")

    try:
        # Try to query recent trades for BTC
        trades = await tracker.query_recent_trades("BTC")

        if trades and len(trades) > 0:
            print_success(f"Connected to Hyperliquid API")
            print_info(f"Retrieved {len(trades)} recent BTC trades")
            return True
        else:
            print_error("Connected but no trades returned")
            return False

    except Exception as e:
        print_error(f"API connection failed: {e}")
        return False


async def test_liquidation_detection(tracker):
    """Test 2: Liquidation detection logic"""
    print_header("TEST 2: Liquidation Detection Logic")

    # Test with mock data
    print_info("Testing with mock liquidation trade...")

    mock_trade = {
        "coin": "BTC",
        "side": "B",  # HLP Liquidator buying
        "px": "45000",
        "sz": "1.5",
        "time": 1702000000000,
        "hash": "0xtest123",
        "tid": 12345,
        "users": [
            HLP_LIQUIDATOR_ADDRESS,  # Buyer (liquidator)
            "0x1234567890abcdef1234567890abcdef12345678"  # Seller (liquidated user)
        ]
    }

    is_liq, liquidated_user = tracker.is_liquidation_trade(mock_trade)

    if is_liq:
        print_success("Liquidation detection works!")
        print_info(f"Detected liquidated user: {liquidated_user[:20]}...")

        # Test parsing
        liquidation = tracker.parse_liquidation(mock_trade)
        print_info(f"Parsed liquidation side: {liquidation.liquidation_side}")
        print_info(f"Value: ${liquidation.value_usd:,.0f}")

        if liquidation.liquidation_side == "SHORT":
            print_success("Side detection correct (HLP buying = SHORT liquidation)")
        else:
            print_error("Side detection incorrect")
            return False

        return True
    else:
        print_error("Failed to detect liquidation in mock trade")
        return False


async def test_live_liquidation_scan(tracker):
    """Test 3: Scan for real liquidations"""
    print_header("TEST 3: Live Liquidation Scan")

    print_info("Scanning BTC recent trades for liquidations...")

    try:
        liquidations = await tracker.scan_recent_liquidations(["BTC"])

        print_success(f"Scan completed!")
        print_info(f"Found {len(liquidations)} BTC liquidations")

        if len(liquidations) > 0:
            print_info("\nMost recent liquidations:")
            for i, liq in enumerate(liquidations[:5]):
                print(f"  {i+1}. {liq.coin} {liq.liquidation_side}")
                print(f"     Value: ${liq.value_usd:,.0f}")
                print(f"     User: {liq.liquidated_user[:20]}...")
                print(f"     Tx: {liq.tx_hash[:20]}...")
        else:
            print_info("No liquidations found in recent trades")
            print_info("(This is normal if market is quiet)")

        return True

    except Exception as e:
        print_error(f"Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_statistics_aggregation(tracker):
    """Test 4: Statistics aggregation"""
    print_header("TEST 4: Statistics Aggregation")

    stats = tracker.get_statistics()

    print_success("Statistics retrieved!")
    print("\n📊 Overall Statistics:")
    print(f"  Total liquidations: {stats['total_liquidations']}")
    print(f"  Total value: ${stats['total_value_usd']:,.0f}")
    print(f"  Average size: ${stats['average_liquidation_size_usd']:,.0f}")

    print("\n📈 By Side:")
    print(f"  Long liquidations: {stats['long_liquidations']} (${stats['long_liquidations_usd']:,.0f})")
    print(f"  Short liquidations: {stats['short_liquidations']} (${stats['short_liquidations_usd']:,.0f})")

    if stats['long_short_ratio'] != 0:
        print(f"  Long/Short ratio: {stats['long_short_ratio']:.2f}")

    print("\n💰 By Coin:")
    for coin, count in stats['liquidations_by_coin'].items():
        print(f"  {coin}: {count} liquidations")

        if coin in stats['liquidations_by_coin_side']:
            sides = stats['liquidations_by_coin_side'][coin]
            print(f"    → {sides['LONG']} longs, {sides['SHORT']} shorts")

    print("\n👥 Users:")
    print(f"  Unique users liquidated: {stats['unique_users_liquidated']}")

    if stats['top_liquidated_users']:
        print("\n  Top liquidated users:")
        for i, user in enumerate(stats['top_liquidated_users'][:3]):
            print(f"    {i+1}. {user['address'][:20]}...")
            print(f"       {user['count']} liquidations, ${user['total_usd']:,.0f}")
            print(f"       {user['long_count']} longs, {user['short_count']} shorts")

    return True


async def test_timeframe_aggregation(tracker):
    """Test 5: Time-based aggregation"""
    print_header("TEST 5: Timeframe Aggregation")

    if tracker.total_liquidations == 0:
        print_info("No liquidations to test timeframe aggregation")
        return True

    # Test different timeframes
    timeframes = [
        (300, "Last 5 minutes"),
        (3600, "Last hour"),
        (86400, "Last 24 hours")
    ]

    for seconds, label in timeframes:
        stats = tracker.get_liquidations_by_timeframe(seconds)
        print(f"\n📅 {label}:")
        print(f"  Count: {stats['count']}")
        print(f"  Total USD: ${stats['total_usd']:,.0f}")

        if stats['count'] > 0:
            print(f"  Long: {stats['long_count']}, Short: {stats['short_count']}")
            print(f"  Average size: ${stats['average_size']:,.0f}")

    print_success("Timeframe aggregation works!")
    return True


async def test_multi_coin_scan(tracker):
    """Test 6: Multi-coin scanning"""
    print_header("TEST 6: Multi-Coin Scanning")

    print_info("Scanning BTC, ETH, SOL for liquidations...")

    try:
        liquidations = await tracker.scan_recent_liquidations(["BTC", "ETH", "SOL"])

        print_success(f"Multi-coin scan completed!")
        print_info(f"Total liquidations found: {len(liquidations)}")

        # Breakdown by coin
        by_coin = {}
        for liq in liquidations:
            by_coin[liq.coin] = by_coin.get(liq.coin, 0) + 1

        print("\n📊 Breakdown by coin:")
        for coin, count in by_coin.items():
            print(f"  {coin}: {count} liquidations")

        return True

    except Exception as e:
        print_error(f"Multi-coin scan failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 "*30)
    print("  HYPERLIQUID BLOCKCHAIN TRACKER - LOCAL TESTING")
    print("🧪 "*30)

    print_info(f"HLP Liquidator Address: {HLP_LIQUIDATOR_ADDRESS}")
    print_info("Testing against Hyperliquid MAINNET API")

    # Initialize tracker
    tracker = HyperliquidBlockchainLiquidationTracker()

    results = {
        "API Connectivity": False,
        "Liquidation Detection": False,
        "Live Scan": False,
        "Statistics": False,
        "Timeframes": False,
        "Multi-Coin": False
    }

    try:
        # Run tests
        results["API Connectivity"] = await test_api_connectivity(tracker)
        results["Liquidation Detection"] = await test_liquidation_detection(tracker)
        results["Live Scan"] = await test_live_liquidation_scan(tracker)
        results["Statistics"] = await test_statistics_aggregation(tracker)
        results["Timeframes"] = await test_timeframe_aggregation(tracker)
        results["Multi-Coin"] = await test_multi_coin_scan(tracker)

    finally:
        await tracker.close()

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print("\n" + "="*60)
    print(f"  PASSED: {passed}/{total} tests")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! Implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
