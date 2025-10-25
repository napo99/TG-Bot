"""
Unified Liquidation Aggregator Module - Production Grade
Central module for all liquidation tracking components
Author: Opus 4.1
Date: October 25, 2025

This module provides a unified interface to all liquidation tracking components:
- CEX liquidation engines (Binance, Bybit, OKX)
- DEX liquidation providers (Hyperliquid)
- Cascade risk calculation
- Market regime detection
- WebSocket management
- Data aggregation
"""

from typing import TYPE_CHECKING, List, Dict, Any, Optional
import logging

__version__ = "1.0.0"
__author__ = "Opus 4.1"

# Setup logging
logger = logging.getLogger(__name__)

# Import components from current directory
try:
    from .unified_monitor import UnifiedMonitor
    from .side_detector import SideDetector
except ImportError as e:
    logger.warning(f"Failed to import unified components: {e}")
    UnifiedMonitor = None
    SideDetector = None

# Import core components from parent directory
try:
    from ..unified_hyperengine import UnifiedHyperEngine
    from ..professional_liquidation_monitor import ProfessionalLiquidationMonitor
except ImportError as e:
    logger.warning(f"Failed to import core engines: {e}")
    UnifiedHyperEngine = None
    ProfessionalLiquidationMonitor = None

# Import data aggregation
try:
    from ..data_aggregator import (
        LiquidationDataAggregator,
        CumulativeStats,
        get_cumulative_stats
    )
except ImportError as e:
    logger.warning(f"Failed to import data aggregation: {e}")
    LiquidationDataAggregator = None
    CumulativeStats = None
    get_cumulative_stats = None

# Import WebSocket management
try:
    from ..enhanced_websocket_manager import (
        EnhancedWebSocketManager,
        VelocityTracker,
        BTCPriceFeed,
        VelocityMetrics,
        BTCPriceUpdate
    )
except ImportError as e:
    logger.warning(f"Failed to import WebSocket components: {e}")
    EnhancedWebSocketManager = None
    VelocityTracker = None
    BTCPriceFeed = None
    VelocityMetrics = None
    BTCPriceUpdate = None

# Import CEX engines
try:
    from ..cex.cex_engine import (
        LiquidationEvent,
        Exchange,
        Side,
        InMemoryLiquidationBuffer,
        RedisLiquidationCache,
        AsyncDatabaseWriter,
        PriceLevelCluster,
        CascadeEvent
    )
except ImportError as e:
    logger.warning(f"Failed to import CEX engine: {e}")
    LiquidationEvent = None
    Exchange = None
    Side = None
    InMemoryLiquidationBuffer = None
    RedisLiquidationCache = None
    AsyncDatabaseWriter = None
    PriceLevelCluster = None
    CascadeEvent = None

# Import CEX exchanges
try:
    from ..cex.cex_exchanges import (
        BinanceLiquidationStream,
        BybitLiquidationStream,
        OKXLiquidationStream
    )
except ImportError as e:
    logger.warning(f"Failed to import CEX exchanges: {e}")
    BinanceLiquidationStream = None
    BybitLiquidationStream = None
    OKXLiquidationStream = None

# Import DEX providers
try:
    from ..dex.hyperliquid_liquidation_provider import HyperliquidLiquidationProvider
except ImportError as e:
    logger.warning(f"Failed to import DEX providers: {e}")
    HyperliquidLiquidationProvider = None

# Import cascade analysis
try:
    from ..cascade_risk_calculator import CascadeRiskCalculator
    from ..cascade_signal_generator import CascadeSignalGenerator
    from ..market_regime_detector import MarketRegimeDetector
    from ..advanced_velocity_engine import AdvancedVelocityEngine
except ImportError as e:
    logger.warning(f"Failed to import cascade analysis: {e}")
    CascadeRiskCalculator = None
    CascadeSignalGenerator = None
    MarketRegimeDetector = None
    AdvancedVelocityEngine = None

