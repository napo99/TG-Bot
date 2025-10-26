"""Compatibility facade for the refactored OI engine primitives."""

from pathlib import Path
import sys

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.exchanges.base import (  # noqa: E402
    AggregatedOIResult,
    BaseExchangeOIProvider,
    ExchangeDataError,
    ExchangeFailure,
    ExchangeOIResult,
    MarketOIData,
    MarketType,
    OIEngineV2,
)

__all__ = [
    "AggregatedOIResult",
    "BaseExchangeOIProvider",
    "ExchangeDataError",
    "ExchangeFailure",
    "ExchangeOIResult",
    "MarketOIData",
    "MarketType",
    "OIEngineV2",
]
