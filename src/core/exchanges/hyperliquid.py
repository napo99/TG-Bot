"""Hyperliquid DEX exchange provider."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from .base import (
    BaseExchangeOIProvider,
    ExchangeDataError,
    ExchangeOIResult,
    MarketOIData,
    MarketType,
)


class HyperliquidOIProvider(BaseExchangeOIProvider):
    """Open Interest provider for the Hyperliquid decentralized perpetuals exchange."""

    CACHE_TTL_SECONDS = 5

    def __init__(self) -> None:
        super().__init__("hyperliquid")
        self.api_base = "https://api.hyperliquid.xyz"
        self.endpoints = {"info": f"{self.api_base}/info"}
        self._snapshot_cache: Optional[Tuple[datetime, Dict[str, Any], List[Dict[str, Any]]]] = None

    def get_supported_market_types(self) -> List[MarketType]:
        """Hyperliquid only settles in USDC."""

        return [MarketType.USDC]

    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """Return the universe symbol used by the Hyperliquid API."""

        return base_symbol.upper()

    async def get_oi_data(self, base_symbol: str) -> ExchangeOIResult:
        """Return Open Interest data for the requested base asset."""

        logger.info(f"🟣 Fetching Hyperliquid OI for {base_symbol}")
        try:
            meta, asset_contexts = await self._fetch_snapshot()
            symbol, asset_data = self._extract_asset_data(meta, asset_contexts, base_symbol)
            market_data = self._process_perpetual_data(asset_data, base_symbol, symbol)

            validation_passed, validation_errors = await self.validate_market_data(market_data)

            oi_usd_billions = market_data.oi_usd / 1e9
            logger.info(
                "✅ Hyperliquid {symbol}: {oi_tokens:,.0f} {symbol} (${oi_usd_billions:.1f}B)",
                symbol=symbol,
                oi_tokens=market_data.oi_tokens,
                oi_usd_billions=oi_usd_billions,
            )

            return ExchangeOIResult(
                exchange="hyperliquid",
                base_symbol=base_symbol,
                markets=[market_data],
                total_oi_tokens=market_data.oi_tokens,
                total_oi_usd=market_data.oi_usd,
                total_volume_24h=market_data.volume_24h,
                total_volume_24h_usd=market_data.volume_24h_usd,
                usdt_markets=[],
                usdc_markets=[market_data],
                usd_markets=[],
                validation_passed=validation_passed,
                validation_errors=validation_errors,
            )
        except ExchangeDataError:
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Unexpected Hyperliquid failure")
            raise ExchangeDataError(
                self.exchange_name,
                "unexpected_error",
                {"error": str(exc)},
            ) from exc

    async def get_funding_rates(self, base_symbol: str) -> Dict[str, float]:
        """Return the most recent funding rate for the requested asset."""

        try:
            meta, asset_contexts = await self._fetch_snapshot()
            symbol, asset_data = self._extract_asset_data(meta, asset_contexts, base_symbol)
            return {f"{symbol}-PERP": float(asset_data.get("funding", 0.0))}
        except ExchangeDataError as exc:
            logger.warning(f"⚠️ Hyperliquid funding unavailable: {exc}")
            return {}

    async def validate_api_connection(self) -> bool:
        """Perform a lightweight API health check."""

        try:
            meta, _ = await self._fetch_snapshot(force_refresh=True)
            return bool(meta.get("universe"))
        except ExchangeDataError as exc:
            logger.error(f"❌ Hyperliquid health check failed: {exc}")
            return False

    async def _fetch_snapshot(
        self, *, force_refresh: bool = False
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetch (or reuse) the `metaAndAssetCtxs` snapshot."""

        if not force_refresh and self._snapshot_cache is not None:
            timestamp, meta, asset_contexts = self._snapshot_cache
            if (datetime.now() - timestamp).total_seconds() < self.CACHE_TTL_SECONDS:
                return meta, asset_contexts

        session = await self.get_session()
        async with session.post(self.endpoints["info"], json={"type": "metaAndAssetCtxs"}) as response:
            if response.status != 200:
                raise ExchangeDataError(
                    self.exchange_name,
                    "http_error",
                    {"status": response.status},
                )

            try:
                payload = await response.json()
            except Exception as exc:  # pragma: no cover - protects against malformed JSON
                raise ExchangeDataError(
                    self.exchange_name,
                    "invalid_json",
                    {"error": str(exc)},
                ) from exc

        if not isinstance(payload, list) or len(payload) < 2:
            raise ExchangeDataError(
                self.exchange_name,
                "unexpected_payload",
                {"type": type(payload).__name__},
            )

        meta, asset_contexts = payload[0], payload[1]
        if not isinstance(meta, dict) or not isinstance(asset_contexts, list):
            raise ExchangeDataError(
                self.exchange_name,
                "malformed_payload",
                {"meta_type": type(meta).__name__, "ctx_type": type(asset_contexts).__name__},
            )

        self._snapshot_cache = (datetime.now(), meta, asset_contexts)
        return meta, asset_contexts

    def _extract_asset_data(
        self,
        meta: Dict[str, Any],
        asset_contexts: List[Dict[str, Any]],
        base_symbol: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """Locate the asset context for the requested symbol."""

        target_symbol = base_symbol.upper()
        universe = meta.get("universe", [])
        for index, asset in enumerate(universe):
            if asset.get("name") == target_symbol:
                if index >= len(asset_contexts):
                    raise ExchangeDataError(
                        self.exchange_name,
                        "asset_context_missing",
                        {"symbol": target_symbol, "index": index, "contexts": len(asset_contexts)},
                    )
                return target_symbol, asset_contexts[index]

        raise ExchangeDataError(
            self.exchange_name,
            "asset_not_listed",
            {"symbol": target_symbol},
        )

    def _process_perpetual_data(
        self, asset_data: Dict[str, Any], base_symbol: str, symbol_name: str
    ) -> MarketOIData:
        """Normalise the Hyperliquid asset context into `MarketOIData`."""

        try:
            oi_tokens = float(asset_data.get("openInterest", 0))
            volume_24h = float(asset_data.get("dayBaseVlm", 0))
            volume_24h_usd = float(asset_data.get("dayNtlVlm", 0))
            mark_price = float(asset_data.get("markPx", 0))
            oracle_price = float(asset_data.get("oraclePx", 0))
            funding_rate = float(asset_data.get("funding", 0))
        except (TypeError, ValueError) as exc:
            raise ExchangeDataError(
                self.exchange_name,
                "invalid_numeric_value",
                {"error": str(exc)},
            ) from exc

        price = mark_price if mark_price > 0 else oracle_price
        if oi_tokens <= 0 or price <= 0:
            raise ExchangeDataError(
                self.exchange_name,
                "invalid_market_snapshot",
                {"symbol": symbol_name, "oi_tokens": oi_tokens, "price": price},
            )

        price_validated = True
        if volume_24h > 0 and volume_24h_usd > 0:
            implied_price = volume_24h_usd / volume_24h
            price_diff_pct = abs(price - implied_price) / price * 100
            if price_diff_pct > 10:
                price_validated = False
                logger.warning(
                    "Hyperliquid price validation mismatch: mark=%s implied=%s diff=%.1f%%",
                    price,
                    implied_price,
                    price_diff_pct,
                )

        return MarketOIData(
            exchange="hyperliquid",
            symbol=f"{symbol_name}-PERP",
            base_symbol=base_symbol,
            market_type=MarketType.USDC,
            oi_tokens=oi_tokens,
            oi_usd=oi_tokens * price,
            price=price,
            funding_rate=funding_rate,
            volume_24h=volume_24h,
            volume_24h_usd=volume_24h_usd,
            timestamp=datetime.now(),
            api_source="metaAndAssetCtxs",
            calculation_method=f"dex: {oi_tokens:,.0f} {symbol_name} × ${price:,.2f}",
            price_validated=price_validated,
            calculation_validated=True,
            api_validated=True,
        )


__all__ = ["HyperliquidOIProvider"]
