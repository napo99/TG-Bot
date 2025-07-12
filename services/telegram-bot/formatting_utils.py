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
            return f"{sign}{abs_value:.{decimals}f}"
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


def format_funding_rate(funding_rate: Union[float, None]) -> str:
    """
    Format funding rate with appropriate precision for small values.
    
    Args:
        funding_rate: Funding rate value (can be None)
    
    Returns:
        Formatted funding rate string with 4 decimal places
    """
    if funding_rate is None:
        return "N/A%"
    
    try:
        funding_rate = float(funding_rate)
        percentage = funding_rate * 100
        sign = "+" if percentage >= 0 else ""
        return f"{sign}{percentage:.4f}%"
    except (ValueError, TypeError):
        return "N/A%"


def format_enhanced_funding_rate(funding_rate: Union[float, None]) -> str:
    """
    Format enhanced funding rate with annual cost, reset timing, and strategy.
    
    Args:
        funding_rate: Funding rate value (can be None)
    
    Returns:
        Multi-line enhanced funding display
    """
    if funding_rate is None:
        return "💸 Funding: N/A"
    
    try:
        from datetime import datetime, timezone
        
        funding_rate = float(funding_rate)
        percentage = funding_rate * 100
        sign = "+" if percentage >= 0 else ""
        
        # Calculate annual cost (funding every 8 hours = 3x daily = 1095x annually)
        annual_rate = funding_rate * 1095 * 100
        annual_sign = "+" if annual_rate >= 0 else ""
        
        # Calculate time to next reset (8-hour cycles: 00:00, 08:00, 16:00 UTC)
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        # Find next reset hour
        reset_hours = [0, 8, 16]
        next_reset = None
        for reset_hour in reset_hours:
            if reset_hour > current_hour:
                next_reset = reset_hour
                break
        
        if next_reset is None:
            next_reset = reset_hours[0] + 24  # Next day's first reset
        
        hours_to_reset = next_reset - current_hour
        minutes_to_reset = 60 - now_utc.minute
        if minutes_to_reset == 60:
            minutes_to_reset = 0
        else:
            hours_to_reset -= 1
        
        # Market pressure analysis
        if abs(percentage) < 0.001:
            pressure = "⚪ NEUTRAL"
            strategy = "Balanced market"
        elif percentage > 0.01:
            pressure = "🔥 LONG SQUEEZE"
            strategy = "Short bias - longs getting expensive"
        elif percentage > 0.005:
            pressure = "🟡 LONG PRESSURE"
            strategy = "Consider short positions"
        elif percentage < -0.01:
            pressure = "❄️ SHORT SQUEEZE"
            strategy = "Long bias - shorts getting expensive"
        elif percentage < -0.005:
            pressure = "🟢 SHORT PRESSURE"
            strategy = "Consider long positions"
        else:
            pressure = "⚪ BALANCED"
            strategy = "Neutral funding environment"
        
        return f"""💸 Funding: {sign}{percentage:.4f}% ({annual_sign}{annual_rate:.2f}% annually)
⏰ Resets in: {hours_to_reset}h {minutes_to_reset}m | {pressure}
🎯 Strategy: {strategy}"""
        
    except (ValueError, TypeError):
        return "💸 Funding: N/A"


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


def format_delta_with_emoji(delta: Union[float, None], token: str, price: Union[float, None], decimals: int = 2) -> str:
    """
    Format delta value with green/red dot emoji and both token amount and USD value.
    
    Args:
        delta: Delta value in tokens (can be None)
        token: Token symbol
        price: Token price in USD (can be None)
        decimals: Number of decimal places
    
    Returns:
        Formatted delta string like "🟢 Delta 24h: +800 BTC (+$86.6M)"
    """
    if delta is None or price is None:
        return f"⚪ N/A {token} ($N/A)"
    
    try:
        delta = float(delta)
        price = float(price)
        
        # Get emoji based on delta value
        emoji = get_change_emoji(delta)
        
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
        
        return f"{emoji} {token_str} {token} ({usd_sign}${usd_str})" if usd_str != "N/A" else f"{emoji} {token_str} {token} ($N/A)"
    except (ValueError, TypeError):
        return f"⚪ N/A {token} ($N/A)"


def calculate_long_short_ratio(delta: float, volume: float) -> float:
    """
    Calculate Long/Short ratio from delta and volume.
    
    Args:
        delta: Volume delta (positive = net buying, negative = net selling)
        volume: Total volume
    
    Returns:
        ratio: Longs over Shorts ratio (e.g., 3.25x means 3.25 longs for every 1 short)
    """
    if volume <= 0:
        return 1.0  # neutral
    
    # Calculate buy and sell volumes
    buy_volume = (volume + delta) / 2
    sell_volume = (volume - delta) / 2
    
    # Ensure no negative volumes
    buy_volume = max(0, buy_volume)
    sell_volume = max(0, sell_volume)
    
    # Calculate ratio (longs over shorts)
    if sell_volume > 0:
        ratio = buy_volume / sell_volume
        return min(ratio, 99.9)  # Cap at 99.9x for display
    else:
        return 99.9


