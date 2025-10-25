"""
Enhanced Liquidation Aggregator with Velocity, Acceleration, and Volatility
Direct integration with your existing CompactLiquidation model and infrastructure
"""

import asyncio
import json
import time
import redis.asyncio as redis
import numpy as np
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Your existing imports
from shared.models.compact_liquidation import CompactLiquidation
from btc_volatility_engine import BTCVolatilityEngine, VolatilityRegime
from professional_cascade_detector import CascadeSignal


class VelocityAccelerationTracker:
    """
    Real-time velocity and acceleration tracking for liquidations
    Designed to work with your existing CompactLiquidation model
    """

    def __init__(self):
        # Multi-timeframe tracking (all in memory for speed)
        self.timeframes = {
            '100ms': {'window': 0.1, 'buffer': deque(maxlen=100)},
            '500ms': {'window': 0.5, 'buffer': deque(maxlen=100)},
            '2s': {'window': 2.0, 'buffer': deque(maxlen=100)},
            '10s': {'window': 10.0, 'buffer': deque(maxlen=60)},
            '1m': {'window': 60.0, 'buffer': deque(maxlen=60)}
        }

        # Velocity history for acceleration calculation
        self.velocity_history = deque(maxlen=100)

        # Per-symbol tracking
        self.symbol_metrics = defaultdict(lambda: {
            'velocity': 0.0,
            'acceleration': 0.0,
            'volume_velocity': 0.0,
            'last_update': 0
        })

        # Per-exchange tracking
        self.exchange_metrics = defaultdict(lambda: {
            'velocity': 0.0,
            'correlation': 0.0
        })

    def update(self, liquidation: CompactLiquidation) -> Dict:
        """
        Update velocity and acceleration metrics
        Returns metrics dict for immediate use
        """
        current_time = time.time()

        # Add to all timeframe buffers
        event_data = {
            'time': current_time,
            'symbol': liquidation.s,  # Symbol
            'exchange': liquidation.e,  # Exchange
            'side': liquidation.si,  # Side (0=long, 1=short)
            'size_usd': liquidation.v,  # USD value
            'timestamp': liquidation.t  # Exchange timestamp
        }

        for tf_name, tf_data in self.timeframes.items():
            tf_data['buffer'].append(event_data)

        # Calculate velocities for each timeframe
        velocities = {}
        volume_velocities = {}

        for tf_name, tf_data in self.timeframes.items():
            window = tf_data['window']
            buffer = tf_data['buffer']

            # Get events within window
            recent_events = [
                e for e in buffer
                if current_time - e['time'] <= window
            ]

            # Event velocity (events per second)
            velocities[tf_name] = len(recent_events) / window if window > 0 else 0

            # Volume velocity (USD per second)
            total_volume = sum(e['size_usd'] for e in recent_events)
            volume_velocities[tf_name] = total_volume / window if window > 0 else 0

        # Calculate acceleration (using 500ms as reference)
        acceleration = 0.0
        if self.velocity_history:
            prev = self.velocity_history[-1]
            dt = current_time - prev['time']
            if dt > 0:
                acceleration = (velocities['500ms'] - prev['velocity']) / dt

        # Store in history
        self.velocity_history.append({
            'time': current_time,
            'velocity': velocities['500ms'],
            'acceleration': acceleration
        })

        # Update symbol-specific metrics
        self.symbol_metrics[liquidation.s].update({
            'velocity': velocities['500ms'],
            'acceleration': acceleration,
            'volume_velocity': volume_velocities['500ms'],
            'last_update': current_time
        })

        # Update exchange metrics
        self.exchange_metrics[liquidation.e]['velocity'] = velocities['500ms']

        # Calculate cross-exchange correlation
        if len(self.exchange_metrics) >= 2:
            exchange_velocities = [m['velocity'] for m in self.exchange_metrics.values()]
            mean_vel = np.mean(exchange_velocities)
            if mean_vel > 0:
                variance = np.var(exchange_velocities)
                correlation = 1.0 - (variance / (mean_vel ** 2))
                for exchange in self.exchange_metrics:
                    self.exchange_metrics[exchange]['correlation'] = max(0, min(1, correlation))

        return {
            'velocities': velocities,
            'volume_velocities': volume_velocities,
            'acceleration': acceleration,
            'symbol_velocity': self.symbol_metrics[liquidation.s]['velocity'],
            'exchange_correlation': self.exchange_metrics[liquidation.e].get('correlation', 0)
        }

    def get_cascade_risk(self, symbol: str) -> float:
        """
        Calculate cascade risk based on velocity and acceleration
        """
        metrics = self.symbol_metrics.get(symbol, {})

        velocity = metrics.get('velocity', 0)
        acceleration = metrics.get('acceleration', 0)
        volume_velocity = metrics.get('volume_velocity', 0)

        # Base risk from velocity
        risk = 0.0

        # Velocity thresholds (events per second)
        if velocity > 50:  # Extreme
            risk += 40
        elif velocity > 20:  # High
            risk += 25
        elif velocity > 10:  # Elevated
            risk += 15
        elif velocity > 5:  # Moderate
            risk += 5

        # Acceleration bonus (things getting worse)
        if acceleration > 10:  # Rapid acceleration
            risk += 30
        elif acceleration > 5:
            risk += 20
        elif acceleration > 2:
            risk += 10

        # Volume velocity (USD per second)
        if volume_velocity > 50_000_000:  # >$50M/s
            risk += 30
        elif volume_velocity > 10_000_000:  # >$10M/s
            risk += 20
        elif volume_velocity > 1_000_000:  # >$1M/s
            risk += 10

        return min(100, risk)  # Cap at 100


