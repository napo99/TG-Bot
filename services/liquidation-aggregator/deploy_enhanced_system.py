#!/usr/bin/env python3
"""
Enhanced Liquidation System - Production Deployment Script
Orchestrates the complete enhanced liquidation cascade detection system

Usage:
    python deploy_enhanced_system.py --mode production
    python deploy_enhanced_system.py --mode test
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from typing import Optional

# Add parent directory to path for shared models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import all agent components
from enhanced_websocket_manager import EnhancedWebSocketManager
from advanced_velocity_engine import AdvancedVelocityEngine
from cascade_risk_calculator import CascadeRiskCalculator
from cascade_signal_generator import CascadeSignalGenerator
from market_regime_detector import MarketRegimeDetector

import redis.asyncio as redis


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('deployment')


class EnhancedLiquidationSystem:
    """
    Complete enhanced liquidation system integrating all agent components
    """

    def __init__(
        self,
        symbols: list[str],
        exchanges: list[str],
        redis_url: str = "redis://localhost:6380/0"
    ):
        self.symbols = symbols
        self.exchanges = exchanges
        self.redis_url = redis_url

        # Components (initialized in setup)
        self.websocket_manager: Optional[EnhancedWebSocketManager] = None
        self.velocity_engine: Optional[AdvancedVelocityEngine] = None
        self.risk_calculator: Optional[CascadeRiskCalculator] = None
        self.signal_generator: Optional[CascadeSignalGenerator] = None
        self.regime_detector: Optional[MarketRegimeDetector] = None
        self.redis_client: Optional[redis.Redis] = None

        self.running = False
        logger.info(f"Initialized Enhanced Liquidation System")
        logger.info(f"  Symbols: {symbols}")
        logger.info(f"  Exchanges: {exchanges}")

    async def setup(self):
        """Initialize all components"""
        logger.info("Setting up components...")

        # Initialize Redis
        self.redis_client = await redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info("✅ Redis connection established")

        # Initialize Agent 2 components
        self.velocity_engine = AdvancedVelocityEngine()
        self.risk_calculator = CascadeRiskCalculator()
        logger.info("✅ Velocity Engine and Risk Calculator initialized")

        # Initialize Agent 3 components
        self.signal_generator = CascadeSignalGenerator(redis_client=self.redis_client)
        self.regime_detector = MarketRegimeDetector()
        logger.info("✅ Signal Generator and Regime Detector initialized")

        # Initialize Agent 1 WebSocket Manager with integrated callback
        # Note: EnhancedWebSocketManager uses redis_host/port/db, not redis_url
        self.websocket_manager = EnhancedWebSocketManager(
            symbols=self.symbols,
            redis_host='localhost',
            redis_port=6380,
            redis_db=0
        )
        self.websocket_manager.user_callback = self.process_liquidation

        # Add exchanges
        for exchange in self.exchanges:
            if exchange.lower() in ['binance', 'bybit', 'okx']:
                self.websocket_manager.add_cex_exchange(exchange.lower())
            elif exchange.lower() == 'hyperliquid':
                # Extract base symbols for Hyperliquid
                base_symbols = [s.replace('USDT', '').replace('USDC', '') for s in self.symbols]
                self.websocket_manager.add_dex_hyperliquid(list(set(base_symbols)))

        logger.info("✅ WebSocket Manager configured")
        logger.info("Setup complete!")

    async def process_liquidation(self, event):
        """
        Integrated liquidation processing pipeline
        Connects all agent components
        """
        try:
            symbol = event.symbol

            # Handle different event types (CEX vs DEX)
            if hasattr(event, 'exchange_name'):
                exchange = event.exchange_name  # LiquidationEvent from CEX
            else:
                exchange = event.exchange  # CompactLiquidation from DEX

            # Get USD value based on event type
            if hasattr(event, 'actual_value_usd'):
                value_usd = event.actual_value_usd  # CompactLiquidation
            else:
                value_usd = event.value_usd  # LiquidationEvent

            # Agent 2: Update velocity engine
            self.velocity_engine.add_event(symbol, value_usd, exchange)

            # Agent 2: Calculate velocity metrics
            metrics = self.velocity_engine.calculate_multi_timeframe_velocity(symbol)

            # Agent 2: Calculate risk
            risk_assessment = self.risk_calculator.calculate_risk(metrics)

            # Agent 3: Update regime detector (using BTC price from Redis)
            btc_price_data = await self.redis_client.get('btc:price:current')
            if btc_price_data:
                import json
                btc_data = json.loads(btc_price_data)
                btc_price = btc_data.get('price', 40000)
                volume = value_usd
                self.regime_detector.update(btc_price, volume)

            # Agent 3: Generate cascade signal
            signal = await self.signal_generator.generate_signal(symbol)

            # Log important events
            if signal and signal.signal.value >= 3:  # CRITICAL or EXTREME
                logger.warning(
                    f"🚨 CASCADE DETECTED - {symbol}\n"
                    f"   Level: {signal.signal.name}\n"
                    f"   Probability: {signal.probability:.2%}\n"
                    f"   Velocity: {metrics.velocity_10s:.2f} events/s\n"
                    f"   Acceleration: {metrics.acceleration:.2f} events/s²\n"
                    f"   Risk Level: {risk_assessment.risk_level.name}\n"
                    f"   Regime: {self.regime_detector.current_regime.market_regime.name}"
                )

        except Exception as e:
            logger.error(f"Error processing liquidation: {e}", exc_info=True)

    async def start(self):
        """Start the enhanced liquidation system"""
        logger.info("🚀 Starting Enhanced Liquidation System...")

        self.running = True

        # Start WebSocket manager (includes BTC price feed)
        await self.websocket_manager.start_all()

    async def stop(self):
        """Gracefully stop the system"""
        logger.info("🛑 Stopping Enhanced Liquidation System...")

        self.running = False

        # Stop WebSocket manager
        if self.websocket_manager:
            await self.websocket_manager.stop_all()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ System stopped gracefully")

    async def health_check(self):
        """Perform system health check"""
        health = {
            'websocket_manager': self.websocket_manager is not None,
            'velocity_engine': self.velocity_engine is not None,
            'signal_generator': self.signal_generator is not None,
            'redis': False
        }

        # Check Redis
        try:
            await self.redis_client.ping()
            health['redis'] = True
        except:
            pass

        logger.info(f"Health Check: {health}")
        return all(health.values())


async def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description='Deploy Enhanced Liquidation System')
    parser.add_argument(
        '--mode',
        choices=['production', 'test', 'development'],
        default='development',
        help='Deployment mode'
    )
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['BTCUSDT', 'ETHUSDT'],
        help='Symbols to track'
    )
    parser.add_argument(
        '--exchanges',
        nargs='+',
        default=['binance', 'bybit', 'okx'],
        help='Exchanges to monitor'
    )
    parser.add_argument(
        '--redis-url',
        default='redis://localhost:6380/0',
        help='Redis URL'
    )

    args = parser.parse_args()

    # Configure based on mode
    if args.mode == 'production':
        logging.getLogger().setLevel(logging.WARNING)
        logger.info("🔴 PRODUCTION MODE")
    elif args.mode == 'test':
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🔵 TEST MODE")
    else:
        logger.info("🟢 DEVELOPMENT MODE")

    # Create system
    system = EnhancedLiquidationSystem(
        symbols=args.symbols,
        exchanges=args.exchanges,
        redis_url=args.redis_url
    )

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(system.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Setup and start
        await system.setup()

        # Health check
        if not await system.health_check():
            logger.error("❌ Health check failed, aborting")
            sys.exit(1)

        logger.info("✅ All systems operational")

        # Start the system
        await system.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await system.stop()


if __name__ == "__main__":
    """
    Usage examples:

    # Development mode (default)
    python deploy_enhanced_system.py

    # Production mode with custom symbols
    python deploy_enhanced_system.py --mode production --symbols BTCUSDT ETHUSDT SOLUSDT

    # Test mode with all exchanges
    python deploy_enhanced_system.py --mode test --exchanges binance bybit okx hyperliquid

    # Custom Redis URL
    python deploy_enhanced_system.py --redis-url redis://production:6380/0
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Deployment terminated by user")
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        sys.exit(1)