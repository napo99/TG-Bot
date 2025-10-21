#!/usr/bin/env python3
"""
OI PROTOTYPING - Standalone Script
Quick prototyping tool for testing exchange OI providers

Usage:
    python oi_prototype_standalone.py BTC
    python oi_prototype_standalone.py ETH --exchanges binance,bybit
    python oi_prototype_standalone.py SOL --compare
"""

import asyncio
import sys
from typing import List, Optional
from loguru import logger

# Import core components
from oi_engine_v2 import BaseExchangeOIProvider, ExchangeOIResult, MarketType
from binance_oi_provider import BinanceOIProvider
from bybit_oi_provider import BybitOIProvider
from okx_oi_provider import OKXOIProvider
from gateio_oi_provider_working import GateIOOIProviderWorking
from bitget_oi_provider_working import BitgetOIProviderWorking
from hyperliquid_oi_provider import HyperliquidOIProvider
# NEW PROVIDERS - Added for expanded exchange coverage
from deribit_oi_provider import DeribitOIProvider
from bitfinex_oi_provider import BitfinexOIProvider
from bitmex_oi_provider import BitmexOIProvider

# Provider registry
PROVIDERS = {
    'binance': BinanceOIProvider,
    'bybit': BybitOIProvider,
    'okx': OKXOIProvider,
    'gateio': GateIOOIProviderWorking,
    'bitget': BitgetOIProviderWorking,
    'hyperliquid': HyperliquidOIProvider,
    # NEW EXCHANGES
    'deribit': DeribitOIProvider,
    'bitfinex': BitfinexOIProvider,
    'bitmex': BitmexOIProvider
}

def format_oi_result(result: ExchangeOIResult, verbose: bool = False) -> str:
    """Format OI result for display"""
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"📊 {result.exchange.upper()} OI ANALYSIS - {result.base_symbol}")
    output.append(f"{'='*70}")

    # Summary
    output.append(f"\n📈 TOTAL OI:")
    output.append(f"   Tokens: {result.total_oi_tokens:,.0f} {result.base_symbol}")
    output.append(f"   USD: ${result.total_oi_usd/1e9:.2f}B")
    output.append(f"   Markets: {len(result.markets)}")
    output.append(f"   Volume 24h: ${result.total_volume_24h_usd/1e9:.2f}B")

    # Market breakdown
    output.append(f"\n📊 MARKET BREAKDOWN:")
    for market in result.markets:
        pct = (market.oi_usd / result.total_oi_usd * 100) if result.total_oi_usd > 0 else 0
        output.append(f"   {market.market_type.value:5} | {market.oi_tokens:10,.0f} {result.base_symbol} | ${market.oi_usd/1e9:6.2f}B | {pct:5.1f}%")

        if verbose:
            output.append(f"         Symbol: {market.symbol}")
            output.append(f"         Price: ${market.price:,.2f}")
            output.append(f"         Funding: {market.funding_rate*100:+.4f}%")
            output.append(f"         Method: {market.calculation_method}")

    # Validation
    if result.validation_passed:
        output.append(f"\n✅ VALIDATION: PASSED")
    else:
        output.append(f"\n❌ VALIDATION: FAILED")
        for error in result.validation_errors:
            output.append(f"   - {error}")

    return "\n".join(output)