def format_long_short_ratio(delta: float, volume: float) -> str:
    """
    Format L/S ratio for display as percentage split.
    
    Args:
        delta: Volume delta
        volume: Total volume
    
    Returns:
        Formatted L/S ratio string like "L/S: 48%/52%"
    """
    if volume <= 0:
        return "L/S: 50%/50%"
    
    # Calculate buy and sell volumes
    buy_volume = (volume + delta) / 2
    sell_volume = (volume - delta) / 2
    
    # Ensure no negative volumes
    buy_volume = max(0, buy_volume)
    sell_volume = max(0, sell_volume)
    
    # Calculate percentages
    total = buy_volume + sell_volume
    if total > 0:
        buy_pct = (buy_volume / total) * 100
        sell_pct = (sell_volume / total) * 100
    else:
        buy_pct = sell_pct = 50
    
    return f"L/S: {buy_pct:.0f}%/{sell_pct:.0f}%"


def analyze_market_control(delta: float, volume: float) -> tuple:
    """
    Analyze market control and pressure level.
    
    Args:
        delta: Volume delta
        volume: Total volume
    
    Returns:
        tuple: (control_string, pressure_percentage)
    """
    if volume <= 0:
        return "⚪ BALANCED", 50
    
    # Calculate buying pressure percentage
    buy_pct = ((volume + delta) / (2 * volume)) * 100
    
    if buy_pct >= 65:
        return "🟢 BUYERS", buy_pct
    elif buy_pct <= 35:
        return "🔴 SELLERS", 100 - buy_pct  # Show selling pressure
    else:
        return "⚪ BALANCED", max(buy_pct, 100 - buy_pct)


def analyze_momentum(delta_15m: float, delta_24h: float, volume_15m: float, volume_24h: float) -> str:
    """
    Analyze momentum direction by comparing 15m vs 24h normalized delta.
    
    Args:
        delta_15m: 15-minute delta
        delta_24h: 24-hour delta
        volume_15m: 15-minute volume
        volume_24h: 24-hour volume
    
    Returns:
        Momentum string: ACCELERATING, DECELERATING, or STEADY
    """
    if volume_24h <= 0 or volume_15m <= 0:
        return "STEADY"
    
    # Normalize deltas to comparable timeframes (per unit volume)
    delta_24h_norm = delta_24h / volume_24h if volume_24h > 0 else 0
    delta_15m_norm = delta_15m / volume_15m if volume_15m > 0 else 0
    
    # Compare momentum
    if abs(delta_15m_norm) > abs(delta_24h_norm) * 1.5:
        return "ACCELERATING"
    elif abs(delta_15m_norm) < abs(delta_24h_norm) * 0.5:
        return "DECELERATING"
    else:
        return "STEADY"


def format_oi_change(oi_change: float, token: str, price: float, current_oi: float = None) -> str:
    """
    Format OI change with token amount, USD value, and percentage.
    
    Args:
        oi_change: OI change in tokens (can be positive or negative)
        token: Token symbol
        price: Token price in USD
        current_oi: Current OI for percentage calculation
    
    Returns:
        Formatted OI change string like "+3,595 BTC (+$423.6M) | +4.62%"
    """
    if oi_change is None:
        return "N/A"
    
    try:
        # Format token amount
        sign = "+" if oi_change >= 0 else ""
        if abs(oi_change) >= 1000:
            token_str = f"{sign}{oi_change:,.0f}"
        else:
            token_str = f"{sign}{oi_change:.2f}"
        
        # Format USD amount
        oi_change_usd = oi_change * price
        usd_str = format_large_number(oi_change_usd, 1)
        usd_sign = "+" if oi_change_usd >= 0 else ""
        
        # Calculate percentage change if current OI is available
        percentage_str = ""
        if current_oi is not None and current_oi > 0:
            percentage = (oi_change / current_oi) * 100
            pct_sign = "+" if percentage >= 0 else ""
            percentage_str = f" | {pct_sign}{percentage:.2f}%"
        
        return f"{token_str} {token} ({usd_sign}${usd_str}){percentage_str}"
        
    except (ValueError, TypeError):
        return "N/A"


def analyze_volume_activity(volume_15m: float, volume_24h: float) -> str:
    """
    Analyze volume activity level relative to 24h average.
    
    Args:
        volume_15m: 15-minute volume
        volume_24h: 24-hour volume
    
    Returns:
        Activity string with ratio like "HIGH (2.1x)"
    """
    if volume_24h <= 0:
        return "NORMAL (1.0x)"
    
    # Expected 15m volume is 1/96th of 24h volume
    expected_15m = volume_24h / 96
    ratio = volume_15m / expected_15m if expected_15m > 0 else 1
    
    if ratio > 3:
        return f"EXTREME ({ratio:.1f}x)"
    elif ratio > 2:
        return f"HIGH ({ratio:.1f}x)"
    elif ratio > 1.5:
        return f"ABOVE AVG ({ratio:.1f}x)"
    elif ratio < 0.5:
        return f"LOW ({ratio:.1f}x)"
    else:
        return f"NORMAL ({ratio:.1f}x)"


