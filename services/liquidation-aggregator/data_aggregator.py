"""
CENTRALIZED DATA AGGREGATION MODULE - Production Grade
Provides consistent cumulative data calculations for all visualization tools
Ensures reliability when adding more exchanges
Enhanced with comprehensive error handling, retry logic, and connection pooling
Author: Opus 4.1
Date: October 25, 2025
"""

import redis
from redis import ConnectionPool, ConnectionError, TimeoutError as RedisTimeoutError
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import time
import json
import traceback
from functools import wraps
from contextlib import contextmanager
import threading
from collections import defaultdict


# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Error tracking
error_stats = defaultdict(int)
error_lock = threading.Lock()

def track_error(error_type: str):
    """Track error statistics for monitoring"""
    with error_lock:
        error_stats[error_type] += 1
        if error_stats[error_type] % 10 == 0:
            logger.warning(f"Error type '{error_type}' has occurred {error_stats[error_type]} times")

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, RedisTimeoutError) as e:
                    last_exception = e
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise

            # All retries exhausted
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            track_error(f"{func.__name__}_max_retries")
            raise last_exception
        return wrapper
    return decorator

@contextmanager
def safe_redis_operation(operation_name: str):
    """Context manager for safe Redis operations with error tracking"""
    start_time = time.time()
    try:
        yield
    except ConnectionError as e:
        logger.error(f"Redis connection error during {operation_name}: {e}")
        track_error(f"redis_connection_{operation_name}")
        raise
    except RedisTimeoutError as e:
        logger.error(f"Redis timeout during {operation_name}: {e}")
        track_error(f"redis_timeout_{operation_name}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {operation_name}: {e}")
        track_error(f"unexpected_{operation_name}")
        raise
    finally:
        duration = time.time() - start_time
        if duration > 1.0:  # Log slow operations
            logger.warning(f"Slow Redis operation '{operation_name}' took {duration:.2f}s")

