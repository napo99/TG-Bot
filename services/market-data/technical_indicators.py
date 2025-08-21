"""
Technical Indicators for Crypto Trading Assistant
Simple implementations using CCXT OHLCV data
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class TechnicalIndicators:
    symbol: str
    timeframe: str
    rsi_14: Optional[float] = None
    vwap: Optional[float] = None
    atr_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_middle: Optional[float] = None
    current_price: Optional[float] = None
    volatility_24h: Optional[float] = None
    # New fields for enhanced template
    volatility_15m: Optional[float] = None
    atr_usd: Optional[float] = None

class IndicatorCalculator:
    """Calculate technical indicators from OHLCV data"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    @staticmethod
    def calculate_vwap(high: List[float], low: List[float], close: List[float], 
                      volume: List[float]) -> Optional[float]:
        """Calculate VWAP (Volume Weighted Average Price)"""
        if not all([high, low, close, volume]) or len(close) == 0:
            return None
        
        typical_price = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]
        vwap_sum = sum(tp * v for tp, v in zip(typical_price, volume))
        volume_sum = sum(volume)
        
        if volume_sum == 0:
            return None
        
        return round(vwap_sum / volume_sum, 4)
    
    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], 
                     period: int = 14) -> Optional[float]:
        """Calculate ATR (Average True Range)"""
        if len(close) < period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        if len(true_ranges) < period:
            return None
        
        atr = np.mean(true_ranges[-period:])
        return round(atr, 4)
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, 
                                std_dev: float = 2.0) -> Dict[str, Optional[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {'upper': None, 'middle': None, 'lower': None}
        
        recent_prices = prices[-period:]
        middle = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return {
            'upper': round(upper, 4),
            'middle': round(middle, 4),
            'lower': round(lower, 4)
        }
    
    @staticmethod
    def calculate_current_volatility(ohlcv_data: List[List[float]]) -> Optional[float]:
        """Calculate volatility for current candle (15m timeframe)"""
        if not ohlcv_data or len(ohlcv_data) == 0:
            return None
        
        current_candle = ohlcv_data[-1]
        timestamp, open_price, high, low, close, volume = current_candle
        
        if open_price <= 0:
            return None
        
        # Calculate volatility as percentage of price range relative to open
        volatility = ((high - low) / open_price) * 100
        return round(volatility, 2)
    
    @staticmethod 
    def calculate_atr_usd(ohlcv_data: List[List[float]], current_price: float, period: int = 14) -> Optional[float]:
        """Calculate ATR in USD value terms"""
        if len(ohlcv_data) < period + 1:
            return None
        
        # Extract OHLC data
        high_prices = [candle[2] for candle in ohlcv_data]
        low_prices = [candle[3] for candle in ohlcv_data]
        close_prices = [candle[4] for candle in ohlcv_data]
        
        # Calculate ATR using existing method
        atr = IndicatorCalculator.calculate_atr(high_prices, low_prices, close_prices, period)
        
        if atr is None:
            return None
        
        # ATR is already in price terms, so it's already in USD for USD pairs
        return round(atr, 2)
    
    @staticmethod
    def calculate_volatility(prices: List[float], period: int = 24) -> Optional[float]:
        """Calculate price volatility (standard deviation of returns)"""
        if len(prices) < period + 1:
            return None
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        recent_returns = returns[-period:]
        volatility = np.std(recent_returns) * 100  # Convert to percentage
        return round(volatility, 2)

class TechnicalAnalysisService:
    """Service to fetch and calculate technical indicators"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
    
    async def get_technical_indicators(self, symbol: str, timeframe: str = '1h', 
                                     exchange: str = None) -> TechnicalIndicators:
        """Fetch OHLCV data and calculate technical indicators"""
        try:
            if exchange is None:
                exchange = 'binance'
            
            if exchange not in self.exchange_manager.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchange_manager.exchanges[exchange]
            
            # Use timeframe-appropriate periods for VWAP calculation
            # This matches trading app behavior better than fixed 100 candles
            # Optimized VWAP periods for trading effectiveness
            # Shorter periods provide more responsive signals for actual trading
            vwap_periods = {
                '1m': 60,      # 1 hour - responsive for scalping
                '3m': 40,      # 2 hours - short-term 
                '5m': 48,      # 4 hours - balanced
                '15m': 96,     # 24 hours - full day context
                '30m': 48,     # 24 hours - extended session
                '1h': 72,      # 3 days - optimal for swing trading
                '2h': 36,      # 3 days - equivalent
                '4h': 42,      # 7 days - position trading
                '6h': 28,      # 7 days - equivalent
                '12h': 14,     # 7 days - equivalent
                '1d': 20,      # 20 days - monthly positioning
            }
            
            # Get appropriate period for this timeframe, fallback to 50 if not specified
            vwap_limit = vwap_periods.get(timeframe, 50)
            
            # Fetch OHLCV data with timeframe-appropriate period
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=vwap_limit)
            
            if len(ohlcv) < 20:  # Need minimum data for calculations
                return TechnicalIndicators(symbol=symbol, timeframe=timeframe)
            
            # Extract OHLCV data
            timestamps = [candle[0] for candle in ohlcv]
            opens = [candle[1] for candle in ohlcv]
            highs = [candle[2] for candle in ohlcv]
            lows = [candle[3] for candle in ohlcv]
            closes = [candle[4] for candle in ohlcv]
            volumes = [candle[5] for candle in ohlcv]
            
            # Calculate indicators
            calc = IndicatorCalculator()
            
            rsi = calc.calculate_rsi(closes)
            # VWAP now uses timeframe-appropriate periods:
            # 15m timeframe = 24 candles = 6 hours (matches trading apps ~$104,850)
            vwap = calc.calculate_vwap(highs, lows, closes, volumes)
            atr = calc.calculate_atr(highs, lows, closes)
            bb = calc.calculate_bollinger_bands(closes)
            volatility = calc.calculate_volatility(closes)
            
            # Calculate new indicators for enhanced template
            current_price = closes[-1] if closes else None
            volatility_15m = calc.calculate_current_volatility(ohlcv)
            atr_usd = calc.calculate_atr_usd(ohlcv, current_price) if current_price else None
            
            return TechnicalIndicators(
                symbol=symbol,
                timeframe=timeframe,
                rsi_14=rsi,
                vwap=vwap,
                atr_14=atr,
                bb_upper=bb['upper'],
                bb_middle=bb['middle'],
                bb_lower=bb['lower'],
                current_price=current_price,
                volatility_24h=volatility,
                volatility_15m=volatility_15m,
                atr_usd=atr_usd
            )
            
        except Exception as e:
            print(f"Error calculating technical indicators: {e}")
            return TechnicalIndicators(symbol=symbol, timeframe=timeframe)

# Example usage:
# ta_service = TechnicalAnalysisService(exchange_manager)
# indicators = await ta_service.get_technical_indicators("BTC/USDT", "1h")
# print(f"RSI: {indicators.rsi_14}, VWAP: {indicators.vwap}")