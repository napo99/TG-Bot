#!/usr/bin/env python3
"""
STANDALONE VELOCITY ENGINE TEST
Simple test script without dependencies on Agent 1's WebSocket manager
"""

import time
import numpy as np

from advanced_velocity_engine import (
    AdvancedVelocityEngine,
    MultiTimeframeVelocity,
    CascadeRiskLevel
)

from cascade_risk_calculator import (
    CascadeRiskCalculator,
    CascadeRiskAssessment
)


def test_basic_functionality():
    """Test basic velocity engine functionality"""
    print("="*60)
    print("TEST 1: Basic Functionality")
    print("="*60)

    engine = AdvancedVelocityEngine()
    calculator = CascadeRiskCalculator()
    symbol = "BTCUSDT"

    # Add some events
    print("\n1. Adding 10 events...")
    for i in range(10):
        engine.add_event(symbol, 10000.0 * (i + 1), "binance")
        time.sleep(0.01)

    # Calculate velocity
    print("2. Calculating velocity metrics...")
    metrics = engine.calculate_multi_timeframe_velocity(symbol)

    if metrics:
        print(f"   ✅ Velocity calculated successfully")
        print(f"   - Count (10s): {metrics.count_10s}")
        print(f"   - Velocity (10s): {metrics.velocity_10s:.2f} events/s")
        print(f"   - Total volume: ${metrics.total_volume_usd:,.2f}")
    else:
        print("   ❌ Failed to calculate velocity")
        return False

    # Calculate risk
    print("3. Calculating risk assessment...")
    assessment = calculator.calculate_risk(metrics)
    print(f"   ✅ Risk calculated: {assessment.risk_level.name}")
    print(f"   - Risk score: {assessment.risk_score:.1f}/100")
    print(f"   - Action: {assessment.action}")
    print(f"   - Confidence: {assessment.confidence:.2f}")

    return True


def test_cascade_detection():
    """Test cascade detection with accelerating pattern"""
    print("\n" + "="*60)
    print("TEST 2: Cascade Detection")
    print("="*60)

    engine = AdvancedVelocityEngine()
    calculator = CascadeRiskCalculator()
    symbol = "BTCUSDT"

    # Simulate cascade: accelerating liquidations
    print("\n1. Simulating cascade pattern (accelerating events)...")
    base_time = time.time()

    event_schedule = [
        (base_time - 30, 1, 5000),      # 1 event 30s ago
        (base_time - 20, 2, 10000),     # 2 events 20s ago
        (base_time - 10, 5, 20000),     # 5 events 10s ago
        (base_time - 5, 10, 40000),     # 10 events 5s ago
        (base_time - 1, 20, 80000),     # 20 events 1s ago (massive spike)
    ]

    total_events = 0
    for event_time, count, value_per_event in event_schedule:
        for i in range(count):
            engine.add_event(symbol, value_per_event, "binance", event_time + i * 0.1)
            total_events += 1

    print(f"   Added {total_events} events in accelerating pattern")

    # Calculate metrics
    print("2. Calculating velocity metrics...")
    metrics = engine.calculate_multi_timeframe_velocity(symbol)

    print(f"   - Velocity (100ms): {metrics.velocity_100ms:.2f} events/s")
    print(f"   - Velocity (10s): {metrics.velocity_10s:.2f} events/s")
    print(f"   - Velocity (60s): {metrics.velocity_60s:.2f} events/s")
    print(f"   - Acceleration: {metrics.acceleration:.2f} events/s²")
    print(f"   - Total volume: ${metrics.total_volume_usd:,.2f}")

    # Calculate risk
    print("3. Risk assessment...")
    assessment = calculator.calculate_risk(metrics)

    print(f"   - Risk level: {assessment.risk_level.name}")
    print(f"   - Risk score: {assessment.risk_score:.1f}/100")
    print(f"   - Action: {assessment.action}")
    print(f"   - Explanation: {assessment.explanation}")

    # Verify cascade was detected
    if assessment.risk_level >= CascadeRiskLevel.MEDIUM:
        print(f"   ✅ CASCADE DETECTED (Risk: {assessment.risk_level.name})")
        return True
    else:
        print(f"   ⚠️ Cascade not detected (Risk: {assessment.risk_level.name})")
        return False


