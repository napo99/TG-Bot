"""
EXCHANGE WEBSOCKET INTEGRATIONS
Binance + Bybit liquidation stream normalizers
"""

import json
import logging
import asyncio
from typing import Optional, Callable, Any
from datetime import datetime

import websockets

from cex_engine import LiquidationEvent, Exchange, Side, TRACKED_SYMBOLS


# =============================================================================
# BINANCE INTEGRATION
# =============================================================================

class BinanceLiquidationStream:
    """
    Binance liquidation WebSocket stream
    URL: wss://fstream.binance.com/ws/!forceOrder@arr
    """

    def __init__(self, callback: Callable[[LiquidationEvent], None]):
        self.callback = callback
        self.url = "wss://fstream.binance.com/ws/!forceOrder@arr"
        self.running = False
        self.websocket = None
        self.reconnect_delays = [1, 2, 4, 8, 16]
        self.logger = logging.getLogger('binance')

    def normalize_event(self, data: dict) -> Optional[LiquidationEvent]:
        """
        Normalize Binance liquidation data

        Binance format:
        {
            "e": "forceOrder",
            "E": 1568014460893,
            "o": {
                "s": "BTCUSDT",
                "S": "SELL",  # SELL = long liquidation
                "o": "LIMIT",
                "f": "IOC",
                "q": "0.014",
                "p": "9910",
                "ap": "9910",  # Average price
                "X": "FILLED",
                "l": "0.014",
                "z": "0.014",  # Filled quantity
                "T": 1568014460893
            }
        }
        """
        try:
            order = data.get('o', {})
            if not order:
                return None

            symbol = order.get('s', '')
            if symbol not in TRACKED_SYMBOLS:
                return None

            # Extract data
            side_str = order.get('S', '')  # SELL or BUY
            price = float(order.get('ap', 0))  # Average price
            quantity = float(order.get('z', 0))  # Filled quantity
            timestamp_ms = int(order.get('T', 0))

            # Calculate USD value
            value_usd = price * quantity

            # Convert side (Binance uses opposite logic)
            # SELL order = LONG liquidation (seller forced to sell their long)
            # BUY order = SHORT liquidation (buyer forced to cover their short)
            side = Side.LONG if side_str == 'SELL' else Side.SHORT

            return LiquidationEvent(
                timestamp_ms=timestamp_ms,
                exchange=Exchange.BINANCE,
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                value_usd=value_usd
            )

        except Exception as e:
            self.logger.error(f"Error normalizing Binance event: {e}")
            return None

    async def start(self):
        """Start WebSocket connection with auto-reconnect"""
        self.running = True
        attempt = 0

        while self.running:
            try:
                self.logger.info(f"Connecting to Binance liquidation stream...")

                async with websockets.connect(self.url) as websocket:
                    self.websocket = websocket
                    self.logger.info("✅ Connected to Binance liquidation stream")
                    attempt = 0  # Reset reconnect delay on successful connection

                    async for message in websocket:
                        if not self.running:
                            break

                        try:
                            data = json.loads(message)
                            event = self.normalize_event(data)

                            if event:
                                await self.callback(event)

                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            self.logger.error(f"Error processing Binance message: {e}")

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Binance WebSocket connection closed")
            except Exception as e:
                self.logger.error(f"Binance WebSocket error: {e}")

            # Reconnect with exponential backoff
            if self.running:
                delay = self.reconnect_delays[min(attempt, len(self.reconnect_delays) - 1)]
                self.logger.info(f"Reconnecting to Binance in {delay}s...")
                await asyncio.sleep(delay)
                attempt += 1

    async def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.logger.info("Binance WebSocket connection closed")


# =============================================================================
# BYBIT INTEGRATION
# =============================================================================

