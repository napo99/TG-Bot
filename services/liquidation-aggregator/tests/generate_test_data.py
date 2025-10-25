#!/usr/bin/env python3
"""
TEST DATA GENERATOR
Generates realistic liquidation event data for comprehensive testing

Features:
- Realistic liquidation event generation
- Cascade simulation scenarios
- Edge case data sets
- Historical cascade replay
- Multi-exchange coordination
- Configurable event patterns

Usage:
    from generate_test_data import TestDataGenerator

    generator = TestDataGenerator()

    # Generate steady flow
    events = generator.generate_steady_flow(duration=60, rate=5)

    # Generate cascade
    events = generator.generate_cascade(
        duration=30,
        initial_rate=2,
        peak_rate=100,
        cascade_duration=10
    )
"""

import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# TEST EVENT DATA MODEL
# =============================================================================

class Side(Enum):
    """Liquidation side"""
    LONG = 0
    SHORT = 1


@dataclass
class TestLiquidationEvent:
    """Test liquidation event matching production format"""
    symbol: str
    timestamp: float
    value_usd: float
    exchange: str
    side: Side
    price: float
    quantity: float

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'value_usd': self.value_usd,
            'exchange': self.exchange,
            'side': self.side.name,
            'price': self.price,
            'quantity': self.quantity
        }


# =============================================================================
# TEST DATA GENERATOR
# =============================================================================

