"""
Enhanced Liquidation Monitor - Phase 2 Implementation
Advanced liquidation detection with real-time intelligence integration
Part of the Institutional Trading Intelligence System
"""

import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from collections import deque
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.intelligence.dynamic_thresholds import DynamicThresholdEngine, ThresholdResult
from shared.intelligence.real_time_pipeline import (
    RealTimeDataPipeline, LiquidationEvent, TradeEvent, StreamProcessor
)

logger = logging.getLogger(__name__)


class EnhancedLiquidationProcessor(StreamProcessor):
    """Advanced liquidation processing with cascade prediction"""
    
    def __init__(self, bot_instance=None, threshold_engine=None):
        self.bot = bot_instance
        self.threshold_engine = threshold_engine or DynamicThresholdEngine()
        
        # Enhanced tracking
        self.liquidation_history: Dict[str, deque] = {}  # symbol -> liquidations
        self.cascade_tracker = LiquidationCascadeTracker()
        self.threshold_cache: Dict[str, ThresholdResult] = {}
        
        # Performance metrics
        self.processed_liquidations = 0
        self.alerts_sent = 0
        self.cascade_predictions = 0
        self.start_time = datetime.now()
        
        # Alert cooldown to prevent spam
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_duration = timedelta(minutes=2)
    
    async def process_trade(self, trade: TradeEvent):
        """Process trade events (used for context in liquidation prediction)"""
        # Trades provide volume context for cascade prediction
        symbol = trade.symbol
        if symbol not in self.liquidation_history:
            self.liquidation_history[symbol] = deque(maxlen=100)
        
        # Store trade context for cascade analysis
        if hasattr(self, 'trade_context'):
            if symbol not in self.trade_context:
                self.trade_context[symbol] = deque(maxlen=50)
            self.trade_context[symbol].append({
                'price': trade.price,
                'volume': trade.value_usd,
                'timestamp': trade.timestamp,
                'is_whale': trade.is_whale
            })
    
    async def process_liquidation(self, liquidation: LiquidationEvent):
        """Enhanced liquidation processing with cascade detection"""
        try:
            symbol = liquidation.symbol
            self.processed_liquidations += 1
            
            # Initialize tracking for new symbols
            if symbol not in self.liquidation_history:
                self.liquidation_history[symbol] = deque(maxlen=100)
            
            # Add to history
            self.liquidation_history[symbol].append({
                'side': liquidation.side,
                'price': liquidation.price,
                'value_usd': liquidation.value_usd,
                'timestamp': liquidation.timestamp,
                'exchange': liquidation.exchange
            })
            
            # Check for single large liquidation alert
            if await self._should_alert_single(liquidation):
                alert_message = await self._format_single_liquidation_alert(liquidation)
                await self._send_alert(alert_message, f"{symbol}_single")
            
            # Check for cascade potential
            cascade_alert = await self._check_cascade_prediction(symbol)
            if cascade_alert:
                await self._send_alert(cascade_alert, f"{symbol}_cascade")
                self.cascade_predictions += 1
            
        except Exception as e:
            logger.error(f"Error processing liquidation for {symbol}: {e}")
    
    async def _should_alert_single(self, liquidation: LiquidationEvent) -> bool:
        """Check if single liquidation meets dynamic alert criteria"""
        try:
            # Get dynamic threshold
            threshold_result = await self._get_threshold(liquidation.symbol)
            return liquidation.value_usd >= threshold_result.single_liquidation_usd
        except Exception as e:
            logger.error(f"Error getting threshold for {liquidation.symbol}: {e}")
            # Fallback to basic threshold
            return liquidation.value_usd >= 100000  # $100k fallback
    
    async def _check_cascade_prediction(self, symbol: str) -> Optional[str]:
        """Advanced cascade prediction with multiple signals"""
        try:
            liquidations = self.liquidation_history.get(symbol, deque())
            if len(liquidations) < 3:
                return None
            
            # Get recent liquidations (last 60 seconds for prediction)
            now = datetime.now()
            recent_window = timedelta(seconds=60)
            recent_liquidations = [
                liq for liq in liquidations
                if (now - liq['timestamp']).total_seconds() <= recent_window.total_seconds()
            ]
            
            if len(recent_liquidations) < 3:
                return None
            
            # Get dynamic cascade thresholds
            threshold_result = await self._get_threshold(symbol)
            
            # Analyze cascade potential
            cascade_analysis = await self._analyze_cascade_potential(
                symbol, recent_liquidations, threshold_result
            )
            
            if cascade_analysis['risk_level'] in ['HIGH', 'EXTREME']:
                return await self._format_cascade_prediction_alert(symbol, cascade_analysis)
            
        except Exception as e:
            logger.error(f"Error in cascade prediction for {symbol}: {e}")
        
        return None
    
    async def _analyze_cascade_potential(self, symbol: str, liquidations: List[dict], 
                                       threshold_result: ThresholdResult) -> Dict:
        """Analyze cascade potential using multiple factors"""
        total_value = sum(liq['value_usd'] for liq in liquidations)
        avg_price = sum(liq['price'] for liq in liquidations) / len(liquidations)
        
        # Factor 1: Volume concentration
        volume_concentration = total_value / threshold_result.cascade_threshold_usd
        
        # Factor 2: Time compression (faster liquidations = higher risk)
        time_span = max(liq['timestamp'] for liq in liquidations) - min(liq['timestamp'] for liq in liquidations)
        time_compression = 60.0 / max(1.0, time_span.total_seconds())  # Normalize to 60 seconds
        
        # Factor 3: Price impact (liquidations at similar prices)
        prices = [liq['price'] for liq in liquidations]
        price_std = (max(prices) - min(prices)) / avg_price if avg_price > 0 else 0
        price_concentration = max(0, 1.0 - price_std * 10)  # Higher when prices are close
        
        # Factor 4: Side imbalance (all longs or all shorts = higher cascade risk)
        sides = [liq['side'] for liq in liquidations]
        long_count = sum(1 for side in sides if side == 'LONG')
        short_count = len(sides) - long_count
        side_imbalance = abs(long_count - short_count) / len(sides)
        
        # Factor 5: Market context (get from trade context if available)
        market_stress = 0.5  # Default - would be calculated from recent volatility/volume
        
        # Composite risk score
        risk_factors = {
            'volume_concentration': volume_concentration * 0.3,
            'time_compression': min(2.0, time_compression) * 0.25,
            'price_concentration': price_concentration * 0.2,
            'side_imbalance': side_imbalance * 0.15,
            'market_stress': market_stress * 0.1
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
            'risk_level': risk_level,
            'composite_risk': composite_risk,
            'risk_factors': risk_factors,
            'total_value': total_value,
            'liquidation_count': len(liquidations),
            'dominant_side': 'LONG' if long_count > short_count else 'SHORT',
            'avg_price': avg_price,
            'time_span_seconds': time_span.total_seconds()
        }
    
    async def _format_single_liquidation_alert(self, liquidation: LiquidationEvent) -> str:
        """Format enhanced single liquidation alert"""
        side_emoji = "📉" if liquidation.side == "LONG" else "📈"
        
        # Add cascade potential assessment
        recent_liquidations = list(self.liquidation_history.get(liquidation.symbol, []))[-5:]
        cascade_risk = "LOW"
        if len(recent_liquidations) >= 3:
            threshold_result = await self._get_threshold(liquidation.symbol)
            analysis = await self._analyze_cascade_potential(liquidation.symbol, recent_liquidations, threshold_result)
            cascade_risk = analysis['risk_level']
        
        risk_emoji = {
            'LOW': '🟢', 'MODERATE': '🟡', 'HIGH': '🟠', 'EXTREME': '🔴'
        }.get(cascade_risk, '🟢')
        
        return (f"🚨 **ENHANCED LIQUIDATION ALERT**\n"
                f"{side_emoji} **{liquidation.symbol} {liquidation.side}** liquidated\n"
                f"💰 **Value**: ${liquidation.value_usd:,.0f}\n"
                f"📊 **Size**: {liquidation.quantity:.4f} @ ${liquidation.price:,.2f}\n"
                f"{risk_emoji} **Cascade Risk**: {cascade_risk}\n"
                f"🏦 **Exchange**: {liquidation.exchange.upper()}\n"
                f"🕐 **Time**: {liquidation.timestamp.strftime('%H:%M:%S')}")
    
    async def _format_cascade_prediction_alert(self, symbol: str, analysis: Dict) -> str:
        """Format cascade prediction alert"""
        risk_level = analysis['risk_level']
        risk_emoji = {
            'HIGH': '🟠⚠️', 'EXTREME': '🔴🚨'
        }.get(risk_level, '🟡')
        
        return (f"{risk_emoji} **LIQUIDATION CASCADE PREDICTION**\n"
                f"📊 **{symbol}**: {analysis['liquidation_count']} liquidations detected\n"
                f"💰 **Total Value**: ${analysis['total_value']:,.0f}\n"
                f"📈 **Risk Level**: {risk_level}\n"
                f"🎯 **Risk Score**: {analysis['composite_risk']:.2f}/2.0\n"
                f"⚖️ **Dominant Side**: {analysis['dominant_side']}\n"
                f"💲 **Price Level**: ${analysis['avg_price']:,.2f}\n"
                f"⏱️ **Time Window**: {analysis['time_span_seconds']:.0f}s\n"
                f"🔮 **Prediction**: Cascade likely within 2-5 minutes")
    
    async def _get_threshold(self, symbol: str) -> ThresholdResult:
        """Get threshold with caching"""
        if symbol in self.threshold_cache:
            cached = self.threshold_cache[symbol]
            if datetime.now() < cached.next_review_time:
                return cached
        
        # Calculate new threshold
        threshold_result = await self.threshold_engine.calculate_liquidation_threshold(symbol)
        self.threshold_cache[symbol] = threshold_result
        return threshold_result
    
    async def _send_alert(self, message: str, alert_key: str):
        """Send alert with cooldown protection"""
        try:
            # Check cooldown
            if alert_key in self.alert_cooldown:
                if datetime.now() - self.alert_cooldown[alert_key] < self.cooldown_duration:
                    return  # Skip alert - still in cooldown
            
            # Send through bot if available
            if self.bot and hasattr(self.bot, 'application'):
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                if chat_id:
                    await self.bot.application.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    self.alerts_sent += 1
                    self.alert_cooldown[alert_key] = datetime.now()
                    logger.info(f"Enhanced liquidation alert sent: {alert_key}")
            
        except Exception as e:
            logger.error(f"Error sending alert {alert_key}: {e}")
    
    async def get_status(self) -> dict:
        """Get enhanced processor status"""
        uptime = datetime.now() - self.start_time
        return {
            'processor_type': 'enhanced_liquidation',
            'processed_liquidations': self.processed_liquidations,
            'alerts_sent': self.alerts_sent,
            'cascade_predictions': self.cascade_predictions,
            'symbols_tracked': len(self.liquidation_history),
            'uptime_seconds': uptime.total_seconds(),
            'processing_rate': self.processed_liquidations / uptime.total_seconds() if uptime.total_seconds() > 0 else 0,
            'alert_effectiveness': self.alerts_sent / max(1, self.processed_liquidations) * 100
        }


