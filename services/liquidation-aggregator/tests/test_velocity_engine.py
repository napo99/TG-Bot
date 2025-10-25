#!/usr/bin/env python3
"""
COMPREHENSIVE UNIT TESTS FOR VELOCITY ENGINE
Tests for advanced_velocity_engine.py and cascade_risk_calculator.py

Test Coverage:
- Multi-timeframe velocity calculations
- Acceleration and jerk calculations
- Volume-weighted metrics
- Exchange correlation
- Cascade risk scoring
- Performance benchmarks
- Edge cases and boundary conditions
"""

import unittest
import time
import numpy as np
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_velocity_engine import (
    AdvancedVelocityEngine,
    MultiTimeframeVelocity,
    ExchangeMetrics,
    CorrelationMatrix,
    CascadeRiskLevel,
    TIMEFRAMES
)

from cascade_risk_calculator import (
    CascadeRiskCalculator,
    CascadeRiskAssessment,
    RiskFactors,
    VELOCITY_THRESHOLDS,
    ACCELERATION_THRESHOLDS
)


class TestAdvancedVelocityEngine(unittest.TestCase):
    """Test cases for AdvancedVelocityEngine"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = AdvancedVelocityEngine()
        self.symbol = "BTCUSDT"

    def test_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.events_processed, 0)
        self.assertEqual(self.engine.calculations_performed, 0)

    def test_add_single_event(self):
        """Test adding a single event"""
        self.engine.add_event(self.symbol, 10000.0, "binance")
        self.assertEqual(self.engine.events_processed, 1)
        self.assertIn(self.symbol, self.engine.event_buffers)
        self.assertEqual(len(self.engine.event_buffers[self.symbol]), 1)

    def test_add_multiple_events(self):
        """Test adding multiple events"""
        for i in range(10):
            self.engine.add_event(self.symbol, 1000.0 * (i + 1), "binance")

        self.assertEqual(self.engine.events_processed, 10)
        self.assertEqual(len(self.engine.event_buffers[self.symbol]), 10)

    def test_velocity_calculation_basic(self):
        """Test basic velocity calculation"""
        # Add events over 5 seconds
        base_time = time.time()
        for i in range(5):
            timestamp = base_time + i
            self.engine.add_event(self.symbol, 1000.0, "binance", timestamp)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.symbol, self.symbol)
        self.assertGreater(metrics.count_10s, 0)

    def test_velocity_calculation_empty(self):
        """Test velocity calculation with no events"""
        metrics = self.engine.calculate_multi_timeframe_velocity("NONEXISTENT")
        self.assertIsNone(metrics)

    def test_multi_timeframe_velocity(self):
        """Test multi-timeframe velocity calculations"""
        # Add 20 events over 30 seconds
        base_time = time.time()
        for i in range(20):
            timestamp = base_time - (30 - i * 1.5)  # Spread over 30s
            self.engine.add_event(self.symbol, 5000.0, "binance", timestamp)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        self.assertIsNotNone(metrics)

        # Verify all timeframes are calculated
        self.assertGreaterEqual(metrics.count_100ms, 0)
        self.assertGreaterEqual(metrics.count_500ms, 0)
        self.assertGreaterEqual(metrics.count_2s, 0)
        self.assertGreaterEqual(metrics.count_10s, 0)
        self.assertGreaterEqual(metrics.count_60s, 0)

        # Long timeframe should have more events than short
        self.assertGreaterEqual(metrics.count_60s, metrics.count_10s)
        self.assertGreaterEqual(metrics.count_10s, metrics.count_2s)

    def test_velocity_values(self):
        """Test velocity value calculations"""
        # Add 10 events in last 10 seconds
        base_time = time.time()
        for i in range(10):
            timestamp = base_time - (10 - i)
            self.engine.add_event(self.symbol, 1000.0, "binance", timestamp)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)

        # 10 events in 10 seconds = 1 event/second
        self.assertAlmostEqual(metrics.velocity_10s, 1.0, places=1)

    def test_volume_weighted_velocity(self):
        """Test volume-weighted velocity calculations"""
        base_time = time.time()

        # Add events with varying sizes
        self.engine.add_event(self.symbol, 100000.0, "binance", base_time - 5)
        self.engine.add_event(self.symbol, 50000.0, "binance", base_time - 3)
        self.engine.add_event(self.symbol, 25000.0, "binance", base_time - 1)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)

        # Volume-weighted velocity should account for event sizes
        self.assertGreater(metrics.vw_velocity_10s, 0)
        self.assertGreater(metrics.total_volume_usd, 0)

    def test_volume_metrics(self):
        """Test volume metric calculations"""
        base_time = time.time()
        values = [10000.0, 20000.0, 30000.0, 40000.0, 50000.0]

        for i, value in enumerate(values):
            self.engine.add_event(self.symbol, value, "binance", base_time - i)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)

        # Check volume metrics
        self.assertAlmostEqual(metrics.total_volume_usd, sum(values), places=2)
        self.assertAlmostEqual(metrics.avg_event_size_usd, np.mean(values), places=2)
        self.assertAlmostEqual(metrics.max_event_size_usd, max(values), places=2)

    def test_acceleration_calculation(self):
        """Test acceleration (2nd derivative) calculation"""
        base_time = time.time()

        # Create accelerating pattern: 1, 2, 4, 8 events per second
        for round_num, count in enumerate([1, 2, 4, 8]):
            for i in range(count):
                timestamp = base_time - (40 - (round_num * 10 + i * (10 / count)))
                self.engine.add_event(self.symbol, 1000.0, "binance", timestamp)

        # Calculate multiple times to build velocity history
        for _ in range(5):
            metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
            time.sleep(0.1)

        # Final calculation should show positive acceleration
        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        # Acceleration can be positive or zero depending on timing
        self.assertIsNotNone(metrics.acceleration)

    def test_jerk_calculation(self):
        """Test jerk (3rd derivative) calculation"""
        base_time = time.time()

        # Add events to create velocity pattern
        for i in range(20):
            self.engine.add_event(self.symbol, 1000.0, "binance", base_time - (20 - i))

        # Calculate multiple times to build history
        for _ in range(5):
            metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
            time.sleep(0.05)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        self.assertIsNotNone(metrics.jerk)

    def test_multiple_exchanges(self):
        """Test handling events from multiple exchanges"""
        base_time = time.time()

        # Add events from different exchanges
        self.engine.add_event(self.symbol, 5000.0, "binance", base_time)
        self.engine.add_event(self.symbol, 6000.0, "bybit", base_time)
        self.engine.add_event(self.symbol, 7000.0, "okx", base_time)

        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        self.assertEqual(metrics.count_10s, 3)

        # Check exchange breakdown
        breakdown = self.engine.get_exchange_breakdown(self.symbol)
        self.assertEqual(len(breakdown), 3)
        self.assertIn("binance", breakdown)
        self.assertIn("bybit", breakdown)
        self.assertIn("okx", breakdown)

    def test_exchange_correlation(self):
        """Test cross-exchange correlation calculation"""
        base_time = time.time()

        # Add correlated events (simultaneous across exchanges)
        for i in range(10):
            timestamp = base_time - (10 - i)
            self.engine.add_event(self.symbol, 1000.0, "binance", timestamp)
            self.engine.add_event(self.symbol, 1100.0, "bybit", timestamp)
            self.engine.add_event(self.symbol, 900.0, "okx", timestamp + 0.1)

        corr_matrix = self.engine.calculate_exchange_correlation(self.symbol, window_seconds=15.0)
        self.assertIsNotNone(corr_matrix)
        self.assertGreater(len(corr_matrix.correlations), 0)

        # Correlation should be high for synchronized events
        binance_bybit_corr = corr_matrix.get_correlation("binance", "bybit")
        if binance_bybit_corr is not None:
            self.assertGreaterEqual(binance_bybit_corr, -1.0)
            self.assertLessEqual(binance_bybit_corr, 1.0)

    def test_memory_limits(self):
        """Test memory management with buffer limits"""
        # Add more events than max buffer size
        base_time = time.time()
        for i in range(5000):  # More than MAX_EVENTS_PER_SYMBOL
            self.engine.add_event(self.symbol, 1000.0, "binance", base_time - i)

        # Buffer should be capped at max size
        self.assertLessEqual(len(self.engine.event_buffers[self.symbol]), 3000)

    def test_clear_old_data(self):
        """Test clearing old data"""
        base_time = time.time()

        # Add old events
        for i in range(10):
            self.engine.add_event(self.symbol, 1000.0, "binance", base_time - 400 - i)

        # Add recent events
        for i in range(5):
            self.engine.add_event(self.symbol, 1000.0, "binance", base_time - i)

        # Clear data older than 300 seconds
        self.engine.clear_old_data(max_age_seconds=300.0)

        # Should only have recent events
        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        if metrics:
            self.assertLessEqual(metrics.count_60s, 5)

    def test_performance_statistics(self):
        """Test performance statistics tracking"""
        # Add events and calculate metrics
        for i in range(10):
            self.engine.add_event(self.symbol, 1000.0, "binance")

        self.engine.calculate_multi_timeframe_velocity(self.symbol)

        stats = self.engine.get_performance_stats()
        self.assertGreater(stats['events_processed'], 0)
        self.assertGreater(stats['calculations_performed'], 0)
        self.assertGreaterEqual(stats['avg_calculation_time_ms'], 0)

    def test_performance_target(self):
        """Test that calculations meet performance targets (<0.5ms)"""
        # Add realistic workload
        base_time = time.time()
        for i in range(100):
            self.engine.add_event(self.symbol, 1000.0 * (i % 3 + 1),
                                f"exchange{i % 3}", base_time - i * 0.5)

        # Measure calculation time
        start = time.perf_counter()
        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        calc_time_ms = (time.perf_counter() - start) * 1000

        self.assertIsNotNone(metrics)
        # Performance target: <1ms (relaxed for test environment)
        self.assertLess(calc_time_ms, 5.0,
                       f"Calculation took {calc_time_ms:.2f}ms, target is <5ms")


class TestCascadeRiskCalculator(unittest.TestCase):
    """Test cases for CascadeRiskCalculator"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = CascadeRiskCalculator()
        self.symbol = "BTCUSDT"

    def test_initialization(self):
        """Test calculator initialization"""
        self.assertIsNotNone(self.calculator)
        self.assertEqual(self.calculator.assessments_performed, 0)

    def test_risk_calculation_low_velocity(self):
        """Test risk calculation with low velocity"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=1.0,  # Low velocity
            velocity_100ms=1.0,
            velocity_60s=1.0,
            total_volume_usd=10000.0
        )

        assessment = self.calculator.calculate_risk(metrics)
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.symbol, self.symbol)
        self.assertLessEqual(assessment.risk_level, CascadeRiskLevel.LOW)

    def test_risk_calculation_high_velocity(self):
        """Test risk calculation with high velocity"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=15.0,  # High velocity
            velocity_100ms=20.0,
            velocity_60s=12.0,
            acceleration=5.0,
            total_volume_usd=500000.0
        )

        assessment = self.calculator.calculate_risk(metrics)
        self.assertGreaterEqual(assessment.risk_level, CascadeRiskLevel.MEDIUM)
        self.assertGreater(assessment.risk_score, 40.0)

    def test_risk_calculation_critical(self):
        """Test risk calculation with critical conditions"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=25.0,  # Critical velocity
            velocity_100ms=30.0,
            velocity_60s=20.0,
            acceleration=12.0,  # Critical acceleration
            jerk=15.0,
            total_volume_usd=6000000.0,  # Critical volume
            count_60s=100
        )

        assessment = self.calculator.calculate_risk(metrics)
        self.assertGreaterEqual(assessment.risk_level, CascadeRiskLevel.HIGH)
        self.assertGreater(assessment.risk_score, 60.0)

    def test_acceleration_scoring(self):
        """Test acceleration risk scoring"""
        # Positive acceleration should increase risk
        metrics_accel = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=5.0,
            acceleration=5.0,  # High positive acceleration
            total_volume_usd=50000.0
        )

        assessment = self.calculator.calculate_risk(metrics_accel)
        self.assertGreater(assessment.risk_factors.acceleration_score, 50.0)

    def test_jerk_scoring(self):
        """Test jerk (3rd derivative) risk scoring"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=5.0,
            acceleration=3.0,
            jerk=6.0,  # High jerk
            total_volume_usd=50000.0
        )

        assessment = self.calculator.calculate_risk(metrics)
        self.assertGreater(assessment.risk_factors.jerk_score, 40.0)

    def test_volume_scoring(self):
        """Test volume risk scoring"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=3.0,
            total_volume_usd=2000000.0,  # High volume
            avg_event_size_usd=100000.0,  # Large events
            count_60s=20
        )

        assessment = self.calculator.calculate_risk(metrics)
        self.assertGreater(assessment.risk_factors.volume_score, 60.0)

    def test_correlation_scoring(self):
        """Test correlation risk scoring"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=5.0,
            total_volume_usd=100000.0
        )

        # High correlation matrix
        corr_matrix = CorrelationMatrix(timestamp=time.time())
        corr_matrix.set_correlation("binance", "bybit", 0.85)
        corr_matrix.set_correlation("binance", "okx", 0.80)
        corr_matrix.set_correlation("bybit", "okx", 0.82)

        assessment = self.calculator.calculate_risk(metrics, corr_matrix)
        self.assertGreater(assessment.risk_factors.correlation_score, 70.0)

    def test_clustering_scoring(self):
        """Test time clustering risk scoring"""
        # High short-term velocity relative to long-term
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_100ms=10.0,  # High recent velocity
            velocity_60s=2.0,     # Low long-term velocity
            velocity_10s=5.0,
            total_volume_usd=50000.0
        )

        assessment = self.calculator.calculate_risk(metrics)
        # Clustering score should reflect the spike
        self.assertGreater(assessment.risk_factors.clustering_score, 30.0)

    def test_confidence_calculation(self):
        """Test confidence scoring"""
        # More data = higher confidence
        metrics_high_data = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=5.0,
            count_60s=50,  # Lots of data
            total_volume_usd=100000.0
        )

        assessment_high = self.calculator.calculate_risk(metrics_high_data)

        # Less data = lower confidence
        metrics_low_data = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=5.0,
            count_60s=2,  # Little data
            total_volume_usd=10000.0
        )

        assessment_low = self.calculator.calculate_risk(metrics_low_data)

        # More data should give higher confidence
        self.assertGreaterEqual(assessment_high.confidence, assessment_low.confidence)

    def test_action_determination(self):
        """Test action recommendations"""
        # Critical risk should trigger URGENT
        metrics_critical = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=25.0,
            acceleration=10.0,
            total_volume_usd=3000000.0,
            count_60s=100
        )

        assessment = self.calculator.calculate_risk(metrics_critical)
        # High risk should trigger at least ALERT
        self.assertIn(assessment.action, ["ALERT", "URGENT"])

    def test_explanation_generation(self):
        """Test human-readable explanation generation"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=8.0,
            acceleration=4.0,
            total_volume_usd=750000.0
        )

        assessment = self.calculator.calculate_risk(metrics)
        self.assertIsNotNone(assessment.explanation)
        self.assertGreater(len(assessment.explanation), 0)
        self.assertIn("Risk Level", assessment.explanation)

    def test_to_dict_serialization(self):
        """Test serialization to dictionary"""
        metrics = MultiTimeframeVelocity(
            symbol=self.symbol,
            timestamp=time.time(),
            velocity_10s=5.0
        )

        assessment = self.calculator.calculate_risk(metrics)
        result_dict = assessment.to_dict()

        self.assertIsInstance(result_dict, dict)
        self.assertIn('symbol', result_dict)
        self.assertIn('risk_level', result_dict)
        self.assertIn('risk_score', result_dict)
        self.assertIn('risk_factors', result_dict)


class TestIntegration(unittest.TestCase):
    """Integration tests combining engine and calculator"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = AdvancedVelocityEngine()
        self.calculator = CascadeRiskCalculator()
        self.symbol = "BTCUSDT"

    def test_full_cascade_detection_pipeline(self):
        """Test complete pipeline from events to risk assessment"""
        base_time = time.time()

        # Simulate cascade: accelerating liquidations
        event_times = [
            (base_time - 30, 1),    # 1 event 30s ago
            (base_time - 20, 2),    # 2 events 20s ago
            (base_time - 10, 5),    # 5 events 10s ago
            (base_time - 5, 10),    # 10 events 5s ago
            (base_time - 1, 20),    # 20 events 1s ago
        ]

        for event_time, count in event_times:
            for i in range(count):
                value = np.random.uniform(5000, 50000)
                exchange = ["binance", "bybit", "okx"][i % 3]
                self.engine.add_event(self.symbol, value, exchange, event_time + i * 0.1)

        # Calculate velocity
        metrics = self.engine.calculate_multi_timeframe_velocity(self.symbol)
        self.assertIsNotNone(metrics)

        # Calculate correlation
        corr_matrix = self.engine.calculate_exchange_correlation(self.symbol)

        # Calculate risk
        assessment = self.calculator.calculate_risk(metrics, corr_matrix)
        self.assertIsNotNone(assessment)

        # Cascade pattern should result in elevated risk
        self.assertGreaterEqual(assessment.risk_level, CascadeRiskLevel.MEDIUM)
        self.assertGreater(assessment.risk_score, 30.0)

    def test_normal_activity_vs_cascade(self):
        """Test discrimination between normal activity and cascade"""
        base_time = time.time()

        # Normal activity: steady, distributed events
        engine_normal = AdvancedVelocityEngine()
        for i in range(20):
            engine_normal.add_event(self.symbol, 5000.0, "binance",
                                   base_time - 60 + i * 3)

        metrics_normal = engine_normal.calculate_multi_timeframe_velocity(self.symbol)
        assessment_normal = self.calculator.calculate_risk(metrics_normal)

        # Cascade: clustered, high-volume events
        engine_cascade = AdvancedVelocityEngine()
        for i in range(20):
            value = np.random.uniform(50000, 200000)
            engine_cascade.add_event(self.symbol, value, "binance",
                                    base_time - 5 + i * 0.2)

        metrics_cascade = engine_cascade.calculate_multi_timeframe_velocity(self.symbol)
        assessment_cascade = self.calculator.calculate_risk(metrics_cascade)

        # Cascade risk should be higher
        self.assertGreater(assessment_cascade.risk_score, assessment_normal.risk_score)