class EnhancedLiquidationAggregator:
    """
    Enhanced aggregator that integrates with your existing system
    Adds velocity, acceleration, and volatility awareness
    """

    def __init__(self, redis_url: str = "redis://localhost"):
        # Redis for state management
        self.redis = redis.from_url(redis_url)

        # Velocity and acceleration tracking
        self.velocity_tracker = VelocityAccelerationTracker()

        # BTC volatility engine
        self.volatility_engine = BTCVolatilityEngine()

        # Metrics storage
        self.metrics_buffer = deque(maxlen=1000)

        # Performance tracking
        self.latency_tracker = deque(maxlen=100)

        # Signal generation
        self.last_signal_time = 0
        self.signal_cooldown = 1.0  # Minimum 1 second between signals

    async def process_liquidation(self, liquidation: CompactLiquidation) -> Dict:
        """
        Process incoming liquidation with full metrics calculation
        This integrates with your existing WebSocket handlers
        """
        start_time = time.perf_counter()

        # 1. Update velocity/acceleration
        velocity_metrics = self.velocity_tracker.update(liquidation)

        # 2. Get current volatility context from Redis
        vol_context = await self.get_volatility_context()

        # 3. Get market context (OI, funding, etc)
        market_context = await self.get_market_context(liquidation.s)

        # 4. Calculate cascade probability
        cascade_score = self.calculate_cascade_score(
            liquidation,
            velocity_metrics,
            vol_context,
            market_context
        )

        # 5. Generate signal if needed
        signal = await self.generate_signal(
            liquidation,
            cascade_score,
            velocity_metrics,
            vol_context
        )

        # 6. Store metrics in Redis for other services
        await self.store_metrics(liquidation, velocity_metrics, cascade_score)

        # Track performance
        latency = (time.perf_counter() - start_time) * 1000
        self.latency_tracker.append(latency)

        if latency > 10:  # Log if >10ms
            print(f"⚠️ High latency: {latency:.2f}ms for {liquidation.s}")

        return {
            'symbol': liquidation.s,
            'exchange': liquidation.e,
            'velocity': velocity_metrics['symbol_velocity'],
            'acceleration': velocity_metrics['acceleration'],
            'cascade_score': cascade_score,
            'signal': signal,
            'latency_ms': latency
        }

    async def update_btc_price(self, price: float):
        """
        Update BTC price and volatility metrics
        Call this from your BTC price WebSocket handler
        """
        vol_metrics = self.volatility_engine.update_price(price)

        # Store in Redis
        await self.redis.setex(
            'btc:volatility:current',
            10,  # 10 second TTL
            json.dumps({
                'regime': vol_metrics.regime.name,
                'vol_1min': vol_metrics.vol_1min,
                'vol_5min': vol_metrics.vol_5min,
                'vol_15min': vol_metrics.vol_15min,
                'vol_1h': vol_metrics.vol_1h,
                'acceleration': vol_metrics.vol_acceleration,
                'percentile_24h': vol_metrics.vol_percentile_24h,
                'z_score': vol_metrics.vol_zscore,
                'risk_multiplier': vol_metrics.cascade_risk_multiplier,
                'timestamp': vol_metrics.timestamp
            })
        )

        return vol_metrics

    async def get_volatility_context(self) -> Dict:
        """
        Get current volatility context from Redis
        """
        vol_data = await self.redis.get('btc:volatility:current')
        if vol_data:
            return json.loads(vol_data)
        return {'risk_multiplier': 1.0, 'regime': 'NORMAL'}

    async def get_market_context(self, symbol: str) -> Dict:
        """
        Get market context (OI, funding) from Redis
        These are updated by your existing REST polling
        """
        context = {}

        # Get OI changes
        oi_data = await self.redis.get(f'oi:{symbol}:changes')
        if oi_data:
            context['oi'] = json.loads(oi_data)
        else:
            context['oi'] = {'change_1m': 0, 'change_5m': 0}

        # Get funding rate
        funding_data = await self.redis.get(f'funding:{symbol}:current')
        if funding_data:
            context['funding'] = json.loads(funding_data)
        else:
            context['funding'] = {'rate': 0, 'trend': 'neutral'}

        return context

    def calculate_cascade_score(
        self,
        liquidation: CompactLiquidation,
        velocity_metrics: Dict,
        vol_context: Dict,
        market_context: Dict
    ) -> float:
        """
        Professional multi-factor cascade scoring
        """
        # Base weights (adjusted by volatility regime)
        weights = {
            'velocity': 0.25,
            'acceleration': 0.20,
            'volume': 0.20,
            'oi_change': 0.15,
            'funding_pressure': 0.10,
            'correlation': 0.10
        }

        # Adjust weights based on volatility regime
        if vol_context.get('regime') == 'EXTREME':
            weights['velocity'] *= 0.8  # Less weight on velocity in extreme vol
            weights['volume'] *= 1.2    # More weight on size
        elif vol_context.get('regime') == 'DORMANT':
            weights['velocity'] *= 1.2  # More weight on velocity in low vol
            weights['correlation'] *= 1.3  # Correlation more important

        # Calculate individual scores (0-1 normalized)
        scores = {}

        # Velocity score
        velocity = velocity_metrics.get('symbol_velocity', 0)
        scores['velocity'] = min(1.0, velocity / 50)  # 50 events/s = max

        # Acceleration score
        acceleration = velocity_metrics.get('acceleration', 0)
        scores['acceleration'] = min(1.0, abs(acceleration) / 20)

        # Volume score
        volume = liquidation.v  # USD value
        scores['volume'] = min(1.0, volume / 10_000_000)  # $10M = max

        # OI change score
        oi_change = abs(market_context.get('oi', {}).get('change_1m', 0))
        scores['oi_change'] = min(1.0, oi_change / 0.05)  # 5% = max

        # Funding pressure score
        funding_rate = abs(market_context.get('funding', {}).get('rate', 0))
        scores['funding_pressure'] = min(1.0, funding_rate / 0.001)  # 0.1% = max

        # Correlation score
        correlation = velocity_metrics.get('exchange_correlation', 0)
        scores['correlation'] = correlation

        # Calculate weighted sum
        cascade_score = sum(scores.get(k, 0) * weights[k] for k in weights)

        # Apply volatility risk multiplier
        cascade_score *= vol_context.get('risk_multiplier', 1.0)

        return min(1.0, cascade_score)  # Cap at 1.0

    async def generate_signal(
        self,
        liquidation: CompactLiquidation,
        cascade_score: float,
        velocity_metrics: Dict,
        vol_context: Dict
    ) -> Optional[Dict]:
        """
        Generate trading signal based on cascade score
        """
        current_time = time.time()

        # Check cooldown
        if current_time - self.last_signal_time < self.signal_cooldown:
            return None

        # Determine signal level
        signal_level = None
        if cascade_score > 0.9:
            signal_level = CascadeSignal.EXTREME
        elif cascade_score > 0.7:
            signal_level = CascadeSignal.CRITICAL
        elif cascade_score > 0.5:
            signal_level = CascadeSignal.ALERT
        elif cascade_score > 0.3:
            signal_level = CascadeSignal.WATCH

        if signal_level and signal_level >= CascadeSignal.ALERT:
            signal = {
                'timestamp': current_time,
                'symbol': liquidation.s,
                'exchange': liquidation.e,
                'level': signal_level.name,
                'cascade_score': cascade_score,
                'velocity': velocity_metrics['symbol_velocity'],
                'acceleration': velocity_metrics['acceleration'],
                'volatility_regime': vol_context.get('regime', 'UNKNOWN'),
                'action': self.get_trading_action(signal_level, liquidation.si)
            }

            # Publish signal
            await self.redis.publish('cascade:signals', json.dumps(signal))

            # Store in history
            await self.redis.zadd(
                'cascade:signals:history',
                {json.dumps(signal): current_time}
            )

            self.last_signal_time = current_time
            return signal

        return None

    def get_trading_action(self, signal_level: CascadeSignal, side: int) -> str:
        """
        Determine trading action based on signal and liquidation side
        """
        # side: 0 = long liquidation, 1 = short liquidation

        if signal_level == CascadeSignal.EXTREME:
            if side == 0:  # Long liquidations = price falling
                return "SHORT_AGGRESSIVE"
            else:  # Short liquidations = price rising
                return "LONG_AGGRESSIVE"
        elif signal_level == CascadeSignal.CRITICAL:
            if side == 0:
                return "SHORT_MODERATE"
            else:
                return "LONG_MODERATE"
        elif signal_level == CascadeSignal.ALERT:
            return "PREPARE_ENTRY"
        else:
            return "MONITOR"

    async def store_metrics(
        self,
        liquidation: CompactLiquidation,
        velocity_metrics: Dict,
        cascade_score: float
    ):
        """
        Store metrics in Redis for dashboards and other services
        """
        symbol = liquidation.s

        # Store velocity metrics
        await self.redis.setex(
            f'velocity:{symbol}:current',
            60,  # 60 second TTL
            json.dumps({
                'velocity': velocity_metrics['symbol_velocity'],
                'acceleration': velocity_metrics['acceleration'],
                'volume_velocity': velocity_metrics['volume_velocities']['500ms'],
                'timestamp': time.time()
            })
        )

        # Store cascade score
        await self.redis.setex(
            f'cascade:{symbol}:score',
            10,  # 10 second TTL
            json.dumps({
                'score': cascade_score,
                'risk': self.velocity_tracker.get_cascade_risk(symbol),
                'timestamp': time.time()
            })
        )

        # Update performance metrics
        if self.latency_tracker:
            avg_latency = np.mean(list(self.latency_tracker))
            await self.redis.hset(
                'performance:metrics',
                'avg_latency_ms',
                str(avg_latency)
            )

    async def get_system_health(self) -> Dict:
        """
        Get system health metrics
        """
        health = {
            'timestamp': time.time(),
            'avg_latency_ms': np.mean(list(self.latency_tracker)) if self.latency_tracker else 0,
            'max_latency_ms': max(self.latency_tracker) if self.latency_tracker else 0,
            'volatility_regime': 'UNKNOWN',
            'active_symbols': len(self.velocity_tracker.symbol_metrics),
            'active_exchanges': len(self.velocity_tracker.exchange_metrics)
        }

        # Get volatility regime
        vol_context = await self.get_volatility_context()
        health['volatility_regime'] = vol_context.get('regime', 'UNKNOWN')

        return health


