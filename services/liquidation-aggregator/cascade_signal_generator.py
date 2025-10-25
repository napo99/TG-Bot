#!/usr/bin/env python3
"""
CASCADE SIGNAL GENERATOR
Professional-grade cascade signal generation integrating multiple data sources

Features:
- Multi-factor cascade scoring (velocity, acceleration, volume, OI, funding, volatility)
- Real-time signal generation (<10ms latency target)
- Redis pub/sub for signal distribution
- Volatility-aware threshold adjustments
- Market regime integration
- Exchange correlation analysis

Architecture:
┌─────────────────────────────────────────────────────────┐
│            Cascade Signal Generator                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Velocity    │  │  Volatility  │  │   Funding    │ │
│  │  Tracker     │  │   Engine     │  │   Rates      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            ▼                            │
│                  ┌──────────────────┐                   │
│                  │ Multi-Factor     │                   │
│                  │ Scoring Engine   │                   │
│                  └────────┬─────────┘                   │
│                           ▼                             │
│                  ┌──────────────────┐                   │
│                  │ Signal Publisher │                   │
│                  │ (Redis Pub/Sub)  │                   │
│                  └──────────────────┘                   │
└─────────────────────────────────────────────────────────┘
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
import numpy as np

try:
    import redis.asyncio as redis
except ImportError:
    import redis

# Import existing components
from btc_volatility_engine import BTCVolatilityEngine, VolatilityRegime, VolatilityMetrics
from professional_cascade_detector import (
    ProfessionalCascadeDetector,
    CascadeSignal,
    LiquidationMetrics
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 1

# Redis channels
SIGNAL_CHANNEL = 'cascade:signals'
CRITICAL_SIGNAL_CHANNEL = 'cascade:critical'
ALERT_CHANNEL = 'cascade:alerts'

# Redis keys
VELOCITY_KEY_PREFIX = 'velocity:'
VOLATILITY_KEY = 'volatility:btc:current'
REGIME_KEY = 'regime:current'
CASCADE_PROB_PREFIX = 'cascade:probability:'
FUNDING_KEY_PREFIX = 'funding:'
OI_KEY_PREFIX = 'oi:'

# Signal generation thresholds
SIGNAL_THRESHOLDS = {
    CascadeSignal.WATCH: 0.30,      # 30% probability
    CascadeSignal.ALERT: 0.50,      # 50% probability
    CascadeSignal.CRITICAL: 0.70,   # 70% probability
    CascadeSignal.EXTREME: 0.90     # 90% probability
}

# Scoring weights (calibrated for crypto markets)
DEFAULT_WEIGHTS = {
    'velocity': 0.25,
    'acceleration': 0.20,
    'volume': 0.20,
    'oi_change': 0.15,
    'funding': 0.10,
    'volatility': 0.10
}

# Logging
logger = logging.getLogger('cascade_signal_generator')
logger.setLevel(logging.INFO)


# =============================================================================
# DATA MODELS
# =============================================================================

class SignalLevel(Enum):
    """Cascade signal severity levels"""
    NONE = 0
    WATCH = 1       # Early warning (30-50% probability)
    ALERT = 2       # Cascade forming (50-70% probability)
    CRITICAL = 3    # Cascade in progress (70-90% probability)
    EXTREME = 4     # Market-wide event (>90% probability)


@dataclass
class CascadeSignalData:
    """Complete cascade signal with all context"""
    # Identifiers
    symbol: str
    timestamp: float

    # Signal level
    signal: SignalLevel
    probability: float

    # Component scores (normalized 0-1)
    velocity_score: float = 0.0
    acceleration_score: float = 0.0
    volume_score: float = 0.0
    oi_change_score: float = 0.0
    funding_score: float = 0.0
    volatility_score: float = 0.0

    # Raw metrics
    velocity: float = 0.0
    acceleration: float = 0.0
    volume_usd: float = 0.0
    oi_change_1m: float = 0.0
    funding_rate: float = 0.0

    # Market context
    volatility_regime: str = "NORMAL"
    btc_price: float = 0.0
    vol_risk_multiplier: float = 1.0

    # Exchange info
    leading_exchange: Optional[str] = None
    exchange_correlation: float = 0.0

    # Metadata
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'signal': self.signal.name,
            'signal_level': self.signal.value,
            'probability': round(self.probability, 4),
            'scores': {
                'velocity': round(self.velocity_score, 3),
                'acceleration': round(self.acceleration_score, 3),
                'volume': round(self.volume_score, 3),
                'oi_change': round(self.oi_change_score, 3),
                'funding': round(self.funding_score, 3),
                'volatility': round(self.volatility_score, 3)
            },
            'metrics': {
                'velocity': round(self.velocity, 2),
                'acceleration': round(self.acceleration, 2),
                'volume_usd': round(self.volume_usd, 2),
                'oi_change_1m': round(self.oi_change_1m, 4),
                'funding_rate': round(self.funding_rate, 6)
            },
            'context': {
                'volatility_regime': self.volatility_regime,
                'btc_price': round(self.btc_price, 2),
                'vol_risk_multiplier': round(self.vol_risk_multiplier, 2),
                'leading_exchange': self.leading_exchange,
                'exchange_correlation': round(self.exchange_correlation, 3)
            },
            'meta': {
                'processing_time_ms': round(self.processing_time_ms, 2)
            }
        }


# =============================================================================
# CASCADE SIGNAL GENERATOR
# =============================================================================

class CascadeSignalGenerator:
    """
    Professional-grade cascade signal generator
    Integrates velocity, volatility, funding, OI, and market context
    """

    def __init__(self,
                 redis_client: Optional[redis.Redis] = None,
                 weights: Optional[Dict[str, float]] = None):
        """
        Initialize cascade signal generator

        Args:
            redis_client: Optional Redis client for metrics and publishing
            weights: Optional custom scoring weights
        """
        self.redis = redis_client
        self.weights = weights or DEFAULT_WEIGHTS.copy()

        # Initialize components
        self.volatility_engine = BTCVolatilityEngine()
        self.cascade_detector = ProfessionalCascadeDetector()

        # Signal history for adaptive thresholds
        self.signal_history = deque(maxlen=1000)

        # Statistics
        self.signals_generated = 0
        self.critical_signals = 0
        self.avg_processing_time_ms = 0.0

        logger.info("✅ CascadeSignalGenerator initialized")

    async def initialize(self, redis_config: Optional[Dict] = None):
        """Initialize Redis connection if not provided"""
        if not self.redis and redis_config:
            try:
                self.redis = await redis.Redis(**redis_config)
                await self.redis.ping()
                logger.info("✅ Connected to Redis")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                logger.warning("⚠️  Running in degraded mode (no Redis)")

    async def generate_signal(self,
                             symbol: str,
                             liquidation_metrics: Optional[LiquidationMetrics] = None) -> CascadeSignalData:
        """
        Generate cascade signal for a symbol

        Args:
            symbol: Trading symbol
            liquidation_metrics: Optional pre-calculated liquidation metrics

        Returns:
            CascadeSignalData with complete signal information
        """
        start_time = time.perf_counter()

        # Gather all metrics
        metrics = await self._gather_metrics(symbol, liquidation_metrics)

        # Calculate component scores
        scores = self._calculate_scores(metrics)

        # Calculate weighted probability
        probability = self._calculate_probability(scores)

        # Get volatility context
        vol_context = await self._get_volatility_context()

        # Adjust probability for volatility regime
        adjusted_probability = probability * vol_context['risk_multiplier']

        # Determine signal level
        signal_level = self._determine_signal_level(adjusted_probability, metrics)

        # Create signal
        processing_time = (time.perf_counter() - start_time) * 1000

        signal = CascadeSignalData(
            symbol=symbol,
            timestamp=time.time(),
            signal=signal_level,
            probability=adjusted_probability,
            velocity_score=scores['velocity'],
            acceleration_score=scores['acceleration'],
            volume_score=scores['volume'],
            oi_change_score=scores['oi_change'],
            funding_score=scores['funding'],
            volatility_score=scores['volatility'],
            velocity=metrics.get('velocity', 0.0),
            acceleration=metrics.get('acceleration', 0.0),
            volume_usd=metrics.get('volume_usd', 0.0),
            oi_change_1m=metrics.get('oi_change_1m', 0.0),
            funding_rate=metrics.get('funding_rate', 0.0),
            volatility_regime=vol_context['regime'],
            btc_price=vol_context['btc_price'],
            vol_risk_multiplier=vol_context['risk_multiplier'],
            leading_exchange=metrics.get('leading_exchange'),
            exchange_correlation=metrics.get('exchange_correlation', 0.0),
            processing_time_ms=processing_time
        )

        # Store signal
        self.signal_history.append(signal)
        self.signals_generated += 1

        if signal_level.value >= SignalLevel.CRITICAL.value:
            self.critical_signals += 1

        # Update running average processing time
        self.avg_processing_time_ms = (
            (self.avg_processing_time_ms * (self.signals_generated - 1) + processing_time)
            / self.signals_generated
        )

        # Publish signal
        await self._publish_signal(signal)

        # Store to Redis
        await self._store_signal(signal)

        # Log performance warning if slow
        if processing_time > 10:
            logger.warning(f"⚠️  Slow signal generation: {processing_time:.2f}ms")

        return signal

    async def _gather_metrics(self,
                             symbol: str,
                             liquidation_metrics: Optional[LiquidationMetrics]) -> Dict[str, float]:
        """Gather all metrics from Redis and components"""
        metrics = {}

        # Get velocity metrics from Redis or liquidation_metrics
        if liquidation_metrics:
            metrics['velocity'] = liquidation_metrics.events_per_second
            metrics['acceleration'] = liquidation_metrics.events_acceleration
            metrics['volume_usd'] = liquidation_metrics.volume_per_second
            metrics['leading_exchange'] = liquidation_metrics.leading_exchange
            metrics['exchange_correlation'] = liquidation_metrics.exchange_correlation
        elif self.redis:
            velocity_data = await self._get_velocity_from_redis(symbol)
            metrics.update(velocity_data)
        else:
            # Default values
            metrics['velocity'] = 0.0
            metrics['acceleration'] = 0.0
            metrics['volume_usd'] = 0.0

        # Get OI change from Redis
        if self.redis:
            oi_data = await self._get_oi_change_from_redis(symbol)
            metrics['oi_change_1m'] = oi_data.get('change_1m', 0.0)
        else:
            metrics['oi_change_1m'] = 0.0

        # Get funding rate from Redis
        if self.redis:
            funding_data = await self._get_funding_from_redis(symbol)
            metrics['funding_rate'] = funding_data.get('rate', 0.0)
        else:
            metrics['funding_rate'] = 0.0

        return metrics

    async def _get_velocity_from_redis(self, symbol: str) -> Dict[str, float]:
        """Get velocity metrics from Redis"""
        try:
            key = f"{VELOCITY_KEY_PREFIX}{symbol}:current"
            data = await self.redis.hgetall(key)

            if not data:
                return {'velocity': 0.0, 'acceleration': 0.0, 'volume_usd': 0.0}

            # Decode bytes to strings
            decoded = {k.decode(): float(v.decode()) for k, v in data.items()}

            return {
                'velocity': decoded.get('velocity_10s', 0.0),
                'acceleration': decoded.get('acceleration', 0.0),
                'volume_usd': decoded.get('total_value_usd', 0.0) / 10,  # Convert to per-second
                'exchange_correlation': decoded.get('exchange_correlation', 0.0),
                'leading_exchange': decoded.get('leading_exchange')
            }
        except Exception as e:
            logger.error(f"Error getting velocity from Redis: {e}")
            return {'velocity': 0.0, 'acceleration': 0.0, 'volume_usd': 0.0}

    async def _get_oi_change_from_redis(self, symbol: str) -> Dict[str, float]:
        """Get OI change from Redis"""
        try:
            key = f"{OI_KEY_PREFIX}{symbol}:change"
            data = await self.redis.get(key)

            if not data:
                return {'change_1m': 0.0}

            oi_data = json.loads(data)
            return {'change_1m': oi_data.get('change_1m', 0.0)}
        except Exception as e:
            logger.error(f"Error getting OI from Redis: {e}")
            return {'change_1m': 0.0}

    async def _get_funding_from_redis(self, symbol: str) -> Dict[str, float]:
        """Get funding rate from Redis"""
        try:
            key = f"{FUNDING_KEY_PREFIX}{symbol}:current"
            data = await self.redis.get(key)

            if not data:
                return {'rate': 0.0}

            funding_data = json.loads(data)
            return {'rate': funding_data.get('rate', 0.0)}
        except Exception as e:
            logger.error(f"Error getting funding from Redis: {e}")
            return {'rate': 0.0}

    async def _get_volatility_context(self) -> Dict[str, Any]:
        """Get volatility context from Redis or engine"""
        try:
            if self.redis:
                data = await self.redis.get(VOLATILITY_KEY)
                if data:
                    vol_data = json.loads(data)
                    return {
                        'regime': vol_data.get('regime', 'NORMAL'),
                        'btc_price': vol_data.get('btc_price', 0.0),
                        'risk_multiplier': vol_data.get('cascade_risk_multiplier', 1.0)
                    }

            # Fallback to engine calculation
            metrics = self.volatility_engine.calculate_metrics()
            return {
                'regime': metrics.regime.name,
                'btc_price': self.volatility_engine.last_price or 0.0,
                'risk_multiplier': metrics.cascade_risk_multiplier
            }
        except Exception as e:
            logger.error(f"Error getting volatility context: {e}")
            return {
                'regime': 'NORMAL',
                'btc_price': 0.0,
                'risk_multiplier': 1.0
            }

    def _calculate_scores(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate normalized scores (0-1) for each component

        Normalization based on professional trading thresholds
        Handles edge cases: zero, negative, NaN, inf values
        """
        import math

        def safe_normalize(value: float, threshold: float, use_abs: bool = False) -> float:
            """Safely normalize value, handling edge cases"""
            # Handle None
            if value is None:
                return 0.0

            # Convert to float if needed
            try:
                value = float(value)
            except (TypeError, ValueError):
                return 0.0

            # Handle NaN and inf
            if math.isnan(value) or math.isinf(value):
                return 0.0

            # Apply absolute value if requested
            if use_abs:
                value = abs(value)

            # Ensure non-negative (for values that should never be negative)
            if not use_abs:
                value = max(0.0, value)

            # Normalize
            if threshold <= 0:
                return 0.0

            return min(1.0, value / threshold)

        scores = {}

        # Velocity score (0-50 events/s range, must be positive)
        scores['velocity'] = safe_normalize(metrics.get('velocity', 0.0), 50.0, use_abs=False)

        # Acceleration score (0-20 events/s² range, use absolute value)
        scores['acceleration'] = safe_normalize(metrics.get('acceleration', 0.0), 20.0, use_abs=True)

        # Volume score (0-$50M/s range, must be positive)
        scores['volume'] = safe_normalize(metrics.get('volume_usd', 0.0), 50_000_000.0, use_abs=False)

        # OI change score (0-5% range, use absolute value)
        scores['oi_change'] = safe_normalize(metrics.get('oi_change_1m', 0.0), 0.05, use_abs=True)

        # Funding pressure score (0-0.1% range, use absolute value)
        scores['funding'] = safe_normalize(metrics.get('funding_rate', 0.0), 0.001, use_abs=True)

        # Volatility score (from risk multiplier, 0-5x range)
        vol_multiplier = metrics.get('vol_risk_multiplier', 1.0)
        scores['volatility'] = safe_normalize(vol_multiplier, 5.0, use_abs=False)

        return scores

    def _calculate_probability(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted cascade probability from component scores

        Uses professional trading weights calibrated for crypto markets
        """
        probability = 0.0

        for component, score in scores.items():
            weight = self.weights.get(component, 0.0)
            probability += score * weight

        # Apply non-linear scaling for extreme events
        if scores.get('acceleration', 0.0) > 0.8 and scores.get('velocity', 0.0) > 0.7:
            probability = min(1.0, probability * 1.5)

        # Apply correlation boost
        correlation = scores.get('exchange_correlation', 0.0)
        if correlation > 0.7:
            probability = min(1.0, probability * 1.2)

        return min(1.0, max(0.0, probability))

    def _determine_signal_level(self,
                                probability: float,
                                metrics: Dict[str, float]) -> SignalLevel:
        """
        Determine signal level based on probability and metrics

        Uses multi-factor conditions for robustness
        Uses absolute values for acceleration (can be positive or negative)
        """
        # EXTREME: Multiple extreme conditions
        if (probability > SIGNAL_THRESHOLDS[CascadeSignal.EXTREME] or
            (metrics.get('velocity', 0.0) > 100 and  # 100 events/s
             abs(metrics.get('acceleration', 0.0)) > 40)):  # 40 events/s²
            return SignalLevel.EXTREME

        # CRITICAL: High probability or combined extreme conditions
        if (probability > SIGNAL_THRESHOLDS[CascadeSignal.CRITICAL] or
            (metrics.get('velocity', 0.0) > 50 and
             abs(metrics.get('acceleration', 0.0)) > 20)):
            return SignalLevel.CRITICAL

        # ALERT: Moderate probability or high velocity
        if (probability > SIGNAL_THRESHOLDS[CascadeSignal.ALERT] or
            metrics.get('velocity', 0.0) > 20):
            return SignalLevel.ALERT

        # WATCH: Low probability or elevated velocity
        if (probability > SIGNAL_THRESHOLDS[CascadeSignal.WATCH] or
            metrics.get('velocity', 0.0) > 10):
            return SignalLevel.WATCH

        return SignalLevel.NONE

    async def _publish_signal(self, signal: CascadeSignalData):
        """Publish signal to Redis pub/sub channels"""
        if not self.redis:
            return

        try:
            signal_json = json.dumps(signal.to_dict())

            # Publish to main channel
            await self.redis.publish(SIGNAL_CHANNEL, signal_json)

            # Publish to critical channel if needed
            if signal.signal.value >= SignalLevel.CRITICAL.value:
                await self.redis.publish(CRITICAL_SIGNAL_CHANNEL, signal_json)

            # Publish to alert channel if needed
            if signal.signal.value >= SignalLevel.ALERT.value:
                await self.redis.publish(ALERT_CHANNEL, signal_json)

            logger.debug(f"Published signal: {signal.symbol} - {signal.signal.name}")

        except Exception as e:
            logger.error(f"Error publishing signal: {e}")

    async def _store_signal(self, signal: CascadeSignalData):
        """Store signal to Redis for historical analysis"""
        if not self.redis:
            return

        try:
            # Store current probability
            key = f"{CASCADE_PROB_PREFIX}{signal.symbol}"
            await self.redis.setex(
                key,
                60,  # 1 minute TTL
                json.dumps({
                    'probability': signal.probability,
                    'signal': signal.signal.name,
                    'timestamp': signal.timestamp
                })
            )

            # Store in time-series for analysis (sorted set by timestamp)
            if signal.signal.value >= SignalLevel.ALERT.value:
                ts_key = f"cascade:signals:history:{signal.symbol}"
                await self.redis.zadd(
                    ts_key,
                    {json.dumps(signal.to_dict()): signal.timestamp}
                )
                # Keep last 1000 signals
                await self.redis.zremrangebyrank(ts_key, 0, -1001)

        except Exception as e:
            logger.error(f"Error storing signal: {e}")

    def update_weights(self, new_weights: Dict[str, float]):
        """Update scoring weights (for adaptive tuning)"""
        # Validate weights sum to 1.0
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing...")
            new_weights = {k: v/total for k, v in new_weights.items()}

        self.weights = new_weights
        logger.info(f"Updated weights: {self.weights}")

    def get_stats(self) -> dict:
        """Get signal generator statistics"""
        return {
            'signals_generated': self.signals_generated,
            'critical_signals': self.critical_signals,
            'critical_rate': self.critical_signals / max(1, self.signals_generated),
            'avg_processing_time_ms': round(self.avg_processing_time_ms, 2),
            'current_weights': self.weights,
            'recent_signals': [
                {
                    'symbol': s.symbol,
                    'signal': s.signal.name,
                    'probability': round(s.probability, 3),
                    'timestamp': s.timestamp
                }
                for s in list(self.signal_history)[-10:]
            ]
        }


# =============================================================================
# SIGNAL SUBSCRIBER (for testing/monitoring)
# =============================================================================

class SignalSubscriber:
    """Subscribe to cascade signals from Redis"""

    def __init__(self, redis_config: Optional[Dict] = None):
        """Initialize signal subscriber"""
        self.redis_config = redis_config or {
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'db': REDIS_DB
        }
        self.redis = None
        self.running = False

    async def subscribe(self, channels: List[str] = None, callback=None):
        """
        Subscribe to signal channels

        Args:
            channels: List of channels to subscribe (default: all)
            callback: Optional callback function for signals
        """
        if channels is None:
            channels = [SIGNAL_CHANNEL, CRITICAL_SIGNAL_CHANNEL, ALERT_CHANNEL]

        self.redis = await redis.Redis(**self.redis_config)
        pubsub = self.redis.pubsub()

        await pubsub.subscribe(*channels)
        self.running = True

        logger.info(f"✅ Subscribed to channels: {channels}")

        try:
            while self.running:
                message = await pubsub.get_message(ignore_subscribe_messages=True)

                if message and message['type'] == 'message':
                    channel = message['channel'].decode()
                    data = json.loads(message['data'].decode())

                    if callback:
                        await callback(channel, data)
                    else:
                        # Default logging
                        signal_level = data.get('signal')
                        symbol = data.get('symbol')
                        prob = data.get('probability')

                        logger.info(
                            f"📡 [{channel}] {symbol}: {signal_level} "
                            f"(probability: {prob:.2%})"
                        )

                await asyncio.sleep(0.01)  # Small delay to prevent busy loop

        except asyncio.CancelledError:
            logger.info("Signal subscriber cancelled")
        finally:
            await pubsub.unsubscribe()
            await self.redis.close()

    async def stop(self):
        """Stop subscriber"""
        self.running = False


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'CascadeSignalGenerator',
    'SignalSubscriber',
    'CascadeSignalData',
    'SignalLevel',
    'DEFAULT_WEIGHTS',
    'SIGNAL_THRESHOLDS'
]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def example_usage():
    """Example of signal generation and subscription"""

    # Initialize Redis
    redis_config = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': REDIS_DB
    }

    redis_client = await redis.Redis(**redis_config)

    # Create signal generator
    generator = CascadeSignalGenerator(redis_client=redis_client)
    await generator.initialize()

    # Generate test signal
    signal = await generator.generate_signal('BTCUSDT')

    print("\n📊 Generated Signal:")
    print(f"Symbol: {signal.symbol}")
    print(f"Signal: {signal.signal.name}")
    print(f"Probability: {signal.probability:.2%}")
    print(f"Processing Time: {signal.processing_time_ms:.2f}ms")
    print(f"\nScores:")
    for key in ['velocity', 'acceleration', 'volume', 'oi_change', 'funding', 'volatility']:
        score = getattr(signal, f'{key}_score')
        print(f"  {key}: {score:.3f}")

    # Get stats
    stats = generator.get_stats()
    print(f"\n📈 Generator Stats:")
    print(f"Signals Generated: {stats['signals_generated']}")
    print(f"Avg Processing Time: {stats['avg_processing_time_ms']:.2f}ms")

    await redis_client.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(example_usage())
