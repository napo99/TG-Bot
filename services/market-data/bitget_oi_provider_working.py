"""Compatibility wrapper for the relocated Bitget provider."""

from pathlib import Path
import sys

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.exchanges.bitget import BitgetOIProvider  # noqa: E402

__all__ = ["BitgetOIProvider", "BitgetOIProviderWorking"]

BitgetOIProviderWorking = BitgetOIProvider
