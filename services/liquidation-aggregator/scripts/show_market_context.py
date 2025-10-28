#!/usr/bin/env python3
"""
Institutional-grade open interest and liquidity dashboard.

Transforms the MarketDataAggregator snapshot into a trader-actionable terminal
surface with severity flags, risk scoring, and a structured checklist.

Usage:
    python -m scripts.show_market_context --symbol BTCUSDT --once
    python -m scripts.show_market_context --symbol ETHUSDT --refresh 15
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import time
from typing import Tuple

from rich.console import Console, Group
from rich.columns import Columns
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from market_data_aggregator import MarketDataAggregator, MarketContext

console = Console()


def _format_usd(value: float) -> str:
    """Compact USD formatting suitable for dense dashboards."""
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"


def _format_percent(value: float, precision: int = 2) -> str:
    """Render a signed percentage with configurable precision."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{precision}f}%"


def _risk_descriptor(score: float) -> Tuple[str, str, str]:
    """Classify risk score into label, style, and icon."""
    if score >= 80:
        return "Extreme", "bold red", "🔴"
    if score >= 60:
        return "High", "bold yellow", "🟠"
    if score >= 40:
        return "Elevated", "yellow", "🟡"
    return "Normal", "bold green", "🟢"


def _severity_row(table: Table, label: str, condition: bool, detail: str) -> None:
    """Append a checklist row with standardised iconography."""
    icon = "🚨" if condition else "✅"
    style = "bold red" if condition else "dim"
    table.add_row(icon, Text(label, style=style), detail)


