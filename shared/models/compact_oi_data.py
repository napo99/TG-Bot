"""
Compact OI Data Model
Memory-optimized structure for OI monitoring
Target: 24-hour rolling window with minimal memory usage
"""

import struct
from typing import NamedTuple, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class OISnapshot:
    """Single OI snapshot for an exchange-symbol pair"""
    timestamp: int  # Unix timestamp
    exchange: str
    symbol: str
    oi_usd: float
    oi_change_24h: float
    
    def __post_init__(self):
        # Normalize symbol
        self.symbol = self.symbol.upper().replace("USDT", "").replace("USDC", "")


class CompactOIData:
    """
    Memory-optimized OI data storage
    Stores 24 hours of OI data with 5-minute granularity
    Max: 288 data points per symbol per exchange = ~7KB per symbol
    """
    
    def __init__(self, symbol: str, max_hours: int = 24):
        self.symbol = symbol.upper()
        self.max_hours = max_hours
        self.max_data_points = (max_hours * 60) // 5  # 5-minute intervals
        
        # Exchange data: exchange -> [(timestamp, oi_usd), ...]
        self.exchange_data: Dict[str, List[tuple[int, float]]] = defaultdict(list)
        
        # Baseline OI values for percentage calculations
        self.baseline_oi: Dict[str, float] = {}
    
    def add_snapshot(self, snapshot: OISnapshot) -> None:
        """Add new OI snapshot"""
        exchange = snapshot.exchange.lower()
        timestamp = snapshot.timestamp
        oi_usd = snapshot.oi_usd
        
        # Add to exchange data
        self.exchange_data[exchange].append((timestamp, oi_usd))
        
        # Sort by timestamp and limit size
        self.exchange_data[exchange].sort(key=lambda x: x[0])
        if len(self.exchange_data[exchange]) > self.max_data_points:
            self.exchange_data[exchange] = self.exchange_data[exchange][-self.max_data_points:]
        
        # Update baseline if needed
        if exchange not in self.baseline_oi or len(self.exchange_data[exchange]) < 12:  # First hour
            self.baseline_oi[exchange] = oi_usd
    
    def get_recent_data(self, exchange: str, minutes: int = 15) -> List[tuple[int, float]]:
        """Get OI data from last N minutes"""
        current_time = int(datetime.now().timestamp())
        cutoff_time = current_time - (minutes * 60)
        
        exchange = exchange.lower()
        if exchange not in self.exchange_data:
            return []
        
        return [(ts, oi) for ts, oi in self.exchange_data[exchange] if ts >= cutoff_time]
    
    def calculate_change_percentage(self, exchange: str, minutes: int = 15) -> Optional[float]:
        """Calculate OI change percentage over time window"""
        recent_data = self.get_recent_data(exchange, minutes)
        if len(recent_data) < 2:
            return None
        
        # Use oldest and newest in window
        old_oi = recent_data[0][1]
        new_oi = recent_data[-1][1]
        
        if old_oi == 0:
            return None
        
        return ((new_oi - old_oi) / old_oi) * 100
    
    def get_current_oi(self, exchange: str) -> Optional[float]:
        """Get most recent OI value"""
        exchange = exchange.lower()
        if exchange not in self.exchange_data or not self.exchange_data[exchange]:
            return None
        
        return self.exchange_data[exchange][-1][1]
    
    def get_cross_exchange_confirmation(self, minutes: int = 15, min_exchanges: int = 2) -> Dict[str, float]:
        """Get cross-exchange OI change confirmation"""
        changes = {}
        
        for exchange in self.exchange_data:
            change_pct = self.calculate_change_percentage(exchange, minutes)
            if change_pct is not None:
                changes[exchange] = change_pct
        
        # Only return if we have enough exchanges
        if len(changes) >= min_exchanges:
            return changes
        
        return {}
    
    def detect_explosion(self, threshold_pct: float, min_oi_usd: float, minutes: int = 15) -> Optional[Dict]:
        """Detect OI explosion across exchanges"""
        cross_exchange_changes = self.get_cross_exchange_confirmation(minutes)
        
        if not cross_exchange_changes:
            return None
        
        # Check if majority of exchanges show explosion
        exploding_exchanges = []
        total_oi = 0
        
        for exchange, change_pct in cross_exchange_changes.items():
            current_oi = self.get_current_oi(exchange)
            if current_oi and current_oi > min_oi_usd and abs(change_pct) >= threshold_pct:
                exploding_exchanges.append({
                    'exchange': exchange,
                    'change_pct': change_pct,
                    'current_oi': current_oi
                })
                total_oi += current_oi
        
        # Need at least 2 exchanges confirming
        if len(exploding_exchanges) >= 2:
            return {
                'symbol': self.symbol,
                'exploding_exchanges': exploding_exchanges,
                'total_oi': total_oi,
                'confirmation_count': len(exploding_exchanges),
                'avg_change_pct': sum(e['change_pct'] for e in exploding_exchanges) / len(exploding_exchanges)
            }
        
        return None
    
    def cleanup_old_data(self) -> None:
        """Remove data older than max_hours"""
        current_time = int(datetime.now().timestamp())
        cutoff_time = current_time - (self.max_hours * 3600)
        
        for exchange in self.exchange_data:
            self.exchange_data[exchange] = [
                (ts, oi) for ts, oi in self.exchange_data[exchange] if ts >= cutoff_time
            ]
    
    def memory_usage_bytes(self) -> int:
        """Estimate memory usage in bytes"""
        total_points = sum(len(data) for data in self.exchange_data.values())
        return total_points * 16  # 8 bytes timestamp + 8 bytes float


