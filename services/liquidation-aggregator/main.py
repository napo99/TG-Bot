"""
MAIN LIQUIDATION AGGREGATOR APPLICATION
Orchestrates multi-level storage: In-Memory → Redis → TimescaleDB
Supports: Binance + Bybit, BTCUSDT (Phase 1)
"""

import asyncio
import logging
import signal
import sys
import uuid
from typing import Optional, Dict, List
from datetime import datetime

import redis.asyncio as redis

from core_engine import (
    InMemoryLiquidationBuffer,
    RedisLiquidationCache,
    AsyncDatabaseWriter,
    LiquidationEvent,
    CascadeEvent,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    CASCADE_MIN_COUNT,
    CASCADE_WINDOW_SECONDS,
    INSTITUTIONAL_THRESHOLD_USD
)

from exchanges import MultiExchangeLiquidationAggregator


# =============================================================================
# CASCADE DETECTION & RISK SCORING
# =============================================================================

class CascadeDetector:
    """
    Cascade detection with cross-exchange correlation
    6-factor risk analysis
    """

    def __init__(self):
        self.logger = logging.getLogger('cascade_detector')
        self.active_cascades: Dict[str, CascadeEvent] = {}

    def calculate_risk_score(self, events: List[LiquidationEvent]) -> float:
        """
        Calculate 6-factor cascade risk score (0.0 to 2.0+)

        Factors:
        1. Volume concentration
        2. Time compression
        3. Price clustering
        4. Side imbalance
        5. Institutional ratio
        6. Exchange diversity (cross-exchange cascades = higher risk)
        """
        if not events:
            return 0.0

        # Factor 1: Volume concentration
        total_value = sum(e.value_usd for e in events)
        volume_factor = min(total_value / 1_000_000, 1.0) * 0.25  # $1M+ = max

        # Factor 2: Time compression (events per minute)
        time_span_seconds = max(1, (max(e.timestamp_ms for e in events) -
                                   min(e.timestamp_ms for e in events)) / 1000)
        events_per_minute = (len(events) / time_span_seconds) * 60
        time_factor = min(events_per_minute / 10, 1.0) * 0.20  # 10+ per minute = max

        # Factor 3: Price clustering (low std dev = higher risk)
        prices = [e.price for e in events]
        if len(prices) > 1:
            import numpy as np
            price_std = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
            price_factor = max(0, 1.0 - price_std * 10) * 0.20
        else:
            price_factor = 0.20

        # Factor 4: Side imbalance (all same side = higher cascade risk)
        long_count = sum(1 for e in events if e.side_name == 'LONG')
        short_count = len(events) - long_count
        side_imbalance = abs(long_count - short_count) / len(events)
        side_factor = side_imbalance * 0.15

        # Factor 5: Institutional ratio (large liquidations = systemic risk)
        institutional_count = sum(1 for e in events if e.value_usd >= 500_000)
        institutional_ratio = institutional_count / len(events)
        institutional_factor = institutional_ratio * 0.15

        # Factor 6: Exchange diversity (cross-exchange = higher systemic risk)
        unique_exchanges = len(set(e.exchange_name for e in events))
        exchange_factor = (unique_exchanges - 1) * 0.05  # 2+ exchanges = bonus

        # Composite risk score
        total_score = (volume_factor + time_factor + price_factor +
                      side_factor + institutional_factor + exchange_factor)

        return round(total_score, 3)

    def detect_cascade(self, events: List[LiquidationEvent], symbol: str) -> Optional[CascadeEvent]:
        """
        Detect cascade from events
        Cross-exchange cascades get higher risk scores
        """
        if len(events) < CASCADE_MIN_COUNT:
            return None

        total_value = sum(e.value_usd for e in events)
        if total_value < INSTITUTIONAL_THRESHOLD_USD:
            return None

        # Calculate risk score
        risk_score = self.calculate_risk_score(events)

        # Create cascade ID
        cascade_id = str(uuid.uuid4())

        # Get unique exchanges involved
        exchanges = list(set(e.exchange_name for e in events))

        # Create cascade event
        cascade = CascadeEvent(
            cascade_id=cascade_id,
            symbol=symbol,
            start_time_ms=min(e.timestamp_ms for e in events),
            end_time_ms=max(e.timestamp_ms for e in events),
            event_count=len(events),
            total_value_usd=total_value,
            exchanges=exchanges,
            risk_score=risk_score,
            events=events
        )

        # Log cascade
        exchanges_str = ', '.join(exchanges)
        cascade_type = "CROSS-EXCHANGE" if len(exchanges) > 1 else "SINGLE-EXCHANGE"

        self.logger.warning(
            f"🚨 {cascade_type} CASCADE DETECTED: {symbol} | "
            f"{len(events)} liquidations | ${total_value:,.0f} | "
            f"Risk: {risk_score:.2f} | Exchanges: {exchanges_str}"
        )

        return cascade


