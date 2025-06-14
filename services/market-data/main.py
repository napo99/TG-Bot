import asyncio
import os
import ccxt
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
        self._init_exchanges()
    
    def _init_exchanges(self):
        # Binance
        if os.getenv('BINANCE_API_KEY'):
            self.exchanges['binance'] = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
                'enableRateLimit': True,
            })
        
        # Bybit
        if os.getenv('BYBIT_API_KEY'):
            self.exchanges['bybit'] = ccxt.bybit({
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

class MarketDataService:
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        logger.info("Market Data Service initialized")
    
    async def handle_price_request(self, symbol: str, exchange: str = None) -> Dict[str, Any]:
        """Handle price request from Telegram bot"""
        try:
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
    
    app.router.add_get('/health', health_handler)
    app.router.add_post('/price', price_handler)
    app.router.add_post('/balance', balance_handler)
    app.router.add_post('/positions', positions_handler)
    app.router.add_post('/pnl', pnl_handler)
    
    return app

if __name__ == "__main__":
    logger.info("Starting Market Data Service...")
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8001)