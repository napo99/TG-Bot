"""
Multi-Exchange Liquidation Monitor
Orchestrates liquidation tracking across multiple exchanges (Binance, Hyperliquid, etc.)
"""

import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from liquidation_monitor import LiquidationTracker, Liquidation
from services.market_data.hyperliquid_liquidation_provider import HyperliquidLiquidationProvider
from shared.models.compact_liquidation import CompactLiquidation


class MultiExchangeLiquidationMonitor:
    """
    Multi-exchange liquidation monitoring system

    Features:
    - Monitors liquidations from multiple exchanges simultaneously
    - Unified alert system across all exchanges
    - Shared liquidation tracker for cascade detection across exchanges
    - Health monitoring per exchange
    """

    def __init__(self, bot_instance, market_data_url: str = "http://localhost:8001",
                 enabled_exchanges: Optional[List[str]] = None):
        """
        Initialize multi-exchange monitor

        Args:
            bot_instance: Telegram bot instance
            market_data_url: Market data service URL
            enabled_exchanges: List of exchanges to monitor (default: ["binance", "hyperliquid"])
        """
        self.bot = bot_instance
        self.tracker = LiquidationTracker(market_data_url)
        self.logger = logging.getLogger(__name__)

        # Exchange configuration
        self.enabled_exchanges = enabled_exchanges or self._get_enabled_exchanges_from_env()

        # Exchange providers
        self.providers: Dict[str, any] = {}
        self.exchange_tasks: Dict[str, asyncio.Task] = {}
        self.exchange_stats: Dict[str, dict] = {}

        # State management
        self.running = False
        self.start_time = None

        # Initialize providers
        self._initialize_providers()

        self.logger.info(f"🌐 Multi-exchange liquidation monitor initialized")
        self.logger.info(f"   Enabled exchanges: {', '.join(self.enabled_exchanges)}")

    def _get_enabled_exchanges_from_env(self) -> List[str]:
        """Get enabled exchanges from environment variables"""
        enabled = os.getenv('LIQUIDATION_EXCHANGES', 'binance,hyperliquid')
        return [ex.strip().lower() for ex in enabled.split(',')]

    def _initialize_providers(self):
        """Initialize liquidation providers for each exchange"""
        # Hyperliquid provider
        if 'hyperliquid' in self.enabled_exchanges:
            symbols = self._get_hyperliquid_symbols()
            self.providers['hyperliquid'] = HyperliquidLiquidationProvider(symbols=symbols)
            self.exchange_stats['hyperliquid'] = {
                'status': 'initialized',
                'liquidations_processed': 0,
                'errors': 0,
                'last_liquidation': None
            }
            self.logger.info(f"   ✅ Hyperliquid provider initialized")

        # Binance is handled separately via existing WebSocket in LiquidationMonitor
        # We keep it separate for backward compatibility
        if 'binance' in self.enabled_exchanges:
            self.exchange_stats['binance'] = {
                'status': 'enabled',
                'liquidations_processed': 0,
                'errors': 0,
                'last_liquidation': None
            }
            self.logger.info(f"   ✅ Binance provider enabled (via legacy monitor)")

    def _get_hyperliquid_symbols(self) -> Optional[List[str]]:
        """Get symbols to monitor on Hyperliquid from environment"""
        symbols_env = os.getenv('HYPERLIQUID_SYMBOLS', '')
        if symbols_env:
            return [s.strip().upper() for s in symbols_env.split(',')]
        # Default to major symbols
        return ["BTC", "ETH", "SOL"]

    async def start_monitoring(self):
        """Start monitoring all enabled exchanges"""
        if self.running:
            self.logger.warning("Monitor already running")
            return

        self.running = True
        self.start_time = datetime.now()
        self.logger.info("🚀 Starting multi-exchange liquidation monitoring...")

        # Start monitoring tasks for each exchange
        tasks = []

        # Hyperliquid monitoring
        if 'hyperliquid' in self.enabled_exchanges and 'hyperliquid' in self.providers:
            task = asyncio.create_task(self._monitor_hyperliquid())
            self.exchange_tasks['hyperliquid'] = task
            tasks.append(task)

        # Note: Binance monitoring is handled by the existing LiquidationMonitor
        # in the main bot for backward compatibility

        # Wait for all tasks
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"Error in monitoring tasks: {e}")
        finally:
            self.running = False

    async def _monitor_hyperliquid(self):
        """Monitor Hyperliquid liquidations"""
        provider = self.providers.get('hyperliquid')
        if not provider:
            return

        self.logger.info("🟣 Starting Hyperliquid liquidation monitoring...")
        self.exchange_stats['hyperliquid']['status'] = 'running'

        try:
            async for compact_liq in provider.start_monitoring():
                if not self.running:
                    break

                # Convert CompactLiquidation to Liquidation for the tracker
                liquidation = self._compact_to_liquidation(compact_liq, 'hyperliquid')

                # Update stats
                self.exchange_stats['hyperliquid']['liquidations_processed'] += 1
                self.exchange_stats['hyperliquid']['last_liquidation'] = datetime.now()

                # Process through tracker
                alert_message = await self.tracker.add_liquidation(liquidation)

                if alert_message:
                    # Add exchange identifier to alert
                    alert_with_exchange = f"🟣 **HYPERLIQUID**\n\n{alert_message}"
                    await self._send_alert(alert_with_exchange)

        except Exception as e:
            self.logger.error(f"❌ Hyperliquid monitoring error: {e}")
            self.exchange_stats['hyperliquid']['errors'] += 1
            self.exchange_stats['hyperliquid']['status'] = 'error'
        finally:
            if provider:
                await provider.stop_monitoring()
            self.exchange_stats['hyperliquid']['status'] = 'stopped'

    def _compact_to_liquidation(self, compact: CompactLiquidation, exchange: str) -> Liquidation:
        """
        Convert CompactLiquidation to Liquidation object

        Args:
            compact: CompactLiquidation object
            exchange: Exchange name

        Returns:
            Liquidation object
        """
        # Reconstruct symbol from hash (we use a simple approach here)
        # In production, you might want to maintain a hash->symbol mapping
        symbol = f"UNKNOWN-{compact.symbol_hash}"

        # For Hyperliquid, we can extract the symbol from the side_str
        # This is a simplified approach - in production, maintain proper mapping
        if exchange == 'hyperliquid':
            # Hyperliquid symbols are like "BTC-PERP", "ETH-PERP"
            # We'll use the symbol hash as a temporary identifier
            symbol = f"ASSET-PERP"  # Placeholder

        return Liquidation(
            symbol=symbol,
            side=compact.side_str,
            price=compact.actual_price,
            quantity=compact.actual_quantity,
            value_usd=compact.actual_value_usd,
            timestamp=datetime.fromtimestamp(compact.timestamp)
        )

    async def _send_alert(self, message: str):
        """Send alert to Telegram chat"""
        try:
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if chat_id and hasattr(self.bot, 'application'):
                await self.bot.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                self.logger.info(f"📨 Liquidation alert sent")
        except Exception as e:
            self.logger.error(f"❌ Error sending alert: {e}")

    def stop_monitoring(self):
        """Stop monitoring all exchanges"""
        self.logger.info("🛑 Stopping multi-exchange liquidation monitoring...")
        self.running = False

        # Cancel all exchange tasks
        for exchange, task in self.exchange_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"   Cancelled {exchange} monitoring task")

        # Stop providers
        for exchange, provider in self.providers.items():
            if hasattr(provider, 'stop_monitoring'):
                asyncio.create_task(provider.stop_monitoring())

    def get_status(self) -> dict:
        """Get comprehensive monitoring status"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        return {
            'running': self.running,
            'uptime_seconds': uptime,
            'enabled_exchanges': self.enabled_exchanges,
            'exchange_stats': self.exchange_stats,
            'tracker_status': self.tracker.get_performance_status(),
            'total_liquidations': sum(
                stats['liquidations_processed']
                for stats in self.exchange_stats.values()
            ),
            'total_errors': sum(
                stats['errors']
                for stats in self.exchange_stats.values()
            )
        }

    def get_exchange_stats(self, exchange: str) -> Optional[dict]:
        """Get statistics for a specific exchange"""
        if exchange in self.providers:
            provider_stats = self.providers[exchange].get_stats()
            return {
                **self.exchange_stats.get(exchange, {}),
                'provider_stats': provider_stats
            }
        return self.exchange_stats.get(exchange)


__all__ = ['MultiExchangeLiquidationMonitor']
