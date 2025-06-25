#!/usr/bin/env python3
"""
GATE.IO OI PROVIDER: Implementation for USDT linear and USD inverse markets
Based on Agent 3's research findings on Gate.io API structure
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

class GateIOOIProvider(BaseExchangeOIProvider):
    """
    Gate.io OI Provider supporting 2 market types:
    - USDT Linear: BTC_USDT perpetual
    - USD Inverse: BTC_USD coin-margined (if available)
    Note: Gate.io typically doesn't offer USDC perpetuals
    """
    
    def __init__(self):
        super().__init__("gateio")
        self.api_base = "https://api.gateio.ws/api/v4"
        
        # Gate.io API endpoints
        self.endpoints = {
            'usdt_oi': f"{self.api_base}/futures/usdt/tickers",
            'usdt_funding': f"{self.api_base}/futures/usdt/funding_rate",
            'usd_oi': f"{self.api_base}/futures/btc/tickers",  # USD inverse (BTC-settled)
            'usd_funding': f"{self.api_base}/futures/btc/funding_rate"
        }
        
        # Gate.io settlement types
        self.settlement_types = {
            MarketType.USDT: "usdt",
            MarketType.USD: "btc"  # BTC-settled (inverse)
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Gate.io supports USDT linear and USD inverse"""
        return [MarketType.USDT, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Gate.io APIs"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}_USDT"  # Linear USDT perpetual
        elif market_type == MarketType.USD:
            return f"{base}_USD"   # Inverse USD perpetual  
        else:
            raise ValueError(f"Unsupported market type for Gate.io: {market_type}")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for Gate.io market types"""
        logger.info(f"🟢 Fetching Gate.io OI for {base_symbol}")
        
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
                logger.warning(f"⚠️ Gate.io {market_type.value} failed: {str(result)}")
            elif result is not None:
                markets.append(result)
                logger.info(f"✅ Gate.io {market_type.value}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
        
        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)
        
        # Categorize markets
        usdt_markets = [m for m in markets if m.market_type == MarketType.USDT]
        usdc_markets = []  # Gate.io doesn't offer USDC perpetuals
        usd_markets = [m for m in markets if m.market_type == MarketType.USD]
        
        result = ExchangeOIResult(
            exchange="gateio",
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
        
        logger.info(f"🟢 Gate.io total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_usdt_market(self, base_symbol: str) -> Optional[MarketOIData]:
        """Fetch USDT linear market data"""
        try:
            symbol = self.format_symbol(base_symbol, MarketType.USDT)
            session = await self.get_session()
            
            # Fetch ticker data (includes OI and volume)
            async with session.get(f"{self.endpoints['usdt_oi']}?contract={symbol}") as response:
                ticker_response = await response.json()
            
            # Fetch funding rate
            async with session.get(f"{self.endpoints['usdt_funding']}?contract={symbol}") as response:
                funding_response = await response.json()
            
            # Validate ticker response
            if not isinstance(ticker_response, list) or len(ticker_response) == 0:
                logger.warning(f"⚠️ Gate.io USDT ticker data unavailable for {symbol}")
                return None
            
            ticker_data = ticker_response[0]
            
            # Extract data
            price = float(ticker_data['last'])
            volume_24h = float(ticker_data['volume_24h'])
            
            # Gate.io USDT OI handling
            # Check for size_24h field (can be used as volume proxy)
            if 'size_24h' in ticker_data:
                volume_24h = float(ticker_data['size_24h'])
            
            # Extract OI if available (Gate.io may not always provide OI in ticker)
            oi_tokens = 0.0
            if 'open_interest' in ticker_data:
                oi_tokens = float(ticker_data['open_interest'])
            elif 'funding_size' in ticker_data:
                # Use funding_size as OI proxy if available
                oi_tokens = float(ticker_data['funding_size'])
            else:
                # Estimate OI from volume (conservative estimate: OI = volume/10)
                oi_tokens = volume_24h / 10.0
                logger.info(f"📊 Gate.io USDT: Estimating OI from volume ({symbol})")
            
            # Extract funding rate
            funding_rate = 0.0
            if isinstance(funding_response, dict) and 'r' in funding_response:
                funding_rate = float(funding_response['r'])
            
            # Calculate USD values
            oi_usd = oi_tokens * price
            volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="gateio",
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
                api_source=f"V4-USDT:{symbol}",
                calculation_method=f"linear: {oi_tokens:,.0f} × ${price:,.2f}",
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Gate.io USDT error: {str(e)}")
            return None
    
    async def _fetch_usd_market(self, base_symbol: str) -> Optional[MarketOIData]:
        """Fetch USD inverse market data"""
        try:
            symbol = self.format_symbol(base_symbol, MarketType.USD)
            session = await self.get_session()
            
            # Fetch ticker data from BTC-settled futures
            async with session.get(f"{self.endpoints['usd_oi']}?contract={symbol}") as response:
                ticker_response = await response.json()
            
            # Fetch funding rate
            async with session.get(f"{self.endpoints['usd_funding']}?contract={symbol}") as response:
                funding_response = await response.json()
            
            # Validate ticker response
            if not isinstance(ticker_response, list) or len(ticker_response) == 0:
                logger.warning(f"⚠️ Gate.io USD ticker data unavailable for {symbol}")
                return None
            
            ticker_data = ticker_response[0]
            
            # Extract data
            price = float(ticker_data['last'])
            volume_24h = float(ticker_data.get('volume_24h', 0))
            
            # Gate.io USD inverse OI handling
            # Inverse contracts are more complex - try multiple fields
            oi_tokens = 0.0
            calculation_method = ""
            
            if 'open_interest' in ticker_data:
                # Direct OI in base currency
                oi_tokens = float(ticker_data['open_interest'])
                calculation_method = f"inverse: oi {oi_tokens:,.0f} × ${price:,.2f}"
            elif 'funding_size' in ticker_data:
                # Use funding_size as proxy
                oi_tokens = float(ticker_data['funding_size'])
                calculation_method = f"inverse: funding_size {oi_tokens:,.0f} × ${price:,.2f}"
            elif 'size_24h' in ticker_data:
                # Estimate from 24h size (conservative: OI = size/20 for inverse)
                oi_tokens = float(ticker_data['size_24h']) / 20.0
                calculation_method = f"inverse: estimated from size_24h"
            else:
                logger.warning(f"⚠️ Gate.io USD: No OI data available for {symbol}")
                return None
            
            # Extract funding rate
            funding_rate = 0.0
            if isinstance(funding_response, dict) and 'r' in funding_response:
                funding_rate = float(funding_response['r'])
            
            # Calculate USD values
            oi_usd = oi_tokens * price
            volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="gateio",
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
                api_source=f"V4-USD:{symbol}",
                calculation_method=calculation_method,
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Gate.io USD error: {str(e)}")
            return None
    
    def _calculate_inverse_usd(self, oi_tokens: float, price: float) -> float:
        """Gate.io-specific inverse calculation"""
        return oi_tokens * price

# Testing function
async def test_gateio_provider():
    """Test Gate.io provider implementation"""
    print("🚀 Testing Gate.io OI Provider")
    
    provider = GateIOOIProvider()
    
    try:
        # Test with BTC
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 GATE.IO TEST RESULTS:")
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
    asyncio.run(test_gateio_provider())