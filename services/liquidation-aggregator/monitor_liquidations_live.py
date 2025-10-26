#!/usr/bin/env python3
"""
Enhanced Hyperliquid liquidation monitor with live activity indicators
Shows trade flow, prices, and activity to prove it's working
"""

import asyncio
import contextlib
import json
import sys
import os
from datetime import datetime
from collections import defaultdict, deque
import websockets
from typing import Dict, List, Optional

from dex.hyperliquid_liquidation_registry import (
    HyperLiquidLiquidationRegistry,
)

# Add repository paths to import local modules
REPO_ROOT = os.path.dirname(__file__)
SERVICE_PARENT = os.path.join(REPO_ROOT, '..', '..')

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if SERVICE_PARENT not in sys.path:
    sys.path.insert(0, SERVICE_PARENT)

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

class LiveLiquidationMonitor:
    def __init__(self):
        self.ws_url = "wss://api.hyperliquid.xyz/ws"
        self.api_base = "https://api.hyperliquid.xyz"
        self.liquidation_registry = HyperLiquidLiquidationRegistry()

        # Aggregation data
        self.liquidations_by_token = defaultdict(lambda: {
            'long_count': 0,
            'short_count': 0,
            'long_volume': 0.0,
            'short_volume': 0.0,
            'total_volume': 0.0,
            'last_price': 0.0,
            'liquidations': []
        })

        # Live activity tracking
        self.latest_prices = {}
        self.trades_per_second = deque(maxlen=60)  # Last 60 seconds
        self.last_activity = {}  # Track last trade time per coin
        self.last_trade_details = {}  # Track last trade size and side
        self.active_coins = set()  # Coins with recent activity
        self.liquidation_timestamps = defaultdict(list)  # Track liquidation times per coin

        self.total_liquidations = 0
        self.total_trades_processed = 0
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.last_trade_count = 0

    def format_usd(self, value):
        """Format USD values nicely"""
        if value >= 1000000:
            return f"${value/1000000:.2f}M"
        elif value >= 1000:
            return f"${value/1000:.2f}K"
        else:
            return f"${value:.2f}"

    def get_recent_liquidations(self, coin, seconds=3600):
        """Get liquidation stats for a coin in the last N seconds"""
        now = datetime.now().timestamp()
        cutoff = now - seconds

        result = {'long_count': 0, 'short_count': 0, 'volume': 0}

        if coin in self.liquidation_timestamps:
            for liq_data in self.liquidation_timestamps[coin]:
                if liq_data['timestamp'] > cutoff:
                    if liq_data['side'] == 'LONG':
                        result['long_count'] += 1
                    else:
                        result['short_count'] += 1
                    result['volume'] += liq_data['value']

        return result

    def clear_screen(self):
        """Clear terminal screen"""
        print('\033[2J\033[H', end='')

    def print_live_dashboard(self):
        """Print live dashboard with activity indicators"""
        now = datetime.now()
        runtime = (now - self.start_time).total_seconds()

        # Calculate trades per second
        time_diff = (now - self.last_update_time).total_seconds()
        if time_diff > 0:
            tps = (self.total_trades_processed - self.last_trade_count) / time_diff
            self.trades_per_second.append(tps)
            self.last_trade_count = self.total_trades_processed
            self.last_update_time = now

        avg_tps = sum(self.trades_per_second) / len(self.trades_per_second) if self.trades_per_second else 0

        # Clear and redraw header
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🔴 HYPERLIQUID LIVE LIQUIDATION MONITOR 🔴{Colors.RESET}")
        print("="*80)

        # Live stats line
        print(f"{Colors.GREEN}⚡ LIVE{Colors.RESET} | ", end='')
        print(f"Runtime: {Colors.WHITE}{runtime:.0f}s{Colors.RESET} | ", end='')
        print(f"Trades: {Colors.YELLOW}{self.total_trades_processed:,}{Colors.RESET} | ", end='')
        print(f"Speed: {Colors.CYAN}{avg_tps:.1f} trades/sec{Colors.RESET} | ", end='')
        print(f"Liquidations: {Colors.BOLD}{Colors.RED}{self.total_liquidations}{Colors.RESET}")
        print("="*80)

        # Registry health
        registry_stats = self.liquidation_registry.snapshot()
        cached_fills = registry_stats.get("cached_fills", 0)
        last_fill_epoch = registry_stats.get("last_fill_epoch") or 0
        if last_fill_epoch:
            age_seconds = max(0, now.timestamp() - last_fill_epoch)
            last_fill_str = datetime.fromtimestamp(last_fill_epoch).strftime('%H:%M:%S')
            age_str = f"{age_seconds:.0f}s ago"
        else:
            last_fill_str = "N/A"
            age_str = "no fills yet"

        print(f"{Colors.DIM}Registry cache: {cached_fills} fills | Last fill: {last_fill_str} ({age_str}){Colors.RESET}")

        # Show top 5 most active coins with live prices
        print(f"\n{Colors.BOLD}📈 LIVE MARKET ACTIVITY:{Colors.RESET}")
        print(f"{'Coin':<8} {'Price':<12} {'Last Size':<10} {'Side':<6} {'1h Liq Vol':<12} {'Time':<8} {'Status'}")
        print("-"*85)

        # Fixed coin list to prevent flickering - show major coins + most liquidated
        major_coins = ['BTC', 'ETH', 'SOL', 'ARB', 'MATIC', 'AVAX', 'OP', 'INJ', 'SUI', 'APT']

        # Add any coins with recent liquidations
        liquidated_coins = [coin for coin in self.liquidations_by_token.keys()
                           if coin not in major_coins][:5]

        display_coins = major_coins[:10 - len(liquidated_coins)] + liquidated_coins

        # Get data for display coins (in fixed order to prevent jumping)
        active_coins_sorted = []
        for coin in display_coins:
            if coin in self.latest_prices:
                active_coins_sorted.append((coin, self.latest_prices[coin]))

        for coin, price in active_coins_sorted:
            last_trade = self.last_activity.get(coin, 0)
            time_since = (now.timestamp() - last_trade) if last_trade else 999

            # Get last trade info
            last_trade_info = self.last_trade_details.get(coin, {})
            last_size = last_trade_info.get('size', 0)
            last_side = last_trade_info.get('side', '')

            # Activity indicator
            if time_since < 1:
                status = f"{Colors.GREEN}● LIVE{Colors.RESET}"
            elif time_since < 5:
                status = f"{Colors.YELLOW}● ACT{Colors.RESET}"
            elif time_since < 30:
                status = f"{Colors.DIM}○ idle{Colors.RESET}"
            else:
                status = f"{Colors.DIM}○ old{Colors.RESET}"

            # Side indicator color
            if last_side == 'B':  # Buy
                side_str = f"{Colors.GREEN}BUY {Colors.RESET}"
            elif last_side == 'A':  # Sell
                side_str = f"{Colors.RED}SELL{Colors.RESET}"
            else:
                side_str = "    "

            # Price color based on recent liquidations (1h)
            token_data = self.liquidations_by_token.get(coin, {})
            recent_liqs = self.get_recent_liquidations(coin, 3600)  # Last hour

            if recent_liqs['long_count'] > recent_liqs['short_count']:
                price_color = Colors.RED  # More longs liquidated recently
            elif recent_liqs['short_count'] > 0:
                price_color = Colors.GREEN  # More shorts liquidated recently
            else:
                price_color = Colors.WHITE

            # Format size based on value
            size_str = f"{last_size:.4f}" if last_size > 0 else "-"
            if len(size_str) > 9:
                size_str = f"{last_size:.2f}"

            # 1h liquidation volume
            hour_vol = recent_liqs.get('volume', 0)

            print(f"{coin:<8} {price_color}${price:>10,.2f}{Colors.RESET} "
                  f"{size_str:>10} {side_str} "
                  f"{self.format_usd(hour_vol):>12} "
                  f"{f'{time_since:.1f}s':>8} {status}")

        # Liquidation summary if any
        if self.total_liquidations > 0:
            print(f"\n{Colors.BOLD}💥 LIQUIDATIONS SUMMARY:{Colors.RESET}")
            total_long = sum(d['long_count'] for d in self.liquidations_by_token.values())
            total_short = sum(d['short_count'] for d in self.liquidations_by_token.values())
            total_vol = sum(d['total_volume'] for d in self.liquidations_by_token.values())

            print(f"Total: {self.total_liquidations} | ", end='')
            print(f"{Colors.RED}Longs: {total_long}{Colors.RESET} | ", end='')
            print(f"{Colors.GREEN}Shorts: {total_short}{Colors.RESET} | ", end='')
            print(f"Volume: {Colors.BOLD}{self.format_usd(total_vol)}{Colors.RESET}")

            # Top liquidated coins
            if self.liquidations_by_token:
                top_coins = sorted(self.liquidations_by_token.items(),
                                 key=lambda x: x[1]['total_volume'],
                                 reverse=True)[:3]
                print(f"\nTop liquidated: ", end='')
                for coin, data in top_coins:
                    total = data['long_count'] + data['short_count']
                    print(f"{coin}({total}) ", end='')
        else:
            print(f"\n{Colors.YELLOW}⏳ Waiting for liquidations...{Colors.RESET}")
            if registry_stats.get("cached_fills", 0) == 0:
                print(f"{Colors.DIM}Registry has not seen recent HyperLiquid fills yet. Keep the monitor running during active sessions.{Colors.RESET}")
            else:
                print(f"{Colors.DIM}Liquidations occur during high volatility. Monitor is actively scanning all trades.{Colors.RESET}")

        print(f"\n{Colors.DIM}Press Ctrl+C to stop and see detailed stats{Colors.RESET}")

    async def process_trade(self, trade: Dict) -> Optional[Dict]:
        """Process a trade and check if it's a liquidation"""
        self.total_trades_processed += 1

        coin = trade.get('coin', '')
        price = float(trade.get('px', 0))
        size = float(trade.get('sz', 0))
        side = trade.get('side', '')  # B or A

        # Update latest price, activity, and trade details
        if coin and price > 0:
            self.latest_prices[coin] = price
            self.last_activity[coin] = datetime.now().timestamp()
            self.last_trade_details[coin] = {
                'size': size,
                'side': side,
                'price': price
            }
            self.active_coins.add(coin)

        # Check for liquidation
        detection = await self.liquidation_registry.classify_trade(trade)
        if not detection:
            return None

        side = detection.get('side')
        if side not in ('LONG', 'SHORT'):
            return None

        participants = detection.get('users', [])
        liquidated_user = self._guess_liquidated_user(side, participants)

        return {
            'coin': detection.get('coin', coin),
            'side': side,
            'price': detection.get('price', price),
            'size': detection.get('size', float(trade.get('sz', 0))),
            'value': detection.get('value', price * float(trade.get('sz', 0))),
            'timestamp': detection.get('timestamp', int(trade.get('time', 0)) / 1000),
            'liquidated_user': liquidated_user,
            'participants': participants,
            'evidence': detection.get('source'),
        }

    @staticmethod
    def _guess_liquidated_user(side: str, participants: List[str]) -> Optional[str]:
        """
        Try to infer the liquidated address from participant ordering.

        HyperLiquid currently lists [buyer, seller]. During a CLOSE LONG,
        the liquidator sells to close the long, so the buyer is the party
        being closed out. The opposite applies for CLOSE SHORT events.
        """
        if len(participants) < 2:
            return None

        buyer, seller = participants[0], participants[1]

        if side == 'LONG':
            return buyer
        if side == 'SHORT':
            return seller

        return None

    def print_liquidation_alert(self, liq):
        """Print a liquidation with alert"""
        timestamp = datetime.fromtimestamp(liq['timestamp'])

        if liq['side'] == 'LONG':
            color = Colors.RED
            arrow = "↓"
            desc = "LONG LIQUIDATION"
        else:
            color = Colors.GREEN
            arrow = "↑"
            desc = "SHORT LIQUIDATION"

        # Clear line and print alert
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  LIQUIDATION ALERT #{self.total_liquidations} ⚠️{Colors.RESET}")
        print(f"Time: {timestamp.strftime('%H:%M:%S')} | Token: {Colors.BOLD}{liq['coin']}{Colors.RESET}")
        print(f"Type: {color}{arrow} {desc}{Colors.RESET} | Price: ${liq['price']:,.2f}")
        print(f"Size: {liq['size']:.6f} | Value: {Colors.BOLD}{self.format_usd(liq['value'])}{Colors.RESET}")
        if liq.get('liquidated_user'):
            print(f"User: {liq['liquidated_user'][:10]}...")
        elif liq.get('participants'):
            masked = ", ".join(p[:6] + "…" for p in liq['participants'])
            print(f"Participants: {masked}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")

        # Wait a bit to show the alert
        asyncio.create_task(self.pause_and_refresh())

    async def pause_and_refresh(self):
        """Pause to show alert then refresh dashboard"""
        await asyncio.sleep(3)
        self.print_live_dashboard()

    async def get_all_coins(self):
        """Get list of all tradeable coins"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base}/info",
                                      json={"type": "meta"}) as response:
                    if response.status == 200:
                        data = await response.json()
                        universe = data.get('universe', [])
                        coins = [asset.get('name') for asset in universe if asset.get('name')]
                        return coins
        except Exception as e:
            print(f"Error getting coins: {e}")
        return ["BTC", "ETH", "SOL", "ARB", "MATIC", "AVAX", "OP", "INJ", "SUI", "APT"]

    async def dashboard_updater(self):
        """Update dashboard every 2 seconds"""
        while True:
            await asyncio.sleep(2)
            self.print_live_dashboard()

    async def monitor_with_activity(self):
        """Monitor with live activity indicators"""
        print(f"{Colors.CYAN}Initializing...{Colors.RESET}")

        # Get all available coins
        coins = await self.get_all_coins()
        print(f"Found {len(coins)} tokens to monitor")

        await self.liquidation_registry.start()

        dashboard_task = None

        try:
            async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as ws:
                print(f"{Colors.GREEN}Connected to WebSocket{Colors.RESET}")

                # Subscribe to all coins
                for coin in coins:
                    subscribe_msg = {
                        "method": "subscribe",
                        "subscription": {
                            "type": "trades",
                            "coin": coin
                        }
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    await asyncio.sleep(0.01)

                print(f"Subscribed to {len(coins)} tokens\n")

                # Start dashboard updater
                dashboard_task = asyncio.create_task(self.dashboard_updater())

                # Initial dashboard
                self.print_live_dashboard()

                # Process messages
                async for message in ws:
                    data = json.loads(message)

                    if data.get('channel') == 'trades':
                        trades = data.get('data', [])

                        for trade in trades:
                            liq = await self.process_trade(trade)

                            if liq:
                                self.total_liquidations += 1

                                # Update aggregated stats
                                token_data = self.liquidations_by_token[liq['coin']]

                                if liq['side'] == 'LONG':
                                    token_data['long_count'] += 1
                                    token_data['long_volume'] += liq['value']
                                else:
                                    token_data['short_count'] += 1
                                    token_data['short_volume'] += liq['value']

                                token_data['total_volume'] += liq['value']
                                token_data['last_price'] = liq['price']

                                # Track liquidation timestamp for recent calculations
                                self.liquidation_timestamps[liq['coin']].append({
                                    'timestamp': liq['timestamp'],
                                    'side': liq['side'],
                                    'value': liq['value']
                                })

                                # Keep only last 1000 liquidations per coin
                                if len(self.liquidation_timestamps[liq['coin']]) > 1000:
                                    self.liquidation_timestamps[liq['coin']] = self.liquidation_timestamps[liq['coin']][-1000:]

                                # Print alert
                                self.print_liquidation_alert(liq)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Stopped by user{Colors.RESET}")
            self.print_final_stats()
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        finally:
            if dashboard_task:
                dashboard_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await dashboard_task
            await self.liquidation_registry.close()

    def print_final_stats(self):
        """Print final aggregated statistics"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 FINAL LIQUIDATION REPORT{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")

        runtime = (datetime.now() - self.start_time).total_seconds()
        print(f"\nTotal Runtime: {runtime:.0f} seconds")
        print(f"Total Trades Processed: {self.total_trades_processed:,}")
        print(f"Total Liquidations: {self.total_liquidations}")
        print(f"Average Speed: {self.total_trades_processed/runtime:.1f} trades/sec")

        if self.liquidations_by_token:
            print(f"\n{Colors.BOLD}BY TOKEN BREAKDOWN:{Colors.RESET}")
            print(f"{'Token':<10} {'Long Liq':<10} {'Short Liq':<10} {'Total Vol':<12} {'Last Price'}")
            print("-"*60)

            sorted_tokens = sorted(self.liquidations_by_token.items(),
                                 key=lambda x: x[1]['total_volume'],
                                 reverse=True)

            for token, data in sorted_tokens:
                if data['long_count'] + data['short_count'] > 0:
                    print(f"{token:<10} "
                          f"{Colors.RED}{data['long_count']:<10}{Colors.RESET} "
                          f"{Colors.GREEN}{data['short_count']:<10}{Colors.RESET} "
                          f"{self.format_usd(data['total_volume']):<12} "
                          f"${data.get('last_price', 0):,.2f}")


async def main():
    """Main entry point"""
    monitor = LiveLiquidationMonitor()
    await monitor.monitor_with_activity()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program terminated{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
