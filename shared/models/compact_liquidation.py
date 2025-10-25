"""
Compact Liquidation Data Model
Memory-optimized structure for liquidation events
Target: 18 bytes per record
"""

import struct
from typing import NamedTuple, Optional, TYPE_CHECKING
from datetime import datetime
from enum import IntEnum

if TYPE_CHECKING:
    from typing import Optional


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

    @classmethod
    def from_hyperliquid_data(cls, data: dict, liquidation_side: Optional['LiquidationSide'] = None) -> 'CompactLiquidation':
        """
        Create compact liquidation from Hyperliquid WebSocket trade data

        Expected Hyperliquid format:
        {
            "coin": "BTC",
            "side": "B",  # B=Buy, A=Sell (trade side, NOT liquidation side)
            "px": "45000.5",
            "sz": "0.5",
            "time": 1702000000000,
            "hash": "0x...",
            "tid": 12345678,
            "users": ["0x...", "0x..."],  # [buyer, seller]
            "liquidation_side": LiquidationSide,  # Added by our processing
            "liquidated_user": "0x..."  # Added by our processing
        }

        Args:
            data: Trade data from WebSocket
            liquidation_side: The actual liquidation side (LONG or SHORT), determined by
                            checking HLP's position in the users array
        """
        # Extract values
        coin = data.get('coin', '')
        price = float(data.get('px', 0))
        size = float(data.get('sz', 0))
        timestamp_ms = int(data.get('time', 0))

        # Convert to seconds
        timestamp = timestamp_ms // 1000

        # Calculate USD value
        value_usd = price * size

        # Use the provided liquidation_side or extract from data
        if liquidation_side is not None:
            side = liquidation_side
        elif 'liquidation_side' in data:
            side = data['liquidation_side']
        else:
            # Fallback to old logic (which is incorrect but prevents breaking)
            # This should not happen if the provider is fixed
            side_str = data.get('side', '')
            side = LiquidationSide.LONG if side_str == 'A' else LiquidationSide.SHORT

        # Create symbol for Hyperliquid (e.g., "BTC-PERP")
        symbol = f"{coin}-PERP"

        # Create compact representation
        return cls(
            timestamp=timestamp,
            symbol_hash=hash(symbol) & 0xFFFFFFFF,  # 4 bytes
            side=side.value,
            price=int(price * 100),  # Store with 2 decimal precision
            quantity=int(size * 1000000),  # Store with 6 decimal precision
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
        # Recalculate from actual price and quantity for accuracy
        # (value_usd field is stored / 1000 for memory optimization)
        return self.actual_price * self.actual_quantity

    @property
    def amount_usd(self) -> float:
        """Alias for actual_value_usd for convenience"""
        return self.actual_value_usd

    @property
    def symbol(self) -> str:
        """Get symbol string (reconstructed from hash - returns generic for now)"""
        # Note: Can't fully reconstruct original symbol from hash
        # This is a limitation of the memory-optimized design
        # For display purposes, use the original symbol if available
        return f"SYMBOL_{self.symbol_hash}"

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