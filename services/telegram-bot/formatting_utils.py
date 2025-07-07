"""
Enhanced formatting utilities for the crypto assistant Telegram bot.
Provides improved number formatting and display functions.
"""

from typing import Optional, Union
from datetime import datetime
import pytz


def format_large_number(value: Union[int, float, None], decimals: int = 2) -> str:
    """
    Format large numbers with B/M/K notation for better readability.
    
    Args:
        value: The number to format (can be None)
        decimals: Number of decimal places (default: 2)
    
    Returns:
        Formatted string with appropriate suffix
    
    Examples:
        format_large_number(3200000000) -> "3.2B"
        format_large_number(32000450000) -> "32.0B"
        format_large_number(150000000) -> "150.0M"
        format_large_number(1500000) -> "1.5M"
        format_large_number(15000) -> "15.0K"
        format_large_number(None) -> "N/A"
    """
    if value is None:
        return "N/A"
    
    if value == 0:
        return "0"
    
    try:
        abs_value = abs(float(value))
        sign = "-" if value < 0 else ""
        
        # Billions
        if abs_value >= 1_000_000_000:
            formatted = abs_value / 1_000_000_000
            return f"{sign}{formatted:.{decimals}f}B"
        
        # Millions
        elif abs_value >= 1_000_000:
            formatted = abs_value / 1_000_000
            return f"{sign}{formatted:.{decimals}f}M"
        
        # Thousands
        elif abs_value >= 1_000:
            formatted = abs_value / 1_000
            return f"{sign}{formatted:.{decimals}f}K"
        
        # Less than 1000
        else:
            return f"{sign}{value:.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"


def format_price(price: Union[float, None], decimals: int = 2) -> str:
    """
    Format price with appropriate decimal places.
    
    Args:
        price: Price value (can be None)
        decimals: Number of decimal places (default: 2)
    
    Returns:
        Formatted price string
    """
    if price is None:
        return "$N/A"
    try:
        return f"${float(price):,.{decimals}f}"
    except (ValueError, TypeError):
        return "$N/A"


def format_percentage(percentage: Union[float, None], decimals: int = 2, show_sign: bool = True) -> str:
    """
    Format percentage with appropriate sign and decimals.
    
    Args:
        percentage: Percentage value (can be None)
        decimals: Number of decimal places (default: 2)
        show_sign: Whether to show + for positive values
    
    Returns:
        Formatted percentage string
    """
    if percentage is None:
        return "N/A%"
    
    try:
        percentage = float(percentage)
        if show_sign:
            sign = "+" if percentage >= 0 else ""
            return f"{sign}{percentage:.{decimals}f}%"
        else:
            return f"{percentage:.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A%"


def format_volume_with_usd(volume_native: Union[float, None], token: str, price: Union[float, None], decimals: int = 2) -> str:
    """
    Format volume showing both native token amount and USD value.
    
    Args:
        volume_native: Volume in native token (can be None)
        token: Token symbol (e.g., "BTC")
        price: Token price in USD (can be None)
        decimals: Number of decimal places for formatting
    
    Returns:
        Formatted volume string like "9,270 BTC ($1.0B)"
    """
    if volume_native is None or price is None:
        return f"N/A {token} ($N/A)"
    
    try:
        volume_native = float(volume_native)
        price = float(price)
        volume_usd = volume_native * price
        
        # Format native volume with appropriate precision
        if volume_native >= 1000:
            native_str = f"{volume_native:,.0f}"
        else:
            native_str = f"{volume_native:.{decimals}f}"
        
        # Format USD volume with B/M/K notation
        usd_str = format_large_number(volume_usd, decimals)
        
        return f"{native_str} {token} (${usd_str})"
    except (ValueError, TypeError):
        return f"N/A {token} ($N/A)"


def format_dollar_amount(amount: Union[float, None], decimals: int = 2) -> str:
    """
    Format dollar amount with appropriate notation.
    
    Args:
        amount: Dollar amount (can be None)
        decimals: Number of decimal places
    
    Returns:
        Formatted dollar amount string
    """
    if amount is None:
        return "$N/A"
    
    try:
        formatted = format_large_number(float(amount), decimals)
        return f"${formatted}" if formatted != "N/A" else "$N/A"
    except (ValueError, TypeError):
        return "$N/A"


def format_dual_timezone_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format timestamp showing both UTC and SGT times.
    
    Args:
        dt: Datetime object (uses current time if None)
    
    Returns:
        Formatted timestamp string like "15:49:39 UTC / 23:49:39 SGT"
    """
    if dt is None:
        dt = datetime.now(pytz.UTC)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    
    # Convert to UTC and SGT
    utc_time = dt.astimezone(pytz.UTC)
    sgt_time = dt.astimezone(pytz.timezone('Asia/Singapore'))
    
    return f"{utc_time.strftime('%H:%M:%S')} UTC / {sgt_time.strftime('%H:%M:%S')} SGT"


def get_change_emoji(change: Union[float, None]) -> str:
    """
    Get appropriate emoji for price/volume change.
    
    Args:
        change: Change value (positive/negative, can be None)
    
    Returns:
        Appropriate emoji
    """
    if change is None:
        return "⚪"
    
    try:
        change = float(change)
        if change > 0:
            return "🟢"
        elif change < 0:
            return "🔴"
        else:
            return "⚪"
    except (ValueError, TypeError):
        return "⚪"


def format_delta_value(delta: Union[float, None], token: str, price: Union[float, None], decimals: int = 2) -> str:
    """
    Format delta value with both token amount and USD value.
    
    Args:
        delta: Delta value in tokens (can be None)
        token: Token symbol
        price: Token price in USD (can be None)
        decimals: Number of decimal places
    
    Returns:
        Formatted delta string like "+800 BTC ($86.6M)"
    """
    if delta is None or price is None:
        return f"N/A {token} ($N/A)"
    
    try:
        delta = float(delta)
        price = float(price)
        sign = "+" if delta >= 0 else ""
        delta_usd = delta * price
        
        # Format token amount
        if abs(delta) >= 1000:
            token_str = f"{sign}{delta:,.0f}"
        else:
            token_str = f"{sign}{delta:.{decimals}f}"
        
        # Format USD amount
        usd_str = format_large_number(delta_usd, decimals)
        usd_sign = "+" if delta_usd >= 0 else ""
        
        return f"{token_str} {token} ({usd_sign}${usd_str})" if usd_str != "N/A" else f"{token_str} {token} ($N/A)"
    except (ValueError, TypeError):
        return f"N/A {token} ($N/A)"