"""
Bitfinex OI Provider
Fetches Open Interest data from Bitfinex derivatives exchange
API Documentation: https://docs.bitfinex.com/reference/rest-public-derivatives-status
"""

import aiohttp
from typing import List, Optional
from datetime import datetime
from loguru import logger
from oi_engine_v2 import BaseExchangeOIProvider, ExchangeOIResult, MarketOIData, MarketType


class BitfinexOIProvider(BaseExchangeOIProvider):
    """Bitfinex Open Interest Provider"""

    def __init__(self):
        self.base_url = "https://api-pub.bitfinex.com/v2"
        self.session: Optional[aiohttp.ClientSession] = None

        # Bitfinex derivative symbols mapping
        self.derivative_symbols = {
            "BTC": "tBTCF0:USTF0",
            "ETH": "tETHF0:USTF0",
            "SOL": "tSOLF0:USTF0",  # May not exist, will handle error
            "ADA": "tADAF0:USTF0",
            "DOT": "tDOTF0:USTF0",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    def get_supported_market_types(self) -> List[MarketType]:
        """Bitfinex supports USDT perpetuals"""
        return [MarketType.USDT]

    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Bitfinex API

        Bitfinex format: tBTCF0:USTF0 (perpetual futures)
        """
        return self.derivative_symbols.get(base_symbol, f"t{base_symbol}F0:USTF0")

    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Fetch OI data from Bitfinex

        Endpoint: GET /v2/status/deriv?keys={SYMBOL}
        Response: Nested array format [[SYMBOL, ...data...]]

        REST API format (differs from WebSocket by +1 offset due to SYMBOL field):
        [
          [
            SYMBOL,               // [0] REST only (not in WebSocket)
            TIME_MS,              // [1]
            null,                 // [2]
            DERIV_PRICE,          // [3]
            SPOT_PRICE,           // [4]
            null,                 // [5]
            INSURANCE_FUND,       // [6]
            null,                 // [7]
            NEXT_FUNDING_EVT,     // [8]
            NEXT_FUNDING_ACCRUED, // [9]
            NEXT_FUNDING_STEP,    // [10]
            null,                 // [11]
            CURRENT_FUNDING,      // [12]
            null,                 // [13]
            null,                 // [14]
            MARK_PRICE,           // [15]
            null,                 // [16]
            null,                 // [17]
            OPEN_INTEREST         // [18] ← HERE!
          ]
        ]
        """
        session = await self._get_session()
        markets = []

        try:
            # Get derivative symbol
            deriv_symbol = self.format_symbol(base_symbol, MarketType.USDT)

            # Bitfinex endpoint - must include derivative symbol in path
            # Format: /v2/status/deriv/{SYMBOL} or /v2/status/deriv?keys={SYMBOL}
            url = f"{self.base_url}/status/deriv?keys={deriv_symbol}"

            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Bitfinex API error: {response.status}")
                    return ExchangeOIResult(
                        exchange="bitfinex",
                        base_symbol=base_symbol,
                        markets=[],
                        total_oi_tokens=0,
                        total_oi_usd=0,
                        total_volume_24h=0,
                        total_volume_24h_usd=0
                    )

                data = await response.json()

                # REST API returns nested array: [[symbol, data...]]
                # Extract the inner array (first element)
                if not isinstance(data, list) or len(data) == 0:
                    logger.warning(f"Bitfinex: Empty response for {base_symbol}")
                    return ExchangeOIResult(
                        exchange="bitfinex",
                        base_symbol=base_symbol,
                        markets=[],
                        total_oi_tokens=0,
                        total_oi_usd=0,
                        total_volume_24h=0,
                        total_volume_24h_usd=0
                    )

                # Get first result (inner array)
                result = data[0]
                if not isinstance(result, list) or len(result) < 19:
                    logger.warning(f"Bitfinex: Unexpected response format for {base_symbol} - got {len(result) if isinstance(result, list) else 0} fields")
                    return ExchangeOIResult(
                        exchange="bitfinex",
                        base_symbol=base_symbol,
                        markets=[],
                        total_oi_tokens=0,
                        total_oi_usd=0,
                        total_volume_24h=0,
                        total_volume_24h_usd=0
                    )

                # Extract data from array positions
                # REST API format (includes SYMBOL at [0], shifts all WebSocket indices by +1):
                # [0] = SYMBOL
                # [3] = DERIV_PRICE
                # [4] = SPOT_PRICE
                # [12] = CURRENT_FUNDING
                # [15] = MARK_PRICE
                # [18] = OPEN_INTEREST ← REST INDEX (WebSocket [17] + 1)

                deriv_price = float(result[3]) if len(result) > 3 and result[3] else 0
                mark_price = float(result[15]) if len(result) > 15 and result[15] else deriv_price
                current_funding = float(result[12]) if len(result) > 12 and result[12] else 0
                open_interest = float(result[18]) if len(result) > 18 and result[18] else 0

                if open_interest <= 0 or mark_price <= 0:
                    logger.warning(f"Bitfinex: Invalid OI or price for {base_symbol}")
                    return ExchangeOIResult(
                        exchange="bitfinex",
                        base_symbol=base_symbol,
                        markets=[],
                        total_oi_tokens=0,
                        total_oi_usd=0,
                        total_volume_24h=0,
                        total_volume_24h_usd=0
                    )

                # Bitfinex OI is in token amount (BTC contracts)
                oi_tokens = open_interest
                oi_usd = oi_tokens * mark_price if mark_price > 0 else 0

                # Funding rate (current 8-hour rate, convert to daily)
                funding_rate_daily = current_funding * 3  # Approximate daily rate

                market = MarketOIData(
                    exchange="bitfinex",
                    symbol=deriv_symbol,
                    base_symbol=base_symbol,
                    market_type=MarketType.USDT,
                    oi_tokens=oi_tokens,
                    oi_usd=oi_usd,
                    price=mark_price,
                    funding_rate=funding_rate_daily,
                    volume_24h=0,  # Not provided in status endpoint
                    volume_24h_usd=0,
                    timestamp=datetime.now(),
                    api_source=f"Bitfinex API v2: deriv status",
                    calculation_method="direct"
                )

                markets.append(market)
                logger.debug(f"Bitfinex {deriv_symbol}: ${oi_usd/1e9:.2f}B @ ${mark_price:,.2f}")

        except Exception as e:
            logger.error(f"Error fetching Bitfinex OI for {base_symbol}: {e}")
            import traceback
            traceback.print_exc()

        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)

        return ExchangeOIResult(
            exchange="bitfinex",
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
async def test_bitfinex_provider():
    """Test Bitfinex OI provider"""
    provider = BitfinexOIProvider()

    try:
        # Test with BTC
        print("\n" + "="*70)
        print("Testing Bitfinex OI Provider - BTC")
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

    finally:
        await provider.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bitfinex_provider())