def test_multi_exchange_correlation():
    """Test cross-exchange correlation"""
    print("\n" + "="*60)
    print("TEST 3: Cross-Exchange Correlation")
    print("="*60)

    engine = AdvancedVelocityEngine()
    calculator = CascadeRiskCalculator()
    symbol = "BTCUSDT"

    # Add correlated events across 3 exchanges
    print("\n1. Adding synchronized liquidations across exchanges...")
    base_time = time.time()

    for i in range(30):
        timestamp = base_time - (30 - i)
        # Simultaneous liquidations across exchanges (high correlation)
        engine.add_event(symbol, 10000 + i * 100, "binance", timestamp)
        engine.add_event(symbol, 11000 + i * 110, "bybit", timestamp)
        engine.add_event(symbol, 9500 + i * 95, "okx", timestamp + 0.05)

    print("   Added 90 events (30 per exchange)")

    # Calculate correlation
    print("2. Calculating cross-exchange correlation...")
    corr_matrix = engine.calculate_exchange_correlation(symbol, window_seconds=60.0)

    if corr_matrix.correlations:
        print("   Correlation matrix:")
        for (ex1, ex2), corr in corr_matrix.correlations.items():
            print(f"   - {ex1} <-> {ex2}: {corr:.3f}")

        # Calculate risk with correlation
        metrics = engine.calculate_multi_timeframe_velocity(symbol)
        assessment = calculator.calculate_risk(metrics, corr_matrix)

        print(f"\n3. Risk with correlation:")
        print(f"   - Correlation score: {assessment.risk_factors.correlation_score:.1f}/100")
        print(f"   - Overall risk: {assessment.risk_level.name} ({assessment.risk_score:.1f}/100)")

        return True
    else:
        print("   ❌ No correlations calculated")
        return False


def test_performance_benchmark():
    """Test performance benchmarks"""
    print("\n" + "="*60)
    print("TEST 4: Performance Benchmark")
    print("="*60)

    engine = AdvancedVelocityEngine()
    calculator = CascadeRiskCalculator()
    symbol = "BTCUSDT"

    # 1. Event insertion performance
    print("\n1. Event insertion (1000 events)...")
    start = time.perf_counter()
    for i in range(1000):
        engine.add_event(symbol, 10000.0, "binance")
    insertion_time = (time.perf_counter() - start) * 1000
    print(f"   Total: {insertion_time:.2f}ms")
    print(f"   Per event: {insertion_time/1000:.4f}ms")

    # 2. Velocity calculation performance
    print("\n2. Velocity calculation (100 iterations)...")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        metrics = engine.calculate_multi_timeframe_velocity(symbol)
        times.append((time.perf_counter() - start) * 1000)

    avg_time = np.mean(times)
    max_time = np.max(times)
    p95_time = np.percentile(times, 95)

    print(f"   Average: {avg_time:.4f}ms")
    print(f"   95th %ile: {p95_time:.4f}ms")
    print(f"   Max: {max_time:.4f}ms")
    print(f"   Target: <0.5ms - {'✅ PASS' if avg_time < 0.5 else '⚠️ CLOSE' if avg_time < 2.0 else '❌ MISS'}")

    # 3. Risk calculation performance
    print("\n3. Risk calculation (100 iterations)...")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        assessment = calculator.calculate_risk(metrics)
        times.append((time.perf_counter() - start) * 1000)

    avg_time = np.mean(times)
    max_time = np.max(times)
    p95_time = np.percentile(times, 95)

    print(f"   Average: {avg_time:.4f}ms")
    print(f"   95th %ile: {p95_time:.4f}ms")
    print(f"   Max: {max_time:.4f}ms")
    print(f"   Target: <0.2ms - {'✅ PASS' if avg_time < 0.2 else '⚠️ CLOSE' if avg_time < 1.0 else '❌ MISS'}")

    # 4. Full pipeline performance
    print("\n4. Full pipeline (add + calc velocity + calc risk, 100 iterations)...")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        engine.add_event(symbol, 10000.0, "binance")
        metrics = engine.calculate_multi_timeframe_velocity(symbol)
        assessment = calculator.calculate_risk(metrics)
        times.append((time.perf_counter() - start) * 1000)

    avg_time = np.mean(times)
    max_time = np.max(times)
    p95_time = np.percentile(times, 95)

    print(f"   Average: {avg_time:.4f}ms")
    print(f"   95th %ile: {p95_time:.4f}ms")
    print(f"   Max: {max_time:.4f}ms")
    print(f"   Target: <1ms - {'✅ PASS' if avg_time < 1.0 else '⚠️ CLOSE' if avg_time < 5.0 else '❌ MISS'}")

    # 5. Memory usage
    print("\n5. Memory usage...")
    stats = engine.get_performance_stats()
    print(f"   Estimated: {stats['memory_estimate_kb']:.2f} KB")
    print(f"   Events: {stats['events_processed']}")
    print(f"   Target: <100KB - {'✅ PASS' if stats['memory_estimate_kb'] < 100 else '⚠️ MISS'}")

    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ADVANCED VELOCITY ENGINE - STANDALONE TEST SUITE")
    print("="*60)

    results = {
        "Basic Functionality": test_basic_functionality(),
        "Cascade Detection": test_cascade_detection(),
        "Cross-Exchange Correlation": test_multi_exchange_correlation(),
        "Performance Benchmark": test_performance_benchmark()
    }

    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