# Define public API
__all__ = [
    # Version info
    '__version__',
    '__author__',

    # Local components
    'UnifiedMonitor',
    'SideDetector',

    # Core engines
    'UnifiedHyperEngine',
    'ProfessionalLiquidationMonitor',

    # Data aggregation
    'LiquidationDataAggregator',
    'CumulativeStats',
    'get_cumulative_stats',

    # WebSocket management
    'EnhancedWebSocketManager',
    'VelocityTracker',
    'BTCPriceFeed',
    'VelocityMetrics',
    'BTCPriceUpdate',

    # CEX components
    'LiquidationEvent',
    'Exchange',
    'Side',
    'InMemoryLiquidationBuffer',
    'RedisLiquidationCache',
    'AsyncDatabaseWriter',
    'PriceLevelCluster',
    'CascadeEvent',

    # CEX exchanges
    'BinanceLiquidationStream',
    'BybitLiquidationStream',
    'OKXLiquidationStream',

    # DEX providers
    'HyperliquidLiquidationProvider',

    # Analysis components
    'CascadeRiskCalculator',
    'CascadeSignalGenerator',
    'MarketRegimeDetector',
    'AdvancedVelocityEngine',

    # Helper functions
    'get_available_components',
    'create_default_engine',
    'get_system_health'
]

def get_available_components() -> Dict[str, bool]:
    """
    Get status of available components

    Returns:
        Dictionary mapping component names to availability status
    """
    return {
        'UnifiedMonitor': UnifiedMonitor is not None,
        'SideDetector': SideDetector is not None,
        'UnifiedHyperEngine': UnifiedHyperEngine is not None,
        'ProfessionalLiquidationMonitor': ProfessionalLiquidationMonitor is not None,
        'LiquidationDataAggregator': LiquidationDataAggregator is not None,
        'EnhancedWebSocketManager': EnhancedWebSocketManager is not None,
        'CEX Engine': LiquidationEvent is not None,
        'Binance Stream': BinanceLiquidationStream is not None,
        'Bybit Stream': BybitLiquidationStream is not None,
        'OKX Stream': OKXLiquidationStream is not None,
        'Hyperliquid Provider': HyperliquidLiquidationProvider is not None,
        'Cascade Risk Calculator': CascadeRiskCalculator is not None,
        'Signal Generator': CascadeSignalGenerator is not None,
        'Market Regime Detector': MarketRegimeDetector is not None,
        'Velocity Engine': AdvancedVelocityEngine is not None
    }

async def create_default_engine(config_path: Optional[str] = None) -> Optional['UnifiedHyperEngine']:
    """
    Create and initialize a default UnifiedHyperEngine instance

    Args:
        config_path: Optional path to configuration file

    Returns:
        Initialized UnifiedHyperEngine or None if not available
    """
    if UnifiedHyperEngine is None:
        raise ImportError("UnifiedHyperEngine not available. Check dependencies.")

    engine = UnifiedHyperEngine(config_path=config_path)
    await engine.initialize_components()
    return engine

def get_system_health() -> Dict[str, Any]:
    """
    Get overall system health status

    Returns:
        Dictionary containing health metrics for all components
    """
    from datetime import datetime

    health = {
        'status': 'operational',
        'components': get_available_components(),
        'timestamp': datetime.utcnow().isoformat(),
        'version': __version__
    }

    # Check if all critical components are available
    critical = [
        'UnifiedHyperEngine',
        'EnhancedWebSocketManager',
        'LiquidationDataAggregator'
    ]

    for component in critical:
        if not health['components'].get(component, False):
            health['status'] = 'degraded'
            break

    return health

# Initialize logging
def setup_logging(level: str = 'INFO') -> None:
    """
    Setup logging for the unified module

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    import logging

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Unified Liquidation Aggregator v{__version__} initialized")

    # Log component availability
    available = get_available_components()
    available_count = sum(available.values())
    total_count = len(available)

    logger.info(f"Available components: {available_count}/{total_count}")

    # Log missing components
    missing = [name for name, status in available.items() if not status]
    if missing:
        logger.warning(f"Missing components: {', '.join(missing)}")

# Auto-setup logging on import (can be overridden)
if __name__ != '__main__':
    setup_logging()

# Provide convenience imports for common use cases
if TYPE_CHECKING:
    # Type hints for IDE support
    from ..unified_hyperengine import UnifiedHyperEngine as _UnifiedHyperEngine
    from ..professional_liquidation_monitor import ProfessionalLiquidationMonitor as _Monitor
    from ..data_aggregator import LiquidationDataAggregator as _Aggregator
    from ..enhanced_websocket_manager import EnhancedWebSocketManager as _WSManager