# =============================================================================
# MAIN APPLICATION
# =============================================================================

class LiquidationAggregatorApp:
    """
    Main liquidation aggregator application
    Coordinates all levels of storage and processing
    """

    def __init__(self):
        self.logger = logging.getLogger('main')

        # Level 1: In-memory buffers
        self.memory_buffer = InMemoryLiquidationBuffer()

        # Level 2: Redis cache
        self.redis_client = None
        self.redis_cache = None

        # Level 3: TimescaleDB writer
        self.db_writer = AsyncDatabaseWriter()

        # Cascade detector
        self.cascade_detector = CascadeDetector()

        # Multi-exchange aggregator
        self.exchange_aggregator = MultiExchangeLiquidationAggregator(
            callback=self.on_liquidation_event
        )

        # Add exchanges (Phase 2: Binance + Bybit + OKX)
        self.exchange_aggregator.add_exchange('binance')
        self.exchange_aggregator.add_exchange('bybit')
        self.exchange_aggregator.add_exchange('okx')

        # Tracking
        self.total_processed = 0
        self.total_institutional = 0
        self.total_cascades = 0

    async def initialize(self):
        """Initialize all components"""
        self.logger.info("🚀 Initializing Liquidation Aggregator...")

        # Initialize Redis
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=False
        )
        self.redis_cache = RedisLiquidationCache(self.redis_client)
        self.logger.info(f"✅ Redis connected (DB {REDIS_DB}, prefix: liq:)")

        # Initialize TimescaleDB
        await self.db_writer.init_db()
        self.logger.info("✅ TimescaleDB connected")

        # Start background database writer
        asyncio.create_task(self.db_writer.background_writer())
        self.logger.info("✅ Background database writer started")

        self.logger.info("🎯 Liquidation Aggregator ready!")

    async def on_liquidation_event(self, event: LiquidationEvent):
        """
        Handle incoming liquidation event
        This is the hot path - must be ultra-fast (<100 microseconds)
        """
        # Level 1: Add to in-memory buffer (O(1), <1 µs)
        self.memory_buffer.add_event(event)
        self.total_processed += 1

        # Log ALL liquidations with detail level based on size
        if event.value_usd >= INSTITUTIONAL_THRESHOLD_USD:
            self.total_institutional += 1
            # Institutional: Full logging
            self.logger.info(
                f"💰 INSTITUTIONAL: {event.exchange_name.upper()} {event.symbol} "
                f"{event.side_name} ${event.value_usd:,.0f} @ ${event.price:,.2f}"
            )
        elif event.value_usd >= 10000:
            # Large retail: Log with less detail
            self.logger.info(
                f"💵 LARGE: {event.exchange_name.upper()} {event.symbol} "
                f"{event.side_name} ${event.value_usd:,.0f}"
            )
        else:
            # Small liquidations: Minimal logging (debug level)
            self.logger.debug(
                f"💸 {event.exchange_name.upper()} {event.side_name} ${event.value_usd:,.2f}"
            )

        # Level 2: Cache in Redis (async, ~1 ms)
        if self.redis_cache:
            try:
                await self.redis_cache.cache_price_level(event)
                await self.redis_cache.cache_time_bucket(event, bucket_seconds=60)
            except Exception as e:
                self.logger.error(f"Redis cache error: {e}")

        # Cascade detection (in-memory, ~10-50 µs)
        cascade_events = self.memory_buffer.detect_cascade_fast(
            event.symbol,
            window_seconds=CASCADE_WINDOW_SECONDS
        )

        cascade_id = None
        risk_score = None

        if cascade_events:
            # Detect cascade with risk scoring
            cascade = self.cascade_detector.detect_cascade(cascade_events, event.symbol)

            if cascade:
                self.total_cascades += 1
                cascade_id = cascade.cascade_id
                risk_score = cascade.risk_score

                # Update Redis cascade status
                if self.redis_cache:
                    try:
                        await self.redis_cache.set_cascade_status(cascade)
                    except Exception as e:
                        self.logger.error(f"Redis cascade status error: {e}")

                # Queue all cascade events for database
                for ce in cascade_events:
                    self.db_writer.queue_event(ce, cascade_id=cascade_id, risk_score=risk_score)

        # Level 3: Queue ALL events for database (not just institutional)
        self.db_writer.queue_event(event, cascade_id=cascade_id, risk_score=risk_score)

    async def print_stats(self):
        """Print periodic statistics"""
        last_processed = 0

        while True:
            await asyncio.sleep(60)  # Every minute

            # Memory buffer stats
            mem_stats = self.memory_buffer.get_stats()

            # Calculate rate since last check
            new_events = self.total_processed - last_processed
            last_processed = self.total_processed

            # Redis stats (count price level keys directly - simpler and more reliable)
            clusters_count = 0
            if self.redis_cache:
                try:
                    # Count keys matching the pattern (faster than querying each)
                    pattern = f"{self.redis_cache.prefix}levels:BTCUSDT:*"
                    keys = []
                    async for key in self.redis_client.scan_iter(match=pattern):
                        if not key.decode().endswith(':exchanges'):
                            keys.append(key)
                    clusters_count = len(keys)
                except Exception as e:
                    # Silently fail - not critical for operation
                    pass

            # Enhanced stats with more detail
            self.logger.info(
                f"📊 STATS: Processed: {self.total_processed} | "
                f"Institutional: {self.total_institutional} | "
                f"Cascades: {self.total_cascades} | "
                f"Events/sec: {mem_stats['events_per_second']:.2f} | "
                f"Price levels: {clusters_count} | "
                f"DB writes: {self.db_writer.written_count}"
            )

            # Show last minute activity
            if new_events > 0:
                self.logger.info(
                    f"📈 Last minute: {new_events} liquidations | "
                    f"Avg rate: {new_events/60:.2f}/sec"
                )

    async def run(self):
        """Run the application"""
        self.logger.info("=" * 80)
        self.logger.info("LIQUIDATION AGGREGATOR - PHASE 2")
        self.logger.info("Exchanges: Binance + Bybit + OKX | Symbol: BTCUSDT")
        self.logger.info("Multi-Level Storage: In-Memory → Redis → TimescaleDB")
        self.logger.info("=" * 80)

        # Initialize all components
        await self.initialize()

        # Start stats printer
        asyncio.create_task(self.print_stats())

        # Start exchange streams
        await self.exchange_aggregator.start_all()

    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("🛑 Shutting down...")

        # Stop exchange streams
        await self.exchange_aggregator.stop_all()

        # Close database writer
        await self.db_writer.close()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        self.logger.info("✅ Shutdown complete")


# =============================================================================
# ENTRY POINT
# =============================================================================

async def main():
    """Main entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator/liquidations.log')
        ]
    )

    # Create application
    app = LiquidationAggregatorApp()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(app.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run application
    try:
        await app.run()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
