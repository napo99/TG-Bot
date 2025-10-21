"""
Real-Time Data Pipeline - Phase 2 Implementation  
Enhanced WebSocket streams for institutional-grade trading intelligence
Part of the Institutional Trading Intelligence System
"""

import asyncio
import websockets
import json
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import deque
import aiohttp
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class TradeEvent:
    """Real-time trade data structure"""
    symbol: str
    price: float
    quantity: float
    value_usd: float
    side: str  # 'BUY' or 'SELL'
    is_whale: bool
    timestamp: datetime
    exchange: str
    trade_id: str


@dataclass  
class OrderBookSnapshot:
    """Order book pressure data"""
    symbol: str
    bid_volume_usd: float
    ask_volume_usd: float
    bid_ask_ratio: float
    spread_bps: float
    best_bid: float
    best_ask: float
    timestamp: datetime


@dataclass
class LiquidationEvent:
    """Enhanced liquidation event"""
    symbol: str
    side: str
    price: float
    quantity: float
    value_usd: float
    timestamp: datetime
    exchange: str
    estimated_leverage: Optional[float] = None
    cascade_potential: Optional[str] = None  # 'LOW', 'MEDIUM', 'HIGH'


class StreamProcessor(ABC):
    """Abstract base class for stream processors"""
    
    @abstractmethod
    async def process_trade(self, trade: TradeEvent):
        """Process a trade event"""
        pass
    
    @abstractmethod
    async def process_liquidation(self, liquidation: LiquidationEvent):
        """Process a liquidation event"""
        pass
    
    @abstractmethod
    async def get_status(self) -> dict:
        """Get processor status"""
        pass


