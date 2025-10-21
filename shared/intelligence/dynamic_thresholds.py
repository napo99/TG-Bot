"""
Dynamic Threshold Engine - Phase 1 Implementation
Intelligent, market-adaptive thresholds replacing all hardcoded values
Part of the Institutional Trading Intelligence System
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import math
from datetime import datetime, timedelta
import aiohttp
import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class AssetProfile:
    """Dynamic asset profiling for intelligent thresholds"""
    symbol: str
    market_cap: float
    avg_daily_volume_usd: float
    volatility_score: float
    liquidity_tier: str  # "TIER_1", "TIER_2", "TIER_3", "MICRO_CAP"
    avg_trade_size: float
    whale_threshold_percentile: float
    last_updated: datetime


@dataclass
class ThresholdResult:
    """Result container for calculated thresholds"""
    single_liquidation_usd: float
    cascade_threshold_usd: float
    cascade_count_threshold: int
    confidence_score: float
    next_review_time: datetime
    calculation_method: str
    volatility_adjustment: float
    session_adjustment: float


@dataclass
class VolumeThreshold:
    """Volume spike thresholds"""
    volume_spike_multiplier: float
    moderate_threshold: float
    high_threshold: float
    extreme_threshold: float
    whale_trade_usd: float
    baseline_volume_usd: float


@dataclass
class OIThreshold:
    """Open Interest change thresholds"""
    oi_change_threshold_pct: float
    minimum_oi_usd: float
    time_window_minutes: int
    cross_exchange_confirmation_required: bool
    maturity_adjustment: float


class MarketDataProvider(ABC):
    """Abstract interface for market data providers"""
    
    @abstractmethod
    async def get_24h_volume(self, symbol: str) -> Optional[float]:
        """Get 24h volume in USD"""
        pass
    
    @abstractmethod
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """Get market cap in USD"""
        pass
    
    @abstractmethod
    async def get_volatility(self, symbol: str, period_hours: int = 24) -> Optional[float]:
        """Get volatility score"""
        pass
    
    @abstractmethod
    async def get_average_trade_size(self, symbol: str) -> Optional[float]:
        """Get average trade size in USD"""
        pass


class DefaultMarketDataProvider(MarketDataProvider):
    """Default implementation using existing market data service"""
    
    def __init__(self, market_data_url: str):
        self.market_data_url = market_data_url
        self.session = None
    
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_24h_volume(self, symbol: str) -> Optional[float]:
        """Get 24h volume from market data service"""
        try:
            session = await self._get_session()
            async with session.post(f"{self.market_data_url}/combined_price", 
                                  json={'symbol': symbol}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        # Try perp first, then spot
                        perp_vol = data.get('data', {}).get('perp', {}).get('volume_24h', 0)
                        spot_vol = data.get('data', {}).get('spot', {}).get('volume_24h', 0)
                        price = (data.get('data', {}).get('perp', {}).get('price') or 
                               data.get('data', {}).get('spot', {}).get('price', 1))
                        
                        volume = max(perp_vol, spot_vol) * price if price else 0
                        return volume if volume > 0 else None
        except Exception as e:
            logger.error(f"Error fetching volume for {symbol}: {e}")
        return None
    
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """Estimate market cap from available data"""
        try:
            # Use volume as a proxy for market cap (rough estimation)
            volume = await self.get_24h_volume(symbol)
            if volume:
                # Rough market cap estimation based on volume patterns
                base_symbol = symbol.replace('USDT', '').replace('USDC', '').replace('-', '')
                
                # Market cap multipliers based on typical volume/mcap ratios
                multipliers = {
                    'BTC': 100,   # Conservative BTC ratio
                    'ETH': 80,    # ETH typically lower
                    'SOL': 30,    # Mid-caps
                    'ADA': 25,
                    'DOT': 20,
                    'AVAX': 15,
                }
                multiplier = multipliers.get(base_symbol, 5)  # Default for smaller caps
                return volume * multiplier
        except Exception as e:
            logger.error(f"Error estimating market cap for {symbol}: {e}")
        return None
    
    async def get_volatility(self, symbol: str, period_hours: int = 24) -> Optional[float]:
        """Get volatility from price changes"""
        try:
            session = await self._get_session()
            async with session.post(f"{self.market_data_url}/combined_price", 
                                  json={'symbol': symbol}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        # Use 24h change as volatility proxy
                        perp_change = data.get('data', {}).get('perp', {}).get('change_24h', 0)
                        spot_change = data.get('data', {}).get('spot', {}).get('change_24h', 0)
                        
                        # Use the larger absolute change
                        volatility = max(abs(perp_change or 0), abs(spot_change or 0)) / 100
                        return volatility if volatility > 0 else None
        except Exception as e:
            logger.error(f"Error fetching volatility for {symbol}: {e}")
        return None
    
    async def get_average_trade_size(self, symbol: str) -> Optional[float]:
        """Estimate average trade size"""
        try:
            volume = await self.get_24h_volume(symbol)
            if volume:
                # Rough estimation: assume 10-50k trades per day depending on asset
                base_symbol = symbol.replace('USDT', '').replace('USDC', '').replace('-', '')
                
                # Typical trades per day
                trades_per_day = {
                    'BTC': 100000,  # Very active
                    'ETH': 80000,
                    'SOL': 30000,
                    'ADA': 20000,
                    'DOT': 15000,
                }.get(base_symbol, 5000)  # Default for smaller assets
                
                avg_trade_size = volume / trades_per_day
                return avg_trade_size if avg_trade_size > 10 else 100  # Minimum $100
        except Exception as e:
            logger.error(f"Error estimating trade size for {symbol}: {e}")
        return None


class DynamicThresholdEngine:
    """Calculates intelligent, market-adaptive thresholds"""
    
    def __init__(self, market_data_provider: MarketDataProvider = None, 
                 market_data_url: str = "http://localhost:8001"):
        self.market_data_provider = market_data_provider or DefaultMarketDataProvider(market_data_url)
        self.asset_cache: Dict[str, AssetProfile] = {}
        self.cache_ttl = timedelta(hours=1)  # Cache profiles for 1 hour
        
        # Market session multipliers (from PRD)
        self.market_session_multipliers = {
            'asian': 0.7,     # Lower volume session
            'european': 0.9,  # Medium volume session  
            'us': 1.0,        # Highest volume session
            'weekend': 0.5    # Much lower weekend activity
        }
        
        # Liquidity tier definitions
        self.tier_definitions = {
            'TIER_1': {'min_market_cap': 100e9, 'min_volume': 1e9},      # $100B+ mcap, $1B+ volume
            'TIER_2': {'min_market_cap': 10e9, 'min_volume': 100e6},     # $10B+ mcap, $100M+ volume  
            'TIER_3': {'min_market_cap': 1e9, 'min_volume': 10e6},       # $1B+ mcap, $10M+ volume
            'MICRO_CAP': {'min_market_cap': 0, 'min_volume': 0}          # Everything else
        }
    
    async def calculate_liquidation_threshold(self, symbol: str) -> ThresholdResult:
        """Calculate dynamic liquidation alert thresholds"""
        try:
            profile = await self.get_asset_profile(symbol)
            session = self.get_current_session()
            volatility = await self.get_volatility_score(symbol)
            
            # Base threshold as percentage of daily volume
            base_threshold_pct = {
                'TIER_1': 0.0005,    # 0.05% of daily volume (BTC, ETH)
                'TIER_2': 0.001,     # 0.1% of daily volume (SOL, ADA)
                'TIER_3': 0.002,     # 0.2% of daily volume (smaller caps)
                'MICRO_CAP': 0.005   # 0.5% of daily volume (micro caps)
            }[profile.liquidity_tier]
            
            # Calculate USD threshold
            base_usd_threshold = profile.avg_daily_volume_usd * base_threshold_pct
            
            # Apply multipliers
            session_multiplier = self.market_session_multipliers[session]
            volatility_multiplier = max(0.5, min(2.0, volatility))  # 0.5x to 2x based on volatility
            
            final_threshold = base_usd_threshold * session_multiplier * volatility_multiplier
            
            # Ensure minimum thresholds
            min_thresholds = {
                'TIER_1': 50000,    # $50k minimum for tier 1
                'TIER_2': 20000,    # $20k minimum for tier 2
                'TIER_3': 5000,     # $5k minimum for tier 3
                'MICRO_CAP': 1000   # $1k minimum for micro caps
            }
            final_threshold = max(final_threshold, min_thresholds[profile.liquidity_tier])
            
            return ThresholdResult(
                single_liquidation_usd=final_threshold,
                cascade_threshold_usd=final_threshold * 5,
                cascade_count_threshold=self._calculate_cascade_count(profile),
                confidence_score=self._calculate_confidence(profile, session, volatility),
                next_review_time=datetime.now() + timedelta(hours=1),
                calculation_method="dynamic_volume_based",
                volatility_adjustment=volatility_multiplier,
                session_adjustment=session_multiplier
            )
            
        except Exception as e:
            logger.error(f"Error calculating liquidation threshold for {symbol}: {e}")
            return self._get_fallback_liquidation_threshold(symbol)
    
    async def calculate_volume_threshold(self, symbol: str) -> VolumeThreshold:
        """Calculate dynamic volume spike thresholds"""
        try:
            profile = await self.get_asset_profile(symbol)
            recent_volatility = await self.get_recent_volatility(symbol, hours=24)
            
            # Dynamic spike multipliers based on asset characteristics
            base_multipliers = {
                'TIER_1': 2.5,    # 250% spike for BTC/ETH
                'TIER_2': 3.0,    # 300% spike for mid caps
                'TIER_3': 4.0,    # 400% spike for smaller caps
                'MICRO_CAP': 5.0  # 500% spike for micro caps
            }
            
            base_multiplier = base_multipliers[profile.liquidity_tier]
            volatility_adjustment = 1.0 + (recent_volatility - 0.05) * 2  # Adjust for volatility
            
            final_multiplier = base_multiplier * volatility_adjustment
            
            return VolumeThreshold(
                volume_spike_multiplier=final_multiplier,
                moderate_threshold=final_multiplier * 0.7,
                high_threshold=final_multiplier,
                extreme_threshold=final_multiplier * 1.5,
                whale_trade_usd=profile.avg_trade_size * 20,  # 20x average trade
                baseline_volume_usd=profile.avg_daily_volume_usd
            )
            
        except Exception as e:
            logger.error(f"Error calculating volume threshold for {symbol}: {e}")
            return self._get_fallback_volume_threshold(symbol)
    
    async def calculate_oi_threshold(self, symbol: str) -> OIThreshold:
        """Calculate dynamic OI change thresholds"""
        try:
            profile = await self.get_asset_profile(symbol)
            market_maturity = await self.get_market_maturity_score(symbol)
            
            # More mature markets have lower threshold percentages
            maturity_multipliers = {
                'VERY_MATURE': 0.8,    # BTC, ETH - lower thresholds
                'MATURE': 1.0,         # SOL, ADA - normal thresholds
                'DEVELOPING': 1.3,     # Newer major caps - higher thresholds
                'EMERGING': 1.8        # Very new assets - much higher thresholds
            }
            
            base_oi_threshold_pct = {
                'TIER_1': 0.12,    # 12% for tier 1
                'TIER_2': 0.15,    # 15% for tier 2
                'TIER_3': 0.20,    # 20% for tier 3
                'MICRO_CAP': 0.30  # 30% for micro caps
            }[profile.liquidity_tier]
            
            maturity_multiplier = maturity_multipliers.get(market_maturity, 1.0)
            final_oi_threshold = base_oi_threshold_pct * maturity_multiplier
            
            return OIThreshold(
                oi_change_threshold_pct=final_oi_threshold,
                minimum_oi_usd=self._calculate_min_oi_threshold(profile),
                time_window_minutes=self._calculate_time_window(profile),
                cross_exchange_confirmation_required=profile.liquidity_tier in ['TIER_3', 'MICRO_CAP'],
                maturity_adjustment=maturity_multiplier
            )
            
        except Exception as e:
            logger.error(f"Error calculating OI threshold for {symbol}: {e}")
            return self._get_fallback_oi_threshold(symbol)
    
    async def get_asset_profile(self, symbol: str) -> AssetProfile:
        """Get or create asset profile with caching"""
        # Clean symbol
        clean_symbol = symbol.replace('/', '-').upper()
        
        # Check cache
        if clean_symbol in self.asset_cache:
            profile = self.asset_cache[clean_symbol]
            if datetime.now() - profile.last_updated < self.cache_ttl:
                return profile
        
        # Fetch fresh data
        try:
            market_cap = await self.market_data_provider.get_market_cap(clean_symbol) or 0
            daily_volume = await self.market_data_provider.get_24h_volume(clean_symbol) or 0
            volatility = await self.market_data_provider.get_volatility(clean_symbol) or 0.05
            avg_trade_size = await self.market_data_provider.get_average_trade_size(clean_symbol) or 1000
            
            # Determine liquidity tier
            liquidity_tier = self._determine_liquidity_tier(market_cap, daily_volume)
            
            # Create profile
            profile = AssetProfile(
                symbol=clean_symbol,
                market_cap=market_cap,
                avg_daily_volume_usd=daily_volume,
                volatility_score=volatility,
                liquidity_tier=liquidity_tier,
                avg_trade_size=avg_trade_size,
                whale_threshold_percentile=0.95,
                last_updated=datetime.now()
            )
            
            # Cache it
            self.asset_cache[clean_symbol] = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error creating asset profile for {symbol}: {e}")
            return self._get_fallback_asset_profile(symbol)
    
    def _determine_liquidity_tier(self, market_cap: float, volume: float) -> str:
        """Determine liquidity tier based on market cap and volume"""
        for tier, requirements in self.tier_definitions.items():
            if (market_cap >= requirements['min_market_cap'] and 
                volume >= requirements['min_volume']):
                return tier
        return 'MICRO_CAP'
    
    def get_current_session(self) -> str:
        """Determine current market session"""
        utc_hour = datetime.utcnow().hour
        day_of_week = datetime.utcnow().weekday()
        
        # Weekend check
        if day_of_week >= 5:  # Saturday = 5, Sunday = 6
            return 'weekend'
        
        # Trading sessions (UTC)
        if 13 <= utc_hour < 22:  # New York: 13:00-22:00 UTC
            return 'us'
        elif 7 <= utc_hour < 16:  # London: 07:00-16:00 UTC
            return 'european'
        else:  # Asia-Pacific
            return 'asian'
    
    async def get_volatility_score(self, symbol: str) -> float:
        """Get current volatility score"""
        try:
            volatility = await self.market_data_provider.get_volatility(symbol)
            return volatility if volatility is not None else 0.05  # Default 5%
        except Exception as e:
            logger.error(f"Error getting volatility for {symbol}: {e}")
            return 0.05
    
    async def get_recent_volatility(self, symbol: str, hours: int = 24) -> float:
        """Get recent volatility (same as get_volatility_score for now)"""
        return await self.get_volatility_score(symbol)
    
    async def get_market_maturity_score(self, symbol: str) -> str:
        """Determine market maturity based on symbol"""
        base_symbol = symbol.replace('USDT', '').replace('USDC', '').replace('-', '').replace('/', '')
        
        # Classify by well-known symbols
        maturity_map = {
            'BTC': 'VERY_MATURE',
            'ETH': 'VERY_MATURE', 
            'SOL': 'MATURE',
            'ADA': 'MATURE',
            'DOT': 'MATURE',
            'AVAX': 'DEVELOPING',
            'MATIC': 'DEVELOPING',
            'LINK': 'MATURE',
            'UNI': 'DEVELOPING'
        }
        
        return maturity_map.get(base_symbol, 'EMERGING')
    
    def _calculate_cascade_count(self, profile: AssetProfile) -> int:
        """Calculate cascade count threshold"""
        base_counts = {
            'TIER_1': 8,     # Higher count for major assets
            'TIER_2': 6,
            'TIER_3': 4,
            'MICRO_CAP': 3
        }
        return base_counts.get(profile.liquidity_tier, 5)
    
    def _calculate_confidence(self, profile: AssetProfile, session: str, volatility: float) -> float:
        """Calculate confidence score for thresholds"""
        base_confidence = 0.8
        
        # Adjust for liquidity tier
        tier_adjustments = {
            'TIER_1': 0.1,    # Higher confidence for major assets
            'TIER_2': 0.05,
            'TIER_3': 0,
            'MICRO_CAP': -0.2  # Lower confidence for micro caps
        }
        
        # Adjust for session (US session has more data = higher confidence)
        session_adjustments = {
            'us': 0.1,
            'european': 0.05,
            'asian': 0,
            'weekend': -0.15
        }
        
        # Adjust for volatility (extreme volatility reduces confidence)
        volatility_adjustment = -0.1 if volatility > 0.15 else 0.05 if volatility < 0.05 else 0
        
        confidence = base_confidence + tier_adjustments.get(profile.liquidity_tier, 0)
        confidence += session_adjustments.get(session, 0)
        confidence += volatility_adjustment
        
        return max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0
    
    def _calculate_min_oi_threshold(self, profile: AssetProfile) -> float:
        """Calculate minimum OI threshold"""
        base_thresholds = {
            'TIER_1': 50_000_000,   # $50M
            'TIER_2': 25_000_000,   # $25M
            'TIER_3': 10_000_000,   # $10M
            'MICRO_CAP': 1_000_000  # $1M
        }
        return base_thresholds.get(profile.liquidity_tier, 5_000_000)
    
    def _calculate_time_window(self, profile: AssetProfile) -> int:
        """Calculate time window for OI monitoring"""
        # Faster monitoring for higher tier assets
        windows = {
            'TIER_1': 10,    # 10 minutes
            'TIER_2': 15,    # 15 minutes
            'TIER_3': 20,    # 20 minutes
            'MICRO_CAP': 30  # 30 minutes
        }
        return windows.get(profile.liquidity_tier, 15)
    
    # Fallback methods for error cases
    def _get_fallback_liquidation_threshold(self, symbol: str) -> ThresholdResult:
        """Fallback liquidation thresholds when calculation fails"""
        base_symbol = symbol.replace('USDT', '').replace('USDC', '').replace('-', '').replace('/', '')
        
        fallback_thresholds = {
            'BTC': 100000,
            'ETH': 50000,
            'SOL': 25000,
            'ADA': 15000,
            'DOT': 10000
        }
        
        threshold = fallback_thresholds.get(base_symbol, 10000)
        
        return ThresholdResult(
            single_liquidation_usd=threshold,
            cascade_threshold_usd=threshold * 5,
            cascade_count_threshold=5,
            confidence_score=0.5,  # Low confidence for fallback
            next_review_time=datetime.now() + timedelta(minutes=30),
            calculation_method="fallback_hardcoded",
            volatility_adjustment=1.0,
            session_adjustment=1.0
        )
    
    def _get_fallback_volume_threshold(self, symbol: str) -> VolumeThreshold:
        """Fallback volume thresholds"""
        return VolumeThreshold(
            volume_spike_multiplier=3.0,
            moderate_threshold=2.5,
            high_threshold=3.0,
            extreme_threshold=5.0,
            whale_trade_usd=100000,
            baseline_volume_usd=10000000
        )
    
    def _get_fallback_oi_threshold(self, symbol: str) -> OIThreshold:
        """Fallback OI thresholds"""
        return OIThreshold(
            oi_change_threshold_pct=0.20,  # 20% default
            minimum_oi_usd=10_000_000,
            time_window_minutes=15,
            cross_exchange_confirmation_required=True,
            maturity_adjustment=1.0
        )
    
    def _get_fallback_asset_profile(self, symbol: str) -> AssetProfile:
        """Fallback asset profile"""
        return AssetProfile(
            symbol=symbol,
            market_cap=1_000_000_000,  # $1B default
            avg_daily_volume_usd=10_000_000,  # $10M default
            volatility_score=0.05,
            liquidity_tier='TIER_3',
            avg_trade_size=5000,
            whale_threshold_percentile=0.95,
            last_updated=datetime.now()
        )
    
    async def close(self):
        """Clean up resources"""
        if hasattr(self.market_data_provider, 'session') and self.market_data_provider.session:
            await self.market_data_provider.session.close()