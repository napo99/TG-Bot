#!/usr/bin/env python3
"""
HYPERLIQUID LIQUIDATION PROVIDER - Production Grade with Enhanced Reliability
Monitors liquidations on Hyperliquid DEX via WebSocket trades stream
Enhanced with comprehensive error handling, retry logic, and health monitoring
Author: Opus 4.1
Date: October 25, 2025
"""

from __future__ import annotations

import asyncio
import json
import signal
import sys
import os
import time
import random
import traceback
from enum import Enum
from dataclasses import dataclass, field
import aiohttp
import websockets
from websockets.exceptions import WebSocketException, ConnectionClosedError, ConnectionClosedOK
from typing import Dict, List, Optional, Any, AsyncIterator, Set, Tuple, Union, Final
from datetime import datetime, timedelta
from loguru import logger
from functools import wraps
from contextlib import asynccontextmanager

# Add parent directories to path for shared models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.models.compact_liquidation import CompactLiquidation, LiquidationSide

# Configuration
LIQUIDATOR_ADDRESS: Final[str] = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"
MAX_RECONNECT_ATTEMPTS: Final[int] = 10
INITIAL_RECONNECT_DELAY: Final[float] = 1.0
MAX_RECONNECT_DELAY: Final[float] = 60.0
HEARTBEAT_INTERVAL: Final[int] = 30

class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    CLOSED = "closed"

@dataclass
class ConnectionHealth:
    """Connection health metrics"""
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_connected: Optional[datetime] = None
    last_disconnected: Optional[datetime] = None
    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_messages: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0
    last_message_time: Optional[datetime] = None

    def update_connected(self) -> None:
        """Update metrics on successful connection"""
        self.state = ConnectionState.CONNECTED
        self.last_connected = datetime.utcnow()
        self.successful_connections += 1
        self.connection_attempts += 1

    def update_disconnected(self, error: Optional[str] = None) -> None:
        """Update metrics on disconnection"""
        self.state = ConnectionState.DISCONNECTED
        self.last_disconnected = datetime.utcnow()
        if error:
            self.error_count += 1
            self.last_error = error
            self.failed_connections += 1
        if self.last_connected:
            self.uptime_seconds += (self.last_disconnected - self.last_connected).total_seconds()

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_exception = e
                    wait_time = min(backoff_factor ** attempt, 30)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Non-retryable error: {e}")
                    raise

            logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator

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

    def __init__(self,
                 symbols: Optional[List[str]] = None,
                 max_reconnect_attempts: int = MAX_RECONNECT_ATTEMPTS,
                 heartbeat_interval: int = HEARTBEAT_INTERVAL):
        """
        Initialize Hyperliquid liquidation provider with production features

        Args:
            symbols: List of symbols to monitor (e.g., ["BTC", "ETH", "SOL"])
                    If None, monitors all available symbols
            max_reconnect_attempts: Maximum reconnection attempts
            heartbeat_interval: Interval for heartbeat checks in seconds
        """
        self.exchange: str = "hyperliquid"
        self.api_base: str = "https://api.hyperliquid.xyz"
        self.ws_url: str = "wss://api.hyperliquid.xyz/ws"

        # Symbols to monitor (None = all)
        self.symbols: Optional[List[str]] = symbols
        self.monitored_coins: Optional[Set[str]] = set(symbols) if symbols else None

        # Connection management
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketClientProtocol] = None
        self.running: bool = False
        self._shutdown_event: asyncio.Event = asyncio.Event()

        # Enhanced connection management
        self.max_reconnect_attempts: int = max_reconnect_attempts
        self.heartbeat_interval: int = heartbeat_interval
        self.health: ConnectionHealth = ConnectionHealth()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_delay: float = INITIAL_RECONNECT_DELAY

        # Statistics
        self.liquidation_count: int = 0
        self.total_trade_count: int = 0
        self.connection_errors: int = 0
        self.start_time: float = time.time()

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

    async def _monitor_heartbeat(self) -> None:
        """Monitor connection heartbeat"""
        while self.running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if self.health.last_message_time:
                    time_since_last = (datetime.utcnow() - self.health.last_message_time).total_seconds()

                    if time_since_last > self.heartbeat_interval * 2:
                        logger.warning(f"No messages for {time_since_last:.1f}s - connection may be stale")

                        # Force reconnection
                        if self.ws_connection:
                            await self.ws_connection.close()

            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")

    def _get_reconnect_delay(self) -> float:
        """Calculate reconnection delay with exponential backoff and jitter"""
        delay = min(self._reconnect_delay, MAX_RECONNECT_DELAY)
        jitter = random.uniform(0, delay * 0.1)  # Add up to 10% jitter
        self._reconnect_delay = min(self._reconnect_delay * 2, MAX_RECONNECT_DELAY)
        return delay + jitter

    @retry_on_failure(max_retries=3)
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
        Connect to Hyperliquid WebSocket with enhanced error handling

        Returns:
            True if connection successful
        """
        try:
            self.health.state = ConnectionState.CONNECTING
            self.health.connection_attempts += 1

            # Add connection timeout
            self.ws_connection = await asyncio.wait_for(
                websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ),
                timeout=30
            )

            self.health.update_connected()
            self._reconnect_delay = INITIAL_RECONNECT_DELAY  # Reset delay on success
            logger.info(f"✅ Connected to Hyperliquid WebSocket")
            return True

        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            self.health.update_disconnected("Connection timeout")
            self.connection_errors += 1
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Hyperliquid WebSocket: {e}")
            self.health.update_disconnected(str(e))
            self.connection_errors += 1
            return False

    async def start_monitoring(self) -> AsyncIterator[CompactLiquidation]:
        """
        Start monitoring liquidations with enhanced reliability

        Yields:
            CompactLiquidation objects as they occur
        """
        self.running = True
        reconnect_attempts = 0

        # Start heartbeat monitor
        self._heartbeat_task = asyncio.create_task(self._monitor_heartbeat())

        while self.running and not self._shutdown_event.is_set() and reconnect_attempts < self.max_reconnect_attempts:
            try:
                # Connect to WebSocket
                if not await self.connect_websocket():
                    reconnect_attempts += 1
                    delay = self._get_reconnect_delay()
                    logger.warning(f"Retrying WebSocket connection in {delay:.1f}s (attempt {reconnect_attempts}/{self.max_reconnect_attempts})")
                    try:
                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=delay)
                        break  # Shutdown requested
                    except asyncio.TimeoutError:
                        continue

                # Connection successful, reset attempt counter
                reconnect_attempts = 0

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
                        self.health.total_messages += 1
                        self.health.last_message_time = datetime.utcnow()

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

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics"""
        uptime = time.time() - self.start_time
        return {
            "exchange": self.exchange,
            "liquidation_count": self.liquidation_count,
            "total_trade_count": self.total_trade_count,
            "connection_errors": self.connection_errors,
            "running": self.running,
            "symbols": list(self.monitored_coins) if self.monitored_coins else "ALL",
            "uptime_seconds": uptime,
            "health": {
                "state": self.health.state.value if isinstance(self.health.state, Enum) else self.health.state,
                "connection_attempts": self.health.connection_attempts,
                "successful_connections": self.health.successful_connections,
                "failed_connections": self.health.failed_connections,
                "total_messages": self.health.total_messages,
                "error_count": self.health.error_count,
                "last_error": self.health.last_error,
                "connection_uptime": self.health.uptime_seconds
            }
        }


# Export for unified aggregator
__all__ = ['HyperliquidLiquidationProvider']
