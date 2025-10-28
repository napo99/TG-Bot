"""HyperLiquid liquidation registry with dynamic vault discovery.

HyperLiquid does not expose a dedicated liquidation stream. Instead,
liquidations executed by the HyperLiquid Protections (HLP) vault appear in the
regular trade channel and can originate from rotating sub-accounts. The most
reliable signal that a trade was a liquidation is whether its trade id (`tid`)
shows up in the `userFills` feed for the currently active liquidation vaults.

HyperLiquid recently started rotating between multiple vault addresses. The
old single-vault approach therefore stopped receiving new fills which caused
the downstream monitors to display zero activity. The registry below discovers
the active vault set automatically, polls every vault on a configurable
interval, and merges the results into a single cache that downstream
components can query.

Call :class:`HyperLiquidLiquidationRegistry` and its :meth:`classify_trade`
method to check websocket trades against the cached liquidation fills.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import aiohttp
from loguru import logger

# Historic HyperLiquid liquidation vault address used as a safe default.
HLP_VAULT_ADDRESS = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"


@dataclass
class VaultCache:
    """Lightweight container for per-vault cache metadata."""

    address: str
    records: Dict[int, "HyperLiquidFill"] = field(default_factory=dict)
    last_success: float = 0.0
    last_error: Optional[str] = None
    last_fill_epoch: float = 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "cached_fills": len(self.records),
            "last_success": self.last_success,
            "last_error": self.last_error,
            "last_fill_epoch": self.last_fill_epoch,
        }


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

    STALE_WARNING_SECONDS = 5 * 60
    DISCOVERY_INTERVAL = 60.0
    CANDIDATE_COOLDOWN = 60.0

    def __init__(
        self,
        *,
        default_vault: str = HLP_VAULT_ADDRESS,
        poll_interval: float = 5.0,
        max_records: int = 500,
        session: Optional[aiohttp.ClientSession] = None,
        discovery_interval: Optional[float] = None,
    ) -> None:
        self._default_vault = default_vault.lower()
        self._poll_interval = poll_interval
        self._max_records = max_records
        self._session: Optional[aiohttp.ClientSession] = session
        self._session_owner = session is None

        self._records: Dict[int, HyperLiquidFill] = {}
        self._vault_state: Dict[str, VaultCache] = {}
        self._candidate_attempts: Dict[str, float] = {}
        self._active_vaults: List[str] = []
        self._lock = asyncio.Lock()
        self._refresh_task: Optional[asyncio.Task[None]] = None
        self._last_refresh = 0.0
        self._last_success_wallclock = 0.0
        self._last_fill_epoch = 0.0
        self._last_discovery = 0.0
        self._all_vaults_stale = False
        self._discovery_interval = (
            discovery_interval if discovery_interval is not None else self.DISCOVERY_INTERVAL
        )

    async def start(self) -> None:
        """Initial fetch so we have some baseline data."""
        await self.refresh(force=True)

    async def close(self) -> None:
        """Close the internal HTTP session if we created it."""
        if self._session_owner and self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def refresh(self, *, force: bool = False) -> None:
        """Public hook to refresh the internal cache."""

        await self._ensure_recent(force=force)

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
            if self._refresh_task and not self._refresh_task.done():
                task = self._refresh_task
            else:
                self._refresh_task = asyncio.create_task(self._refresh(force=force))
                task = self._refresh_task

        await task

    async def _refresh(self, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_refresh) < self._poll_interval:
            return

        try:
            vaults = await self._discover_active_vaults()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to discover HyperLiquid vaults: {exc}")
            vaults = self._active_vaults or [self._default_vault]

        if not vaults:
            vaults = [self._default_vault]

        results = await asyncio.gather(
            *(self._fetch_vault_fills(vault) for vault in vaults),
            return_exceptions=True,
        )

        combined: Dict[int, HyperLiquidFill] = {}
        wallclock_now = time.time()
        any_success = False

        for vault, result in zip(vaults, results):
            cache = self._vault_state.setdefault(vault, VaultCache(address=vault))
            if isinstance(result, Exception):
                cache.last_error = str(result)
                logger.error(
                    "Failed to refresh HyperLiquid userFills for %s: %s", vault, result
                )
                continue

            if result:
                cache.records = result
                cache.last_success = wallclock_now
                cache.last_error = None
                cache.last_fill_epoch = max(
                    (fill.timestamp_ms for fill in result.values()),
                    default=0,
                ) / 1000.0
                combined.update(result)
                any_success = True
            else:
                logger.warning(
                    "HyperLiquid userFills for %s returned no liquidation records", vault
                )

        # Drop caches for vaults no longer active
        inactive = set(self._vault_state) - set(vaults)
        for vault in inactive:
            logger.info("Removing stale HyperLiquid vault %s from registry", vault)
            self._vault_state.pop(vault, None)

        if any_success:
            self._records = combined
            self._last_success_wallclock = wallclock_now
            self._last_fill_epoch = max(
                (cache.last_fill_epoch for cache in self._vault_state.values()),
                default=0.0,
            )
            logger.debug(
                "Updated HyperLiquid liquidation cache from %d vault(s) (%d fills)",
                len(self._vault_state),
                len(self._records),
            )

        self._active_vaults = list(vaults)
        self._last_refresh = now
        self._refresh_task = None

        self._all_vaults_stale = self._compute_stale_flag()
        if self._all_vaults_stale:
            logger.warning(
                "All HyperLiquid vault caches stale for >%ds (last fill %.0fs ago)",
                self.STALE_WARNING_SECONDS,
                wallclock_now - self._last_fill_epoch,
            )

    async def _discover_active_vaults(self) -> List[str]:
        now = time.monotonic()
        if self._active_vaults and (now - self._last_discovery) < self._discovery_interval:
            return self._active_vaults

        session = await self._get_session()

        candidates: List[str] = []
        payloads = [{"type": "vaults"}, {"type": "meta"}]

        for payload in payloads:
            try:
                async with session.post(self.INFO_ENDPOINT, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.debug(
                            "HyperLiquid %s discovery request failed: %s %s",
                            payload.get("type"),
                            response.status,
                            text[:200],
                        )
                        continue
                    data = await response.json()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Error fetching HyperLiquid %s payload: %s", payload, exc)
                continue

            discovered = self._extract_vault_addresses(data)
            for address in discovered:
                if address not in candidates:
                    candidates.append(address)

            if candidates:
                break

        if not candidates:
            # Fall back to previously known vaults or the baked-in default.
            if self._active_vaults:
                candidates = list(self._active_vaults)
            else:
                candidates = [self._default_vault]

        self._last_discovery = now
        return [address.lower() for address in candidates]

    @staticmethod
    def _extract_vault_addresses(payload: Any) -> List[str]:
        """Parse vault addresses from the HyperLiquid info payload."""

        addresses: List[str] = []

        if isinstance(payload, dict):
            if "addresses" in payload and isinstance(payload["addresses"], Sequence):
                for entry in payload["addresses"]:
                    addr = HyperLiquidLiquidationRegistry._normalize_address(entry)
                    if addr:
                        addresses.append(addr)

            if "vaults" in payload:
                vault_section = payload["vaults"]
                if isinstance(vault_section, dict):
                    for value in vault_section.values():
                        if isinstance(value, (dict, list, tuple)):
                            addresses.extend(
                                HyperLiquidLiquidationRegistry._extract_vault_addresses(
                                    value
                                )
                            )
                        else:
                            addr = HyperLiquidLiquidationRegistry._normalize_address(value)
                            if addr:
                                addresses.append(addr)
                elif isinstance(vault_section, Sequence):
                    for entry in vault_section:
                        addr = HyperLiquidLiquidationRegistry._normalize_address(entry)
                        if addr:
                            addresses.append(addr)

            if "meta" in payload:
                addresses.extend(
                    HyperLiquidLiquidationRegistry._extract_vault_addresses(
                        payload["meta"]
                    )
                )

            for key in ("liquidationVault", "liquidationVaults", "vaultAddresses"):
                if key in payload:
                    addresses.extend(
                        HyperLiquidLiquidationRegistry._extract_vault_addresses(
                            payload[key]
                        )
                    )

        elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
            for entry in payload:
                addr = HyperLiquidLiquidationRegistry._normalize_address(entry)
                if addr:
                    addresses.append(addr)
                elif isinstance(entry, (dict, list, tuple)):
                    addresses.extend(
                        HyperLiquidLiquidationRegistry._extract_vault_addresses(entry)
                    )

        # Deduplicate while preserving order.
        deduped: List[str] = []
        for address in addresses:
            if address and address not in deduped:
                deduped.append(address)
        return deduped

    async def _maybe_probe_candidates(self, users: Sequence[Any]) -> None:
        """Attempt to treat trade participants as candidate liquidation vaults."""

        if not users:
            return

        now_monotonic = time.monotonic()
        candidates: List[str] = []
        for user in users:
            addr = self._normalize_address(user)
            if not addr or addr in self._vault_state:
                continue
            last_attempt = self._candidate_attempts.get(addr, 0.0)
            if (now_monotonic - last_attempt) < self.CANDIDATE_COOLDOWN:
                continue
            self._candidate_attempts[addr] = now_monotonic
            candidates.append(addr)

        if not candidates:
            return

        results = await asyncio.gather(
            *(self._fetch_vault_fills(address) for address in candidates),
            return_exceptions=True,
        )

        wallclock_now = time.time()
        any_new_records = False

        for address, result in zip(candidates, results):
            cache = self._vault_state.setdefault(address, VaultCache(address=address))
            if isinstance(result, Exception):
                cache.last_error = str(result)
                continue

            if result:
                cache.records = result
                cache.last_success = wallclock_now
                cache.last_error = None
                cache.last_fill_epoch = max(
                    (fill.timestamp_ms for fill in result.values()),
                    default=0,
                ) / 1000.0
                self._records.update(result)
                any_new_records = True
                if address not in self._active_vaults:
                    self._active_vaults.append(address)

        if any_new_records:
            self._last_success_wallclock = wallclock_now
            self._last_fill_epoch = max(
                (cache.last_fill_epoch for cache in self._vault_state.values()),
                default=0.0,
            )
            self._all_vaults_stale = self._compute_stale_flag()

    @staticmethod
    def _normalize_address(entry: Any) -> Optional[str]:
        if isinstance(entry, str) and entry.startswith("0x"):
            return entry.lower()
        if isinstance(entry, dict):
            for key in ("address", "addr", "vault", "user", "account"):
                value = entry.get(key)
                if isinstance(value, str) and value.startswith("0x"):
                    return value.lower()
        return None

    async def _fetch_vault_fills(self, vault_address: str) -> Dict[int, HyperLiquidFill]:
        session = await self._get_session()
        payload = {"type": "userFills", "user": vault_address}

        async with session.post(self.INFO_ENDPOINT, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise RuntimeError(
                    "userFills request failed for %s (status=%s, body=%s)"
                    % (vault_address, response.status, text[:200])
                )

            data = await response.json()

        if not isinstance(data, list):
            logger.warning("Unexpected userFills payload for %s: %s", vault_address, data)
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
            await self._maybe_probe_candidates(trade.get("users", []))
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
            "active_vaults": list(self._active_vaults),
            "vaults": [cache.snapshot() for cache in self._vault_state.values()],
            "all_vaults_stale": self._all_vaults_stale,
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

    def active_vaults(self) -> List[str]:
        """Return the currently tracked vault addresses."""

        return list(self._active_vaults)

    def _compute_stale_flag(self) -> bool:
        if not self._vault_state:
            return False

        now = time.time()
        last_fill_times = [cache.last_fill_epoch for cache in self._vault_state.values()]
        if not any(last_fill_times):
            return False

        return all(
            (last_fill == 0.0) or (now - last_fill) >= self.STALE_WARNING_SECONDS
            for last_fill in last_fill_times
        )