class LiquidationCascadeTracker:
    """Specialized tracker for liquidation cascade patterns"""
    
    def __init__(self):
        self.cascade_history: Dict[str, List] = {}  # symbol -> cascade events
        self.cascade_patterns = {
            'flash_cascade': {'duration': 30, 'min_liquidations': 5},      # 30s, 5+ liquidations
            'rolling_cascade': {'duration': 300, 'min_liquidations': 10},  # 5min, 10+ liquidations
            'death_spiral': {'duration': 900, 'min_liquidations': 20}      # 15min, 20+ liquidations
        }
    
    async def track_cascade_event(self, symbol: str, liquidations: List[dict]) -> Optional[str]:
        """Track and classify cascade events"""
        if len(liquidations) < 3:
            return None
        
        # Classify cascade type
        time_span = max(liq['timestamp'] for liq in liquidations) - min(liq['timestamp'] for liq in liquidations)
        duration_seconds = time_span.total_seconds()
        liquidation_count = len(liquidations)
        
        cascade_type = None
        if duration_seconds <= 30 and liquidation_count >= 5:
            cascade_type = 'flash_cascade'
        elif duration_seconds <= 300 and liquidation_count >= 10:
            cascade_type = 'rolling_cascade'
        elif duration_seconds <= 900 and liquidation_count >= 20:
            cascade_type = 'death_spiral'
        
        if cascade_type:
            # Record cascade event
            if symbol not in self.cascade_history:
                self.cascade_history[symbol] = []
            
            cascade_event = {
                'type': cascade_type,
                'liquidation_count': liquidation_count,
                'total_value': sum(liq['value_usd'] for liq in liquidations),
                'duration_seconds': duration_seconds,
                'timestamp': datetime.now(),
                'liquidations': liquidations
            }
            
            self.cascade_history[symbol].append(cascade_event)
            logger.info(f"Cascade detected: {symbol} - {cascade_type} ({liquidation_count} liquidations)")
            
            return cascade_type
        
        return None