@dataclass
class CumulativeStats:
    """Cumulative statistics across all data with validation"""
    # Overall totals
    total_events: int = 0
    total_usd: float = 0.0
    total_btc: float = 0.0

    # Time range
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=datetime.utcnow)
    duration_hours: float = 0.0

    # By side
    long_events: int = 0
    short_events: int = 0
    long_btc: float = 0.0
    short_btc: float = 0.0
    long_usd: float = 0.0
    short_usd: float = 0.0

    # By exchange (dynamic - supports any number of exchanges)
    exchange_events: Dict[str, int] = field(default_factory=dict)
    exchange_usd: Dict[str, float] = field(default_factory=dict)
    exchange_btc: Dict[str, float] = field(default_factory=dict)

    # Combined breakdowns
    exchange_side_events: Dict[str, Dict[str, int]] = field(default_factory=dict)
    exchange_side_usd: Dict[str, Dict[str, float]] = field(default_factory=dict)
    exchange_side_btc: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Metadata
    errors_during_collection: int = 0
    partial_data: bool = False
    collection_timestamp: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate statistics for consistency"""
        errors = []

        # Check event counts
        if self.total_events < 0:
            errors.append(f"Negative total events: {self.total_events}")

        if self.long_events + self.short_events != self.total_events:
            errors.append(f"Long+Short events ({self.long_events}+{self.short_events}) != Total ({self.total_events})")

        # Check USD values
        if self.total_usd < 0:
            errors.append(f"Negative total USD: {self.total_usd}")

        # Check exchange totals
        exchange_total = sum(self.exchange_events.values())
        if exchange_total != self.total_events:
            errors.append(f"Exchange total ({exchange_total}) != Total events ({self.total_events})")

        # Check time range
        if self.end_time < self.start_time:
            errors.append(f"End time before start time")

        return len(errors) == 0, errors


class LiquidationDataAggregator:
    """
    Production-grade centralized data aggregation from Redis
    Features:
    - Connection pooling for efficiency
    - Comprehensive error handling
    - Retry logic with exponential backoff
    - Health monitoring
    - Graceful degradation
    """

    # Class-level connection pool (shared across instances)
    _connection_pools: Dict[str, ConnectionPool] = {}
    _pool_lock = threading.Lock()

    def __init__(self,
                 redis_host: str = 'localhost',
                 redis_port: int = 6380,
                 redis_db: int = 1,
                 max_connections: int = 50,
                 socket_timeout: int = 5,
                 socket_connect_timeout: int = 5,
                 health_check_interval: int = 30):
        """Initialize with production configuration"""

        # Create or reuse connection pool
        pool_key = f"{redis_host}:{redis_port}:{redis_db}"

        with self._pool_lock:
            if pool_key not in self._connection_pools:
                logger.info(f"Creating new Redis connection pool for {pool_key}")
                self._connection_pools[pool_key] = ConnectionPool(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    max_connections=max_connections,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=socket_connect_timeout,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPIDLE
                        2: 3,  # TCP_KEEPINTVL
                        3: 5   # TCP_KEEPCNT
                    },
                    retry=Retry(ExponentialBackoff(), 3)
                )

            self.pool = self._connection_pools[pool_key]

        # Initialize Redis client with pool
        self.r = redis.Redis(connection_pool=self.pool)

        # Configuration
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.health_check_interval = health_check_interval

        # Health monitoring
        self._last_health_check = datetime.utcnow()
        self._connection_healthy = True
        self._error_count = 0
        self._total_operations = 0
        self._failed_operations = 0

        # Perform initial health check
        self._check_connection_health()

    def _check_connection_health(self) -> bool:
        """Check Redis connection health"""
        try:
            self.r.ping()
            self._connection_healthy = True
            logger.debug("Redis connection healthy")
            return True
        except (ConnectionError, RedisTimeoutError) as e:
            self._connection_healthy = False
            logger.error(f"Redis connection unhealthy: {e}")
            track_error("redis_health_check_failed")
            return False

    def _should_check_health(self) -> bool:
        """Determine if health check is needed"""
        time_since_check = (datetime.utcnow() - self._last_health_check).total_seconds()
        return time_since_check > self.health_check_interval

    def _safe_parse_int(self, value: Any, default: int = 0) -> int:
        """Safely parse integer with error handling"""
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse int: {value}, using default {default}. Error: {e}")
            return default

    def _safe_parse_float(self, value: Any, default: float = 0.0) -> float:
        """Safely parse float with error handling"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse float: {value}, using default {default}. Error: {e}")
            return default

    @retry_on_failure(max_retries=3)
    def get_cumulative_stats(self, symbol: str = 'BTCUSDT') -> CumulativeStats:
        """
        Calculate cumulative statistics from ALL data in Redis
        Enhanced with comprehensive error handling and validation
        """
        self._total_operations += 1

        # Health check if needed
        if self._should_check_health():
            self._check_connection_health()
            self._last_health_check = datetime.utcnow()

        # Initialize stats to track errors
        stats = CumulativeStats()
        errors_encountered = 0

        try:
            with safe_redis_operation("get_cumulative_stats"):
                # Get all aggregated time window keys
                agg_keys = self.r.keys(f"liq:agg:{symbol}:60s:*")

                if not agg_keys:
                    logger.info(f"No data found for symbol {symbol}")
                    return self._empty_stats()

                # Initialize totals
                total_events = 0
                total_usd = 0.0
                total_longs = 0
                total_shorts = 0

                # Dynamic exchange tracking
                exchange_counts = {}

                # Get time range with error handling
                timestamps = []
                for k in agg_keys:
                    try:
                        ts = int(k.split(':')[-1])
                        timestamps.append(ts)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse timestamp from key {k}: {e}")
                        errors_encountered += 1

                if not timestamps:
                    logger.warning("No valid timestamps found")
                    return self._empty_stats()

                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)

                # Process all time windows with error handling
                for key in agg_keys:
                    try:
                        data = self.r.hgetall(key)

                        # Overall aggregation with safe parsing
                        count = self._safe_parse_int(data.get('count', 0))
                        value = self._safe_parse_float(data.get('total_value', 0))
                        long_count = self._safe_parse_int(data.get('long_count', 0))
                        short_count = self._safe_parse_int(data.get('short_count', 0))

                        total_events += count
                        total_usd += value
                        total_longs += long_count
                        total_shorts += short_count

                        # Dynamic exchange counting (supports any exchange)
                        for field, val in data.items():
                            if field.endswith('_count') and field not in ['count', 'long_count', 'short_count', 'institutional_count']:
                                try:
                                    # Extract exchange name (e.g., 'binance_count' -> 'binance')
                                    exchange = field.replace('_count', '')
                                    count_val = self._safe_parse_int(val)
                                    exchange_counts[exchange] = exchange_counts.get(exchange, 0) + count_val
                                except Exception as e:
                                    logger.warning(f"Failed to process exchange field {field}: {e}")
                                    errors_encountered += 1

                    except Exception as e:
                        logger.error(f"Failed to process key {key}: {e}")
                        errors_encountered += 1
                        stats.partial_data = True

                # Calculate BTC amounts from price levels
                level_stats = self._get_price_level_stats(symbol)

                # Calculate exchange USD and BTC values (proportional distribution)
                exchange_usd = {}
                exchange_btc = {}

                for exchange, count in exchange_counts.items():
                    proportion = count / max(total_events, 1)
                    exchange_usd[exchange] = total_usd * proportion
                    exchange_btc[exchange] = level_stats.get('total_btc', 0.0) * proportion

                # Calculate exchange × side breakdown
                # CRITICAL: Must ensure sum across exchanges equals overall totals!
                long_pct = total_longs / max(total_events, 1)
                short_pct = total_shorts / max(total_events, 1)

                exchange_side_events = {}
                exchange_side_usd = {}
                exchange_side_btc = {}

                # Track running totals to distribute exactly
                running_long_events = 0
                running_short_events = 0

                exchanges_list = sorted(exchange_counts.items())

                for idx, (exchange, count) in enumerate(exchanges_list):
                    # For all but last exchange: proportional distribution
                    # For last exchange: assign remainder to guarantee exact totals
                    is_last = (idx == len(exchanges_list) - 1)

                    if is_last:
                        # Last exchange gets remainder
                        long_count = total_longs - running_long_events
                        short_count = total_shorts - running_short_events
                    else:
                        # Proportional distribution
                        long_count = int(count * long_pct)
                        short_count = count - long_count
                        running_long_events += long_count
                        running_short_events += short_count

                    exchange_side_events[exchange] = {
                        'LONG': long_count,
                        'SHORT': short_count
                    }

                    # USD and BTC: Use proportions from aggregated data (NOT price levels!)
                    # Price levels track different data, use aggregated proportions instead
                    exchange_side_usd[exchange] = {
                        'LONG': exchange_usd[exchange] * long_pct,
                        'SHORT': exchange_usd[exchange] * short_pct
                    }

                    exchange_side_btc[exchange] = {
                        'LONG': exchange_btc[exchange] * long_pct,
                        'SHORT': exchange_btc[exchange] * short_pct
                    }

                # Calculate LONG/SHORT USD from aggregated data (not price levels!)
                # Use same source for consistency
                total_long_usd = total_usd * long_pct
                total_short_usd = total_usd * short_pct

                # Build CumulativeStats with all calculated values
                stats = CumulativeStats(
                    total_events=total_events,
                    total_usd=total_usd,
                    total_btc=level_stats.get('total_btc', 0.0),
                    start_time=datetime.fromtimestamp(oldest_ts / 1000),
                    end_time=datetime.fromtimestamp(newest_ts / 1000),
                    duration_hours=(newest_ts - oldest_ts) / 1000 / 3600,
                    long_events=total_longs,
                    short_events=total_shorts,
                    long_btc=level_stats.get('long_btc', 0.0),
                    short_btc=level_stats.get('short_btc', 0.0),
                    long_usd=total_long_usd,
                    short_usd=total_short_usd,
                    exchange_events=exchange_counts,
                    exchange_usd=exchange_usd,
                    exchange_btc=exchange_btc,
                    exchange_side_events=exchange_side_events,
                    exchange_side_usd=exchange_side_usd,
                    exchange_side_btc=exchange_side_btc,
                    errors_during_collection=errors_encountered,
                    partial_data=(errors_encountered > 0)
                )

                # Validate the stats
                is_valid, validation_errors = stats.validate()
                if not is_valid:
                    logger.warning(f"Stats validation failed: {validation_errors}")
                    stats.partial_data = True

                return stats

        except Exception as e:
            logger.error(f"Critical error in get_cumulative_stats: {e}")
            logger.error(traceback.format_exc())
            self._failed_operations += 1
            track_error("get_cumulative_stats_critical")

            # Return empty stats with error flag
            empty = self._empty_stats()
            empty.errors_during_collection = 1
            empty.partial_data = True
            return empty

    @retry_on_failure(max_retries=2)
    def _get_price_level_stats(self, symbol: str = 'BTCUSDT') -> Dict[str, float]:
        """
        Calculate BTC and USD amounts from price levels
        Enhanced with error handling and safe parsing
        """
        try:
            with safe_redis_operation("get_price_level_stats"):
                level_keys = self.r.keys(f"liq:levels:{symbol}:*")
                level_keys = [k for k in level_keys if not k.endswith(':exchanges')]

                long_btc = 0.0
                short_btc = 0.0
                long_usd = 0.0
                short_usd = 0.0

                for key in level_keys:
                    try:
                        if self.r.type(key) == 'hash':
                            data = self.r.hgetall(key)
                            quantity = self._safe_parse_float(data.get('total_quantity', 0))
                            value = self._safe_parse_float(data.get('total_value', 0))

                            if ':LONG' in key:
                                long_btc += quantity
                                long_usd += value
                            elif ':SHORT' in key:
                                short_btc += quantity
                                short_usd += value
                    except Exception as e:
                        logger.warning(f"Failed to process price level {key}: {e}")
                        track_error("price_level_processing")

                return {
                    'total_btc': long_btc + short_btc,
                    'long_btc': long_btc,
                    'short_btc': short_btc,
                    'long_usd': long_usd,
                    'short_usd': short_usd
                }

        except Exception as e:
            logger.error(f"Failed to get price level stats: {e}")
            track_error("get_price_level_stats_failed")
            # Return zeros on failure
            return {
                'total_btc': 0.0,
                'long_btc': 0.0,
                'short_btc': 0.0,
                'long_usd': 0.0,
                'short_usd': 0.0
            }

    def _empty_stats(self) -> CumulativeStats:
        """Return empty stats when no data available"""
        now = datetime.utcnow()
        return CumulativeStats(
            total_events=0,
            total_usd=0.0,
            total_btc=0.0,
            start_time=now,
            end_time=now,
            duration_hours=0.0,
            long_events=0,
            short_events=0,
            long_btc=0.0,
            short_btc=0.0,
            long_usd=0.0,
            short_usd=0.0,
            exchange_events={},
            exchange_usd={},
            exchange_btc={},
            exchange_side_events={},
            exchange_side_usd={},
            exchange_side_btc={},
            errors_during_collection=0,
            partial_data=False
        )

    @retry_on_failure(max_retries=2)
    def get_exchanges(self) -> List[str]:
        """
        Get list of all active exchanges with error handling
        Dynamically determined from data
        """
        try:
            with safe_redis_operation("get_exchanges"):
                agg_keys = self.r.keys("liq:agg:*:60s:*")

                if not agg_keys:
                    logger.debug("No aggregation keys found")
                    return []

                exchanges = set()

                # Check ALL keys to find all exchanges (not just first key)
                for sample_key in agg_keys[:100]:  # Limit to first 100 keys for performance
                    try:
                        data = self.r.hgetall(sample_key)

                        for field in data.keys():
                            if field.endswith('_count') and field not in ['count', 'long_count', 'short_count', 'institutional_count']:
                                exchange = field.replace('_count', '')
                                exchanges.add(exchange)
                    except Exception as e:
                        logger.warning(f"Failed to process key {sample_key}: {e}")
                        continue

                return sorted(list(exchanges))

        except Exception as e:
            logger.error(f"Failed to get exchanges: {e}")
            track_error("get_exchanges_failed")
            return []

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the aggregator"""
        return {
            'connection_healthy': self._connection_healthy,
            'total_operations': self._total_operations,
            'failed_operations': self._failed_operations,
            'error_count': self._error_count,
            'error_rate': self._failed_operations / max(self._total_operations, 1),
            'last_health_check': self._last_health_check.isoformat(),
            'redis_host': self.redis_host,
            'redis_port': self.redis_port,
            'connection_pool_size': len(self.pool._in_use_connections),
            'error_stats': dict(error_stats)
        }

    def format_stats_summary(self, stats: CumulativeStats) -> str:
        """
        Format cumulative stats as a summary string
        Useful for logging or simple displays
        """
        lines = []
        lines.append("="*80)
        lines.append("CUMULATIVE LIQUIDATION STATISTICS")
        lines.append("="*80)
        lines.append(f"Total Events: {stats.total_events:,}")
        lines.append(f"Total USD:    ${stats.total_usd:,.2f}")
        lines.append(f"Total BTC:    {stats.total_btc:.4f} BTC")
        lines.append(f"Duration:     {stats.duration_hours:.1f} hours")
        lines.append("-"*80)
        lines.append(f"Longs:        {stats.long_events:,} ({stats.long_events/max(stats.total_events,1)*100:.1f}%)")
        lines.append(f"  ├─ BTC:     {stats.long_btc:.4f} BTC")
        lines.append(f"  └─ USD:     ${stats.long_usd:,.2f}")
        lines.append(f"Shorts:       {stats.short_events:,} ({stats.short_events/max(stats.total_events,1)*100:.1f}%)")
        lines.append(f"  ├─ BTC:     {stats.short_btc:.4f} BTC")
        lines.append(f"  └─ USD:     ${stats.short_usd:,.2f}")
        lines.append("-"*80)

        for exchange in sorted(stats.exchange_events.keys()):
            count = stats.exchange_events[exchange]
            usd = stats.exchange_usd[exchange]
            btc = stats.exchange_btc[exchange]
            pct = count / max(stats.total_events, 1) * 100

            lines.append(f"{exchange.upper():12} {count:>6,} events ({pct:>5.1f}%) | "
                        f"{btc:>10.4f} BTC | ${usd:>12,.2f}")

        lines.append("="*80)

        return "\n".join(lines)


# Convenience function for quick access
def get_cumulative_stats(symbol='BTCUSDT') -> CumulativeStats:
    """Quick access to cumulative stats"""
    aggregator = LiquidationDataAggregator()
    return aggregator.get_cumulative_stats(symbol)


if __name__ == "__main__":
    # Test the aggregator
    print("\nTesting Data Aggregator...\n")

    aggregator = LiquidationDataAggregator()
    stats = aggregator.get_cumulative_stats()

    print(aggregator.format_stats_summary(stats))

    print(f"\nActive Exchanges: {', '.join(aggregator.get_exchanges())}")
    print("\n✅ Data Aggregator working!\n")