class TestDataGenerator:
    """
    Generate realistic test data for liquidation cascade testing

    Simulates:
    - Normal market conditions
    - Flash crashes
    - Gradual cascade buildup
    - Multi-exchange cascades
    - Extreme volatility events
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize test data generator

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Exchange probabilities (realistic distribution)
        self.exchanges = {
            'binance': 0.40,  # 40% of events
            'bybit': 0.25,    # 25%
            'okx': 0.20,      # 20%
            'hyperliquid': 0.15  # 15%
        }

        # Symbol probabilities
        self.symbols = {
            'BTCUSDT': 0.50,  # 50% BTC
            'ETHUSDT': 0.30,  # 30% ETH
            'SOLUSDT': 0.10,  # 10% SOL
            'ARBUSDT': 0.05,  # 5% ARB
            'DOGEUSDT': 0.05  # 5% DOGE
        }

        # Base prices for symbols
        self.base_prices = {
            'BTCUSDT': 43000,
            'ETHUSDT': 2300,
            'SOLUSDT': 100,
            'ARBUSDT': 1.5,
            'DOGEUSDT': 0.08
        }

        # Liquidation size distributions (USD)
        self.size_ranges = {
            'small': (1000, 10000),      # Retail
            'medium': (10000, 100000),   # Prosumer
            'large': (100000, 1000000),  # Whale
            'mega': (1000000, 10000000)  # Institutional
        }

        self.size_probabilities = {
            'small': 0.60,   # 60% small
            'medium': 0.30,  # 30% medium
            'large': 0.08,   # 8% large
            'mega': 0.02     # 2% mega (rare)
        }

    def _weighted_choice(self, choices: Dict[str, float]) -> str:
        """Make weighted random choice"""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]

    def _generate_single_event(self,
                               symbol: Optional[str] = None,
                               exchange: Optional[str] = None,
                               timestamp: Optional[float] = None,
                               size_category: Optional[str] = None) -> TestLiquidationEvent:
        """Generate a single liquidation event"""

        # Select symbol
        if symbol is None:
            symbol = self._weighted_choice(self.symbols)

        # Select exchange
        if exchange is None:
            exchange = self._weighted_choice(self.exchanges)

        # Select timestamp
        if timestamp is None:
            timestamp = time.time()

        # Select size category
        if size_category is None:
            size_category = self._weighted_choice(self.size_probabilities)

        # Generate liquidation size
        min_size, max_size = self.size_ranges[size_category]
        value_usd = random.uniform(min_size, max_size)

        # Generate price (with small random variation)
        base_price = self.base_prices[symbol]
        price_variation = random.uniform(0.98, 1.02)  # ±2%
        price = base_price * price_variation

        # Calculate quantity
        quantity = value_usd / price

        # Random side (slight bias toward longs during cascades)
        side = random.choices(
            [Side.LONG, Side.SHORT],
            weights=[0.55, 0.45]
        )[0]

        return TestLiquidationEvent(
            symbol=symbol,
            timestamp=timestamp,
            value_usd=value_usd,
            exchange=exchange,
            side=side,
            price=price,
            quantity=quantity
        )

    def generate_steady_flow(self,
                            duration: int = 60,
                            rate: float = 5.0,
                            symbol: Optional[str] = None) -> List[TestLiquidationEvent]:
        """
        Generate steady flow of liquidations

        Args:
            duration: Duration in seconds
            rate: Events per second
            symbol: Optional specific symbol

        Returns:
            List of liquidation events
        """
        events = []
        num_events = int(duration * rate)
        start_time = time.time()

        for i in range(num_events):
            # Distribute events evenly over duration with small jitter
            timestamp = start_time + (i / rate) + random.uniform(-0.1, 0.1)
            event = self._generate_single_event(symbol=symbol, timestamp=timestamp)
            events.append(event)

        return events

    def generate_cascade(self,
                        duration: int = 30,
                        initial_rate: float = 2.0,
                        peak_rate: float = 100.0,
                        cascade_duration: int = 10,
                        symbol: Optional[str] = None) -> List[TestLiquidationEvent]:
        """
        Generate cascade event pattern

        Pattern:
        1. Steady initial rate
        2. Rapid acceleration to peak
        3. Sustained peak
        4. Gradual deceleration

        Args:
            duration: Total duration in seconds
            initial_rate: Initial events per second
            peak_rate: Peak events per second
            cascade_duration: How long to sustain peak
            symbol: Optional specific symbol

        Returns:
            List of liquidation events
        """
        events = []
        start_time = time.time()
        current_time = start_time

        # Phase 1: Pre-cascade (25% of duration)
        pre_cascade_duration = duration * 0.25
        pre_cascade_end = start_time + pre_cascade_duration

        while current_time < pre_cascade_end:
            # Poisson process for steady rate
            interval = np.random.exponential(1.0 / initial_rate)
            current_time += interval

            if current_time < pre_cascade_end:
                event = self._generate_single_event(
                    symbol=symbol,
                    timestamp=current_time
                )
                events.append(event)

        # Phase 2: Acceleration (10% of duration)
        accel_duration = duration * 0.10
        accel_end = current_time + accel_duration

        while current_time < accel_end:
            # Linearly increase rate
            progress = (current_time - pre_cascade_end) / accel_duration
            current_rate = initial_rate + (peak_rate - initial_rate) * progress

            interval = np.random.exponential(1.0 / current_rate)
            current_time += interval

            if current_time < accel_end:
                # Larger events during cascade
                size_category = random.choices(
                    ['small', 'medium', 'large', 'mega'],
                    weights=[0.30, 0.40, 0.20, 0.10]
                )[0]

                event = self._generate_single_event(
                    symbol=symbol,
                    timestamp=current_time,
                    size_category=size_category
                )
                events.append(event)

        # Phase 3: Peak cascade (cascade_duration)
        peak_end = current_time + cascade_duration

        while current_time < peak_end:
            # Sustained high rate with variance
            current_rate = peak_rate * random.uniform(0.9, 1.1)
            interval = np.random.exponential(1.0 / current_rate)
            current_time += interval

            if current_time < peak_end:
                # Even larger events at peak
                size_category = random.choices(
                    ['small', 'medium', 'large', 'mega'],
                    weights=[0.20, 0.30, 0.30, 0.20]
                )[0]

                event = self._generate_single_event(
                    symbol=symbol,
                    timestamp=current_time,
                    size_category=size_category
                )
                events.append(event)

        # Phase 4: Deceleration (remaining duration)
        end_time = start_time + duration

        while current_time < end_time:
            # Exponentially decay back to initial rate
            progress = (current_time - peak_end) / (end_time - peak_end)
            current_rate = peak_rate * np.exp(-3 * progress) + initial_rate

            interval = np.random.exponential(1.0 / current_rate)
            current_time += interval

            if current_time < end_time:
                event = self._generate_single_event(
                    symbol=symbol,
                    timestamp=current_time
                )
                events.append(event)

        return events

    def generate_multi_exchange_cascade(self,
                                       duration: int = 30,
                                       lead_exchange: str = 'binance',
                                       correlation: float = 0.8) -> List[TestLiquidationEvent]:
        """
        Generate multi-exchange correlated cascade

        Simulates cascade starting on one exchange and spreading to others

        Args:
            duration: Duration in seconds
            lead_exchange: Exchange that starts cascade
            correlation: How correlated other exchanges are (0-1)

        Returns:
            List of liquidation events
        """
        events = []
        start_time = time.time()

        # Generate lead exchange cascade
        lead_events = self.generate_cascade(
            duration=duration,
            initial_rate=2.0,
            peak_rate=100.0,
            cascade_duration=10,
            symbol='BTCUSDT'
        )

        # Override exchange for lead events
        for event in lead_events:
            event.exchange = lead_exchange

        events.extend(lead_events)

        # Generate correlated events on other exchanges
        other_exchanges = [e for e in self.exchanges.keys() if e != lead_exchange]

        for event in lead_events:
            for other_exchange in other_exchanges:
                # Probability of correlated event
                if random.random() < correlation:
                    # Small time delay (cascade propagation)
                    delay = random.uniform(0.1, 1.0)

                    # Similar size with variation
                    size_factor = random.uniform(0.7, 1.3)

                    # Create correlated event
                    correlated_event = TestLiquidationEvent(
                        symbol=event.symbol,
                        timestamp=event.timestamp + delay,
                        value_usd=event.value_usd * size_factor,
                        exchange=other_exchange,
                        side=event.side,
                        price=event.price * random.uniform(0.98, 1.02),
                        quantity=event.quantity * size_factor
                    )
                    events.append(correlated_event)

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        return events

    def generate_flash_crash(self,
                            duration: int = 10,
                            peak_rate: float = 200.0) -> List[TestLiquidationEvent]:
        """
        Generate flash crash pattern

        Very rapid spike in liquidations over short duration

        Args:
            duration: Duration in seconds (typically 5-10s)
            peak_rate: Peak events per second

        Returns:
            List of liquidation events
        """
        events = []
        start_time = time.time()
        current_time = start_time
        end_time = start_time + duration

        # Spike shape: rapid rise, brief peak, rapid fall
        while current_time < end_time:
            # Calculate rate based on position in duration
            progress = (current_time - start_time) / duration

            # Gaussian-like spike
            rate = peak_rate * np.exp(-((progress - 0.5) ** 2) / 0.05)
            rate = max(rate, 5.0)  # Minimum rate

            interval = np.random.exponential(1.0 / rate)
            current_time += interval

            if current_time < end_time:
                # Mega liquidations during flash crash
                size_category = random.choices(
                    ['medium', 'large', 'mega'],
                    weights=[0.30, 0.40, 0.30]
                )[0]

                event = self._generate_single_event(
                    symbol='BTCUSDT',
                    timestamp=current_time,
                    size_category=size_category
                )
                events.append(event)

        return events

    def generate_edge_cases(self) -> Dict[str, List[TestLiquidationEvent]]:
        """
        Generate edge case test scenarios

        Returns:
            Dictionary of edge case scenarios
        """
        scenarios = {}
        start_time = time.time()

        # 1. Zero events (dormant market)
        scenarios['zero_events'] = []

        # 2. Single massive liquidation
        scenarios['single_mega'] = [
            self._generate_single_event(
                timestamp=start_time,
                size_category='mega'
            )
        ]

        # 3. Rapid burst (100 events in 1 second)
        scenarios['rapid_burst'] = [
            self._generate_single_event(
                timestamp=start_time + i * 0.01
            )
            for i in range(100)
        ]

        # 4. All one exchange
        scenarios['single_exchange'] = [
            self._generate_single_event(
                exchange='binance',
                timestamp=start_time + i
            )
            for i in range(50)
        ]

        # 5. Perfectly alternating exchanges
        scenarios['alternating_exchanges'] = [
            self._generate_single_event(
                exchange=['binance', 'bybit'][i % 2],
                timestamp=start_time + i
            )
            for i in range(50)
        ]

        # 6. All same size
        scenarios['uniform_size'] = [
            self._generate_single_event(
                timestamp=start_time + i,
                size_category='medium'
            )
            for i in range(50)
        ]

        # 7. Exponentially increasing sizes
        scenarios['exponential_growth'] = []
        for i in range(20):
            value_usd = 1000 * (1.3 ** i)  # Exponential growth
            event = self._generate_single_event(timestamp=start_time + i)
            event.value_usd = value_usd
            scenarios['exponential_growth'].append(event)

        return scenarios

    def generate_stress_test_data(self,
                                 duration: int = 60,
                                 target_rate: float = 10000.0) -> List[TestLiquidationEvent]:
        """
        Generate high-volume stress test data

        Args:
            duration: Duration in seconds
            target_rate: Target events per second

        Returns:
            List of liquidation events
        """
        events = []
        num_events = int(duration * target_rate)
        start_time = time.time()

        print(f"Generating {num_events:,} events for stress test...")

        for i in range(num_events):
            if i % 100000 == 0:
                print(f"  Generated {i:,}/{num_events:,} events...")

            # Evenly distribute over duration
            timestamp = start_time + (i / target_rate)
            event = self._generate_single_event(timestamp=timestamp)
            events.append(event)

        print(f"✅ Generated {len(events):,} events")
        return events

    def get_statistics(self, events: List[TestLiquidationEvent]) -> dict:
        """
        Calculate statistics for generated events

        Args:
            events: List of events

        Returns:
            Statistics dictionary
        """
        if not events:
            return {'event_count': 0}

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Time range
        start_time = sorted_events[0].timestamp
        end_time = sorted_events[-1].timestamp
        duration = end_time - start_time

        # Event count
        total_events = len(events)

        # Exchange distribution
        exchange_counts = {}
        for event in events:
            exchange_counts[event.exchange] = exchange_counts.get(event.exchange, 0) + 1

        # Symbol distribution
        symbol_counts = {}
        for event in events:
            symbol_counts[event.symbol] = symbol_counts.get(event.symbol, 0) + 1

        # Size statistics
        values = [e.value_usd for e in events]
        total_value = sum(values)

        # Velocity
        avg_rate = total_events / duration if duration > 0 else 0

        return {
            'event_count': total_events,
            'duration': duration,
            'avg_rate': avg_rate,
            'total_value_usd': total_value,
            'avg_value_usd': np.mean(values),
            'median_value_usd': np.median(values),
            'max_value_usd': np.max(values),
            'min_value_usd': np.min(values),
            'exchange_distribution': exchange_counts,
            'symbol_distribution': symbol_counts
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def example_usage():
    """Demonstrate test data generator"""
    generator = TestDataGenerator(seed=42)

    print("=" * 60)
    print("TEST DATA GENERATOR EXAMPLES")
    print("=" * 60)

    # 1. Steady flow
    print("\n1. STEADY FLOW (60s, 5 events/s)")
    events = generator.generate_steady_flow(duration=60, rate=5.0)
    stats = generator.get_statistics(events)
    print(f"   Generated: {stats['event_count']} events")
    print(f"   Avg Rate: {stats['avg_rate']:.2f} events/s")
    print(f"   Total Value: ${stats['total_value_usd']:,.2f}")

    # 2. Cascade
    print("\n2. CASCADE (30s, 2→100 events/s)")
    events = generator.generate_cascade(
        duration=30,
        initial_rate=2.0,
        peak_rate=100.0,
        cascade_duration=10
    )
    stats = generator.get_statistics(events)
    print(f"   Generated: {stats['event_count']} events")
    print(f"   Avg Rate: {stats['avg_rate']:.2f} events/s")
    print(f"   Total Value: ${stats['total_value_usd']:,.2f}")

    # 3. Multi-exchange cascade
    print("\n3. MULTI-EXCHANGE CASCADE (30s, 0.8 correlation)")
    events = generator.generate_multi_exchange_cascade(
        duration=30,
        lead_exchange='binance',
        correlation=0.8
    )
    stats = generator.get_statistics(events)
    print(f"   Generated: {stats['event_count']} events")
    print(f"   Exchange Distribution: {stats['exchange_distribution']}")

    # 4. Flash crash
    print("\n4. FLASH CRASH (10s, 200 events/s peak)")
    events = generator.generate_flash_crash(duration=10, peak_rate=200.0)
    stats = generator.get_statistics(events)
    print(f"   Generated: {stats['event_count']} events")
    print(f"   Avg Rate: {stats['avg_rate']:.2f} events/s")

    # 5. Edge cases
    print("\n5. EDGE CASES")
    scenarios = generator.generate_edge_cases()
    for name, events in scenarios.items():
        print(f"   {name}: {len(events)} events")

    print("\n" + "=" * 60)
    print("✅ Test data generation complete")
    print("=" * 60)


if __name__ == "__main__":
    example_usage()
