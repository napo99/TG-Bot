"""
Liquidation Monitor for Telegram Bot
Real-time liquidation tracking integrated into the main bot
"""

import asyncio
import json
import websockets
import logging
from typing import Optional, Dict, List
from datetime import datetime
import os
from dataclasses import dataclass


@dataclass
class Liquidation:
    """Simple liquidation data structure"""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    price: float
    quantity: float
    value_usd: float
    timestamp: datetime
    
    def format_alert(self) -> str:
        """Format liquidation as alert message"""
        side_emoji = "📉" if self.side == "LONG" else "📈"
        return (f"🚨 **{self.symbol} LIQUIDATION**\n"
                f"{side_emoji} **{self.side}** position liquidated\n"
                f"💰 **Value**: ${self.value_usd:,.0f}\n"
                f"📊 **Size**: {self.quantity:.4f} @ ${self.price:,.2f}\n"
                f"🕐 **Time**: {self.timestamp.strftime('%H:%M:%S')}")


class LiquidationTracker:
    """Tracks liquidations and detects significant events"""
    
    def __init__(self):
        self.recent_liquidations: List[Liquidation] = []
        self.thresholds = {
            'BTC': 100000,  # $100k+ for BTC
            'ETH': 50000,   # $50k+ for ETH  
            'SOL': 25000,   # $25k+ for SOL
            'default': 10000  # $10k+ for others
        }
        self.cascade_window = 30  # 30 seconds
        self.cascade_min_count = 5  # 5+ liquidations for cascade
    
    def add_liquidation(self, liquidation: Liquidation) -> Optional[str]:
        """Add liquidation and check for alerts"""
        # Clean old liquidations (keep last 100)
        self.recent_liquidations = self.recent_liquidations[-99:]
        self.recent_liquidations.append(liquidation)
        
        # Check for single large liquidation alert
        if self._should_alert_single(liquidation):
            return liquidation.format_alert()
        
        # Check for cascade
        cascade_alert = self._check_cascade()
        if cascade_alert:
            return cascade_alert
        
        return None
    
    def _should_alert_single(self, liquidation: Liquidation) -> bool:
        """Check if single liquidation meets alert criteria"""
        symbol_base = liquidation.symbol.replace('USDT', '').replace('USDC', '')
        threshold = self.thresholds.get(symbol_base, self.thresholds['default'])
        return liquidation.value_usd >= threshold
    
    def _check_cascade(self) -> Optional[str]:
        """Check for liquidation cascade"""
        if len(self.recent_liquidations) < self.cascade_min_count:
            return None
        
        # Get liquidations from last 30 seconds
        now = datetime.now()
        recent = [liq for liq in self.recent_liquidations 
                 if (now - liq.timestamp).total_seconds() <= self.cascade_window]
        
        if len(recent) >= self.cascade_min_count:
            # Group by symbol
            symbol_groups = {}
            for liq in recent:
                symbol_groups.setdefault(liq.symbol, []).append(liq)
            
            # Find largest group
            largest_group = max(symbol_groups.values(), key=len)
            if len(largest_group) >= self.cascade_min_count:
                symbol = largest_group[0].symbol
                total_value = sum(liq.value_usd for liq in largest_group)
                long_count = sum(1 for liq in largest_group if liq.side == 'LONG')
                short_count = len(largest_group) - long_count
                
                return (f"🚨 **{symbol} LIQUIDATION CASCADE**\n"
                       f"⚡ **{len(largest_group)} liquidations** in 30 seconds\n"
                       f"💰 **Total**: ${total_value:,.0f}\n"
                       f"📊 **Breakdown**: {long_count} longs, {short_count} shorts\n"
                       f"⚠️ **Potential price impact expected**")
        
        return None


class LiquidationMonitor:
    """WebSocket liquidation monitor for the telegram bot"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.tracker = LiquidationTracker()
        self.websocket_url = "wss://fstream.binance.com/ws/!forceOrder@arr"
        self.running = False
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        
    async def start_monitoring(self):
        """Start liquidation monitoring"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting liquidation monitoring...")
        
        while self.running:
            try:
                await self._connect_and_monitor()
            except Exception as e:
                self.logger.error(f"Liquidation monitor error: {e}")
                if self.running:
                    await asyncio.sleep(5)  # Wait before reconnecting
    
    def stop_monitoring(self):
        """Stop liquidation monitoring"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
    
    async def _connect_and_monitor(self):
        """Connect to WebSocket and monitor liquidations"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                self.logger.info("Connected to Binance liquidation stream")
                
                async for message in websocket:
                    if not self.running:
                        break
                    
                    try:
                        data = json.loads(message)
                        await self._process_liquidation(data)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing liquidation: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            raise
    
    async def _process_liquidation(self, data: dict):
        """Process incoming liquidation data"""
        try:
            order = data.get('o', {})
            if not order:
                return
            
            # Extract liquidation data
            symbol = order.get('s', '')
            side_str = order.get('S', '')  # SELL = long liquidation
            price = float(order.get('ap', 0))
            quantity = float(order.get('z', 0))
            timestamp_ms = int(order.get('T', 0))
            
            # Calculate USD value
            value_usd = price * quantity
            
            # Convert side (Binance uses opposite logic)
            side = 'LONG' if side_str == 'SELL' else 'SHORT'
            
            # Create liquidation object
            liquidation = Liquidation(
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                value_usd=value_usd,
                timestamp=datetime.fromtimestamp(timestamp_ms / 1000)
            )
            
            # Check for alerts
            alert_message = self.tracker.add_liquidation(liquidation)
            if alert_message:
                await self._send_alert(alert_message)
                
        except Exception as e:
            self.logger.error(f"Error processing liquidation data: {e}")
    
    async def _send_alert(self, message: str):
        """Send alert to telegram chat"""
        try:
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if chat_id and hasattr(self.bot, 'application'):
                await self.bot.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                self.logger.info("Liquidation alert sent")
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    def get_recent_liquidations(self, limit: int = 10) -> List[Liquidation]:
        """Get recent liquidations for display"""
        return self.tracker.recent_liquidations[-limit:]
    
    def get_status(self) -> dict:
        """Get monitoring status"""
        return {
            'running': self.running,
            'connected': self.websocket is not None,
            'total_tracked': len(self.tracker.recent_liquidations),
            'thresholds': self.tracker.thresholds
        }