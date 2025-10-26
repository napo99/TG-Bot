"""Compatibility entry point for the unified OI aggregator."""

from pathlib import Path
import sys

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.exchanges.unified_aggregator import (  # noqa: E402
    UnifiedOIAggregator,
    UnifiedOIResponse,
    test_unified_system,
)

__all__ = ["UnifiedOIAggregator", "UnifiedOIResponse", "test_unified_system"]

if __name__ == "__main__":  # pragma: no cover - legacy CLI support
    import asyncio

    asyncio.run(test_unified_system())
