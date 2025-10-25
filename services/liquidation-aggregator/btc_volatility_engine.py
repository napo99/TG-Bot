"""
BTC Volatility Engine - Multi-Timeframe Real-Time Volatility Tracking
Uses BTC as the market alpha indicator for cascade prediction
"""

import numpy as np
import time
from collections import deque
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


class VolatilityRegime(Enum):
    """Market volatility regimes"""
    DORMANT = 0      # <0.5% 5min vol
    LOW = 1          # 0.5-1% 5min vol
    NORMAL = 2       # 1-2% 5min vol
    ELEVATED = 3     # 2-3% 5min vol
    HIGH = 4         # 3-5% 5min vol
    EXTREME = 5      # >5% 5min vol


@dataclass
class VolatilityMetrics:
    """Real-time volatility metrics across multiple timeframes"""
    timestamp: float

    # Realized volatility (from price movements)
    vol_1min: float = 0.0      # Ultra-fast changes
    vol_5min: float = 0.0      # Standard reference
    vol_15min: float = 0.0     # Medium-term
    vol_1h: float = 0.0        # Trend volatility

    # Volatility derivatives
    vol_acceleration: float = 0.0  # Is volatility increasing?
    vol_dispersion: float = 0.0    # Disagreement between timeframes

    # Liquidation-based volatility
    liq_vol_1min: float = 0.0     # From liquidation sizes
    liq_vol_5min: float = 0.0

    # Regime classification
    regime: VolatilityRegime = VolatilityRegime.NORMAL
    regime_change: bool = False

    # Risk metrics
    vol_percentile_24h: float = 0.0  # Where are we vs last 24h?
    vol_zscore: float = 0.0          # Standard deviations from mean
    cascade_risk_multiplier: float = 1.0


