#!/usr/bin/env python3
"""
Enhanced Hyperliquid liquidation monitor with live activity indicators
Shows trade flow, prices, velocity, and registry health to prove it's working.
"""

import argparse
import asyncio
import contextlib
import json
import sys
import os
import time
from datetime import datetime
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Sequence, Tuple

import websockets

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from loguru import logger

from dex.hyperliquid_liquidation_registry import HyperLiquidLiquidationRegistry

# Add repository paths to import local modules
REPO_ROOT = os.path.dirname(__file__)
SERVICE_PARENT = os.path.join(REPO_ROOT, '..', '..')

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if SERVICE_PARENT not in sys.path:
    sys.path.insert(0, SERVICE_PARENT)

MAJOR_COINS: List[str] = ["BTC", "ETH", "SOL", "XRP", "BNB"]
DEFAULT_WATCHLIST: List[str] = list(MAJOR_COINS)


def _configure_logging() -> None:
    """Route verbose registry logs to file while keeping console noise low."""

    # Remove default stderr handler to avoid duplicate output.
    logger.remove()

    log_level_console = os.getenv("HYPERLIQUID_CONSOLE_LEVEL", "ERROR").upper()
    log_level_file = os.getenv("HYPERLIQUID_FILE_LEVEL", "INFO").upper()
    log_dir = os.getenv(
        "HYPERLIQUID_LOG_DIR",
        os.path.join(SERVICE_PARENT, "logs"),
    )
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "hyperliquid_monitor.log")

    # Console handler – default ERROR to keep dashboard clean.
    logger.add(
        sys.stderr,
        level=log_level_console,
        backtrace=False,
        diagnose=False,
    )

    # File handler – capture full telemetry for later review.
    logger.add(
        log_path,
        level=log_level_file,
        rotation="1 day",
        retention="7 days",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )


_configure_logging()

