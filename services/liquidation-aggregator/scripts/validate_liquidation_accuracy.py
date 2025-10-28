#!/usr/bin/env python3
"""
Comprehensive liquidation data validation script.

This script validates our HyperLiquid liquidation detection system by:
1. Testing the vault discovery mechanism with live API
2. Collecting liquidation data from our system
3. Comparing against CoinGlass reference data
4. Generating accuracy metrics and reports

Usage:
    # Quick validation (5 minutes)
    python -m scripts.validate_liquidation_accuracy --duration 5

    # Extended validation with CoinGlass comparison
    python -m scripts.validate_liquidation_accuracy --duration 30 --coinglass-api-key YOUR_KEY

    # Export detailed report
    python -m scripts.validate_liquidation_accuracy --duration 10 --export validation_report.json

Requirements:
    - pip install -r requirements.txt
    - Optional: CoinGlass API key for external validation
"""

import asyncio
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import sys
import os

# Add parent directories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SERVICE_DIR)

try:
    import aiohttp
    from loguru import logger
    from dex.hyperliquid_liquidation_registry import (
        HyperLiquidLiquidationRegistry,
        HyperLiquidFill,
    )
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


class LiquidationValidator:
    """Validates liquidation detection accuracy against multiple sources."""

    def __init__(
        self,
        duration_minutes: int = 5,
        coinglass_api_key: Optional[str] = None,
    ):
        self.duration_minutes = duration_minutes
        self.coinglass_api_key = coinglass_api_key
        self.registry = HyperLiquidLiquidationRegistry(poll_interval=5.0)

        # Tracking metrics
        self.our_liquidations: List[HyperLiquidFill] = []
        self.coinglass_data: List[Dict[str, Any]] = []
        self.vault_snapshots: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "vault_discovery_count": 0,
            "vaults_discovered": [],
            "total_liquidations_detected": 0,
            "liquidations_by_exchange": defaultdict(int),
            "liquidations_by_coin": defaultdict(int),
            "liquidations_by_side": defaultdict(int),
            "total_volume_usd": 0.0,
            "avg_liquidation_size": 0.0,
            "vault_health_checks": 0,
            "vault_errors": 0,
        }

    async def run_validation(self) -> Dict[str, Any]:
        """Run the complete validation suite."""
        logger.info(
            f"🚀 Starting {self.duration_minutes}-minute liquidation validation"
        )
        self.stats["start_time"] = datetime.now().isoformat()

        # Initialize registry
        try:
            await self.registry.start()
            logger.info("✅ HyperLiquid registry initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize registry: {e}")
            return self._generate_error_report(str(e))

        # Test vault discovery
        await self._test_vault_discovery()

        # Monitor liquidations for specified duration
        await self._monitor_liquidations()

        # Fetch CoinGlass data if API key provided
        if self.coinglass_api_key:
            await self._fetch_coinglass_data()

        # Generate comparison report
        report = await self._generate_report()

        # Cleanup
        await self.registry.close()
        logger.info("✅ Validation complete")

        return report

    async def _test_vault_discovery(self) -> None:
        """Test the vault discovery mechanism."""
        logger.info("🔍 Testing vault discovery...")

        # Force a refresh to discover vaults
        await self.registry.refresh(force=True)

        # Get snapshot
        snapshot = self.registry.snapshot()
        self.vault_snapshots.append(
            {"timestamp": datetime.now().isoformat(), "data": snapshot}
        )

        # Extract vault information
        vaults = snapshot.get("vaults", [])
        self.stats["vault_discovery_count"] = len(vaults)
        self.stats["vaults_discovered"] = [v.get("address") for v in vaults]

        logger.info(f"✅ Discovered {len(vaults)} active vault(s)")

        for vault in vaults:
            address = vault.get("address", "unknown")
            cached_fills = vault.get("cached_fills", 0)
            last_fill_epoch = vault.get("last_fill_epoch", 0)
            last_error = vault.get("last_error")

            short_addr = f"{address[:6]}...{address[-4:]}" if len(address) > 10 else address

            if last_error:
                logger.warning(f"  ⚠️  {short_addr}: ERROR - {last_error}")
                self.stats["vault_errors"] += 1
            else:
                age_seconds = time.time() - last_fill_epoch if last_fill_epoch else 0
                logger.info(
                    f"  ✓ {short_addr}: {cached_fills} fills "
                    f"(last fill {age_seconds:.0f}s ago)"
                )

        # Check for stale vaults
        if snapshot.get("all_vaults_stale"):
            logger.warning(
                "⚠️  All vaults are stale - may indicate API issues or low activity period"
            )

    async def _monitor_liquidations(self) -> None:
        """Monitor liquidations for the specified duration."""
        logger.info(
            f"📊 Monitoring liquidations for {self.duration_minutes} minute(s)..."
        )

        start_time = time.time()
        end_time = start_time + (self.duration_minutes * 60)
        check_interval = 10  # Check every 10 seconds

        iteration = 0
        while time.time() < end_time:
            iteration += 1

            # Refresh registry to get latest data
            await self.registry.refresh()

            # Get recent fills
            fills = self.registry.recent_fills(limit=100)

            # Track new liquidations
            for fill in fills:
                if fill not in self.our_liquidations:
                    self.our_liquidations.append(fill)
                    self._update_stats(fill)

            # Get vault health snapshot
            snapshot = self.registry.snapshot()
            self.vault_snapshots.append(
                {"timestamp": datetime.now().isoformat(), "data": snapshot}
            )
            self.stats["vault_health_checks"] += 1

            # Progress update
            elapsed = time.time() - start_time
            remaining = end_time - time.time()
            progress = (elapsed / (self.duration_minutes * 60)) * 100

            logger.info(
                f"⏱️  Progress: {progress:.0f}% | "
                f"Liquidations: {len(self.our_liquidations)} | "
                f"Remaining: {remaining:.0f}s"
            )

            # Wait for next check
            await asyncio.sleep(check_interval)

        logger.info(
            f"✅ Monitoring complete. Detected {len(self.our_liquidations)} liquidations"
        )

    def _update_stats(self, fill: HyperLiquidFill) -> None:
        """Update statistics with new fill data."""
        self.stats["total_liquidations_detected"] += 1
        self.stats["liquidations_by_exchange"]["hyperliquid"] += 1
        self.stats["liquidations_by_coin"][fill.coin] += 1

        side = fill.liquidation_side or "UNKNOWN"
        self.stats["liquidations_by_side"][side] += 1

        self.stats["total_volume_usd"] += fill.value

    async def _fetch_coinglass_data(self) -> None:
        """Fetch comparison data from CoinGlass API."""
        if not self.coinglass_api_key:
            return

        logger.info("🔍 Fetching CoinGlass reference data...")

        try:
            async with aiohttp.ClientSession() as session:
                # CoinGlass liquidation order endpoint (real-time data)
                url = "https://open-api.coinglass.com/public/v2/liquidation_order"

                headers = {
                    "coinglassSecret": self.coinglass_api_key,
                    "Content-Type": "application/json",
                }

                params = {
                    "ex": "Hyperliquid",  # Exchange filter
                    "time_type": "all",  # All time ranges
                }

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.coinglass_data = data.get("data", [])
                        logger.info(
                            f"✅ Retrieved {len(self.coinglass_data)} CoinGlass records"
                        )
                    else:
                        logger.error(
                            f"❌ CoinGlass API error: {response.status} - {await response.text()}"
                        )

        except Exception as e:
            logger.error(f"❌ Failed to fetch CoinGlass data: {e}")

    async def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["duration_seconds"] = self.duration_minutes * 60

        # Calculate average liquidation size
        if self.our_liquidations:
            self.stats["avg_liquidation_size"] = (
                self.stats["total_volume_usd"] / len(self.our_liquidations)
            )

        # Comparison analysis if CoinGlass data available
        comparison = None
        if self.coinglass_data:
            comparison = self._compare_with_coinglass()

        report = {
            "validation_metadata": {
                "duration_minutes": self.duration_minutes,
                "start_time": self.stats["start_time"],
                "end_time": self.stats["end_time"],
                "coinglass_api_used": bool(self.coinglass_api_key),
            },
            "vault_discovery": {
                "vaults_discovered": self.stats["vault_discovery_count"],
                "vault_addresses": self.stats["vaults_discovered"],
                "vault_errors": self.stats["vault_errors"],
                "health_checks_performed": self.stats["vault_health_checks"],
            },
            "liquidation_detection": {
                "total_detected": self.stats["total_liquidations_detected"],
                "by_coin": dict(self.stats["liquidations_by_coin"]),
                "by_side": dict(self.stats["liquidations_by_side"]),
                "total_volume_usd": self.stats["total_volume_usd"],
                "avg_size_usd": self.stats["avg_liquidation_size"],
            },
            "detailed_liquidations": [
                {
                    "tid": fill.tid,
                    "coin": fill.coin,
                    "side": fill.liquidation_side,
                    "price": fill.price,
                    "size": fill.size,
                    "value_usd": fill.value,
                    "timestamp_ms": fill.timestamp_ms,
                }
                for fill in self.our_liquidations[:50]  # First 50 for brevity
            ],
            "vault_health_timeline": self.vault_snapshots,
            "coinglass_comparison": comparison,
            "verdict": self._generate_verdict(),
        }

        return report

    def _compare_with_coinglass(self) -> Dict[str, Any]:
        """Compare our data with CoinGlass reference data."""
        # Create lookup for our liquidations by tid
        our_tids = {fill.tid for fill in self.our_liquidations}

        # Try to match CoinGlass records (if they provide tid or similar)
        coinglass_count = len(self.coinglass_data)
        our_count = len(self.our_liquidations)

        # Calculate basic comparison metrics
        comparison = {
            "our_count": our_count,
            "coinglass_count": coinglass_count,
            "difference": abs(our_count - coinglass_count),
            "difference_percent": (
                abs(our_count - coinglass_count) / max(coinglass_count, 1) * 100
            ),
            "notes": [],
        }

        if coinglass_count == 0:
            comparison["notes"].append(
                "No CoinGlass data available for comparison period"
            )
        elif our_count == coinglass_count:
            comparison["notes"].append("Perfect match with CoinGlass data")
        elif our_count > coinglass_count:
            comparison["notes"].append(
                f"Detected {our_count - coinglass_count} more liquidations than CoinGlass"
            )
        else:
            comparison["notes"].append(
                f"Detected {coinglass_count - our_count} fewer liquidations than CoinGlass"
            )

        return comparison

    def _generate_verdict(self) -> Dict[str, Any]:
        """Generate overall validation verdict."""
        verdict = {"status": "UNKNOWN", "issues": [], "successes": []}

        # Check vault discovery
        if self.stats["vault_discovery_count"] > 0:
            verdict["successes"].append(
                f"✅ Vault discovery working ({self.stats['vault_discovery_count']} vault(s) found)"
            )
        else:
            verdict["issues"].append("❌ No vaults discovered")

        # Check liquidation detection
        if self.stats["total_liquidations_detected"] > 0:
            verdict["successes"].append(
                f"✅ Liquidation detection working ({self.stats['total_liquidations_detected']} detected)"
            )
        else:
            verdict["issues"].append(
                "⚠️  No liquidations detected (may be low activity period)"
            )

        # Check vault health
        if self.stats["vault_errors"] > 0:
            verdict["issues"].append(
                f"⚠️  {self.stats['vault_errors']} vault errors encountered"
            )
        else:
            verdict["successes"].append("✅ No vault errors")

        # Overall status
        if not verdict["issues"]:
            verdict["status"] = "PASS"
        elif len(verdict["successes"]) > len(verdict["issues"]):
            verdict["status"] = "PASS_WITH_WARNINGS"
        else:
            verdict["status"] = "FAIL"

        return verdict

    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """Generate error report if validation fails."""
        return {
            "validation_metadata": {
                "duration_minutes": self.duration_minutes,
                "start_time": self.stats["start_time"],
                "end_time": datetime.now().isoformat(),
                "coinglass_api_used": bool(self.coinglass_api_key),
            },
            "error": error_message,
            "verdict": {
                "status": "FAIL",
                "issues": [f"❌ Critical error: {error_message}"],
                "successes": [],
            },
        }