class BTCVolatilityEngine:
    """
    Professional-grade volatility calculation for BTC
    Used by firms like Two Sigma, Citadel for risk management
    """

    def __init__(self):
        # Price storage for different timeframes
        self.price_buffers = {
            '1s': deque(maxlen=60),      # 1 minute of second data
            '5s': deque(maxlen=60),      # 5 minutes of 5s data
            '30s': deque(maxlen=30),     # 15 minutes of 30s data
            '1m': deque(maxlen=60),      # 1 hour of minute data
            '5m': deque(maxlen=288)      # 24 hours of 5min data
        }

        # Liquidation-based volatility
        self.liq_buffers = {
            '1m': deque(maxlen=60),
            '5m': deque(maxlen=60)
        }

        # Historical volatility for percentile calculation
        self.vol_history_24h = deque(maxlen=288)  # 24h of 5min vols

        # Current regime tracking
        self.current_regime = VolatilityRegime.NORMAL
        self.regime_history = deque(maxlen=100)

        # Cascade risk thresholds (calibrated from historical cascades)
        self.cascade_thresholds = {
            VolatilityRegime.DORMANT: 1.0,
            VolatilityRegime.LOW: 1.2,
            VolatilityRegime.NORMAL: 1.5,
            VolatilityRegime.ELEVATED: 2.0,
            VolatilityRegime.HIGH: 3.0,
            VolatilityRegime.EXTREME: 5.0
        }

        self.last_price = None
        self.last_update = 0

    def update_price(self, price: float, timestamp: Optional[float] = None) -> VolatilityMetrics:
        """
        Update BTC price and calculate all volatility metrics
        This should be called on every price update (from trades or mid-price)
        """
        if timestamp is None:
            timestamp = time.time()

        # Store price with timestamp
        price_point = {'price': price, 'time': timestamp}

        # Update all timeframe buffers
        self.price_buffers['1s'].append(price_point)

        # Downsample to other timeframes
        if timestamp - self.last_update >= 5:
            self.price_buffers['5s'].append(price_point)
        if timestamp - self.last_update >= 30:
            self.price_buffers['30s'].append(price_point)
        if timestamp - self.last_update >= 60:
            self.price_buffers['1m'].append(price_point)
        if timestamp - self.last_update >= 300:
            self.price_buffers['5m'].append(price_point)

        self.last_update = timestamp
        self.last_price = price

        # Calculate metrics
        return self.calculate_metrics()

    def calculate_metrics(self) -> VolatilityMetrics:
        """
        Calculate comprehensive volatility metrics
        """
        metrics = VolatilityMetrics(timestamp=time.time())

        # Calculate realized volatility for each timeframe
        metrics.vol_1min = self._calculate_realized_vol(self.price_buffers['1s'], 60)
        metrics.vol_5min = self._calculate_realized_vol(self.price_buffers['5s'], 300)
        metrics.vol_15min = self._calculate_realized_vol(self.price_buffers['30s'], 900)
        metrics.vol_1h = self._calculate_realized_vol(self.price_buffers['1m'], 3600)

        # Calculate volatility acceleration (is vol increasing?)
        if len(self.vol_history_24h) > 2:
            recent_vols = list(self.vol_history_24h)[-3:]
            metrics.vol_acceleration = (recent_vols[-1] - recent_vols[0]) / len(recent_vols)

        # Calculate dispersion (disagreement between timeframes)
        vols = [metrics.vol_1min, metrics.vol_5min, metrics.vol_15min]
        if vols:
            metrics.vol_dispersion = np.std(vols) / np.mean(vols) if np.mean(vols) > 0 else 0

        # Update history
        self.vol_history_24h.append(metrics.vol_5min)

        # Calculate percentile and z-score
        if len(self.vol_history_24h) > 10:
            vols_array = np.array(list(self.vol_history_24h))
            metrics.vol_percentile_24h = np.percentile(vols_array,
                                                       np.searchsorted(np.sort(vols_array),
                                                                      metrics.vol_5min))
            metrics.vol_zscore = (metrics.vol_5min - np.mean(vols_array)) / np.std(vols_array)

        # Determine regime
        metrics.regime = self._classify_regime(metrics.vol_5min)
        metrics.regime_change = (metrics.regime != self.current_regime)

        if metrics.regime_change:
            self.current_regime = metrics.regime
            self.regime_history.append({'time': time.time(), 'regime': metrics.regime})

        # Calculate cascade risk multiplier
        metrics.cascade_risk_multiplier = self._calculate_cascade_risk(metrics)

        return metrics

    def _calculate_realized_vol(self, buffer: deque, window_seconds: float) -> float:
        """
        Calculate realized volatility using Garman-Klass or simple returns
        """
        if len(buffer) < 2:
            return 0.0

        # Get prices within window
        current_time = time.time()
        prices = [p['price'] for p in buffer if current_time - p['time'] <= window_seconds]

        if len(prices) < 2:
            return 0.0

        # Calculate returns
        returns = np.diff(np.log(prices))

        if len(returns) == 0:
            return 0.0

        # Annualized volatility (crypto trades 24/7)
        periods_per_year = 365 * 24 * 3600 / window_seconds
        vol = np.std(returns) * np.sqrt(periods_per_year)

        return vol

    def _classify_regime(self, vol_5min: float) -> VolatilityRegime:
        """
        Classify current volatility regime based on 5-minute vol
        """
        # These thresholds are calibrated from historical BTC data
        if vol_5min < 0.005:  # <0.5%
            return VolatilityRegime.DORMANT
        elif vol_5min < 0.01:  # <1%
            return VolatilityRegime.LOW
        elif vol_5min < 0.02:  # <2%
            return VolatilityRegime.NORMAL
        elif vol_5min < 0.03:  # <3%
            return VolatilityRegime.ELEVATED
        elif vol_5min < 0.05:  # <5%
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME

    def _calculate_cascade_risk(self, metrics: VolatilityMetrics) -> float:
        """
        Calculate cascade risk multiplier based on volatility metrics
        This amplifies or dampens cascade signals
        """
        risk = 1.0

        # Base multiplier from regime
        risk = self.cascade_thresholds[metrics.regime]

        # Adjust for volatility acceleration
        if metrics.vol_acceleration > 0:
            risk *= (1 + metrics.vol_acceleration * 10)  # Increasing vol = higher risk

        # Adjust for extreme percentiles
        if metrics.vol_percentile_24h > 95:
            risk *= 1.5  # Top 5% volatility
        elif metrics.vol_percentile_24h > 90:
            risk *= 1.2  # Top 10% volatility

        # Adjust for dispersion (timeframe disagreement = uncertainty)
        if metrics.vol_dispersion > 0.5:
            risk *= 1.3  # High disagreement = higher risk

        # Z-score adjustment
        if abs(metrics.vol_zscore) > 3:
            risk *= 2.0  # 3+ standard deviations = extreme
        elif abs(metrics.vol_zscore) > 2:
            risk *= 1.5  # 2+ standard deviations = unusual

        return min(10.0, risk)  # Cap at 10x

    def update_liquidations(self, liquidation_volume: float, timeframe: str = '1m'):
        """
        Update liquidation-based volatility
        Large liquidations increase effective volatility
        """
        self.liq_buffers[timeframe].append({
            'time': time.time(),
            'volume': liquidation_volume
        })

    def get_signal_adjustment(self) -> Dict[str, float]:
        """
        Get signal adjustments based on current volatility regime
        Used to tune cascade detection sensitivity
        """
        metrics = self.calculate_metrics()

        adjustments = {
            'velocity_threshold_multiplier': 1.0,
            'volume_threshold_multiplier': 1.0,
            'correlation_threshold_adjustment': 0.0,
            'timeframe_weight_adjustment': {}
        }

        # In high volatility, increase thresholds to reduce false positives
        if metrics.regime == VolatilityRegime.EXTREME:
            adjustments['velocity_threshold_multiplier'] = 2.0
            adjustments['volume_threshold_multiplier'] = 1.5
            adjustments['correlation_threshold_adjustment'] = 0.1
            # Weight faster timeframes more in extreme volatility
            adjustments['timeframe_weight_adjustment'] = {
                'ultra_fast': 1.5,
                'fast': 1.3,
                'normal': 1.0,
                'medium': 0.8,
                'slow': 0.6
            }
        elif metrics.regime == VolatilityRegime.HIGH:
            adjustments['velocity_threshold_multiplier'] = 1.5
            adjustments['volume_threshold_multiplier'] = 1.2
        elif metrics.regime == VolatilityRegime.DORMANT:
            # In low volatility, decrease thresholds to catch smaller moves
            adjustments['velocity_threshold_multiplier'] = 0.5
            adjustments['volume_threshold_multiplier'] = 0.7
            adjustments['correlation_threshold_adjustment'] = -0.1
            # Weight slower timeframes more in low volatility
            adjustments['timeframe_weight_adjustment'] = {
                'ultra_fast': 0.7,
                'fast': 0.9,
                'normal': 1.0,
                'medium': 1.2,
                'slow': 1.3
            }

        return adjustments

    def get_market_context_string(self) -> str:
        """
        Get human-readable market context for logging/alerts
        """
        metrics = self.calculate_metrics()

        context = f"""
        🎯 BTC VOLATILITY CONTEXT:
        ├─ Regime: {metrics.regime.name}
        ├─ 1min Vol: {metrics.vol_1min:.2%}
        ├─ 5min Vol: {metrics.vol_5min:.2%}
        ├─ 15min Vol: {metrics.vol_15min:.2%}
        ├─ 1h Vol: {metrics.vol_1h:.2%}
        ├─ Acceleration: {metrics.vol_acceleration:+.4f}
        ├─ 24h Percentile: {metrics.vol_percentile_24h:.0f}%
        ├─ Z-Score: {metrics.vol_zscore:+.2f}σ
        └─ Cascade Risk: {metrics.cascade_risk_multiplier:.1f}x
        """

        return context


