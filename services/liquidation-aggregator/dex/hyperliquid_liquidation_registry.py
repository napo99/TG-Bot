"""
Utility module for detecting HyperLiquid liquidation agents dynamically.

HyperLiquid does not expose a dedicated liquidation stream. Instead,
liquidations executed by the HyperLiquid Protections (HLP) vault appear in the
regular trade channel and can originate from many rotating sub-accounts. The
most reliable public signal that a trade was a liquidation is whether the trade
ID (`tid`) shows up in the vault's recent fills.

This registry polls the `userFills` endpoint for the official HLP vault and
keeps a bounded cache of recent liquidation `tid`s along with useful metadata.
Call `classify_trade(trade)` with trades from the websocket feed to check if
they correspond to a known liquidation.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger

# Official HyperLiquid liquidation vault address
HLP_VAULT_ADDRESS = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"


@dataclass
class HyperLiquidFill:
    """Normalized representation of a HyperLiquid vault fill."""

    tid: int
    coin: str
    direction: str
    price: float
    size: float
    timestamp_ms: int

    @property
    def value(self) -> float:
        return self.price * self.size

    @property
    def liquidation_side(self) -> Optional[str]:
        """
        Infer liquidation side from the direction label.

        Returns:
            "LONG" if a long position was liquidated
            "SHORT" if a short position was liquidated
            None if the direction cannot be resolved
        """
        direction = (self.direction or "").lower()

        if "close long" in direction or "liquidate long" in direction:
            return "LONG"
        if "close short" in direction or "liquidate short" in direction:
            return "SHORT"

        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tid": self.tid,
            "coin": self.coin,
            "direction": self.direction,
            "price": self.price,
            "size": self.size,
            "timestamp_ms": self.timestamp_ms,
            "value": self.value,
            "liquidation_side": self.liquidation_side,
        }


class HyperLiquidLiquidationRegistry:
    """
    Maintains a cache of recent HyperLiquid liquidation fills.

    Usage pattern:
        registry = HyperLiquidLiquidationRegistry()
        await registry.start()
        ...
        match = await registry.classify_trade(trade)
        if match:
            # trade is a liquidation
    """

    INFO_ENDPOINT = "https://api.hyperliquid.xyz/info"

    def __init__(
        self,
        *,
        vault_address: str = HLP_VAULT_ADDRESS,
        poll_interval: float = 5.0,
        max_records: int = 500,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self._vault_address = vault_address.lower()
        self._poll_interval = poll_interval
        self._max_records = max_records
        self._session: Optional[aiohttp.ClientSession] = session
        self._session_owner = session is None

        self._records: Dict[int, HyperLiquidFill] = {}
        self._lock = asyncio.Lock()
        self._last_refresh = 0.0
        self._last_success_wallclock = 0.0
        self._last_fill_epoch = 0.0

    async def start(self) -> None:
        """Initial fetch so we have some baseline data."""
        await self._ensure_recent(force=True)

    async def close(self) -> None:
        """Close the internal HTTP session if we created it."""
        if self._session_owner and self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            self._session = aiohttp.ClientSession(timeout=timeout)
            self._session_owner = True
        return self._session

    async def _ensure_recent(self, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_refresh) < self._poll_interval:
            return

        async with self._lock:
            now = time.monotonic()
            if not force and (now - self._last_refresh) < self._poll_interval:
                return

            try:
                records = await self._fetch_latest_fills()
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to refresh HyperLiquid fills: {exc}")
                self._last_refresh = now
                return

            if records:
                self._records = records
                self._last_success_wallclock = time.time()
                self._last_fill_epoch = max(
                    (fill.timestamp_ms for fill in records.values()),
                    default=0,
                ) / 1000.0
                logger.debug(
                    "Updated HyperLiquid liquidation cache (%d records, latest tid=%s)",
                    len(records),
                    max(records.keys()),
                )
            else:
                logger.warning(
                    "HyperLiquid userFills returned no data; retaining previous cache"
                )

            self._last_refresh = now

    async def _fetch_latest_fills(self) -> Dict[int, HyperLiquidFill]:
        session = await self._get_session()
        payload = {"type": "userFills", "user": self._vault_address}

        async with session.post(self.INFO_ENDPOINT, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise RuntimeError(
                    f"userFills request failed (status={response.status}, body={text[:200]})"
                )

            data = await response.json()

        if not isinstance(data, list):
            logger.warning("Unexpected userFills payload: %s", data)
            return {}

        fills: Dict[int, HyperLiquidFill] = {}

        for entry in data:
            try:
                tid = int(entry.get("tid"))
                coin = entry.get("coin") or ""
                direction = entry.get("dir") or entry.get("side") or ""
                price = float(entry.get("px", 0))
                size = float(entry.get("sz", 0))
                timestamp_ms = int(entry.get("time", 0))
            except (TypeError, ValueError):
                continue

            fill = HyperLiquidFill(
                tid=tid,
                coin=coin,
                direction=direction,
                price=price,
                size=size,
                timestamp_ms=timestamp_ms,
            )

            if fill.liquidation_side is None:
                # Skip fills that are not clearly liquidation events
                continue

            fills[tid] = fill

            if len(fills) >= self._max_records:
                break

        return fills

    async def classify_trade(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check whether a websocket trade corresponds to a known liquidation.

        Args:
            trade: Raw trade dictionary from HyperLiquid websocket feed.

        Returns:
            A normalized liquidation payload if detected, otherwise None.
        """
        await self._ensure_recent()

        try:
            tid = int(trade.get("tid"))
        except (TypeError, ValueError):
            return None

        match = self._records.get(tid)
        if not match:
            return None

        price = float(trade.get("px", match.price))
        size = float(trade.get("sz", match.size))
        timestamp_ms = int(trade.get("time", match.timestamp_ms))

        return {
            "coin": trade.get("coin", match.coin),
            "side": match.liquidation_side,
            "price": price,
            "size": size,
            "value": price * size,
            "timestamp": timestamp_ms / 1000.0,
            "tid": tid,
            "users": trade.get("users", []),
            "source": "userFills",
            "raw_fill": match.to_dict(),
        }

    def snapshot(self) -> Dict[str, Any]:
        """
        Return lightweight diagnostics about the cached fills.
        """
        return {
            "cached_fills": len(self._records),
            "last_success": self._last_success_wallclock,
            "last_fill_epoch": self._last_fill_epoch,
        }

    def recent_fills(self, limit: int = 10) -> list[HyperLiquidFill]:
        """
        Return the most recent cached fills, newest first.
        """
        fills = sorted(
            self._records.values(),
            key=lambda fill: fill.timestamp_ms,
            reverse=True,
        )
        return fills[:limit]
