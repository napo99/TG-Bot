#!/usr/bin/env python3
"""
BITGET OI PROVIDER - WORKING: Using Agent 2's proven direct API implementation
Based on the exact working code from crypto-assistant-perf that was verified
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

class BitgetOIProviderWorking(BaseExchangeOIProvider):
    """
    Bitget OI Provider using Agent 2's PROVEN working implementation
    Direct API calls to Bitget V1 Mix API with exact working endpoints
    """
    
    def __init__(self):
        super().__init__("bitget")
        
        # Bitget API configuration from Agent 2's working system
        self.bitget_oi_url = "https://api.bitget.com/api/mix/v1/market/open-interest"
        self.bitget_ticker_url = "https://api.bitget.com/api/mix/v1/market/ticker"
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Bitget supports USDT linear and USD inverse (no USDC)"""
        return [MarketType.USDT, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Bitget APIs using Agent 2's proven format"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}USDT_UMCBL"    # Linear USDT (U-margined)
        elif market_type == MarketType.USD:
            return f"{base}USD_DMCBL"     # Inverse USD (Coin-margined)
        else:
            raise ValueError(f"Unsupported market type: {market_type} (Bitget only supports USDT/USD)")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data using Agent 2's proven working method"""
        logger.info(f"🟡 Fetching Bitget OI for {base_symbol} (WORKING)")
        
        markets = []
        errors = []
        
        try:
            # Bitget symbol formats from Agent 2's working implementation
            bitget_symbols = {
                'USDT': f'{base_symbol.upper()}USDT_UMCBL',    # Linear USDT (U-margined)
                'USD': f'{base_symbol.upper()}USD_DMCBL'       # Inverse USD (Coin-margined)
            }
            
            session = await self.get_session()
            
            # Fetch both settlement types in parallel (Agent 2's proven approach)
            tasks = []
            for settlement, bitget_symbol in bitget_symbols.items():
                market_type = MarketType.USDT if settlement == 'USDT' else MarketType.USD
                tasks.append(self._fetch_bitget_settlement(session, base_symbol, bitget_symbol, settlement, market_type))
            
            settlement_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(settlement_results):
                settlement = ['USDT', 'USD'][i]
                if isinstance(result, MarketOIData):
                    markets.append(result)
                    logger.info(f"✅ Bitget {settlement}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
                elif isinstance(result, Exception):
                    error_msg = f"{settlement}: {str(result)}"
                    errors.append(error_msg)
                    logger.warning(f"⚠️ Bitget {settlement} failed: {str(result)}")
        
        except Exception as e:
            error_msg = f"General error: {str(e)}"
            errors.append(error_msg)
            logger.error(f"❌ Bitget general error: {str(e)}")
        
        # Calculate totals
        total_oi_tokens = sum(m.oi_tokens for m in markets)
        total_oi_usd = sum(m.oi_usd for m in markets)
        total_volume_24h = sum(m.volume_24h for m in markets)
        total_volume_24h_usd = sum(m.volume_24h_usd for m in markets)
        
        # Categorize markets (Bitget only has USDT and USD)
        usdt_markets = [m for m in markets if m.market_type == MarketType.USDT]
        usdc_markets = []  # Bitget doesn't offer USDC
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
            validation_passed=len(markets) > 0,
            validation_errors=errors
        )
        
        logger.info(f"🟡 Bitget total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_bitget_settlement(self, session: aiohttp.ClientSession, base_symbol: str, bitget_symbol: str, settlement: str, market_type: MarketType) -> Optional[MarketOIData]:
        """Fetch Bitget OI data for a specific settlement currency - Agent 2's WORKING implementation"""
        try:
            # Step 1: Get Open Interest data (Agent 2's exact approach)
            params = {'symbol': bitget_symbol}
            
            async with session.get(self.bitget_oi_url, params=params) as response:
                if response.status != 200:
                    logger.debug(f"Bitget OI API HTTP {response.status} for {bitget_symbol}")
                    return None
                
                oi_response = await response.json()
                
                if oi_response.get('code') != '00000':
                    logger.debug(f"Bitget OI API error for {bitget_symbol}: {oi_response.get('msg')}")
                    return None
                
                oi_data = oi_response.get('data')
                if not oi_data:
                    logger.debug(f"Bitget OI no data for {bitget_symbol}")
                    return None
                
                # Extract OI data (CORRECTED field usage based on actual API)
                open_interest = float(oi_data.get('amount', 0))  # API returns 'amount' not 'openInterest'
                open_interest_usd = 0  # Calculate from amount × price
            
            # Step 2: Get additional market data from ticker endpoint (Agent 2's approach)
            ticker_params = {'symbol': bitget_symbol}
            
            async with session.get(self.bitget_ticker_url, params=ticker_params) as ticker_response:
                if ticker_response.status != 200:
                    logger.debug(f"Bitget ticker API HTTP {ticker_response.status} for {bitget_symbol}")
                    return None
                
                ticker_data_response = await ticker_response.json()
                if ticker_data_response.get('code') != '00000':
                    logger.debug(f"Bitget ticker API error for {bitget_symbol}: {ticker_data_response.get('msg')}")
                    return None
                
                ticker = ticker_data_response.get('data')
                if not ticker:
                    logger.debug(f"Bitget ticker no data for {bitget_symbol}")
                    return None
                
                price = float(ticker.get('last', 0))
                volume_24h_usd = float(ticker.get('usdtVol', 0))
                funding_rate = float(ticker.get('fundingRate', 0))
            
            # Step 3: Calculate token amounts (CORRECTED calculation)
            if settlement == 'USD':  # Inverse contracts
                # For inverse contracts, amount is in contracts, convert to BTC
                oi_tokens = open_interest  # Contract amount in BTC
                oi_usd = oi_tokens * price
                volume_24h = volume_24h_usd / price if price > 0 else 0
                calculation_method = f"inverse: {oi_tokens:,.0f} BTC contracts × ${price:,.2f}"
            else:  # Linear USDT
                # For linear contracts, amount is in token units (BTC)
                oi_tokens = open_interest  # Already in BTC
                oi_usd = oi_tokens * price
                volume_24h = volume_24h_usd / price if price > 0 else 0
                calculation_method = f"linear: {oi_tokens:,.0f} BTC × ${price:,.2f}"
            
            if oi_tokens <= 0 or price <= 0:
                logger.debug(f"Bitget {bitget_symbol}: Invalid OI ({oi_tokens}) or price ({price})")
                return None
            
            logger.info(f"Bitget {bitget_symbol} ({settlement}): {oi_tokens:,.2f} tokens, ${oi_usd:,.2f} USD")
            
            return MarketOIData(
                exchange="bitget",
                symbol=bitget_symbol,
                base_symbol=base_symbol,
                market_type=market_type,
                oi_tokens=oi_tokens,
                oi_usd=oi_usd,
                price=price,
                funding_rate=funding_rate,
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h_usd,
                timestamp=datetime.now(),
                api_source=f"V1-Mix-{settlement}:{bitget_symbol}",
                calculation_method=calculation_method,
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
                
        except Exception as e:
            logger.warning(f"Error fetching Bitget {settlement} for {base_symbol}: {e}")
            return None

# Testing function
async def test_bitget_working():
    """Test the working Bitget provider"""
    print("🚀 Testing WORKING Bitget OI Provider")
    
    provider = BitgetOIProviderWorking()
    
    try:
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 BITGET WORKING RESULTS:")
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
    asyncio.run(test_bitget_working())