"""
Technical Indicators Module

This module provides efficient implementations of common technical indicators
for cryptocurrency market analysis. All functions are optimized for real-time
calculation and handle edge cases appropriately.

Functions take OHLCV data as input in the format:
[timestamp, open, high, low, close, volume]
"""

from typing import List, Tuple, Optional
import math


def calculate_rsi(ohlcv_data: List[List[float]], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI) for the given OHLCV data.
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        period: RSI period (default: 14)
    
    Returns:
        RSI value as float, or None if insufficient data
    """
    if len(ohlcv_data) < period + 1:
        return None
    
    # Extract closing prices
    closes = [candle[4] for candle in ohlcv_data]
    
    # Calculate price changes
    price_changes = []
    for i in range(1, len(closes)):
        price_changes.append(closes[i] - closes[i-1])
    
    if len(price_changes) < period:
        return None
    
    # Separate gains and losses
    gains = [change if change > 0 else 0 for change in price_changes]
    losses = [-change if change < 0 else 0 for change in price_changes]
    
    # Calculate initial averages (SMA for first calculation)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Apply smoothing for remaining periods (EMA-like smoothing)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    # Calculate RSI
    if avg_loss == 0:
        return 100.0  # No losses, RSI = 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_vwap(ohlcv_data: List[List[float]]) -> Optional[float]:
    """
    Calculate Volume Weighted Average Price (VWAP) for the given period.
    
    VWAP = Sum(Price * Volume) / Sum(Volume)
    Typical Price = (High + Low + Close) / 3
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
    
    Returns:
        VWAP value as float, or None if insufficient data
    """
    if not ohlcv_data:
        return None
    
    total_pv = 0  # Price * Volume sum
    total_volume = 0
    
    for candle in ohlcv_data:
        timestamp, open_price, high, low, close, volume = candle
        
        # Calculate typical price (HLC/3)
        typical_price = (high + low + close) / 3
        
        # Accumulate price*volume and volume
        pv = typical_price * volume
        total_pv += pv
        total_volume += volume
    
    if total_volume == 0:
        return None
    
    vwap = total_pv / total_volume
    return round(vwap, 8)  # Higher precision for crypto prices


def calculate_atr(ohlcv_data: List[List[float]], period: int = 14) -> Optional[float]:
    """
    Calculate Average True Range (ATR) - a volatility indicator.
    
    True Range = max(
        High - Low,
        |High - Previous Close|,
        |Low - Previous Close|
    )
    ATR = Average of True Range over the period
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        period: ATR period (default: 14)
    
    Returns:
        ATR value as float, or None if insufficient data
    """
    if len(ohlcv_data) < period + 1:
        return None
    
    true_ranges = []
    
    for i in range(1, len(ohlcv_data)):
        current = ohlcv_data[i]
        previous = ohlcv_data[i-1]
        
        high = current[2]
        low = current[3]
        prev_close = previous[4]
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = max(tr1, tr2, tr3)
        true_ranges.append(true_range)
    
    if len(true_ranges) < period:
        return None
    
    # Calculate initial ATR (SMA)
    atr = sum(true_ranges[:period]) / period
    
    # Apply smoothing for remaining periods (Wilder's smoothing)
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
    
    return round(atr, 8)


def calculate_volume_ratio(ohlcv_data: List[List[float]], lookback: int = 96) -> Optional[float]:
    """
    Calculate Volume Ratio - current volume vs average volume ratio.
    
    Volume Ratio = Current Volume / Average Volume (over lookback period)
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        lookback: Number of periods to look back for average (default: 96)
    
    Returns:
        Volume ratio as float, or None if insufficient data
    """
    if len(ohlcv_data) < 2:
        return None
    
    # Get current volume (latest candle)
    current_volume = ohlcv_data[-1][5]
    
    if current_volume == 0:
        return 0.0
    
    # Calculate average volume over lookback period
    end_index = len(ohlcv_data) - 1  # Exclude current candle from average
    start_index = max(0, end_index - lookback)
    
    if start_index >= end_index:
        return 1.0  # Not enough historical data
    
    volumes = [candle[5] for candle in ohlcv_data[start_index:end_index]]
    
    if not volumes:
        return 1.0
    
    avg_volume = sum(volumes) / len(volumes)
    
    if avg_volume == 0:
        return float('inf') if current_volume > 0 else 1.0
    
    volume_ratio = current_volume / avg_volume
    return round(volume_ratio, 2)


def get_all_indicators(ohlcv_data: List[List[float]], 
                      rsi_period: int = 14, 
                      atr_period: int = 14, 
                      volume_lookback: int = 96) -> dict:
    """
    Calculate all technical indicators at once for efficiency.
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        rsi_period: RSI calculation period
        atr_period: ATR calculation period
        volume_lookback: Volume ratio lookback period
    
    Returns:
        Dictionary containing all indicator values
    """
    indicators = {}
    
    try:
        indicators['rsi'] = calculate_rsi(ohlcv_data, rsi_period)
        indicators['vwap'] = calculate_vwap(ohlcv_data)
        indicators['atr'] = calculate_atr(ohlcv_data, atr_period)
        indicators['volume_ratio'] = calculate_volume_ratio(ohlcv_data, volume_lookback)
    except Exception as e:
        # Log error but don't crash
        indicators['error'] = str(e)
    
    return indicators


def validate_ohlcv_data(ohlcv_data: List[List[float]]) -> bool:
    """
    Validate OHLCV data format and basic integrity.
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
    
    Returns:
        True if data is valid, False otherwise
    """
    if not ohlcv_data or not isinstance(ohlcv_data, list):
        return False
    
    for candle in ohlcv_data:
        if not isinstance(candle, list) or len(candle) != 6:
            return False
        
        timestamp, open_price, high, low, close, volume = candle
        
        # Basic validation
        if not all(isinstance(x, (int, float)) for x in candle):
            return False
        
        # Price validation
        if high < low or high < open_price or high < close or low > open_price or low > close:
            return False
        
        # Volume should be non-negative
        if volume < 0:
            return False
    
    return True


# Example usage and testing
if __name__ == "__main__":
    # Sample OHLCV data for testing
    sample_data = [
        [1640995200, 47000, 47500, 46800, 47200, 1000],
        [1640998800, 47200, 47800, 47000, 47600, 1200],
        [1641002400, 47600, 48000, 47400, 47800, 900],
        [1641006000, 47800, 48200, 47600, 48000, 1100],
        [1641009600, 48000, 48500, 47900, 48300, 1300],
        [1641013200, 48300, 48600, 48100, 48400, 800],
        [1641016800, 48400, 48700, 48200, 48500, 1000],
        [1641020400, 48500, 48800, 48300, 48600, 1100],
        [1641024000, 48600, 49000, 48400, 48900, 1400],
        [1641027600, 48900, 49200, 48700, 49000, 1200],
        [1641031200, 49000, 49300, 48800, 49100, 1000],
        [1641034800, 49100, 49400, 48900, 49200, 900],
        [1641038400, 49200, 49500, 49000, 49300, 1100],
        [1641042000, 49300, 49600, 49100, 49400, 1300],
        [1641045600, 49400, 49700, 49200, 49500, 1500],
    ]
    
    print("Technical Indicators Test:")
    print("-" * 40)
    
    if validate_ohlcv_data(sample_data):
        indicators = get_all_indicators(sample_data)
        
        print(f"RSI (14): {indicators.get('rsi')}")
        print(f"VWAP: {indicators.get('vwap')}")
        print(f"ATR (14): {indicators.get('atr')}")
        print(f"Volume Ratio: {indicators.get('volume_ratio')}")
    else:
        print("Invalid OHLCV data format")