class BybitLiquidationStream:
    """
    Bybit liquidation WebSocket stream
    URL: wss://stream.bybit.com/v5/public/linear

    NOTE: Bybit requires subscription per symbol
    """

    def __init__(self, callback: Callable[[LiquidationEvent], None]):
        self.callback = callback
        self.url = "wss://stream.bybit.com/v5/public/linear"
        self.running = False
        self.websocket = None
        self.reconnect_delays = [1, 2, 4, 8, 16]
        self.logger = logging.getLogger('bybit')

    def normalize_event(self, data: dict) -> Optional[list[LiquidationEvent]]:
        """
        Normalize Bybit liquidation data

        Bybit format:
        {
            "topic": "liquidation.BTCUSDT",
            "type": "snapshot",
            "ts": 1672304486868,
            "data": {
                "updatedTime": 1672304486868,
                "symbol": "BTCUSDT",
                "side": "Buy",  # Buy = SHORT liquidation
                "size": "0.01",
                "price": "16493.50"
            }
        }
        """
        try:
            topic = data.get('topic', '')
            if not topic.startswith('liquidation.'):
                return None

            liq_data = data.get('data', {})
            if not liq_data:
                return None

            symbol = liq_data.get('symbol', '')
            if symbol not in TRACKED_SYMBOLS:
                return None

            # Extract data
            side_str = liq_data.get('side', '')  # Buy or Sell
            price = float(liq_data.get('price', 0))
            size = float(liq_data.get('size', 0))  # Quantity
            timestamp_ms = int(liq_data.get('updatedTime', 0))

            # Calculate USD value
            value_usd = price * size

            # Convert side (Bybit logic)
            # Buy order = SHORT liquidation (forced buy to close short)
            # Sell order = LONG liquidation (forced sell to close long)
            side = Side.SHORT if side_str == 'Buy' else Side.LONG

            event = LiquidationEvent(
                timestamp_ms=timestamp_ms,
                exchange=Exchange.BYBIT,
                symbol=symbol,
                side=side,
                price=price,
                quantity=size,
                value_usd=value_usd
            )

            return [event]

        except Exception as e:
            self.logger.error(f"Error normalizing Bybit event: {e}")
            return None

    async def subscribe_symbols(self, websocket):
        """Subscribe to liquidation streams for tracked symbols"""
        for symbol in TRACKED_SYMBOLS:
            subscription = {
                "op": "subscribe",
                "args": [f"liquidation.{symbol}"]
            }
            await websocket.send(json.dumps(subscription))
            self.logger.info(f"Subscribed to Bybit liquidations for {symbol}")

    async def start(self):
        """Start WebSocket connection with auto-reconnect"""
        self.running = True
        attempt = 0

        while self.running:
            try:
                self.logger.info(f"Connecting to Bybit liquidation stream...")

                async with websockets.connect(self.url) as websocket:
                    self.websocket = websocket
                    self.logger.info("✅ Connected to Bybit liquidation stream")
                    attempt = 0  # Reset reconnect delay

                    # Subscribe to symbols
                    await self.subscribe_symbols(websocket)

                    async for message in websocket:
                        if not self.running:
                            break

                        try:
                            data = json.loads(message)

                            # Skip subscription responses
                            if data.get('op') == 'subscribe':
                                continue

                            events = self.normalize_event(data)

                            if events:
                                for event in events:
                                    await self.callback(event)

                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            self.logger.error(f"Error processing Bybit message: {e}")

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Bybit WebSocket connection closed")
            except Exception as e:
                self.logger.error(f"Bybit WebSocket error: {e}")

            # Reconnect with exponential backoff
            if self.running:
                delay = self.reconnect_delays[min(attempt, len(self.reconnect_delays) - 1)]
                self.logger.info(f"Reconnecting to Bybit in {delay}s...")
                await asyncio.sleep(delay)
                attempt += 1

    async def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.logger.info("Bybit WebSocket connection closed")


# =============================================================================
# OKX INTEGRATION
# =============================================================================

