#!/usr/bin/env python3
"""
OI ENGINE V2: Clean Modular Architecture
Built for target specification compliance and independent validation
Target: 13 markets across 5 exchanges with proper USD calculations
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import json
from loguru import logger

class MarketType(Enum):
    """Market settlement types for proper categorization"""
    USDT = "USDT"  # Stablecoin-margined (USDT)
    USDC = "USDC"  # Stablecoin-margined (USDC) 
    USD = "USD"    # Coin-margined (Inverse)

@dataclass
class MarketOIData:
    """Single market OI data with complete validation"""
    exchange: str
    symbol: str           # Exchange-specific symbol (e.g., BTCUSDT, BTC-USDT-SWAP)
    base_symbol: str      # Normalized symbol (e.g., BTC)
    market_type: MarketType
    
    # Core OI data
    oi_tokens: float      # Open Interest in base tokens (e.g., BTC)
    oi_usd: float         # Open Interest in USD (calculated: oi_tokens * price)
    price: float          # Current price in USD
    
    # Additional market data
    funding_rate: float   # Current funding rate
    volume_24h: float     # 24h volume in base tokens
    volume_24h_usd: float # 24h volume in USD
    
    # Metadata
    timestamp: datetime
    api_source: str       # API endpoint used
    calculation_method: str # How oi_usd was calculated
    
    # Validation flags
    price_validated: bool = False
    calculation_validated: bool = False
    api_validated: bool = False

@dataclass
class ExchangeOIResult:
    """Complete OI result for a single exchange"""
    exchange: str
    base_symbol: str
    markets: List[MarketOIData]
    
    # Exchange totals
    total_oi_tokens: float
    total_oi_usd: float
    total_volume_24h: float
    total_volume_24h_usd: float
    
    # Market breakdown
    usdt_markets: List[MarketOIData] = field(default_factory=list)
    usdc_markets: List[MarketOIData] = field(default_factory=list)
    usd_markets: List[MarketOIData] = field(default_factory=list)
    
    # Validation status
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AggregatedOIResult:
    """Final aggregated OI result matching target specification"""
    base_symbol: str
    timestamp: datetime
    
    # Target specification totals
    total_oi_tokens: float
    total_oi_usd: float
    
    # Market type breakdown (target spec requirement)
    stablecoin_oi_usd: float    # USDT + USDC combined
    stablecoin_percentage: float # % of total
    inverse_oi_usd: float       # USD (coin-margined)
    inverse_percentage: float   # % of total
    
    # USDT/USDC breakdown
    usdt_oi_usd: float
    usdt_percentage: float
    usdc_oi_usd: float  
    usdc_percentage: float
    
    # Exchange results
    exchange_results: List[ExchangeOIResult]
    
    # Top markets (sorted by OI size for target output)
    top_markets: List[MarketOIData]
    
    # Coverage summary
    exchanges_working: int
    total_markets: int
    
    # Validation summary
    overall_validation_status: str  # TRUSTED, SUSPICIOUS, REJECTED
    validation_pass_rate: float

class BaseExchangeOIProvider(ABC):
    """Abstract base class for exchange OI providers"""
    
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @abstractmethod
    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Get OI data for all markets of a base symbol"""
        pass
    
    @abstractmethod
    def get_supported_market_types(self) -> List[MarketType]:
        """Get supported market types for this exchange"""
        pass
    
    @abstractmethod
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Format symbol for exchange API"""
        pass
    
    def calculate_usd_value(self, oi_tokens: float, price: float, market_type: MarketType) -> Tuple[float, str]:
        """Calculate USD value with proper method documentation"""
        if market_type in [MarketType.USDT, MarketType.USDC]:
            # Linear contracts: OI_USD = OI_TOKENS × PRICE
            oi_usd = oi_tokens * price
            method = f"linear: {oi_tokens:,.0f} × ${price:,.2f}"
        else:  # MarketType.USD (inverse)
            # Inverse contracts: depends on exchange-specific contract sizes
            oi_usd = self._calculate_inverse_usd(oi_tokens, price)
            method = f"inverse: {self.exchange_name} specific calculation"
        
        return oi_usd, method
    
    def _calculate_inverse_usd(self, oi_tokens: float, price: float) -> float:
        """Default inverse calculation - override in exchange-specific implementations"""
        return oi_tokens * price
    
    async def validate_market_data(self, market_data: MarketOIData) -> Tuple[bool, List[str]]:
        """Validate market data accuracy"""
        errors = []
        
        # Validate price reasonableness (should be > $1000 for major cryptos)
        if market_data.base_symbol in ['BTC', 'ETH'] and market_data.price < 1000:
            errors.append(f"Price too low: ${market_data.price:.2f}")
        
        # Validate USD calculation
        expected_usd, _ = self.calculate_usd_value(
            market_data.oi_tokens, 
            market_data.price, 
            market_data.market_type
        )
        
        if expected_usd > 0:
            error_pct = abs(market_data.oi_usd - expected_usd) / expected_usd * 100
            if error_pct > 1.0:  # Max 1% calculation error
                errors.append(f"USD calculation error: {error_pct:.2f}% deviation")
        
        # Validate OI magnitude (should be reasonable for major exchanges)
        if market_data.base_symbol == 'BTC':
            if market_data.oi_tokens < 1000 or market_data.oi_tokens > 10_000_000:
                errors.append(f"BTC OI magnitude suspicious: {market_data.oi_tokens:,.0f}")
        
        return len(errors) == 0, errors

class OIEngineV2:
    """
    Modular OI Engine V2: Clean architecture for target specification compliance
    
    Target Specification:
    - 5 exchanges: Binance, Bybit, OKX, Gate.io, Bitget
    - 13 markets: Up to 3 per exchange (USDT, USDC, USD)
    - Proper market type breakdown (84.9% stablecoin, 15.1% inverse)
    - Total OI: ~322K BTC (~$32.7B)
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseExchangeOIProvider] = {}
        self.validation_enabled = True
    
    def register_provider(self, provider: BaseExchangeOIProvider):
        """Register an exchange OI provider"""
        self.providers[provider.exchange_name] = provider
        logger.info(f"✅ Registered OI provider: {provider.exchange_name}")
    
    async def get_comprehensive_oi(self, base_symbol: str) -> AggregatedOIResult:
        """Get comprehensive OI analysis across all registered exchanges"""
        logger.info(f"🚀 Starting comprehensive OI analysis for {base_symbol}")
        
        # Fetch data from all exchanges in parallel
        exchange_tasks = []
        for exchange_name, provider in self.providers.items():
            task = asyncio.create_task(
                self._fetch_exchange_oi(exchange_name, provider, base_symbol)
            )
            exchange_tasks.append(task)
        
        exchange_results = await asyncio.gather(*exchange_tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        for i, result in enumerate(exchange_results):
            exchange_name = list(self.providers.keys())[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ {exchange_name} failed: {str(result)}")
            elif isinstance(result, ExchangeOIResult):
                if result.validation_passed:
                    valid_results.append(result)
                    logger.info(f"✅ {exchange_name}: {len(result.markets)} markets, ${result.total_oi_usd/1e9:.1f}B")
                else:
                    logger.warning(f"⚠️ {exchange_name} validation failed: {result.validation_errors}")
        
        # Aggregate results
        aggregated = await self._aggregate_results(base_symbol, valid_results)
        
        # Validate against target specification
        if self.validation_enabled:
            await self._validate_target_specification(aggregated)
        
        return aggregated
    
    async def _fetch_exchange_oi(self, exchange_name: str, provider: BaseExchangeOIProvider, base_symbol: str) -> ExchangeOIResult:
        """Fetch OI data from a single exchange with error handling"""
        try:
            logger.info(f"📊 Fetching {exchange_name} OI for {base_symbol}")
            result = await provider.get_oi_data(base_symbol)
            
            # Validate result
            if self.validation_enabled:
                await self._validate_exchange_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {exchange_name} error: {str(e)}")
            # Return empty result on error
            return ExchangeOIResult(
                exchange=exchange_name,
                base_symbol=base_symbol,
                markets=[],
                total_oi_tokens=0,
                total_oi_usd=0,
                total_volume_24h=0,
                total_volume_24h_usd=0,
                validation_passed=False,
                validation_errors=[str(e)]
            )
    
    async def _validate_exchange_result(self, result: ExchangeOIResult):
        """Validate exchange result data"""
        errors = []
        
        # Validate each market
        for market in result.markets:
            market_valid, market_errors = await self.providers[result.exchange].validate_market_data(market)
            if not market_valid:
                errors.extend([f"{market.symbol}: {err}" for err in market_errors])
        
        # Validate totals consistency
        calculated_total_tokens = sum(m.oi_tokens for m in result.markets)
        calculated_total_usd = sum(m.oi_usd for m in result.markets)
        
        if abs(calculated_total_tokens - result.total_oi_tokens) > 0.01 * result.total_oi_tokens:
            errors.append("Token total inconsistency")
        
        if abs(calculated_total_usd - result.total_oi_usd) > 0.01 * result.total_oi_usd:
            errors.append("USD total inconsistency")
        
        result.validation_passed = len(errors) == 0
        result.validation_errors = errors
    
    async def _aggregate_results(self, base_symbol: str, exchange_results: List[ExchangeOIResult]) -> AggregatedOIResult:
        """Aggregate exchange results into final OI analysis"""
        all_markets = []
        total_oi_tokens = 0
        total_oi_usd = 0
        
        usdt_oi_usd = 0
        usdc_oi_usd = 0
        usd_oi_usd = 0
        
        # Collect all markets and calculate totals
        for exchange_result in exchange_results:
            all_markets.extend(exchange_result.markets)
            total_oi_tokens += exchange_result.total_oi_tokens
            total_oi_usd += exchange_result.total_oi_usd
            
            # Calculate market type breakdowns
            for market in exchange_result.markets:
                if market.market_type == MarketType.USDT:
                    usdt_oi_usd += market.oi_usd
                elif market.market_type == MarketType.USDC:
                    usdc_oi_usd += market.oi_usd
                elif market.market_type == MarketType.USD:
                    usd_oi_usd += market.oi_usd
        
        # Calculate percentages
        stablecoin_oi_usd = usdt_oi_usd + usdc_oi_usd
        stablecoin_percentage = (stablecoin_oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
        inverse_percentage = (usd_oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
        usdt_percentage = (usdt_oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
        usdc_percentage = (usdc_oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
        
        # Sort markets by OI size for target output format
        top_markets = sorted(all_markets, key=lambda m: m.oi_usd, reverse=True)
        
        return AggregatedOIResult(
            base_symbol=base_symbol,
            timestamp=datetime.now(),
            total_oi_tokens=total_oi_tokens,
            total_oi_usd=total_oi_usd,
            stablecoin_oi_usd=stablecoin_oi_usd,
            stablecoin_percentage=stablecoin_percentage,
            inverse_oi_usd=usd_oi_usd,
            inverse_percentage=inverse_percentage,
            usdt_oi_usd=usdt_oi_usd,
            usdt_percentage=usdt_percentage,
            usdc_oi_usd=usdc_oi_usd,
            usdc_percentage=usdc_percentage,
            exchange_results=exchange_results,
            top_markets=top_markets,
            exchanges_working=len(exchange_results),
            total_markets=len(all_markets),
            overall_validation_status="PENDING",
            validation_pass_rate=0.0
        )
    
    async def _validate_target_specification(self, result: AggregatedOIResult):
        """Validate result against target specification"""
        pass  # Will implement validation checks
    
    def format_target_output(self, result: AggregatedOIResult) -> str:
        """Format output to match exact target specification"""
        message = f"""📊 OPEN INTEREST ANALYSIS - {result.base_symbol}

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {result.total_oi_tokens:,.0f} {result.base_symbol} (${result.total_oi_usd/1e9:.1f}B)
• Stablecoin-Margined: ${result.stablecoin_oi_usd/1e9:.1f}B | {result.stablecoin_percentage:.1f}%
  - USDT: ${result.usdt_oi_usd/1e9:.1f}B ({result.usdt_percentage:.1f}%)
  - USDC: ${result.usdc_oi_usd/1e9:.1f}B ({result.usdc_percentage:.1f}%)
• Coin-Margined (Inverse): ${result.inverse_oi_usd/1e9:.1f}B | {result.inverse_percentage:.1f}%
  - USD: ${result.inverse_oi_usd/1e9:.1f}B ({result.inverse_percentage:.1f}%)

🔢 STABLECOIN MARKETS ({result.stablecoin_percentage:.1f}%): ${result.stablecoin_oi_usd/1e9:.1f}B
🔢 INVERSE MARKETS ({result.inverse_percentage:.1f}%): ${result.inverse_oi_usd/1e9:.1f}B
📊 COMBINED TOTAL: ${result.total_oi_usd/1e9:.1f}B

📈 TOP MARKETS:"""
        
        # Add top markets
        for i, market in enumerate(result.top_markets[:13], 1):  # Top 13 markets
            market_type_label = "STABLE" if market.market_type in [MarketType.USDT, MarketType.USDC] else "INVERSE"
            message += f"\n{i}. {market.exchange.title()} {market.market_type.value}: {market.oi_tokens:,.0f} {result.base_symbol} (${market.oi_usd/1e9:.1f}B) | {market.oi_usd/result.total_oi_usd*100:.1f}% {market_type_label}"
            message += f"\n   Funding: {market.funding_rate*100:+.4f}% | Vol: {market.volume_24h:,.0f} {result.base_symbol}"
        
        message += f"""

🏢 COVERAGE SUMMARY:
• Exchanges: {result.exchanges_working} working
• Markets: {result.total_markets} total

🕐 {datetime.now().strftime('%H:%M:%S')} UTC"""
        
        return message
    
    async def close_all(self):
        """Close all provider sessions"""
        for provider in self.providers.values():
            await provider.close()

# Example usage and testing framework
async def test_oi_engine_foundation():
    """Test the OI Engine foundation"""
    engine = OIEngineV2()
    
    # Test with mock data
    print("✅ OI Engine V2 foundation created")
    print(f"📊 Providers registered: {len(engine.providers)}")
    print("🏗️ Ready for exchange-specific implementations")
    
    return engine

if __name__ == "__main__":
    asyncio.run(test_oi_engine_foundation())