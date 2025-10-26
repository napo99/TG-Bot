"""Unified Open Interest aggregation across all supported exchanges."""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from loguru import logger

from .base import ExchangeDataError, ExchangeFailure, ExchangeOIResult, MarketType
from .binance import BinanceOIProvider
from .bitget import BitgetOIProvider
from .bybit import BybitOIProvider
from .gateio import GateIOOIProvider
from .hyperliquid import HyperliquidOIProvider
from .okx import OKXOIProvider


@dataclass
class UnifiedOIResponse:
    """Structured result returned by :class:`UnifiedOIAggregator`."""

    base_symbol: str
    timestamp: datetime
    total_markets: int
    aggregated_oi: Dict[str, Any]
    exchange_breakdown: List[Dict[str, Any]]
    market_categories: Dict[str, Any]
    validation_summary: Dict[str, Any]


class UnifiedOIAggregator:
    """Aggregate exchange results while capturing validation failures."""

    def __init__(self) -> None:
        self.providers = {
            "binance": BinanceOIProvider(),
            "bybit": BybitOIProvider(),
            "okx": OKXOIProvider(),
            "gateio": GateIOOIProvider(),
            "bitget": BitgetOIProvider(),
            "hyperliquid": HyperliquidOIProvider(),
        }
        self.exchange_priority = list(self.providers.keys())

    async def get_unified_oi_data(self, base_symbol: str) -> UnifiedOIResponse:
        logger.info("🎯 Starting unified OI aggregation for {}", base_symbol)

        tasks = {
            exchange: asyncio.create_task(provider.get_oi_data(base_symbol))
            for exchange, provider in self.providers.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        successes: Dict[str, ExchangeOIResult] = {}
        failures: List[ExchangeFailure] = []

        for exchange, result in zip(tasks.keys(), results):
            failure: Optional[ExchangeFailure] = None

            if isinstance(result, ExchangeOIResult):
                if result.validation_passed:
                    successes[exchange] = result
                    logger.info(
                        "✅ {}: {} {} (${:.1f}B)",
                        exchange.title(),
                        f"{result.total_oi_tokens:,.0f}",
                        base_symbol,
                        result.total_oi_usd / 1e9,
                    )
                else:
                    failure = ExchangeFailure(
                        exchange,
                        "validation_failed",
                        {"errors": result.validation_errors},
                    )
                    logger.warning(
                        "⚠️ {} validation failed: {}",
                        exchange.title(),
                        result.validation_errors,
                    )
            elif isinstance(result, ExchangeDataError):
                failure = ExchangeFailure(exchange, result.reason, result.details)
                logger.error("❌ {} data error: {}", exchange.title(), result)
            elif isinstance(result, Exception):
                failure = ExchangeFailure(
                    exchange,
                    "unexpected_exception",
                    {"error": str(result)},
                )
                logger.exception("❌ {} raised an unexpected error", exchange.title())
            elif result is None:
                failure = ExchangeFailure(exchange, "no_data", None)
                logger.error("❌ {} returned no data", exchange.title())
            else:
                failure = ExchangeFailure(
                    exchange,
                    "unknown_result",
                    {"type": type(result).__name__},
                )
                logger.error("❌ {} returned an unrecognised payload: {}", exchange.title(), result)

            if failure:
                failures.append(failure)

        return self._build_unified_response(base_symbol, successes, failures)

    def _build_unified_response(
        self,
        base_symbol: str,
        successful_exchanges: Mapping[str, ExchangeOIResult],
        failures: List[ExchangeFailure],
    ) -> UnifiedOIResponse:
        total_oi_tokens = sum(result.total_oi_tokens for result in successful_exchanges.values())
        total_oi_usd = sum(result.total_oi_usd for result in successful_exchanges.values())
        total_volume_24h = sum(result.total_volume_24h for result in successful_exchanges.values())
        total_volume_24h_usd = sum(result.total_volume_24h_usd for result in successful_exchanges.values())

        exchange_breakdown: List[Dict[str, Any]] = []
        for exchange in self.exchange_priority:
            if exchange not in successful_exchanges:
                continue

            result = successful_exchanges[exchange]
            oi_weight = result.total_oi_usd if result.total_oi_usd > 0 else 0
            weighted_funding = 0.0
            if oi_weight > 0:
                weighted_funding = sum(
                    market.funding_rate * market.oi_usd
                    for market in result.markets
                    if market.funding_rate != 0
                )
                funding_denominator = sum(
                    market.oi_usd for market in result.markets if market.funding_rate != 0
                )
                if funding_denominator > 0:
                    weighted_funding /= funding_denominator
                else:
                    weighted_funding = 0.0

            exchange_breakdown.append(
                {
                    "exchange": exchange,
                    "oi_tokens": result.total_oi_tokens,
                    "oi_usd": result.total_oi_usd,
                    "oi_percentage": (result.total_oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0,
                    "funding_rate": weighted_funding,
                    "volume_24h": result.total_volume_24h,
                    "volume_24h_usd": result.total_volume_24h_usd,
                    "markets": len(result.markets),
                    "market_breakdown": [
                        {
                            "type": market.market_type.value,
                            "symbol": market.symbol,
                            "oi_tokens": market.oi_tokens,
                            "oi_usd": market.oi_usd,
                            "price": market.price,
                            "funding_rate": market.funding_rate,
                            "volume_24h": market.volume_24h,
                            "volume_24h_usd": market.volume_24h_usd,
                            "price_validated": market.price_validated,
                        }
                        for market in result.markets
                    ],
                }
            )

        market_categories = self._calculate_market_categories(successful_exchanges, total_oi_usd)

        validation_summary = {
            "successful_exchanges": len(successful_exchanges),
            "failed_exchanges": len(failures),
            "total_markets": sum(len(result.markets) for result in successful_exchanges.values()),
            "validation_passed": len(successful_exchanges) >= 4,
            "failed_details": [
                {
                    "exchange": failure.exchange,
                    "reason": failure.reason,
                    "details": failure.details,
                }
                for failure in failures
            ],
        }

        aggregated_oi = {
            "total_tokens": total_oi_tokens,
            "total_usd": total_oi_usd,
            "total_volume_24h": total_volume_24h,
            "total_volume_24h_usd": total_volume_24h_usd,
            "exchanges_count": len(successful_exchanges),
        }

        return UnifiedOIResponse(
            base_symbol=base_symbol,
            timestamp=datetime.now(),
            total_markets=validation_summary["total_markets"],
            aggregated_oi=aggregated_oi,
            exchange_breakdown=exchange_breakdown,
            market_categories=market_categories,
            validation_summary=validation_summary,
        )

    def _calculate_market_categories(
        self, successful_exchanges: Mapping[str, ExchangeOIResult], total_oi_usd: float
    ) -> Dict[str, Any]:
        category_totals = {
            MarketType.USDT: {"tokens": 0.0, "usd": 0.0, "exchanges": 0},
            MarketType.USDC: {"tokens": 0.0, "usd": 0.0, "exchanges": 0},
            MarketType.USD: {"tokens": 0.0, "usd": 0.0, "exchanges": 0},
        }

        for result in successful_exchanges.values():
            seen = set()
            for market in result.markets:
                category_totals[market.market_type]["tokens"] += market.oi_tokens
                category_totals[market.market_type]["usd"] += market.oi_usd
                seen.add(market.market_type)

            for market_type in seen:
                category_totals[market_type]["exchanges"] += 1

        def _summary(market_type: MarketType) -> Dict[str, Any]:
            entry = category_totals[market_type]
            return {
                "total_tokens": entry["tokens"],
                "total_usd": entry["usd"],
                "percentage": (entry["usd"] / total_oi_usd * 100) if total_oi_usd > 0 else 0,
                "exchanges": entry["exchanges"],
            }

        return {
            "usdt_stable": _summary(MarketType.USDT),
            "usdc_stable": _summary(MarketType.USDC),
            "usd_inverse": _summary(MarketType.USD),
        }

    async def close(self) -> None:
        for provider in self.providers.values():
            await provider.close()


async def test_unified_system() -> Optional[UnifiedOIResponse]:
    """Convenience helper to fetch and persist a snapshot for BTC."""

    print("🚀 Testing UNIFIED 6-Exchange OI System")
    print("=" * 60)

    aggregator = UnifiedOIAggregator()
    try:
        result = await aggregator.get_unified_oi_data("BTC")

        print("\n📊 UNIFIED SYSTEM RESULTS:")
        print(f"Base Symbol: {result.base_symbol}")
        print(f"Total Markets: {result.total_markets}")
        print(
            f"Total OI: {result.aggregated_oi['total_tokens']:,.0f} BTC "
            f"(${result.aggregated_oi['total_usd']/1e9:.1f}B)"
        )
        print(
            "Successful Exchanges: "
            f"{result.validation_summary['successful_exchanges']}/{len(aggregator.providers)}"
        )

        print("\n📈 EXCHANGE BREAKDOWN:")
        for exchange_data in result.exchange_breakdown:
            exchange = exchange_data["exchange"]
            oi_tokens = exchange_data["oi_tokens"]
            oi_usd = exchange_data["oi_usd"]
            percentage = exchange_data["oi_percentage"]
            markets = exchange_data["markets"]

            print(
                f"  {exchange.upper()}: {oi_tokens:,.0f} BTC (${oi_usd/1e9:.1f}B) - {percentage:.1f}% - {markets} markets"
            )

        print("\n🏷️ MARKET CATEGORIES:")
        categories = result.market_categories
        for label, entry in categories.items():
            print(
                f"  {label.replace('_', ' ').upper()}: {entry['total_tokens']:,.0f} BTC "
                f"(${entry['total_usd']/1e9:.1f}B) - {entry['percentage']:.1f}% - {entry['exchanges']} exchanges"
            )

        print("\n✅ VALIDATION SUMMARY:")
        validation = result.validation_summary
        status = "✅ PASSED" if validation["validation_passed"] else "❌ FAILED"
        print(f"  Status: {status}")
        print(
            f"  Working: {validation['successful_exchanges']}"
            f"/{len(aggregator.providers)} exchanges"
        )
        if validation["failed_details"]:
            print("  Failed Exchanges:")
            for failure in validation["failed_details"]:
                print(
                    f"    - {failure['exchange']}: {failure['reason']} "
                    f"{failure.get('details', '')}"
                )

        output_path = Path("unified_oi_results.json")
        with output_path.open("w", encoding="utf-8") as handle:
            payload = asdict(result)
            payload["timestamp"] = payload["timestamp"].isoformat()
            json.dump(payload, handle, indent=2)

        print(f"\n📄 Detailed results saved to: {output_path.resolve()}")
        return result
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f"❌ Unified system test failed: {exc}")
        import traceback

        traceback.print_exc()
        return None
    finally:
        await aggregator.close()


if __name__ == "__main__":
    asyncio.run(test_unified_system())
