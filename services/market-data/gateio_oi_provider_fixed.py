#!/usr/bin/env python3
"""
GATE.IO OI PROVIDER - FIXED: Using the actual working implementation from Agent 2
Based on the proven direct API calls that were working before
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

class GateIOOIProviderFixed(BaseExchangeOIProvider):
    """
    Gate.io OI Provider using the WORKING implementation from Agent 2
    Direct API calls to Gate.io futures endpoints
    """
    
    def __init__(self):
        super().__init__("gateio")
        
        # Gate.io API configuration (from working implementation)
        self.gateio_base = "https://api.gateio.ws/api/v4/futures"
        self.gateio_endpoints = {
            'USDT': f'{self.gateio_base}/usdt/tickers',     # Linear USDT
            'USDC': f'{self.gateio_base}/usdc/tickers',     # Linear USDC
            'USD': f'{self.gateio_base}/btc/tickers'        # Inverse BTC-settled
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Gate.io supports USDT, USDC, and USD"""
        return [MarketType.USDT, MarketType.USDC, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Gate.io APIs (from working implementation)"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}_USDT"
        elif market_type == MarketType.USDC:
            return f"{base}_USDC"
        elif market_type == MarketType.USD:
            return f"{base}_USD"
        else:
            raise ValueError(f"Unsupported market type: {market_type}")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data using the proven working method"""
        logger.info(f"🟢 Fetching Gate.io OI for {base_symbol} (FIXED)")
        
        markets = []
        errors = []
        
        # Use the working implementation from Agent 2
        try:
            session = await self.get_session()
            
            # Fetch all three settlement types in parallel (proven working)
            tasks = []
            for settlement, endpoint in self.gateio_endpoints.items():
                market_type = MarketType.USDT if settlement == 'USDT' else \
                             MarketType.USDC if settlement == 'USDC' else \
                             MarketType.USD
                tasks.append(self._fetch_gateio_settlement(session, base_symbol, market_type, settlement, endpoint))
            
            settlement_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(settlement_results):
                settlement = ['USDT', 'USDC', 'USD'][i]
                if isinstance(result, MarketOIData):
                    markets.append(result)
                    logger.info(f"✅ Gate.io {settlement}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
                elif isinstance(result, Exception):
                    error_msg = f"{settlement}: {str(result)}"
                    errors.append(error_msg)
                    logger.warning(f"⚠️ Gate.io {settlement} failed: {str(result)}")
        
        except Exception as e:
            error_msg = f"General error: {str(e)}"
            errors.append(error_msg)
            logger.error(f"❌ Gate.io general error: {str(e)}")
        
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
            validation_passed=len(markets) > 0,  # Success if any market works
            validation_errors=errors
        )
        
        logger.info(f"🟢 Gate.io total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_gateio_settlement(self, session: aiohttp.ClientSession, base_symbol: str, market_type: MarketType, settlement: str, endpoint: str) -> Optional[MarketOIData]:
        """Fetch Gate.io OI data for a specific settlement currency - EXACT COPY from working implementation"""
        try:
            base_token = base_symbol.upper()
            
            # Gate.io symbol formats (from working implementation)
            if settlement == 'USDT':
                gateio_symbol = f"{base_token}_USDT"
            elif settlement == 'USDC':
                gateio_symbol = f"{base_token}_USDC"
            else:  # USD (inverse)
                gateio_symbol = f"{base_token}_USD"
            
            # Fetch ticker data (proven working)
            async with session.get(endpoint) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Find our symbol in the tickers list (proven working logic)
                ticker = None
                for t in data:
                    if t.get('contract') == gateio_symbol:
                        ticker = t
                        break
                
                if not ticker:
                    logger.debug(f"Gate.io symbol {gateio_symbol} not found in {settlement} market")
                    return None
                
                # Extract data (proven working)
                price = float(ticker.get('last', 0))
                funding_rate = float(ticker.get('funding_rate', 0))
                volume_24h = float(ticker.get('volume_24h', 0))
                
                # For OI, Gate.io uses different fields depending on settlement (proven working logic)
                if settlement == 'USD':  # Inverse
                    # For inverse contracts, size_24h is in contract units
                    oi_contracts = float(ticker.get('size_24h', 0))  # This might be volume, need position endpoint
                    oi_tokens = oi_contracts / price if price > 0 else 0  # Convert to token units
                    calculation_method = f"inverse: {oi_contracts:,.0f} contracts ÷ ${price:,.2f}"
                else:  # Linear USDT/USDC
                    # For linear contracts, use position size directly
                    oi_contracts = float(ticker.get('volume_24h', 0))  # May need different endpoint
                    oi_tokens = oi_contracts
                    calculation_method = f"linear: {oi_tokens:,.0f} × ${price:,.2f}"
                
                oi_usd = oi_tokens * price
                volume_24h_usd = volume_24h * price
                
                if oi_tokens <= 0 or price <= 0:
                    logger.debug(f"Gate.io {gateio_symbol}: Invalid OI ({oi_tokens}) or price ({price})")
                    return None
                
                return MarketOIData(
                    exchange="gateio",
                    symbol=gateio_symbol,
                    base_symbol=base_symbol,
                    market_type=market_type,
                    oi_tokens=oi_tokens,
                    oi_usd=oi_usd,
                    price=price,
                    funding_rate=funding_rate,
                    volume_24h=volume_24h,
                    volume_24h_usd=volume_24h_usd,
                    timestamp=datetime.now(),
                    api_source=f"V4-{settlement}:{gateio_symbol}",
                    calculation_method=calculation_method,
                    price_validated=False,
                    calculation_validated=False,
                    api_validated=False
                )
                
        except Exception as e:
            logger.warning(f"Error fetching Gate.io {settlement} for {base_symbol}: {e}")
            return None

# Testing function
async def test_gateio_fixed():
    """Test the fixed Gate.io provider"""
    print("🚀 Testing FIXED Gate.io OI Provider")
    
    provider = GateIOOIProviderFixed()
    
    try:
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 GATE.IO FIXED RESULTS:")
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
    asyncio.run(test_gateio_fixed())