"""
OI Monitor for Telegram Bot
Open Interest explosion detection integrated into the main bot
"""

import asyncio
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import aiohttp
import os
from dataclasses import dataclass


@dataclass
class OISnapshot:
    """Open Interest snapshot"""
    symbol: str
    exchange: str
    oi_usd: float
    timestamp: datetime


class OITracker:
    """Tracks OI changes and detects explosions"""
    
    def __init__(self):
        self.snapshots: Dict[str, List[OISnapshot]] = {}  # symbol -> snapshots
        self.thresholds = {
            'BTC': {'change_pct': 15.0, 'min_oi': 50_000_000},
            'ETH': {'change_pct': 18.0, 'min_oi': 25_000_000},
            'SOL': {'change_pct': 25.0, 'min_oi': 10_000_000},
            'default': {'change_pct': 30.0, 'min_oi': 5_000_000}
        }
        self.window_minutes = 15  # Detection window
        self.min_exchanges = 2    # Minimum exchanges for confirmation
    
    def add_snapshot(self, snapshot: OISnapshot) -> Optional[str]:
        """Add OI snapshot and check for explosions"""
        symbol_key = snapshot.symbol
        
        # Initialize if new symbol
        if symbol_key not in self.snapshots:
            self.snapshots[symbol_key] = []
        
        # Add snapshot
        self.snapshots[symbol_key].append(snapshot)
        
        # Keep only recent snapshots (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.snapshots[symbol_key] = [
            s for s in self.snapshots[symbol_key] if s.timestamp > cutoff_time
        ]
        
        # Check for explosion
        return self._check_explosion(symbol_key)
    
    def _check_explosion(self, symbol: str) -> Optional[str]:
        """Check for OI explosion"""
        snapshots = self.snapshots.get(symbol, [])
        if len(snapshots) < 2:
            return None
        
        # Get snapshots from detection window
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        recent_snapshots = [s for s in snapshots if s.timestamp >= window_start]
        if len(recent_snapshots) < 2:
            return None
        
        # Group by exchange
        exchange_data = {}
        for snapshot in recent_snapshots:
            if snapshot.exchange not in exchange_data:
                exchange_data[snapshot.exchange] = []
            exchange_data[snapshot.exchange].append(snapshot)
        
        # Check each exchange for significant change
        exploding_exchanges = []
        for exchange, ex_snapshots in exchange_data.items():
            if len(ex_snapshots) < 2:
                continue
            
            # Calculate change
            oldest = min(ex_snapshots, key=lambda x: x.timestamp)
            newest = max(ex_snapshots, key=lambda x: x.timestamp)
            
            if oldest.oi_usd > 0:
                change_pct = ((newest.oi_usd - oldest.oi_usd) / oldest.oi_usd) * 100
                
                # Get thresholds for this symbol
                symbol_base = symbol.replace('USDT', '').replace('USDC', '')
                thresholds = self.thresholds.get(symbol_base, self.thresholds['default'])
                
                if (abs(change_pct) >= thresholds['change_pct'] and 
                    newest.oi_usd >= thresholds['min_oi']):
                    exploding_exchanges.append({
                        'exchange': exchange,
                        'change_pct': change_pct,
                        'old_oi': oldest.oi_usd,
                        'new_oi': newest.oi_usd
                    })
        
        # Need confirmation from multiple exchanges
        if len(exploding_exchanges) >= self.min_exchanges:
            return self._format_explosion_alert(symbol, exploding_exchanges)
        
        return None
    
    def _format_explosion_alert(self, symbol: str, explosions: List[Dict]) -> str:
        """Format OI explosion alert"""
        avg_change = sum(e['change_pct'] for e in explosions) / len(explosions)
        total_oi = sum(e['new_oi'] for e in explosions)
        
        direction_emoji = "📈" if avg_change > 0 else "📉"
        direction_word = "EXPLOSION" if avg_change > 0 else "COLLAPSE"
        
        symbol_clean = symbol.replace('USDT', '').replace('USDC', '')
        
        message = (f"🚨 **{symbol_clean} OI {direction_word}**\n"
                  f"{direction_emoji} **{avg_change:+.1f}%** change in 15 minutes\n"
                  f"💰 **Total OI**: ${total_oi:,.0f}\n"
                  f"🏦 **{len(explosions)}/{len(explosions)} exchanges** confirming\n")
        
        if abs(avg_change) > 20:
            message += "⚡ **Institutional positioning detected**"
        else:
            message += "📊 **Significant position building activity**"
        
        return message


class OIMonitor:
    """OI explosion monitor for the telegram bot"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.tracker = OITracker()
        self.running = False
        self.monitoring_task = None
        self.logger = logging.getLogger(__name__)
        self.market_data_url = os.getenv('MARKET_DATA_URL', 'http://localhost:8001')
        self.session = None
        
        # Symbols to monitor
        self.symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'ADA-USDT', 'DOT-USDT']
        self.check_interval = 300  # 5 minutes
    
    async def start_monitoring(self):
        """Start OI monitoring"""
        if self.running:
            return
        
        self.running = True
        self.session = aiohttp.ClientSession()
        self.logger.info("Starting OI monitoring...")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop OI monitoring"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                for symbol in self.symbols:
                    if not self.running:
                        break
                    await self._check_symbol_oi(symbol)
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"OI monitoring error: {e}")
                await asyncio.sleep(60)  # Wait on error
    
    async def _check_symbol_oi(self, symbol: str):
        """Check OI for a specific symbol"""
        try:
            # Get OI data from market data service
            oi_data = await self._fetch_oi_data(symbol)
            if not oi_data:
                return
            
            # Create snapshots for each exchange
            timestamp = datetime.now()
            for exchange, data in oi_data.items():
                if isinstance(data, dict) and 'oi_usd' in data:
                    snapshot = OISnapshot(
                        symbol=symbol,
                        exchange=exchange,
                        oi_usd=float(data['oi_usd']),
                        timestamp=timestamp
                    )
                    
                    # Check for explosion
                    alert_message = self.tracker.add_snapshot(snapshot)
                    if alert_message:
                        await self._send_alert(alert_message)
                        
        except Exception as e:
            self.logger.error(f"Error checking OI for {symbol}: {e}")
    
    async def _fetch_oi_data(self, symbol: str) -> Optional[Dict]:
        """Fetch OI data from market data service"""
        try:
            if not self.session:
                return None
            
            async with self.session.post(
                f"{self.market_data_url}/multi_oi",
                json={'symbol': symbol},
                timeout=10
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        return result.get('data', {})
                        
        except Exception as e:
            self.logger.error(f"Error fetching OI data for {symbol}: {e}")
        
        return None
    
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
                self.logger.info("OI explosion alert sent")
        except Exception as e:
            self.logger.error(f"Error sending OI alert: {e}")
    
    def get_status(self) -> dict:
        """Get monitoring status"""
        return {
            'running': self.running,
            'symbols_monitored': len(self.symbols),
            'check_interval': self.check_interval,
            'total_snapshots': sum(len(snapshots) for snapshots in self.tracker.snapshots.values()),
            'thresholds': self.tracker.thresholds
        }