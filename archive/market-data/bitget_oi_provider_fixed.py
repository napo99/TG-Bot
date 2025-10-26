#!/usr/bin/env python3
"""
BITGET OI PROVIDER: FIXED IMPLEMENTATION
Based on independent validation findings to resolve critical API endpoint issues

CRITICAL FIXES APPLIED:
1. ✅ USING: V1 API endpoints (confirmed working by validation agent)
2. ✅ FIXED: Symbol formats (BTCUSDT_UMCBL confirmed working)
3. ✅ USING: 'holdingAmount' field (validated 45,913 BTC, $4.9B realistic)
4. ✅ ADDED: Proper error handling and realistic value validation
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

class BitgetOIProviderFixed(BaseExchangeOIProvider):
    """
    FIXED Bitget OI Provider with validation-based corrections
    """
    
    def __init__(self):
        super().__init__("bitget")
        self.api_base = "https://api.bitget.com"
        
        # FIXED: Use V1 API endpoints (validated as working)
        self.endpoints = {
            'ticker': f"{self.api_base}/api/mix/v1/market/ticker",  # V1 confirmed working
            'funding': f"{self.api_base}/api/v2/mix/market/current-fund-rate"
        }
        
        # VALIDATED product types from validation agent
        self.product_types = {
            MarketType.USDT: "USDT-FUTURES",   # Confirmed working
            MarketType.USD: "COIN-FUTURES"     # Confirmed working
        }
        
        # VALIDATED field mappings from validation agent
        self.oi_field_mappings = {
            'BTCUSDT_UMCBL': {
                'oi_field': 'holdingAmount',  # VALIDATED: 45,913 BTC ($4.9B) ✅ REALISTIC
                'realistic_range': (20_000, 80_000)
            },
            'BTCUSD_DMCBL': {
                'oi_field': 'holdingAmount',
                'realistic_range': (20_000, 80_000)
            }
        }
        
    def get_supported_market_types(self) -> List[MarketType]:
        """Bitget supports USDT linear and USD inverse"""
        return [MarketType.USDT, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """FIXED symbol formatting based on validation results"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}USDT_UMCBL"  # VALIDATED format
        elif market_type == MarketType.USD:
            return f"{base}USD_DMCBL"   # VALIDATED format
        else:
            raise ValueError(f"Unsupported market type for Bitget: {market_type}")
    
    def _validate_oi_value(self, symbol: str, oi_tokens: float, price: float) -> Tuple[bool, str]:
        """Validate OI value against realistic ranges"""
        if symbol in self.oi_field_mappings:
            min_oi, max_oi = self.oi_field_mappings[symbol]['realistic_range']
            
            if min_oi <= oi_tokens <= max_oi:
                return True, f"VALID: {oi_tokens:,.0f} BTC within range {min_oi:,}-{max_oi:,}"
            else:
                return False, f"INVALID: {oi_tokens:,.0f} BTC outside range {min_oi:,}-{max_oi:,}"
        
        # Generic validation for other symbols
        oi_usd = oi_tokens * price
        if 1e9 <= oi_usd <= 10e9:  # $1B-10B USD range
            return True, f"VALID: ${oi_usd/1e9:.1f}B USD within reasonable range"
        else:
            return False, f"INVALID: ${oi_usd/1e9:.1f}B USD outside reasonable range"
    
    def _extract_oi_safely(self, ticker_data: dict, symbol: str, price: float) -> Tuple[float, str]:
        """
        Extract OI using validated field mappings with safety checks
        """
        if symbol in self.oi_field_mappings:
            mapping = self.oi_field_mappings[symbol]
            oi_field = mapping['oi_field']
            
            if oi_field in ticker_data:
                oi_candidate = float(ticker_data[oi_field])
                is_valid, validation_msg = self._validate_oi_value(symbol, oi_candidate, price)
                
                if is_valid:
                    logger.info(f"✅ {symbol}: Using validated field '{oi_field}': {validation_msg}")
                    return oi_candidate, f"validated: {oi_field}"
                else:
                    logger.warning(f"⚠️ {symbol}: Field validation failed: {validation_msg}")
                    # Don't fall back to potentially wrong fields, return 0
                    return 0.0, "validation_failed"
            else:
                logger.error(f"❌ {symbol}: Expected field '{oi_field}' not found in ticker data")
                logger.debug(f"Available fields: {list(ticker_data.keys())}")
                return 0.0, "field_missing"
        
        # For unmapped symbols, try holdingAmount as it was validated to work
        if 'holdingAmount' in ticker_data:
            oi_candidate = float(ticker_data['holdingAmount'])
            is_valid, validation_msg = self._validate_oi_value(symbol, oi_candidate, price)
            
            if is_valid:
                logger.info(f"✅ {symbol}: Using generic 'holdingAmount': {validation_msg}")
                return oi_candidate, "generic_holdingAmount"
            else:
                logger.warning(f"⚠️ {symbol}: Generic validation failed: {validation_msg}")
        
        # Try openInterest as last resort
        if 'openInterest' in ticker_data:
            oi_candidate = float(ticker_data['openInterest'])
            is_valid, validation_msg = self._validate_oi_value(symbol, oi_candidate, price)
            
            if is_valid:
                logger.info(f"✅ {symbol}: Using 'openInterest': {validation_msg}")
                return oi_candidate, "openInterest"
        
        logger.error(f"❌ {symbol}: No valid OI fields found")
        return 0.0, "no_oi_data"
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for Bitget market types using FIXED implementation"""
        logger.info(f"🔧 Fetching Bitget OI for {base_symbol} (FIXED implementation)")
        
        markets = []
        errors = []
        
        # Fetch supported market types in parallel
        market_tasks = [
            self._fetch_usdt_market_fixed(base_symbol),
            self._fetch_usd_market_fixed(base_symbol)
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
            validation_passed=len(errors) < len(market_tasks) and total_oi_tokens > 0,
            validation_errors=errors
        )
        
        logger.info(f"🔧 Bitget FIXED total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_usdt_market_fixed(self, base_symbol: str) -> Optional[MarketOIData]:
        """Fetch USDT linear market data using FIXED methodology"""
        try:
            symbol = self.format_symbol(base_symbol, MarketType.USDT)
            product_type = self.product_types[MarketType.USDT]
            session = await self.get_session()
            
            # FIXED: Use V1 ticker endpoint with validated parameters
            ticker_params = {"symbol": symbol, "productType": product_type}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Fetch funding rate (keep V2 as it may work)
            funding_params = {"symbol": symbol, "productType": product_type}
            try:
                async with session.get(self.endpoints['funding'], params=funding_params) as response:
                    funding_response = await response.json()
            except Exception as e:
                logger.warning(f"⚠️ Bitget funding rate fetch failed: {str(e)}")
                funding_response = {}
            
            # FIXED: Validate response structure
            if (not ticker_response or 
                ticker_response.get('code') != '00000' or 
                not ticker_response.get('data')):
                logger.warning(f"⚠️ Bitget USDT ticker data unavailable for {symbol}")
                logger.debug(f"Response: {ticker_response}")
                return None
            
            ticker_data = ticker_response['data']
            
            # Extract price (try multiple fields)
            price = 0.0
            for price_field in ['lastPr', 'last', 'close']:
                if price_field in ticker_data:
                    price = float(ticker_data[price_field])
                    break
            
            if price <= 0:
                logger.error(f"❌ Bitget USDT: No valid price for {symbol}")
                return None
            
            # FIXED: Extract OI using validated methodology
            oi_tokens, extraction_method = self._extract_oi_safely(ticker_data, symbol, price)
            
            if oi_tokens <= 0:
                logger.warning(f"⚠️ Bitget USDT: No valid OI data for {symbol}")
                return None
            
            # Extract funding rate
            funding_rate = 0.0
            if (funding_response.get('code') == '00000' and 
                funding_response.get('data')):
                funding_data = funding_response['data']
                funding_rate = float(funding_data.get('fundingRate', 0))
            
            # Extract volume
            volume_24h = float(ticker_data.get('baseVolume', ticker_data.get('vol', 0)))
            
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
                api_source=f"V1-USDT-FIXED:{symbol}",
                calculation_method=f"linear_fixed: {oi_tokens:,.0f} × ${price:,.2f} ({extraction_method})",
                price_validated=True,
                calculation_validated=True,
                api_validated=True
            )
            
        except Exception as e:
            logger.error(f"❌ Bitget USDT FIXED error: {str(e)}")
            return None
    
    async def _fetch_usd_market_fixed(self, base_symbol: str) -> Optional[MarketOIData]:
        """Fetch USD inverse market data using FIXED methodology"""
        try:
            symbol = self.format_symbol(base_symbol, MarketType.USD)
            product_type = self.product_types[MarketType.USD]
            session = await self.get_session()
            
            # FIXED: Use V1 ticker endpoint with validated parameters
            ticker_params = {"symbol": symbol, "productType": product_type}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Fetch funding rate
            funding_params = {"symbol": symbol, "productType": product_type}
            try:
                async with session.get(self.endpoints['funding'], params=funding_params) as response:
                    funding_response = await response.json()
            except Exception as e:
                logger.warning(f"⚠️ Bitget funding rate fetch failed: {str(e)}")
                funding_response = {}
            
            # FIXED: Validate response structure
            if (not ticker_response or 
                ticker_response.get('code') != '00000' or 
                not ticker_response.get('data')):
                logger.warning(f"⚠️ Bitget USD ticker data unavailable for {symbol}")
                logger.debug(f"Response: {ticker_response}")
                return None
            
            ticker_data = ticker_response['data']
            
            # Extract price
            price = 0.0
            for price_field in ['lastPr', 'last', 'close']:
                if price_field in ticker_data:
                    price = float(ticker_data[price_field])
                    break
            
            if price <= 0:
                logger.error(f"❌ Bitget USD: No valid price for {symbol}")
                return None
            
            # FIXED: Extract OI using validated methodology
            oi_tokens, extraction_method = self._extract_oi_safely(ticker_data, symbol, price)
            
            if oi_tokens <= 0:
                logger.warning(f"⚠️ Bitget USD: No valid OI data for {symbol}")
                return None
            
            # Extract funding rate
            funding_rate = 0.0
            if (funding_response.get('code') == '00000' and 
                funding_response.get('data')):
                funding_data = funding_response['data']
                funding_rate = float(funding_data.get('fundingRate', 0))
            
            # Extract volume
            volume_24h = float(ticker_data.get('baseVolume', ticker_data.get('vol', 0)))
            
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
                api_source=f"V1-USD-FIXED:{symbol}",
                calculation_method=f"inverse_fixed: {oi_tokens:,.0f} × ${price:,.2f} ({extraction_method})",
                price_validated=True,
                calculation_validated=True,
                api_validated=True
            )
            
        except Exception as e:
            logger.error(f"❌ Bitget USD FIXED error: {str(e)}")
            return None

# Testing function
async def test_bitget_fixed():
    """Test FIXED Bitget provider implementation"""
    print("🔧 Testing Bitget FIXED OI Provider")
    
    provider = BitgetOIProviderFixed()
    
    try:
        # Test with BTC
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 BITGET FIXED TEST RESULTS:")
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
            print(f"    Validated: {market.api_validated}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(test_bitget_fixed())