class OKXLiquidationStream:
    """
    OKX liquidation WebSocket stream
    URL: wss://ws.okx.com:8443/ws/v5/public

    NOTE: OKX provides liquidation-orders channel with SWAP data
    """

    def __init__(self, callback: Callable[[LiquidationEvent], None]):
        self.callback = callback
        self.url = "wss://ws.okx.com:8443/ws/v5/public"
        self.running = False
        self.websocket = None
        self.reconnect_delays = [1, 2, 4, 8, 16]
        self.logger = logging.getLogger('okx')
        self.last_ping = 0
        self.ping_interval = 20  # Ping every 20 seconds (OKX idle timeout is 30s)

    def normalize_event(self, data: dict) -> Optional[list[LiquidationEvent]]:
        """
        Normalize OKX liquidation data

        OKX format:
        {
            "arg": {
                "channel": "liquidation-orders",
                "instType": "SWAP"
            },
            "data": [
                {
                    "instId": "BTC-USDT-SWAP",
                    "instType": "SWAP",
                    "instFamily": "BTC-USDT",
                    "uly": "BTC-USDT",
                    "details": [
                        {
                            "posSide": "long",  # Position side: long/short
                            "side": "sell",      # Liquidation side: sell (for long), buy (for short)
                            "bkPx": "67234.50",  # Bankruptcy price
                            "sz": "2.5",         # Size/quantity
                            "bkLoss": "0",       # Bankruptcy loss
                            "ccy": "",           # Currency
                            "ts": "1729512000000" # Timestamp in milliseconds
                        }
                    ]
                }
            ]
        }
        """
        try:
            # Check if it's liquidation data
            arg = data.get('arg', {})
            if arg.get('channel') != 'liquidation-orders':
                return None

            data_list = data.get('data', [])
            if not data_list:
                return None

            events = []

            for item in data_list:
                inst_id = item.get('instId', '')

                # Convert OKX symbol format to our standard format
                # OKX: "BTC-USDT-SWAP" -> Our format: "BTCUSDT"
                symbol = inst_id.replace('-SWAP', '').replace('-', '')

                if symbol not in TRACKED_SYMBOLS:
                    continue

                details = item.get('details', [])
                for detail in details:
                    # Extract data
                    pos_side = detail.get('posSide', '')  # long or short
                    price = float(detail.get('bkPx', 0))  # Bankruptcy price
                    quantity = float(detail.get('sz', 0))  # Size
                    timestamp_ms = int(detail.get('ts', 0))

                    # Calculate USD value
                    value_usd = price * quantity

                    # Convert side (OKX logic matches position side)
                    # posSide="long" means LONG liquidation (forced to close long position)
                    # posSide="short" means SHORT liquidation (forced to close short position)
                    side = Side.LONG if pos_side == 'long' else Side.SHORT

                    event = LiquidationEvent(
                        timestamp_ms=timestamp_ms,
                        exchange=Exchange.OKX,
                        symbol=symbol,
                        side=side,
                        price=price,
                        quantity=quantity,
                        value_usd=value_usd
                    )

                    events.append(event)

            return events if events else None

        except Exception as e:
            self.logger.error(f"Error normalizing OKX event: {e}")
            return None

    async def send_ping(self, websocket):
        """Send ping to keep connection alive"""
        try:
            await websocket.send("ping")
            self.logger.debug("Sent ping to OKX")
        except Exception as e:
            self.logger.error(f"Error sending ping: {e}")

    async def start(self):
        """Start WebSocket connection with auto-reconnect"""
        self.running = True
        attempt = 0

        while self.running:
            try:
                self.logger.info(f"Connecting to OKX liquidation stream...")

                async with websockets.connect(self.url) as websocket:
                    self.websocket = websocket
                    self.logger.info("✅ Connected to OKX liquidation stream")
                    attempt = 0  # Reset reconnect delay

                    # Subscribe to liquidation orders
                    subscription = {
                        "op": "subscribe",
                        "args": [{
                            "channel": "liquidation-orders",
                            "instType": "SWAP"
                        }]
                    }
                    await websocket.send(json.dumps(subscription))
                    self.logger.info("Subscribed to OKX liquidation orders (SWAP)")

                    self.last_ping = asyncio.get_event_loop().time()

                    async for message in websocket:
                        if not self.running:
                            break

                        # Handle pong responses
                        if message == "pong":
                            self.logger.debug("Received pong from OKX")
                            continue

                        # Send ping if needed
                        current_time = asyncio.get_event_loop().time()
                        if current_time - self.last_ping > self.ping_interval:
                            await self.send_ping(websocket)
                            self.last_ping = current_time

                        try:
                            data = json.loads(message)

                            # Skip subscription confirmation
                            if data.get('event') == 'subscribe':
                                self.logger.info(f"✅ OKX subscription confirmed: {data}")
                                continue

                            # Process liquidation data
                            events = self.normalize_event(data)

                            if events:
                                for event in events:
                                    await self.callback(event)

                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            self.logger.error(f"Error processing OKX message: {e}")

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("OKX WebSocket connection closed")
            except Exception as e:
                self.logger.error(f"OKX WebSocket error: {e}")

            # Reconnect with exponential backoff
            if self.running:
                delay = self.reconnect_delays[min(attempt, len(self.reconnect_delays) - 1)]
                self.logger.info(f"Reconnecting to OKX in {delay}s...")
                await asyncio.sleep(delay)
                attempt += 1

    async def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.logger.info("OKX WebSocket connection closed")


