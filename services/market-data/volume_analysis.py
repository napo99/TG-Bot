"""
Volume Analysis Engine for Crypto Trading Assistant
Implements sophisticated volume spike detection and CVD calculation
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from loguru import logger

@dataclass
class VolumeSpike:
    symbol: str
    timeframe: str
    current_volume: float
    average_volume: float
    spike_percentage: float
    spike_level: str  # "MODERATE", "HIGH", "EXTREME"
    timestamp: datetime
    volume_usd: float
    is_significant: bool

@dataclass
class CVDData:
    symbol: str
    timeframe: str
    current_cvd: float
    cvd_change_24h: float
    cvd_trend: str  # "BULLISH", "BEARISH", "NEUTRAL"
    divergence_detected: bool
    price_trend: str
    timestamp: datetime

@dataclass
class VolumeAlert:
    id: str
    user_id: str
    symbol: str
    threshold_percentage: float
    timeframe: str
    alert_type: str  # "volume_spike", "oi_change"
    threshold_value: Optional[float] = None
    is_active: bool = True
    created_at: datetime = None
    last_triggered: Optional[datetime] = None

class VolumeAnalysisEngine:
    """Advanced volume analysis with spike detection and CVD calculation"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.volume_cache = {}  # Cache for volume history
        self.cvd_cache = {}     # Cache for CVD calculations
        
    async def detect_volume_spike(self, symbol: str, timeframe: str = '15m', 
                                 lookback_periods: int = 96, exchange: str = None) -> VolumeSpike:
        """
        Detect volume spikes with sophisticated analysis
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('15m', '1h', '4h')
            lookback_periods: Periods to analyze (96 = 24h of 15m candles)
            exchange: Exchange to use
        """
        try:
            if exchange is None:
                exchange = 'binance'
            
            if exchange not in self.exchange_manager.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchange_manager.exchanges[exchange]
            
            # Fetch OHLCV data
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=lookback_periods + 1)
            
            if len(ohlcv) < 20:  # Need minimum data
                return self._create_empty_spike(symbol, timeframe)
            
            # Extract volume data
            volumes = [candle[5] for candle in ohlcv]  # Volume is index 5
            prices = [candle[4] for candle in ohlcv]   # Close prices
            timestamps = [candle[0] for candle in ohlcv]
            
            current_volume = volumes[-1]
            current_price = prices[-1]
            
            # Smart volume analysis
            spike_analysis = self._analyze_volume_pattern(volumes, timestamps, timeframe)
            
            # Calculate volume in USD
            volume_usd = current_volume * current_price
            
            # Determine spike significance
            spike_level, is_significant = self._classify_spike(spike_analysis['spike_percentage'])
            
            return VolumeSpike(
                symbol=symbol,
                timeframe=timeframe,
                current_volume=float(current_volume),
                average_volume=float(spike_analysis['average_volume']),
                spike_percentage=float(spike_analysis['spike_percentage']),
                spike_level=spike_level,
                timestamp=datetime.now(),
                volume_usd=float(volume_usd),
                is_significant=bool(is_significant)
            )
            
        except Exception as e:
            logger.error(f"Error detecting volume spike for {symbol}: {e}")
            return self._create_empty_spike(symbol, timeframe)
    
    def _analyze_volume_pattern(self, volumes: List[float], timestamps: List[int], 
                               timeframe: str) -> Dict:
        """
        Sophisticated volume pattern analysis accounting for:
        - Time-of-day patterns
        - Day-of-week effects
        - Market session overlaps
        - Weekend vs weekday differences
        """
        if len(volumes) < 10:
            return {'spike_percentage': 0, 'average_volume': 0}
        
        current_volume = volumes[-1]
        historical_volumes = volumes[:-1]
        
        # Remove outliers for cleaner baseline (top 5% and bottom 5%)
        sorted_volumes = sorted(historical_volumes)
        trim_count = max(1, len(sorted_volumes) // 20)  # 5%
        trimmed_volumes = sorted_volumes[trim_count:-trim_count]
        
        if not trimmed_volumes:
            trimmed_volumes = historical_volumes
        
        # Calculate different averages
        average_volume = statistics.mean(trimmed_volumes)
        median_volume = statistics.median(trimmed_volumes)
        
        # Use median as baseline (more robust against outliers)
        baseline_volume = median_volume
        
        # Account for time-of-day patterns
        baseline_volume = self._adjust_for_time_patterns(baseline_volume, timeframe)
        
        # Calculate spike percentage
        if baseline_volume > 0:
            spike_percentage = ((current_volume - baseline_volume) / baseline_volume) * 100
        else:
            spike_percentage = 0
        
        return {
            'spike_percentage': round(spike_percentage, 2),
            'average_volume': round(average_volume, 2),
            'baseline_volume': round(baseline_volume, 2),
            'median_volume': round(median_volume, 2)
        }
    
    def _adjust_for_time_patterns(self, baseline_volume: float, timeframe: str) -> float:
        """
        Adjust baseline volume for known time-of-day patterns
        Crypto markets are 24/7 but still have patterns:
        - Asia session: Higher volume 00:00-08:00 UTC
        - Europe session: Higher volume 08:00-16:00 UTC  
        - US session: Highest volume 16:00-00:00 UTC
        """
        current_hour = datetime.utcnow().hour
        
        # Volume multipliers based on market sessions
        if 0 <= current_hour < 8:      # Asia session
            multiplier = 0.8
        elif 8 <= current_hour < 16:   # Europe session
            multiplier = 1.0  
        elif 16 <= current_hour < 24:  # US session (highest volume)
            multiplier = 1.2
        else:
            multiplier = 1.0
        
        # Weekend adjustment (typically lower volume)
        if datetime.utcnow().weekday() >= 5:  # Saturday/Sunday
            multiplier *= 0.7
        
        return baseline_volume * multiplier
    
    def _classify_spike(self, spike_percentage: float) -> Tuple[str, bool]:
        """Classify volume spike severity and significance"""
        if spike_percentage >= 500:
            return "EXTREME", True
        elif spike_percentage >= 300:
            return "HIGH", True
        elif spike_percentage >= 150:
            return "MODERATE", True
        elif spike_percentage >= 50:
            return "LOW", False
        else:
            return "NORMAL", False
    
    async def calculate_cvd(self, symbol: str, timeframe: str = '15m', 
                           periods: int = 96, exchange: str = None) -> CVDData:
        """
        Calculate Cumulative Volume Delta (CVD)
        
        CVD tracks buying vs selling pressure:
        - Green candle (close > open): +volume (buying pressure)
        - Red candle (close < open): -volume (selling pressure)
        - Cumulative sum shows overall market sentiment
        """
        try:
            if exchange is None:
                exchange = 'binance'
            
            if exchange not in self.exchange_manager.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchange_manager.exchanges[exchange]
            
            # Fetch OHLCV data
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=periods)
            
            if len(ohlcv) < 10:
                return self._create_empty_cvd(symbol, timeframe)
            
            # Calculate CVD
            cvd_values = []
            cumulative_cvd = 0
            
            for candle in ohlcv:
                open_price = candle[1]
                close_price = candle[4]
                volume = candle[5]
                
                # Determine candle direction
                if close_price > open_price:
                    # Green candle = buying pressure
                    volume_delta = volume
                elif close_price < open_price:
                    # Red candle = selling pressure  
                    volume_delta = -volume
                else:
                    # Doji = neutral
                    volume_delta = 0
                
                cumulative_cvd += volume_delta
                cvd_values.append(cumulative_cvd)
            
            current_cvd = cvd_values[-1]
            cvd_24h_ago = cvd_values[0] if len(cvd_values) > 0 else 0
            cvd_change_24h = current_cvd - cvd_24h_ago
            
            # Determine CVD trend
            cvd_trend = self._analyze_cvd_trend(cvd_values)
            
            # Check for price-CVD divergence
            prices = [candle[4] for candle in ohlcv]
            divergence_detected = self._detect_cvd_divergence(prices, cvd_values)
            
            # Determine price trend for divergence analysis
            price_trend = "BULLISH" if prices[-1] > prices[0] else "BEARISH"
            
            return CVDData(
                symbol=symbol,
                timeframe=timeframe,
                current_cvd=float(round(current_cvd, 2)),
                cvd_change_24h=float(round(cvd_change_24h, 2)),
                cvd_trend=cvd_trend,
                divergence_detected=bool(divergence_detected),
                price_trend=price_trend,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating CVD for {symbol}: {e}")
            return self._create_empty_cvd(symbol, timeframe)
    
    def _analyze_cvd_trend(self, cvd_values: List[float]) -> str:
        """Analyze CVD trend over recent periods"""
        if len(cvd_values) < 10:
            return "NEUTRAL"
        
        recent_cvd = cvd_values[-10:]  # Last 10 periods
        
        # Calculate trend using linear regression slope
        x = list(range(len(recent_cvd)))
        slope = np.polyfit(x, recent_cvd, 1)[0]
        
        if slope > 0:
            return "BULLISH"  # Increasing buying pressure
        elif slope < 0:
            return "BEARISH"  # Increasing selling pressure
        else:
            return "NEUTRAL"
    
    def _detect_cvd_divergence(self, prices: List[float], cvd_values: List[float]) -> bool:
        """
        Detect divergence between price and CVD
        Divergence signals potential trend reversals
        """
        if len(prices) < 20 or len(cvd_values) < 20:
            return False
        
        # Compare recent trends (last 20 periods)
        recent_prices = prices[-20:]
        recent_cvd = cvd_values[-20:]
        
        # Calculate trends
        price_slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        cvd_slope = np.polyfit(range(len(recent_cvd)), recent_cvd, 1)[0]
        
        # Divergence occurs when price and CVD trends oppose
        price_trend_up = price_slope > 0
        cvd_trend_up = cvd_slope > 0
        
        # Convert to Python bool to ensure JSON serialization
        return bool(price_trend_up != cvd_trend_up)
    
    async def scan_volume_spikes(self, timeframe: str = '15m', 
                                min_spike_percentage: float = 200) -> List[VolumeSpike]:
        """Scan all major symbols for volume spikes"""
        major_symbols = [
            'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'BNB/USDT', 'SOL/USDT',
            'ADA/USDT', 'DOGE/USDT', 'MATIC/USDT', 'DOT/USDT', 'LINK/USDT'
        ]
        
        spikes = []
        for symbol in major_symbols:
            try:
                spike = await self.detect_volume_spike(symbol, timeframe)
                if spike.spike_percentage >= min_spike_percentage:
                    spikes.append(spike)
            except Exception as e:
                logger.warning(f"Error scanning {symbol}: {e}")
        
        # Sort by spike percentage
        return sorted(spikes, key=lambda x: x.spike_percentage, reverse=True)
    
    def _create_empty_spike(self, symbol: str, timeframe: str) -> VolumeSpike:
        """Create empty volume spike for error cases"""
        return VolumeSpike(
            symbol=symbol,
            timeframe=timeframe,
            current_volume=0,
            average_volume=0,
            spike_percentage=0,
            spike_level="NORMAL",
            timestamp=datetime.now(),
            volume_usd=0,
            is_significant=False
        )
    
    def _create_empty_cvd(self, symbol: str, timeframe: str) -> CVDData:
        """Create empty CVD data for error cases"""
        return CVDData(
            symbol=symbol,
            timeframe=timeframe,
            current_cvd=0,
            cvd_change_24h=0,
            cvd_trend="NEUTRAL",
            divergence_detected=False,
            price_trend="NEUTRAL",
            timestamp=datetime.now()
        )

# Example usage:
# volume_engine = VolumeAnalysisEngine(exchange_manager)
# spike = await volume_engine.detect_volume_spike("BTC/USDT", "15m")
# cvd = await volume_engine.calculate_cvd("BTC/USDT", "1h")
# all_spikes = await volume_engine.scan_volume_spikes("15m", 200)