def compare_results(results: List[ExchangeOIResult], base_symbol: str) -> str:
    """Compare OI results across exchanges"""
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"🔍 EXCHANGE COMPARISON - {base_symbol}")
    output.append(f"{'='*70}")

    # Header
    output.append(f"\n{'Exchange':<12} | {'Total OI':>12} | {'USD Value':>12} | {'Markets':>8} | Status")
    output.append(f"{'-'*70}")

    # Data
    total_oi_across_all = sum(r.total_oi_tokens for r in results)

    for result in sorted(results, key=lambda x: x.total_oi_usd, reverse=True):
        status = "✅" if result.validation_passed else "❌"
        pct = (result.total_oi_tokens / total_oi_across_all * 100) if total_oi_across_all > 0 else 0

        output.append(
            f"{result.exchange.capitalize():<12} | "
            f"{result.total_oi_tokens:>10,.0f} | "
            f"${result.total_oi_usd/1e9:>10.2f}B | "
            f"{len(result.markets):>8} | "
            f"{status} ({pct:.1f}%)"
        )

    # Totals
    output.append(f"{'-'*70}")
    total_usd = sum(r.total_oi_usd for r in results)
    output.append(f"{'TOTAL':<12} | {total_oi_across_all:>10,.0f} | ${total_usd/1e9:>10.2f}B | {sum(len(r.markets) for r in results):>8}")

    # Market type breakdown
    output.append(f"\n📊 MARKET TYPE BREAKDOWN:")
    usdt_total = sum(sum(m.oi_usd for m in r.usdt_markets) for r in results)
    usdc_total = sum(sum(m.oi_usd for m in r.usdc_markets) for r in results)
    usd_total = sum(sum(m.oi_usd for m in r.usd_markets) for r in results)

    output.append(f"   USDT Stable: ${usdt_total/1e9:.2f}B ({usdt_total/total_usd*100:.1f}%)")
    output.append(f"   USDC Stable: ${usdc_total/1e9:.2f}B ({usdc_total/total_usd*100:.1f}%)")
    output.append(f"   USD Inverse: ${usd_total/1e9:.2f}B ({usd_total/total_usd*100:.1f}%)")

    return "\n".join(output)

async def test_single_provider(provider_name: str, base_symbol: str, verbose: bool = False):
    """Test a single OI provider"""
    if provider_name not in PROVIDERS:
        logger.error(f"Unknown provider: {provider_name}")
        logger.info(f"Available providers: {', '.join(PROVIDERS.keys())}")
        return None

    provider_class = PROVIDERS[provider_name]
    provider = provider_class()

    try:
        logger.info(f"Testing {provider_name} for {base_symbol}...")
        result = await provider.get_oi_data(base_symbol)
        print(format_oi_result(result, verbose=verbose))
        return result

    except Exception as e:
        logger.error(f"Error testing {provider_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        await provider.close()

async def test_all_providers(base_symbol: str, compare: bool = True):
    """Test all OI providers"""
    results = []

    for provider_name in PROVIDERS.keys():
        result = await test_single_provider(provider_name, base_symbol)
        if result and result.validation_passed:
            results.append(result)

    if compare and len(results) > 1:
        print(compare_results(results, base_symbol))

async def test_specific_providers(provider_names: List[str], base_symbol: str, compare: bool = True):
    """Test specific OI providers"""
    results = []

    for provider_name in provider_names:
        result = await test_single_provider(provider_name, base_symbol)
        if result:
            results.append(result)

    if compare and len(results) > 1:
        print(compare_results(results, base_symbol))

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="OI Provider Prototyping Tool")
    parser.add_argument("symbol", help="Base symbol (e.g., BTC, ETH, SOL)")
    parser.add_argument("--exchanges", help="Comma-separated list of exchanges to test")
    parser.add_argument("--compare", action="store_true", help="Show comparison table")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    base_symbol = args.symbol.upper()

    if args.exchanges:
        # Test specific providers
        provider_names = [p.strip() for p in args.exchanges.split(',')]
        asyncio.run(test_specific_providers(provider_names, base_symbol, compare=args.compare))
    else:
        # Test all providers
        asyncio.run(test_all_providers(base_symbol, compare=args.compare))

if __name__ == "__main__":
    # Quick test mode if no args
    if len(sys.argv) == 1:
        print("🚀 OI Provider Prototyping Tool")
        print("=" * 70)
        print("\nUsage:")
        print("  python oi_prototype_standalone.py BTC")
        print("  python oi_prototype_standalone.py ETH --exchanges binance,bybit")
        print("  python oi_prototype_standalone.py SOL --compare --verbose")
        print("\nAvailable exchanges:")
        for name in PROVIDERS.keys():
            print(f"  - {name}")
        print("\nRunning quick test with BTC...\n")
        asyncio.run(test_single_provider("binance", "BTC", verbose=True))
    else:
        main()
