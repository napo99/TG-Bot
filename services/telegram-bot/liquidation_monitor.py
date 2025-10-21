"""
Liquidation Monitor for Telegram Bot
Real-time liquidation tracking integrated into the main bot
"""

import asyncio
import json
import websockets
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import os
from dataclasses import dataclass
import numpy as np  # Added for advanced cascade prediction
from collections import deque
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
    """Enhanced liquidation tracker with institutional intelligence (consolidated system)"""
    
    def __init__(self, market_data_url: str = "http://localhost:8001"):
        # Enhanced tracking with deque for better performance
        self.recent_liquidations: deque = deque(maxlen=100)  # Performance optimization
        self.threshold_engine = DynamicThresholdEngine(market_data_url=market_data_url)
        self.threshold_cache: Dict[str, ThresholdResult] = {}
        self.cascade_window = 30  # 30 seconds for immediate cascade, 60s for prediction
        
        # DATA-DRIVEN INSTITUTIONAL THRESHOLDS - Based on 0.05% of Open Interest Analysis
        # Analysis: BTC $10.6B OI, ETH $11.0B OI, SOL $2.5B OI (Aug 2025)
        # Target: Eliminate 99.95% of retail noise, align with $530M+ institutional liquidation events
        self.fallback_thresholds = {
            'BTC': 5000000,   # $5M+ (0.05% of $10.6B OI) - True institutional level
            'ETH': 5000000,   # $5M+ (0.05% of $11.0B OI) - True institutional level  
            'SOL': 1250000,   # $1.25M+ (0.05% of $2.5B OI) - True institutional level
            'default': 1000000  # $1M+ MINIMUM - Major altcoins institutional floor
        }
        
        # Alert cooldown to prevent spam (from enhanced system)
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_duration = timedelta(minutes=2)
        
        # Performance metrics (consolidated from enhanced system)
        self.processed_liquidations = 0
        self.alerts_sent = 0
        self.cascade_predictions = 0
        self.start_time = datetime.now()
    
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
        """Enhanced liquidation processing with performance tracking"""
        self.processed_liquidations += 1
        
        # Add to deque (automatically maintains size limit)
        self.recent_liquidations.append(liquidation)
        
        # Check for single large liquidation alert with cooldown
        if await self._should_alert_single(liquidation):
            alert_key = f"{liquidation.symbol}_single"
            if self._check_alert_cooldown(alert_key):
                self.alerts_sent += 1
                self._set_alert_cooldown(alert_key)
                return liquidation.format_alert()
        
        # Check for cascade with enhanced prediction
        cascade_alert = await self._check_cascade()
        if cascade_alert:
            alert_key = f"{liquidation.symbol}_cascade"
            if self._check_alert_cooldown(alert_key):
                self.cascade_predictions += 1
                self.alerts_sent += 1
                self._set_alert_cooldown(alert_key)
                return cascade_alert
        
        return None
    
    def _check_alert_cooldown(self, alert_key: str) -> bool:
        """Check if alert is not in cooldown period"""
        if alert_key in self.alert_cooldown:
            return datetime.now() - self.alert_cooldown[alert_key] >= self.cooldown_duration
        return True
    
    def _set_alert_cooldown(self, alert_key: str):
        """Set alert cooldown timestamp"""
        self.alert_cooldown[alert_key] = datetime.now()
    
    async def _should_alert_single(self, liquidation: Liquidation) -> bool:
        """Check if single liquidation meets INSTITUTIONAL criteria (minimum $100K)"""
        # Get minimum institutional threshold
        symbol_base = liquidation.symbol.replace('USDT', '').replace('USDC', '')
        min_institutional_threshold = self.fallback_thresholds.get(symbol_base, self.fallback_thresholds['default'])
        
        try:
            # Try to get dynamic threshold but ENFORCE institutional minimums
            threshold_result = await self._get_threshold(liquidation.symbol)
            dynamic_threshold = threshold_result.single_liquidation_usd
            
            # Use the HIGHER of dynamic or institutional threshold (never go below institutional)
            final_threshold = max(dynamic_threshold, min_institutional_threshold)
            return liquidation.value_usd >= final_threshold
        except Exception as e:
            logging.error(f"Error getting dynamic threshold for {liquidation.symbol}: {e}")
            # Fallback to institutional thresholds (minimum $100K for all assets)
            return liquidation.value_usd >= min_institutional_threshold
    
    async def _check_cascade(self) -> Optional[str]:
        """Enhanced cascade detection with 6-factor analysis (consolidated from enhanced system)"""
        if len(self.recent_liquidations) < 3:  # Minimum cascades needed
            return None
        
        # Get liquidations from last 60 seconds (extended for better prediction)
        now = datetime.now()
        recent = [liq for liq in self.recent_liquidations 
                 if (now - liq.timestamp).total_seconds() <= 60]  # Extended window
        
        if len(recent) >= 3:  # Minimum for any cascade
            # Group by symbol
            symbol_groups = {}
            for liq in recent:
                symbol_groups.setdefault(liq.symbol, []).append(liq)
            
            # Find largest group and analyze it
            largest_group = max(symbol_groups.values(), key=len)
            symbol = largest_group[0].symbol
            total_value = sum(liq.value_usd for liq in largest_group)
            
            # Get dynamic cascade threshold
            try:
                threshold_result = await self._get_threshold(symbol)
                cascade_min_count = threshold_result.cascade_count_threshold
                cascade_min_value = threshold_result.cascade_threshold_usd
            except Exception as e:
                logging.error(f"Error getting cascade thresholds for {symbol}: {e}")
                cascade_min_count = 5  # Fallback
                cascade_min_value = 500000  # Fallback
            
            # Enhanced 6-factor cascade analysis (consolidated from enhanced_liquidation_monitor.py)
            if len(largest_group) >= cascade_min_count and total_value >= cascade_min_value:
                # Calculate advanced risk factors
                risk_analysis = await self._analyze_cascade_risk_factors(largest_group, threshold_result)
                
                long_count = sum(1 for liq in largest_group if liq.side == 'LONG')
                short_count = len(largest_group) - long_count
                
                # Enhanced institutional intelligence
                symbol_clean = symbol.replace('USDT', '').replace('USDC', '')
                avg_size = total_value / len(largest_group)
                max_single = max(liq.value_usd for liq in largest_group)
                long_bias_pct = (long_count / len(largest_group)) * 100
                
                # Classify cascade severity with risk scoring
                if risk_analysis['composite_risk'] > 1.5:
                    severity = "🔴 EXTREME CASCADE RISK"
                elif risk_analysis['composite_risk'] > 1.0:
                    severity = "🟠 HIGH CASCADE RISK"
                elif total_value >= 10_000_000:  # $10M+
                    severity = "🚨 TIER-1 INSTITUTIONAL"
                elif total_value >= 5_000_000:  # $5M+
                    severity = "⚡ TIER-2 MAJOR"
                else:
                    severity = "📊 TIER-3 SIGNIFICANT"
                
                # Advanced cascade risk prediction
                cascade_risk = risk_analysis['risk_level']
                
                # Calculate total coin amount
                total_coins = sum(liq.quantity for liq in largest_group)
                
                return (f"{severity} - {symbol_clean}\n"
                       f"⚡ **{len(largest_group)} liquidations** in 60s\n"
                       f"💰 **{format_dollar_amount(total_value, 1)}** ({total_coins:.1f} {symbol_clean})\n"
                       f"📊 **Avg**: {format_dollar_amount(avg_size, 1)} | **Max**: {format_dollar_amount(max_single, 1)}\n"
                       f"⚖️ **{long_bias_pct:.0f}% LONG** vs {100-long_bias_pct:.0f}% SHORT\n"
                       f"🎯 **Risk Score**: {risk_analysis['composite_risk']:.2f}/2.0 ({cascade_risk})\n"
                       f"🔮 **Prediction**: {'Cascade imminent (30-90s)' if risk_analysis['composite_risk'] > 1.2 else 'Next 2-5min critical'}\n"
                       f"🏦 {'Institutional deleveraging detected' if avg_size > 200_000 else 'Market stress detected'}")
        
        return None
    
    async def _analyze_cascade_risk_factors(self, liquidations: List, threshold_result) -> Dict:
        """6-factor cascade risk analysis (consolidated from enhanced system)"""
        if not liquidations:
            return {'composite_risk': 0.0, 'risk_level': 'LOW'}
        
        total_value = sum(liq.value_usd for liq in liquidations)
        avg_price = sum(liq.price for liq in liquidations) / len(liquidations)
        
        # Factor 1: Volume concentration
        volume_concentration = total_value / threshold_result.cascade_threshold_usd
        
        # Factor 2: Time compression (faster liquidations = higher risk)
        timestamps = [liq.timestamp for liq in liquidations]
        time_span = max(timestamps) - min(timestamps)
        time_compression = 60.0 / max(1.0, time_span.total_seconds())  # Normalize to 60 seconds
        
        # Factor 3: Price concentration (liquidations at similar prices)
        prices = [liq.price for liq in liquidations]
        if len(prices) > 1:
            price_std = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
            price_concentration = max(0, 1.0 - price_std * 10)  # Higher when prices are close
        else:
            price_concentration = 1.0
        
        # Factor 4: Side imbalance (all longs or all shorts = higher cascade risk)
        sides = [liq.side for liq in liquidations]
        long_count = sum(1 for side in sides if side == 'LONG')
        short_count = len(sides) - long_count
        side_imbalance = abs(long_count - short_count) / len(sides)
        
        # Factor 5: Institutional ratio (more institutional = higher systemic risk)
        institutional_count = sum(1 for liq in liquidations if liq.value_usd >= 500_000)
        institutional_ratio = institutional_count / len(liquidations)
        
        # Factor 6: Market session context
        session_multiplier = self._get_session_risk_multiplier()
        
        # Composite risk score (0.0 to 2.0+)
        risk_factors = {
            'volume_concentration': volume_concentration * 0.25,
            'time_compression': min(2.0, time_compression) * 0.20,
            'price_concentration': price_concentration * 0.20,
            'side_imbalance': side_imbalance * 0.15,
            'institutional_ratio': institutional_ratio * 0.15,
            'session_context': session_multiplier * 0.05
        }
        
        composite_risk = sum(risk_factors.values())
        
        # Determine risk level
        if composite_risk > 1.5:
            risk_level = 'EXTREME'
        elif composite_risk > 1.0:
            risk_level = 'HIGH'
        elif composite_risk > 0.7:
            risk_level = 'MODERATE'
        else:
            risk_level = 'LOW'
        
        return {
            'composite_risk': composite_risk,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'institutional_ratio': institutional_ratio,
            'side_imbalance': side_imbalance
        }
    
    def _get_session_risk_multiplier(self) -> float:
        """Get session-based risk multiplier (Asian=higher risk due to lower liquidity)"""
        utc_hour = datetime.utcnow().hour
        
        if utc_hour >= 20 or utc_hour < 4:
            return 1.2  # Asian session - higher cascade risk
        elif 4 <= utc_hour < 12:
            return 0.9  # European session - medium liquidity
        elif 12 <= utc_hour < 20:
            return 0.8  # US session - highest liquidity, lower cascade risk
        else:
            # Weekend check
            weekday = datetime.utcnow().weekday()
            if weekday >= 5:  # Saturday = 5, Sunday = 6
                return 1.5  # Weekend - very low liquidity, highest cascade risk
            return 0.8
    
    def get_performance_status(self) -> dict:
        """Get enhanced performance metrics (consolidated from enhanced system)"""
        uptime = datetime.now() - self.start_time
        return {
            'tracker_type': 'consolidated_institutional',
            'processed_liquidations': self.processed_liquidations,
            'alerts_sent': self.alerts_sent,
            'cascade_predictions': self.cascade_predictions,
            'recent_liquidations_count': len(self.recent_liquidations),
            'threshold_cache_size': len(self.threshold_cache),
            'uptime_seconds': uptime.total_seconds(),
            'processing_rate': self.processed_liquidations / uptime.total_seconds() if uptime.total_seconds() > 0 else 0,
            'alert_effectiveness': (self.alerts_sent / max(1, self.processed_liquidations)) * 100,
            'cooldown_active_alerts': len([k for k, v in self.alert_cooldown.items() 
                                         if datetime.now() - v < self.cooldown_duration])
        }


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
        """Get comprehensive monitoring status (consolidated system)"""
        tracker_performance = self.tracker.get_performance_status()
        return {
            'running': self.running,
            'connected': self.websocket is not None,
            'websocket_url': self.websocket_url,
            'system_type': 'consolidated_institutional_liquidation_monitor',
            'total_tracked': len(self.tracker.recent_liquidations),
            'threshold_cache_size': len(getattr(self.tracker, 'threshold_cache', {})),
            'performance_metrics': tracker_performance,
            'features': {
                'dynamic_thresholds': True,
                '6_factor_cascade_prediction': True,
                'institutional_filtering': True,
                'alert_cooldown': True,
                'session_awareness': True,
                'enhanced_risk_scoring': True
            }
        }