# =============================================================================
# MULTI-EXCHANGE AGGREGATOR
# =============================================================================

class MultiExchangeLiquidationAggregator:
    """
    Aggregate liquidations from multiple exchanges simultaneously
    Runs each exchange stream concurrently
    """

    def __init__(self, callback: Callable[[LiquidationEvent], None]):
        self.callback = callback
        self.streams = []
        self.logger = logging.getLogger('aggregator')

    def add_exchange(self, exchange: str):
        """Add exchange stream"""
        if exchange.lower() == 'binance':
            stream = BinanceLiquidationStream(self.callback)
            self.streams.append(stream)
            self.logger.info(f"Added Binance stream")
        elif exchange.lower() == 'bybit':
            stream = BybitLiquidationStream(self.callback)
            self.streams.append(stream)
            self.logger.info(f"Added Bybit stream")
        elif exchange.lower() == 'okx':
            stream = OKXLiquidationStream(self.callback)
            self.streams.append(stream)
            self.logger.info(f"Added OKX stream")
        else:
            self.logger.warning(f"Unknown exchange: {exchange}")

    async def start_all(self):
        """Start all exchange streams concurrently"""
        if not self.streams:
            self.logger.error("No exchange streams configured!")
            return

        self.logger.info(f"Starting {len(self.streams)} exchange streams...")

        # Run all streams concurrently with error isolation
        tasks = [asyncio.create_task(stream.start()) for stream in self.streams]

        # Use gather with return_exceptions=True to prevent one failure from killing all
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_all(self):
        """Stop all exchange streams"""
        self.logger.info("Stopping all exchange streams...")

        for stream in self.streams:
            await stream.stop()

        self.logger.info("All exchange streams stopped")


if __name__ == "__main__":
    # Test Binance normalizer
    test_binance_data = {
        "e": "forceOrder",
        "E": 1729512000000,
        "o": {
            "s": "BTCUSDT",
            "S": "SELL",
            "o": "LIMIT",
            "f": "IOC",
            "q": "2.5",
            "p": "67234.50",
            "ap": "67234.50",
            "X": "FILLED",
            "l": "2.5",
            "z": "2.5",
            "T": 1729512000000
        }
    }

    binance_stream = BinanceLiquidationStream(lambda e: print(f"Binance: {e}"))
    event = binance_stream.normalize_event(test_binance_data)
    print(f"Normalized Binance event: {event}")
    print(f"Event dict: {event.to_dict()}")