def _build_dashboard(symbol: str, context: MarketContext, risk_score: float) -> Group:
    """Compose the Rich dashboard object for the current snapshot."""
    risk_label, risk_style, risk_icon = _risk_descriptor(risk_score)
    updated_at = datetime.fromtimestamp(context.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    header_text = Text()
    header_text.append(f"{risk_icon} {symbol} Open Interest Command Center\n", style="bold white")
    header_text.append(f"Risk {risk_score:.0f}/100 • {risk_label}", style=risk_style)
    header_text.append(f"   Updated {updated_at}", style="dim")
    header_panel = Panel(header_text, border_style=risk_style.replace("bold ", ""), padding=(0, 1))

    # Derivatives pulse (open interest + funding)
    derivatives = Table.grid(padding=(0, 1))
    derivatives.add_column("Metric", justify="left", min_width=16)
    derivatives.add_column("Value", justify="right", min_width=14)
    derivatives.add_row("Open Interest", _format_usd(context.open_interest_usd))
    derivatives.add_row("Δ 1m", _format_percent(context.oi_change_1m))
    derivatives.add_row("Δ 5m", _format_percent(context.oi_change_5m))
    derivatives.add_row("Δ 1h", _format_percent(context.oi_change_1h))
    derivatives.add_row("Funding", f"{context.funding_rate:.4%} ({context.funding_trend})")
    derivatives.add_row("Max Funding 24h", f"{context.max_funding_24h:.4%}")
    derivatives_panel = Panel(derivatives, title="Derivatives Pulse", border_style="cyan", padding=(0, 1))

    # Liquidity and flow
    liquidity = Table.grid(padding=(0, 1))
    liquidity.add_column("Metric", min_width=16)
    liquidity.add_column("Value", justify="right", min_width=14)
    liquidity.add_row("Bid Depth (2%)", _format_usd(context.bid_depth_2pct))
    liquidity.add_row("Ask Depth (2%)", _format_usd(context.ask_depth_2pct))
    liquidity.add_row("Imbalance", _format_percent(context.book_imbalance * 100))
    liquidity.add_row("Depth Δ1m", _format_percent(context.depth_change_1m))
    liquidity.add_row("Large Trades 1m", f"{context.large_trades_1m}")
    liquidity.add_row("Whale Flow", _format_usd(context.whale_accumulation))
    liquidity_panel = Panel(liquidity, title="Liquidity & Flow", border_style="magenta", padding=(0, 1))

    # Spread, premium, volatility
    spread = Table.grid(padding=(0, 1))
    spread.add_column("Metric", min_width=16)
    spread.add_column("Value", justify="right", min_width=14)
    if context.spot_price:
        spread.add_row("Spot Price", f"${context.spot_price:,.2f}")
    if context.perp_price:
        spread.add_row("Perp Price", f"${context.perp_price:,.2f}")
    spread.add_row("Premium", f"{context.premium:.3%}")
    spread.add_row("Realized Vol 5m", f"{context.realized_vol_5m:.2%}")
    spread.add_row("Arb Opportunity", "Yes" if context.arbitrage_opportunity else "No")
    spread_panel = Panel(spread, title="Spread & Volatility", border_style="yellow", padding=(0, 1))

    checklist = Table.grid(padding=(0, 1))
    checklist.add_column(" ", width=2)
    checklist.add_column("Signal", justify="left", min_width=20)
    checklist.add_column("Detail", justify="left", min_width=24)

    _severity_row(
        checklist,
        "OI Flush",
        context.oi_change_5m <= -5 or context.oi_change_1m <= -3,
        f"Δ5m { _format_percent(context.oi_change_5m) }",
    )
    _severity_row(
        checklist,
        "Funding Extreme",
        abs(context.funding_rate) >= 0.05,
        f"{context.funding_rate:.4%}",
    )
    _severity_row(
        checklist,
        "Book Stress",
        context.depth_change_1m <= -10,
        f"Depth Δ1m { _format_percent(context.depth_change_1m) }",
    )
    _severity_row(
        checklist,
        "Premium Dislocation",
        abs(context.premium) >= 0.005,
        f"{context.premium:.3%}",
    )
    _severity_row(
        checklist,
        "Whale Dominance",
        context.large_trades_1m >= 10 or abs(context.whale_accumulation) > 5_000_000,
        f"Trades {context.large_trades_1m}  Flow { _format_usd(context.whale_accumulation) }",
    )
    _severity_row(
        checklist,
        "Cascade Probability",
        risk_score >= 60,
        f"Risk {risk_score:.0f}/100",
    )
    checklist_panel = Panel(checklist, title="Playbook Checklist", border_style="red", padding=(0, 1))

    return Group(
        header_panel,
        Columns([derivatives_panel, liquidity_panel, spread_panel], equal=True, expand=True, padding=(0, 1)),
        checklist_panel,
    )


async def _snapshot(symbol: str, aggregator: MarketDataAggregator) -> Tuple[MarketContext, float]:
    """Fetch market context and cascade risk score."""
    try:
        context = await aggregator.get_complete_context(symbol=symbol)
    except Exception as exc:
        console.log(f"[yellow]Warning:[/yellow] failed to fetch market context for {symbol}: {exc}")
        context = MarketContext(timestamp=time.time())
    risk_score = aggregator.get_cascade_risk_score(context) if aggregator else 0.0
    return context, risk_score


async def _run_once(symbol: str, aggregator: MarketDataAggregator) -> None:
    context, risk = await _snapshot(symbol, aggregator)
    dashboard = _build_dashboard(symbol, context, risk)
    console.print(dashboard)


async def _run_stream(symbol: str, refresh: float, aggregator: MarketDataAggregator) -> None:
    refresh = max(refresh, 1.0)
    context, risk = await _snapshot(symbol, aggregator)
    dashboard = _build_dashboard(symbol, context, risk)

    with Live(dashboard, console=console, refresh_per_second=min(10, 1 / (refresh / 2)), screen=False) as live:
        while True:
            context, risk = await _snapshot(symbol, aggregator)
            live.update(_build_dashboard(symbol, context, risk))
            await asyncio.sleep(refresh)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Institutional-grade market context dashboard (open interest, funding, liquidity)."
    )
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol to query (default BTCUSDT)")
    parser.add_argument("--refresh", type=float, default=0.0, help="If >0, stream updates every N seconds")
    parser.add_argument("--once", action="store_true", help="Fetch a single snapshot and exit")
    args = parser.parse_args()

    aggregator = MarketDataAggregator()

    if args.once or args.refresh <= 0:
        await _run_once(args.symbol.upper(), aggregator)
    else:
        await _run_stream(args.symbol.upper(), args.refresh, aggregator)


if __name__ == "__main__":
    asyncio.run(main())