class OIDataManager:
    """
    Manages OI data for multiple symbols
    Memory-optimized with automatic cleanup
    """
    
    def __init__(self, target_memory_mb: int = 40):
        self.target_memory_mb = target_memory_mb
        self.target_memory_bytes = target_memory_mb * 1024 * 1024
        
        # Symbol -> CompactOIData
        self.symbol_data: Dict[str, CompactOIData] = {}
        
        # Supported symbols (focus on major pairs)
        self.monitored_symbols = ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "ATOM"]
    
    def add_oi_snapshot(self, snapshot: OISnapshot) -> None:
        """Add OI snapshot for a symbol"""
        symbol = snapshot.symbol
        
        if symbol not in self.symbol_data:
            if symbol in self.monitored_symbols:
                self.symbol_data[symbol] = CompactOIData(symbol)
            else:
                return  # Skip unmonitored symbols
        
        self.symbol_data[symbol].add_snapshot(snapshot)
    
    def detect_explosions(self) -> List[Dict]:
        """Detect OI explosions across all monitored symbols"""
        explosions = []
        
        for symbol, data in self.symbol_data.items():
            # Get symbol-specific thresholds
            from shared.config.alert_thresholds import get_oi_threshold
            
            threshold_pct = get_oi_threshold(symbol, "change_pct")
            min_oi_usd = get_oi_threshold(symbol, "min_value")
            
            explosion = data.detect_explosion(threshold_pct, min_oi_usd)
            if explosion:
                explosions.append(explosion)
        
        return explosions
    
    def cleanup_memory(self) -> None:
        """Cleanup old data to stay within memory limits"""
        # Clean old data from all symbols
        for data in self.symbol_data.values():
            data.cleanup_old_data()
        
        # Check total memory usage
        total_memory = sum(data.memory_usage_bytes() for data in self.symbol_data.values())
        
        if total_memory > self.target_memory_bytes:
            # Remove least active symbols
            symbol_activity = {
                symbol: sum(len(data.exchange_data[ex]) for ex in data.exchange_data)
                for symbol, data in self.symbol_data.items()
            }
            
            # Keep most active symbols
            sorted_symbols = sorted(symbol_activity.items(), key=lambda x: x[1], reverse=True)
            symbols_to_keep = [s[0] for s in sorted_symbols[:6]]  # Keep top 6
            
            # Remove less active symbols
            for symbol in list(self.symbol_data.keys()):
                if symbol not in symbols_to_keep:
                    del self.symbol_data[symbol]
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        symbol_usage = {
            symbol: data.memory_usage_bytes()
            for symbol, data in self.symbol_data.items()
        }
        
        total_usage = sum(symbol_usage.values())
        
        return {
            "total_bytes": total_usage,
            "total_mb": total_usage / (1024 * 1024),
            "symbol_breakdown": symbol_usage,
            "symbols_count": len(self.symbol_data)
        }
    
    def get_symbol_status(self, symbol: str) -> Optional[Dict]:
        """Get status for a specific symbol"""
        if symbol not in self.symbol_data:
            return None
        
        data = self.symbol_data[symbol]
        
        return {
            "symbol": symbol,
            "exchanges": list(data.exchange_data.keys()),
            "data_points": {ex: len(data.exchange_data[ex]) for ex in data.exchange_data},
            "current_oi": {ex: data.get_current_oi(ex) for ex in data.exchange_data},
            "memory_bytes": data.memory_usage_bytes()
        }