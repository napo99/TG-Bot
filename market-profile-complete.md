# SAVE THIS FILE AS: market-profile-implementation.md
# Complete Market Profile Feature Implementation Guide
# Generated: 2024
# Description: Full implementation guide for /profile command with VP and TPO calculations

################################################################################
# SECTION 1: PROJECT OVERVIEW
################################################################################

PROJECT: Market Profile Feature - /profile Command
OBJECTIVE: Implement Volume Profile and TPO calculations for Telegram bot
PERFORMANCE: <2 seconds response time
ACCURACY: TradingView-compatible methodology
EXCHANGE: Binance (default)

################################################################################
# SECTION 2: FILE 1 - profile_calculator.py
# Location: market_data_service/profile_calculator.py
################################################################################

"""
Copy this entire code block to market_data_service/profile_calculator.py
This is the core calculation engine for Volume Profile and TPO
"""

import numpy as np
import aiohttp
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
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
            
            # Fetch all candle data in parallel
            candle_data = await self._fetch_all_candles(binance_symbol)
            
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
                    
                    profiles[timeframe] = {
                        'volume_profile': vp,
                        'tpo': tpo,
                        'candles': len(candles),
                        'period': self.TIMEFRAME_CONFIG[timeframe]['period_name']
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
    
    async def _fetch_candles(self, session: aiohttp.ClientSession, 
                           symbol: str, interval: str, limit: int) -> List[Candle]:
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

################################################################################
# SECTION 3: FILE 2 - Update market_data_service/main.py
# ADD these lines to your existing main.py
################################################################################

# ADD IMPORTS:
from profile_calculator import ProfileCalculator
from pydantic import BaseModel
from typing import Optional

# ADD MODEL:
class ProfileRequest(BaseModel):
    symbol: str
    exchange: Optional[str] = "binance"

# ADD ENDPOINT:
@app.post("/market_profile")
async def get_market_profile(request: ProfileRequest) -> Dict[str, Any]:
    """
    Calculate Volume Profile and TPO for multiple timeframes
    """
    calculator = ProfileCalculator()
    try:
        result = await calculator.calculate_all_profiles(request.symbol, request.exchange)
        return result
    finally:
        await calculator.close()

################################################################################
# SECTION 4: FILE 3 - Update telegram_bot/main.py
# ADD to TelegramBot class
################################################################################

# ADD TO TelegramBot CLASS:

async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Market Profile command - Volume Profile and TPO analysis
    Usage: /profile BTC or /profile ETH
    """
    if not self._is_authorized(str(update.effective_user.id)):
        await update.message.reply_text("❌ Unauthorized access")
        return
    
    # Parse symbol (default to BTC)
    symbol = "BTC"
    if context.args:
        symbol = context.args[0].upper().replace('/', '').replace('-', '')
    
    # Send loading message
    loading_msg = await update.message.reply_text(
        f"⏳ Calculating Market Profile for {symbol}...\n"
        f"Computing VP & TPO across 5 timeframes..."
    )
    
    try:
        # Call market data service
        result = await self.market_client.get_market_profile(symbol)
        
        if result['success']:
            # Format the response
            message = self._format_profile_response(result['data'])
            
            # Delete loading message and send result
            await loading_msg.delete()
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await loading_msg.edit_text(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Profile command error: {e}")
        await loading_msg.edit_text(f"❌ Error calculating profile: {str(e)}")

def _format_profile_response(self, data: dict) -> str:
    """
    Format profile data for Telegram display
    """
    symbol = data['symbol']
    current_price = data['current_price']
    
    # Build message header
    message = f"""📊 **MARKET PROFILE - {symbol}**
💰 Current: ${current_price:,.2f}
{'─' * 30}

"""
    
    # Process each timeframe
    for tf in ['1m', '15m', '1h', '4h', '1d']:
        if tf not in data:
            continue
        
        tf_data = data[tf]
        vp = tf_data['volume_profile']
        tpo = tf_data['tpo']
        period = tf_data['period']
        candles = tf_data['candles']
        
        # Check if price is in value area
        vp_in_va = "✅" if vp['val'] <= current_price <= vp['vah'] else "❌"
        tpo_in_va = "✅" if tpo['val'] <= current_price <= tpo['vah'] else "❌"
        
        # Format section
        message += f"""**{tf.upper()}** ({period}, {candles} candles)
VP:  POC: ${vp['poc']:,.0f} | VAL: ${vp['val']:,.0f} | VAH: ${vp['vah']:,.0f} {vp_in_va}
TPO: POC: ${tpo['poc']:,.0f} | VAL: ${tpo['val']:,.0f} | VAH: ${tpo['vah']:,.0f} {tpo_in_va}
VA%: VP: {vp['value_area_pct']:.1f}% | TPO: {tpo['value_area_pct']:.1f}%

"""
    
    # Add analysis summary
    message += f"""{'─' * 30}
📍 **ANALYSIS**
"""
    
    # Count how many timeframes have price in value area
    in_vp_count = 0
    in_tpo_count = 0
    
    for tf in ['1m', '15m', '1h', '4h', '1d']:
        if tf in data:
            vp = data[tf]['volume_profile']
            tpo = data[tf]['tpo']
            if vp['val'] <= current_price <= vp['vah']:
                in_vp_count += 1
            if tpo['val'] <= current_price <= tpo['vah']:
                in_tpo_count += 1
    
    # Market state analysis
    if in_vp_count >= 3 and in_tpo_count >= 3:
        message += "• ✅ **BALANCED**: Price within value area on most timeframes\n"
        message += "• Strategy: Mean reversion likely, fade breakouts\n"
    elif in_vp_count <= 1 or in_tpo_count <= 1:
        message += "• ⚠️ **TRENDING**: Price outside value area on most timeframes\n"
        message += "• Strategy: Follow trend, breakout continuation likely\n"
    else:
        message += "• ⚪ **TRANSITIONING**: Mixed signals across timeframes\n"
        message += "• Strategy: Wait for clearer structure\n"
    
    # Add key levels
    message += f"""
📊 **KEY LEVELS**
- 1H VP POC: ${data.get('1h', {}).get('volume_profile', {}).get('poc', 0):,.0f} (High volume node)
- 4H VA: ${data.get('4h', {}).get('volume_profile', {}).get('val', 0):,.0f} - ${data.get('4h', {}).get('volume_profile', {}).get('vah', 0):,.0f}
- Daily POC: ${data.get('1d', {}).get('volume_profile', {}).get('poc', 0):,.0f} (Major reference)

✅ = In Value Area | ❌ = Outside VA

🕐 {datetime.now().strftime('%H:%M:%S')} UTC"""
    
    return message

# ADD TO MarketDataClient class:
async def get_market_profile(self, symbol: str) -> Dict[str, Any]:
    session = await self._get_session()
    try:
        async with session.post(f"{self.base_url}/market_profile", json={
            'symbol': symbol,
            'exchange': 'binance'
        }) as response:
            return await response.json()
    except Exception as e:
        logger.error(f"Error fetching market profile: {e}")
        return {'success': False, 'error': str(e)}

# IN main() function, ADD:
application.add_handler(CommandHandler("profile", bot.profile_command))

# UPDATE commands list:
BotCommand("profile", "📊 Market Profile (VP & TPO) analysis"),

################################################################################
# SECTION 5: DEPLOYMENT BASH SCRIPT
################################################################################

#!/bin/bash

# Save as: deploy_profile_feature.sh
# Make executable: chmod +x deploy_profile_feature.sh
# Run: ./deploy_profile_feature.sh

echo "🚀 Market Profile Feature Deployment"
echo "===================================="

# 1. Create branch
git checkout -b feature/market-profile-command

# 2. Install dependencies
pip install numpy==1.24.3
pip install pytest==7.4.0
pip install pytest-asyncio==0.21.1

# 3. Update requirements.txt
echo "numpy==1.24.3" >> requirements.txt

# 4. Create files
mkdir -p market_data_service/tests
mkdir -p telegram_bot/tests
touch market_data_service/profile_calculator.py
touch market_data_service/tests/test_profile.py
touch telegram_bot/tests/test_profile_cmd.py

# 5. Run tests
pytest market_data_service/tests/test_profile.py -v
pytest telegram_bot/tests/test_profile_cmd.py -v

# 6. Commit
git add .
git commit -m "feat: Add /profile command for VP and TPO analysis"
git push origin feature/market-profile-command

echo "✅ Deployment complete!"

################################################################################
# SECTION 6: VALIDATION CHECKLIST
################################################################################

VALIDATION CHECKLIST:
□ Response time <2 seconds
□ All 5 timeframes return data
□ POC, VAH, VAL values are consistent (VAL ≤ POC ≤ VAH)
□ Value area percentage between 65-75%
□ Binance API calls ≤5 per request
□ Memory usage <100MB
□ All tests pass
□ /profile BTC works in Telegram

################################################################################
# SECTION 7: KEY IMPLEMENTATION NOTES
################################################################################

CRITICAL NOTES FOR CLAUDE CODE:

1. PERFORMANCE:
   - Use NumPy, NOT pandas
   - Cache results for 60 seconds
   - Parallel API calls for all timeframes
   - Target <2 second response

2. BINS EXPLAINED:
   - Bins = price levels where we aggregate volume
   - Like horizontal bars in a histogram
   - TradingView default = 24 bins
   - More bins = more granular, slower calculation

3. API LIMITS:
   - Binance: 1200 weight/minute
   - Our usage: 5 calls (one per timeframe)
   - Well within limits

4. CALCULATION METHOD:
   - Volume Profile: Distribute candle volume across price range
   - TPO: Count time periods at each price level
   - Value Area: 70% of volume/time starting from POC

5. IF 1M IS TOO NOISY:
   - Keep code but comment out from display
   - Or reduce to last 30 minutes instead of 60

6. TESTING:
   - Run unit tests first
   - Then integration test
   - Finally manual Telegram test

################################################################################
# END OF DOCUMENT
################################################################################
