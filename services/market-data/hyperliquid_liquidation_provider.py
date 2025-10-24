#!/usr/bin/env python3
"""
HYPERLIQUID LIQUIDATION PROVIDER: Real-time liquidation tracking
Monitors liquidations on Hyperliquid DEX via WebSocket trades stream
"""

import asyncio
import json
import aiohttp
import websockets
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime
from loguru import logger

from shared.models.compact_liquidation import CompactLiquidation, LiquidationSide


class HyperliquidLiquidationProvider:
    """
    Hyperliquid Liquidation Provider for DEX perpetuals

    Key Features:
    - Real-time WebSocket monitoring of all trades
    - Filters liquidation events from trade stream
    - Blockchain-native liquidation tracking
    - Multi-asset support (BTC, ETH, SOL, etc.)

    Architecture:
    - Hyperliquid L1 blockchain records all trades on-chain
    - WebSocket 'trades' channel provides real-time trade events
    - Liquidations are marked in trade metadata
    """

    def __init__(self, symbols: Optional[List[str]] = None):
        """
        Initialize Hyperliquid liquidation provider

        Args:
            symbols: List of symbols to monitor (e.g., ["BTC", "ETH", "SOL"])
                    If None, monitors all available symbols
        """
        self.exchange = "hyperliquid"
        self.api_base = "https://api.hyperliquid.xyz"
        self.ws_url = "wss://api.hyperliquid.xyz/ws"

        # Symbols to monitor (None = all)
        self.symbols = symbols
        self.monitored_coins = set(symbols) if symbols else None

        # Connection management
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False

        # Statistics
        self.liquidation_count = 0
        self.total_trade_count = 0
        self.connection_errors = 0

        logger.info(f"🟣 Hyperliquid liquidation provider initialized")
        if self.symbols:
            logger.info(f"   Monitoring symbols: {', '.join(self.symbols)}")
        else:
            logger.info(f"   Monitoring: ALL symbols")

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def get_available_symbols(self) -> List[str]:
        """
        Get list of available trading symbols from Hyperliquid

        Returns:
            List of symbol names (e.g., ["BTC", "ETH", "SOL"])
        """
        try:
            session = await self.get_session()

            async with session.post(f"{self.api_base}/info",
                                  json={"type": "meta"}) as response:
                if response.status != 200:
                    logger.error(f"Hyperliquid meta API error: HTTP {response.status}")
                    return []

                data = await response.json()
                universe = data.get('universe', [])

                symbols = [asset.get('name') for asset in universe if asset.get('name')]
                logger.info(f"✅ Found {len(symbols)} symbols on Hyperliquid")

                return symbols

        except Exception as e:
            logger.error(f"❌ Error fetching Hyperliquid symbols: {e}")
            return []

    async def subscribe_to_trades(self, coin: str) -> None:
        """
        Subscribe to trades for a specific coin

        Args:
            coin: Symbol name (e.g., "BTC")
        """
        if not self.ws_connection:
            logger.error("WebSocket not connected")
            return

        try:
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "trades",
                    "coin": coin
                }
            }

            await self.ws_connection.send(json.dumps(subscribe_msg))
            logger.info(f"🟣 Subscribed to Hyperliquid {coin} trades")

        except Exception as e:
            logger.error(f"❌ Error subscribing to {coin} trades: {e}")

    async def subscribe_to_all_mids(self) -> None:
        """
        Subscribe to allMids (all mark prices)
        This helps us get price data for liquidation value calculation
        """
        if not self.ws_connection:
            logger.error("WebSocket not connected")
            return

        try:
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "allMids"
                }
            }

            await self.ws_connection.send(json.dumps(subscribe_msg))
            logger.info(f"🟣 Subscribed to Hyperliquid allMids")

        except Exception as e:
            logger.error(f"❌ Error subscribing to allMids: {e}")

    async def connect_websocket(self) -> bool:
        """
        Connect to Hyperliquid WebSocket

        Returns:
            True if connection successful
        """
        try:
            self.ws_connection = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10
            )

            logger.info(f"✅ Connected to Hyperliquid WebSocket")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to Hyperliquid WebSocket: {e}")
            self.connection_errors += 1
            return False

    async def start_monitoring(self) -> AsyncIterator[CompactLiquidation]:
        """
        Start monitoring liquidations

        Yields:
            CompactLiquidation objects as they occur
        """
        self.running = True

        while self.running:
            try:
                # Connect to WebSocket
                if not await self.connect_websocket():
                    logger.warning("Retrying WebSocket connection in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                # Subscribe to allMids for price data
                await self.subscribe_to_all_mids()

                # Get available symbols if not specified
                if self.monitored_coins is None:
                    symbols = await self.get_available_symbols()
                    # Default to major coins if we can't get full list
                    self.monitored_coins = set(symbols) if symbols else {"BTC", "ETH", "SOL"}

                # Subscribe to trades for each symbol
                for coin in self.monitored_coins:
                    await self.subscribe_to_trades(coin)
                    await asyncio.sleep(0.1)  # Rate limiting

                # Process messages
                async for message in self.ws_connection:
                    try:
                        data = json.loads(message)

                        # Process trade data
                        if self._is_trade_message(data):
                            liquidation = await self._process_trade_message(data)
                            if liquidation:
                                self.liquidation_count += 1
                                yield liquidation

                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON decode error: {e}")
                    except Exception as e:
                        logger.error(f"❌ Error processing message: {e}")
                        continue

            except websockets.exceptions.ConnectionClosed:
                logger.warning("🟣 WebSocket connection closed, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Hyperliquid monitor error: {e}")
                self.connection_errors += 1
                await asyncio.sleep(10)
            finally:
                if self.ws_connection:
                    await self.ws_connection.close()
                    self.ws_connection = None

    def _is_trade_message(self, data: dict) -> bool:
        """
        Check if message is a trade event

        Args:
            data: WebSocket message data

        Returns:
            True if this is a trade message
        """
        # Hyperliquid trade message format:
        # {
        #   "channel": "trades",
        #   "data": [...]
        # }
        return data.get('channel') == 'trades'

    async def _process_trade_message(self, data: dict) -> Optional[CompactLiquidation]:
        """
        Process trade message and extract liquidation if present

        Hyperliquid Trade Format:
        {
            "channel": "trades",
            "data": [
                {
                    "coin": "BTC",
                    "side": "B",  # B=Buy, A=Sell
                    "px": "45000.5",
                    "sz": "0.5",
                    "time": 1702000000000,
                    "hash": "0x...",
                    "tid": 12345678,
                    "liquidation": true  # Only present if this is a liquidation
                }
            ]
        }

        Args:
            data: WebSocket message data

        Returns:
            CompactLiquidation if this is a liquidation, None otherwise
        """
        try:
            trades = data.get('data', [])

            for trade in trades:
                self.total_trade_count += 1

                # Check if this trade is a liquidation
                is_liquidation = trade.get('liquidation', False)

                if not is_liquidation:
                    continue

                # Extract trade data
                coin = trade.get('coin', '')
                side_str = trade.get('side', '')  # "B" or "A"
                price = float(trade.get('px', 0))
                size = float(trade.get('sz', 0))
                timestamp_ms = int(trade.get('time', 0))

                # Validate data
                if not coin or price <= 0 or size <= 0:
                    logger.warning(f"Invalid liquidation data: {trade}")
                    continue

                # Convert to CompactLiquidation
                return CompactLiquidation.from_hyperliquid_data(trade)

            return None

        except Exception as e:
            logger.error(f"❌ Error processing Hyperliquid trade: {e}")
            return None

    async def stop_monitoring(self) -> None:
        """Stop monitoring liquidations"""
        self.running = False

        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None

        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

        logger.info(f"🟣 Hyperliquid liquidation monitor stopped")
        logger.info(f"   Total trades: {self.total_trade_count}")
        logger.info(f"   Liquidations: {self.liquidation_count}")

    def get_stats(self) -> dict:
        """Get monitoring statistics"""
        return {
            "exchange": self.exchange,
            "liquidation_count": self.liquidation_count,
            "total_trade_count": self.total_trade_count,
            "connection_errors": self.connection_errors,
            "running": self.running,
            "symbols": list(self.monitored_coins) if self.monitored_coins else "ALL"
        }


# Export for unified aggregator
__all__ = ['HyperliquidLiquidationProvider']
