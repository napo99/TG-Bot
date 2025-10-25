#!/usr/bin/env python3
"""
Unified Liquidation Monitor - Professional Trading Dashboard
Combines CEX and DEX liquidations with improved UX
"""

import asyncio
import json
import time
from datetime import datetime
from decimal import Decimal
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Terminal colors for better UX
class Colors:
    # Main colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Styles
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

# =============================================================================
# UNIFIED DATA MODEL
# =============================================================================

class LiquidationSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class UnifiedLiquidation:
    """Universal liquidation event for all exchanges"""
    timestamp_ms: int
    exchange: str
    symbol: str
    side: LiquidationSide
    price: float
    quantity: float
    value_usd: float
    liquidated_user: Optional[str] = None

    @property
    def is_institutional(self) -> bool:
        return self.value_usd >= 100_000

    @property
    def price_level(self) -> int:
        """Round to nearest $100"""
        return int(self.price / 100) * 100


# =============================================================================
# UNIFIED SIDE DETECTOR
# =============================================================================

class UnifiedSideDetector:
    """Handles correct side detection for all exchanges"""

    HLP_LIQUIDATOR = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"

    @classmethod
    def detect(cls, exchange: str, data: Dict) -> Optional[LiquidationSide]:
        """Universal side detection with correct logic per exchange"""

        if exchange == 'binance':
            # Binance: SELL order = LONG liquidation (forced to sell longs)
            order_side = data.get('o', {}).get('S', '')
            return LiquidationSide.LONG if order_side == 'SELL' else LiquidationSide.SHORT

        elif exchange == 'bybit':
            # Bybit: Sell = LONG liquidation, Buy = SHORT liquidation
            side = data.get('side', '')
            return LiquidationSide.LONG if side == 'Sell' else LiquidationSide.SHORT

        elif exchange == 'okx':
            # OKX: Position side directly indicates liquidation type
            pos_side = data.get('posSide', '')
            return LiquidationSide.LONG if pos_side == 'long' else LiquidationSide.SHORT

        elif exchange == 'hyperliquid':
            # Hyperliquid: Check HLP position in users array
            users = data.get('users', [])
            if not users or len(users) < 2:
                return None

            buyer = users[0].lower()
            seller = users[1].lower()
            liquidator = cls.HLP_LIQUIDATOR.lower()

            if buyer == liquidator:
                return LiquidationSide.SHORT  # HLP buying = closing shorts
            elif seller == liquidator:
                return LiquidationSide.LONG   # HLP selling = closing longs

        return None


# =============================================================================
# UNIFIED LIVE MONITOR
# =============================================================================

