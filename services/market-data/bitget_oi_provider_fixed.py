"""Access to the archived Bitget provider implementation."""

from importlib import util
from pathlib import Path

ARCHIVE_MODULE = Path(__file__).resolve().parents[2] / "archive" / "market-data" / "bitget_oi_provider_fixed.py"
_spec = util.spec_from_file_location("archive.bitget_oi_provider_fixed", ARCHIVE_MODULE)
if _spec and _spec.loader:
    _module = util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    BitgetOIProviderFixed = _module.BitgetOIProviderFixed  # type: ignore[attr-defined]
    __all__ = ["BitgetOIProviderFixed"]
else:  # pragma: no cover - defensive fallback
    raise ImportError(f"Unable to load archived Bitget provider from {ARCHIVE_MODULE}")
