#!/usr/bin/env python3
"""
BYBIT OI PROVIDER: Complete implementation for all 3 market types
Implements Linear (USDT/USDC) and Inverse (USD) with proper inverse contract handling
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

class BybitOIProvider(BaseExchangeOIProvider):
    """
    Bybit OI Provider supporting all market types:
    - USDT Linear: BTCUSDT
    - USDC Linear: BTCUSDC  
    - USD Inverse: BTCUSD (coin-margined)
    """
    
    def __init__(self):
        super().__init__("bybit")
        self.api_base = "https://api.bybit.com"
        
        # Bybit V5 API endpoints
        self.endpoints = {
            'oi': f"{self.api_base}/v5/market/open-interest",
            'ticker': f"{self.api_base}/v5/market/tickers",
            'funding': f"{self.api_base}/v5/market/funding/history"
        }
        
        # Bybit categories
        self.categories = {
            MarketType.USDT: "linear",     # Linear USDT
            MarketType.USDC: "linear",     # Linear USDC (if available)
            MarketType.USD: "inverse"      # Inverse USD
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Bybit supports all 3 market types"""
        return [MarketType.USDT, MarketType.USDC, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Bybit APIs"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}USDT"
        elif market_type == MarketType.USDC:
            return f"{base}PERP"  # Bybit uses BTCPERP for USDC linear
        elif market_type == MarketType.USD:
            return f"{base}USD"  # Inverse contracts
        else:
            raise ValueError(f"Unsupported market type: {market_type}")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for all Bybit market types"""
        logger.info(f"🟣 Fetching Bybit OI for {base_symbol}")
        
        markets = []
        errors = []
        
        # Fetch all market types in parallel
        market_tasks = [
            self._fetch_linear_market(base_symbol, MarketType.USDT),
            self._fetch_linear_market(base_symbol, MarketType.USDC),
            self._fetch_inverse_market(base_symbol, MarketType.USD)
        ]
        
        market_results = await asyncio.gather(*market_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(market_results):
            market_type = [MarketType.USDT, MarketType.USDC, MarketType.USD][i]
            
            if isinstance(result, Exception):
                error_msg = f"{market_type.value}: {str(result)}"
                errors.append(error_msg)
                logger.warning(f"⚠️ Bybit {market_type.value} failed: {str(result)}")
            elif result is not None:
                markets.append(result)
                logger.info(f"✅ Bybit {market_type.value}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
        
        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)
        
        # Categorize markets
        usdt_markets = [m for m in markets if m.market_type == MarketType.USDT]
        usdc_markets = [m for m in markets if m.market_type == MarketType.USDC]
        usd_markets = [m for m in markets if m.market_type == MarketType.USD]
        
        result = ExchangeOIResult(
            exchange="bybit",
            base_symbol=base_symbol,
            markets=markets,
            total_oi_tokens=total_oi_tokens,
            total_oi_usd=total_oi_usd,
            total_volume_24h=total_volume_24h,
            total_volume_24h_usd=total_volume_24h_usd,
            usdt_markets=usdt_markets,
            usdc_markets=usdc_markets,
            usd_markets=usd_markets,
            validation_passed=len(errors) == 0,
            validation_errors=errors
        )
        
        logger.info(f"🟣 Bybit total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_linear_market(self, base_symbol: str, market_type: MarketType) -> Optional[MarketOIData]:
        """Fetch linear market data (USDT/USDC)"""
        try:
            symbol = self.format_symbol(base_symbol, market_type)
            category = self.categories[market_type]
            session = await self.get_session()
            
            # Use ticker API which includes OI data (OI endpoint requires IntervalTime param)
            ticker_params = {"category": category, "symbol": symbol}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Extract ticker data (includes OI, price, volume, funding)
            if (ticker_response.get('retCode') != 0 or 
                not ticker_response.get('result', {}).get('list')):
                logger.warning(f"⚠️ Bybit {market_type.value} ticker data unavailable")
                return None
                
            ticker_data = ticker_response['result']['list'][0]
            
            # Extract all data from ticker API
            oi_tokens = float(ticker_data['openInterest'])
            price = float(ticker_data['lastPrice'])
            volume_24h = float(ticker_data['volume24h'])
            funding_rate = float(ticker_data.get('fundingRate', 0.0))
            
            # Calculate USD values (Linear: tokens × price)
            oi_usd = oi_tokens * price
            volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="bybit",
                symbol=symbol,
                base_symbol=base_symbol,
                market_type=market_type,
                oi_tokens=oi_tokens,
                oi_usd=oi_usd,
                price=price,
                funding_rate=funding_rate,
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h_usd,
                timestamp=datetime.now(),
                api_source=f"V5-Linear:{symbol}",
                calculation_method=f"linear: {oi_tokens:,.0f} × ${price:,.2f}",
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Bybit Linear {market_type.value} error: {str(e)}")
            return None
    
    async def _fetch_inverse_market(self, base_symbol: str, market_type: MarketType) -> Optional[MarketOIData]:
        """Fetch inverse market data (USD coin-margined)"""
        try:
            symbol = self.format_symbol(base_symbol, market_type)
            category = self.categories[market_type]
            session = await self.get_session()
            
            # Use ticker API which includes all needed data
            ticker_params = {"category": category, "symbol": symbol}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Extract ticker data
            if (ticker_response.get('retCode') != 0 or 
                not ticker_response.get('result', {}).get('list')):
                logger.warning(f"⚠️ Bybit {market_type.value} ticker data unavailable")
                return None
                
            ticker_data = ticker_response['result']['list'][0]
            price = float(ticker_data['lastPrice'])
            volume_24h = float(ticker_data['volume24h'])
            funding_rate = float(ticker_data.get('fundingRate', 0.0))
            
            # Bybit Inverse Contract Calculation
            # Ticker API provides both openInterest and openInterestValue
            oi_raw = ticker_data.get('openInterest', '0')
            oi_value = ticker_data.get('openInterestValue', '0')
            
            if float(oi_raw) > 0:
                # Use openInterest (contract units) - correct for Bybit inverse
                oi_contracts = float(oi_raw)
                # For Bybit inverse: contracts represent USD notional, convert to tokens
                oi_tokens = oi_contracts / price if price > 0 else 0
                oi_usd = oi_tokens * price  # Standard calculation
                calculation_method = f"inverse: {oi_contracts:,.0f} contracts ÷ ${price:,.2f}"
            elif float(oi_value) > 0:
                # Fallback: Use openInterestValue (already in token terms for inverse)
                oi_tokens = float(oi_value)
                oi_usd = oi_tokens * price
                calculation_method = f"inverse: oi_value {oi_tokens:,.0f} tokens × ${price:,.2f}"
            else:
                logger.warning(f"⚠️ Bybit {market_type.value} no valid OI data")
                return None
            
            # Volume calculation (similar approach)
            volume_24h_usd = volume_24h  # Volume already in USD for inverse
            volume_24h = volume_24h_usd / price if price > 0 else volume_24h
            
            return MarketOIData(
                exchange="bybit",
                symbol=symbol,
                base_symbol=base_symbol,
                market_type=market_type,
                oi_tokens=oi_tokens,
                oi_usd=oi_usd,
                price=price,
                funding_rate=funding_rate,
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h_usd,
                timestamp=datetime.now(),
                api_source=f"V5-Inverse:{symbol}",
                calculation_method=calculation_method,
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Bybit Inverse {market_type.value} error: {str(e)}")
            return None
    
    def _calculate_inverse_usd(self, oi_tokens: float, price: float) -> float:
        """Bybit-specific inverse calculation (handled in _fetch_inverse_market)"""
        return oi_tokens * price

# Testing function
async def test_bybit_provider():
    """Test Bybit provider implementation"""
    print("🚀 Testing Bybit OI Provider")
    
    provider = BybitOIProvider()
    
    try:
        # Test with BTC
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 BYBIT TEST RESULTS:")
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
    asyncio.run(test_bybit_provider())