class EnhancedLiquidationMonitor:
    """Enhanced liquidation monitor with real-time intelligence"""
    
    def __init__(self, bot_instance, market_data_url: str = "http://localhost:8001"):
        self.bot = bot_instance
        self.market_data_url = market_data_url
        
        # Initialize components
        self.threshold_engine = DynamicThresholdEngine(market_data_url=market_data_url)
        self.liquidation_processor = EnhancedLiquidationProcessor(bot_instance, self.threshold_engine)
        self.real_time_pipeline = RealTimeDataPipeline()
        
        # Add liquidation processor to pipeline
        self.real_time_pipeline.processors.append(self.liquidation_processor)
        
        self.running = False
        self.monitoring_task = None
        
        # Monitor major symbols by default
        self.monitored_symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT',
            'AVAXUSDT', 'MATICUSDT', 'LINKUSDT', 'UNIUSDT', 'AAVEUSDT'
        ]
    
    async def start_enhanced_monitoring(self):
        """Start enhanced liquidation monitoring with real-time pipeline"""
        if self.running:
            logger.info("Enhanced monitoring already running")
            return
        
        self.running = True
        logger.info("Starting enhanced liquidation monitoring...")
        
        try:
            # Start real-time data pipeline
            await self.real_time_pipeline.start_comprehensive_monitoring(self.monitored_symbols)
            
            logger.info(f"Enhanced liquidation monitoring started for {len(self.monitored_symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error starting enhanced monitoring: {e}")
            self.running = False
            raise
    
    async def stop_monitoring(self):
        """Stop enhanced monitoring"""
        if not self.running:
            return
        
        logger.info("Stopping enhanced liquidation monitoring...")
        self.running = False
        
        try:
            # Stop real-time pipeline
            await self.real_time_pipeline.stop_monitoring()
            
            # Close threshold engine
            await self.threshold_engine.close()
            
            logger.info("Enhanced liquidation monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping enhanced monitoring: {e}")
    
    async def get_comprehensive_status(self) -> dict:
        """Get comprehensive monitoring status"""
        pipeline_status = await self.real_time_pipeline.get_comprehensive_status()
        processor_status = await self.liquidation_processor.get_status()
        
        return {
            'enhanced_monitoring_running': self.running,
            'monitored_symbols': len(self.monitored_symbols),
            'symbol_list': self.monitored_symbols,
            'real_time_pipeline': pipeline_status,
            'liquidation_processor': processor_status,
            'threshold_engine_active': hasattr(self.threshold_engine, 'asset_cache'),
            'cache_size': len(getattr(self.threshold_engine, 'asset_cache', {}))
        }