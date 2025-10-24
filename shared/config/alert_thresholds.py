"""
Alert Thresholds Configuration
Configurable parameters for liquidation and OI alerts
"""

import os
from typing import Dict, Any

# Liquidation Alert Thresholds
LIQUIDATION_THRESHOLDS = {
    "BTC": {
        "single_large": float(os.getenv("LIQUIDATION_THRESHOLD_BTC", "100000")),     # $100k+ single liquidation
        "cascade_count": 5,           # 5+ liquidations in 30s
        "cascade_value": 500000       # $500k+ total cascade
    },
    "ETH": {
        "single_large": float(os.getenv("LIQUIDATION_THRESHOLD_ETH", "50000")),      # $50k+ single liquidation
        "cascade_count": 5,           # 5+ liquidations in 30s
        "cascade_value": 250000       # $250k+ total cascade
    },
    "SOL": {
        "single_large": float(os.getenv("LIQUIDATION_THRESHOLD_SOL", "25000")),      # $25k+ single liquidation
        "cascade_count": 4,           # 4+ liquidations in 30s
        "cascade_value": 100000       # $100k+ total cascade
    }
}

# OI Explosion Alert Thresholds
OI_EXPLOSION_THRESHOLDS = {
    "BTC": {
        "change_pct": float(os.getenv("OI_THRESHOLD_BTC", "15.0")),                  # 15%+ OI change
        "time_window": 15,            # 15-minute windows
        "min_value": 50_000_000       # $50M+ minimum OI
    },
    "ETH": {
        "change_pct": float(os.getenv("OI_THRESHOLD_ETH", "18.0")),                  # 18%+ OI change  
        "time_window": 15,            # 15-minute windows
        "min_value": 25_000_000       # $25M+ minimum OI
    },
    "SOL": {
        "change_pct": float(os.getenv("OI_THRESHOLD_SOL", "25.0")),                  # 25%+ OI change
        "time_window": 15,            # 15-minute windows
        "min_value": 10_000_000       # $10M+ minimum OI
    }
}

# System Performance Limits
SYSTEM_LIMITS = {
    "max_memory_mb": 512,             # Total system memory limit
    "liquidation_monitor_mb": 50,     # Agent 1 memory limit
    "oi_detector_mb": 40,             # Agent 2 memory limit
    "alert_dispatcher_mb": 30,        # Agent 3 memory limit
    "infrastructure_mb": 10,          # Agent 4 memory limit
    "buffer_overhead_mb": 12          # Buffer for overhead
}

# Alert Rate Limiting
ALERT_RATE_LIMITS = {
    "max_alerts_per_hour": 10,        # Maximum alerts per user per hour
    "deduplication_window_minutes": 5, # Prevent duplicate alerts
    "telegram_rate_limit_per_second": 30, # Telegram API limit
    "alert_retry_attempts": 3,        # Number of retry attempts
    "retry_backoff_seconds": [1, 2, 4] # Exponential backoff
}

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    "binance_liquidation_url": "wss://fstream.binance.com/ws/!forceOrder@arr",
    "hyperliquid_ws_url": "wss://api.hyperliquid.xyz/ws",
    "reconnect_delays": [1, 2, 4, 8, 16],  # Exponential backoff seconds
    "max_reconnect_delay": 16,
    "ping_interval": 20,              # WebSocket ping interval
    "ping_timeout": 10,               # WebSocket ping timeout
    "close_timeout": 10               # WebSocket close timeout
}

