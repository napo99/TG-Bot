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
from shared.intelligence.dynamic_thresholds import DynamicThresholdEngine, ThresholdResult
from formatting_utils import format_dollar_amount, format_large_number


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
        """Format institutional-grade liquidation alert with context"""
        side_emoji = "📉" if self.side == "LONG" else "📈"
        symbol_clean = self.symbol.replace('USDT', '').replace('USDC', '')
        
        # Determine size classification for institutional context
        if self.value_usd >= 1_000_000:
            size_class = "🐋 WHALE"
        elif self.value_usd >= 500_000:
            size_class = "🦈 INSTITUTIONAL"  
        elif self.value_usd >= 100_000:
            size_class = "🐟 LARGE TRADER"
        else:
            size_class = "📊 TRADER"
            
        # Calculate market impact indicator
        leverage_estimate = "~3-5x" if self.value_usd > 500_000 else "~10-20x"
        
        return (f"🚨 **{symbol_clean} LIQUIDATION - {size_class}**\n"
                f"{side_emoji} **{self.side}** liquidated\n"
                f"💰 **{format_dollar_amount(self.value_usd, 1)}** ({self.quantity:.2f} {symbol_clean})\n"
                f"📊 **Price**: ${self.price:,.2f} | **Leverage**: {leverage_estimate}\n"
                f"🎯 **Impact**: {'HIGH' if self.value_usd > 500_000 else 'MEDIUM'} - Watch cascade\n"
                f"🕐 {self.timestamp.strftime('%H:%M:%S')}")


class LiquidationTracker:
    """Tracks liquidations and detects significant events with dynamic thresholds"""
    
    def __init__(self, market_data_url: str = "http://localhost:8001"):
        self.recent_liquidations: List[Liquidation] = []
        self.threshold_engine = DynamicThresholdEngine(market_data_url=market_data_url)
        self.threshold_cache: Dict[str, ThresholdResult] = {}
        self.cascade_window = 30  # 30 seconds
        
        # INSTITUTIONAL THRESHOLDS - Eliminate retail noise
        self.fallback_thresholds = {
            'BTC': 500000,  # $500k+ for BTC (5x increase) 
            'ETH': 250000,  # $250k+ for ETH (5x increase)
            'SOL': 100000,  # $100k+ for SOL (4x increase)
            'default': 50000  # $50k+ for others (5x increase)
        }
    
    async def _get_threshold(self, symbol: str) -> ThresholdResult:
        """Get threshold with caching"""
        # Check cache first
        if symbol in self.threshold_cache:
            cached = self.threshold_cache[symbol]
            if datetime.now() < cached.next_review_time:
                return cached
        
        # Calculate new threshold
        threshold_result = await self.threshold_engine.calculate_liquidation_threshold(symbol)
        self.threshold_cache[symbol] = threshold_result
        return threshold_result
    
    async def add_liquidation(self, liquidation: Liquidation) -> Optional[str]:
        """Add liquidation and check for alerts"""
        # Clean old liquidations (keep last 100)
        self.recent_liquidations = self.recent_liquidations[-99:]
        self.recent_liquidations.append(liquidation)
        
        # Check for single large liquidation alert
        if await self._should_alert_single(liquidation):
            return liquidation.format_alert()
        
        # Check for cascade
        cascade_alert = await self._check_cascade()
        if cascade_alert:
            return cascade_alert
        
        return None
    
    async def _should_alert_single(self, liquidation: Liquidation) -> bool:
        """Check if single liquidation meets alert criteria using dynamic thresholds"""
        try:
            # Get dynamic threshold
            threshold_result = await self._get_threshold(liquidation.symbol)
            return liquidation.value_usd >= threshold_result.single_liquidation_usd
        except Exception as e:
            logging.error(f"Error getting dynamic threshold for {liquidation.symbol}: {e}")
            # Fallback to hardcoded thresholds
            symbol_base = liquidation.symbol.replace('USDT', '').replace('USDC', '')
            threshold = self.fallback_thresholds.get(symbol_base, self.fallback_thresholds['default'])
            return liquidation.value_usd >= threshold
    
    async def _check_cascade(self) -> Optional[str]:
        """Check for liquidation cascade"""
        if len(self.recent_liquidations) < 3:  # Minimum cascades needed
            return None
        
        # Get liquidations from last 30 seconds
        now = datetime.now()
        recent = [liq for liq in self.recent_liquidations 
                 if (now - liq.timestamp).total_seconds() <= self.cascade_window]
        
        if len(recent) >= 3:  # Minimum for any cascade
            # Group by symbol
            symbol_groups = {}
            for liq in recent:
                symbol_groups.setdefault(liq.symbol, []).append(liq)
            
            # Find largest group
            largest_group = max(symbol_groups.values(), key=len)
            # Get dynamic cascade threshold
            try:
                threshold_result = await self._get_threshold(symbol)
                cascade_min_count = threshold_result.cascade_count_threshold
                cascade_min_value = threshold_result.cascade_threshold_usd
            except Exception as e:
                logging.error(f"Error getting cascade thresholds for {symbol}: {e}")
                cascade_min_count = 5  # Fallback
                cascade_min_value = 500000  # Fallback
            
            if len(largest_group) >= cascade_min_count and total_value >= cascade_min_value:
                symbol = largest_group[0].symbol
                total_value = sum(liq.value_usd for liq in largest_group)
                long_count = sum(1 for liq in largest_group if liq.side == 'LONG')
                short_count = len(largest_group) - long_count
                
                # Enhanced institutional intelligence
                symbol_clean = symbol.replace('USDT', '').replace('USDC', '')
                avg_size = total_value / len(largest_group)
                max_single = max(liq.value_usd for liq in largest_group)
                long_bias_pct = (long_count / len(largest_group)) * 100
                
                # Classify cascade severity
                if total_value >= 10_000_000:  # $10M+
                    severity = "🚨 TIER-1 INSTITUTIONAL"
                elif total_value >= 5_000_000:  # $5M+
                    severity = "⚡ TIER-2 MAJOR"
                else:
                    severity = "📊 TIER-3 SIGNIFICANT"
                
                # Estimate cascade probability (simple heuristic)
                cascade_risk = "HIGH" if long_count > short_count * 2 else "MEDIUM"
                
                # Calculate total coin amount
                total_coins = sum(liq.quantity for liq in largest_group)
                
                return (f"{severity} CASCADE - {symbol_clean}\n"
                       f"⚡ **{len(largest_group)} liquidations** in 30s\n"
                       f"💰 **{format_dollar_amount(total_value, 1)}** ({total_coins:.1f} {symbol_clean})\n"
                       f"📊 **Avg**: {format_dollar_amount(avg_size, 1)} | **Max**: {format_dollar_amount(max_single, 1)}\n"
                       f"⚖️ **{long_bias_pct:.0f}% LONG** vs {100-long_bias_pct:.0f}% SHORT\n"
                       f"🎯 **Risk**: {cascade_risk} - Next 2-5min critical\n"
                       f"🏦 {'Institutional deleveraging' if avg_size > 200_000 else 'Retail panic'}")
        
        return None


class LiquidationMonitor:
    """WebSocket liquidation monitor for the telegram bot"""
    
    def __init__(self, bot_instance, market_data_url: str = "http://localhost:8001"):
        self.bot = bot_instance
        self.tracker = LiquidationTracker(market_data_url)
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
            
            # Check for alerts (now async)
            alert_message = await self.tracker.add_liquidation(liquidation)
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
            'threshold_cache_size': len(getattr(self.tracker, 'threshold_cache', {}))
        }