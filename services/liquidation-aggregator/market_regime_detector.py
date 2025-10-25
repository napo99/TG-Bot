#!/usr/bin/env python3
"""
MARKET REGIME DETECTOR
Advanced market state classification for adaptive cascade detection

Features:
- Multi-dimensional regime classification
- Volatility-based regime detection
- Liquidity regime analysis
- Trend/momentum regime detection
- Adaptive threshold adjustment based on regime
- Real-time regime change detection

Regimes:
- DORMANT: Very low activity, tight ranges
- LOW: Below average volatility and volume
- NORMAL: Average market conditions
- ELEVATED: Above average activity
- HIGH: High volatility and volume
- EXTREME: Exceptional market conditions
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import numpy as np

try:
    import redis.asyncio as redis
except ImportError:
    import redis

from btc_volatility_engine import BTCVolatilityEngine, VolatilityRegime


# =============================================================================
# CONFIGURATION
# =============================================================================

# Redis keys
REGIME_KEY = 'regime:current'
REGIME_HISTORY_KEY = 'regime:history'

# Logging
logger = logging.getLogger('market_regime_detector')
logger.setLevel(logging.INFO)


# =============================================================================
# DATA MODELS
# =============================================================================

class MarketRegime(Enum):
    """Composite market regime states"""
    DORMANT = 0      # Very low volatility and volume
    LOW = 1          # Below average activity
    NORMAL = 2       # Average market conditions
    ELEVATED = 3     # Above average activity
    HIGH = 4         # High volatility/volume
    EXTREME = 5      # Exceptional conditions


class LiquidityRegime(Enum):
    """Market liquidity states"""
    DEEP = 0        # High liquidity, tight spreads
    NORMAL = 1      # Average liquidity
    SHALLOW = 2     # Low liquidity, wide spreads
    ILLIQUID = 3    # Very poor liquidity


class TrendRegime(Enum):
    """Market trend states"""
    STRONG_DOWN = 0
    DOWN = 1
    RANGING = 2
    UP = 3
    STRONG_UP = 4


@dataclass
class RegimeMetrics:
    """Comprehensive market regime metrics"""
    timestamp: float

    # Primary regime
    market_regime: MarketRegime = MarketRegime.NORMAL
    regime_confidence: float = 0.5

    # Sub-regimes
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL
    liquidity_regime: LiquidityRegime = LiquidityRegime.NORMAL
    trend_regime: TrendRegime = TrendRegime.RANGING

    # Regime change detection
    regime_changed: bool = False
    time_in_regime: float = 0.0

    # Adaptive thresholds
    velocity_threshold_multiplier: float = 1.0
    volume_threshold_multiplier: float = 1.0
    cascade_sensitivity: float = 1.0

    # Context
    btc_price: float = 0.0
    volume_24h_percentile: float = 50.0
    volatility_24h_percentile: float = 50.0

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'timestamp': self.timestamp,
            'market_regime': self.market_regime.name,
            'regime_confidence': round(self.regime_confidence, 3),
            'volatility_regime': self.volatility_regime.name,
            'liquidity_regime': self.liquidity_regime.name,
            'trend_regime': self.trend_regime.name,
            'regime_changed': self.regime_changed,
            'time_in_regime': round(self.time_in_regime, 1),
            'thresholds': {
                'velocity_multiplier': round(self.velocity_threshold_multiplier, 2),
                'volume_multiplier': round(self.volume_threshold_multiplier, 2),
                'cascade_sensitivity': round(self.cascade_sensitivity, 2)
            },
            'context': {
                'btc_price': round(self.btc_price, 2),
                'volume_24h_percentile': round(self.volume_24h_percentile, 1),
                'volatility_24h_percentile': round(self.volatility_24h_percentile, 1)
            }
        }


# =============================================================================
# MARKET REGIME DETECTOR
# =============================================================================

class MarketRegimeDetector:
    """
    Professional market regime detection
    Combines multiple signals for robust regime classification
    """

    def __init__(self, volatility_engine: Optional[BTCVolatilityEngine] = None):
        """
        Initialize market regime detector

        Args:
            volatility_engine: Optional BTC volatility engine
        """
        self.volatility_engine = volatility_engine or BTCVolatilityEngine()

        # Regime state
        self.current_regime = MarketRegime.NORMAL
        self.regime_start_time = time.time()
        self.regime_history = deque(maxlen=100)

        # Volume tracking for liquidity regime
        self.volume_history_24h = deque(maxlen=288)  # 5min intervals for 24h
        self.spread_history = deque(maxlen=60)  # 1min intervals for 1h

        # Price tracking for trend regime
        self.price_history = deque(maxlen=100)

        # Statistics
        self.regime_changes = 0
        self.time_in_regimes = {regime: 0.0 for regime in MarketRegime}

        logger.info("✅ MarketRegimeDetector initialized")

    def update(self,
               btc_price: Optional[float] = None,
               volume_usd: Optional[float] = None,
               spread_bps: Optional[float] = None) -> RegimeMetrics:
        """
        Update regime detection with new data

        Args:
            btc_price: Current BTC price
            volume_usd: Current trading volume (USD)
            spread_bps: Current bid-ask spread in basis points

        Returns:
            RegimeMetrics with current regime classification
        """
        current_time = time.time()

        # Update volatility engine
        if btc_price:
            self.volatility_engine.update_price(btc_price, current_time)
            self.price_history.append({'price': btc_price, 'time': current_time})

        # Update volume history
        if volume_usd:
            self.volume_history_24h.append({'volume': volume_usd, 'time': current_time})

        # Update spread history
        if spread_bps:
            self.spread_history.append({'spread': spread_bps, 'time': current_time})

        # Get volatility metrics
        vol_metrics = self.volatility_engine.calculate_metrics()

        # Detect liquidity regime
        liquidity_regime = self._detect_liquidity_regime()

        # Detect trend regime
        trend_regime = self._detect_trend_regime()

        # Detect composite market regime
        market_regime, confidence = self._detect_market_regime(
            vol_metrics,
            liquidity_regime,
            trend_regime
        )

        # Check for regime change
        regime_changed = (market_regime != self.current_regime)

        if regime_changed:
            self.regime_changes += 1
            # Update time in old regime
            time_in_old_regime = current_time - self.regime_start_time
            self.time_in_regimes[self.current_regime] += time_in_old_regime

            logger.info(
                f"🔄 Regime Change: {self.current_regime.name} → {market_regime.name} "
                f"(after {time_in_old_regime:.1f}s)"
            )

            self.current_regime = market_regime
            self.regime_start_time = current_time

        # Calculate time in current regime
        time_in_regime = current_time - self.regime_start_time

        # Get adaptive thresholds
        thresholds = self._get_adaptive_thresholds(market_regime, vol_metrics)

        # Calculate percentiles
        vol_percentile = vol_metrics.vol_percentile_24h if hasattr(vol_metrics, 'vol_percentile_24h') else 50.0
        volume_percentile = self._calculate_volume_percentile()

        # Create metrics
        metrics = RegimeMetrics(
            timestamp=current_time,
            market_regime=market_regime,
            regime_confidence=confidence,
            volatility_regime=vol_metrics.regime,
            liquidity_regime=liquidity_regime,
            trend_regime=trend_regime,
            regime_changed=regime_changed,
            time_in_regime=time_in_regime,
            velocity_threshold_multiplier=thresholds['velocity_multiplier'],
            volume_threshold_multiplier=thresholds['volume_multiplier'],
            cascade_sensitivity=thresholds['cascade_sensitivity'],
            btc_price=btc_price or 0.0,
            volume_24h_percentile=volume_percentile,
            volatility_24h_percentile=vol_percentile
        )

        # Store in history
        self.regime_history.append(metrics)

        return metrics

    def _detect_liquidity_regime(self) -> LiquidityRegime:
        """
        Detect liquidity regime based on volume and spreads

        Uses volume depth and bid-ask spread as proxies
        """
        if len(self.volume_history_24h) < 10:
            return LiquidityRegime.NORMAL

        # Get recent volume
        current_time = time.time()
        recent_volumes = [
            v['volume'] for v in self.volume_history_24h
            if current_time - v['time'] <= 3600  # Last hour
        ]

        if not recent_volumes:
            return LiquidityRegime.NORMAL

        avg_volume = np.mean(recent_volumes)
        volume_std = np.std(recent_volumes)

        # Get recent spreads if available
        avg_spread = None
        if len(self.spread_history) > 0:
            recent_spreads = [
                s['spread'] for s in self.spread_history
                if current_time - s['time'] <= 600  # Last 10 minutes
            ]
            if recent_spreads:
                avg_spread = np.mean(recent_spreads)

        # Classify based on volume and spreads
        # High volume + tight spreads = DEEP
        # Low volume + wide spreads = ILLIQUID

        if avg_spread is not None:
            if avg_volume > np.percentile(recent_volumes, 75) and avg_spread < 5:
                return LiquidityRegime.DEEP
            elif avg_volume < np.percentile(recent_volumes, 25) and avg_spread > 20:
                return LiquidityRegime.ILLIQUID
            elif avg_spread > 15:
                return LiquidityRegime.SHALLOW
        else:
            # Volume-only classification
            if avg_volume > np.percentile(recent_volumes, 75):
                return LiquidityRegime.DEEP
            elif avg_volume < np.percentile(recent_volumes, 25):
                return LiquidityRegime.SHALLOW

        return LiquidityRegime.NORMAL

    def _detect_trend_regime(self) -> TrendRegime:
        """
        Detect trend regime using price momentum

        Uses simple moving average crossover and momentum
        """
        if len(self.price_history) < 20:
            return TrendRegime.RANGING

        prices = [p['price'] for p in self.price_history]

        # Calculate short and long moving averages
        short_ma = np.mean(prices[-10:])  # 10-period MA
        long_ma = np.mean(prices[-20:])   # 20-period MA

        # Calculate momentum
        momentum = (prices[-1] - prices[-10]) / prices[-10] if prices[-10] > 0 else 0

        # Calculate volatility
        returns = np.diff(np.log(prices))
        volatility = np.std(returns)

        # Classify trend
        # Strong trend: MA crossover + high momentum
        # Ranging: Small momentum + low volatility

        trend_strength = abs(momentum)

        if momentum > 0.02 and short_ma > long_ma:  # 2% up
            return TrendRegime.STRONG_UP if trend_strength > 0.05 else TrendRegime.UP
        elif momentum < -0.02 and short_ma < long_ma:  # 2% down
            return TrendRegime.STRONG_DOWN if trend_strength > 0.05 else TrendRegime.DOWN

        return TrendRegime.RANGING

    def _detect_market_regime(self,
                             vol_metrics,
                             liquidity_regime: LiquidityRegime,
                             trend_regime: TrendRegime) -> Tuple[MarketRegime, float]:
        """
        Detect composite market regime from sub-regimes

        Returns:
            Tuple of (MarketRegime, confidence)
        """
        # Start with volatility regime as primary signal
        vol_regime = vol_metrics.regime

        # Map volatility regime to market regime
        regime_mapping = {
            VolatilityRegime.DORMANT: MarketRegime.DORMANT,
            VolatilityRegime.LOW: MarketRegime.LOW,
            VolatilityRegime.NORMAL: MarketRegime.NORMAL,
            VolatilityRegime.ELEVATED: MarketRegime.ELEVATED,
            VolatilityRegime.HIGH: MarketRegime.HIGH,
            VolatilityRegime.EXTREME: MarketRegime.EXTREME
        }

        base_regime = regime_mapping.get(vol_regime, MarketRegime.NORMAL)
        confidence = 0.5

        # Adjust regime based on liquidity
        if liquidity_regime == LiquidityRegime.ILLIQUID:
            # Illiquid markets amplify volatility impact
            if base_regime.value < MarketRegime.EXTREME.value:
                base_regime = MarketRegime(base_regime.value + 1)
            confidence += 0.2

        elif liquidity_regime == LiquidityRegime.DEEP:
            # Deep liquidity dampens volatility impact
            if base_regime.value > MarketRegime.DORMANT.value:
                base_regime = MarketRegime(base_regime.value - 1)
            confidence += 0.1

        # Adjust regime based on trend
        if trend_regime in [TrendRegime.STRONG_UP, TrendRegime.STRONG_DOWN]:
            # Strong trends increase regime severity
            if base_regime.value < MarketRegime.HIGH.value:
                confidence += 0.2
        elif trend_regime == TrendRegime.RANGING:
            # Ranging markets are more stable
            confidence += 0.1

        # Ensure confidence is in valid range
        confidence = min(1.0, max(0.3, confidence))

        return base_regime, confidence

    def _get_adaptive_thresholds(self,
                                regime: MarketRegime,
                                vol_metrics) -> Dict[str, float]:
        """
        Get adaptive thresholds based on market regime

        Higher thresholds in volatile markets (reduce false positives)
        Lower thresholds in calm markets (increase sensitivity)
        """
        # Base thresholds
        thresholds = {
            'velocity_multiplier': 1.0,
            'volume_multiplier': 1.0,
            'cascade_sensitivity': 1.0
        }

        # Adjust based on regime
        if regime == MarketRegime.EXTREME:
            thresholds['velocity_multiplier'] = 2.5
            thresholds['volume_multiplier'] = 2.0
            thresholds['cascade_sensitivity'] = 0.5  # Less sensitive
        elif regime == MarketRegime.HIGH:
            thresholds['velocity_multiplier'] = 1.8
            thresholds['volume_multiplier'] = 1.5
            thresholds['cascade_sensitivity'] = 0.7
        elif regime == MarketRegime.ELEVATED:
            thresholds['velocity_multiplier'] = 1.3
            thresholds['volume_multiplier'] = 1.2
            thresholds['cascade_sensitivity'] = 0.9
        elif regime == MarketRegime.DORMANT:
            thresholds['velocity_multiplier'] = 0.5
            thresholds['volume_multiplier'] = 0.6
            thresholds['cascade_sensitivity'] = 1.5  # More sensitive
        elif regime == MarketRegime.LOW:
            thresholds['velocity_multiplier'] = 0.7
            thresholds['volume_multiplier'] = 0.8
            thresholds['cascade_sensitivity'] = 1.2

        # Apply volatility-specific adjustments ONLY if we have sufficient volatility data
        # This prevents default/empty volatility engine from incorrectly dampening regime-based thresholds
        if hasattr(vol_metrics, 'vol_5min') and vol_metrics.vol_5min > 0:
            vol_adjustments = self.volatility_engine.get_signal_adjustment()
            thresholds['velocity_multiplier'] *= vol_adjustments.get('velocity_threshold_multiplier', 1.0)
            thresholds['volume_multiplier'] *= vol_adjustments.get('volume_threshold_multiplier', 1.0)

        return thresholds

    def _calculate_volume_percentile(self) -> float:
        """Calculate current volume percentile vs 24h history"""
        if len(self.volume_history_24h) < 10:
            return 50.0

        volumes = [v['volume'] for v in self.volume_history_24h]
        current_volume = volumes[-1] if volumes else 0

        if current_volume == 0:
            return 0.0

        # Calculate percentile
        percentile = (sum(1 for v in volumes if v <= current_volume) / len(volumes)) * 100

        return percentile

    def get_regime_summary(self) -> dict:
        """Get comprehensive regime summary"""
        current_time = time.time()
        time_in_regime = current_time - self.regime_start_time

        return {
            'current_regime': self.current_regime.name,
            'time_in_regime_seconds': round(time_in_regime, 1),
            'regime_changes': self.regime_changes,
            'regime_distribution': {
                regime.name: round(duration, 1)
                for regime, duration in self.time_in_regimes.items()
            },
            'recent_regimes': [
                {
                    'regime': m.market_regime.name,
                    'confidence': round(m.regime_confidence, 2),
                    'timestamp': m.timestamp
                }
                for m in list(self.regime_history)[-10:]
            ]
        }

    def get_trading_adjustments(self) -> dict:
        """
        Get trading parameter adjustments based on current regime

        Used by trading strategies to adapt to market conditions
        """
        if not self.regime_history:
            return {'position_size_multiplier': 1.0, 'stop_loss_multiplier': 1.0}

        latest = self.regime_history[-1]

        adjustments = {
            'position_size_multiplier': 1.0,
            'stop_loss_multiplier': 1.0,
            'take_profit_multiplier': 1.0,
            'entry_aggressiveness': 1.0
        }

        # Adjust based on market regime
        regime = latest.market_regime

        if regime == MarketRegime.EXTREME:
            # Reduce position size, widen stops in extreme volatility
            adjustments['position_size_multiplier'] = 0.3
            adjustments['stop_loss_multiplier'] = 2.0
            adjustments['take_profit_multiplier'] = 1.5
            adjustments['entry_aggressiveness'] = 0.5
        elif regime == MarketRegime.HIGH:
            adjustments['position_size_multiplier'] = 0.5
            adjustments['stop_loss_multiplier'] = 1.5
            adjustments['take_profit_multiplier'] = 1.3
            adjustments['entry_aggressiveness'] = 0.7
        elif regime == MarketRegime.DORMANT:
            # Can take larger positions with tighter stops in low vol
            adjustments['position_size_multiplier'] = 1.5
            adjustments['stop_loss_multiplier'] = 0.7
            adjustments['take_profit_multiplier'] = 0.8
            adjustments['entry_aggressiveness'] = 1.3

        # Adjust based on liquidity
        if latest.liquidity_regime == LiquidityRegime.ILLIQUID:
            adjustments['position_size_multiplier'] *= 0.7
            adjustments['entry_aggressiveness'] *= 0.6
        elif latest.liquidity_regime == LiquidityRegime.DEEP:
            adjustments['position_size_multiplier'] *= 1.2
            adjustments['entry_aggressiveness'] *= 1.1

        return adjustments


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'MarketRegimeDetector',
    'MarketRegime',
    'LiquidityRegime',
    'TrendRegime',
    'RegimeMetrics'
]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import random

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create detector
    detector = MarketRegimeDetector()

    # Simulate price movements
    btc_price = 40000
    print("🎯 Market Regime Detection Test\n")

    for i in range(50):
        # Simulate varying volatility
        if i < 15:
            # Low volatility period
            volatility = 0.0005
        elif i < 30:
            # Normal volatility
            volatility = 0.002
        else:
            # High volatility period
            volatility = 0.01

        # Update price
        btc_price *= (1 + random.gauss(0, volatility))

        # Simulate volume
        volume_usd = random.uniform(1_000_000, 10_000_000) * (1 + volatility * 100)

        # Update detector
        metrics = detector.update(btc_price=btc_price, volume_usd=volume_usd)

        # Print on regime changes
        if metrics.regime_changed or i % 10 == 0:
            print(f"\n[Update {i}]")
            print(f"Price: ${btc_price:,.2f}")
            print(f"Regime: {metrics.market_regime.name} (confidence: {metrics.regime_confidence:.2f})")
            print(f"Volatility: {metrics.volatility_regime.name}")
            print(f"Liquidity: {metrics.liquidity_regime.name}")
            print(f"Trend: {metrics.trend_regime.name}")
            print(f"Cascade Sensitivity: {metrics.cascade_sensitivity:.2f}x")

    # Final summary
    print("\n" + "="*60)
    print("📊 Final Regime Summary:")
    summary = detector.get_regime_summary()
    print(f"Current Regime: {summary['current_regime']}")
    print(f"Time in Regime: {summary['time_in_regime_seconds']:.1f}s")
    print(f"Total Regime Changes: {summary['regime_changes']}")

    # Trading adjustments
    print("\n💹 Trading Adjustments:")
    adjustments = detector.get_trading_adjustments()
    for key, value in adjustments.items():
        print(f"  {key}: {value:.2f}x")
