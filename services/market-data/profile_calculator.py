import numpy as np
import aiohttp
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Candle:
    """Candle data structure"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class ProfileCalculator:
    """
    High-performance Volume Profile and TPO calculator
    Matches TradingView methodology for institutional-grade accuracy
    """
    
    TIMEFRAME_CONFIG = {
        '1m': {
            'interval': '1m',
            'lookback': 60,      # 1 hour of 1m candles
            'bins': 20,          # Fewer bins for short timeframe
            'period_name': 'Last hour',
            'tpo_period': 1      # 1 minute TPO blocks
        },
        '15m': {
            'interval': '15m',
            'lookback': 96,      # 24 hours
            'bins': 24,          # TradingView default
            'period_name': 'Last 24 hours',
            'tpo_period': 15     # 15 minute TPO blocks
        },
        '30m': {
            'interval': '30m',
            'lookback': 48,      # 24 hours of 30m candles
            'bins': 24,          # TradingView default
            'period_name': 'Last 24 hours',
            'tpo_period': 30     # 30 minute TPO blocks
        },
        '1h': {
            'interval': '1h',
            'lookback': 168,     # 7 days
            'bins': 24,
            'period_name': 'Last 7 days',
            'tpo_period': 30     # 30 minute TPO blocks
        },
        '4h': {
            'interval': '4h',
            'lookback': 84,      # 14 days (84 * 4 hours)
            'bins': 30,
            'period_name': 'Last 14 days',
            'tpo_period': 60     # 1 hour TPO blocks
        },
        '1d': {
            'interval': '1d',
            'lookback': 30,      # 30 days
            'bins': 50,
            'period_name': 'Last 30 days',
            'tpo_period': 240    # 4 hour TPO blocks
        }
    }
    
    # Session-based approach - midnight UTC for all timeframes (professional standard)
    SESSION_CONFIG = {
        'intraday_reset_hour': 0,  # 00:00 UTC for all timeframes (consistent)
        'daily_reset_hour': 0,     # 00:00 UTC for all timeframes (consistent)
        'intraday_timeframes': ['1m', '15m', '30m', '1h'],  # Use 00:00 UTC reset
        'daily_timeframes': ['4h', '1d']                    # Use 00:00 UTC reset
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}
        self.cache_ttl = 60  # 60 seconds cache
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Clean up session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_session_start_time(self, timeframe: str) -> datetime:
        """Get session start time based on timeframe - TradingView compatible"""
        utc_now = datetime.now(timezone.utc)
        
        # All timeframes now use midnight UTC reset (professional standard)
        reset_hour = 0  # Always midnight UTC
        session_start = utc_now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
        
        # Since reset is midnight, no need to check if we haven't reached today's reset
        # Current session always starts at today's midnight
                
        return session_start
    
    def _calculate_session_candles(self, interval: str, session_start: datetime) -> int:
        """Calculate number of candles needed from session start"""
        utc_now = datetime.now(timezone.utc)
        time_elapsed = utc_now - session_start
        hours_elapsed = max(0.1, time_elapsed.total_seconds() / 3600)  # Minimum 0.1 hour
        
        # Convert interval to minutes
        interval_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30, 
            '1h': 60, '4h': 240, '1d': 1440
        }
        
        minutes_per_candle = interval_minutes.get(interval, 60)
        candles_needed = int((hours_elapsed * 60) / minutes_per_candle)
        
        # Ensure reasonable bounds
        return max(1, min(candles_needed, 1000))  # Binance API limit
    
    def _get_session_period_name(self, timeframe: str) -> str:
        """Get session-based period name for display"""
        session_start = self._get_session_start_time(timeframe)
        
        hours_elapsed = (datetime.now(timezone.utc) - session_start).total_seconds() / 3600
        return f"Since {session_start.strftime('%Y-%m-%d 00:00 UTC')} ({hours_elapsed:.1f}h session)"
    
    async def calculate_all_profiles(self, symbol: str, exchange: str = "binance") -> Dict[str, Any]:
        """
        Main entry point - calculates profiles for all timeframes
        """
        try:
            await self._ensure_session()
            
            # Normalize symbol for Binance
            binance_symbol = symbol.replace('/', '').replace('-', '').upper()
            if not binance_symbol.endswith('USDT'):
                binance_symbol += 'USDT'
            
            logger.info(f"Calculating profiles for {binance_symbol}")
            
            # Fetch current price first
            current_price = await self._get_current_price(binance_symbol)
            
            # Fetch session-based candle data for each timeframe
            candle_data = await self._fetch_all_session_candles(binance_symbol)
            
            # Calculate profiles for each timeframe
            profiles = {
                'symbol': symbol,
                'current_price': current_price
            }
            
            for timeframe, candles in candle_data.items():
                if candles:
                    logger.info(f"Calculating {timeframe} profile with {len(candles)} candles")
                    
                    vp = self.calculate_volume_profile(
                        candles, 
                        num_bins=self.TIMEFRAME_CONFIG[timeframe]['bins']
                    )
                    
                    tpo = self.calculate_tpo_profile(
                        candles,
                        timeframe=timeframe
                    )
                    
                    # Calculate VWAP using same session data as Volume Profile
                    vwap = self.calculate_vwap(candles)
                    
                    profiles[timeframe] = {
                        'volume_profile': vp,
                        'tpo': tpo,
                        'vwap': vwap,
                        'candles': len(candles),
                        'period': self._get_session_period_name(timeframe)
                    }
            
            return {
                'success': True,
                'data': profiles
            }
            
        except Exception as e:
            logger.error(f"Profile calculation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_current_price(self, symbol: str) -> float:
        """Fetch current price from Binance"""
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to get price: HTTP {response.status}")
            
            data = await response.json()
            return float(data['price'])
    
    async def _fetch_all_session_candles(self, symbol: str) -> Dict[str, List[Candle]]:
        """Fetch session-based candles for all timeframes - TradingView compatible"""
        tasks = {}
        
        for timeframe, config in self.TIMEFRAME_CONFIG.items():
            # Get session start time for this timeframe
            session_start = self._get_session_start_time(timeframe)
            candles_needed = self._calculate_session_candles(config['interval'], session_start)
            
            logger.info(f"Timeframe {timeframe}: Session start {session_start.strftime('%Y-%m-%d %H:%M UTC')}, "
                       f"candles needed: {candles_needed}")
            
            task = self._fetch_candles(symbol, config['interval'], candles_needed)
            tasks[timeframe] = task
        
        # Execute all fetches in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        candle_data = {}
        for timeframe, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {timeframe} candles: {result}")
                candle_data[timeframe] = []
            else:
                candle_data[timeframe] = result
        
        return candle_data
    
    async def _fetch_all_candles(self, symbol: str) -> Dict[str, List[Candle]]:
        """Fetch candles for all timeframes in parallel"""
        tasks = {}
        
        for timeframe, config in self.TIMEFRAME_CONFIG.items():
            task = self._fetch_candles(
                symbol, 
                config['interval'], 
                config['lookback']
            )
            tasks[timeframe] = task
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        candle_data = {}
        for timeframe, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {timeframe} candles: {result}")
                candle_data[timeframe] = []
            else:
                candle_data[timeframe] = result
        
        return candle_data
    
    async def _fetch_vwap_candles(self, symbol: str, interval: str, limit: int) -> List[Candle]:
        """Fetch candles specifically for VWAP calculation with trading-optimized periods"""
        return await self._fetch_candles(symbol, interval, limit)
    
    async def _fetch_candles(self, symbol: str, interval: str, limit: int) -> List[Candle]:
        """Fetch candles from Binance API"""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)  # Binance limit
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"Binance API error: {response.status}")
            
            data = await response.json()
            
            candles = []
            for kline in data:
                candles.append(Candle(
                    timestamp=kline[0],
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5])
                ))
            
            return candles
    
    def calculate_volume_profile(self, candles: List[Candle], num_bins: int = 24) -> Dict[str, float]:
        """
        Calculate Volume Profile (VP) - TradingView compatible
        
        Returns:
            poc: Point of Control (highest volume price)
            vah: Value Area High (upper boundary of 70% volume)
            val: Value Area Low (lower boundary of 70% volume)
            value_area_pct: Actual percentage of volume in value area
        """
        if not candles:
            return {'poc': 0, 'vah': 0, 'val': 0, 'value_area_pct': 0}
        
        # Find price range
        high = max(c.high for c in candles)
        low = min(c.low for c in candles)
        
        # Prevent division by zero
        if high == low:
            return {'poc': high, 'vah': high, 'val': low, 'value_area_pct': 100.0}
        
        # Create price levels (bins)
        price_levels = np.linspace(low, high, num_bins + 1)
        volume_at_price = np.zeros(num_bins)
        
        # Distribute volume across price levels (TradingView method)
        for candle in candles:
            candle_range = candle.high - candle.low
            
            if candle_range == 0:
                # Single price point (doji candle)
                idx = np.searchsorted(price_levels[:-1], candle.close)
                if idx > 0:
                    idx -= 1
                if idx < num_bins:
                    volume_at_price[idx] += candle.volume
            else:
                # Distribute volume uniformly across candle range
                for i in range(num_bins):
                    level_low = price_levels[i]
                    level_high = price_levels[i + 1]
                    
                    # Calculate overlap between candle and price level
                    overlap_low = max(candle.low, level_low)
                    overlap_high = min(candle.high, level_high)
                    
                    if overlap_low < overlap_high:
                        # Calculate proportion of candle in this level
                        overlap_pct = (overlap_high - overlap_low) / candle_range
                        volume_at_price[i] += candle.volume * overlap_pct
        
        # Find POC (Point of Control)
        if np.sum(volume_at_price) == 0:
            return {'poc': (high + low) / 2, 'vah': high, 'val': low, 'value_area_pct': 0}
        
        poc_index = np.argmax(volume_at_price)
        poc_price = (price_levels[poc_index] + price_levels[poc_index + 1]) / 2
        
        # Calculate Value Area (70% of total volume) - TradingView method
        total_volume = np.sum(volume_at_price)
        value_area_volume = total_volume * 0.70
        
        # TradingView method: expand from POC outward, checking 2 levels at a time
        va_indices = {poc_index}
        accumulated_volume = volume_at_price[poc_index]
        
        while accumulated_volume < value_area_volume:
            max_idx = max(va_indices)
            min_idx = min(va_indices)
            
            above_volume = 0
            below_volume = 0
            
            # Check 2 levels above
            if max_idx + 1 < num_bins:
                above_volume = volume_at_price[max_idx + 1]
                if max_idx + 2 < num_bins:
                    above_volume += volume_at_price[max_idx + 2]
            
            # Check 2 levels below
            if min_idx - 1 >= 0:
                below_volume = volume_at_price[min_idx - 1]
                if min_idx - 2 >= 0:
                    below_volume += volume_at_price[min_idx - 2]
            
            # Add the side with more volume
            if above_volume > below_volume and max_idx + 1 < num_bins:
                va_indices.add(max_idx + 1)
                accumulated_volume += volume_at_price[max_idx + 1]
                if max_idx + 2 < num_bins and accumulated_volume < value_area_volume:
                    va_indices.add(max_idx + 2)
                    accumulated_volume += volume_at_price[max_idx + 2]
            elif min_idx - 1 >= 0:
                va_indices.add(min_idx - 1)
                accumulated_volume += volume_at_price[min_idx - 1]
                if min_idx - 2 >= 0 and accumulated_volume < value_area_volume:
                    va_indices.add(min_idx - 2)
                    accumulated_volume += volume_at_price[min_idx - 2]
            else:
                break
        
        # Get VAH and VAL
        vah_index = max(va_indices)
        val_index = min(va_indices)
        
        vah = price_levels[min(vah_index + 1, len(price_levels) - 1)]
        val = price_levels[val_index]
        
        return {
            'poc': round(poc_price, 2),
            'vah': round(vah, 2),
            'val': round(val, 2),
            'value_area_pct': round((accumulated_volume / total_volume) * 100, 1)
        }
    
    def calculate_tpo_profile(self, candles: List[Candle], timeframe: str) -> Dict[str, float]:
        """
        Calculate Time Price Opportunity (TPO) profile
        """
        if not candles:
            return {'poc': 0, 'vah': 0, 'val': 0, 'value_area_pct': 0}
        
        # Find price range
        high = max(c.high for c in candles)
        low = min(c.low for c in candles)
        
        if high == low:
            return {'poc': high, 'vah': high, 'val': low, 'value_area_pct': 100.0}
        
        # Create price levels (0.1% increments or 100 levels)
        num_levels = 100
        price_levels = np.linspace(low, high, num_levels)
        
        # Count time at each price level
        time_at_price = {}
        
        for candle in candles:
            # Find all price levels touched by this candle
            touched_levels = price_levels[
                (price_levels >= candle.low) & (price_levels <= candle.high)
            ]
            
            for level in touched_levels:
                level_key = round(level, 2)
                time_at_price[level_key] = time_at_price.get(level_key, 0) + 1
        
        if not time_at_price:
            return {'poc': (high + low) / 2, 'vah': high, 'val': low, 'value_area_pct': 0}
        
        # Find TPO POC (most time at price)
        tpo_poc = max(time_at_price, key=time_at_price.get)
        
        # Calculate TPO Value Area (70% of time)
        total_time = sum(time_at_price.values())
        value_area_time = total_time * 0.70
        
        # Sort prices
        sorted_prices = sorted(time_at_price.keys())
        
        # Find POC index
        try:
            poc_index = sorted_prices.index(tpo_poc)
        except ValueError:
            poc_index = len(sorted_prices) // 2
        
        # Expand from POC outward
        va_indices = {poc_index}
        accumulated_time = time_at_price[tpo_poc]
        
        while accumulated_time < value_area_time:
            max_idx = max(va_indices)
            min_idx = min(va_indices)
            
            added = False
            
            # Try to expand upward
            if max_idx + 1 < len(sorted_prices):
                va_indices.add(max_idx + 1)
                accumulated_time += time_at_price[sorted_prices[max_idx + 1]]
                added = True
            
            # Try to expand downward if still need more
            if accumulated_time < value_area_time and min_idx - 1 >= 0:
                va_indices.add(min_idx - 1)
                accumulated_time += time_at_price[sorted_prices[min_idx - 1]]
                added = True
            
            if not added:
                break
        
        tpo_vah = sorted_prices[max(va_indices)]
        tpo_val = sorted_prices[min(va_indices)]
        
        return {
            'poc': round(tpo_poc, 2),
            'vah': round(tpo_vah, 2),
            'val': round(tpo_val, 2),
            'value_area_pct': round((accumulated_time / total_time) * 100, 1)
        }
    
    def calculate_vwap(self, candles: List[Candle]) -> float:
        """Calculate VWAP (Volume Weighted Average Price)"""
        if not candles:
            return 0.0
        
        total_volume_price = 0.0
        total_volume = 0.0
        
        for candle in candles:
            # Calculate typical price (H + L + C) / 3
            typical_price = (candle.high + candle.low + candle.close) / 3.0
            volume = candle.volume
            
            total_volume_price += typical_price * volume
            total_volume += volume
        
        if total_volume == 0:
            return candles[-1].close  # Return last close if no volume
        
        return round(total_volume_price / total_volume, 2)