class VolumeIntelligenceProcessor(StreamProcessor):
    """Real-time volume and delta intelligence processor"""
    
    def __init__(self, intelligence_engine=None):
        self.intelligence_engine = intelligence_engine
        self.volume_windows: Dict[str, Dict] = {}  # symbol -> time windows
        self.delta_accumulators: Dict[str, Dict] = {}  # symbol -> delta tracking
        self.whale_tracker = WhaleActivityTracker()
        
        # Time windows for analysis
        self.time_windows = {
            '1m': timedelta(minutes=1),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1)
        }
        
        self.processed_count = 0
        self.start_time = datetime.now()
    
    async def process_trade(self, trade: TradeEvent):
        """Process individual trade for volume/delta intelligence"""
        try:
            symbol = trade.symbol
            
            # Initialize tracking for new symbols
            if symbol not in self.volume_windows:
                self._initialize_symbol_tracking(symbol)
            
            # Update volume tracking across all timeframes
            await self._update_volume_tracking(symbol, trade)
            
            # Update real-time delta tracking
            await self._update_delta_tracking(symbol, trade)
            
            # Track whale activity
            if trade.is_whale:
                await self.whale_tracker.process_whale_trade(trade)
            
            # Check for volume spikes and alerts
            await self._check_volume_alerts(symbol)
            
            self.processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing trade for {trade.symbol}: {e}")
    
    async def process_liquidation(self, liquidation: LiquidationEvent):
        """Process liquidation events"""
        # Volume intelligence doesn't directly process liquidations
        # but can use them for context
        pass
    
    def _initialize_symbol_tracking(self, symbol: str):
        """Initialize tracking structures for a new symbol"""
        self.volume_windows[symbol] = {}
        for window_name, duration in self.time_windows.items():
            self.volume_windows[symbol][window_name] = {
                'trades': deque(maxlen=10000),
                'duration': duration,
                'last_volume': 0,
                'baseline_volume': 0
            }
        
        self.delta_accumulators[symbol] = {
            'running_delta': 0.0,
            'last_reset': datetime.now(),
            'delta_history': deque(maxlen=1000),
            'session_delta': 0.0
        }
    
    async def _update_volume_tracking(self, symbol: str, trade: TradeEvent):
        """Update rolling volume windows"""
        windows = self.volume_windows[symbol]
        
        for window_name, window_data in windows.items():
            # Add trade to window
            window_data['trades'].append({
                'value_usd': trade.value_usd,
                'timestamp': trade.timestamp,
                'is_whale': trade.is_whale,
                'side': trade.side,
                'price': trade.price,
                'quantity': trade.quantity
            })
            
            # Remove old trades outside window
            cutoff_time = datetime.now() - window_data['duration']
            window_data['trades'] = deque([
                t for t in window_data['trades'] 
                if t['timestamp'] > cutoff_time
            ], maxlen=10000)
            
            # Update current volume
            window_data['last_volume'] = sum(
                t['value_usd'] for t in window_data['trades']
            )
    
    async def _update_delta_tracking(self, symbol: str, trade: TradeEvent):
        """Update real-time cumulative delta"""
        accumulator = self.delta_accumulators[symbol]
        
        # Calculate trade delta (positive for buy pressure, negative for sell)
        trade_delta = trade.value_usd if trade.side == 'BUY' else -trade.value_usd
        
        # Update running delta
        accumulator['running_delta'] += trade_delta
        accumulator['session_delta'] += trade_delta
        accumulator['delta_history'].append({
            'delta': trade_delta,
            'timestamp': trade.timestamp,
            'cumulative': accumulator['running_delta'],
            'price': trade.price
        })
        
        # Reset session delta at session boundaries (every 8 hours)
        if self._should_reset_session_delta(accumulator['last_reset']):
            accumulator['session_delta'] = 0.0
            accumulator['last_reset'] = datetime.now()
    
    async def _check_volume_alerts(self, symbol: str):
        """Check if volume spike thresholds are exceeded"""
        try:
            if not self.intelligence_engine:
                return
            
            # Get dynamic thresholds
            thresholds = await self.intelligence_engine.calculate_volume_threshold(symbol)
            windows = self.volume_windows[symbol]
            
            # Check 15-minute window for spikes
            window_15m = windows.get('15m')
            if not window_15m or len(window_15m['trades']) < 10:
                return
            
            current_volume = window_15m['last_volume']
            baseline_volume = await self._get_baseline_volume(symbol, '15m')
            
            if baseline_volume > 0:
                spike_multiplier = current_volume / baseline_volume
                
                # Determine alert level
                if spike_multiplier >= thresholds.extreme_threshold:
                    alert_type = 'EXTREME'
                elif spike_multiplier >= thresholds.high_threshold:
                    alert_type = 'HIGH'
                elif spike_multiplier >= thresholds.moderate_threshold:
                    alert_type = 'MODERATE'
                else:
                    return  # No alert needed
                
                # Create volume spike alert
                alert_data = {
                    'type': 'volume_spike',
                    'symbol': symbol,
                    'alert_level': alert_type,
                    'spike_multiplier': spike_multiplier,
                    'current_volume_usd': current_volume,
                    'baseline_volume_usd': baseline_volume,
                    'timeframe': '15m',
                    'timestamp': datetime.now(),
                    'dominant_side': self._calculate_dominant_side(window_15m['trades']),
                    'whale_participation': self._calculate_whale_participation(window_15m['trades'])
                }
                
                # Send alert through intelligence engine
                if hasattr(self.intelligence_engine, 'send_alert'):
                    await self.intelligence_engine.send_alert(alert_data)
                    
        except Exception as e:
            logger.error(f"Error checking volume alerts for {symbol}: {e}")
    
    def _calculate_dominant_side(self, trades: deque) -> str:
        """Calculate dominant trading side"""
        if not trades:
            return 'NEUTRAL'
        
        buy_volume = sum(t['value_usd'] for t in trades if t['side'] == 'BUY')
        total_volume = sum(t['value_usd'] for t in trades)
        
        if total_volume == 0:
            return 'NEUTRAL'
        
        buy_ratio = buy_volume / total_volume
        if buy_ratio > 0.6:
            return 'BUY_PRESSURE'
        elif buy_ratio < 0.4:
            return 'SELL_PRESSURE'
        else:
            return 'BALANCED'
    
    def _calculate_whale_participation(self, trades: deque) -> float:
        """Calculate whale participation percentage"""
        if not trades:
            return 0.0
        
        whale_volume = sum(t['value_usd'] for t in trades if t.get('is_whale', False))
        total_volume = sum(t['value_usd'] for t in trades)
        
        return whale_volume / total_volume if total_volume > 0 else 0.0
    
    async def _get_baseline_volume(self, symbol: str, timeframe: str) -> float:
        """Get baseline volume for comparison (7-day average)"""
        # For now, use simple estimation - in production this would query historical data
        current_window = self.volume_windows[symbol].get(timeframe)
        if not current_window:
            return 0.0
        
        # Rough baseline estimation (would be replaced with historical data)
        recent_volume = current_window['last_volume']
        return recent_volume * 0.4  # Assume current is 250% of baseline
    
    def _should_reset_session_delta(self, last_reset: datetime) -> bool:
        """Check if session delta should be reset"""
        hours_elapsed = (datetime.now() - last_reset).total_seconds() / 3600
        return hours_elapsed >= 8  # Reset every 8 hours
    
    async def get_status(self) -> dict:
        """Get processor status"""
        uptime = datetime.now() - self.start_time
        return {
            'processor_type': 'volume_intelligence',
            'symbols_tracked': len(self.volume_windows),
            'trades_processed': self.processed_count,
            'uptime_seconds': uptime.total_seconds(),
            'processing_rate': self.processed_count / uptime.total_seconds() if uptime.total_seconds() > 0 else 0
        }


