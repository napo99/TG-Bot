"""
VISUAL LIQUIDATION MONITOR
Real-time terminal-based visualization of liquidations over time
Shows: Day, Time, Value, Exchange breakdown
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
from collections import defaultdict
import os

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class LiquidationVisualMonitor:
    """Real-time visual monitoring of liquidations"""

    def __init__(self):
        self.db_pool = None

    async def init_db(self):
        """Initialize database connection"""
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5432,
            database='liquidations',
            user=os.getenv('USER'),
            min_size=1,
            max_size=3
        )

    async def get_recent_liquidations(self, minutes=60):
        """Get recent liquidations from database"""
        # Use interval multiplication instead of parameterized string
        query = """
        SELECT
            time,
            exchange,
            symbol,
            side,
            price,
            quantity,
            value_usd,
            is_cascade,
            risk_score
        FROM liquidations_significant
        WHERE time >= NOW() - (INTERVAL '1 minute' * $1)
        ORDER BY time ASC
        """

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, minutes)

        return rows

    def create_terminal_chart(self, data, width=80):
        """Create ASCII bar chart for terminal"""
        if not data:
            return "No data available"

        max_value = max(data.values()) if data else 1
        chart = []

        for label, value in sorted(data.items()):
            bar_length = int((value / max_value) * (width - 30))
            bar = '█' * bar_length
            chart.append(f"{label:12} | {bar} ${value:,.0f}")

        return '\n'.join(chart)

    def create_timeline_chart(self, events, hours=24):
        """Create timeline visualization of liquidations"""
        if not events:
            return "No events to display"

        # Group by hour
        hourly_data = defaultdict(lambda: {'binance': 0, 'bybit': 0, 'total': 0})

        for event in events:
            hour = event['time'].replace(minute=0, second=0, microsecond=0)
            exchange = event['exchange']
            value = float(event['value_usd'])

            hourly_data[hour][exchange] += value
            hourly_data[hour]['total'] += value

        # Create chart
        chart_lines = []
        max_value = max((h['total'] for h in hourly_data.values()), default=1)

        for hour in sorted(hourly_data.keys()):
            data = hourly_data[hour]
            time_str = hour.strftime('%m/%d %H:%M')

            # Calculate bar lengths
            binance_len = int((data['binance'] / max_value) * 40)
            bybit_len = int((data['bybit'] / max_value) * 40)

            # Create colored bars
            binance_bar = f"{Colors.YELLOW}{'█' * binance_len}{Colors.END}"
            bybit_bar = f"{Colors.CYAN}{'█' * bybit_len}{Colors.END}"

            chart_lines.append(
                f"{time_str} | "
                f"B:{binance_bar:<50} ${data['binance']:>12,.0f} | "
                f"Y:{bybit_bar:<50} ${data['bybit']:>12,.0f} | "
                f"T:${data['total']:>12,.0f}"
            )

        return '\n'.join(chart_lines)

    async def display_realtime_stats(self):
        """Display real-time statistics"""
        while True:
            os.system('clear' if os.name != 'nt' else 'cls')

            print(f"{Colors.BOLD}{Colors.HEADER}{'='*120}{Colors.END}")
            print(f"{Colors.BOLD}📊 LIQUIDATION MONITOR - REAL-TIME VISUALIZATION{Colors.END}")
            print(f"{Colors.BOLD}{Colors.HEADER}{'='*120}{Colors.END}\n")

            # Get data from last hour
            events = await self.get_recent_liquidations(minutes=60)

            if not events:
                print(f"{Colors.YELLOW}⏳ Waiting for liquidation data...{Colors.END}")
                print(f"\n{Colors.CYAN}Start the aggregator in another terminal:{Colors.END}")
                print(f"  cd /Users/screener-m3/projects/crypto-assistant/services/liquidation-aggregator")
                print(f"  python3 main.py\n")
                await asyncio.sleep(10)
                continue

            # Convert to dict
            events_list = [dict(row) for row in events]

            # Calculate stats
            total_count = len(events_list)
            total_value = sum(float(e['value_usd']) for e in events_list)
            binance_count = sum(1 for e in events_list if e['exchange'] == 'binance')
            bybit_count = sum(1 for e in events_list if e['exchange'] == 'bybit')
            binance_value = sum(float(e['value_usd']) for e in events_list if e['exchange'] == 'binance')
            bybit_value = sum(float(e['value_usd']) for e in events_list if e['exchange'] == 'bybit')
            cascade_count = sum(1 for e in events_list if e['is_cascade'])

            # Calculate LONG vs SHORT breakdown
            long_count = sum(1 for e in events_list if e['side'] == 'LONG')
            short_count = sum(1 for e in events_list if e['side'] == 'SHORT')
            long_value = sum(float(e['value_usd']) for e in events_list if e['side'] == 'LONG')
            short_value = sum(float(e['value_usd']) for e in events_list if e['side'] == 'SHORT')
            long_btc = sum(float(e['quantity']) for e in events_list if e['side'] == 'LONG')
            short_btc = sum(float(e['quantity']) for e in events_list if e['side'] == 'SHORT')

            # Calculate exchange totals in BTC
            binance_btc = sum(float(e['quantity']) for e in events_list if e['exchange'] == 'binance')
            bybit_btc = sum(float(e['quantity']) for e in events_list if e['exchange'] == 'bybit')
            total_btc = binance_btc + bybit_btc

            # Calculate percentages
            binance_pct = (binance_value / total_value * 100) if total_value > 0 else 0
            bybit_pct = (bybit_value / total_value * 100) if total_value > 0 else 0

            # Display header stats
            print(f"{Colors.BOLD}📈 LAST 60 MINUTES - TOTAL:{Colors.END}")
            print(f"{'─'*120}")
            print(f"Total Liquidations: {Colors.BOLD}{total_count}{Colors.END} events | "
                  f"Total BTC: {Colors.BOLD}{total_btc:.4f} BTC{Colors.END} | "
                  f"Total USD: {Colors.BOLD}${total_value:,.0f}{Colors.END} | "
                  f"Cascades: {Colors.BOLD}{cascade_count}{Colors.END}")
            print(f"{'─'*120}\n")

            # LONG vs SHORT breakdown
            print(f"{Colors.BOLD}📊 LONG vs SHORT BREAKDOWN:{Colors.END}")
            print(f"{'─'*120}")
            print(f"{Colors.RED}🔻 LONG Liquidations:{Colors.END}  {long_count:3} events | "
                  f"{long_btc:>10.4f} BTC | ${long_value:>15,.0f} | "
                  f"{(long_value/total_value*100) if total_value > 0 else 0:>5.1f}% of total")
            print(f"{Colors.GREEN}🔺 SHORT Liquidations:{Colors.END} {short_count:3} events | "
                  f"{short_btc:>10.4f} BTC | ${short_value:>15,.0f} | "
                  f"{(short_value/total_value*100) if total_value > 0 else 0:>5.1f}% of total")
            print(f"{'─'*120}\n")

            # Exchange breakdown
            print(f"{Colors.BOLD}🏦 EXCHANGE BREAKDOWN:{Colors.END}")
            print(f"{'─'*120}")
            print(f"{Colors.YELLOW}📊 BINANCE:{Colors.END}")
            print(f"   Events: {binance_count:3} | "
                  f"BTC: {binance_btc:>10.4f} | "
                  f"USD: ${binance_value:>15,.0f} | "
                  f"Share: {binance_pct:>5.1f}% of total")

            print(f"{Colors.CYAN}📊 BYBIT:{Colors.END}")
            print(f"   Events: {bybit_count:3} | "
                  f"BTC: {bybit_btc:>10.4f} | "
                  f"USD: ${bybit_value:>15,.0f} | "
                  f"Share: {bybit_pct:>5.1f}% of total")
            print(f"{'─'*120}\n")

            # Timeline chart (last hour by 10-minute buckets)
            print(f"{Colors.BOLD}⏱️  TIMELINE (10-minute buckets, last 60 minutes):{Colors.END}")
            print(f"{'─'*120}")

            # Group by 10-minute buckets
            bucket_data = defaultdict(lambda: {'binance': 0, 'bybit': 0, 'count': 0})

            for event in events_list:
                # Round to 10-minute bucket
                bucket = event['time'].replace(
                    minute=(event['time'].minute // 10) * 10,
                    second=0,
                    microsecond=0
                )
                exchange = event['exchange']
                value = float(event['value_usd'])

                bucket_data[bucket][exchange] += value
                bucket_data[bucket]['count'] += 1

            max_bucket_value = max((b['binance'] + b['bybit'] for b in bucket_data.values()), default=1)

            for bucket in sorted(bucket_data.keys()):
                data = bucket_data[bucket]
                time_str = bucket.strftime('%H:%M')

                # Calculate percentages
                total_bucket = data['binance'] + data['bybit']
                binance_pct = (data['binance'] / total_bucket * 100) if total_bucket > 0 else 0
                bybit_pct = (data['bybit'] / total_bucket * 100) if total_bucket > 0 else 0

                # Calculate bar length (max 50 chars)
                bar_length = int((total_bucket / max_bucket_value) * 50)
                binance_bar_len = int(bar_length * binance_pct / 100)
                bybit_bar_len = bar_length - binance_bar_len

                bar = (f"{Colors.YELLOW}{'█' * binance_bar_len}{Colors.END}"
                       f"{Colors.CYAN}{'█' * bybit_bar_len}{Colors.END}")

                print(f"{time_str} | {bar:<60} | "
                      f"{data['count']:2} events | "
                      f"${total_bucket:>12,.0f} "
                      f"({Colors.YELLOW}B:{binance_pct:.0f}%{Colors.END} "
                      f"{Colors.CYAN}Y:{bybit_pct:.0f}%{Colors.END})")

            print(f"{'─'*120}\n")

            # Recent liquidations table
            print(f"{Colors.BOLD}📋 LATEST 10 LIQUIDATIONS (Real-Time from Exchanges):{Colors.END}")
            print(f"{'─'*120}")
            print(f"{'Date':<10} | {'Time (UTC)':<10} | {'Exchange':<8} | {'Side':<5} | {'Amount (BTC)':<13} | "
                  f"{'USD Value':<15} | {'Price':<12} | {'Cascade'}")
            print(f"{'─'*120}")

            for event in events_list[-10:]:
                # Format as YYYYMMDD and HH:MM:SS UTC
                date_str = event['time'].strftime('%Y%m%d')
                time_str = event['time'].strftime('%H:%M:%S')
                exchange = event['exchange'].upper()
                side = event['side']
                quantity = float(event['quantity'])
                value_usd = float(event['value_usd'])
                price = float(event['price'])
                cascade = '🚨' if event['is_cascade'] else ''

                # Color code by exchange
                ex_color = Colors.YELLOW if exchange == 'BINANCE' else Colors.CYAN
                side_color = Colors.RED if side == 'LONG' else Colors.GREEN

                print(f"{date_str:<10} | "
                      f"{time_str:<10} | "
                      f"{ex_color}{exchange:<8}{Colors.END} | "
                      f"{side_color}{side:<5}{Colors.END} | "
                      f"{quantity:>12.4f} | "
                      f"${value_usd:>13,.0f} | "
                      f"${price:>10,.2f} | "
                      f"{cascade}")

            print(f"{'─'*120}\n")

            # Exchange comparison
            print(f"{Colors.BOLD}🏦 EXCHANGE COMPARISON (Last 60 min):{Colors.END}")
            print(f"{'─'*120}")

            # Create bar chart
            exchange_data = {
                'Binance': binance_value,
                'Bybit': bybit_value
            }

            max_ex_value = max(exchange_data.values()) if exchange_data else 1

            for exchange, value in exchange_data.items():
                bar_length = int((value / max_ex_value) * 60)
                color = Colors.YELLOW if exchange == 'Binance' else Colors.CYAN
                bar = f"{color}{'█' * bar_length}{Colors.END}"

                count = binance_count if exchange == 'Binance' else bybit_count
                avg = value / count if count > 0 else 0

                print(f"{exchange:8} | {bar:<70} | "
                      f"{count:2} events | "
                      f"${value:>12,.0f} total | "
                      f"${avg:>10,.0f} avg")

            print(f"{'─'*120}\n")

            # Footer
            now = datetime.now()
            print(f"{Colors.CYAN}Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"| Refreshing every 10 seconds... (Ctrl+C to exit){Colors.END}")
            print(f"{Colors.BOLD}{Colors.HEADER}{'='*120}{Colors.END}\n")

            await asyncio.sleep(10)  # Refresh every 10 seconds

    async def run(self):
        """Run the visual monitor"""
        await self.init_db()
        await self.display_realtime_stats()

    async def close(self):
        """Close database connection"""
        if self.db_pool:
            await self.db_pool.close()


async def main():
    """Main entry point"""
    monitor = LiquidationVisualMonitor()

    try:
        await monitor.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down monitor...{Colors.END}")
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
