#!/usr/bin/env python3
"""
ENHANCED WEBSOCKET MANAGER EXAMPLE
Demonstrates integration of velocity tracking with existing WebSocket handlers

Usage:
    python enhanced_websocket_example.py

Features Demonstrated:
- Zero-breaking integration with existing handlers
- Real-time velocity tracking
- BTC price feed integration
- Redis metrics storage
- Acceleration detection
- Cascade monitoring
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_websocket_manager import (
    EnhancedWebSocketManager,
    VelocityMetrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# EXAMPLE 1: BASIC USAGE (BACKWARD COMPATIBLE)
# =============================================================================

async def example_basic():
    """
    Basic example showing backward compatible usage
    Works exactly like existing code, but with velocity tracking
    """
    logger.info("=" * 80)
    logger.info("EXAMPLE 1: Basic Usage (Backward Compatible)")
    logger.info("=" * 80)

    # Create manager
    manager = EnhancedWebSocketManager(
        symbols=['BTCUSDT'],
        redis_host='localhost',
        redis_port=6379,
        redis_db=1
    )

    # Add exchanges (just like before)
    manager.add_cex_exchange('binance')
    manager.add_cex_exchange('bybit')
    manager.add_cex_exchange('okx')

    # Start all streams
    try:
        logger.info("Starting all streams...")
        await asyncio.wait_for(manager.start_all(), timeout=30)
    except asyncio.TimeoutError:
        logger.info("Running for 30 seconds...")

    # Stop all streams
    await manager.stop_all()

    # Show statistics
    stats = manager.get_stats()
    logger.info(f"Statistics: {stats}")


# =============================================================================
# EXAMPLE 2: WITH CUSTOM CALLBACK
# =============================================================================

async def example_with_callback():
    """
    Example with custom callback for processing events
    Velocity tracking happens automatically in background
    """
    logger.info("=" * 80)
    logger.info("EXAMPLE 2: With Custom Callback")
    logger.info("=" * 80)

    # Event counter
    event_count = 0

    # Custom callback
    async def my_callback(event):
        nonlocal event_count
        event_count += 1

        # Process event (your custom logic here)
        if hasattr(event, 'value_usd'):
            value = event.value_usd
            symbol = event.symbol
            side = event.side_name if hasattr(event, 'side_name') else 'UNKNOWN'

            logger.info(f"Event #{event_count}: {symbol} {side} ${value:,.2f}")
        elif hasattr(event, 'actual_value_usd'):
            # CompactLiquidation
            value = event.actual_value_usd
            symbol = event.symbol
            side = event.side_str

            logger.info(f"Event #{event_count}: {symbol} {side} ${value:,.2f}")

    # Create manager with callback
    manager = EnhancedWebSocketManager(symbols=['BTCUSDT'])
    manager.user_callback = my_callback

    # Add exchanges
    manager.add_cex_exchange('binance')

    # Start
    try:
        await asyncio.wait_for(manager.start_all(), timeout=30)
    except asyncio.TimeoutError:
        pass

    # Stop
    await manager.stop_all()

    logger.info(f"Total events processed: {event_count}")


# =============================================================================
# EXAMPLE 3: MULTI-EXCHANGE WITH DEX
# =============================================================================

async def example_multi_exchange():
    """
    Example combining CEX and DEX streams
    Shows unified velocity tracking across all exchanges
    """
    logger.info("=" * 80)
    logger.info("EXAMPLE 3: Multi-Exchange (CEX + DEX)")
    logger.info("=" * 80)

    # Create manager
    manager = EnhancedWebSocketManager(
        symbols=['BTCUSDT', 'ETHUSDT'],
        redis_host='localhost',
        redis_port=6379
    )

    # Add CEX exchanges
    manager.add_cex_exchange('binance')
    manager.add_cex_exchange('bybit')
    manager.add_cex_exchange('okx')

    # Add DEX (Hyperliquid)
    manager.add_dex_hyperliquid(['BTC', 'ETH', 'SOL'])

    # Start all
    try:
        logger.info("Starting all CEX and DEX streams...")
        await asyncio.wait_for(manager.start_all(), timeout=60)
    except asyncio.TimeoutError:
        pass

    # Stop all
    await manager.stop_all()

    # Show comprehensive stats
    stats = manager.get_stats()
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE STATISTICS")
    logger.info("=" * 80)
    for key, value in stats.items():
        logger.info(f"{key}: {value}")


# =============================================================================
# EXAMPLE 4: VELOCITY MONITORING
# =============================================================================

async def example_velocity_monitoring():
    """
    Example focused on velocity and acceleration monitoring
    Shows real-time velocity metrics
    """
    logger.info("=" * 80)
    logger.info("EXAMPLE 4: Velocity Monitoring")
    logger.info("=" * 80)

    # Create manager
    manager = EnhancedWebSocketManager(symbols=['BTCUSDT'])

    # Add exchanges
    manager.add_cex_exchange('binance')
    manager.add_cex_exchange('bybit')

    # Create velocity monitoring task
    async def monitor_velocity():
        """Monitor velocity metrics in real-time"""
        await asyncio.sleep(5)  # Let some data accumulate

        while True:
            if manager.velocity_tracker:
                # Get velocity metrics for BTCUSDT
                metrics = manager.velocity_tracker.calculate_velocity('BTCUSDT')

                if metrics:
                    logger.info("─" * 80)
                    logger.info(f"Symbol: {metrics.symbol}")
                    logger.info(f"Timestamp: {metrics.timestamp}")
                    logger.info(f"Event Count (10s): {metrics.event_count_10s}")
                    logger.info(f"Event Count (30s): {metrics.event_count_30s}")
                    logger.info(f"Event Count (60s): {metrics.event_count_60s}")
                    logger.info(f"Velocity (10s): {metrics.velocity_10s:.2f} events/s")
                    logger.info(f"Velocity (30s): {metrics.velocity_30s:.2f} events/s")
                    logger.info(f"Velocity (60s): {metrics.velocity_60s:.2f} events/s")
                    logger.info(f"Acceleration: {metrics.acceleration:.2f} events/s²")
                    logger.info(f"Total Value: ${metrics.total_value_usd:,.2f}")
                    logger.info(f"BTC Price: ${metrics.btc_price:,.2f}" if metrics.btc_price else "BTC Price: N/A")
                    logger.info(f"Volatility Factor: {metrics.volatility_factor:.4f}" if metrics.volatility_factor else "Volatility: N/A")

                    # Check for high velocity
                    if metrics.velocity_10s > 5:
                        logger.warning("⚡ HIGH VELOCITY DETECTED!")

                    # Check for high acceleration
                    if abs(metrics.acceleration) > 2:
                        logger.warning("⚡ HIGH ACCELERATION DETECTED!")

            await asyncio.sleep(10)  # Update every 10 seconds

    # Run both tasks concurrently
    try:
        await asyncio.gather(
            manager.start_all(),
            monitor_velocity()
        )
    except KeyboardInterrupt:
        logger.info("Stopping...")

    # Stop
    await manager.stop_all()


# =============================================================================
# EXAMPLE 5: REDIS METRICS INSPECTION
# =============================================================================

async def example_redis_inspection():
    """
    Example showing how to inspect Redis metrics
    Useful for debugging and monitoring
    """
    logger.info("=" * 80)
    logger.info("EXAMPLE 5: Redis Metrics Inspection")
    logger.info("=" * 80)

    import redis.asyncio as redis

    # Create manager
    manager = EnhancedWebSocketManager(symbols=['BTCUSDT'])
    manager.add_cex_exchange('binance')

    # Create Redis inspection task
    async def inspect_redis():
        """Inspect Redis keys and values"""
        await asyncio.sleep(10)  # Let data accumulate

        redis_client = await redis.Redis(host='localhost', port=6379, db=1)

        try:
            while True:
                logger.info("=" * 80)
                logger.info("REDIS INSPECTION")
                logger.info("=" * 80)

                # Check velocity keys
                keys = await redis_client.keys('velocity:*')
                logger.info(f"Velocity keys: {len(keys)}")

                for key in keys[:5]:  # Show first 5
                    data = await redis_client.hgetall(key)
                    logger.info(f"\nKey: {key.decode()}")
                    for field, value in data.items():
                        logger.info(f"  {field.decode()}: {value.decode()}")

                # Check BTC price
                btc_price = await redis_client.get('btc:price:current')
                if btc_price:
                    import json
                    price_data = json.loads(btc_price)
                    logger.info(f"\nBTC Price: ${price_data['price']:,.2f}")
                    logger.info(f"Timestamp: {price_data['timestamp']}")

                await asyncio.sleep(15)

        finally:
            await redis_client.close()

    # Run both tasks
    try:
        await asyncio.gather(
            manager.start_all(),
            inspect_redis()
        )
    except KeyboardInterrupt:
        logger.info("Stopping...")

    await manager.stop_all()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run examples"""
    logger.info("Enhanced WebSocket Manager Examples")
    logger.info("=" * 80)

    # Choose which example to run
    examples = {
        '1': ('Basic Usage', example_basic),
        '2': ('With Custom Callback', example_with_callback),
        '3': ('Multi-Exchange (CEX + DEX)', example_multi_exchange),
        '4': ('Velocity Monitoring', example_velocity_monitoring),
        '5': ('Redis Metrics Inspection', example_redis_inspection)
    }

    print("\nAvailable Examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    choice = input("\nSelect example (1-5, or 'all'): ").strip()

    if choice == 'all':
        # Run all examples sequentially
        for key, (name, func) in examples.items():
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Running Example {key}: {name}")
            logger.info(f"{'=' * 80}\n")
            try:
                await func()
            except Exception as e:
                logger.error(f"Error in example {key}: {e}")
            await asyncio.sleep(2)  # Pause between examples

    elif choice in examples:
        name, func = examples[choice]
        logger.info(f"\nRunning Example {choice}: {name}\n")
        await func()

    else:
        # Default: run velocity monitoring
        logger.info("\nRunning default: Velocity Monitoring\n")
        await example_velocity_monitoring()


if __name__ == "__main__":
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler(sig, frame):
        logger.info("Shutting down gracefully...")
        loop.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