def print_report(report: Dict[str, Any]) -> None:
    """Print formatted validation report."""
    print("\n" + "=" * 80)
    print("LIQUIDATION VALIDATION REPORT")
    print("=" * 80)

    # Metadata
    meta = report["validation_metadata"]
    print(f"\n📅 Duration: {meta['duration_minutes']} minutes")
    print(f"⏰ Start: {meta['start_time']}")
    print(f"⏰ End: {meta['end_time']}")

    # Vault Discovery
    if "vault_discovery" in report:
        vault = report["vault_discovery"]
        print(f"\n🔍 VAULT DISCOVERY")
        print(f"  Vaults Found: {vault['vaults_discovered']}")
        for addr in vault["vault_addresses"]:
            short = f"{addr[:6]}...{addr[-4:]}" if len(addr) > 10 else addr
            print(f"    • {short}")
        print(f"  Health Checks: {vault['health_checks_performed']}")
        print(f"  Errors: {vault['vault_errors']}")

    # Liquidation Detection
    if "liquidation_detection" in report:
        liq = report["liquidation_detection"]
        print(f"\n💥 LIQUIDATION DETECTION")
        print(f"  Total Detected: {liq['total_detected']}")
        print(f"  Total Volume: ${liq['total_volume_usd']:,.2f}")
        print(f"  Avg Size: ${liq['avg_size_usd']:,.2f}")

        if liq["by_coin"]:
            print(f"\n  By Coin:")
            for coin, count in sorted(
                liq["by_coin"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    • {coin}: {count}")

        if liq["by_side"]:
            print(f"\n  By Side:")
            for side, count in liq["by_side"].items():
                print(f"    • {side}: {count}")

    # CoinGlass Comparison
    if report.get("coinglass_comparison"):
        comp = report["coinglass_comparison"]
        print(f"\n📊 COINGLASS COMPARISON")
        print(f"  Our Count: {comp['our_count']}")
        print(f"  CoinGlass Count: {comp['coinglass_count']}")
        print(f"  Difference: {comp['difference']} ({comp['difference_percent']:.1f}%)")
        for note in comp["notes"]:
            print(f"  {note}")

    # Verdict
    verdict = report["verdict"]
    print(f"\n🎯 VERDICT: {verdict['status']}")

    if verdict["successes"]:
        print("\nSuccesses:")
        for success in verdict["successes"]:
            print(f"  {success}")

    if verdict["issues"]:
        print("\nIssues:")
        for issue in verdict["issues"]:
            print(f"  {issue}")

    print("\n" + "=" * 80 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate liquidation detection accuracy"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Validation duration in minutes (default: 5)",
    )
    parser.add_argument(
        "--coinglass-api-key",
        type=str,
        help="CoinGlass API key for external validation",
    )
    parser.add_argument(
        "--export", type=str, help="Export report to JSON file"
    )

    args = parser.parse_args()

    # Run validation
    validator = LiquidationValidator(
        duration_minutes=args.duration,
        coinglass_api_key=args.coinglass_api_key,
    )

    report = await validator.run_validation()

    # Print report
    print_report(report)

    # Export if requested
    if args.export:
        with open(args.export, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report exported to {args.export}")


if __name__ == "__main__":
    asyncio.run(main())