class UnifiedLiquidationMonitor:
    """Professional liquidation monitor with improved UX"""

    def __init__(self):
        # Data storage
        self.liquidations = deque(maxlen=1000)  # Last 1000 liquidations
        self.exchange_stats = defaultdict(lambda: {
            'long_count': 0, 'short_count': 0,
            'long_volume': 0.0, 'short_volume': 0.0,
            'last_update': 0
        })
        self.symbol_stats = defaultdict(lambda: {
            'long_count': 0, 'short_count': 0,
            'long_volume': 0.0, 'short_volume': 0.0,
            'last_price': 0.0, 'last_size': 0.0,
            'last_side': None
        })

        # Tracking
        self.total_liquidations = 0
        self.start_time = time.time()
        self.last_update = time.time()

        # Display settings
        self.refresh_interval = 1.0  # Refresh every second
        self.display_mode = 'professional'  # professional, simple, detailed

    def clear_screen(self):
        """Clear terminal screen"""
        print('\033[2J\033[H', end='')

    def format_usd(self, value: float) -> str:
        """Format USD values with color coding"""
        if value >= 1_000_000:
            color = Colors.RED + Colors.BOLD
            text = f"${value/1_000_000:.2f}M"
        elif value >= 100_000:
            color = Colors.YELLOW
            text = f"${value/1_000:.0f}K"
        elif value >= 10_000:
            color = Colors.WHITE
            text = f"${value/1_000:.1f}K"
        else:
            color = Colors.DIM
            text = f"${value:.0f}"
        return f"{color}{text}{Colors.RESET}"

    def format_side(self, side: LiquidationSide) -> str:
        """Format side with color"""
        if side == LiquidationSide.LONG:
            return f"{Colors.RED}↓LONG{Colors.RESET}"
        else:
            return f"{Colors.GREEN}↑SHORT{Colors.RESET}"

    def add_liquidation(self, liq: UnifiedLiquidation):
        """Add liquidation event and update statistics"""
        self.liquidations.append(liq)
        self.total_liquidations += 1

        # Update exchange stats
        stats = self.exchange_stats[liq.exchange]
        if liq.side == LiquidationSide.LONG:
            stats['long_count'] += 1
            stats['long_volume'] += liq.value_usd
        else:
            stats['short_count'] += 1
            stats['short_volume'] += liq.value_usd
        stats['last_update'] = time.time()

        # Update symbol stats
        sym_stats = self.symbol_stats[liq.symbol]
        if liq.side == LiquidationSide.LONG:
            sym_stats['long_count'] += 1
            sym_stats['long_volume'] += liq.value_usd
        else:
            sym_stats['short_count'] += 1
            sym_stats['short_volume'] += liq.value_usd
        sym_stats['last_price'] = liq.price
        sym_stats['last_size'] = liq.quantity
        sym_stats['last_side'] = liq.side

    def print_dashboard(self):
        """Print professional trading dashboard"""
        self.clear_screen()
        now = time.time()
        runtime = now - self.start_time

        # Header
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*100}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🔥 UNIFIED LIQUIDATION MONITOR - PROFESSIONAL TRADING DASHBOARD 🔥{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*100}{Colors.RESET}")

        # Overall stats line
        events_per_sec = self.total_liquidations / runtime if runtime > 0 else 0
        total_volume = sum(s['long_volume'] + s['short_volume'] for s in self.exchange_stats.values())
        total_long = sum(s['long_count'] for s in self.exchange_stats.values())
        total_short = sum(s['short_count'] for s in self.exchange_stats.values())

        print(f"\n{Colors.BOLD}📊 OVERALL STATISTICS{Colors.RESET}")
        print(f"Runtime: {Colors.WHITE}{runtime:.0f}s{Colors.RESET} | "
              f"Total: {Colors.YELLOW}{self.total_liquidations:,}{Colors.RESET} | "
              f"Speed: {Colors.CYAN}{events_per_sec:.1f}/s{Colors.RESET} | "
              f"Volume: {self.format_usd(total_volume)} | "
              f"L/S Ratio: {Colors.RED}{total_long}{Colors.RESET}/{Colors.GREEN}{total_short}{Colors.RESET}")

        # Exchange breakdown
        print(f"\n{Colors.BOLD}🏛️ EXCHANGE BREAKDOWN{Colors.RESET}")
        print(f"{'Exchange':<12} {'Long Liq':<12} {'Short Liq':<12} {'Long Vol':<15} {'Short Vol':<15} {'Total Vol':<15} {'Status'}")
        print("-" * 100)

        # Sort exchanges by total volume
        sorted_exchanges = sorted(self.exchange_stats.items(),
                                key=lambda x: x[1]['long_volume'] + x[1]['short_volume'],
                                reverse=True)

        for exchange, stats in sorted_exchanges:
            total_vol = stats['long_volume'] + stats['short_volume']
            time_since = now - stats['last_update'] if stats['last_update'] > 0 else 999

            # Status indicator
            if time_since < 2:
                status = f"{Colors.GREEN}● ACTIVE{Colors.RESET}"
            elif time_since < 10:
                status = f"{Colors.YELLOW}● RECENT{Colors.RESET}"
            else:
                status = f"{Colors.DIM}○ IDLE{Colors.RESET}"

            # Exchange name color based on type
            if exchange == 'hyperliquid':
                ex_color = Colors.MAGENTA  # DEX in purple
            else:
                ex_color = Colors.CYAN  # CEX in cyan

            print(f"{ex_color}{exchange:<12}{Colors.RESET} "
                  f"{Colors.RED}{stats['long_count']:<12}{Colors.RESET} "
                  f"{Colors.GREEN}{stats['short_count']:<12}{Colors.RESET} "
                  f"{self.format_usd(stats['long_volume']):<15} "
                  f"{self.format_usd(stats['short_volume']):<15} "
                  f"{self.format_usd(total_vol):<15} "
                  f"{status}")

        # Top symbols
        print(f"\n{Colors.BOLD}💎 TOP LIQUIDATED SYMBOLS{Colors.RESET}")
        print(f"{'Symbol':<10} {'Price':<12} {'Long':<8} {'Short':<8} {'L/S Ratio':<12} {'Total Vol':<15} {'Last Side'}")
        print("-" * 100)

        # Sort symbols by volume
        sorted_symbols = sorted(self.symbol_stats.items(),
                              key=lambda x: x[1]['long_volume'] + x[1]['short_volume'],
                              reverse=True)[:10]  # Top 10

        for symbol, stats in sorted_symbols:
            total_vol = stats['long_volume'] + stats['short_volume']
            ratio = stats['long_count'] / max(stats['short_count'], 1)

            # Color code the ratio
            if ratio > 1.5:
                ratio_color = Colors.RED  # More longs liquidated
            elif ratio < 0.67:
                ratio_color = Colors.GREEN  # More shorts liquidated
            else:
                ratio_color = Colors.YELLOW  # Balanced

            last_side_str = self.format_side(stats['last_side']) if stats['last_side'] else "-"

            print(f"{Colors.BOLD}{symbol:<10}{Colors.RESET} "
                  f"${stats['last_price']:>10,.0f} "
                  f"{Colors.RED}{stats['long_count']:<8}{Colors.RESET} "
                  f"{Colors.GREEN}{stats['short_count']:<8}{Colors.RESET} "
                  f"{ratio_color}{ratio:>10.2f}x{Colors.RESET} "
                  f"{self.format_usd(total_vol):<15} "
                  f"{last_side_str}")

        # Recent liquidations
        print(f"\n{Colors.BOLD}⚡ RECENT LIQUIDATIONS{Colors.RESET}")
        print(f"{'Time':<10} {'Exchange':<12} {'Symbol':<10} {'Side':<12} {'Price':<12} {'Size':<12} {'Value':<15}")
        print("-" * 100)

        recent = list(self.liquidations)[-10:]  # Last 10
        for liq in reversed(recent):  # Show newest first
            time_str = datetime.fromtimestamp(liq.timestamp_ms/1000).strftime('%H:%M:%S')

            # Highlight institutional liquidations
            if liq.is_institutional:
                row_color = Colors.BOLD + Colors.YELLOW
            else:
                row_color = ""

            print(f"{row_color}{time_str:<10} "
                  f"{liq.exchange:<12} "
                  f"{liq.symbol:<10} "
                  f"{self.format_side(liq.side):<12} "
                  f"${liq.price:>10,.0f} "
                  f"{liq.quantity:>10.4f} "
                  f"{self.format_usd(liq.value_usd):<15}{Colors.RESET}")

        # Cascade detection
        recent_window = [l for l in self.liquidations if l.timestamp_ms > (now - 60) * 1000]
        if len(recent_window) >= 5:
            cascade_volume = sum(l.value_usd for l in recent_window)
            if cascade_volume >= 100_000:
                print(f"\n{Colors.BG_RED}{Colors.BOLD} ⚠️  CASCADE ALERT: "
                      f"{len(recent_window)} liquidations, "
                      f"{self.format_usd(cascade_volume)} in last 60s {Colors.RESET}")

        # Footer
        print(f"\n{Colors.DIM}Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
              f"Press Ctrl+C to exit{Colors.RESET}")

    async def run_demo(self):
        """Run demo with simulated data"""
        print("Starting demo mode with simulated liquidations...")

        import random
        exchanges = ['binance', 'bybit', 'okx', 'hyperliquid']
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ARBUSDT', 'OPUSDT']

        while True:
            # Generate random liquidation
            exchange = random.choice(exchanges)
            symbol = random.choice(symbols)
            side = random.choice([LiquidationSide.LONG, LiquidationSide.SHORT])

            # Price based on symbol
            base_prices = {
                'BTCUSDT': 45000,
                'ETHUSDT': 2500,
                'SOLUSDT': 100,
                'ARBUSDT': 1.2,
                'OPUSDT': 2.5
            }
            price = base_prices.get(symbol, 100) * (1 + random.uniform(-0.02, 0.02))

            # Random size (sometimes institutional)
            if random.random() < 0.1:  # 10% institutional
                quantity = random.uniform(5, 50)
            else:
                quantity = random.uniform(0.01, 2)

            liq = UnifiedLiquidation(
                timestamp_ms=int(time.time() * 1000),
                exchange=exchange,
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                value_usd=price * quantity,
                liquidated_user="0x" + "".join(random.choices("0123456789abcdef", k=8)) if exchange == 'hyperliquid' else None
            )

            self.add_liquidation(liq)
            self.print_dashboard()

            await asyncio.sleep(random.uniform(0.1, 2))  # Random interval


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point"""
    monitor = UnifiedLiquidationMonitor()

    try:
        await monitor.run_demo()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitor stopped by user{Colors.RESET}")
        print(f"Total liquidations processed: {monitor.total_liquidations:,}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")