# Integration example
class VolatilityAwareCascadeDetector:
    """
    Example of how to integrate volatility with cascade detection
    """

    def __init__(self):
        self.volatility_engine = BTCVolatilityEngine()
        # Your existing cascade detector
        # self.cascade_detector = ProfessionalCascadeDetector()

    async def process_price_update(self, btc_price: float):
        """
        Update volatility on every BTC price tick
        """
        vol_metrics = self.volatility_engine.update_price(btc_price)

        # Adjust cascade detection based on volatility
        if vol_metrics.regime_change:
            print(f"⚠️ REGIME CHANGE: {self.volatility_engine.current_regime.name}")
            # Adjust thresholds
            adjustments = self.volatility_engine.get_signal_adjustment()
            # Apply to cascade detector
            # self.cascade_detector.apply_adjustments(adjustments)

        return vol_metrics

    async def process_liquidation_with_context(self, liquidation_event: dict):
        """
        Process liquidation with volatility context
        """
        # Get current volatility context
        vol_metrics = self.volatility_engine.calculate_metrics()

        # Adjust cascade probability based on volatility
        # base_probability = await self.cascade_detector.process(liquidation_event)
        # adjusted_probability = base_probability * vol_metrics.cascade_risk_multiplier

        # Return signal with context
        # return {
        #     'cascade_probability': adjusted_probability,
        #     'volatility_regime': vol_metrics.regime.name,
        #     'risk_multiplier': vol_metrics.cascade_risk_multiplier
        # }
        pass


if __name__ == "__main__":
    # Test the volatility engine
    engine = BTCVolatilityEngine()

    # Simulate price movements
    import random

    btc_price = 40000
    for i in range(100):
        # Simulate price with increasing volatility
        volatility = 0.001 * (1 + i/50)  # Gradually increase volatility
        btc_price *= (1 + random.gauss(0, volatility))

        metrics = engine.update_price(btc_price)

        if i % 20 == 0:
            print(f"\nUpdate {i}:")
            print(f"Price: ${btc_price:.2f}")
            print(f"5min Vol: {metrics.vol_5min:.2%}")
            print(f"Regime: {metrics.regime.name}")
            print(f"Cascade Risk: {metrics.cascade_risk_multiplier:.1f}x")

    # Show final context
    print("\n" + "="*50)
    print(engine.get_market_context_string())