def generate_market_signals(control_24h: str, control_15m: str, volume_activity: str, 
                          delta_15m: float, volume_15m: float, price_change_15m: float) -> str:
    """
    Generate market intelligence signals based on current conditions.
    
    Args:
        control_24h: 24H market control string
        control_15m: 15M market control string
        volume_activity: Volume activity string
        delta_15m: 15-minute delta
        volume_15m: 15-minute volume
        price_change_15m: 15-minute price change percentage
    
    Returns:
        Market signals string like "Strong Support | Seller Exhaustion | High Activity"
    """
    signals = []
    
    # Calculate pressure for pattern detection
    if volume_15m > 0:
        pressure_pct = abs(delta_15m / volume_15m) * 100
        
        # Absorption patterns (high pressure, low price movement)
        if pressure_pct > 70 and abs(price_change_15m) < 0.1:
            if delta_15m < 0:
                signals.append("Strong Support")
            else:
                signals.append("Strong Resistance")
        
        # Exhaustion patterns (very high pressure)
        elif pressure_pct > 80:
            if delta_15m < 0:
                signals.append("Seller Exhaustion")
            else:
                signals.append("Buyer Climax")
    
    # Volume context signals
    if "HIGH" in volume_activity or "EXTREME" in volume_activity:
        activity_level = volume_activity.split()[0].title()
        signals.append(f"{activity_level} Activity")
    
    # Control divergence patterns
    if "BUYERS" in control_24h and "SELLERS" in control_15m:
        signals.append("Institutional Buying")
    elif "SELLERS" in control_24h and "BUYERS" in control_15m:
        signals.append("Retail Bounce")
    
    return " | ".join(signals[:4])  # Max 4 signals for readability


def format_market_intelligence(spot_data: dict, perp_data: dict) -> str:
    """
    Format market intelligence section for price command.
    
    Args:
        spot_data: Spot market data dictionary
        perp_data: Perpetuals market data dictionary
    
    Returns:
        Formatted market intelligence string
    """
    # Use perp data as primary (higher volume, more institutional)
    primary_data = perp_data if perp_data else spot_data
    if not primary_data:
        return "🧠 MARKET INTELLIGENCE\n💪 Data unavailable"
    
    # 24H Analysis
    control_24h, pressure_24h = analyze_market_control(
        primary_data.get('delta_24h', 0), 
        primary_data.get('volume_24h', 0)
    )
    
    momentum = analyze_momentum(
        primary_data.get('delta_15m', 0),
        primary_data.get('delta_24h', 0),
        primary_data.get('volume_15m', 0),
        primary_data.get('volume_24h', 0)
    )
    
    # 15M Analysis
    control_15m, pressure_15m = analyze_market_control(
        primary_data.get('delta_15m', 0),
        primary_data.get('volume_15m', 0)
    )
    
    volume_activity = analyze_volume_activity(
        primary_data.get('volume_15m', 0),
        primary_data.get('volume_24h', 0)
    )
    
    return f"""🧠 MARKET INTELLIGENCE
💪 24H Control: {control_24h} ({pressure_24h:.0f}% pressure) | Momentum: {momentum}
⚡ 15M Control: {control_15m} ({pressure_15m:.0f}% pressure) | Activity: {volume_activity}"""


def format_market_summary(spot_data: dict, perp_data: dict) -> str:
    """
    Format market summary section for price command.
    
    Args:
        spot_data: Spot market data dictionary
        perp_data: Perpetuals market data dictionary
    
    Returns:
        Formatted market summary string
    """
    # Use perp data as primary
    primary_data = perp_data if perp_data else spot_data
    if not primary_data:
        return "🎯 MARKET SUMMARY\n🧠 Data unavailable"
    
    # Analyze market conditions
    control_24h, _ = analyze_market_control(
        primary_data.get('delta_24h', 0), 
        primary_data.get('volume_24h', 0)
    )
    
    control_15m, _ = analyze_market_control(
        primary_data.get('delta_15m', 0),
        primary_data.get('volume_15m', 0)
    )
    
    volume_activity = analyze_volume_activity(
        primary_data.get('volume_15m', 0),
        primary_data.get('volume_24h', 0)
    )
    
    # Generate signals
    signals = generate_market_signals(
        control_24h, control_15m, volume_activity,
        primary_data.get('delta_15m', 0),
        primary_data.get('volume_15m', 0),
        primary_data.get('change_15m', 0)
    )
    
    if signals:
        return f"🎯 MARKET SUMMARY\n🧠 {signals}"
    else:
        return "🎯 MARKET SUMMARY\n🧠 Balanced Market"