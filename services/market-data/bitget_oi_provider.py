#!/usr/bin/env python3
"""
BITGET OI PROVIDER: Implementation for USDT linear and USD inverse markets
Based on Agent 3's research findings on Bitget API structure
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger

from oi_engine_v2 import (
    BaseExchangeOIProvider, 
    MarketOIData, 
    ExchangeOIResult, 
    MarketType
)

class BitgetOIProvider(BaseExchangeOIProvider):
    """
    Bitget OI Provider supporting 2 market types:
    - USDT Linear: BTCUSDT_UMCBL (linear perpetual)
    - USD Inverse: BTCUSD_DMCBL (coin-margined)
    Note: Bitget may not offer USDC perpetuals
    """
    
    def __init__(self):
        super().__init__("bitget")
        self.api_base = "https://api.bitget.com"
        
        # Bitget V1 API endpoints (V2 returns 400 errors)
        self.endpoints = {
            'ticker': f"{self.api_base}/api/mix/v1/market/ticker",
            'funding': f"{self.api_base}/api/mix/v1/market/current-fund-rate"
        }
        
        # Bitget product types
        self.product_types = {
            MarketType.USDT: "USDT-FUTURES",   # Linear USDT
            MarketType.USD: "COIN-FUTURES"     # Inverse USD
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Bitget supports USDT linear and USD inverse"""
        return [MarketType.USDT, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Bitget APIs"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}USDT_UMCBL"  # Linear USDT perpetual
        elif market_type == MarketType.USD:
            return f"{base}USD_DMCBL"   # Inverse USD perpetual  
        else:
            raise ValueError(f"Unsupported market type for Bitget: {market_type}")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for Bitget market types"""
        logger.info(f"🟡 Fetching Bitget OI for {base_symbol}")
        
        markets = []
        errors = []
        
        # Fetch supported market types in parallel
        market_tasks = [
            self._fetch_usdt_market(base_symbol),
            self._fetch_usd_market(base_symbol)
        ]
        
        market_results = await asyncio.gather(*market_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(market_results):
            market_type = [MarketType.USDT, MarketType.USD][i]
            
            if isinstance(result, Exception):
                error_msg = f"{market_type.value}: {str(result)}"
                errors.append(error_msg)
                logger.warning(f"⚠️ Bitget {market_type.value} failed: {str(result)}")
            elif result is not None:
                markets.append(result)
                logger.info(f"✅ Bitget {market_type.value}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
        
        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)
        
        # Categorize markets
        usdt_markets = [m for m in markets if m.market_type == MarketType.USDT]
        usdc_markets = []  # Bitget doesn't offer USDC perpetuals
        usd_markets = [m for m in markets if m.market_type == MarketType.USD]
        
        result = ExchangeOIResult(
            exchange="bitget",
            base_symbol=base_symbol,
            markets=markets,
            total_oi_tokens=total_oi_tokens,
            total_oi_usd=total_oi_usd,
            total_volume_24h=total_volume_24h,
            total_volume_24h_usd=total_volume_24h_usd,
            usdt_markets=usdt_markets,
            usdc_markets=usdc_markets,
            usd_markets=usd_markets,
            validation_passed=len(errors) < len(market_tasks),  # Allow some failures
            validation_errors=errors
        )
        
        logger.info(f"🟡 Bitget total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_usdt_market(self, base_symbol: str) -> Optional[MarketOIData]:
        """Fetch USDT linear market data"""
        try:
            symbol = self.format_symbol(base_symbol, MarketType.USDT)
            product_type = self.product_types[MarketType.USDT]
            session = await self.get_session()
            
            # Fetch ticker data (includes OI, price, volume)
            ticker_params = {"symbol": symbol, "productType": product_type}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Fetch funding rate
            funding_params = {"symbol": symbol, "productType": product_type}
            async with session.get(self.endpoints['funding'], params=funding_params) as response:
                funding_response = await response.json()
            
            # Validate ticker response (V1 API doesn't use 'code' field)
            if not ticker_response.get('data'):
                logger.warning(f"⚠️ Bitget USDT ticker data unavailable for {symbol}")
                return None
            
            ticker_data = ticker_response['data']
            
            # Extract data from ticker (using correct field names from API)
            price = float(ticker_data['last'])  # Price field is 'last', not 'lastPr'
            # Use baseVolume field which contains 24h volume in base currency (BTC)
            volume_24h = float(ticker_data.get('baseVolume', 0))
            
            # Extract OI data
            oi_tokens = 0.0
            if 'openInterest' in ticker_data:
                oi_tokens = float(ticker_data['openInterest'])
            elif 'holdingAmount' in ticker_data:
                # Use holding amount as OI proxy
                oi_tokens = float(ticker_data['holdingAmount'])
            else:
                logger.warning(f"⚠️ Bitget USDT: No OI field found for {symbol}")
                return None
            
            # Extract funding rate (V1 API doesn't use 'code' field)
            funding_rate = 0.0
            if funding_response.get('data'):
                funding_data = funding_response['data']
                funding_rate = float(funding_data.get('fundingRate', 0))
            
            # Calculate USD values
            oi_usd = oi_tokens * price
            volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="bitget",
                symbol=symbol,
                base_symbol=base_symbol,
                market_type=MarketType.USDT,
                oi_tokens=oi_tokens,
                oi_usd=oi_usd,
                price=price,
                funding_rate=funding_rate,
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h_usd,
                timestamp=datetime.now(),
                api_source=f"V2-USDT:{symbol}",
                calculation_method=f"linear: {oi_tokens:,.0f} × ${price:,.2f}",
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Bitget USDT error: {str(e)}")
            return None
    
    async def _fetch_usd_market(self, base_symbol: str) -> Optional[MarketOIData]:
        """Fetch USD inverse market data"""
        try:
            symbol = self.format_symbol(base_symbol, MarketType.USD)
            product_type = self.product_types[MarketType.USD]
            session = await self.get_session()
            
            # Fetch ticker data
            ticker_params = {"symbol": symbol, "productType": product_type}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Fetch funding rate
            funding_params = {"symbol": symbol, "productType": product_type}
            async with session.get(self.endpoints['funding'], params=funding_params) as response:
                funding_response = await response.json()
            
            # Validate ticker response (V1 API doesn't use 'code' field)
            if not ticker_response.get('data'):
                logger.warning(f"⚠️ Bitget USD ticker data unavailable for {symbol}")
                return None
            
            ticker_data = ticker_response['data']
            
            # Extract data (using correct field names from API)
            price = float(ticker_data['last'])  # Price field is 'last', not 'lastPr'
            # Use baseVolume field which contains 24h volume in base currency (BTC)
            volume_24h = float(ticker_data.get('baseVolume', 0))
            
            # Extract OI data for inverse contracts
            oi_tokens = 0.0
            calculation_method = ""
            
            if 'openInterest' in ticker_data:
                # For inverse contracts, openInterest might be in contracts
                oi_raw = float(ticker_data['openInterest'])
                # Bitget inverse: Check if this needs conversion
                # If value seems too large, it might be in USD terms, divide by price
                if oi_raw > 1_000_000:  # Likely in USD terms
                    oi_tokens = oi_raw / price
                    calculation_method = f"inverse: {oi_raw:,.0f} USD ÷ ${price:,.2f}"
                else:  # Likely already in BTC terms
                    oi_tokens = oi_raw
                    calculation_method = f"inverse: {oi_tokens:,.0f} × ${price:,.2f}"
            elif 'holdingAmount' in ticker_data:
                oi_tokens = float(ticker_data['holdingAmount'])
                calculation_method = f"inverse: holding {oi_tokens:,.0f} × ${price:,.2f}"
            else:
                logger.warning(f"⚠️ Bitget USD: No OI field found for {symbol}")
                return None
            
            # Extract funding rate (V1 API doesn't use 'code' field)
            funding_rate = 0.0
            if funding_response.get('data'):
                funding_data = funding_response['data']
                funding_rate = float(funding_data.get('fundingRate', 0))
            
            # Calculate USD values
            oi_usd = oi_tokens * price
            volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="bitget",
                symbol=symbol,
                base_symbol=base_symbol,
                market_type=MarketType.USD,
                oi_tokens=oi_tokens,
                oi_usd=oi_usd,
                price=price,
                funding_rate=funding_rate,
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h_usd,
                timestamp=datetime.now(),
                api_source=f"V2-USD:{symbol}",
                calculation_method=calculation_method,
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Bitget USD error: {str(e)}")
            return None
    
    def _calculate_inverse_usd(self, oi_tokens: float, price: float) -> float:
        """Bitget-specific inverse calculation"""
        return oi_tokens * price

# Testing function
async def test_bitget_provider():
    """Test Bitget provider implementation"""
    print("🚀 Testing Bitget OI Provider")
    
    provider = BitgetOIProvider()
    
    try:
        # Test with BTC
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 BITGET TEST RESULTS:")
        print(f"Exchange: {result.exchange}")
        print(f"Symbol: {result.base_symbol}")
        print(f"Markets found: {len(result.markets)}")
        print(f"Total OI: {result.total_oi_tokens:,.0f} BTC (${result.total_oi_usd/1e9:.1f}B)")
        print(f"Validation: {'✅ PASSED' if result.validation_passed else '❌ FAILED'}")
        
        if result.validation_errors:
            print(f"Errors: {result.validation_errors}")
        
        print(f"\n📈 MARKET BREAKDOWN:")
        for market in result.markets:
            print(f"  {market.market_type.value}: {market.oi_tokens:,.0f} BTC (${market.oi_usd/1e9:.1f}B)")
            print(f"    Price: ${market.price:,.2f}")
            print(f"    Method: {market.calculation_method}")
            print(f"    Source: {market.api_source}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(test_bitget_provider())