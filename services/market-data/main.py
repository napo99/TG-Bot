import asyncio
import os
import ccxt.pro as ccxt
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
from loguru import logger
from dotenv import load_dotenv
try:
    from .volume_analysis import VolumeAnalysisEngine, VolumeSpike, CVDData
    from .technical_indicators import TechnicalAnalysisService, TechnicalIndicators
    from .oi_analysis import OIAnalysisService
except ImportError:
    # For direct execution
    from volume_analysis import VolumeAnalysisEngine, VolumeSpike, CVDData
    from technical_indicators import TechnicalAnalysisService, TechnicalIndicators
    from oi_analysis import OIAnalysisService

load_dotenv()

# Symbol Harmonization System for 5 Exchanges
EXCHANGE_SYMBOL_MAPPING = {
    'binance': {
        'linear_usdt': lambda base: f"{base}USDT",
        'linear_usdc': lambda base: f"{base}USDC", 
        'inverse': lambda base: f"{base}USD_PERP"
    },
    'bybit': {
        'linear_usdt': lambda base: f"{base}USDT",
        'linear_usdc': lambda base: f"{base}USDC",
        'inverse': lambda base: f"{base}USD"
    },
    'okx': {
        'linear_usdt': lambda base: f"{base}-USDT-SWAP",
        'linear_usdc': lambda base: f"{base}-USDC-SWAP",
        'inverse': lambda base: f"{base}-USD-SWAP"
    },
    'gateio': {
        'linear_usdt': lambda base: f"{base}_USDT",
        'linear_usdc': lambda base: f"{base}_USDC",
        'inverse': lambda base: f"{base}_USD"
    },
    'bitget': {
        'linear_usdt': lambda base: f"{base}USDT_UMCBL",
        'linear_usdc': lambda base: f"{base}USDC_UMCBL",
        'inverse': lambda base: f"{base}USD_DMCBL"
    }
}

