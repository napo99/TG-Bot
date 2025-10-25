# 🎯 Critical Cascade Metrics Integration Plan

## Executive Summary
Integration plan to add velocity, acceleration, volatility tracking, and multi-timeframe analysis to the existing liquidation aggregator system.

## 📊 Current State vs Target State

### Current State (What You Have)
- ✅ Real-time liquidation WebSocket feeds (6 exchanges)
- ✅ Open Interest tracking via REST (1m, 5m, 1h windows)
- ✅ Funding rate collection and trends
- ✅ Basic aggregation with Redis caching
- ✅ TimescaleDB for historical data

### Target State (What We're Adding)
- 🎯 **Velocity/Acceleration tracking** for liquidations
- 🎯 **BTC volatility engine** (multi-timeframe)
- 🎯 **Weighted cascade scoring** with regime adjustments
- 🎯 **Real-time signal generation** (<10ms latency)
- 🎯 **Cross-symbol cascade detection**

## 🚀 Phase 1: Core Velocity & Acceleration (Week 1)

### Step 1.1: Add Velocity Tracking to LiquidationAggregator
```python
# File: services/liquidation-aggregator/aggregator.py

class EnhancedLiquidationAggregator(LiquidationAggregator):
    def __init__(self):
        super().__init__()

        # Add velocity tracking
        self.velocity_tracker = {
            'events_100ms': deque(maxlen=10),   # 1 second window
            'events_500ms': deque(maxlen=10),   # 5 second window
            'events_2s': deque(maxlen=10),      # 20 second window
            'events_10s': deque(maxlen=6),      # 1 minute window
        }

        # Acceleration tracking
        self.velocity_history = deque(maxlen=100)
        self.last_velocity_calc = 0
```

### Step 1.2: Implement Real-time Velocity Calculation
```python
async def calculate_velocity(self, event: CompactLiquidation):
    current_time = time.time()

    # Update all timeframe buffers
    for window_name, buffer in self.velocity_tracker.items():
        buffer.append({'time': current_time, 'event': event})

    # Calculate velocity every 100ms
    if current_time - self.last_velocity_calc >= 0.1:
        velocities = {}
        for window_name, buffer in self.velocity_tracker.items():
            window_duration = float(window_name.split('_')[1].rstrip('ms')) / 1000
            recent = [e for e in buffer if current_time - e['time'] <= window_duration]
            velocities[window_name] = len(recent) / window_duration if window_duration > 0 else 0

        # Calculate acceleration (second derivative)
        if len(self.velocity_history) > 0:
            prev_velocity = self.velocity_history[-1]['velocity']
            dt = current_time - self.velocity_history[-1]['time']
            acceleration = (velocities['events_500ms'] - prev_velocity) / dt if dt > 0 else 0
        else:
            acceleration = 0

        self.velocity_history.append({
            'time': current_time,
            'velocity': velocities['events_500ms'],
            'acceleration': acceleration
        })

        self.last_velocity_calc = current_time
        return velocities, acceleration
```

### Step 1.3: Add to Redis for Fast Access
```python
# Store velocity metrics in Redis with TTL
await self.redis.setex(
    f"velocity:{symbol}:500ms",
    10,  # 10 second TTL
    json.dumps({
        'velocity': velocities['events_500ms'],
        'acceleration': acceleration,
        'timestamp': current_time
    })
)
```

## 🎯 Phase 2: BTC Volatility Integration (Week 1)

### Step 2.1: Add BTC Price Feed
```python
# Add to existing WebSocket managers
class BinanceBTCPriceFeed:
    async def subscribe_btc_trades(self):
        """Subscribe to BTC aggTrade stream for real-time prices"""
        ws_url = "wss://stream.binance.com/ws/btcusdt@aggTrade"

        async with websockets.connect(ws_url) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                price = float(data['p'])

                # Update volatility engine
                vol_metrics = self.volatility_engine.update_price(price)

                # Store in Redis for other services
                await self.redis.set('btc:volatility:current', json.dumps({
                    'regime': vol_metrics.regime.name,
                    'vol_5min': vol_metrics.vol_5min,
                    'risk_multiplier': vol_metrics.cascade_risk_multiplier
                }))
```

### Step 2.2: Integrate Volatility with Cascade Detection
```python
class VolatilityAwareCascadeDetector:
    async def process_liquidation(self, event: CompactLiquidation):
        # Get current volatility context
        vol_context = await self.redis.get('btc:volatility:current')
        vol_data = json.loads(vol_context) if vol_context else {'risk_multiplier': 1.0}

        # Calculate base cascade probability
        base_prob = await self.calculate_cascade_probability(event)

        # Adjust for volatility regime
        adjusted_prob = base_prob * vol_data['risk_multiplier']

        # Adjust thresholds based on regime
        if vol_data.get('regime') == 'EXTREME':
            self.thresholds['velocity_critical'] *= 2.0
        elif vol_data.get('regime') == 'DORMANT':
            self.thresholds['velocity_critical'] *= 0.5
```

## 📈 Phase 3: Enhanced Signal Generation (Week 2)