# Example integration with your existing WebSocket handler
async def example_integration():
    """
    Example of how to integrate with your existing system
    """
    # Initialize enhanced aggregator
    aggregator = EnhancedLiquidationAggregator()

    # Example liquidation from your WebSocket
    liquidation = CompactLiquidation(
        t=int(time.time() * 1000),  # Timestamp
        e=1,  # Exchange ID (1=Binance)
        s="BTCUSDT",  # Symbol
        si=0,  # Side (0=long)
        p=40000.0,  # Price
        q=2.5,  # Quantity
        v=100000.0  # USD value
    )

    # Process liquidation
    result = await aggregator.process_liquidation(liquidation)

    print(f"""
    📊 LIQUIDATION PROCESSED:
    Symbol: {result['symbol']}
    Velocity: {result['velocity']:.2f} events/s
    Acceleration: {result['acceleration']:.2f} events/s²
    Cascade Score: {result['cascade_score']:.2%}
    Signal: {result.get('signal', 'None')}
    Latency: {result['latency_ms']:.2f}ms
    """)

    # Update BTC price (from your price feed)
    btc_price = 40000
    vol_metrics = await aggregator.update_btc_price(btc_price)
    print(f"Volatility Regime: {vol_metrics.regime.name}")

    # Get system health
    health = await aggregator.get_system_health()
    print(f"System Health: {health}")

    # Cleanup
    await aggregator.redis.close()


if __name__ == "__main__":
    asyncio.run(example_integration())