class SymbolHarmonizer:
    """Unified symbol mapping across all 5 exchanges"""
    
    @staticmethod
    def get_exchange_symbol(base_symbol: str, exchange: str, market_type: str) -> str:
        """Convert base symbol to exchange-specific format"""
        # Extract just the base token (e.g., BTC from BTC/USDT)
        if '/' in base_symbol:
            base_token = base_symbol.split('/')[0].upper()
        else:
            # Remove common suffixes if present
            base_token = base_symbol.upper()
            for suffix in ['USDT', 'USDC', 'USD']:
                if base_token.endswith(suffix):
                    base_token = base_token[:-len(suffix)]
                    break
        
        if exchange not in EXCHANGE_SYMBOL_MAPPING:
            raise ValueError(f"Unsupported exchange: {exchange}")
        
        if market_type not in EXCHANGE_SYMBOL_MAPPING[exchange]:
            raise ValueError(f"Unsupported market type '{market_type}' for {exchange}")
        
        return EXCHANGE_SYMBOL_MAPPING[exchange][market_type](base_token)
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Normalize symbol to standard format (BTC/USDT)"""
        # Remove exchange-specific suffixes and convert to standard format
        symbol = symbol.upper()
        
        # Handle different formats
        if '_UMCBL' in symbol or '_DMCBL' in symbol:
            # Bitget format
            symbol = symbol.replace('_UMCBL', '').replace('_DMCBL', '')
        elif '-SWAP' in symbol:
            # OKX format
            symbol = symbol.replace('-SWAP', '')
        elif '_' in symbol:
            # Gate.io format
            symbol = symbol.replace('_', '/')
        elif 'USD_PERP' in symbol:
            # Binance inverse format
            symbol = symbol.replace('USD_PERP', 'USD')
        
        # Convert to standard format
        if '/' not in symbol and '-' not in symbol:
            # Handle formats like BTCUSDT -> BTC/USDT
            for quote in ['USDT', 'USDC', 'USD']:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    return f"{base}/{quote}"
        elif '-' in symbol:
            # Handle formats like BTC-USDT -> BTC/USDT
            symbol = symbol.replace('-', '/')
        
        return symbol
    
    @staticmethod
    def get_all_exchange_symbols(base_symbol: str) -> Dict[str, Dict[str, str]]:
        """Get all exchange symbols for a base symbol"""
        # Extract just the base token (e.g., BTC from BTC/USDT)
        if '/' in base_symbol:
            base_token = base_symbol.split('/')[0].upper()
        else:
            # Remove common suffixes if present
            base_token = base_symbol.upper()
            for suffix in ['USDT', 'USDC', 'USD']:
                if base_token.endswith(suffix):
                    base_token = base_token[:-len(suffix)]
                    break
        
        result = {}
        for exchange, mappings in EXCHANGE_SYMBOL_MAPPING.items():
            result[exchange] = {}
            for market_type, mapper in mappings.items():
                result[exchange][market_type] = mapper(base_token)
        
        return result

class MarketCapRanking:
    """Smart ranking system using known market cap order and trading data"""
    
    # REMOVED: Hardcoded market cap rankings to comply with real data requirements
    # All rankings now based on real trading volume data only
    
    @classmethod
    def get_ranking_score(cls, symbol: str, price: float, volume_24h: float) -> float:
        """
        Calculate ranking score based ONLY on real trading activity
        Removed synthetic market cap rankings to comply with real data requirements
        """
        # REMOVED: Hardcoded MARKET_CAP_RANKING to comply with real data requirements
        # Use ONLY real trading volume and price data for ranking
        volume_usd = volume_24h * price
        
        # Volume-based ranking using real market data only
        if volume_usd > 0:
            # Ranking based purely on USD trading volume (real data)
            return volume_usd / 1e6  # Convert to millions for scoring
        else:
            return 0.1  # Minimum score for zero volume
    
    @classmethod  
    def get_estimated_market_cap(cls, symbol: str, price: float) -> Optional[float]:
        """
        Real-time market cap data not available
        Removed hardcoded estimates to comply with real data requirements
        """
        # REMOVED: All hardcoded market cap estimates to comply with real data requirements
        # TODO: Integrate CoinGecko API for real-time market cap data
        return None  # Don't provide synthetic/fake market cap data


@dataclass
class PriceData:
    symbol: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    market_type: str = "spot"  # "spot" or "perp"
    market_cap: Optional[float] = None  # Real market cap from CoinGecko
    # Enhanced 15m data
    volume_15m: Optional[float] = None
    change_15m: Optional[float] = None
    delta_24h: Optional[float] = None
    delta_15m: Optional[float] = None
    atr_24h: Optional[float] = None
    atr_15m: Optional[float] = None

@dataclass
class PerpData:
    symbol: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    funding_rate_change: Optional[float] = None
    market_cap: Optional[float] = None  # Real market cap from CoinGecko
    # Enhanced 15m data
    volume_15m: Optional[float] = None
    change_15m: Optional[float] = None
    delta_24h: Optional[float] = None
    delta_15m: Optional[float] = None
    atr_24h: Optional[float] = None
    atr_15m: Optional[float] = None
    open_interest_15m: Optional[float] = None  # 15m OI calculation based on current OI

@dataclass
class CombinedPriceData:
    base_symbol: str
    spot: Optional[PriceData] = None
    perp: Optional[PerpData] = None
    timestamp: datetime = None
    spot_exchange: str = "binance"
    perp_exchange: str = "binance_futures"

@dataclass
class PositionData:
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    percentage: float

class ExchangeManager:
    def __init__(self):
        self.exchanges = {}
        # Will be initialized in async context
    
    async def _init_exchanges(self):
        # Always add Binance for public data (no API keys needed for price data)
        self.exchanges['binance'] = ccxt.binance({
            'enableRateLimit': True,
        })
        
        # Add Binance USD-M Futures for perpetual contracts
        self.exchanges['binance_futures'] = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        })
        
        # Add authenticated exchanges if API keys are provided
        if os.getenv('BINANCE_API_KEY'):
            self.exchanges['binance_auth'] = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
                'enableRateLimit': True,
            })
            
            self.exchanges['binance_futures_auth'] = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures market
                }
            })
        
        # Bybit public data
        self.exchanges['bybit'] = ccxt.bybit({
            'enableRateLimit': True,
        })
        
        if os.getenv('BYBIT_API_KEY'):
            self.exchanges['bybit_auth'] = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_SECRET_KEY'),
                'sandbox': os.getenv('BYBIT_TESTNET', 'false').lower() == 'true',
                'enableRateLimit': True,
            })
        
        logger.info(f"Initialized exchanges: {list(self.exchanges.keys())}")
    
    async def get_price(self, symbol: str, exchange: str = None) -> PriceData:
        """Get current price for a symbol"""
        try:
            # Use first available exchange if none specified
            if exchange is None:
                exchange = next(iter(self.exchanges.keys()))
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            ticker = await ex.fetch_ticker(symbol)
            
            return PriceData(
                symbol=symbol,
                price=ticker['last'],
                timestamp=datetime.now(),
                volume_24h=ticker.get('baseVolume'),
                change_24h=ticker.get('percentage')
            )
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            raise
    
    async def get_balance(self, exchange: str = None) -> Dict[str, float]:
        """Get account balance"""
        try:
            if exchange is None:
                exchange = next(iter(self.exchanges.keys()))
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            balance = await ex.fetch_balance()
            
            # Return only non-zero balances
            return {
                asset: info['free'] + info['used'] 
                for asset, info in balance.items() 
                if isinstance(info, dict) and (info.get('free', 0) + info.get('used', 0)) > 0
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    async def get_positions(self, exchange: str = None) -> list[PositionData]:
        """Get open positions"""
        try:
            if exchange is None:
                exchange = next(iter(self.exchanges.keys()))
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            positions = await ex.fetch_positions()
            
            # Filter only open positions
            open_positions = []
            for pos in positions:
                if pos['contracts'] > 0:  # Open position
                    open_positions.append(PositionData(
                        symbol=pos['symbol'],
                        side=pos['side'],
                        size=pos['contracts'],
                        entry_price=pos['entryPrice'],
                        mark_price=pos['markPrice'],
                        unrealized_pnl=pos['unrealizedPnl'],
                        percentage=pos['percentage']
                    ))
            
            return open_positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise
    
    async def get_total_pnl(self, exchange: str = None) -> Dict[str, float]:
        """Get total PNL summary"""
        try:
            positions = await self.get_positions(exchange)
            
            total_unrealized = sum(pos.unrealized_pnl for pos in positions)
            total_percentage = sum(pos.percentage for pos in positions) / len(positions) if positions else 0
            
            return {
                'total_unrealized_pnl': total_unrealized,
                'average_percentage': total_percentage,
                'position_count': len(positions)
            }
        except Exception as e:
            logger.error(f"Error calculating total PNL: {e}")
            raise
    
    async def get_combined_price(self, base_symbol: str, exchange: str = None) -> CombinedPriceData:
        """Get both spot and perpetual prices for a symbol with enhanced 15m data"""
        try:
            if exchange is None:
                exchange = next(iter(self.exchanges.keys()))
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            base_symbol = base_symbol.upper().replace('-', '/')
            
            # Try to get spot price with enhanced data
            spot_data = None
            try:
                spot_symbol = f"{base_symbol}"
                ticker = await ex.fetch_ticker(spot_symbol)
                
                # Get 15m candles for enhanced calculations
                candles_15m = await self._fetch_15m_data(ex, spot_symbol)
                volume_15m, change_15m, delta_24h, delta_15m, atr_24h, atr_15m = await self._calculate_enhanced_metrics(
                    candles_15m, ticker.get('baseVolume', 0), ex, spot_symbol
                )
                logger.info(f"✅ Enhanced spot metrics: vol_15m={volume_15m}, change_15m={change_15m}")
                
                spot_data = PriceData(
                    symbol=spot_symbol,
                    price=ticker['last'],
                    timestamp=datetime.now(),
                    volume_24h=ticker.get('baseVolume'),
                    change_24h=ticker.get('percentage'),
                    market_type="spot",
                    volume_15m=volume_15m,
                    change_15m=change_15m,
                    delta_24h=delta_24h,
                    delta_15m=delta_15m,
                    atr_24h=atr_24h,
                    atr_15m=atr_15m
                )
            except Exception as e:
                logger.warning(f"Could not fetch spot data for {base_symbol}: {e}")
            
            # Try to get perp price with OI and funding and enhanced data
            perp_data = None
            try:
                # Use futures exchange for perp data
                futures_ex = self.exchanges.get('binance_futures')
                if futures_ex:
                    # Try different perp symbol formats
                    perp_symbols = [f"{base_symbol}:USDT", f"{base_symbol}/USDT:USDT"]
                    
                    for perp_symbol in perp_symbols:
                        try:
                            ticker = await futures_ex.fetch_ticker(perp_symbol)
                            
                            # Try to get funding rate
                            funding_rate = None
                            funding_change = None
                            try:
                                funding_info = await futures_ex.fetch_funding_rate(perp_symbol)
                                funding_rate = funding_info.get('fundingRate')
                                funding_change = 0.0  # Would need historical data for accurate calculation
                            except Exception:
                                pass
                            
                            # Try to get open interest (current)
                            open_interest = None
                            try:
                                oi_info = await futures_ex.fetch_open_interest(perp_symbol)
                                open_interest = oi_info.get('openInterestAmount')
                            except Exception:
                                pass
                            
                            # Get 15m candles for enhanced calculations
                            candles_15m = await self._fetch_15m_data(futures_ex, perp_symbol)
                            volume_15m, change_15m, delta_24h, delta_15m, atr_24h, atr_15m = await self._calculate_enhanced_metrics(
                                candles_15m, ticker.get('baseVolume', 0), ex, perp_symbol
                            )
                            logger.info(f"✅ Enhanced perp metrics: vol_15m={volume_15m}, change_15m={change_15m}")
                            
                            # Calculate 15m OI based on current OI and volume activity
                            open_interest_15m = self._calculate_oi_15m(open_interest, volume_15m, ticker.get('baseVolume', 0))
                            
                            perp_data = PerpData(
                                symbol=perp_symbol,
                                price=ticker['last'],
                                timestamp=datetime.now(),
                                volume_24h=ticker.get('baseVolume'),
                                change_24h=ticker.get('percentage'),
                                open_interest=open_interest,
                                funding_rate=funding_rate,
                                funding_rate_change=funding_change,
                                volume_15m=volume_15m,
                                change_15m=change_15m,
                                delta_24h=delta_24h,
                                delta_15m=delta_15m,
                                atr_24h=atr_24h,
                                atr_15m=atr_15m,
                                open_interest_15m=open_interest_15m
                            )
                            logger.info(f"🔍 DEBUG: Created PerpData with delta_15m={delta_15m}, delta_24h={delta_24h}")
                            break
                        except Exception:
                            continue
                        
            except Exception as e:
                logger.warning(f"Could not fetch perp data for {base_symbol}: {e}")
            
            return CombinedPriceData(
                base_symbol=base_symbol,
                spot=spot_data,
                perp=perp_data,
                timestamp=datetime.now(),
                spot_exchange="Binance",
                perp_exchange="Binance Futures"
            )
            
        except Exception as e:
            logger.error(f"Error fetching combined price for {base_symbol}: {e}")
            raise
    
    async def _fetch_15m_data(self, exchange, symbol: str):
        """Fetch 15-minute OHLCV data for enhanced calculations"""
        try:
            # Fetch last 100 periods (25 hours of 15m data) for calculations
            # Note: Using ccxt.pro so fetch_ohlcv is async
            candles = await exchange.fetch_ohlcv(symbol, '15m', limit=100)
            logger.info(f"✅ Fetched {len(candles)} 15m candles for {symbol}")
            return candles
        except Exception as e:
            logger.warning(f"Could not fetch 15m data for {symbol}: {e}")
            return []
    
    async def _calculate_enhanced_metrics(self, candles_15m: list, volume_24h: float, exchange, symbol: str):
        """Calculate enhanced metrics from 15m candlestick data"""
        try:
            if not candles_15m or len(candles_15m) < 2:
                return None, None, None, None, None, None
            
            # Extract data from candles [timestamp, open, high, low, close, volume]
            latest_candle = candles_15m[-1]
            previous_candle = candles_15m[-2] if len(candles_15m) > 1 else latest_candle
            
            # 15m volume (latest candle volume)
            volume_15m = latest_candle[5] if len(latest_candle) > 5 else 0
            
            # 15m price change
            if len(candles_15m) > 1:
                current_price = latest_candle[4]  # Close price
                previous_price = previous_candle[4]  # Previous close price
                change_15m = ((current_price - previous_price) / previous_price) * 100 if previous_price > 0 else 0
            else:
                change_15m = 0
            
            # Delta calculations (volume-based momentum)
            delta_24h = await self._calculate_volume_delta(candles_15m, 96)  # 96 * 15m = 24h
            delta_15m = await self._calculate_volume_delta(candles_15m, 1)   # Last 1 period
            
            # ATR calculations (Average True Range)
            # ATR 24h: Use 6 periods of 4h data for recent daily volatility
            atr_24h = await self._calculate_atr_24h(exchange, symbol)
            # ATR 15m: Use 7 periods of 15m data for current session volatility
            atr_15m = await self._calculate_atr(candles_15m, period=7)
            
            return volume_15m, change_15m, delta_24h, delta_15m, atr_24h, atr_15m
            
        except Exception as e:
            logger.warning(f"Error calculating enhanced metrics: {e}")
            return None, None, None, None, None, None
    
    async def _calculate_volume_delta(self, candles: list, periods: int):
        """Calculate volume delta using price-weighted volume analysis"""
        try:
            if not candles or len(candles) < periods:
                return 0
            
            # Take the last 'periods' candles
            relevant_candles = candles[-periods:]
            
            total_delta = 0
            for candle in relevant_candles:
                if len(candle) >= 6:
                    open_price = float(candle[1])
                    high_price = float(candle[2])
                    low_price = float(candle[3])
                    close_price = float(candle[4])
                    volume = float(candle[5])
                    
                    # Calculate buy/sell volume approximation using price action
                    # Method: Use close position relative to high-low range
                    # Higher close in range = more buying pressure
                    if high_price != low_price:
                        # Close position in range (0 to 1)
                        close_position = (close_price - low_price) / (high_price - low_price)
                        
                        # Split volume based on close position
                        # close_position > 0.5 means more buying, < 0.5 means more selling
                        buy_volume = volume * close_position
                        sell_volume = volume * (1 - close_position)
                        
                        candle_delta = buy_volume - sell_volume
                    else:
                        # No price movement, assume neutral
                        candle_delta = 0
                    
                    total_delta += candle_delta
            
            return total_delta
            
        except Exception as e:
            logger.warning(f"Error calculating volume delta: {e}")
            return 0
    
    async def _calculate_atr_24h(self, exchange, symbol):
        """Calculate 24h ATR using 6 periods of 4h data for recent daily volatility"""
        try:
            # Fetch 4-hour candlestick data (last 10 periods for buffer)
            candles_4h = await exchange.fetch_ohlcv(symbol, '4h', limit=10)
            if not candles_4h or len(candles_4h) < 7:  # Need at least 7 for 6 periods
                logger.warning(f"Insufficient 4h data for ATR calculation: {len(candles_4h) if candles_4h else 0} candles")
                return None
            
            return await self._calculate_atr(candles_4h, period=6)
            
        except Exception as e:
            logger.warning(f"Error calculating 24h ATR: {e}")
            return None
    
    async def _calculate_atr(self, candles: list, period: int = 14):
        """Calculate Average True Range (ATR)"""
        try:
            if not candles or len(candles) < period + 1:
                return None
            
            true_ranges = []
            
            # Calculate True Range for each candle
            for i in range(1, min(len(candles), period + 1)):
                current = candles[-(i)]
                previous = candles[-(i+1)]
                
                if len(current) >= 5 and len(previous) >= 5:
                    high = current[2]
                    low = current[3]
                    prev_close = previous[4]
                    
                    # True Range = max(high-low, high-prev_close, prev_close-low)
                    tr1 = high - low
                    tr2 = abs(high - prev_close)
                    tr3 = abs(prev_close - low)
                    
                    true_range = max(tr1, tr2, tr3)
                    true_ranges.append(true_range)
            
            # Calculate ATR as average of true ranges
            if true_ranges:
                atr = sum(true_ranges) / len(true_ranges)
                return atr
            
            return None
            
        except Exception as e:
            logger.warning(f"Error calculating ATR: {e}")
            return None
    
    def _calculate_oi_15m(self, open_interest_24h: Optional[float], volume_15m: Optional[float], volume_24h: Optional[float]) -> Optional[float]:
        """Calculate 15m OI based on current OI and volume activity ratio"""
        try:
            if not open_interest_24h or open_interest_24h <= 0:
                return None
            
            # If we don't have 15m volume data, return a fraction of 24h OI
            if not volume_15m or not volume_24h or volume_24h <= 0:
                # Return approximately 1/96th of 24h OI (24h / 15m = 96 periods)
                return open_interest_24h / 96
            
            # Calculate OI based on volume activity ratio
            # This is an approximation since OI is typically only available as current value
            volume_ratio = volume_15m / volume_24h
            
            # Calculate 15m OI as a fraction of 24h OI weighted by volume activity
            # We use a combination of time-based fraction and volume-based weighting
            base_fraction = 1 / 96  # 24h / 15m = 96 periods
            volume_weight = min(volume_ratio * 96, 3.0)  # Cap at 3x to avoid extreme values
            
            oi_15m = open_interest_24h * base_fraction * volume_weight
            
            # Ensure result is reasonable (between 0.1% and 20% of 24h OI)
            min_oi = open_interest_24h * 0.001
            max_oi = open_interest_24h * 0.2
            
            return max(min_oi, min(max_oi, oi_15m))
            
        except Exception as e:
            logger.warning(f"Error calculating 15m OI: {e}")
            return None
    
    async def get_top_symbols(self, market_type: str = "spot", limit: int = 10, exchange: str = None) -> list:
        """Get top symbols by volume"""
        try:
            # Choose the right exchange based on market type
            if exchange is None:
                if market_type == "perp":
                    exchange = 'binance_futures'  # Use futures exchange for perpetuals
                else:
                    exchange = 'binance'  # Use spot exchange for spot markets
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            
            # Fetch all tickers
            tickers = await ex.fetch_tickers()
            
            # Filter by market type 
            filtered_tickers = []
            for symbol, ticker in tickers.items():
                if market_type == "spot":
                    # Filter for major crypto spot markets (exclude fiat and test tokens)
                    if ('/' in symbol and ':' not in symbol and symbol.endswith('/USDT') and 
                        not any(x in symbol for x in ['UP', 'DOWN', 'BULL', 'BEAR', 'TRY', 'COP', 'ARS', 'UAH', 'RUB']) and
                        not symbol.startswith('USDT/')):
                        filtered_tickers.append((symbol, ticker))
                elif market_type == "perp":
                    # Filter for perpetual contracts from Binance futures
                    # Format is: BTC/USDT:USDT for USD-M perpetual futures
                    if (symbol.endswith(':USDT') and '/USDT:' in symbol and 
                        ticker.get('baseVolume', 0) and ticker.get('last') and
                        not any(x in symbol for x in ['UP', 'DOWN', 'BULL', 'BEAR', '_', '-'])):
                        filtered_tickers.append((symbol, ticker))
            
            # Sort by smart ranking (known market cap order + trading activity)
            def get_ranking_value(item):
                symbol, ticker = item
                price = ticker.get('last', 0) or 0
                volume = ticker.get('baseVolume', 0) or 0
                return MarketCapRanking.get_ranking_score(symbol, price, volume)
            
            sorted_tickers = sorted(filtered_tickers, key=get_ranking_value, reverse=True)
            
            # Return top N with additional data for perps
            top_symbols = []
            for symbol, ticker in sorted_tickers[:limit]:
                if market_type == "perp":
                    # Try to get OI and funding rate for perps
                    try:
                        funding_info = await ex.fetch_funding_rate(symbol)
                        funding_rate = funding_info.get('fundingRate')
                    except Exception:
                        funding_rate = None
                    
                    try:
                        oi_info = await ex.fetch_open_interest(symbol)
                        open_interest = oi_info.get('openInterestAmount')
                    except Exception:
                        open_interest = None
                    
                    # Get estimated market cap for this perp symbol
                    estimated_market_cap = MarketCapRanking.get_estimated_market_cap(symbol, ticker['last'])
                    
                    perp_data = PerpData(
                        symbol=symbol,
                        price=ticker['last'],
                        timestamp=datetime.now(),
                        volume_24h=ticker.get('baseVolume'),
                        change_24h=ticker.get('percentage'),
                        open_interest=open_interest,
                        funding_rate=funding_rate,
                        funding_rate_change=0.0,
                        market_cap=estimated_market_cap
                    )
                    top_symbols.append(perp_data)
                else:
                    # Get estimated market cap for this symbol
                    estimated_market_cap = MarketCapRanking.get_estimated_market_cap(symbol, ticker['last'])
                    
                    price_data = PriceData(
                        symbol=symbol,
                        price=ticker['last'],
                        timestamp=datetime.now(),
                        volume_24h=ticker.get('baseVolume'),
                        change_24h=ticker.get('percentage'),
                        market_type=market_type,
                        market_cap=estimated_market_cap
                    )
                    top_symbols.append(price_data)
            
            return top_symbols
            
        except Exception as e:
            logger.error(f"Error fetching top {market_type} symbols: {e}")
            raise

class MarketDataService:
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.volume_engine = None  # Will be initialized after exchange_manager
        self.technical_service = None  # Will be initialized after exchange_manager
        self.oi_service = None  # Will be initialized after exchange_manager
        self._initialized = False
        logger.info("Market Data Service created")
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            await self.exchange_manager._init_exchanges()
            self.volume_engine = VolumeAnalysisEngine(self.exchange_manager)
            self.technical_service = TechnicalAnalysisService(self.exchange_manager)
            self.oi_service = OIAnalysisService(self.exchange_manager)
            self._initialized = True
            logger.info("Market Data Service initialized")
    
    async def handle_price_request(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        """Handle price request from Telegram bot"""
        try:
            await self.initialize()
            price_data = await self.exchange_manager.get_price(symbol, exchange)
            return {
                'success': True,
                'data': {
                    'symbol': price_data.symbol,
                    'price': price_data.price,
                    'volume_24h': price_data.volume_24h,
                    'change_24h': price_data.change_24h,
                    'timestamp': price_data.timestamp.isoformat()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_balance_request(self, exchange: str = None) -> Dict[str, Any]:
        """Handle balance request from Telegram bot"""
        try:
            await self.initialize()
            balance = await self.exchange_manager.get_balance(exchange)
            return {
                'success': True,
                'data': balance
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_positions_request(self, exchange: str = None) -> Dict[str, Any]:
        """Handle positions request from Telegram bot"""
        try:
            await self.initialize()
            positions = await self.exchange_manager.get_positions(exchange)
            return {
                'success': True,
                'data': [
                    {
                        'symbol': pos.symbol,
                        'side': pos.side,
                        'size': pos.size,
                        'entry_price': pos.entry_price,
                        'mark_price': pos.mark_price,
                        'unrealized_pnl': pos.unrealized_pnl,
                        'percentage': pos.percentage
                    } for pos in positions
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_pnl_request(self, exchange: str = None) -> Dict[str, Any]:
        """Handle PNL request from Telegram bot"""
        try:
            await self.initialize()
            pnl_data = await self.exchange_manager.get_total_pnl(exchange)
            return {
                'success': True,
                'data': pnl_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_combined_price_request(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        """Handle combined spot + perp price request"""
        try:
            await self.initialize()
            combined_data = await self.exchange_manager.get_combined_price(symbol, exchange)
            
            result = {
                'base_symbol': combined_data.base_symbol,
                'timestamp': combined_data.timestamp.isoformat(),
                'spot_exchange': combined_data.spot_exchange,
                'perp_exchange': combined_data.perp_exchange
            }
            
            if combined_data.spot:
                result['spot'] = {
                    'symbol': combined_data.spot.symbol,
                    'price': combined_data.spot.price,
                    'volume_24h': combined_data.spot.volume_24h,
                    'change_24h': combined_data.spot.change_24h,
                    'market_type': 'spot',
                    'volume_15m': getattr(combined_data.spot, 'volume_15m', None),
                    'change_15m': getattr(combined_data.spot, 'change_15m', None),
                    'delta_24h': getattr(combined_data.spot, 'delta_24h', None),
                    'delta_15m': getattr(combined_data.spot, 'delta_15m', None),
                    'atr_24h': getattr(combined_data.spot, 'atr_24h', None),
                    'atr_15m': getattr(combined_data.spot, 'atr_15m', None)
                }
            
            if combined_data.perp:
                result['perp'] = {
                    'symbol': combined_data.perp.symbol,
                    'price': combined_data.perp.price,
                    'volume_24h': combined_data.perp.volume_24h,
                    'change_24h': combined_data.perp.change_24h,
                    'open_interest': combined_data.perp.open_interest,
                    'funding_rate': combined_data.perp.funding_rate,
                    'funding_rate_change': combined_data.perp.funding_rate_change,
                    'market_type': 'perp',
                    'volume_15m': getattr(combined_data.perp, 'volume_15m', None),
                    'change_15m': getattr(combined_data.perp, 'change_15m', None),
                    'delta_24h': getattr(combined_data.perp, 'delta_24h', None),
                    'delta_15m': getattr(combined_data.perp, 'delta_15m', None),
                    'atr_24h': getattr(combined_data.perp, 'atr_24h', None),
                    'atr_15m': getattr(combined_data.perp, 'atr_15m', None),
                    'open_interest_15m': getattr(combined_data.perp, 'open_interest_15m', None)
                }
            
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_top_symbols_request(self, market_type: str = "spot", limit: int = 10, exchange: str = None) -> Dict[str, Any]:
        """Handle top symbols request"""
        try:
            await self.initialize()
            top_symbols = await self.exchange_manager.get_top_symbols(market_type, limit, exchange)
            
            result = []
            for symbol_data in top_symbols:
                if hasattr(symbol_data, 'open_interest'):  # PerpData
                    result.append({
                        'symbol': symbol_data.symbol,
                        'price': symbol_data.price,
                        'volume_24h': symbol_data.volume_24h,
                        'change_24h': symbol_data.change_24h,
                        'open_interest': symbol_data.open_interest,
                        'funding_rate': symbol_data.funding_rate,
                        'market_cap': symbol_data.market_cap,
                        'market_type': 'perp'
                    })
                else:  # PriceData
                    result.append({
                        'symbol': symbol_data.symbol,
                        'price': symbol_data.price,
                        'volume_24h': symbol_data.volume_24h,
                        'change_24h': symbol_data.change_24h,
                        'market_cap': symbol_data.market_cap,
                        'market_type': symbol_data.market_type
                    })
            
            return {
                'success': True,
                'data': {
                    'market_type': market_type,
                    'symbols': result
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_volume_spike_request(self, symbol: str, timeframe: str = '15m', exchange: str = None) -> Dict[str, Any]:
        """Handle volume spike detection request"""
        try:
            await self.initialize()
            spike = await self.volume_engine.detect_volume_spike(symbol, timeframe, exchange=exchange)
            
            return {
                'success': True,
                'data': {
                    'symbol': spike.symbol,
                    'timeframe': spike.timeframe,
                    'current_volume': spike.current_volume,
                    'average_volume': spike.average_volume,
                    'spike_percentage': spike.spike_percentage,
                    'spike_level': spike.spike_level,
                    'volume_usd': spike.volume_usd,
                    'is_significant': bool(spike.is_significant),
                    'timestamp': spike.timestamp.isoformat()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_cvd_request(self, symbol: str, timeframe: str = '15m', exchange: str = None) -> Dict[str, Any]:
        """Handle CVD calculation request"""
        try:
            await self.initialize()
            cvd = await self.volume_engine.calculate_cvd(symbol, timeframe, exchange=exchange)
            
            return {
                'success': True,
                'data': {
                    'symbol': cvd.symbol,
                    'timeframe': cvd.timeframe,
                    'current_cvd': cvd.current_cvd,
                    'cvd_change_24h': cvd.cvd_change_24h,
                    'cvd_trend': cvd.cvd_trend,
                    'divergence_detected': bool(cvd.divergence_detected),
                    'price_trend': cvd.price_trend,
                    'timestamp': cvd.timestamp.isoformat()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_volume_scan_request(self, timeframe: str = '15m', min_spike: float = 200) -> Dict[str, Any]:
        """Handle volume spike scanning request"""
        try:
            await self.initialize()
            spikes = await self.volume_engine.scan_volume_spikes(timeframe, min_spike)
            
            spike_data = []
            for spike in spikes:
                spike_data.append({
                    'symbol': spike.symbol,
                    'spike_percentage': spike.spike_percentage,
                    'spike_level': spike.spike_level,
                    'current_volume': spike.current_volume,
                    'volume_usd': spike.volume_usd,
                    'is_significant': bool(spike.is_significant)
                })
            
            return {
                'success': True,
                'data': {
                    'timeframe': timeframe,
                    'min_spike_threshold': min_spike,
                    'spikes_found': len(spike_data),
                    'spikes': spike_data
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_comprehensive_analysis_request(self, symbol: str, timeframe: str = '15m', exchange: str = None) -> Dict[str, Any]:
        """Handle comprehensive market analysis request"""
        try:
            await self.initialize()
            
            # Gather all data concurrently for better performance
            import asyncio
            
            # Run all analysis in parallel
            tasks = [
                self.exchange_manager.get_combined_price(symbol, exchange),
                self.volume_engine.detect_volume_spike(symbol, timeframe, exchange=exchange),
                self.volume_engine.calculate_cvd(symbol, timeframe, exchange=exchange),
                self.technical_service.get_technical_indicators(symbol, timeframe, exchange)
            ]
            
            combined_price, volume_spike, cvd_data, tech_indicators = await asyncio.gather(*tasks)
            
            # Analyze market sentiment and control
            sentiment_analysis = self._analyze_market_sentiment(
                combined_price, volume_spike, cvd_data, tech_indicators
            )
            
            # Format the response exactly as the Telegram bot expects
            price_data = self._format_price_data(combined_price)
            logger.info(f"🔍 DEBUG: price_data keys: {list(price_data.keys())}")
            
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': datetime.now().isoformat(),
                    
                    # Price data (formatted for Telegram bot compatibility)
                    'price_data': {
                        'current_price': float(price_data.get('current_price', 0)),
                        'change_24h': float(price_data.get('change_24h', 0)),
                        'volume_24h': float(price_data.get('volume_24h', 0)),
                        'volume_24h_usd': float(price_data.get('volume_24h_usd', 0)),
                        'market_type': price_data.get('market_type', 'spot'),
                        'funding_rate': price_data.get('funding_rate', 0),
                        # Enhanced 15m metrics
                        'volume_15m': price_data.get('volume_15m'),
                        'change_15m': price_data.get('change_15m'),
                        'delta_15m': price_data.get('delta_15m'),
                        'delta_24h': price_data.get('delta_24h'),
                        'atr_15m': price_data.get('atr_15m'),
                        'atr_24h': price_data.get('atr_24h')
                    },
                    
                    # Volume analysis (formatted for Telegram bot compatibility)
                    'volume_analysis': {
                        'current_volume': float(volume_spike.current_volume),
                        'volume_usd': float(volume_spike.volume_usd),
                        'spike_level': volume_spike.spike_level,
                        'spike_percentage': float(volume_spike.spike_percentage),
                        'is_significant': bool(volume_spike.is_significant),
                        'relative_volume': float(volume_spike.current_volume / volume_spike.average_volume) if volume_spike.average_volume > 0 else 1.0
                    },
                    
                    # CVD analysis (formatted for Telegram bot compatibility)
                    'cvd_analysis': {
                        'current_cvd': float(cvd_data.current_cvd),
                        'cvd_trend': cvd_data.cvd_trend,
                        'divergence_detected': bool(cvd_data.divergence_detected),
                        'cvd_change_24h': float(cvd_data.cvd_change_24h)
                    },
                    
                    # Technical indicators (formatted for Telegram bot compatibility)
                    'technical_indicators': {
                        'rsi_14': float(tech_indicators.rsi_14) if tech_indicators.rsi_14 is not None else 50.0,
                        'vwap': float(tech_indicators.vwap) if tech_indicators.vwap is not None else float(price_data.get('current_price', 0)),
                        'atr_14': float(tech_indicators.atr_14) if tech_indicators.atr_14 is not None else 0.0,
                        'volatility_24h': float(tech_indicators.volatility_24h) if tech_indicators.volatility_24h is not None else 0.0,
                        'bb_upper': float(tech_indicators.bb_upper) if tech_indicators.bb_upper is not None else 0.0,
                        'bb_middle': float(tech_indicators.bb_middle) if tech_indicators.bb_middle is not None else 0.0,
                        'bb_lower': float(tech_indicators.bb_lower) if tech_indicators.bb_lower is not None else 0.0
                    },
                    
                    # Market sentiment analysis (formatted for Telegram bot compatibility)
                    'market_sentiment': sentiment_analysis,
                    
                    # OI data (for perps) (formatted for Telegram bot compatibility)
                    'oi_data': self._extract_oi_data(combined_price)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_multi_oi_request(self, base_symbol: str) -> Dict[str, Any]:
        """Handle unified 13-market OI analysis request"""
        try:
            # Import the unified aggregator
            try:
                from .unified_oi_aggregator import UnifiedOIAggregator
            except ImportError:
                from unified_oi_aggregator import UnifiedOIAggregator
            
            # Extract base symbol (remove suffixes)
            clean_symbol = base_symbol.upper()
            for suffix in ['USDT', 'USDC', 'USD', '/USDT', '/USDC', '/USD', '-USDT', '-USDC', '-USD']:
                if clean_symbol.endswith(suffix):
                    clean_symbol = clean_symbol.replace(suffix, '')
                    break
            
            # Initialize unified aggregator
            aggregator = UnifiedOIAggregator()
            
            try:
                # Get unified data
                unified_result = await aggregator.get_unified_oi_data(clean_symbol)
                
                # Convert to API response format
                response = {
                    'success': True,
                    'base_symbol': unified_result.base_symbol,
                    'timestamp': unified_result.timestamp.isoformat(),
                    'total_markets': unified_result.total_markets,
                    'aggregated_oi': unified_result.aggregated_oi,
                    'exchange_breakdown': unified_result.exchange_breakdown,
                    'market_categories': unified_result.market_categories,
                    'validation_summary': unified_result.validation_summary
                }
                
                logger.info(f"✅ Unified OI analysis completed for {clean_symbol}: {unified_result.total_markets} markets, {unified_result.aggregated_oi['total_tokens']:,.0f} {clean_symbol}")
                
                return response
                
            finally:
                await aggregator.close()
            
        except Exception as e:
            logger.error(f"Error in unified OI analysis for {base_symbol}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'base_symbol': base_symbol
            }
    
    async def handle_test_exchange_oi_request(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Handle test exchange OI request for validation"""
        try:
            await self.initialize()
            
            # Normalize symbol format
            normalized_symbol = SymbolHarmonizer.normalize_symbol(symbol)
            if '/' not in normalized_symbol:
                normalized_symbol = f"{symbol}/USDT"  # Default to USDT pair
            
            # Get all exchange symbols for this base symbol
            all_symbols = SymbolHarmonizer.get_all_exchange_symbols(normalized_symbol)
            
            return {
                'success': True,
                'data': {
                    'exchange': exchange,
                    'base_symbol': symbol,
                    'normalized_symbol': normalized_symbol,
                    'exchange_symbols': all_symbols.get(exchange, {}),
                    'all_exchange_symbols': all_symbols
                }
            }
            
        except Exception as e:
            logger.error(f"Error in test exchange OI for {exchange}/{symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_price_data(self, combined_price: CombinedPriceData) -> Dict[str, Any]:
        """Format price data for analysis response"""
        if not combined_price:
            return {}
        
        # Use perp data if available, otherwise spot
        if combined_price.perp:
            price_data = combined_price.perp
            market_type = 'perp'
            logger.info(f"🔍 DEBUG: Perp data has delta_15m={getattr(price_data, 'delta_15m', 'MISSING')}, delta_24h={getattr(price_data, 'delta_24h', 'MISSING')}")
        elif combined_price.spot:
            price_data = combined_price.spot
            market_type = 'spot'
            logger.info(f"🔍 DEBUG: Spot data has delta_15m={getattr(price_data, 'delta_15m', 'MISSING')}, delta_24h={getattr(price_data, 'delta_24h', 'MISSING')}")
        else:
            return {}
        
        return {
            'current_price': float(price_data.price),
            'change_24h': float(price_data.change_24h or 0),
            'volume_24h': float(price_data.volume_24h or 0),
            'volume_24h_usd': float((price_data.volume_24h or 0) * price_data.price),
            'market_type': market_type,
            'funding_rate': float(price_data.funding_rate or 0) if hasattr(price_data, 'funding_rate') else None,
            # Enhanced metrics
            'volume_15m': float(price_data.volume_15m or 0) if hasattr(price_data, 'volume_15m') else None,
            'change_15m': float(price_data.change_15m or 0) if hasattr(price_data, 'change_15m') else None,
            'delta_24h': float(price_data.delta_24h or 0) if hasattr(price_data, 'delta_24h') else None,
            'delta_15m': float(price_data.delta_15m or 0) if hasattr(price_data, 'delta_15m') else None,
            'atr_24h': float(price_data.atr_24h or 0) if hasattr(price_data, 'atr_24h') else None,
            'atr_15m': float(price_data.atr_15m or 0) if hasattr(price_data, 'atr_15m') else None
        }
    
    def _extract_oi_data(self, combined_price: CombinedPriceData) -> Dict[str, Any]:
        """Extract Open Interest data for perpetuals"""
        if not combined_price or not combined_price.perp:
            return {}
        
        perp = combined_price.perp
        oi = perp.open_interest
        oi_15m = perp.open_interest_15m
        
        if not oi:
            return {}
        
        oi_usd = oi * perp.price
        oi_15m_usd = (oi_15m * perp.price) if oi_15m else None
        
        result = {
            'open_interest': float(oi),
            'open_interest_usd': float(oi_usd),
            'funding_rate': float(perp.funding_rate or 0)
        }
        
        # Add 15m OI data if available
        if oi_15m:
            result['open_interest_15m'] = float(oi_15m)
            result['open_interest_15m_usd'] = float(oi_15m_usd)
        
        return result
    
    def _analyze_market_sentiment(self, combined_price, volume_spike, cvd_data, tech_indicators) -> Dict[str, Any]:
        """Analyze overall market sentiment and control"""
        
        # Sentiment scoring components
        price_sentiment = 0  # -3 to +3
        volume_sentiment = 0  # -2 to +2
        cvd_sentiment = 0   # -3 to +3
        tech_sentiment = 0  # -2 to +2
        
        # Price sentiment (based on 24h change)
        if combined_price and (combined_price.perp or combined_price.spot):
            price_data = combined_price.perp or combined_price.spot
            change_24h = price_data.change_24h or 0
            
            if change_24h > 5:
                price_sentiment = 3
            elif change_24h > 2:
                price_sentiment = 2
            elif change_24h > 0:
                price_sentiment = 1
            elif change_24h > -2:
                price_sentiment = -1
            elif change_24h > -5:
                price_sentiment = -2
            else:
                price_sentiment = -3
        
        # Volume sentiment (based on spike level)
        volume_level = volume_spike.spike_level
        if volume_level == 'EXTREME':
            volume_sentiment = 2
        elif volume_level == 'HIGH':
            volume_sentiment = 1
        elif volume_level == 'MODERATE':
            volume_sentiment = 1
        else:
            volume_sentiment = 0
        
        # CVD sentiment (based on trend and change)
        if cvd_data.cvd_trend == 'BULLISH':
            cvd_sentiment = 2 if cvd_data.cvd_change_24h > 0 else 1
        elif cvd_data.cvd_trend == 'BEARISH':
            cvd_sentiment = -2 if cvd_data.cvd_change_24h < 0 else -1
        else:
            cvd_sentiment = 0
        
        # Add divergence penalty
        if cvd_data.divergence_detected:
            cvd_sentiment -= 1
        
        # Technical sentiment (RSI + volatility)
        if tech_indicators.rsi_14:
            if tech_indicators.rsi_14 > 70:
                tech_sentiment -= 1  # Overbought
            elif tech_indicators.rsi_14 < 30:
                tech_sentiment += 1  # Oversold
            elif tech_indicators.rsi_14 > 50:
                tech_sentiment += 1  # Bullish momentum
            else:
                tech_sentiment -= 1  # Bearish momentum
        
        # Overall sentiment calculation
        total_sentiment = price_sentiment + volume_sentiment + cvd_sentiment + tech_sentiment
        max_possible = 10  # 3+2+3+2
        sentiment_score = (total_sentiment / max_possible) * 100
        
        # Determine market control
        if sentiment_score > 30:
            control = "BULLS"
            control_strength = min(abs(sentiment_score), 100)
        elif sentiment_score < -30:
            control = "BEARS"
            control_strength = min(abs(sentiment_score), 100)
        else:
            control = "NEUTRAL"
            control_strength = 50
        
        # Aggression level based on volume and CVD alignment
        aggression = "LOW"
        if volume_spike.is_significant and abs(cvd_data.cvd_change_24h) > 1000:
            aggression = "HIGH"
        elif volume_spike.spike_level in ['HIGH', 'EXTREME'] or abs(cvd_data.cvd_change_24h) > 500:
            aggression = "MODERATE"
        
        return {
            'overall_sentiment': round(sentiment_score, 1),
            'market_control': control,
            'control_strength': round(control_strength, 1),
            'aggression_level': aggression,
            'divergence_warning': cvd_data.divergence_detected,
            'components': {
                'price_sentiment': price_sentiment,
                'volume_sentiment': volume_sentiment,
                'cvd_sentiment': cvd_sentiment,
                'tech_sentiment': tech_sentiment
            }
        }

# Simple HTTP server for inter-service communication
from aiohttp import web, ClientSession

async def create_app():
    app = web.Application()
    market_service = MarketDataService()
    
    async def price_handler(request):
        data = await request.json()
        symbol = data.get('symbol')
        exchange = data.get('exchange')
        result = await market_service.handle_price_request(symbol, exchange)
        return web.json_response(result)
    
    async def balance_handler(request):
        data = await request.json()
        exchange = data.get('exchange')
        result = await market_service.handle_balance_request(exchange)
        return web.json_response(result)
    
    async def positions_handler(request):
        data = await request.json()
        exchange = data.get('exchange')
        result = await market_service.handle_positions_request(exchange)
        return web.json_response(result)
    
    async def pnl_handler(request):
        data = await request.json()
        exchange = data.get('exchange')
        result = await market_service.handle_pnl_request(exchange)
        return web.json_response(result)
    
    async def health_handler(request):
        return web.json_response({'status': 'healthy', 'service': 'market-data'})
    
    async def combined_price_handler(request):
        data = await request.json()
        symbol = data.get('symbol')
        exchange = data.get('exchange')
        result = await market_service.handle_combined_price_request(symbol, exchange)
        return web.json_response(result)
    
    async def top_symbols_handler(request):
        data = await request.json()
        market_type = data.get('market_type', 'spot')
        limit = data.get('limit', 10)
        exchange = data.get('exchange')
        result = await market_service.handle_top_symbols_request(market_type, limit, exchange)
        return web.json_response(result)
    
    async def debug_tickers_handler(request):
        data = await request.json()
        market_type = data.get('market_type', 'spot')
        limit = data.get('limit', 10)
        
        try:
            await market_service.initialize()
            
            # Get raw ticker data for debugging from the appropriate exchange
            if market_type == "perp":
                exchange = 'binance_futures'  # USD-M futures
            else:
                exchange = 'binance'  # Spot
            
            if exchange not in market_service.exchange_manager.exchanges:
                return web.json_response({
                    'success': False,
                    'error': f'Exchange {exchange} not available'
                })
            
            ex = market_service.exchange_manager.exchanges[exchange]
            tickers = await ex.fetch_tickers()
            
            # Show raw sample data to understand ALL available fields
            sample_symbols = []
            count = 0
            for symbol, ticker in tickers.items():
                if count >= 10:  # Just first 10 for detailed analysis
                    break
                if 'BTC' in symbol or 'ETH' in symbol:  # Focus on major coins
                    sample_symbols.append({
                        'symbol': symbol,
                        'raw_ticker_data': ticker,  # Show ALL fields available
                        'exchange_used': exchange
                    })
                    count += 1
            
            return web.json_response({
                'success': True,
                'total_tickers': len(tickers),
                'market_type': market_type,
                'exchange_used': exchange,
                'sample_detailed_data': sample_symbols
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            })
    
    async def volume_spike_handler(request):
        data = await request.json()
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', '15m')
        exchange = data.get('exchange')
        result = await market_service.handle_volume_spike_request(symbol, timeframe, exchange)
        return web.json_response(result)
    
    async def cvd_handler(request):
        data = await request.json()
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', '15m')
        exchange = data.get('exchange')
        result = await market_service.handle_cvd_request(symbol, timeframe, exchange)
        return web.json_response(result)
    
    async def volume_scan_handler(request):
        data = await request.json()
        timeframe = data.get('timeframe', '15m')
        min_spike = data.get('min_spike', 200)
        result = await market_service.handle_volume_scan_request(timeframe, min_spike)
        return web.json_response(result)
    
    async def comprehensive_analysis_handler(request):
        # Support both GET and POST methods
        if request.method == 'GET':
            # GET method - parse query parameters
            symbol = request.query.get('symbol')
            timeframe = request.query.get('timeframe', '15m')
            exchange = request.query.get('exchange')
        else:
            # POST method - parse JSON body
            data = await request.json()
            symbol = data.get('symbol')
            timeframe = data.get('timeframe', '15m')
            exchange = data.get('exchange')
        
        result = await market_service.handle_comprehensive_analysis_request(symbol, timeframe, exchange)
        return web.json_response(result)
    
    async def multi_oi_handler(request):
        data = await request.json()
        base_symbol = data.get('base_symbol')
        result = await market_service.handle_multi_oi_request(base_symbol)
        return web.json_response(result)
    
    async def test_exchange_oi_handler(request):
        data = await request.json()
        exchange = data.get('exchange')
        symbol = data.get('symbol')
        result = await market_service.handle_test_exchange_oi_request(exchange, symbol)
        return web.json_response(result)
    
    app.router.add_get('/health', health_handler)
    app.router.add_post('/price', price_handler)
    app.router.add_post('/combined_price', combined_price_handler)
    app.router.add_post('/top_symbols', top_symbols_handler)
    app.router.add_post('/debug_tickers', debug_tickers_handler)
    app.router.add_post('/volume_spike', volume_spike_handler)
    app.router.add_post('/cvd', cvd_handler)
    app.router.add_post('/volume_scan', volume_scan_handler)
    app.router.add_get('/comprehensive_analysis', comprehensive_analysis_handler)
    app.router.add_post('/comprehensive_analysis', comprehensive_analysis_handler)
    app.router.add_post('/balance', balance_handler)
    app.router.add_post('/positions', positions_handler)
    app.router.add_post('/pnl', pnl_handler)
    app.router.add_post('/multi_oi', multi_oi_handler)
    app.router.add_post('/test_exchange_oi', test_exchange_oi_handler)
    
    return app

async def main():
    logger.info("Starting Market Data Service...")
    app = await create_app()
    return app

if __name__ == "__main__":
    web.run_app(main(), host='0.0.0.0', port=8001)