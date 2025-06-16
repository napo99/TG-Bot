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

load_dotenv()

class MarketCapRanking:
    """Smart ranking system using known market cap order and trading data"""
    
    # Top cryptocurrencies by known market cap (approximate order)
    MARKET_CAP_RANKING = {
        'BTC': 1,   # ~$2T
        'ETH': 2,   # ~$306B  
        'USDT': 3,  # ~$137B
        'XRP': 4,   # ~$77B
        'BNB': 5,   # ~$67B
        'SOL': 6,   # ~$64B
        'USDC': 7,  # ~$46B
        'ADA': 8,   # ~$18B
        'DOGE': 9,  # ~$17B
        'TRX': 10,  # ~$15B
        'AVAX': 11, # ~$14B
        'SHIB': 12, # ~$13B
        'TON': 13,  # ~$12B
        'DOT': 14,  # ~$11B
        'LINK': 15, # ~$10B
        'MATIC': 16, # ~$9B
        'UNI': 17,  # ~$8B
        'LTC': 18,  # ~$7B
        'BCH': 19,  # ~$6B
        'NEAR': 20, # ~$5B
        'ATOM': 21, # ~$4B
        'ICP': 22,  # ~$4B
        'FIL': 23,  # ~$3B
        'ETC': 24,  # ~$3B
        'APT': 25,  # ~$3B
        'HBAR': 26, # ~$2.5B
        'XLM': 27,  # ~$2.5B
        'VET': 28,  # ~$2B
        'OP': 29,   # ~$2B
        'ALGO': 30, # ~$1.5B
        'MANA': 40,
        'SAND': 41,
        'AXS': 42,
        'GALA': 43,
        'CHZ': 44,
        'FLOW': 45,
        'ONE': 46,
        'THETA': 47,
        'XTZ': 48,
        'EOS': 49,
        'AAVE': 50,
        'MKR': 51,
        'SNX': 52,
        'COMP': 53,
        'YFI': 54,
        'SUSHI': 55
    }
    
    @classmethod
    def get_ranking_score(cls, symbol: str, price: float, volume_24h: float) -> float:
        """
        Calculate ranking score based on known market cap order + trading activity
        Returns higher score for better ranking
        """
        # Extract base symbol
        base_symbol = symbol.replace('/USDT', '').replace(':USDT', '').replace('-USDT', '').upper()
        
        # Get market cap rank (lower number = higher market cap)
        market_cap_rank = cls.MARKET_CAP_RANKING.get(base_symbol, 1000)  # Unknown tokens get low priority
        
        # Convert rank to score (higher score = better ranking)
        # Top 30 get significant boost, others get volume-based scoring
        if market_cap_rank <= 30:
            base_score = 10000 / market_cap_rank  # BTC=10000, ETH=5000, etc.
            volume_boost = min(volume_24h * price / 1e6, 50)  # Cap volume boost at 50
            return base_score + volume_boost
        else:
            # For unknown tokens, use volume-based ranking but heavily penalized
            volume_score = (volume_24h * price / 1e6) * 0.01  # 100x penalty for unknown tokens
            return max(volume_score, 0.1)  # Minimum score of 0.1 for unknown tokens
    
    @classmethod  
    def get_estimated_market_cap(cls, symbol: str, price: float) -> Optional[float]:
        """
        Get estimated market cap based on known rankings
        This is approximate but much better than price × volume
        """
        base_symbol = symbol.replace('/USDT', '').replace(':USDT', '').replace('-USDT', '').upper()
        
        # Rough market cap estimates (in billions USD)
        market_cap_estimates = {
            'BTC': 2100,
            'ETH': 306,  
            'USDT': 137,
            'XRP': 77,
            'BNB': 67,
            'SOL': 64,
            'USDC': 46,
            'ADA': 18,
            'DOGE': 17,
            'TRX': 15,
            'AVAX': 14,
            'SHIB': 13,
            'TON': 12,
            'DOT': 11,
            'LINK': 10,
            'MATIC': 9,
            'UNI': 8,
            'LTC': 7,
            'BCH': 6,
            'NEAR': 5,
            'ATOM': 4,
            'ICP': 4,
            'FIL': 3,
            'ETC': 3,
            'APT': 3,
            'HBAR': 2.5,
            'XLM': 2.5,
            'VET': 2,
            'OP': 2,
            'ALGO': 1.5
        }
        
        if base_symbol in market_cap_estimates:
            return market_cap_estimates[base_symbol] * 1e9  # Convert to USD
        
        return None  # Unknown token


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

class MarketDataService:
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.volume_engine = None  # Will be initialized after exchange_manager
        self._initialized = False
        logger.info("Market Data Service created")
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            await self.exchange_manager._init_exchanges()
            self.volume_engine = VolumeAnalysisEngine(self.exchange_manager)
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
                    'is_significant': spike.is_significant,
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
                    'divergence_detected': cvd.divergence_detected,
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
                    'is_significant': spike.is_significant
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
    
    app.router.add_get('/health', health_handler)
    app.router.add_post('/price', price_handler)
    app.router.add_post('/combined_price', combined_price_handler)
    app.router.add_post('/top_symbols', top_symbols_handler)
    app.router.add_post('/debug_tickers', debug_tickers_handler)
    app.router.add_post('/volume_spike', volume_spike_handler)
    app.router.add_post('/cvd', cvd_handler)
    app.router.add_post('/volume_scan', volume_scan_handler)
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