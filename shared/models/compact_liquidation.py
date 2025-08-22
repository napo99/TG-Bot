"""
Compact Liquidation Data Model
Memory-optimized structure for liquidation events
Target: 18 bytes per record
"""

import struct
from typing import NamedTuple, Optional
from datetime import datetime
from enum import IntEnum


class LiquidationSide(IntEnum):
    """Liquidation side enumeration"""
    LONG = 1
    SHORT = 2


class CompactLiquidation(NamedTuple):
    """
    Memory-optimized liquidation record
    Total size: 18 bytes
    """
    timestamp: int  # Unix timestamp (4 bytes)
    symbol_hash: int  # Hash of symbol (4 bytes)
    side: int  # 1=long, 2=short (1 byte)
    price: int  # Price * 100 (4 bytes)
    quantity: int  # Quantity * 1000000 (4 bytes)
    value_usd: int  # USD value (1 byte for scaling factor, stored as value/1000)
    
    @classmethod
    def from_binance_data(cls, data: dict) -> 'CompactLiquidation':
        """
        Create compact liquidation from Binance WebSocket data
        
        Expected Binance format:
        {
            "o": {
                "s": "BTCUSDT",
                "S": "SELL",  # SELL = long liquidation, BUY = short liquidation
                "o": "MARKET",
                "q": "0.162",
                "p": "43811.36",
                "ap": "43811.36",
                "X": "FILLED",
                "l": "0.162", 
                "z": "0.162",
                "T": 1640995200000
            }
        }
        """
        order = data.get('o', {})
        
        # Extract values
        symbol = order.get('s', '')
        side_str = order.get('S', '')
        price = float(order.get('ap', 0))  # Average price
        quantity = float(order.get('z', 0))  # Filled quantity
        timestamp = int(order.get('T', 0)) // 1000  # Convert to seconds
        
        # Calculate USD value
        value_usd = price * quantity
        
        # Convert side (Binance uses opposite logic)
        side = LiquidationSide.LONG if side_str == 'SELL' else LiquidationSide.SHORT
        
        # Create compact representation
        return cls(
            timestamp=timestamp,
            symbol_hash=hash(symbol) & 0xFFFFFFFF,  # 4 bytes
            side=side.value,
            price=int(price * 100),  # Store with 2 decimal precision
            quantity=int(quantity * 1000000),  # Store with 6 decimal precision
            value_usd=int(value_usd / 1000)  # Store in thousands
        )
    
    @property
    def actual_price(self) -> float:
        """Get actual price with decimal precision"""
        return self.price / 100.0
    
    @property
    def actual_quantity(self) -> float:
        """Get actual quantity with decimal precision"""
        return self.quantity / 1000000.0
    
    @property
    def actual_value_usd(self) -> float:
        """Get actual USD value"""
        return self.actual_price * self.actual_quantity
    
    @property
    def side_str(self) -> str:
        """Get human-readable side"""
        return "LONG" if self.side == LiquidationSide.LONG else "SHORT"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'side': self.side_str,
            'price': self.actual_price,
            'quantity': self.actual_quantity,
            'value_usd': self.actual_value_usd
        }
    
    def __sizeof__(self) -> int:
        """Return memory size in bytes"""
        return 18  # 4+4+1+4+4+1 bytes


class LiquidationBuffer:
    """
    Ring buffer for liquidations with memory constraints
    Max 1000 liquidations = ~18KB memory usage
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: list[CompactLiquidation] = []
        self.head = 0
        self.count = 0
    
    def add(self, liquidation: CompactLiquidation) -> None:
        """Add liquidation to buffer"""
        if self.count < self.max_size:
            self.buffer.append(liquidation)
            self.count += 1
        else:
            # Overwrite oldest entry
            self.buffer[self.head] = liquidation
            self.head = (self.head + 1) % self.max_size
    
    def get_recent(self, seconds: int = 30) -> list[CompactLiquidation]:
        """Get liquidations from last N seconds"""
        current_time = int(datetime.now().timestamp())
        cutoff_time = current_time - seconds
        
        recent = []
        for liq in self.buffer:
            if liq.timestamp >= cutoff_time:
                recent.append(liq)
        
        return recent
    
    def get_cascade_data(self, seconds: int = 30) -> tuple[list[CompactLiquidation], float]:
        """Get cascade liquidations and total value"""
        recent = self.get_recent(seconds)
        total_value = sum(liq.actual_value_usd for liq in recent)
        return recent, total_value
    
    def clear_old(self, seconds: int = 300) -> None:
        """Clear liquidations older than N seconds"""
        current_time = int(datetime.now().timestamp())
        cutoff_time = current_time - seconds
        
        self.buffer = [liq for liq in self.buffer if liq.timestamp >= cutoff_time]
        self.count = len(self.buffer)
        self.head = 0
    
    def memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        return len(self.buffer) * 18
    
    def __len__(self) -> int:
        return len(self.buffer)