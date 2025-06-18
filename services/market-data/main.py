import asyncio
import os
import ccxt.pro as ccxt
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
from loguru import logger
from dotenv import load_dotenv
from volume_analysis import VolumeAnalysisEngine, VolumeSpike, CVDData
from technical_indicators import TechnicalAnalysisService, TechnicalIndicators

load_dotenv()

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

@dataclass
class CombinedPriceData:
    base_symbol: str
    spot: Optional[PriceData] = None
    perp: Optional[PerpData] = None
    timestamp: datetime = None

@dataclass
class PositionData:
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    percentage: float

@dataclass
class LongShortData:
    symbol: str
    timestamp: int
    # Institutional (Top Traders)
    institutional_long_pct: float
    institutional_short_pct: float
    institutional_long_ratio: float
    # Retail (All Users)
    retail_long_pct: float
    retail_short_pct: float
    retail_long_ratio: float
    # Net positions in tokens
    total_oi_tokens: float
    net_longs_institutional: float
    net_shorts_institutional: float
    net_longs_retail: float
    net_shorts_retail: float
    # USD values
    token_price: float
    net_longs_institutional_usd: float
    net_shorts_institutional_usd: float
    net_longs_retail_usd: float
    net_shorts_retail_usd: float

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
        """Get both spot and perpetual prices for a symbol"""
        try:
            if exchange is None:
                exchange = next(iter(self.exchanges.keys()))
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            base_symbol = base_symbol.upper().replace('-', '/')
            
            # Try to get spot price
            spot_data = None
            try:
                spot_symbol = f"{base_symbol}"
                ticker = await ex.fetch_ticker(spot_symbol)
                spot_data = PriceData(
                    symbol=spot_symbol,
                    price=ticker['last'],
                    timestamp=datetime.now(),
                    volume_24h=ticker.get('baseVolume'),
                    change_24h=ticker.get('percentage'),
                    market_type="spot"
                )
            except Exception as e:
                logger.warning(f"Could not fetch spot data for {base_symbol}: {e}")
            
            # Try to get perp price with OI and funding
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
                                # Calculate funding rate change (simplified)
                                funding_change = 0.0  # Would need historical data for accurate calculation
                            except Exception:
                                pass
                            
                            # Try to get open interest
                            open_interest = None
                            try:
                                oi_info = await futures_ex.fetch_open_interest(perp_symbol)
                                open_interest = oi_info.get('openInterestAmount')
                            except Exception:
                                pass
                            
                            perp_data = PerpData(
                                symbol=perp_symbol,
                                price=ticker['last'],
                                timestamp=datetime.now(),
                                volume_24h=ticker.get('baseVolume'),
                                change_24h=ticker.get('percentage'),
                                open_interest=open_interest,
                                funding_rate=funding_rate,
                                funding_rate_change=funding_change
                            )
                            break
                        except Exception:
                            continue
                        
            except Exception as e:
                logger.warning(f"Could not fetch perp data for {base_symbol}: {e}")
            
            return CombinedPriceData(
                base_symbol=base_symbol,
                spot=spot_data,
                perp=perp_data,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error fetching combined price for {base_symbol}: {e}")
            raise
    
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
    
    async def get_long_short_data(self, symbol: str) -> Optional[LongShortData]:
        """Get long/short position data for a symbol"""
        try:
            # Convert symbol format for Binance API (e.g., SOL/USDT -> SOLUSDT)
            binance_symbol = symbol.replace('/', '')
            
            # Get current price and OI
            combined_price = await self.get_combined_price(symbol)
            if not combined_price or not combined_price.perp:
                logger.warning(f"No perpetual data available for {symbol}")
                return None
            
            current_price = combined_price.perp.price
            total_oi = combined_price.perp.open_interest
            
            if not total_oi:
                logger.warning(f"No open interest data for {symbol}")
                return None
            
            # Fetch long/short ratios using direct HTTP requests (more reliable than ccxt)
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Get top trader position ratio (institutional)
                institutional_url = f"https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol={binance_symbol}&period=15m&limit=1"
                async with session.get(institutional_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to fetch institutional data: {resp.status}")
                    institutional_data = await resp.json()
                
                # Get global account ratio (retail)
                retail_url = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={binance_symbol}&period=15m&limit=1"
                async with session.get(retail_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to fetch retail data: {resp.status}")
                    retail_data = await resp.json()
            
            if not institutional_data or not retail_data:
                logger.warning(f"No long/short ratio data for {symbol}")
                return None
            
            # Parse institutional data (top traders)
            inst_data = institutional_data[0]
            inst_long_pct = float(inst_data['longAccount']) * 100
            inst_short_pct = float(inst_data['shortAccount']) * 100
            inst_long_ratio = float(inst_data['longShortRatio'])
            
            # Parse retail data (all users)
            ret_data = retail_data[0]
            ret_long_pct = float(ret_data['longAccount']) * 100
            ret_short_pct = float(ret_data['shortAccount']) * 100
            ret_long_ratio = float(ret_data['longShortRatio'])
            
            # Calculate net positions in tokens
            net_longs_inst = total_oi * (inst_long_pct / 100)
            net_shorts_inst = total_oi * (inst_short_pct / 100)
            net_longs_ret = total_oi * (ret_long_pct / 100)
            net_shorts_ret = total_oi * (ret_short_pct / 100)
            
            # Calculate USD values
            net_longs_inst_usd = net_longs_inst * current_price
            net_shorts_inst_usd = net_shorts_inst * current_price
            net_longs_ret_usd = net_longs_ret * current_price
            net_shorts_ret_usd = net_shorts_ret * current_price
            
            return LongShortData(
                symbol=symbol,
                timestamp=inst_data['timestamp'],
                # Institutional data
                institutional_long_pct=inst_long_pct,
                institutional_short_pct=inst_short_pct,
                institutional_long_ratio=inst_long_ratio,
                # Retail data
                retail_long_pct=ret_long_pct,
                retail_short_pct=ret_short_pct,
                retail_long_ratio=ret_long_ratio,
                # Net positions
                total_oi_tokens=total_oi,
                net_longs_institutional=net_longs_inst,
                net_shorts_institutional=net_shorts_inst,
                net_longs_retail=net_longs_ret,
                net_shorts_retail=net_shorts_ret,
                # USD values
                token_price=current_price,
                net_longs_institutional_usd=net_longs_inst_usd,
                net_shorts_institutional_usd=net_shorts_inst_usd,
                net_longs_retail_usd=net_longs_ret_usd,
                net_shorts_retail_usd=net_shorts_ret_usd
            )
            
        except Exception as e:
            logger.error(f"Error fetching long/short data for {symbol}: {e}")
            return None

class MarketDataService:
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.volume_engine = None  # Will be initialized after exchange_manager
        self.technical_service = None  # Will be initialized after exchange_manager
        self._initialized = False
        logger.info("Market Data Service created")
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            await self.exchange_manager._init_exchanges()
            self.volume_engine = VolumeAnalysisEngine(self.exchange_manager)
            self.technical_service = TechnicalAnalysisService(self.exchange_manager)
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
                'timestamp': combined_data.timestamp.isoformat()
            }
            
            if combined_data.spot:
                result['spot'] = {
                    'symbol': combined_data.spot.symbol,
                    'price': combined_data.spot.price,
                    'volume_24h': combined_data.spot.volume_24h,
                    'change_24h': combined_data.spot.change_24h,
                    'market_type': 'spot'
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
                    'market_type': 'perp'
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
            
            # First get combined price to determine which market is available
            combined_price = await self.exchange_manager.get_combined_price(symbol, exchange)
            
            # Determine the primary market type and exchange to use for technical analysis
            # This ensures VWAP comes from the same market as the displayed price
            if combined_price.perp:
                # If perp data is available, use futures exchange for all technical analysis
                primary_exchange = 'binance_futures'
                primary_symbol = combined_price.perp.symbol
                primary_price_data = combined_price.perp
            elif combined_price.spot:
                # If only spot data is available, use spot exchange for technical analysis
                primary_exchange = 'binance'
                primary_symbol = combined_price.spot.symbol
                primary_price_data = combined_price.spot
            else:
                raise ValueError(f"No price data available for {symbol}")
            
            # Run remaining analysis with consistent exchange/market
            tasks = [
                self.volume_engine.detect_volume_spike(primary_symbol, timeframe, exchange=primary_exchange),
                self.volume_engine.calculate_cvd(primary_symbol, timeframe, exchange=primary_exchange),
                self.technical_service.get_technical_indicators(primary_symbol, timeframe, primary_exchange),
                self.exchange_manager.get_long_short_data(symbol) if combined_price.perp else None
            ]
            
            volume_spike, cvd_data, tech_indicators, long_short_data = await asyncio.gather(*tasks)
            
            # Analyze market sentiment and control
            sentiment_analysis = self._analyze_market_sentiment(
                combined_price, volume_spike, cvd_data, tech_indicators
            )
            
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': datetime.now().isoformat(),
                    
                    # Price data (using the same market as technical analysis)
                    'price_data': {
                        'current_price': float(primary_price_data.price),
                        'change_24h': float(primary_price_data.change_24h or 0),
                        'volume_24h': float(primary_price_data.volume_24h or 0),
                        'volume_24h_usd': float((primary_price_data.volume_24h or 0) * primary_price_data.price),
                        'market_type': 'perp' if combined_price.perp else 'spot',
                        'funding_rate': float(primary_price_data.funding_rate or 0) if hasattr(primary_price_data, 'funding_rate') else None
                    },
                    
                    # Volume analysis
                    'volume_analysis': {
                        'current_volume': float(volume_spike.current_volume),
                        'volume_usd': float(volume_spike.volume_usd),
                        'spike_level': volume_spike.spike_level,
                        'spike_percentage': float(volume_spike.spike_percentage),
                        'is_significant': bool(volume_spike.is_significant),
                        'relative_volume': float(volume_spike.current_volume / volume_spike.average_volume) if volume_spike.average_volume > 0 else 1.0
                    },
                    
                    # CVD analysis
                    'cvd_analysis': {
                        'current_cvd': float(cvd_data.current_cvd),
                        'cvd_trend': cvd_data.cvd_trend,
                        'divergence_detected': bool(cvd_data.divergence_detected),
                        'cvd_change_24h': float(cvd_data.cvd_change_24h),
                        'current_delta': float(cvd_data.current_delta),
                        'current_delta_usd': float(cvd_data.current_delta_usd)
                    },
                    
                    # Technical indicators
                    'technical_indicators': {
                        'rsi_14': tech_indicators.rsi_14,
                        'vwap': tech_indicators.vwap,
                        'atr_14': tech_indicators.atr_14,
                        'volatility_24h': tech_indicators.volatility_24h,
                        'bb_upper': tech_indicators.bb_upper,
                        'bb_middle': tech_indicators.bb_middle,
                        'bb_lower': tech_indicators.bb_lower,
                        'volatility_15m': tech_indicators.volatility_15m,
                        'atr_usd': tech_indicators.atr_usd
                    },
                    
                    # Market sentiment analysis
                    'market_sentiment': sentiment_analysis,
                    
                    # Long/Short position data (for perps)
                    'long_short_data': self._format_long_short_data(long_short_data) if long_short_data else {},
                    
                    # OI data (for perps)
                    'oi_data': self._extract_oi_data(combined_price)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
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
        elif combined_price.spot:
            price_data = combined_price.spot
            market_type = 'spot'
        else:
            return {}
        
        return {
            'current_price': float(price_data.price),
            'change_24h': float(price_data.change_24h or 0),
            'volume_24h': float(price_data.volume_24h or 0),
            'volume_24h_usd': float((price_data.volume_24h or 0) * price_data.price),
            'market_type': market_type,
            'funding_rate': float(price_data.funding_rate or 0) if hasattr(price_data, 'funding_rate') else None
        }
    
    def _extract_oi_data(self, combined_price: CombinedPriceData) -> Dict[str, Any]:
        """Extract Open Interest data for perpetuals"""
        if not combined_price or not combined_price.perp:
            return {}
        
        perp = combined_price.perp
        oi = perp.open_interest
        
        if not oi:
            return {}
        
        oi_usd = oi * perp.price
        
        return {
            'open_interest': float(oi),
            'open_interest_usd': float(oi_usd),
            'funding_rate': float(perp.funding_rate or 0)
        }
    
    def _format_long_short_data(self, long_short_data: LongShortData) -> Dict[str, Any]:
        """Format long/short position data for response"""
        if not long_short_data:
            return {}
        
        base_token = long_short_data.symbol.split('/')[0]
        
        # Calculate smart money edge
        institutional_long_pct = long_short_data.institutional_long_pct
        retail_long_pct = long_short_data.retail_long_pct
        smart_money_edge = institutional_long_pct - retail_long_pct
        
        return {
            'symbol': long_short_data.symbol,
            'timestamp': long_short_data.timestamp,
            'base_token': base_token,
            
            # Institutional (Top Traders)
            'institutional': {
                'long_pct': float(long_short_data.institutional_long_pct),
                'short_pct': float(long_short_data.institutional_short_pct),
                'long_ratio': float(long_short_data.institutional_long_ratio),
                'net_longs_tokens': float(long_short_data.net_longs_institutional),
                'net_shorts_tokens': float(long_short_data.net_shorts_institutional),
                'net_longs_usd': float(long_short_data.net_longs_institutional_usd),
                'net_shorts_usd': float(long_short_data.net_shorts_institutional_usd)
            },
            
            # Retail (All Users)
            'retail': {
                'long_pct': float(long_short_data.retail_long_pct),
                'short_pct': float(long_short_data.retail_short_pct),
                'long_ratio': float(long_short_data.retail_long_ratio),
                'net_longs_tokens': float(long_short_data.net_longs_retail),
                'net_shorts_tokens': float(long_short_data.net_shorts_retail),
                'net_longs_usd': float(long_short_data.net_longs_retail_usd),
                'net_shorts_usd': float(long_short_data.net_shorts_retail_usd)
            },
            
            # Summary with smart money edge
            'total_oi_tokens': float(long_short_data.total_oi_tokens),
            'token_price': float(long_short_data.token_price),
            'smart_money_edge': float(round(smart_money_edge, 1))
        }
    
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
        data = await request.json()
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', '15m')
        exchange = data.get('exchange')
        result = await market_service.handle_comprehensive_analysis_request(symbol, timeframe, exchange)
        return web.json_response(result)
    
    app.router.add_get('/health', health_handler)
    app.router.add_post('/price', price_handler)
    app.router.add_post('/combined_price', combined_price_handler)
    app.router.add_post('/top_symbols', top_symbols_handler)
    app.router.add_post('/debug_tickers', debug_tickers_handler)
    app.router.add_post('/volume_spike', volume_spike_handler)
    app.router.add_post('/cvd', cvd_handler)
    app.router.add_post('/volume_scan', volume_scan_handler)
    app.router.add_post('/comprehensive_analysis', comprehensive_analysis_handler)
    app.router.add_post('/balance', balance_handler)
    app.router.add_post('/positions', positions_handler)
    app.router.add_post('/pnl', pnl_handler)
    
    return app

async def main():
    logger.info("Starting Market Data Service...")
    app = await create_app()
    return app

if __name__ == "__main__":
    web.run_app(main(), host='0.0.0.0', port=8001)