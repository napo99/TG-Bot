#!/usr/bin/env python3
"""
BINANCE OI PROVIDER: Complete implementation for all 3 market types
Implements FAPI (USDT/USDC linear) and DAPI (USD inverse) with proper calculations
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

class BinanceOIProvider(BaseExchangeOIProvider):
    """
    Binance OI Provider supporting all market types:
    - USDT Linear (FAPI): BTCUSDT 
    - USDC Linear (FAPI): BTCUSDC
    - USD Inverse (DAPI): BTCUSD_PERP ($100 contracts)
    """
    
    def __init__(self):
        super().__init__("binance")
        self.fapi_base = "https://fapi.binance.com"  # Linear contracts (USDT/USDC)
        self.dapi_base = "https://dapi.binance.com"  # Inverse contracts (USD)
        
        # API endpoints
        self.endpoints = {
            'fapi_oi': f"{self.fapi_base}/fapi/v1/openInterest",
            'fapi_ticker': f"{self.fapi_base}/fapi/v1/ticker/24hr",
            'fapi_funding': f"{self.fapi_base}/fapi/v1/premiumIndex",
            'dapi_oi': f"{self.dapi_base}/dapi/v1/openInterest", 
            'dapi_ticker': f"{self.dapi_base}/dapi/v1/ticker/24hr",
            'dapi_funding': f"{self.dapi_base}/dapi/v1/premiumIndex"
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Binance supports all 3 market types"""
        return [MarketType.USDT, MarketType.USDC, MarketType.USD]
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for Binance APIs"""
        base = base_symbol.upper()
        
        if market_type == MarketType.USDT:
            return f"{base}USDT"
        elif market_type == MarketType.USDC:
            return f"{base}USDC"
        elif market_type == MarketType.USD:
            return f"{base}USD_PERP"  # DAPI format
        else:
            raise ValueError(f"Unsupported market type: {market_type}")
    
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for all Binance market types"""
        logger.info(f"🟡 Fetching Binance OI for {base_symbol}")
        
        markets = []
        errors = []
        
        # Fetch all market types in parallel
        market_tasks = [
            self._fetch_fapi_market(base_symbol, MarketType.USDT),
            self._fetch_fapi_market(base_symbol, MarketType.USDC),
            self._fetch_dapi_market(base_symbol, MarketType.USD)
        ]
        
        market_results = await asyncio.gather(*market_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(market_results):
            market_type = [MarketType.USDT, MarketType.USDC, MarketType.USD][i]
            
            if isinstance(result, Exception):
                error_msg = f"{market_type.value}: {str(result)}"
                errors.append(error_msg)
                logger.warning(f"⚠️ Binance {market_type.value} failed: {str(result)}")
            elif result is not None:
                markets.append(result)
                logger.info(f"✅ Binance {market_type.value}: {result.oi_tokens:,.0f} {base_symbol} (${result.oi_usd/1e9:.1f}B)")
        
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
            exchange="binance",
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
        
        logger.info(f"🟡 Binance total: {total_oi_tokens:,.0f} {base_symbol} (${total_oi_usd/1e9:.1f}B) across {len(markets)} markets")
        
        return result
    
    async def _fetch_fapi_market(self, base_symbol: str, market_type: MarketType) -> Optional[MarketOIData]:
        """Fetch FAPI market data (USDT/USDC linear contracts)"""
        try:
            symbol = self.format_symbol(base_symbol, market_type)
            session = await self.get_session()
            
            # Fetch OI, ticker, and funding data in parallel
            oi_task = session.get(f"{self.endpoints['fapi_oi']}?symbol={symbol}")
            ticker_task = session.get(f"{self.endpoints['fapi_ticker']}?symbol={symbol}")
            funding_task = session.get(f"{self.endpoints['fapi_funding']}?symbol={symbol}")
            
            async with oi_task as oi_response, ticker_task as ticker_response, funding_task as funding_response:
                oi_data = await oi_response.json()
                ticker_data = await ticker_response.json()
                funding_data = await funding_response.json()
            
            # Extract data
            oi_tokens = float(oi_data['openInterest'])
            price = float(ticker_data['lastPrice'])
            volume_24h = float(ticker_data['volume'])
            funding_rate = float(funding_data['lastFundingRate'])
            
            # Calculate USD values
            oi_usd = oi_tokens * price  # Linear: tokens × price
            volume_24h_usd = volume_24h * price
            
            return MarketOIData(
                exchange="binance",
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
                api_source=f"FAPI:{symbol}",
                calculation_method=f"linear: {oi_tokens:,.0f} × ${price:,.2f}",
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Binance FAPI {market_type.value} error: {str(e)}")
            return None
    
    async def _fetch_dapi_market(self, base_symbol: str, market_type: MarketType) -> Optional[MarketOIData]:
        """Fetch DAPI market data (USD inverse contracts)"""
        try:
            symbol = self.format_symbol(base_symbol, market_type)
            session = await self.get_session()
            
            # Fetch data sequentially to avoid parallel execution issues
            # OI data
            async with session.get(f"{self.endpoints['dapi_oi']}?symbol={symbol}") as response:
                oi_data = await response.json()
                
            # Ticker data (returns list)
            async with session.get(f"{self.endpoints['dapi_ticker']}?symbol={symbol}") as response:
                ticker_data = await response.json()
                if isinstance(ticker_data, list) and len(ticker_data) > 0:
                    ticker_data = ticker_data[0]
                    
            # Funding data (returns list)
            async with session.get(f"{self.endpoints['dapi_funding']}?symbol={symbol}") as response:
                funding_data = await response.json()
                if isinstance(funding_data, list) and len(funding_data) > 0:
                    funding_data = funding_data[0]
            
            # Extract data with validation
            oi_contracts = float(oi_data['openInterest'])  # Contract units
            price = float(ticker_data['lastPrice'])
            volume_24h_contracts = float(ticker_data['volume'])
            funding_rate = float(funding_data['lastFundingRate'])
            
            # DAPI Inverse Contract Calculation
            # Each contract = $100 USD worth of BTC
            # OI in tokens = (contracts × $100) / price
            contract_value_usd = 100.0  # $100 per contract
            oi_usd = oi_contracts * contract_value_usd
            oi_tokens = oi_usd / price
            
            # Volume calculation
            volume_24h_usd = volume_24h_contracts * contract_value_usd
            volume_24h = volume_24h_usd / price
            
            return MarketOIData(
                exchange="binance",
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
                api_source=f"DAPI:{symbol}",
                calculation_method=f"inverse: {oi_contracts:,.0f} contracts × $100 ÷ ${price:,.2f}",
                price_validated=False,
                calculation_validated=False,
                api_validated=False
            )
            
        except Exception as e:
            logger.error(f"❌ Binance DAPI {market_type.value} error: {str(e)}")
            return None
    
    def _calculate_inverse_usd(self, oi_tokens: float, price: float) -> float:
        """Binance-specific inverse calculation (already handled in _fetch_dapi_market)"""
        # For DAPI, this is already calculated correctly in _fetch_dapi_market
        # This method is just for consistency with base class
        return oi_tokens * price

# Testing and validation functions
async def test_binance_provider():
    """Test Binance provider implementation"""
    print("🚀 Testing Binance OI Provider")
    
    provider = BinanceOIProvider()
    
    try:
        # Test with BTC
        result = await provider.get_oi_data("BTC")
        
        print(f"\n📊 BINANCE TEST RESULTS:")
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
        return None
    finally:
        await provider.close()

async def validate_binance_with_counter_agents():
    """Validate Binance implementation with counter-agents"""
    from counter_agent_validation import CounterAgentValidationSystem
    
    print("🛡️ Validating Binance with Counter-Agents")
    
    # Get Binance data
    provider = BinanceOIProvider()
    binance_result = await provider.get_oi_data("BTC")
    await provider.close()
    
    if not binance_result.validation_passed:
        print("❌ Binance provider validation failed - cannot proceed to counter-agent validation")
        return False
    
    # Format for counter-agent validation
    validation_data = {
        'symbol': 'BTC',
        'aggregated_oi': {
            'total_tokens': binance_result.total_oi_tokens,
            'total_usd': binance_result.total_oi_usd
        },
        'exchange_breakdown': [
            {
                'exchange': 'binance',
                'oi_tokens': market.oi_tokens,
                'oi_usd': market.oi_usd,
                'price': market.price
            } for market in binance_result.markets
        ]
    }
    
    # Run counter-agent validation
    validator = CounterAgentValidationSystem()
    counter_results = await validator.deploy_counter_agents(validation_data)
    validation_report = validator.generate_validation_report(counter_results)
    
    print(f"\n🔍 COUNTER-AGENT VALIDATION REPORT:")
    print(f"Overall Status: {validation_report['validation_summary']['overall_status']}")
    print(f"Agreement Rate: {validation_report['validation_summary']['agreement_rate_pct']:.1f}%")
    print(f"Agreements: {validation_report['validation_summary']['agreements']}")
    print(f"Disagreements: {validation_report['validation_summary']['disagreements']}")
    
    # Show specific results
    for result in validation_report['counter_agent_results']:
        status_emoji = "✅" if result['status'] == 'AGREEMENT' else "❌"
        print(f"{status_emoji} {result['validation_type']}: {result['evidence']}")
    
    return validation_report['validation_summary']['overall_status'] in ['TRUSTED', 'CAUTIOUS']

if __name__ == "__main__":
    async def main():
        # Test provider
        await test_binance_provider()
        
        print("\n" + "="*80)
        
        # Validate with counter-agents
        validation_passed = await validate_binance_with_counter_agents()
        
        if validation_passed:
            print("\n✅ BINANCE PROVIDER READY FOR INTEGRATION")
        else:
            print("\n❌ BINANCE PROVIDER NEEDS FIXES BEFORE INTEGRATION")
    
    asyncio.run(main())