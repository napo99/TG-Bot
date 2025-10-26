#!/usr/bin/env python3
"""
OKX OI PROVIDER: Complete implementation for all 3 market types
Implements SWAP contracts with USDT/USDC linear and USD inverse
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger

from .base import (
    BaseExchangeOIProvider,
    MarketOIData,
    ExchangeOIResult,
    MarketType
)

class OKXOIProvider(BaseExchangeOIProvider):
    """
    OKX OI Provider supporting all market types:
    - USDT Linear: BTC-USDT-SWAP
    - USDC Linear: BTC-USDC-SWAP  
    - USD Inverse: BTC-USD-SWAP (coin-margined)
    """
    
    def __init__(self):
        super().__init__("okx")
        self.api_base = "https://www.okx.com"
        
        # OKX V5 API endpoints
        self.endpoints = {
            'oi': f"{self.api_base}/api/v5/public/open-interest",
            'ticker': f"{self.api_base}/api/v5/market/ticker",
            'funding': f"{self.api_base}/api/v5/public/funding-rate"
        }
        
        # OKX instrument types
        self.inst_types = {
            MarketType.USDT: "SWAP",     # Linear USDT
            MarketType.USDC: "SWAP",     # Linear USDC
            MarketType.USD: "SWAP"       # Inverse USD
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """OKX supports all 3 market types"""
        return [MarketType.USDT, MarketType.USDC, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for OKX APIs"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}-USDT-SWAP"
        elif market_type == MarketType.USDC:
            return f"{base}-USDC-SWAP"
        elif market_type == MarketType.USD:
            return f"{base}-USD-SWAP"  # Inverse contracts
        else:
            raise ValueError(f"Unsupported market type: {market_type}")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for all OKX market types"""
        logger.info(f"🟠 Fetching OKX OI for {base_symbol}")
        
        markets = []
        errors = []
        
        # Fetch all market types in parallel
        market_tasks = [
            self._fetch_swap_market(base_symbol, MarketType.USDT),
            self._fetch_swap_market(base_symbol, MarketType.USDC),
            self._fetch_swap_market(base_symbol, MarketType.USD)
        ]
        
        market_results = await asyncio.gather(*market_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(market_results):
            market_type = [MarketType.USDT, MarketType.USDC, MarketType.USD][i]
            
            if isinstance(result, Exception):
                error_msg = f"{market_type.value}: {str(result)}"
                errors.append(error_msg)
                logger.warning(f"⚠️ OKX {market_type.value} failed: {str(result)}")
            elif result is not None:
                markets.append(result)
                logger.info(f"✅ OKX {market_type.value}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
        
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
            exchange="okx",
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
        
        logger.info(f"🟠 OKX total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_swap_market(self, base_symbol: str, market_type: MarketType) -> Optional[MarketOIData]:
        """Fetch SWAP market data (USDT/USDC/USD)"""
        try:
            symbol = self.format_symbol(base_symbol, market_type)
            inst_type = self.inst_types[market_type]
            session = await self.get_session()
            
            # Fetch OI data
            oi_params = {"instType": inst_type, "instId": symbol}
            async with session.get(self.endpoints['oi'], params=oi_params) as response:
                oi_response = await response.json()
                
            # Fetch ticker data
            ticker_params = {"instId": symbol}
            async with session.get(self.endpoints['ticker'], params=ticker_params) as response:
                ticker_response = await response.json()
            
            # Fetch funding data
            funding_params = {"instId": symbol}
            async with session.get(self.endpoints['funding'], params=funding_params) as response:
                funding_response = await response.json()
            
            # Extract OI data
            if (oi_response.get('code') != '0' or 
                not oi_response.get('data')):
                logger.warning(f"⚠️ OKX {market_type.value} OI data unavailable")
                return None
                
            oi_data = oi_response['data'][0]
            
            # Extract ticker data
            if (ticker_response.get('code') != '0' or 
                not ticker_response.get('data')):
                logger.warning(f"⚠️ OKX {market_type.value} ticker data unavailable")
                return None
                
            ticker_data = ticker_response['data'][0]
            price = float(ticker_data['last'])
            # CRITICAL FIX: Use volCcy24h for base currency volume (BTC), not vol24h (contracts)
            volume_24h_base = float(ticker_data.get('volCcy24h', 0))  # Volume in base currency (BTC)
            volume_24h_contracts = float(ticker_data.get('vol24h', 0))  # Volume in contracts
            
            # Extract funding data
            funding_rate = 0.0  # Default if not available
            if (funding_response.get('code') == '0' and 
                funding_response.get('data')):
                funding_data = funding_response['data'][0]
                funding_rate = float(funding_data['fundingRate'])
            
            # OKX OI Calculation
            # CRITICAL FIX: Use oiCcy (base currency) not oi (quote currency)
            if market_type in [MarketType.USDT, MarketType.USDC]:
                # Linear markets: Use oiCcy for base currency amount (BTC)
                oi_tokens = float(oi_data['oiCcy'])  # Open interest in base currency (BTC)
                # VOLUME FIX: Use volCcy24h for base currency volume (BTC)
                volume_24h = volume_24h_base  # Volume in base currency (BTC)
                
                # Calculate USD values
                oi_usd = oi_tokens * price
                volume_24h_usd = volume_24h * price
                calculation_method = f"linear: {oi_tokens:,.0f} × ${price:,.2f} (oiCcy), vol: {volume_24h:,.0f} BTC"
                
            else:  # MarketType.USD (inverse)
                # Inverse markets: oi in contracts, oiCcy in base currency
                oi_ccy = oi_data.get('oiCcy', '0')  # OI in base currency (BTC)
                oi_contracts = oi_data.get('oi', '0')  # OI in contracts
                
                if float(oi_ccy) > 0:
                    # Use oiCcy (already in BTC terms)
                    oi_tokens = float(oi_ccy)
                    oi_usd = oi_tokens * price
                    calculation_method = f"inverse: oiCcy {oi_tokens:,.0f} × ${price:,.2f}"
                elif float(oi_contracts) > 0:
                    # Convert contracts to tokens
                    # OKX inverse: 1 contract = $100 USD worth
                    oi_contracts_num = float(oi_contracts)
                    contract_value_usd = 100.0  # $100 per contract
                    oi_usd_from_contracts = oi_contracts_num * contract_value_usd
                    oi_tokens = oi_usd_from_contracts / price
                    oi_usd = oi_tokens * price
                    calculation_method = f"inverse: {oi_contracts_num:,.0f} contracts × $100 ÷ ${price:,.2f}"
                else:
                    logger.warning(f"⚠️ OKX {market_type.value} no valid OI data")
                    return None
                
                # Volume calculation for inverse - FIXED: Use volCcy24h for BTC volume
                volume_24h = volume_24h_base  # Volume in base currency (BTC) from volCcy24h
                volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="okx",
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
                api_source=f"V5-SWAP:{symbol}",
                calculation_method=calculation_method,
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ OKX SWAP {market_type.value} error: {str(e)}")
            return None
    
    def _calculate_inverse_usd(self, oi_tokens: float, price: float) -> float:
        """OKX-specific inverse calculation (handled in _fetch_swap_market)"""
        return oi_tokens * price

# Testing function
async def test_okx_provider():
    """Test OKX provider implementation"""
    print("🚀 Testing OKX OI Provider")
    
    provider = OKXOIProvider()
    
    try:
        # Test with BTC
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 OKX TEST RESULTS:")
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
    asyncio.run(test_okx_provider())