import asyncio
import os
import ccxt.pro as ccxt
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PriceData:
    symbol: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    market_type: str = "spot"  # "spot" or "perp"

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
        
        # Add authenticated exchanges if API keys are provided
        if os.getenv('BINANCE_API_KEY'):
            self.exchanges['binance_auth'] = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
                'enableRateLimit': True,
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
                # Try different perp symbol formats
                perp_symbols = [f"{base_symbol}:USDT", f"{base_symbol}-PERP", f"{base_symbol}/USDT:USDT"]
                
                for perp_symbol in perp_symbols:
                    try:
                        ticker = await ex.fetch_ticker(perp_symbol)
                        
                        # Try to get funding rate
                        funding_rate = None
                        funding_change = None
                        try:
                            funding_info = await ex.fetch_funding_rate(perp_symbol)
                            funding_rate = funding_info.get('fundingRate')
                            # Calculate funding rate change (simplified)
                            funding_change = 0.0  # Would need historical data for accurate calculation
                        except Exception:
                            pass
                        
                        # Try to get open interest
                        open_interest = None
                        try:
                            oi_info = await ex.fetch_open_interest(perp_symbol)
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
            if exchange is None:
                exchange = next(iter(self.exchanges.keys()))
            
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not configured")
            
            ex = self.exchanges[exchange]
            
            # Fetch all tickers
            tickers = await ex.fetch_tickers()
            
            # Filter by market type and sort by volume
            filtered_tickers = []
            for symbol, ticker in tickers.items():
                if market_type == "spot":
                    # Filter for spot markets (usually contain / and not :)
                    if '/' in symbol and ':' not in symbol and 'USDT' in symbol:
                        filtered_tickers.append((symbol, ticker))
                elif market_type == "perp":
                    # Filter for perp markets (usually contain :USDT or -PERP)
                    if ':USDT' in symbol or 'PERP' in symbol:
                        filtered_tickers.append((symbol, ticker))
            
            # Sort by 24h volume (descending)
            sorted_tickers = sorted(
                filtered_tickers, 
                key=lambda x: x[1].get('baseVolume', 0) or 0, 
                reverse=True
            )
            
            # Return top N
            top_symbols = []
            for symbol, ticker in sorted_tickers[:limit]:
                price_data = PriceData(
                    symbol=symbol,
                    price=ticker['last'],
                    timestamp=datetime.now(),
                    volume_24h=ticker.get('baseVolume'),
                    change_24h=ticker.get('percentage'),
                    market_type=market_type
                )
                top_symbols.append(price_data)
            
            return top_symbols
            
        except Exception as e:
            logger.error(f"Error fetching top {market_type} symbols: {e}")
            raise

class MarketDataService:
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self._initialized = False
        logger.info("Market Data Service created")
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            await self.exchange_manager._init_exchanges()
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
                result.append({
                    'symbol': symbol_data.symbol,
                    'price': symbol_data.price,
                    'volume_24h': symbol_data.volume_24h,
                    'change_24h': symbol_data.change_24h,
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
    
    app.router.add_get('/health', health_handler)
    app.router.add_post('/price', price_handler)
    app.router.add_post('/combined_price', combined_price_handler)
    app.router.add_post('/top_symbols', top_symbols_handler)
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