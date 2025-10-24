#!/usr/bin/env python3
"""
HYPERLIQUID BLOCKCHAIN LIQUIDATION TRACKER
Monitors ALL liquidations on Hyperliquid L1 blockchain by parsing on-chain trade data

Architecture:
- Queries blockchain blocks and transactions
- Identifies liquidations by HLP Liquidator address presence
- Aggregates liquidations across ALL users
- Provides real-time monitoring and historical queries
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger


# HLP Liquidator address - official Hyperliquid liquidation contract
HLP_LIQUIDATOR_ADDRESS = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"


@dataclass
class BlockchainLiquidation:
    """
    Liquidation event parsed from blockchain
    """
    # Transaction info
    tx_hash: str
    block_height: int
    timestamp: int  # Unix timestamp in ms

    # Trade info
    coin: str  # e.g. "BTC", "ETH"
    side: str  # "B" (buy) or "A" (sell/ask)
    price: float
    size: float
    value_usd: float

    # User info
    liquidated_user: str  # Address of user being liquidated
    liquidator: str  # HLP_LIQUIDATOR_ADDRESS

    # Liquidation details (from extra_fields if available)
    closed_pnl: Optional[float] = None
    leverage: Optional[float] = None

    @property
    def liquidation_side(self) -> str:
        """
        Determine if this was a long or short liquidation

        If HLP Liquidator is buying (side="B"), they're closing a short position
        If HLP Liquidator is selling (side="A"), they're closing a long position
        """
        return "SHORT" if self.side == "B" else "LONG"


class HyperliquidBlockchainLiquidationTracker:
    """
    Tracks ALL liquidations on Hyperliquid blockchain

    Methods:
    1. Explorer API: Query recent trades
    2. Block polling: Monitor new blocks for liquidations
    3. Historical scan: Scan past blocks for liquidations
    """

    def __init__(self, api_base: str = "https://api.hyperliquid.xyz"):
        self.api_base = api_base
        self.session: Optional[aiohttp.ClientSession] = None

        # Tracking state
        self.last_processed_block = 0
        self.liquidations: List[BlockchainLiquidation] = []

        # Statistics
        self.total_liquidations = 0
        self.total_value_usd = 0.0
        self.liquidations_by_coin: Dict[str, int] = {}
        self.liquidations_by_user: Dict[str, int] = {}

        logger.info(f"🔗 Hyperliquid Blockchain Liquidation Tracker initialized")
        logger.info(f"   HLP Liquidator: {HLP_LIQUIDATOR_ADDRESS}")

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def query_recent_trades(self, coin: str, limit: int = 2000) -> List[dict]:
        """
        Query recent trades for a coin using Info API

        Args:
            coin: Symbol (e.g., "BTC", "ETH")
            limit: Maximum trades to return

        Returns:
            List of trade dicts from recentTrades endpoint
        """
        try:
            session = await self.get_session()

            payload = {
                "type": "recentTrades",
                "coin": coin
            }

            async with session.post(f"{self.api_base}/info", json=payload) as response:
                if response.status != 200:
                    logger.error(f"API error: HTTP {response.status}")
                    return []

                trades = await response.json()
                return trades if isinstance(trades, list) else []

        except Exception as e:
            logger.error(f"Error querying recent trades for {coin}: {e}")
            return []

    async def query_block_details(self, block_height: int) -> Optional[dict]:
        """
        Query details for a specific block

        Args:
            block_height: Block number to query

        Returns:
            Block details dict including transactions
        """
        try:
            session = await self.get_session()

            payload = {
                "type": "blockDetails",
                "height": block_height
            }

            # Note: Explorer API endpoint (not /info)
            async with session.post(f"{self.api_base}/explorer", json=payload) as response:
                if response.status != 200:
                    logger.warning(f"Block {block_height} query failed: HTTP {response.status}")
                    return None

                return await response.json()

        except Exception as e:
            logger.error(f"Error querying block {block_height}: {e}")
            return None

    def is_liquidation_trade(self, trade: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if a trade is a liquidation

        Args:
            trade: Trade dict with buyer/seller info

        Returns:
            (is_liquidation, liquidated_user_address)
        """
        # Trade structure from WebSocket/recentTrades:
        # {
        #   "coin": "BTC",
        #   "side": "B" or "A",
        #   "px": "45000.5",
        #   "sz": "0.5",
        #   "time": 1702000000000,
        #   "hash": "0x...",
        #   "tid": 12345,
        #   "users": ["0xbuyer...", "0xseller..."]
        # }

        users = trade.get('users', [])
        if len(users) != 2:
            return False, None

        buyer, seller = users[0].lower(), users[1].lower()
        liquidator_addr = HLP_LIQUIDATOR_ADDRESS.lower()

        if buyer == liquidator_addr:
            # HLP Liquidator is buying = closing short position = short liquidation
            return True, seller  # Seller is the liquidated user
        elif seller == liquidator_addr:
            # HLP Liquidator is selling = closing long position = long liquidation
            return True, buyer  # Buyer is the liquidated user

        return False, None

    def parse_liquidation(self, trade: dict, extra_fields: Optional[dict] = None) -> BlockchainLiquidation:
        """
        Parse a trade dict into a BlockchainLiquidation object

        Args:
            trade: Trade dict from API
            extra_fields: Optional extra_fields JSON with PnL/liquidation details

        Returns:
            BlockchainLiquidation object
        """
        is_liq, liquidated_user = self.is_liquidation_trade(trade)

        if not is_liq:
            raise ValueError("Trade is not a liquidation")

        # Extract trade data
        coin = trade.get('coin', 'UNKNOWN')
        side = trade.get('side', '')
        price = float(trade.get('px', 0))
        size = float(trade.get('sz', 0))
        timestamp = int(trade.get('time', 0))
        tx_hash = trade.get('hash', '')

        value_usd = price * size

        # Parse extra_fields if available
        closed_pnl = None
        if extra_fields:
            # extra_fields structure:
            # {
            #   "buyer": {"closed_pnl": "123.45", "liquidation": {...}},
            #   "seller": {"closed_pnl": "-456.78", "liquidation": {...}}
            # }
            buyer_data = extra_fields.get('buyer', {})
            seller_data = extra_fields.get('seller', {})

            # Get PnL for the liquidated user
            users = trade.get('users', [])
            if len(users) == 2:
                buyer_addr, seller_addr = users[0].lower(), users[1].lower()

                if buyer_addr == liquidated_user.lower():
                    closed_pnl_str = buyer_data.get('closed_pnl')
                elif seller_addr == liquidated_user.lower():
                    closed_pnl_str = seller_data.get('closed_pnl')
                else:
                    closed_pnl_str = None

                if closed_pnl_str:
                    try:
                        closed_pnl = float(closed_pnl_str)
                    except:
                        pass

        return BlockchainLiquidation(
            tx_hash=tx_hash,
            block_height=0,  # Will be set if known
            timestamp=timestamp,
            coin=coin,
            side=side,
            price=price,
            size=size,
            value_usd=value_usd,
            liquidated_user=liquidated_user,
            liquidator=HLP_LIQUIDATOR_ADDRESS,
            closed_pnl=closed_pnl
        )

    async def scan_recent_liquidations(self, coins: List[str] = None) -> List[BlockchainLiquidation]:
        """
        Scan recent trades for liquidations across specified coins

        Args:
            coins: List of coins to scan (default: BTC, ETH, SOL)

        Returns:
            List of BlockchainLiquidation objects
        """
        if coins is None:
            coins = ["BTC", "ETH", "SOL"]

        logger.info(f"🔍 Scanning recent liquidations for {len(coins)} coins...")

        all_liquidations = []

        for coin in coins:
            try:
                trades = await self.query_recent_trades(coin)
                logger.info(f"   {coin}: Found {len(trades)} recent trades")

                for trade in trades:
                    is_liq, _ = self.is_liquidation_trade(trade)

                    if is_liq:
                        try:
                            liquidation = self.parse_liquidation(trade)
                            all_liquidations.append(liquidation)

                            # Update statistics
                            self.total_liquidations += 1
                            self.total_value_usd += liquidation.value_usd
                            self.liquidations_by_coin[coin] = self.liquidations_by_coin.get(coin, 0) + 1
                            self.liquidations_by_user[liquidation.liquidated_user] = \
                                self.liquidations_by_user.get(liquidation.liquidated_user, 0) + 1

                        except Exception as e:
                            logger.error(f"Error parsing liquidation: {e}")

            except Exception as e:
                logger.error(f"Error scanning {coin}: {e}")
                continue

        logger.info(f"✅ Found {len(all_liquidations)} total liquidations")

        # Store liquidations
        self.liquidations.extend(all_liquidations)

        return all_liquidations

    async def monitor_realtime(self, coins: List[str] = None, interval: int = 10):
        """
        Monitor blockchain for new liquidations in real-time

        Args:
            coins: List of coins to monitor
            interval: Polling interval in seconds
        """
        if coins is None:
            coins = ["BTC", "ETH", "SOL"]

        logger.info(f"🚀 Starting real-time liquidation monitoring")
        logger.info(f"   Coins: {', '.join(coins)}")
        logger.info(f"   Interval: {interval}s")

        seen_hashes = set()

        while True:
            try:
                for coin in coins:
                    trades = await self.query_recent_trades(coin)

                    for trade in trades:
                        tx_hash = trade.get('hash', '')

                        # Skip if already processed
                        if tx_hash in seen_hashes:
                            continue

                        seen_hashes.add(tx_hash)

                        # Check if liquidation
                        is_liq, _ = self.is_liquidation_trade(trade)

                        if is_liq:
                            liquidation = self.parse_liquidation(trade)

                            # Log liquidation event
                            logger.info(
                                f"💥 LIQUIDATION: {liquidation.coin} | "
                                f"{liquidation.liquidation_side} | "
                                f"${liquidation.value_usd:,.0f} | "
                                f"User: {liquidation.liquidated_user[:10]}..."
                            )

                            # Store and update stats
                            self.liquidations.append(liquidation)
                            self.total_liquidations += 1
                            self.total_value_usd += liquidation.value_usd
                            self.liquidations_by_coin[liquidation.coin] = \
                                self.liquidations_by_coin.get(liquidation.coin, 0) + 1

                            # Yield liquidation for processing
                            yield liquidation

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(interval)

    def get_statistics(self) -> dict:
        """Get aggregated liquidation statistics"""
        return {
            "total_liquidations": self.total_liquidations,
            "total_value_usd": self.total_value_usd,
            "unique_users_liquidated": len(self.liquidations_by_user),
            "liquidations_by_coin": self.liquidations_by_coin,
            "recent_liquidations_count": len(self.liquidations),
        }

    def get_recent_liquidations(self, limit: int = 10) -> List[BlockchainLiquidation]:
        """Get most recent liquidations"""
        return sorted(
            self.liquidations,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]


__all__ = ['HyperliquidBlockchainLiquidationTracker', 'BlockchainLiquidation']
