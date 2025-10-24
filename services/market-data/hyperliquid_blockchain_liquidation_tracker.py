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

        # Statistics - Basic counts
        self.total_liquidations = 0
        self.total_value_usd = 0.0
        self.liquidations_by_coin: Dict[str, int] = {}
        self.liquidations_by_user: Dict[str, int] = {}

        # Statistics - Side tracking
        self.long_liquidations = 0
        self.short_liquidations = 0
        self.long_liquidations_usd = 0.0
        self.short_liquidations_usd = 0.0

        # Statistics - Detailed by coin and side
        self.liquidations_by_coin_side: Dict[str, Dict[str, int]] = {}  # {"BTC": {"LONG": 5, "SHORT": 3}}
        self.volume_by_coin_side: Dict[str, Dict[str, float]] = {}  # {"BTC": {"LONG": 1000000, "SHORT": 500000}}

        # Statistics - User details
        self.user_liquidation_details: Dict[str, Dict] = {}  # {user_addr: {count, total_usd, coins, sides}}

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

    def _update_statistics(self, liquidation: BlockchainLiquidation):
        """
        Update all aggregated statistics for a liquidation

        Args:
            liquidation: BlockchainLiquidation to record
        """
        # Basic totals
        self.total_liquidations += 1
        self.total_value_usd += liquidation.value_usd

        # By coin
        coin = liquidation.coin
        self.liquidations_by_coin[coin] = self.liquidations_by_coin.get(coin, 0) + 1

        # By side
        side = liquidation.liquidation_side
        if side == "LONG":
            self.long_liquidations += 1
            self.long_liquidations_usd += liquidation.value_usd
        else:  # SHORT
            self.short_liquidations += 1
            self.short_liquidations_usd += liquidation.value_usd

        # By coin and side
        if coin not in self.liquidations_by_coin_side:
            self.liquidations_by_coin_side[coin] = {"LONG": 0, "SHORT": 0}
        if coin not in self.volume_by_coin_side:
            self.volume_by_coin_side[coin] = {"LONG": 0.0, "SHORT": 0.0}

        self.liquidations_by_coin_side[coin][side] += 1
        self.volume_by_coin_side[coin][side] += liquidation.value_usd

        # By user
        user = liquidation.liquidated_user
        self.liquidations_by_user[user] = self.liquidations_by_user.get(user, 0) + 1

        # Detailed user stats
        if user not in self.user_liquidation_details:
            self.user_liquidation_details[user] = {
                "count": 0,
                "total_usd": 0.0,
                "coins": set(),
                "long_count": 0,
                "short_count": 0,
                "first_seen": liquidation.timestamp,
                "last_seen": liquidation.timestamp
            }

        user_details = self.user_liquidation_details[user]
        user_details["count"] += 1
        user_details["total_usd"] += liquidation.value_usd
        user_details["coins"].add(coin)
        user_details["last_seen"] = max(user_details["last_seen"], liquidation.timestamp)

        if side == "LONG":
            user_details["long_count"] += 1
        else:
            user_details["short_count"] += 1

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

                            # Update all statistics
                            self._update_statistics(liquidation)

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

                            # Store and update all statistics
                            self.liquidations.append(liquidation)
                            self._update_statistics(liquidation)

                            # Yield liquidation for processing
                            yield liquidation

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(interval)

    def get_statistics(self) -> dict:
        """
        Get comprehensive aggregated liquidation statistics

        Returns:
            Dict with all aggregated metrics including:
            - Totals (count, USD volume)
            - By side (long vs short)
            - By coin
            - By coin and side
            - User statistics
        """
        # Calculate additional metrics
        avg_liquidation_size = self.total_value_usd / self.total_liquidations if self.total_liquidations > 0 else 0

        # Get top liquidated users
        top_users = sorted(
            [
                {
                    "address": addr,
                    "count": details["count"],
                    "total_usd": details["total_usd"],
                    "long_count": details["long_count"],
                    "short_count": details["short_count"],
                    "coins": list(details["coins"])
                }
                for addr, details in self.user_liquidation_details.items()
            ],
            key=lambda x: x["total_usd"],
            reverse=True
        )[:10]

        # Long vs Short ratio
        long_short_ratio = (
            self.long_liquidations / self.short_liquidations
            if self.short_liquidations > 0
            else float('inf') if self.long_liquidations > 0 else 0
        )

        return {
            # Overall totals
            "total_liquidations": self.total_liquidations,
            "total_value_usd": self.total_value_usd,
            "average_liquidation_size_usd": avg_liquidation_size,

            # By side
            "long_liquidations": self.long_liquidations,
            "short_liquidations": self.short_liquidations,
            "long_liquidations_usd": self.long_liquidations_usd,
            "short_liquidations_usd": self.short_liquidations_usd,
            "long_short_ratio": long_short_ratio,

            # By coin
            "liquidations_by_coin": self.liquidations_by_coin,
            "liquidations_by_coin_side": self.liquidations_by_coin_side,
            "volume_by_coin_side": self.volume_by_coin_side,

            # User statistics
            "unique_users_liquidated": len(self.liquidations_by_user),
            "top_liquidated_users": top_users,

            # Buffer info
            "recent_liquidations_count": len(self.liquidations),
        }

    def get_recent_liquidations(self, limit: int = 10) -> List[BlockchainLiquidation]:
        """Get most recent liquidations"""
        return sorted(
            self.liquidations,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

    def get_liquidations_by_timeframe(self, seconds: int) -> Dict:
        """
        Get aggregated liquidations within a time window

        Args:
            seconds: Time window in seconds (e.g., 3600 for last hour)

        Returns:
            Dict with aggregated stats for the timeframe
        """
        now = datetime.now().timestamp() * 1000  # Convert to ms
        cutoff = now - (seconds * 1000)

        # Filter liquidations within timeframe
        recent = [liq for liq in self.liquidations if liq.timestamp >= cutoff]

        if not recent:
            return {
                "count": 0,
                "total_usd": 0,
                "long_count": 0,
                "short_count": 0,
                "by_coin": {}
            }

        # Aggregate
        total_usd = sum(liq.value_usd for liq in recent)
        long_count = sum(1 for liq in recent if liq.liquidation_side == "LONG")
        short_count = len(recent) - long_count

        by_coin = {}
        for liq in recent:
            if liq.coin not in by_coin:
                by_coin[liq.coin] = {"count": 0, "usd": 0, "long": 0, "short": 0}
            by_coin[liq.coin]["count"] += 1
            by_coin[liq.coin]["usd"] += liq.value_usd
            if liq.liquidation_side == "LONG":
                by_coin[liq.coin]["long"] += 1
            else:
                by_coin[liq.coin]["short"] += 1

        return {
            "timeframe_seconds": seconds,
            "count": len(recent),
            "total_usd": total_usd,
            "long_count": long_count,
            "short_count": short_count,
            "long_usd": sum(liq.value_usd for liq in recent if liq.liquidation_side == "LONG"),
            "short_usd": sum(liq.value_usd for liq in recent if liq.liquidation_side == "SHORT"),
            "by_coin": by_coin,
            "average_size": total_usd / len(recent) if recent else 0
        }


__all__ = ['HyperliquidBlockchainLiquidationTracker', 'BlockchainLiquidation']
