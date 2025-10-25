#!/usr/bin/env python3
"""
HYPERLIQUID LIQUIDATION PROVIDER: Real-time liquidation tracking
Monitors liquidations on Hyperliquid DEX via WebSocket trades stream
"""

import asyncio
import json
import signal
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
        self._shutdown_event = asyncio.Event()

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

        while self.running and not self._shutdown_event.is_set():
            try:
                # Connect to WebSocket
                if not await self.connect_websocket():
                    logger.warning("Retrying WebSocket connection in 5 seconds...")
                    try:
                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=5.0)
                        break  # Shutdown requested
                    except asyncio.TimeoutError:
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
                    if self._shutdown_event.is_set():
                        break
                    await self.subscribe_to_trades(coin)
                    await asyncio.sleep(0.1)  # Rate limiting

                # Process messages
                async for message in self.ws_connection:
                    if self._shutdown_event.is_set():
                        break

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
                if not self._shutdown_event.is_set():
                    logger.warning("🟣 WebSocket connection closed, reconnecting...")
                    try:
                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=5.0)
                        break
                    except asyncio.TimeoutError:
                        continue
            except asyncio.CancelledError:
                logger.info("🟣 Monitoring task cancelled, shutting down gracefully...")
                break
            except Exception as e:
                if not self._shutdown_event.is_set():
                    logger.error(f"❌ Hyperliquid monitor error: {e}")
                    self.connection_errors += 1
                    try:
                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=10.0)
                        break
                    except asyncio.TimeoutError:
                        continue
            finally:
                await self._cleanup_connection()

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
                    "users": ["0x...", "0x..."]  # [buyer, seller]
                }
            ]
        }

        Liquidation Detection:
        A trade is a liquidation if HLP Liquidator address is involved:
        0x2e3d94f0562703b25c83308a05046ddaf9a8dd14

        Args:
            data: WebSocket message data

        Returns:
            CompactLiquidation if this is a liquidation, None otherwise
        """
        # HLP Liquidator address (official Hyperliquid liquidation bot)
        LIQUIDATOR_ADDRESS = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"

        try:
            trades = data.get('data', [])

            for trade in trades:
                self.total_trade_count += 1

                # Check if this trade involves the liquidator
                users = trade.get('users', [])
                if not users or len(users) < 2:
                    continue

                buyer = users[0].lower()
                seller = users[1].lower()
                liquidator = LIQUIDATOR_ADDRESS.lower()

                # Determine if it's a liquidation and which side
                liquidation_side = None
                liquidated_user = None

                if buyer == liquidator:
                    # HLP is buying = closing a short position = SHORT liquidation
                    liquidation_side = LiquidationSide.SHORT
                    liquidated_user = users[1]  # The seller being liquidated
                elif seller == liquidator:
                    # HLP is selling = closing a long position = LONG liquidation
                    liquidation_side = LiquidationSide.LONG
                    liquidated_user = users[0]  # The buyer being liquidated
                else:
                    # Not a liquidation
                    continue

                # Extract trade data
                coin = trade.get('coin', '')
                price = float(trade.get('px', 0))
                size = float(trade.get('sz', 0))
                timestamp_ms = int(trade.get('time', 0))

                # Validate data
                if not coin or price <= 0 or size <= 0:
                    logger.warning(f"Invalid liquidation data: {trade}")
                    continue

                # Add the liquidation side and liquidated user to trade data
                trade['liquidation_side'] = liquidation_side
                trade['liquidated_user'] = liquidated_user

                # Log the liquidation detection
                logger.debug(f"💥 Liquidation detected: {coin} {liquidation_side.name} "
                           f"${price * size:.2f} (user: {liquidated_user[:8]}...)")

                # Convert to CompactLiquidation with correct side
                return CompactLiquidation.from_hyperliquid_data(trade, liquidation_side)

            return None

        except Exception as e:
            logger.error(f"❌ Error processing Hyperliquid trade: {e}")
            return None

    async def _cleanup_connection(self) -> None:
        """Clean up WebSocket and HTTP connections"""
        try:
            if self.ws_connection:
                try:
                    # Close WebSocket gracefully with timeout
                    await asyncio.wait_for(self.ws_connection.close(), timeout=2.0)
                except asyncio.TimeoutError:
                    logger.warning("WebSocket close timeout, forcing closure")
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
                finally:
                    self.ws_connection = None
        except Exception as e:
            logger.warning(f"Error in WebSocket cleanup: {e}")

    async def stop_monitoring(self) -> None:
        """Stop monitoring liquidations"""
        logger.info("🟣 Stopping Hyperliquid liquidation monitor...")

        self.running = False
        self._shutdown_event.set()

        # Clean up connections
        await self._cleanup_connection()

        if self.session and not self.session.closed:
            try:
                await asyncio.wait_for(self.session.close(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("HTTP session close timeout")
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self.session = None

        logger.info(f"✅ Hyperliquid liquidation monitor stopped")
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