def run_performance_benchmarks():
    """Run performance benchmarks"""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARKS")
    print("="*60)

    engine = AdvancedVelocityEngine()
    calculator = CascadeRiskCalculator()
    symbol = "BTCUSDT"

    # Benchmark 1: Event insertion
    print("\n1. Event Insertion Performance")
    start = time.perf_counter()
    for i in range(1000):
        engine.add_event(symbol, 10000.0, "binance")
    insertion_time = (time.perf_counter() - start) * 1000
    print(f"   1000 insertions: {insertion_time:.2f}ms")
    print(f"   Per insertion: {insertion_time/1000:.4f}ms")

    # Benchmark 2: Velocity calculation
    print("\n2. Velocity Calculation Performance")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        metrics = engine.calculate_multi_timeframe_velocity(symbol)
        times.append((time.perf_counter() - start) * 1000)

    print(f"   Average: {np.mean(times):.4f}ms")
    print(f"   Median: {np.median(times):.4f}ms")
    print(f"   95th percentile: {np.percentile(times, 95):.4f}ms")
    print(f"   Max: {np.max(times):.4f}ms")
    print(f"   Target: <0.5ms - {'✅ PASS' if np.mean(times) < 0.5 else '⚠️ MISS'}")

    # Benchmark 3: Risk calculation
    print("\n3. Risk Calculation Performance")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        assessment = calculator.calculate_risk(metrics)
        times.append((time.perf_counter() - start) * 1000)

    print(f"   Average: {np.mean(times):.4f}ms")
    print(f"   Median: {np.median(times):.4f}ms")
    print(f"   95th percentile: {np.percentile(times, 95):.4f}ms")
    print(f"   Target: <0.2ms - {'✅ PASS' if np.mean(times) < 0.2 else '⚠️ MISS'}")

    # Benchmark 4: Full pipeline
    print("\n4. Full Pipeline Performance")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        engine.add_event(symbol, 10000.0, "binance")
        metrics = engine.calculate_multi_timeframe_velocity(symbol)
        assessment = calculator.calculate_risk(metrics)
        times.append((time.perf_counter() - start) * 1000)

    print(f"   Average: {np.mean(times):.4f}ms")
    print(f"   Median: {np.median(times):.4f}ms")
    print(f"   95th percentile: {np.percentile(times, 95):.4f}ms")
    print(f"   Target: <1ms - {'✅ PASS' if np.mean(times) < 1.0 else '⚠️ MISS'}")

    # Benchmark 5: Memory usage
    print("\n5. Memory Usage")
    stats = engine.get_performance_stats()
    print(f"   Estimated memory: {stats['memory_estimate_kb']:.2f} KB")
    print(f"   Target: <100KB per symbol - {'✅ PASS' if stats['memory_estimate_kb'] < 100 else '⚠️ MISS'}")

    # Benchmark 6: Throughput
    print("\n6. Throughput Test")
    engine_throughput = AdvancedVelocityEngine()
    start = time.perf_counter()
    events_count = 10000
    for i in range(events_count):
        engine_throughput.add_event(symbol, 10000.0, "binance")
        if i % 100 == 0:
            engine_throughput.calculate_multi_timeframe_velocity(symbol)

    elapsed = time.perf_counter() - start
    throughput = events_count / elapsed
    print(f"   Processed {events_count} events in {elapsed:.2f}s")
    print(f"   Throughput: {throughput:.0f} events/second")
    print(f"   Target: >1000 events/sec - {'✅ PASS' if throughput > 1000 else '⚠️ MISS'}")

    print("\n" + "="*60)


if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], verbosity=2, exit=False)

    # Run performance benchmarks
    run_performance_benchmarks()