class WhaleActivityTracker:
    """Track whale trading activity and patterns"""
    
    def __init__(self):
        self.whale_trades: Dict[str, deque] = {}  # symbol -> whale trades
        self.whale_summary: Dict[str, Dict] = {}  # symbol -> summary stats
    
    async def process_whale_trade(self, trade: TradeEvent):
        """Process a whale trade"""
        symbol = trade.symbol
        
        if symbol not in self.whale_trades:
            self.whale_trades[symbol] = deque(maxlen=100)  # Keep last 100 whale trades
            self.whale_summary[symbol] = {
                'total_volume_24h': 0.0,
                'buy_volume_24h': 0.0,
                'sell_volume_24h': 0.0,
                'trade_count_24h': 0,
                'largest_trade_24h': 0.0,
                'last_update': datetime.now()
            }
        
        # Add trade to history
        self.whale_trades[symbol].append({
            'value_usd': trade.value_usd,
            'side': trade.side,
            'price': trade.price,
            'timestamp': trade.timestamp
        })
        
        # Update summary stats
        await self._update_whale_summary(symbol)
    
    async def _update_whale_summary(self, symbol: str):
        """Update 24h whale summary for a symbol"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_trades = [
            trade for trade in self.whale_trades[symbol]
            if trade['timestamp'] > cutoff_time
        ]
        
        if not recent_trades:
            return
        
        summary = self.whale_summary[symbol]
        summary['total_volume_24h'] = sum(t['value_usd'] for t in recent_trades)
        summary['buy_volume_24h'] = sum(t['value_usd'] for t in recent_trades if t['side'] == 'BUY')
        summary['sell_volume_24h'] = sum(t['value_usd'] for t in recent_trades if t['side'] == 'SELL')
        summary['trade_count_24h'] = len(recent_trades)
        summary['largest_trade_24h'] = max(t['value_usd'] for t in recent_trades)
        summary['last_update'] = datetime.now()


class RealTimeDataPipeline:
    """Manages multiple WebSocket streams for real-time intelligence"""
    
    def __init__(self, intelligence_engine=None):
        self.intelligence_engine = intelligence_engine
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.processors: List[StreamProcessor] = []
        self.volume_processor = VolumeIntelligenceProcessor(intelligence_engine)
        
        # Add processors
        self.processors.append(self.volume_processor)
        
        # Stream configurations
        self.stream_configs = {
            'binance_trades': 'wss://fstream.binance.com/ws/!ticker@arr',
            'binance_liquidations': 'wss://fstream.binance.com/ws/!forceOrder@arr',
            'binance_bookTicker': 'wss://fstream.binance.com/ws/!bookTicker'
        }
        
        self.running = False
        self.reconnect_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.max_reconnect_delay = 60
    
    async def start_comprehensive_monitoring(self, symbols: List[str]):
        """Start all real-time streams for given symbols"""
        logger.info(f"Starting comprehensive monitoring for {len(symbols)} symbols")
        self.running = True
        
        tasks = []
        
        # Start individual symbol streams
        for symbol in symbols:
            # Trade stream for volume/delta analysis
            task = asyncio.create_task(self._start_trade_stream(symbol))
            self.active_streams[f"{symbol}_trades"] = task
            tasks.append(task)
        
        # Global streams (all symbols)
        # Liquidation stream
        task = asyncio.create_task(self._start_liquidation_stream())
        self.active_streams['liquidations'] = task
        tasks.append(task)
        
        # Book ticker stream for order book analysis
        task = asyncio.create_task(self._start_book_ticker_stream())
        self.active_streams['book_ticker'] = task
        tasks.append(task)
        
        logger.info(f"Started {len(tasks)} real-time streams")
        
        # Don't await - let streams run in background
        return tasks
    
    async def stop_monitoring(self):
        """Stop all monitoring streams"""
        logger.info("Stopping real-time monitoring")
        self.running = False
        
        # Cancel all active streams
        for stream_name, task in self.active_streams.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Stopped stream: {stream_name}")
                except Exception as e:
                    logger.error(f"Error stopping stream {stream_name}: {e}")
        
        self.active_streams.clear()
    
    async def _start_trade_stream(self, symbol: str):
        """WebSocket stream for individual symbol trades"""
        stream_name = f"{symbol.lower()}@trade"
        url = f"wss://fstream.binance.com/ws/{stream_name}"
        
        retry_count = 0
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as websocket:
                    logger.info(f"Connected to trade stream: {symbol}")
                    retry_count = 0  # Reset on successful connection
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._process_trade_message(data)
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error processing trade message for {symbol}: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Trade stream connection closed: {symbol}")
            except Exception as e:
                logger.error(f"Trade stream error for {symbol}: {e}")
            
            # Reconnect with exponential backoff
            if self.running:
                delay = min(self.reconnect_delays[min(retry_count, len(self.reconnect_delays)-1)], 
                          self.max_reconnect_delay)
                logger.info(f"Reconnecting trade stream for {symbol} in {delay}s...")
                await asyncio.sleep(delay)
                retry_count += 1
    
    async def _start_liquidation_stream(self):
        """WebSocket stream for liquidations"""
        url = "wss://fstream.binance.com/ws/!forceOrder@arr"
        
        retry_count = 0
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as websocket:
                    logger.info("Connected to liquidation stream")
                    retry_count = 0
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._process_liquidation_message(data)
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error processing liquidation message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Liquidation stream connection closed")
            except Exception as e:
                logger.error(f"Liquidation stream error: {e}")
            
            if self.running:
                delay = min(self.reconnect_delays[min(retry_count, len(self.reconnect_delays)-1)], 
                          self.max_reconnect_delay)
                logger.info(f"Reconnecting liquidation stream in {delay}s...")
                await asyncio.sleep(delay)
                retry_count += 1
    
    async def _start_book_ticker_stream(self):
        """WebSocket stream for order book tickers"""
        url = "wss://fstream.binance.com/ws/!bookTicker"
        
        retry_count = 0
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as websocket:
                    logger.info("Connected to book ticker stream")
                    retry_count = 0
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._process_book_ticker_message(data)
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error processing book ticker message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Book ticker stream connection closed")
            except Exception as e:
                logger.error(f"Book ticker stream error: {e}")
            
            if self.running:
                delay = min(self.reconnect_delays[min(retry_count, len(self.reconnect_delays)-1)], 
                          self.max_reconnect_delay)
                logger.info(f"Reconnecting book ticker stream in {delay}s...")
                await asyncio.sleep(delay)
                retry_count += 1
    
    async def _process_trade_message(self, data: dict):
        """Process individual trade message"""
        try:
            # Binance trade stream format
            symbol = data.get('s', '')
            price = float(data.get('p', 0))
            quantity = float(data.get('q', 0))
            timestamp_ms = int(data.get('T', 0))
            is_buyer_maker = data.get('m', False)
            
            # Calculate trade details
            value_usd = price * quantity
            side = 'SELL' if is_buyer_maker else 'BUY'  # Buyer maker = sell pressure
            is_whale = value_usd > 500000  # >$500k = whale trade
            
            # Create trade event
            trade_event = TradeEvent(
                symbol=symbol,
                price=price,
                quantity=quantity,
                value_usd=value_usd,
                side=side,
                is_whale=is_whale,
                timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                exchange='binance',
                trade_id=data.get('t', '')
            )
            
            # Process through all processors
            for processor in self.processors:
                await processor.process_trade(trade_event)
                
        except Exception as e:
            logger.error(f"Error processing trade message: {e}")
    
    async def _process_liquidation_message(self, data: dict):
        """Process liquidation message"""
        try:
            order = data.get('o', {})
            if not order:
                return
            
            symbol = order.get('s', '')
            side_str = order.get('S', '')  # SELL = long liquidation
            price = float(order.get('ap', 0))
            quantity = float(order.get('z', 0))
            timestamp_ms = int(order.get('T', 0))
            
            # Convert side (Binance uses opposite logic)
            side = 'LONG' if side_str == 'SELL' else 'SHORT'
            value_usd = price * quantity
            
            # Create liquidation event
            liquidation_event = LiquidationEvent(
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                value_usd=value_usd,
                timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                exchange='binance'
            )
            
            # Process through all processors
            for processor in self.processors:
                await processor.process_liquidation(liquidation_event)
                
        except Exception as e:
            logger.error(f"Error processing liquidation message: {e}")
    
    async def _process_book_ticker_message(self, data: dict):
        """Process book ticker message for order book analysis"""
        try:
            symbol = data.get('s', '')
            best_bid = float(data.get('b', 0))
            best_ask = float(data.get('a', 0))
            bid_qty = float(data.get('B', 0))
            ask_qty = float(data.get('A', 0))
            
            if best_bid > 0 and best_ask > 0:
                # Calculate order book metrics
                mid_price = (best_bid + best_ask) / 2
                spread_bps = ((best_ask - best_bid) / mid_price) * 10000
                
                bid_volume_usd = best_bid * bid_qty
                ask_volume_usd = best_ask * ask_qty
                
                bid_ask_ratio = bid_volume_usd / ask_volume_usd if ask_volume_usd > 0 else 0
                
                # Create order book snapshot
                ob_snapshot = OrderBookSnapshot(
                    symbol=symbol,
                    bid_volume_usd=bid_volume_usd,
                    ask_volume_usd=ask_volume_usd,
                    bid_ask_ratio=bid_ask_ratio,
                    spread_bps=spread_bps,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    timestamp=datetime.now()
                )
                
                # Process order book data (could add order book processor later)
                # For now, just log significant imbalances
                if bid_ask_ratio > 3.0 or bid_ask_ratio < 0.33:
                    logger.info(f"Order book imbalance {symbol}: Bid/Ask ratio {bid_ask_ratio:.2f}")
                    
        except Exception as e:
            logger.error(f"Error processing book ticker message: {e}")
    
    async def get_comprehensive_status(self) -> dict:
        """Get comprehensive status of all streams and processors"""
        processor_status = []
        for processor in self.processors:
            status = await processor.get_status()
            processor_status.append(status)
        
        return {
            'pipeline_running': self.running,
            'active_streams': len(self.active_streams),
            'stream_names': list(self.active_streams.keys()),
            'processors': processor_status,
            'total_symbols_monitored': len([s for s in self.active_streams.keys() if '_trades' in s])
        }