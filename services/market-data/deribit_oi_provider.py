"""
Deribit OI Provider
Fetches Open Interest data from Deribit derivatives exchange
API Documentation: https://docs.deribit.com/
"""

import aiohttp
from typing import List, Optional
from datetime import datetime
from loguru import logger
from oi_engine_v2 import BaseExchangeOIProvider, ExchangeOIResult, MarketOIData, MarketType


class DeribitOIProvider(BaseExchangeOIProvider):
    """Deribit Open Interest Provider"""

    def __init__(self):
        self.base_url = "https://www.deribit.com/api/v2"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    def get_supported_market_types(self) -> List[MarketType]:
        """Deribit supports futures/perpetuals (we'll categorize as USDT for now)"""
        return [MarketType.USDT]  # Deribit uses native BTC/ETH settlement

    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Deribit API

        Deribit format: BTC-PERPETUAL, ETH-PERPETUAL
        """
        return f"{base_symbol}-PERPETUAL"

    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Fetch OI data from Deribit

        Endpoint: GET /public/get_book_summary_by_currency
        Parameters: currency (BTC, ETH, SOL, etc.), kind=future

        Response includes:
        - open_interest: Total OI in contracts
        - volume_usd: 24h volume in USD
        - mark_price: Current mark price
        - funding_rate: Current funding rate (for perpetuals)
        """
        session = await self._get_session()
        markets = []

        try:
            # Deribit uses currency-based endpoint
            url = f"{self.base_url}/public/get_book_summary_by_currency"
            params = {
                "currency": base_symbol,
                "kind": "future"  # Includes perpetuals
            }

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Deribit API error: {response.status}")
                    return ExchangeOIResult(
                        exchange="deribit",
                        base_symbol=base_symbol,
                        markets=[]
                    )

                data = await response.json()

                if "result" not in data:
                    logger.warning(f"Deribit: No result for {base_symbol}")
                    return ExchangeOIResult(
                        exchange="deribit",
                        base_symbol=base_symbol,
                        markets=[]
                    )

                # Process each instrument (multiple futures/perpetuals possible)
                for instrument in data["result"]:
                    instrument_name = instrument.get("instrument_name", "")

                    # Focus on perpetual contracts
                    if "PERPETUAL" not in instrument_name:
                        continue

                    # Extract data
                    open_interest_usd = float(instrument.get("open_interest", 0))  # Already in USD!
                    mark_price = float(instrument.get("mark_price", 0))
                    volume_usd = float(instrument.get("volume_usd", 0))

                    # Funding rate (8-hour rate, convert to daily for consistency)
                    funding_rate_8h = float(instrument.get("funding_8h", 0))
                    funding_rate_daily = funding_rate_8h * 3  # Approximate daily rate

                    if open_interest_usd <= 0 or mark_price <= 0:
                        continue

                    # IMPORTANT: Deribit's open_interest is ALREADY in USD!
                    # Need to convert to BTC tokens: OI_USD / Price
                    oi_usd = open_interest_usd
                    oi_tokens = oi_usd / mark_price if mark_price > 0 else 0

                    # Volume 24h in tokens (approximate from USD)
                    volume_24h_tokens = volume_usd / mark_price if mark_price > 0 else 0

                    market = MarketOIData(
                        exchange="deribit",
                        symbol=instrument_name,
                        base_symbol=base_symbol,
                        market_type=MarketType.USDT,  # Categorize as linear for consistency
                        oi_tokens=oi_tokens,
                        oi_usd=oi_usd,
                        price=mark_price,
                        funding_rate=funding_rate_daily,
                        volume_24h=volume_24h_tokens,
                        volume_24h_usd=volume_usd,
                        timestamp=datetime.now(),
                        api_source=f"Deribit API v2: {instrument_name}",
                        calculation_method="direct"
                    )

                    markets.append(market)
                    logger.debug(f"Deribit {instrument_name}: {oi_tokens:,.0f} contracts @ ${mark_price:,.2f}")

        except Exception as e:
            logger.error(f"Error fetching Deribit OI for {base_symbol}: {e}")
            import traceback
            traceback.print_exc()

        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)

        return ExchangeOIResult(
            exchange="deribit",
            base_symbol=base_symbol,
            markets=markets,
            total_oi_tokens=total_oi_tokens,
            total_oi_usd=total_oi_usd,
            total_volume_24h=total_volume_24h,
            total_volume_24h_usd=total_volume_24h_usd,
            validation_passed=len(markets) > 0,  # Pass validation if we have markets
            validation_errors=[]
        )

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None


# Test function
async def test_deribit_provider():
    """Test Deribit OI provider"""
    provider = DeribitOIProvider()

    try:
        # Test with BTC
        print("\n" + "="*70)
        print("Testing Deribit OI Provider - BTC")
        print("="*70)

        result = await provider.get_oi_data("BTC")

        print(f"\nExchange: {result.exchange}")
        print(f"Symbol: {result.base_symbol}")
        print(f"Total OI: {result.total_oi_tokens:,.2f} BTC")
        print(f"Total USD: ${result.total_oi_usd/1e9:.2f}B")
        print(f"Markets: {len(result.markets)}")
        print(f"Validation: {'✅ PASSED' if result.validation_passed else '❌ FAILED'}")

        if result.validation_errors:
            print("\nValidation Errors:")
            for error in result.validation_errors:
                print(f"  - {error}")

        print("\nMarket Breakdown:")
        for market in result.markets:
            print(f"  {market.symbol}:")
            print(f"    OI: {market.oi_tokens:,.2f} BTC (${market.oi_usd/1e9:.2f}B)")
            print(f"    Price: ${market.price:,.2f}")
            print(f"    Funding: {market.funding_rate*100:.4f}%")
            print(f"    Volume 24h: {market.volume_24h:,.0f} BTC")

    finally:
        await provider.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_deribit_provider())