# Hyperliquid Configuration
HYPERLIQUID_CONFIG = {
    "enabled": os.getenv("ENABLE_HYPERLIQUID_LIQUIDATION_ALERTS", "true").lower() == "true",
    "api_base": "https://api.hyperliquid.xyz",
    "ws_url": "wss://api.hyperliquid.xyz/ws",
    "monitored_symbols": os.getenv("HYPERLIQUID_SYMBOLS", "BTC,ETH,SOL").split(","),
    "api_timeout": 10,
    "polling_interval": 5,  # seconds (used if WebSocket unavailable)
    "thresholds": {
        "BTC": {
            "single_large": float(os.getenv("HYPERLIQUID_THRESHOLD_BTC", "100000")),
            "cascade_count": 5,
            "cascade_value": 500000
        },
        "ETH": {
            "single_large": float(os.getenv("HYPERLIQUID_THRESHOLD_ETH", "50000")),
            "cascade_count": 5,
            "cascade_value": 250000
        },
        "SOL": {
            "single_large": float(os.getenv("HYPERLIQUID_THRESHOLD_SOL", "25000")),
            "cascade_count": 4,
            "cascade_value": 100000
        },
        "default": {
            "single_large": 10000,
            "cascade_count": 3,
            "cascade_value": 50000
        }
    }
}

# Monitoring Configuration
MONITORING_CONFIG = {
    "health_check_interval": 30,      # Health check every 30 seconds
    "max_failure_count": 3,           # Max failures before restart
    "data_retention_hours": 24,       # Keep data for 24 hours
    "log_level": os.getenv("MONITORING_LOG_LEVEL", "INFO"),
    "structured_logging": True        # Use structured JSON logging
}

# Exchange API Configuration
EXCHANGE_CONFIG = {
    "oi_monitoring_interval": 300,    # Check OI every 5 minutes
    "api_timeout_seconds": 10,        # API request timeout
    "max_concurrent_requests": 5,     # Max parallel requests
    "rate_limit_buffer": 0.8,         # Use 80% of rate limit
    "supported_exchanges": ["binance", "bybit", "okx"],
    "cross_exchange_confirmation_threshold": 2  # 2/3 exchanges must confirm
}

def get_liquidation_threshold(symbol: str, threshold_type: str) -> float:
    """Get liquidation threshold for a symbol"""
    base_symbol = symbol.replace("USDT", "").replace("USDC", "").upper()
    
    if base_symbol in LIQUIDATION_THRESHOLDS:
        return LIQUIDATION_THRESHOLDS[base_symbol].get(threshold_type, 0)
    
    # Default thresholds for unknown symbols
    defaults = {
        "single_large": 10000,        # $10k default
        "cascade_value": 50000        # $50k default
    }
    return defaults.get(threshold_type, 0)

def get_oi_threshold(symbol: str, threshold_type: str) -> float:
    """Get OI threshold for a symbol"""
    base_symbol = symbol.replace("USDT", "").replace("USDC", "").upper()
    
    if base_symbol in OI_EXPLOSION_THRESHOLDS:
        return OI_EXPLOSION_THRESHOLDS[base_symbol].get(threshold_type, 0)
    
    # Default thresholds for unknown symbols
    defaults = {
        "change_pct": 30.0,           # 30% default
        "min_value": 5_000_000        # $5M default
    }
    return defaults.get(threshold_type, 0)

def validate_memory_usage(component: str, usage_mb: float) -> bool:
    """Validate memory usage against limits"""
    limit_key = f"{component}_mb"
    if limit_key in SYSTEM_LIMITS:
        return usage_mb <= SYSTEM_LIMITS[limit_key]
    return True

def get_environment_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "enable_liquidation_alerts": os.getenv("ENABLE_LIQUIDATION_ALERTS", "true").lower() == "true",
        "enable_oi_alerts": os.getenv("ENABLE_OI_ALERTS", "true").lower() == "true",
        "alert_rate_limit_seconds": int(os.getenv("ALERT_RATE_LIMIT_SECONDS", "60")),
        "market_data_url": os.getenv("MARKET_DATA_URL", "http://market-data:8001"),
        "liquidation_exchanges": os.getenv("LIQUIDATION_EXCHANGES", "binance,hyperliquid").split(","),
        "enable_hyperliquid": HYPERLIQUID_CONFIG["enabled"]
    }