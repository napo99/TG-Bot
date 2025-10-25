"""
CENTRALIZED DATA AGGREGATION MODULE
Provides consistent cumulative data calculations for all visualization tools
Ensures reliability when adding more exchanges
"""

import redis
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class CumulativeStats:
    """Cumulative statistics across all data"""
    # Overall totals
    total_events: int
    total_usd: float
    total_btc: float

    # Time range
    start_time: datetime
    end_time: datetime
    duration_hours: float

    # By side
    long_events: int
    short_events: int
    long_btc: float
    short_btc: float
    long_usd: float
    short_usd: float

    # By exchange (dynamic - supports any number of exchanges)
    exchange_events: Dict[str, int]  # exchange_name -> count
    exchange_usd: Dict[str, float]   # exchange_name -> usd value
    exchange_btc: Dict[str, float]   # exchange_name -> btc amount

    # Combined breakdowns
    exchange_side_events: Dict[str, Dict[str, int]]  # exchange -> side -> count
    exchange_side_usd: Dict[str, Dict[str, float]]   # exchange -> side -> usd
    exchange_side_btc: Dict[str, Dict[str, float]]   # exchange -> side -> btc


class LiquidationDataAggregator:
    """
    Centralized data aggregation from Redis
    Provides consistent calculations for all dashboards
    """

    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=1):
        self.r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )

    def get_cumulative_stats(self, symbol='BTCUSDT') -> CumulativeStats:
        """
        Calculate cumulative statistics from ALL data in Redis

        Returns complete CumulativeStats object with all aggregations
        """

        # Get all aggregated time window keys
        agg_keys = self.r.keys(f"liq:agg:{symbol}:60s:*")

        if not agg_keys:
            # Return empty stats
            return self._empty_stats()

        # Initialize totals
        total_events = 0
        total_usd = 0.0
        total_longs = 0
        total_shorts = 0

        # Dynamic exchange tracking
        exchange_counts = {}

        # Get time range
        timestamps = [int(k.split(':')[-1]) for k in agg_keys]
        oldest_ts = min(timestamps)
        newest_ts = max(timestamps)

        # Process all time windows
        for key in agg_keys:
            data = self.r.hgetall(key)

            # Overall aggregation
            count = int(data.get('count', 0))
            value = float(data.get('total_value', 0))
            long_count = int(data.get('long_count', 0))
            short_count = int(data.get('short_count', 0))

            total_events += count
            total_usd += value
            total_longs += long_count
            total_shorts += short_count

            # Dynamic exchange counting (supports any exchange)
            for field, val in data.items():
                if field.endswith('_count') and field not in ['count', 'long_count', 'short_count', 'institutional_count']:
                    # Extract exchange name (e.g., 'binance_count' -> 'binance')
                    exchange = field.replace('_count', '')
                    exchange_counts[exchange] = exchange_counts.get(exchange, 0) + int(val)

        # Calculate BTC amounts from price levels
        level_stats = self._get_price_level_stats(symbol)

        # Calculate exchange USD and BTC values (proportional distribution)
        exchange_usd = {}
        exchange_btc = {}

        for exchange, count in exchange_counts.items():
            proportion = count / max(total_events, 1)
            exchange_usd[exchange] = total_usd * proportion
            exchange_btc[exchange] = level_stats['total_btc'] * proportion

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

        # Build CumulativeStats
        return CumulativeStats(
            total_events=total_events,
            total_usd=total_usd,
            total_btc=level_stats['total_btc'],
            start_time=datetime.fromtimestamp(oldest_ts / 1000),
            end_time=datetime.fromtimestamp(newest_ts / 1000),
            duration_hours=(newest_ts - oldest_ts) / 1000 / 3600,
            long_events=total_longs,
            short_events=total_shorts,
            long_btc=level_stats['long_btc'],
            short_btc=level_stats['short_btc'],
            long_usd=total_long_usd,  # From aggregated data, not price levels
            short_usd=total_short_usd,  # From aggregated data, not price levels
            exchange_events=exchange_counts,
            exchange_usd=exchange_usd,
            exchange_btc=exchange_btc,
            exchange_side_events=exchange_side_events,
            exchange_side_usd=exchange_side_usd,
            exchange_side_btc=exchange_side_btc
        )

    def _get_price_level_stats(self, symbol='BTCUSDT') -> Dict[str, float]:
        """
        Calculate BTC and USD amounts from price levels
        More accurate than proportional distribution
        """
        level_keys = self.r.keys(f"liq:levels:{symbol}:*")
        level_keys = [k for k in level_keys if not k.endswith(':exchanges')]

        long_btc = 0.0
        short_btc = 0.0
        long_usd = 0.0
        short_usd = 0.0

        for key in level_keys:
            if self.r.type(key) == 'hash':
                data = self.r.hgetall(key)
                quantity = float(data.get('total_quantity', 0))
                value = float(data.get('total_value', 0))

                if ':LONG' in key:
                    long_btc += quantity
                    long_usd += value
                elif ':SHORT' in key:
                    short_btc += quantity
                    short_usd += value

        return {
            'total_btc': long_btc + short_btc,
            'long_btc': long_btc,
            'short_btc': short_btc,
            'long_usd': long_usd,
            'short_usd': short_usd
        }

    def _empty_stats(self) -> CumulativeStats:
        """Return empty stats when no data available"""
        now = datetime.now()
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
            exchange_side_btc={}
        )

    def get_exchanges(self) -> List[str]:
        """
        Get list of all active exchanges
        Dynamically determined from data
        """
        agg_keys = self.r.keys("liq:agg:*:60s:*")

        if not agg_keys:
            return []

        exchanges = set()

        # Check ALL keys to find all exchanges (not just first key)
        for sample_key in agg_keys:
            data = self.r.hgetall(sample_key)

            for field in data.keys():
                if field.endswith('_count') and field not in ['count', 'long_count', 'short_count', 'institutional_count']:
                    exchange = field.replace('_count', '')
                    exchanges.add(exchange)

        return sorted(list(exchanges))

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