class LiveLiquidationMonitor:
    def __init__(
        self,
        *,
        coins: Optional[Sequence[str]] = None,
        exclude_coins: Optional[Sequence[str]] = None,
        max_coins: Optional[int] = None,
        display_watchlist: Optional[Sequence[str]] = None,
        registry_poll_interval: Optional[float] = None,
    ):
        self.ws_url = "wss://api.hyperliquid.xyz/ws"
        self.api_base = "https://api.hyperliquid.xyz"
        registry_kwargs = {}
        if registry_poll_interval and registry_poll_interval > 0:
            registry_kwargs["poll_interval"] = float(registry_poll_interval)
        self.liquidation_registry = HyperLiquidLiquidationRegistry(**registry_kwargs)

        self._requested_coins = (
            [coin.upper() for coin in coins] if coins else None
        )
        self._excluded_coins = {
            coin.upper() for coin in (exclude_coins or [])
        }
        self._max_coins = max_coins if max_coins and max_coins > 0 else None
        self.max_display_rows = 20
        self.max_vault_rows = 18
        self._custom_display_watchlist = (
            [coin.upper() for coin in display_watchlist] if display_watchlist else None
        )
        self.watchlist: List[str] = (
            list(self._custom_display_watchlist)
            if self._custom_display_watchlist is not None
            else (list(self._requested_coins) if self._requested_coins else list(DEFAULT_WATCHLIST))
        )
        self.dynamic_watchlist: List[str] = list(DEFAULT_WATCHLIST)
        self.subscribed_coins: List[str] = []
        self.missing_requested: List[str] = []
        self._dynamic_display_limit = 6

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
        self.detection_latency_samples: deque = deque(maxlen=240)
        self.last_detection_latency: Optional[float] = None
        self._last_throttle_total = 0

        self.total_liquidations = 0
        self.total_trades_processed = 0
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.last_trade_count = 0
        self.recent_alerts: deque = deque(maxlen=10)

        # Rendering
        self.console = Console()
        self.refresh_interval = 2.0
        self._render_task: Optional[asyncio.Task] = None
        self._render_running: bool = False

        # Connection telemetry
        self.connection_state: str = "initializing"
        self.last_connection_error: Optional[str] = None

    def format_usd(self, value):
        """Format USD values nicely"""
        if value >= 1000000:
            return f"${value/1000000:.2f}M"
        elif value >= 1000:
            return f"${value/1000:.2f}K"
        else:
            return f"${value:.2f}"

    def format_usd_short(self, value: float) -> str:
        """Compact USD formatter for dense tables."""
        if value <= 0:
            return "—"
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        if value >= 1_000:
            return f"${value/1_000:.1f}K"
        if value >= 100:
            return f"${value:,.0f}"
        if value >= 1:
            return f"${value:,.1f}"
        return f"${value:.2f}"

    def _liquidation_window_stats(self, window_seconds: int) -> Dict[str, Any]:
        """Aggregate liquidation activity for a rolling window."""
        cutoff = time.time() - window_seconds
        long_notional = 0.0
        short_notional = 0.0
        long_count = 0
        short_count = 0
        per_symbol: Dict[str, Dict[str, float]] = defaultdict(lambda: {"notional": 0.0, "count": 0})

        for symbol, entries in self.liquidation_timestamps.items():
            for entry in entries:
                if entry['timestamp'] < cutoff:
                    continue
                value = float(entry.get('value', 0.0) or 0.0)
                side = entry.get('side')
                if side == 'LONG':
                    long_notional += value
                    long_count += 1
                elif side == 'SHORT':
                    short_notional += value
                    short_count += 1
                else:
                    continue

                symbol_stats = per_symbol[symbol]
                symbol_stats["notional"] += value
                symbol_stats["count"] += 1

        total_notional = long_notional + short_notional
        return {
            "long_notional": long_notional,
            "short_notional": short_notional,
            "total_notional": total_notional,
            "long_count": long_count,
            "short_count": short_count,
            "per_symbol": per_symbol,
        }

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

    def _update_throughput_metrics(self, now: datetime) -> float:
        """Update rolling throughput metrics and return average trades/sec."""
        time_diff = (now - self.last_update_time).total_seconds()
        if time_diff > 0:
            tps = (self.total_trades_processed - self.last_trade_count) / time_diff
            self.trades_per_second.append(max(tps, 0.0))
            self.last_trade_count = self.total_trades_processed
            self.last_update_time = now

        if not self.trades_per_second:
            return 0.0
        return sum(self.trades_per_second) / len(self.trades_per_second)

    @staticmethod
    def _format_seconds(value: float) -> str:
        if value >= 3600:
            return f"{value/3600:.1f}h"
        if value >= 60:
            return f"{value/60:.1f}m"
        return f"{value:.0f}s"

    def _latency_metrics(self) -> Tuple[Optional[float], Optional[float]]:
        """Return average and last detection latencies in seconds."""
        if not self.detection_latency_samples:
            return None, self.last_detection_latency
        average = sum(self.detection_latency_samples) / len(self.detection_latency_samples)
        return average, self.last_detection_latency

    @staticmethod
    def _format_latency(value: Optional[float]) -> str:
        if value is None:
            return "—"
        if value < 1:
            return f"{value * 1000:.0f} ms"
        return f"{value:.2f} s"

    @staticmethod
    def _format_price_compact(value: Optional[float]) -> str:
        if value is None:
            return "—"
        if value >= 1000:
            return f"${value:,.0f}"
        if value >= 10:
            return f"${value:,.2f}"
        if value >= 1:
            return f"${value:,.3f}"
        return f"${value:.4f}"

    @staticmethod
    def _format_quantity(value: float) -> str:
        if value <= 0:
            return "—"
        if value >= 1000:
            return f"{value:,.0f}"
        if value >= 1:
            return f"{value:,.2f}"
        return f"{value:.3f}"

    @staticmethod
    def _format_age(seconds: float) -> str:
        """Compact relative-age formatter for table display."""
        if seconds < 0.05:
            return "<0.1s"
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            minutes = int(seconds // 60)
            remainder = int(seconds % 60)
            return f"{minutes}m" if remainder == 0 else f"{minutes}m{remainder}s"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h{minutes:02d}m"

    def _connection_status_text(self) -> Text:
        """Return formatted connection status text."""
        state = (self.connection_state or "unknown").lower()
        if "connected" in state and "reconnect" not in state:
            style = "bold green"
        elif "reconnect" in state or "subscrib" in state:
            style = "bold yellow"
        elif "error" in state or "closed" in state:
            style = "bold red"
        else:
            style = "bold cyan"
        return Text(state.upper(), style=style)

    def _watchlist_preview(self, max_items: int = 4) -> str:
        if not self.watchlist:
            return "—"
        preview = ", ".join(self.watchlist[:max_items])
        if len(self.watchlist) > max_items:
            preview += "…"
        return preview

    def _build_header_panel(self, registry_stats: Dict[str, Any]) -> Panel:
        now = datetime.now()
        runtime = (now - self.start_time).total_seconds()
        avg_tps = self._update_throughput_metrics(now)
        throttle_total = registry_stats.get("throttle_events_total", 0)
        last_throttle_ago = registry_stats.get("last_throttle_ago")
        avg_latency, last_latency = self._latency_metrics()
        if last_throttle_ago is not None:
            throttle_text = Text(
                f"{int(throttle_total)} (last {self._format_seconds(last_throttle_ago)} ago)",
                style="yellow" if throttle_total else "dim",
            )
        else:
            throttle_text = Text(str(int(throttle_total)), style="yellow" if throttle_total else "dim")

        stats = Table.grid(expand=True)
        stats.add_column()
        stats.add_column()
        stats.add_column()
        stats.add_column()
        stats.add_row(
            Text("Status", style="dim"),
            self._connection_status_text(),
            Text("Runtime", style="dim"),
            Text(self._format_seconds(runtime), style="bold"),
        )
        stats.add_row(
            Text("Trades", style="dim"),
            Text(f"{self.total_trades_processed:,}", style="bold"),
            Text("Avg TPS", style="dim"),
            Text(f"{avg_tps:.2f}", style="bold cyan"),
        )
        stats.add_row(
            Text("Liquidations", style="dim"),
            Text(str(self.total_liquidations), style="bold magenta"),
            Text("Last Error", style="dim"),
            Text(self.last_connection_error or "—", style="yellow" if self.last_connection_error else "dim"),
        )
        stats.add_row(
            Text("Throttle", style="dim"),
            throttle_text,
            Text("Candidates", style="dim"),
            Text(str(registry_stats.get("candidate_pool", 0)), style="bold"),
        )
        stats.add_row(
            Text("Avg Latency", style="dim"),
            Text(self._format_latency(avg_latency), style="bold"),
            Text("Last Latency", style="dim"),
            Text(self._format_latency(last_latency), style="bold"),
        )
        stats.add_row(
            Text("Markets", style="dim"),
            Text(str(len(self.subscribed_coins) or 0), style="bold cyan"),
            Text("Watchlist", style="dim"),
            Text(self._watchlist_preview(), style="cyan"),
        )

        return Panel(
            stats,
            title="🔴 HyperLiquid Live Monitor",
            border_style="cyan",
            box=box.ROUNDED,
        )

    def _build_registry_panel(self, stats: Dict[str, Any]) -> Panel:
        now = datetime.now()
        table = Table(
            box=box.MINIMAL_HEAVY_HEAD,
            header_style="bold dim",
            expand=True,
            pad_edge=False,
        )
        table.add_column("Vault")
        table.add_column("Cached", justify="right")
        table.add_column("Last Fill", justify="right")
        table.add_column("Retry In", justify="right")
        table.add_column("429", justify="right")
        table.add_column("Status", justify="left")

        vaults = stats.get("vaults", [])
        if vaults:
            now_ts = now.timestamp()
            ordered_vaults = sorted(
                vaults,
                key=lambda item: (
                    max(0.0, now_ts - float(item.get("last_fill_epoch") or 0.0))
                    if item.get("last_fill_epoch")
                    else float("inf")
                ),
            )
            for idx, vault in enumerate(ordered_vaults):
                if idx >= self.max_vault_rows:
                    break
                address = vault.get("address", "")
                short_addr = f"{address[:6]}…{address[-4:]}" if len(address) > 10 else address or "—"
                cached = vault.get("cached_fills", 0)
                last_epoch = vault.get("last_fill_epoch")
                last_error = vault.get("last_error")
                retry_in = float(vault.get("retry_in") or 0.0)
                throttle_count = int(vault.get("throttle_events") or 0)
                last_status = vault.get("last_status")
                backoff_seconds = float(vault.get("backoff_seconds") or 0.0)

                if last_epoch:
                    age = max(0, now_ts - last_epoch)
                    if age < 60:
                        age_style = "green"
                    elif age < 180:
                        age_style = "yellow"
                    else:
                        age_style = "red"
                    last_fill_text = Text(self._format_seconds(age) + " ago", style=age_style)
                else:
                    last_fill_text = Text("—", style="dim")

                failures = int(vault.get("consecutive_failures") or 0)
                if retry_in <= 1:
                    retry_text = Text("now", style="green")
                elif retry_in < 30:
                    retry_text = Text(self._format_seconds(retry_in), style="yellow")
                else:
                    retry_text = Text(self._format_seconds(retry_in), style="red")

                if throttle_count:
                    throttle_text = Text(str(throttle_count), style="yellow")
                else:
                    throttle_text = Text(str(throttle_count), style="dim")

                if last_error:
                    label = f"error ×{failures}" if failures else "error"
                    status_text = Text(label, style="bold red")
                elif failures:
                    status_text = Text(f"retry ×{failures}", style="yellow")
                elif throttle_count and retry_in > 1:
                    status_text = Text("cooldown", style="yellow")
                elif backoff_seconds > 30:
                    status_text = Text("slow", style="yellow")
                elif last_status in (200, None):
                    status_text = Text("live", style="bold green")
                else:
                    status_text = Text(str(last_status or "idle"), style="dim")

                table.add_row(
                    short_addr,
                    str(cached),
                    last_fill_text,
                    retry_text,
                    throttle_text,
                    status_text,
                )
        else:
            table.add_row(
                "—",
                "0",
                Text("—", style="dim"),
                Text("warming up", style="yellow"),
                Text("0", style="dim"),
                Text("initializing", style="yellow"),
            )

        meta = Table.grid(expand=True)
        meta.add_column(justify="left")
        meta.add_column(justify="right")
        meta.add_row(
            Text("Cached fills", style="dim"),
            Text(str(stats.get("cached_fills", 0)), style="bold"),
        )

        last_fill_epoch = stats.get("last_fill_epoch")
        if last_fill_epoch:
            age = max(0, now.timestamp() - last_fill_epoch)
            meta.add_row(Text("Last registry fill", style="dim"), Text(self._format_seconds(age) + " ago", style="cyan"))
        else:
            meta.add_row(Text("Last registry fill", style="dim"), Text("none yet", style="yellow"))
        meta.add_row(
            Text("Active vaults", style="dim"),
            Text(str(len(stats.get("active_vaults", []))), style="bold"),
        )
        meta.add_row(
            Text("Candidate pool", style="dim"),
            Text(str(stats.get("candidate_pool", 0)), style="bold"),
        )
        if stats.get("throttle_events_total"):
            last_throttle_ago = stats.get("last_throttle_ago")
            if last_throttle_ago is not None:
                throttle_age = self._format_seconds(last_throttle_ago)
                meta.add_row(
                    Text("Last throttle", style="dim"),
                    Text(f"{throttle_age} ago", style="yellow"),
                )
            meta.add_row(
                Text("Throttle events", style="dim"),
                Text(str(stats.get("throttle_events_total", 0)), style="yellow"),
            )

        max_backoff = max(
            (float(vault.get("backoff_seconds") or 0.0) for vault in vaults),
            default=0.0,
        )
        if max_backoff > 0:
            meta.add_row(
                Text("Max backoff", style="dim"),
                Text(self._format_seconds(max_backoff), style="dim"),
            )

        extras: List[Text] = []
        failing = stats.get("failing_vaults") or {}
        if failing:
            summary = ", ".join(
                f"{addr[:6]}…{addr[-4:]}×{count}"
                for addr, count in failing.items()
            )
            extras.append(Text(f"Retries in progress: {summary}", style="yellow"))

        warning: Optional[Text] = None
        if stats.get("all_vaults_stale"):
            warning = Text("⚠ All vault feeds stale — waiting for HyperLiquid activity", style="bold yellow")
        elif self.last_connection_error:
            warning = Text(f"⚠ {self.last_connection_error}", style="bold yellow")
        elif stats.get("throttle_events_total"):
            warning = Text("⚠ Rate limiting active — registry using exponential backoff", style="bold yellow")

        group_items = [meta, table]
        if extras:
            group_items.extend(extras)
        if warning:
            group_items.append(warning)

        body = Group(*group_items)

        return Panel(body, title="Registry / Vault", border_style="magenta", box=box.ROUNDED, padding=(0, 1))

    def _build_market_activity_panel(self) -> Panel:
        now = datetime.now()
        table = Table(
            box=box.MINIMAL,
            header_style="bold cyan",
            expand=True,
            pad_edge=False,
        )
        table.add_column("Coin", justify="left", style="bold", no_wrap=True)
        table.add_column("Price", justify="right", no_wrap=True, min_width=7)
        table.add_column("Size", justify="right", no_wrap=True, min_width=6)
        table.add_column("Side", justify="center", no_wrap=True, min_width=5)
        table.add_column("1h Liq Vol", justify="right", no_wrap=True, min_width=8)
        table.add_column("Last Trade", justify="right", no_wrap=True, min_width=6)
        table.add_column("•", justify="center", no_wrap=True, width=2)

        watchlist = self.watchlist or list(DEFAULT_WATCHLIST)
        watchlist = [coin.upper() for coin in watchlist]
        watch_coins = watchlist[: self.max_display_rows]
        dynamic_candidates = sorted(
            self.liquidations_by_token.items(),
            key=lambda item: item[1]['total_volume'],
            reverse=True,
        )
        dynamic_coins: List[str] = []
        for coin, _ in dynamic_candidates:
            if coin in watch_coins or coin in dynamic_coins:
                continue
            dynamic_coins.append(coin)
            if len(dynamic_coins) >= max(0, self.max_display_rows - len(watch_coins)):
                break

        display_coins = (watch_coins + dynamic_coins)[: self.max_display_rows]

        rows_added = False
        for coin in display_coins:
            rows_added = True
            price = self.latest_prices.get(coin)
            last_trade = self.last_activity.get(coin, 0)
            time_since = (now.timestamp() - last_trade) if last_trade else None
            last_trade_info = self.last_trade_details.get(coin, {})
            last_size = float(last_trade_info.get('size', 0.0) or 0.0)
            last_side = last_trade_info.get('side', '')
            recent_liqs = self.get_recent_liquidations(coin, 3600)
            hour_vol = recent_liqs.get('volume', 0.0)

            if time_since is None:
                age_text = Text("—", style="dim")
                status_text = Text("○", style="dim")
            else:
                age_str = self._format_age(time_since)
                age_style = "cyan" if time_since < 5 else "dim"
                age_text = Text(age_str, style=age_style)
                if time_since < 1:
                    status_text = Text("●", style="green")
                elif time_since < 5:
                    status_text = Text("●", style="yellow")
                elif time_since < 30:
                    status_text = Text("○", style="dim")
                else:
                    status_text = Text("○", style="red")

            if last_side == 'B':
                side_text = Text("BUY", style="bold green")
            elif last_side == 'A':
                side_text = Text("SELL", style="bold red")
            else:
                side_text = Text("—", style="dim")

            if recent_liqs['long_count'] > recent_liqs['short_count']:
                price_style = "bold red"
            elif recent_liqs['short_count'] > 0:
                price_style = "bold green"
            else:
                price_style = "white"

            price_text = Text(self._format_price_compact(price), style=price_style) if price else Text("—", style="dim")

            size_display = self._format_quantity(last_size) if last_size else "—"
            hour_vol_display = self.format_usd_short(hour_vol) if hour_vol else "—"

            table.add_row(
                coin,
                price_text,
                size_display,
                side_text,
                hour_vol_display,
                age_text,
                status_text,
            )

        if not rows_added:
            table.add_row("—", "—", "—", "—", "—", Text("—", style="dim"), Text("collecting…", style="dim"))

        return Panel(table, title="📈 Live Market Activity", border_style="cyan", box=box.ROUNDED, padding=(0, 0))

    def _build_summary_panel(self) -> Panel:
        total_volume = sum(d['total_volume'] for d in self.liquidations_by_token.values())

        overview = Table.grid(expand=True, padding=(0, 1))
        overview.add_column(justify="left")
        overview.add_column(justify="right")
        overview.add_row(Text("Total Liquidations", style="dim"), Text(str(self.total_liquidations), style="bold magenta"))
        overview.add_row(Text("Session Notional", style="dim"), Text(self.format_usd(total_volume), style="bold cyan"))

        if self.liquidations_by_token:
            top_coins = sorted(
                self.liquidations_by_token.items(),
                key=lambda x: x[1]['total_volume'],
                reverse=True
            )[:3]
            top_line = ", ".join(
                f"{coin}({data['long_count'] + data['short_count']})"
                for coin, data in top_coins
                if data['total_volume'] > 0
            )
            if top_line:
                overview.add_row(Text("Top Symbols", style="dim"), Text(top_line, style="bold"))

        stats_15m = self._liquidation_window_stats(900)
        stats_1h = self._liquidation_window_stats(3600)

        def format_bucket(stats: Dict[str, Any], side: str) -> Text:
            key_notional = f"{side.lower()}_notional"
            key_count = f"{side.lower()}_count"
            notional = stats.get(key_notional, 0.0)
            count = stats.get(key_count, 0)
            style = "bold red" if side == "LONG" else "bold green"
            value = self.format_usd_short(notional)
            return Text(f"{value} ({count})", style=style if notional else "dim")

        def top_symbols_line(stats: Dict[str, Any]) -> str:
            per_symbol = stats.get("per_symbol", {})
            if not per_symbol:
                return "—"
            leaders = sorted(
                per_symbol.items(),
                key=lambda item: item[1]["notional"],
                reverse=True,
            )[:2]
            return ", ".join(
                f"{symbol} {self.format_usd_short(data['notional'])}"
                for symbol, data in leaders
                if data["notional"] > 0
            ) or "—"

        timeframe_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.MINIMAL,
            expand=True,
            pad_edge=False,
        )
        timeframe_table.add_column("Window", justify="left")
        timeframe_table.add_column("Long", justify="right")
        timeframe_table.add_column("Short", justify="right")
        timeframe_table.add_column("Total", justify="right")
        timeframe_table.add_column("Leaders", justify="left")

        for label, stats in (("15m", stats_15m), ("1h", stats_1h)):
            total_text = Text(self.format_usd_short(stats.get("total_notional", 0.0)), style="bold")
            leaders_text = Text(top_symbols_line(stats), style="cyan")
            timeframe_table.add_row(
                label,
                format_bucket(stats, "LONG"),
                format_bucket(stats, "SHORT"),
                total_text,
                leaders_text,
            )

        body = Group(overview, timeframe_table)

        return Panel(body, title="Liquidation Summary", border_style="magenta", box=box.ROUNDED, padding=(0, 1))

    def _build_alerts_panel(self) -> Panel:
        table = Table(
            show_header=True,
            header_style="bold yellow",
            box=box.MINIMAL,
            expand=True,
            pad_edge=False,
        )
        table.add_column("Time", justify="left", no_wrap=True, width=8)
        table.add_column("Market", justify="left", min_width=8)
        table.add_column("Notional / Price", justify="right", min_width=12)

        alerts_list = list(self.recent_alerts)
        if alerts_list:
            for alert in alerts_list[:10]:
                ts = datetime.fromtimestamp(alert["timestamp"]).strftime("%H:%M:%S")
                side_style = "bold red" if alert["side"] == "LONG" else "bold green"
                arrow = "▲" if alert["side"] == "LONG" else "▼"
                market_text = Text.assemble(
                    Text(alert["coin"], style="bold"),
                    Text(" "),
                    Text(arrow, style=side_style),
                )
                notional = self.format_usd_short(alert["value"])
                price = self._format_price_compact(alert["price"])
                detail_text = Text.assemble(
                    Text(notional, style="bold"),
                    Text("\n"),
                    Text(price, style="dim"),
                )
                table.add_row(ts, market_text, detail_text)
        else:
            table.add_row("—", Text("—", style="dim"), Text("—", style="dim"))

        return Panel(table, title="Recent Alerts", border_style="yellow", box=box.ROUNDED, padding=(0, 0))

    def _build_layout_structure(self) -> Layout:
        placeholder = Panel("Loading…", border_style="dim", box=box.ROUNDED)
        layout = Layout()
        layout.split_column(
            Layout(placeholder, name="header", size=7),
            Layout(name="body", ratio=1),
        )
        layout["body"].split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=2),
        )
        layout["left"].split_column(
            Layout(placeholder, name="market", ratio=2),
            Layout(placeholder, name="registry", ratio=3),
        )
        layout["right"].split_column(
            Layout(placeholder, name="summary", ratio=2),
            Layout(placeholder, name="alerts", ratio=3),
        )
        return layout

    def _refresh_layout(self, layout: Layout) -> None:
        registry_stats = self.liquidation_registry.snapshot()
        throttle_total = int(registry_stats.get("throttle_events_total", 0) or 0)
        if throttle_total > self._last_throttle_total:
            delta = throttle_total - self._last_throttle_total
            self.console.log(
                f"[yellow]HyperLiquid REST throttled {delta} additional time(s) "
                f"(total {throttle_total}); applying extended backoff.[/]"
            )
        self._last_throttle_total = throttle_total
        layout["header"].update(self._build_header_panel(registry_stats))
        layout["market"].update(self._build_market_activity_panel())
        layout["registry"].update(self._build_registry_panel(registry_stats))
        layout["summary"].update(self._build_summary_panel())
        layout["alerts"].update(self._build_alerts_panel())

    async def render_loop(self) -> None:
        """Continuously render the dashboard using Rich Live."""
        self._render_running = True
        refresh_interval = max(self.refresh_interval, 0.5)
        refresh_hz = 1.0 / refresh_interval
        layout = self._build_layout_structure()
        try:
            with Live(
                layout,
                console=self.console,
                refresh_per_second=refresh_hz,
                screen=True,
            ) as live:
                while self._render_running:
                    self._refresh_layout(layout)
                    live.refresh()
                    await asyncio.sleep(refresh_interval)
        except asyncio.CancelledError:
            raise
        finally:
            self._render_running = False

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

        detection_ts = detection.get('timestamp')
        if detection_ts:
            latency = max(0.0, datetime.now().timestamp() - float(detection_ts))
            self.detection_latency_samples.append(latency)
            self.last_detection_latency = latency

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

    def record_liquidation_alert(self, liq: Dict) -> None:
        """Store liquidation alert info for dashboard display."""
        self.recent_alerts.appendleft({
            "coin": liq.get("coin", "?"),
            "side": liq.get("side", "UNK"),
            "price": liq.get("price", 0.0),
            "value": liq.get("value", 0.0),
            "timestamp": liq.get("timestamp", datetime.now().timestamp()),
        })
        # Keep alerts sorted by recency (deque already ensures ordering)
        # Emit a quick log line for terminal history
        side = liq.get("side", "?")
        direction = "LONG" if side == "LONG" else "SHORT"
        self.console.log(
            f"💥 {liq.get('coin')} {direction} liquidation "
            f"{self.format_usd(liq.get('value', 0.0))} @ ${liq.get('price', 0.0):,.2f}"
        )

    async def _fetch_universe_snapshot(self) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
        """Fetch HyperLiquid universe metadata with retry/backoff."""
        import aiohttp

        url = f"{self.api_base}/info"
        attempts = 5
        delay = 0.6
        for attempt in range(attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={"type": "metaAndAssetCtxs"}) as response:
                        if response.status == 200:
                            payload = await response.json()
                            if isinstance(payload, list) and len(payload) >= 2:
                                meta, contexts = payload[0], payload[1]
                                universe = meta.get("universe") if isinstance(meta, dict) else None
                                if isinstance(universe, list):
                                    names = [
                                        str(asset.get("name")).upper()
                                        for asset in universe
                                        if asset.get("name")
                                    ]
                                    return names, universe, contexts if isinstance(contexts, list) else []
                        elif response.status == 429:
                            await asyncio.sleep(delay * (attempt + 1))
                            continue
                        else:
                            text = await response.text()
                            self.console.print(
                                f"[yellow]HyperLiquid meta request failed ({response.status}): {text[:120]}[/]"
                            )
            except Exception as exc:  # noqa: BLE001
                self.console.print(f"[yellow]HyperLiquid meta fetch error: {exc}[/]")
            await asyncio.sleep(delay * (attempt + 1))
        return [], [], []

    @staticmethod
    def _extract_volume(context: Dict[str, Any], fallback: Dict[str, Any]) -> float:
        """Extract a 24h notional volume estimate from asset context."""
        candidates = (
            "dayNtlVlm",
            "day_ntl_vlm",
            "dayNotionalVolume",
            "volume24hUsd",
            "volume24hUSDC",
            "volume24h_quote",
            "volume24h",
            "volume_24h",
            "dayBaseVlm",
        )
        for key in candidates:
            value = context.get(key)
            if value is None and fallback:
                value = fallback.get(key)
            if value is None:
                continue
            try:
                volume = float(value)
                if volume > 0:
                    return volume
            except (TypeError, ValueError):
                continue
        return 0.0

    def _build_dynamic_watchlist(
        self,
        universe: List[Dict[str, Any]],
        contexts: List[Dict[str, Any]],
    ) -> List[str]:
        """Return majors plus top-10 non-majors by 24h notional volume."""
        if not universe:
            return list(DEFAULT_WATCHLIST)

        volumes: List[Tuple[str, float]] = []
        for idx, asset in enumerate(universe):
            name = str(asset.get("name") or "").upper()
            if not name:
                continue
            context = contexts[idx] if idx < len(contexts) else {}
            volume = self._extract_volume(context, asset)
            volumes.append((name, volume))

        volumes.sort(key=lambda item: item[1], reverse=True)

        majors_set = set(MAJOR_COINS)
        dynamic: List[str] = list(MAJOR_COINS)
        for name, _ in volumes:
            if name in majors_set or name in dynamic:
                continue
            dynamic.append(name)
            if len(dynamic) >= len(MAJOR_COINS) + 10:
                break

        return dynamic

    async def get_all_coins(self) -> List[str]:
        """Retrieve the tradable coin universe and apply filters."""

        names, universe, contexts = await self._fetch_universe_snapshot()

        if universe:
            dynamic = self._build_dynamic_watchlist(universe, contexts)
        else:
            dynamic = list(DEFAULT_WATCHLIST)

        self.dynamic_watchlist = list(dynamic)

        # Prioritise majors+top10, then append remaining markets for expansion.
        ordered: List[str] = []
        for coin in dynamic + names:
            if coin and coin not in ordered:
                ordered.append(coin)

        if not ordered:
            ordered = list(DEFAULT_WATCHLIST)

        if self._requested_coins:
            requested_set = [coin.upper() for coin in self._requested_coins]
            available = [coin for coin in ordered if coin in requested_set]
            missing = [coin for coin in requested_set if coin not in ordered]
            self.missing_requested = missing
            coins = available or requested_set
        else:
            self.missing_requested = []
            coins = ordered
            if self._excluded_coins:
                coins = [coin for coin in coins if coin not in self._excluded_coins]
            if self._max_coins:
                coins = coins[: self._max_coins]

        return coins or list(DEFAULT_WATCHLIST)

    async def monitor_with_activity(self):
        """Monitor HyperLiquid trades and render a Rich dashboard."""
        self.console.print("[cyan]Initializing HyperLiquid live monitor…[/]")

        coins = await self.get_all_coins()
        self.subscribed_coins = coins
        if self._custom_display_watchlist is not None:
            self.watchlist = (
                [coin for coin in self._custom_display_watchlist if coin in coins]
                or list(self._custom_display_watchlist)
            )
        elif self._requested_coins:
            requested_available = [
                coin for coin in self._requested_coins if coin in coins
            ]
            self.watchlist = requested_available or list(self._requested_coins)
        else:
            base_watch = [coin for coin in self.dynamic_watchlist if coin in coins]
            if not base_watch:
                base_watch = coins[: self.max_display_rows]
            self.watchlist = base_watch[: self.max_display_rows]

        self.console.print(
            f"[cyan]Tracking {len(coins)} perpetual markets "
            f"(subscription limit: {self._max_coins or 'all'})[/]"
        )
        if self._excluded_coins:
            self.console.print(
                f"[cyan]Excluded coins:[/] {', '.join(sorted(self._excluded_coins))}"
            )
        if self.missing_requested:
            self.console.print(
                f"[yellow]Skipped unavailable coins:[/] {', '.join(self.missing_requested)}"
            )
        if self.watchlist:
            preview = ", ".join(self.watchlist[:8])
            if len(self.watchlist) > 8:
                preview += "…"
            self.console.print(f"[cyan]Watchlist focus:[/] {preview}")

        await self.liquidation_registry.start()
        self._render_task = asyncio.create_task(self.render_loop())

        try:
            self.connection_state = "connecting"
            async with websockets.connect(
                self.ws_url,
                ping_interval=45,
                ping_timeout=25,
                close_timeout=10,
                max_queue=None,
            ) as ws:
                self.connection_state = "connected"
                self.console.log("Connected to HyperLiquid trades stream")

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

                self.connection_state = f"subscribed ({len(coins)})"
                self.console.log(f"Subscribed to {len(coins)} markets")

                self.connection_state = "live"
                async for message in ws:
                    data = json.loads(message)

                    if data.get('channel') != 'trades':
                        continue

                    trades = data.get('data', [])
                    for trade in trades:
                        liq = await self.process_trade(trade)

                        if liq:
                            self.total_liquidations += 1

                            token_data = self.liquidations_by_token[liq['coin']]
                            if liq['side'] == 'LONG':
                                token_data['long_count'] += 1
                                token_data['long_volume'] += liq['value']
                            else:
                                token_data['short_count'] += 1
                                token_data['short_volume'] += liq['value']

                            token_data['total_volume'] += liq['value']
                            token_data['last_price'] = liq['price']

                            self.liquidation_timestamps[liq['coin']].append({
                                'timestamp': liq['timestamp'],
                                'side': liq['side'],
                                'value': liq['value']
                            })

                            if len(self.liquidation_timestamps[liq['coin']]) > 1000:
                                self.liquidation_timestamps[liq['coin']] = self.liquidation_timestamps[liq['coin']][-1000:]

                            self.record_liquidation_alert(liq)

        except KeyboardInterrupt:
            self.console.print("[yellow]\nStopped by user[/]")
        except websockets.exceptions.ConnectionClosedError as e:
            self.connection_state = "closed"
            self.last_connection_error = f"Connection closed ({getattr(e, 'code', 'n/a')}): {e}"
            self.console.print(f"[red]WebSocket closed: {self.last_connection_error}[/]")
        except Exception as e:
            self.connection_state = "error"
            self.last_connection_error = str(e)
            self.console.print(f"[red]Monitor error: {e}[/]")
        finally:
            self.connection_state = "stopped"
            if self._render_task:
                self._render_running = False
                self._render_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._render_task
            await self.liquidation_registry.close()
            self.print_final_stats()

    def print_final_stats(self):
        """Print final aggregated statistics"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        avg_speed = (self.total_trades_processed / runtime) if runtime > 0 else 0.0

        headline = Table.grid(expand=True)
        headline.add_column(justify="left")
        headline.add_column(justify="right")
        headline.add_row(Text("Runtime", style="dim"), Text(self._format_seconds(runtime), style="bold"))
        headline.add_row(Text("Trades processed", style="dim"), Text(f"{self.total_trades_processed:,}", style="bold"))
        headline.add_row(Text("Liquidations detected", style="dim"), Text(str(self.total_liquidations), style="bold magenta"))
        headline.add_row(Text("Average throughput", style="dim"), Text(f"{avg_speed:.2f} trades/s", style="bold cyan"))

        rows = []
        if self.liquidations_by_token:
            breakdown = Table(
                title="By Token",
                box=box.SIMPLE_HEAVY,
                header_style="bold",
                expand=True,
            )
            breakdown.add_column("Token", justify="left")
            breakdown.add_column("Long Liq", justify="right")
            breakdown.add_column("Short Liq", justify="right")
            breakdown.add_column("Total Vol", justify="right")
            breakdown.add_column("Last Price", justify="right")

            sorted_tokens = sorted(
                self.liquidations_by_token.items(),
                key=lambda x: x[1]['total_volume'],
                reverse=True
            )

            for token, data in sorted_tokens:
                if data['long_count'] + data['short_count'] == 0:
                    continue
                breakdown.add_row(
                    token,
                    str(data['long_count']),
                    str(data['short_count']),
                    self.format_usd(data['total_volume']),
                    f"${data.get('last_price', 0):,.2f}",
                )
            rows.append(breakdown)

        body = Group(headline, *rows) if rows else headline
        self.console.print(
            Panel(
                body,
                title="📊 Final Liquidation Report",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [token.strip().upper() for token in value.split(",") if token.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HyperLiquid live liquidation monitor")
    parser.add_argument(
        "--coins",
        default=None,
        help="Comma-separated list of coins to subscribe (overrides auto universe)",
    )
    parser.add_argument(
        "--exclude",
        default=None,
        help="Comma-separated list of coins to skip when auto-subscribing",
    )
    parser.add_argument(
        "--max-coins",
        type=int,
        default=60,
        help="Maximum number of markets to subscribe to (default: 60)",
    )
    parser.add_argument(
        "--majors-only",
        action="store_true",
        help="Subscribe only to the default major watchlist",
    )
    parser.add_argument(
        "--display-watchlist",
        default=None,
        help="Comma-separated list of coins to prioritise in the dashboard watchlist",
    )
    parser.add_argument(
        "--refresh-interval",
        type=float,
        default=2.0,
        help="UI refresh interval in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--registry-poll",
        type=float,
        default=None,
        help="Registry poll interval in seconds (increase to ease API load)",
    )
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()
    coins = _split_csv(args.coins)
    if args.majors_only and not coins:
        coins = list(DEFAULT_WATCHLIST)
    exclude = _split_csv(args.exclude)
    display_watchlist = _split_csv(args.display_watchlist)
    monitor = LiveLiquidationMonitor(
        coins=coins or None,
        exclude_coins=exclude or None,
        max_coins=args.max_coins,
        display_watchlist=display_watchlist or None,
        registry_poll_interval=args.registry_poll,
    )
    monitor.refresh_interval = max(0.5, args.refresh_interval)
    await monitor.monitor_with_activity()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated.")
    except Exception as e:
        print(f"Error: {e}")