### Step 3.1: Multi-Factor Cascade Scoring
```python
class CascadeScorer:
    def calculate_score(self, metrics: dict) -> float:
        """
        Professional cascade scoring combining all factors
        """
        weights = {
            'velocity': 0.25,
            'acceleration': 0.20,
            'volume': 0.20,
            'oi_change': 0.15,
            'funding_pressure': 0.10,
            'volatility': 0.10
        }

        # Normalize each metric to 0-1
        scores = {
            'velocity': min(1.0, metrics['velocity'] / 50),  # 50 events/s = max
            'acceleration': min(1.0, abs(metrics['acceleration']) / 20),
            'volume': min(1.0, metrics['volume_usd'] / 50_000_000),  # $50M = max
            'oi_change': min(1.0, abs(metrics['oi_change_1m']) / 0.05),  # 5% = max
            'funding_pressure': min(1.0, abs(metrics['funding_rate']) / 0.001),
            'volatility': metrics.get('vol_risk_multiplier', 1.0) / 5.0
        }

        # Weighted sum
        total_score = sum(scores[k] * weights[k] for k in weights)

        return total_score
```

### Step 3.2: Real-time Signal Publishing
```python
class SignalPublisher:
    async def publish_cascade_signal(self, signal: dict):
        """Publish to multiple channels for different consumers"""

        # 1. Redis Pub/Sub for real-time consumers
        await self.redis.publish('cascade:signals', json.dumps(signal))

        # 2. Store in time-series for analysis
        await self.redis.zadd(
            'cascade:signals:history',
            {json.dumps(signal): signal['timestamp']}
        )

        # 3. Alert if critical
        if signal['level'] >= CascadeSignal.CRITICAL:
            await self.send_alert(signal)
```

## 🔧 Phase 4: System Integration (Week 2)

### Step 4.1: Update Main Aggregator Loop
```python
async def enhanced_main_loop(self):
    """Enhanced main processing loop with all metrics"""

    tasks = [
        self.process_liquidations(),       # Existing
        self.track_open_interest(),        # Existing
        self.track_funding_rates(),        # Existing
        self.track_btc_volatility(),       # NEW
        self.calculate_velocities(),       # NEW
        self.generate_signals()            # NEW
    ]

    await asyncio.gather(*tasks)
```

### Step 4.2: Add Performance Monitoring
```python
class PerformanceMonitor:
    def track_latency(self, stage: str, duration_ms: float):
        """Track processing latency at each stage"""

        # Store in Redis for dashboard
        await self.redis.hset(
            'performance:latency',
            stage,
            json.dumps({
                'avg_ms': duration_ms,
                'timestamp': time.time()
            })
        )

        # Alert if too slow
        if duration_ms > 10:  # 10ms threshold
            logger.warning(f"High latency in {stage}: {duration_ms}ms")
```

## 📊 Implementation Priority & Timeline

### Week 1: Core Metrics
- [x] Day 1-2: Velocity/Acceleration tracking
- [x] Day 3-4: BTC Volatility Engine
- [ ] Day 5: Integration testing

### Week 2: Signal Generation
- [ ] Day 1-2: Multi-factor scoring
- [ ] Day 3-4: Signal publishing
- [ ] Day 5: End-to-end testing

### Week 3: Production Readiness
- [ ] Day 1-2: Performance optimization
- [ ] Day 3-4: Monitoring & alerts
- [ ] Day 5: Deploy to staging

## 🚨 Critical Implementation Notes

### 1. **OI Data Limitation**
Since OI is mostly REST-based (except Bybit WSS):
```python
# Use adaptive polling based on market conditions
if volatility_regime == 'EXTREME':
    oi_poll_interval = 5  # 5 seconds during high vol
else:
    oi_poll_interval = 30  # 30 seconds normally
```

### 2. **Memory Management**
```python
# Use circular buffers with fixed sizes
from collections import deque

velocity_buffer = deque(maxlen=1000)  # Fixed memory
# NOT: velocity_buffer = []  # Unbounded growth
```

### 3. **Redis Key Strategy**
```python
# Use consistent key naming with TTLs
keys = {
    'velocity': 'liq:vel:{symbol}:{timeframe}',  # TTL: 60s
    'volatility': 'btc:vol:current',             # TTL: 10s
    'cascade': 'cascade:score:{symbol}',         # TTL: 5s
    'signal': 'signal:{level}:{timestamp}'       # TTL: 3600s
}
```

## 🎯 Success Metrics

### Latency Targets
- Velocity calculation: <1ms
- Cascade scoring: <5ms
- Signal generation: <10ms
- End-to-end: <50ms

### Accuracy Targets
- False positive rate: <20%
- False negative rate: <10%
- Detection lag: <500ms

### System Health
- Memory usage: <500MB
- CPU usage: <50%
- Redis memory: <100MB

## 🚀 Next Steps After Integration

1. **Backtest with historical data** (cascade_backtest_framework.py)
2. **Tune thresholds** based on backtesting results
3. **Add exchange-specific adjustments**
4. **Implement position sizing based on signals**
5. **Create monitoring dashboard**

## 📝 Migration Checklist

- [ ] Create feature branch
- [ ] Add velocity tracking to aggregator
- [ ] Integrate BTC volatility engine
- [ ] Update Redis schema
- [ ] Add performance monitoring
- [ ] Run integration tests
- [ ] Backtest on historical data
- [ ] Document API changes
- [ ] Update deployment configs
- [ ] Deploy to staging
- [ ] Monitor for 24h
- [ ] Deploy to production

## 🔥 Quick Start Commands

```bash
# Test velocity tracking
python -m services.liquidation_aggregator.test_velocity

# Run backtesting
python cascade_backtest_framework.py

# Monitor performance
redis-cli --latency-history

# Check signal generation
redis-cli SUBSCRIBE cascade:signals
```

---

**This plan provides a clear path to integrate professional-grade cascade detection into your existing system while maintaining <50ms end-to-end latency.**