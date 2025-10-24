"""
Bitmex OI Provider
Fetches Open Interest data from Bitmex derivatives exchange
API Documentation: https://www.bitmex.com/api/explorer/
"""

import aiohttp
from typing import List, Optional
from datetime import datetime
from loguru import logger
from oi_engine_v2 import BaseExchangeOIProvider, ExchangeOIResult, MarketOIData, MarketType


class BitmexOIProvider(BaseExchangeOIProvider):
    """Bitmex Open Interest Provider"""

    def __init__(self):
        self.base_url = "https://www.bitmex.com/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None

        # Bitmex symbol mapping (inverse perpetuals)
        self.perpetual_symbols = {
            "BTC": "XBTUSD",
            "ETH": "ETHUSD",
            "SOL": "SOLUSD",
            "ADA": "ADAUSD",
            "DOT": "DOTUSD",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    def get_supported_market_types(self) -> List[MarketType]:
        """Bitmex primarily uses inverse perpetuals (USD-margined)"""
        return [MarketType.USD]  # Inverse contracts

    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Bitmex API

        Bitmex format: XBTUSD (BTC perpetual), ETHUSD, etc.
        """
        return self.perpetual_symbols.get(base_symbol, f"{base_symbol}USD")

    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Fetch OI data from Bitmex

        Endpoint: GET /instrument
        Parameters: symbol={symbol}, filter={"typ":"FFWCSX"}

        Response includes:
        - openInterest: Total OI in USD (for inverse contracts)
        - markPrice: Current mark price
        - fundingRate: Current funding rate
        - volume24h: 24h volume
        """
        session = await self._get_session()
        markets = []

        try:
            # Get Bitmex symbol
            bitmex_symbol = self.format_symbol(base_symbol, MarketType.USD)

            # Bitmex instrument endpoint
            url = f"{self.base_url}/instrument"
            params = {
                "symbol": bitmex_symbol,
                "count": 1
            }

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Bitmex API error: {response.status}")
                    return ExchangeOIResult(
                        exchange="bitmex",
                        base_symbol=base_symbol,
                        markets=[]
                    )

                data = await response.json()

                if not isinstance(data, list) or len(data) == 0:
                    logger.warning(f"Bitmex: No data for {base_symbol}")
                    return ExchangeOIResult(
                        exchange="bitmex",
                        base_symbol=base_symbol,
                        markets=[]
                    )

                instrument = data[0]

                # Extract data
                open_interest_usd = float(instrument.get("openInterest", 0) or 0)
                mark_price = float(instrument.get("markPrice", 0) or 0)
                funding_rate = float(instrument.get("fundingRate", 0) or 0)
                volume_24h = float(instrument.get("volume24h", 0) or 0)
                last_price = float(instrument.get("lastPrice", 0) or 0)

                # Use mark price if available, otherwise last price
                price = mark_price if mark_price > 0 else last_price

                if open_interest_usd <= 0 or price <= 0:
                    logger.warning(f"Bitmex: Invalid OI or price for {base_symbol}")
                    return ExchangeOIResult(
                        exchange="bitmex",
                        base_symbol=base_symbol,
                        markets=[]
                    )

                # Bitmex inverse contracts: OI is in USD
                # Convert to tokens (BTC/ETH contracts)
                # For inverse: 1 contract = $1 USD, so OI in BTC = OI_USD / Price
                oi_tokens = open_interest_usd / price if price > 0 else 0
                oi_usd = open_interest_usd

                # Funding rate (8-hour rate, convert to daily)
                funding_rate_daily = funding_rate * 3  # Approximate daily rate

                # Volume 24h in tokens (approximate from USD volume)
                volume_24h_tokens = volume_24h / price if price > 0 else 0

                market = MarketOIData(
                    exchange="bitmex",
                    symbol=bitmex_symbol,
                    base_symbol=base_symbol,
                    market_type=MarketType.USD,  # Inverse contract
                    oi_tokens=oi_tokens,
                    oi_usd=oi_usd,
                    price=price,
                    funding_rate=funding_rate_daily,
                    volume_24h=volume_24h_tokens,
                    volume_24h_usd=volume_24h,
                    timestamp=datetime.now(),
                    api_source=f"Bitmex API v1: {bitmex_symbol}",
                    calculation_method="inverse"
                )

                markets.append(market)
                logger.debug(f"Bitmex {bitmex_symbol}: {oi_tokens:,.2f} contracts @ ${price:,.2f}")

        except Exception as e:
            logger.error(f"Error fetching Bitmex OI for {base_symbol}: {e}")
            import traceback
            traceback.print_exc()

        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)

        return ExchangeOIResult(
            exchange="bitmex",
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
async def test_bitmex_provider():
    """Test Bitmex OI provider"""
    provider = BitmexOIProvider()

    try:
        # Test with BTC
        print("\n" + "="*70)
        print("Testing Bitmex OI Provider - BTC")
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
            print(f"    Method: {market.calculation_method}")

    finally:
        await provider.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bitmex_provider())
