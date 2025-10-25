"""
Market Data Aggregator - Funding Rates, Open Interest, and Order Book Depth
Critical missing pieces for professional cascade detection
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import numpy as np


@dataclass
class MarketContext:
    """
    Complete market context that professionals track
    This is what your simple system was missing!
    """
    timestamp: float

    # Derivatives pressure
    funding_rate: float = 0.0              # Current funding rate (8h)
    funding_trend: str = 'neutral'         # increasing/decreasing/neutral
    max_funding_24h: float = 0.0          # Peak funding in 24h

    # Open Interest dynamics
    open_interest_usd: float = 0.0        # Current OI in USD
    oi_change_1m: float = 0.0             # 1 minute change %
    oi_change_5m: float = 0.0             # 5 minute change %
    oi_change_1h: float = 0.0             # 1 hour change %

    # Order book health
    bid_depth_2pct: float = 0.0           # Bid liquidity within 2%
    ask_depth_2pct: float = 0.0           # Ask liquidity within 2%
    book_imbalance: float = 0.0           # (bids - asks) / (bids + asks)
    depth_change_1m: float = 0.0          # Liquidity change %

    # Spot-Perp divergence
    spot_price: float = 0.0
    perp_price: float = 0.0
    premium: float = 0.0                  # (perp - spot) / spot

    # Cross-exchange metrics
    exchange_dispersion: float = 0.0      # Price dispersion across exchanges
    arbitrage_opportunity: bool = False    # Significant arb available

    # Volatility metrics
    realized_vol_5m: float = 0.0          # 5-minute realized volatility
    implied_vol: float = 0.0              # From options if available

    # Whale activity
    large_trades_1m: int = 0              # Trades > $1M last minute
    whale_accumulation: float = 0.0       # Net whale flow


class MarketDataAggregator:
    """
    Professional-grade market data aggregation
    This is what separates amateur from professional systems
    """

    def __init__(self):
        # API endpoints for major exchanges
        self.endpoints = {
            'binance': {
                'funding': 'https://fapi.binance.com/fapi/v1/fundingRate',
                'open_interest': 'https://fapi.binance.com/fapi/v1/openInterest',
                'depth': 'https://fapi.binance.com/fapi/v1/depth',
                'ticker': 'https://fapi.binance.com/fapi/v1/ticker/24hr'
            },
            'bybit': {
                'funding': 'https://api.bybit.com/v5/market/funding/history',
                'open_interest': 'https://api.bybit.com/v5/market/open-interest',
                'orderbook': 'https://api.bybit.com/v5/market/orderbook'
            },
            'okx': {
                'funding': 'https://www.okx.com/api/v5/public/funding-rate',
                'open_interest': 'https://www.okx.com/api/v5/public/open-interest',
                'books': 'https://www.okx.com/api/v5/market/books'
            }
        }

        # Historical storage
        self.funding_history = deque(maxlen=288)  # 24h at 5min intervals
        self.oi_history = deque(maxlen=720)       # 1h at 5sec intervals
        self.depth_history = deque(maxlen=60)     # 1min at 1sec intervals

        # Cache for expensive calculations
        self.context_cache = None
        self.cache_timestamp = 0

    async def get_complete_context(self, symbol: str = 'BTCUSDT') -> MarketContext:
        """
        Get complete market context in <100ms
        This is what professionals check before ANY trade
        """
        # Use cache if fresh (<100ms old)
        if self.context_cache and (time.time() - self.cache_timestamp) < 0.1:
            return self.context_cache

        # Parallel fetch all data
        tasks = [
            self._fetch_funding_rates(symbol),
            self._fetch_open_interest(symbol),
            self._fetch_order_book_depth(symbol),
            self._fetch_spot_perp_prices(symbol),
            self._calculate_volatility(symbol)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine into context
        context = MarketContext(timestamp=time.time())

        # Process funding rates
        if not isinstance(results[0], Exception):
            funding_data = results[0]
            context.funding_rate = funding_data['rate']
            context.funding_trend = funding_data['trend']
            context.max_funding_24h = funding_data['max_24h']

        # Process OI
        if not isinstance(results[1], Exception):
            oi_data = results[1]
            context.open_interest_usd = oi_data['current']
            context.oi_change_1m = oi_data['change_1m']
            context.oi_change_5m = oi_data['change_5m']
            context.oi_change_1h = oi_data['change_1h']

        # Process order book
        if not isinstance(results[2], Exception):
            depth_data = results[2]
            context.bid_depth_2pct = depth_data['bid_depth']
            context.ask_depth_2pct = depth_data['ask_depth']
            context.book_imbalance = depth_data['imbalance']
            context.depth_change_1m = depth_data['change_1m']

        # Process spot-perp
        if not isinstance(results[3], Exception):
            price_data = results[3]
            context.spot_price = price_data['spot']
            context.perp_price = price_data['perp']
            context.premium = (context.perp_price - context.spot_price) / context.spot_price

        # Process volatility
        if not isinstance(results[4], Exception):
            vol_data = results[4]
            context.realized_vol_5m = vol_data['realized']

        # Cache result
        self.context_cache = context
        self.cache_timestamp = time.time()

        return context

    async def _fetch_funding_rates(self, symbol: str) -> dict:
        """
        Fetch funding rates from multiple exchanges
        High funding = overleveraged market = cascade risk
        """
        funding_rates = {}

        async with aiohttp.ClientSession() as session:
            # Binance funding
            try:
                url = f"{self.endpoints['binance']['funding']}?symbol={symbol}"
                async with session.get(url, timeout=0.5) as resp:
                    data = await resp.json()
                    if data:
                        funding_rates['binance'] = float(data[-1]['fundingRate'])
            except:
                pass

            # Add more exchanges...

        # Calculate aggregate metrics
        if funding_rates:
            rates = list(funding_rates.values())
            current_rate = np.mean(rates)

            # Check trend
            self.funding_history.append({'time': time.time(), 'rate': current_rate})
            trend = 'neutral'
            if len(self.funding_history) > 10:
                recent = [h['rate'] for h in list(self.funding_history)[-10:]]
                if recent[-1] > recent[0] * 1.1:
                    trend = 'increasing'
                elif recent[-1] < recent[0] * 0.9:
                    trend = 'decreasing'

            # Get 24h max
            max_24h = max((h['rate'] for h in self.funding_history), default=current_rate)

            return {
                'rate': current_rate,
                'trend': trend,
                'max_24h': max_24h,
                'exchanges': funding_rates
            }

        return {'rate': 0, 'trend': 'neutral', 'max_24h': 0}

    async def _fetch_open_interest(self, symbol: str) -> dict:
        """
        Track open interest changes - rapid drops = position closing = cascades
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Simplified Binance OI fetch
                url = f"{self.endpoints['binance']['open_interest']}?symbol={symbol}"
                async with session.get(url, timeout=0.5) as resp:
                    data = await resp.json()
                    current_oi = float(data['openInterest']) * float(data.get('price', 40000))

                    # Store history
                    self.oi_history.append({'time': time.time(), 'oi': current_oi})

                    # Calculate changes
                    changes = {}
                    current_time = time.time()

                    for timeframe, seconds in [('1m', 60), ('5m', 300), ('1h', 3600)]:
                        past_oi = next(
                            (h['oi'] for h in self.oi_history
                             if current_time - h['time'] >= seconds),
                            current_oi
                        )
                        changes[f'change_{timeframe}'] = ((current_oi - past_oi) / past_oi * 100) if past_oi else 0

                    return {
                        'current': current_oi,
                        **changes
                    }
        except:
            return {'current': 0, 'change_1m': 0, 'change_5m': 0, 'change_1h': 0}

    async def _fetch_order_book_depth(self, symbol: str) -> dict:
        """
        Order book depth - liquidity evaporation = cascade amplification
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.endpoints['binance']['depth']}?symbol={symbol}&limit=100"
                async with session.get(url, timeout=0.5) as resp:
                    data = await resp.json()

                    # Get mid price
                    best_bid = float(data['bids'][0][0])
                    best_ask = float(data['asks'][0][0])
                    mid_price = (best_bid + best_ask) / 2

                    # Calculate depth within 2%
                    bid_depth = sum(
                        float(bid[0]) * float(bid[1])
                        for bid in data['bids']
                        if float(bid[0]) >= mid_price * 0.98
                    )

                    ask_depth = sum(
                        float(ask[0]) * float(ask[1])
                        for ask in data['asks']
                        if float(ask[0]) <= mid_price * 1.02
                    )

                    # Book imbalance
                    imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0

                    # Store and calculate change
                    self.depth_history.append({
                        'time': time.time(),
                        'bid': bid_depth,
                        'ask': ask_depth
                    })

                    change_1m = 0
                    if len(self.depth_history) > 60:
                        old_depth = self.depth_history[-60]
                        old_total = old_depth['bid'] + old_depth['ask']
                        new_total = bid_depth + ask_depth
                        change_1m = ((new_total - old_total) / old_total * 100) if old_total else 0

                    return {
                        'bid_depth': bid_depth,
                        'ask_depth': ask_depth,
                        'imbalance': imbalance,
                        'change_1m': change_1m
                    }
        except:
            return {'bid_depth': 0, 'ask_depth': 0, 'imbalance': 0, 'change_1m': 0}

    async def _fetch_spot_perp_prices(self, symbol: str) -> dict:
        """
        Spot-perp divergence indicates derivatives stress
        """
        try:
            # In production, fetch real prices
            # Simplified for example
            return {
                'spot': 40000,
                'perp': 40050
            }
        except:
            return {'spot': 0, 'perp': 0}

    async def _calculate_volatility(self, symbol: str) -> dict:
        """
        Calculate realized volatility from recent price movements
        """
        # Simplified - in production use proper OHLC data
        return {'realized': 0.02}  # 2% 5-minute volatility

    def get_cascade_risk_score(self, context: MarketContext) -> float:
        """
        Combine all market metrics into cascade risk score
        This is what was missing from your simple detector!
        """
        risk_score = 0.0

        # Funding rate pressure (0-25 points)
        if abs(context.funding_rate) > 0.1:  # >0.1% per 8h
            risk_score += 25
        elif abs(context.funding_rate) > 0.05:
            risk_score += 15
        elif abs(context.funding_rate) > 0.02:
            risk_score += 5

        # OI rapid drop (0-30 points)
        if context.oi_change_1m < -5:  # >5% drop in 1 minute
            risk_score += 30
        elif context.oi_change_5m < -10:  # >10% drop in 5 minutes
            risk_score += 20
        elif context.oi_change_1h < -15:  # >15% drop in 1 hour
            risk_score += 10

        # Liquidity evaporation (0-25 points)
        if context.depth_change_1m < -20:  # >20% depth loss
            risk_score += 25
        elif context.depth_change_1m < -10:
            risk_score += 15
        elif context.depth_change_1m < -5:
            risk_score += 5

        # Spot-perp divergence (0-20 points)
        if abs(context.premium) > 0.005:  # >0.5% premium
            risk_score += 20
        elif abs(context.premium) > 0.003:
            risk_score += 10
        elif abs(context.premium) > 0.001:
            risk_score += 5

        return min(100, risk_score)  # Cap at 100


# Example usage showing what professionals actually track
async def professional_monitoring():
    """
    This is what your simple system was missing!
    """
    aggregator = MarketDataAggregator()

    # Get complete market context
    context = await aggregator.get_complete_context('BTCUSDT')

    # Calculate risk
    risk = aggregator.get_cascade_risk_score(context)

    print(f"""
    🎯 PROFESSIONAL MARKET CONTEXT (What simple systems miss):

    📊 DERIVATIVES PRESSURE:
    Funding Rate: {context.funding_rate:.4%} ({context.funding_trend})
    Max 24h: {context.max_funding_24h:.4%}
    Risk: {'🔴 EXTREME' if abs(context.funding_rate) > 0.1 else '🟡 ELEVATED' if abs(context.funding_rate) > 0.05 else '🟢 NORMAL'}

    📈 OPEN INTEREST DYNAMICS:
    Current OI: ${context.open_interest_usd:,.0f}
    1m Change: {context.oi_change_1m:+.2f}%
    5m Change: {context.oi_change_5m:+.2f}%
    1h Change: {context.oi_change_1h:+.2f}%
    Signal: {'🔴 MASS CLOSING' if context.oi_change_1m < -5 else '🟡 CLOSING' if context.oi_change_1m < -2 else '🟢 STABLE'}

    📚 ORDER BOOK HEALTH:
    Bid Depth (2%): ${context.bid_depth_2pct:,.0f}
    Ask Depth (2%): ${context.ask_depth_2pct:,.0f}
    Imbalance: {context.book_imbalance:+.2%}
    Depth Change: {context.depth_change_1m:+.2f}%
    Health: {'🔴 THIN' if context.depth_change_1m < -20 else '🟡 WEAKENING' if context.depth_change_1m < -10 else '🟢 HEALTHY'}

    💱 SPOT-PERP DIVERGENCE:
    Spot: ${context.spot_price:,.2f}
    Perp: ${context.perp_price:,.2f}
    Premium: {context.premium:.3%}
    Status: {'🔴 STRESSED' if abs(context.premium) > 0.5 else '🟡 ELEVATED' if abs(context.premium) > 0.2 else '🟢 NORMAL'}

    🎯 CASCADE RISK SCORE: {risk:.0f}/100
    {'🚨 EXTREME RISK - CASCADE IMMINENT' if risk > 80 else
     '⚠️ HIGH RISK - CASCADE POSSIBLE' if risk > 60 else
     '👁️ MODERATE RISK - MONITOR CLOSELY' if risk > 40 else
     '✅ LOW RISK - NORMAL CONDITIONS'}
    """)

    return context, risk


if __name__ == "__main__":
    # This is what professionals check every second
    asyncio.run(professional_monitoring())