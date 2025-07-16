"""
Enhanced Market Data Service with Comprehensive Logging Integration
This demonstrates how to integrate the structured logging system into the market data service
"""

import asyncio
import os
import time
import ccxt.pro as ccxt
import aiohttp
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Import new logging system
from ..shared.logging_config import setup_service_logging, get_logging_config
from .market_logger import market_logger, MarketDataLogger
from ..shared.exchange_logger import exchange_logger
from ..shared.structured_logger import ExchangeAPIData, PerformanceMetric

# Import existing modules
try:
    from .volume_analysis import VolumeAnalysisEngine, VolumeSpike, CVDData
    from .technical_indicators import TechnicalAnalysisService, TechnicalIndicators
    from .oi_analysis import OIAnalysisService
    from .unified_oi_aggregator import UnifiedOIAggregator
except ImportError:
    # For direct execution
    from volume_analysis import VolumeAnalysisEngine, VolumeSpike, CVDData
    from technical_indicators import TechnicalAnalysisService, TechnicalIndicators
    from oi_analysis import OIAnalysisService
    from unified_oi_aggregator import UnifiedOIAggregator

load_dotenv()

# Setup structured logging
logger = setup_service_logging('market-data', 'main')
market_logger = MarketDataLogger()

# Configure uvicorn logging
logging_config = get_logging_config('market-data')
logging_config.setup_uvicorn_logging()

# FastAPI app
app = FastAPI(title="Enhanced Crypto Market Data API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class PriceRequest(BaseModel):
    symbol: str
    exchange: Optional[str] = None

class ComprehensiveRequest(BaseModel):
    symbol: str
    timeframe: Optional[str] = "15m"
    exchange: Optional[str] = None

class EnhancedMarketDataService:
    """Enhanced market data service with comprehensive logging"""
    
    def __init__(self):
        self.exchanges = {}
        self.volume_engine = VolumeAnalysisEngine()
        self.technical_service = TechnicalAnalysisService()
        self.oi_service = OIAnalysisService()
        self.oi_aggregator = UnifiedOIAggregator()
        self.logger = setup_service_logging('market-data', 'service')
        
        # Log service initialization
        market_logger.log_business_event('service_initialization', {
            'components': ['volume_engine', 'technical_service', 'oi_service', 'oi_aggregator'],
            'supported_exchanges': self._get_supported_exchanges()
        })
    
    def _get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchanges"""
        supported = os.getenv('SUPPORTED_EXCHANGES', 'binance,bybit,okx,kucoin').split(',')
        return [ex.strip() for ex in supported]
    
    async def initialize_exchange(self, exchange_name: str) -> Optional[ccxt.Exchange]:
        """Initialize exchange with comprehensive logging"""
        start_time = time.time()
        
        try:
            with market_logger.time_operation('exchange_initialization', {'exchange': exchange_name}):
                # Get exchange class
                exchange_class = getattr(ccxt, exchange_name)
                
                # Configuration
                config = {
                    'apiKey': os.getenv(f'{exchange_name.upper()}_API_KEY'),
                    'secret': os.getenv(f'{exchange_name.upper()}_SECRET_KEY'),
                    'sandbox': os.getenv('SANDBOX_MODE', 'false').lower() == 'true',
                    'enableRateLimit': True,
                    'timeout': 30000,
                }
                
                # Remove None values
                config = {k: v for k, v in config.items() if v is not None}
                
                # Initialize exchange
                exchange = exchange_class(config)
                
                # Test connection
                await exchange.load_markets()
                
                initialization_time = (time.time() - start_time) * 1000
                
                # Log successful initialization
                exchange_logger.log_exchange_initialization(
                    exchange_name, config, True, initialization_time
                )
                
                self.exchanges[exchange_name] = exchange
                return exchange
                
        except Exception as e:
            initialization_time = (time.time() - start_time) * 1000
            
            # Log failed initialization
            exchange_logger.log_exchange_initialization(
                exchange_name, {}, False, initialization_time, str(e)
            )
            
            self.logger.error(f"Failed to initialize {exchange_name}: {e}")
            return None
    
    async def get_exchange(self, exchange_name: str) -> Optional[ccxt.Exchange]:
        """Get or initialize exchange"""
        if exchange_name not in self.exchanges:
            await self.initialize_exchange(exchange_name)
        return self.exchanges.get(exchange_name)
    
    async def fetch_ticker_data(self, symbol: str, exchange_name: str) -> Dict[str, Any]:
        """Fetch ticker data with comprehensive logging"""
        start_time = time.time()
        
        try:
            exchange = await self.get_exchange(exchange_name)
            if not exchange:
                raise Exception(f"Exchange {exchange_name} not available")
            
            # Log symbol harmonization
            original_symbol = symbol
            harmonized_symbol = self._harmonize_symbol(symbol, exchange_name)
            
            if original_symbol != harmonized_symbol:
                market_logger.log_symbol_harmonization(
                    original_symbol, exchange_name, harmonized_symbol, 'spot'
                )
            
            with market_logger.time_operation('ticker_fetch', {
                'symbol': harmonized_symbol, 
                'exchange': exchange_name
            }):
                # Fetch ticker
                ticker = await exchange.fetch_ticker(harmonized_symbol)
                
                response_time = (time.time() - start_time) * 1000
                
                # Log successful fetch
                market_logger.log_price_data_fetch(
                    harmonized_symbol, exchange_name, 'spot', True, response_time, 1
                )
                
                # Log exchange API call
                exchange_logger.log_ccxt_operation(
                    exchange_name, 'fetch_ticker', harmonized_symbol,
                    success=True, response_time_ms=response_time, data_size=len(str(ticker))
                )
                
                return ticker
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            # Log failed fetch
            market_logger.log_price_data_fetch(
                symbol, exchange_name, 'spot', False, response_time, error=str(e)
            )
            
            exchange_logger.log_ccxt_operation(
                exchange_name, 'fetch_ticker', symbol,
                success=False, response_time_ms=response_time, error=str(e)
            )
            
            raise
    
    async def fetch_ohlcv_data(self, symbol: str, timeframe: str, exchange_name: str, 
                               limit: int = 100) -> List[List]:
        """Fetch OHLCV data with logging"""
        start_time = time.time()
        
        try:
            exchange = await self.get_exchange(exchange_name)
            if not exchange:
                raise Exception(f"Exchange {exchange_name} not available")
            
            harmonized_symbol = self._harmonize_symbol(symbol, exchange_name)
            
            with market_logger.time_operation('ohlcv_fetch', {
                'symbol': harmonized_symbol, 
                'exchange': exchange_name,
                'timeframe': timeframe,
                'limit': limit
            }):
                ohlcv = await exchange.fetch_ohlcv(harmonized_symbol, timeframe, limit=limit)
                
                response_time = (time.time() - start_time) * 1000
                
                # Log successful fetch
                exchange_logger.log_market_data_request(
                    exchange_name, harmonized_symbol, 'ohlcv',
                    {'timeframe': timeframe, 'limit': limit},
                    response_time, True, len(ohlcv)
                )
                
                return ohlcv
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            exchange_logger.log_market_data_request(
                exchange_name, symbol, 'ohlcv',
                {'timeframe': timeframe, 'limit': limit},
                response_time, False, error=str(e)
            )
            
            raise
    
    async def get_comprehensive_analysis(self, symbol: str, timeframe: str = "15m", 
                                       exchange: str = None) -> Dict[str, Any]:
        """Get comprehensive analysis with detailed logging"""
        analysis_start = time.time()
        analysis_components = []
        data_sources = {}
        
        try:
            exchange = exchange or 'binance'
            
            market_logger.log_business_event('comprehensive_analysis_start', {
                'symbol': symbol,
                'timeframe': timeframe,
                'exchange': exchange
            })
            
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'exchange': exchange,
                'success': True
            }
            
            # Fetch price data
            try:
                with market_logger.time_operation('price_data_component'):
                    ticker = await self.fetch_ticker_data(symbol, exchange)
                    result['price_data'] = ticker
                    analysis_components.append('price_data')
                    data_sources['price_data'] = True
            except Exception as e:
                self.logger.error(f"Failed to fetch price data: {e}")
                data_sources['price_data'] = False
            
            # Fetch OHLCV for technical analysis
            try:
                with market_logger.time_operation('ohlcv_component'):
                    ohlcv = await self.fetch_ohlcv_data(symbol, timeframe, exchange)
                    if ohlcv:
                        # Technical indicators
                        indicators = await self.technical_service.calculate_indicators(ohlcv)
                        result['technical_indicators'] = indicators
                        analysis_components.append('technical_indicators')
                        data_sources['technical_indicators'] = True
                        
                        # Log technical indicator calculation
                        market_logger.log_technical_indicators(
                            symbol, indicators, 
                            (time.time() - analysis_start) * 1000
                        )
            except Exception as e:
                self.logger.error(f"Failed to calculate technical indicators: {e}")
                data_sources['technical_indicators'] = False
            
            # Volume analysis
            try:
                with market_logger.time_operation('volume_analysis_component'):
                    volume_data = await self.volume_engine.analyze_volume(symbol, timeframe, exchange)
                    if volume_data:
                        result['volume_analysis'] = volume_data
                        analysis_components.append('volume_analysis')
                        data_sources['volume_analysis'] = True
                        
                        # Log volume analysis
                        market_logger.log_volume_analysis(
                            symbol, timeframe, 
                            volume_data.get('spike_level', 'NORMAL'),
                            volume_data.get('cvd_trend', 'NEUTRAL'),
                            (time.time() - analysis_start) * 1000
                        )
            except Exception as e:
                self.logger.error(f"Failed to analyze volume: {e}")
                data_sources['volume_analysis'] = False
            
            # OI aggregation
            try:
                with market_logger.time_operation('oi_aggregation_component'):
                    oi_data = await self.oi_aggregator.get_unified_oi(symbol)
                    if oi_data and oi_data.get('success'):
                        result['oi_analysis'] = oi_data
                        analysis_components.append('oi_analysis')
                        data_sources['oi_analysis'] = True
                        
                        # Log OI aggregation
                        market_logger.log_oi_aggregation(
                            symbol,
                            oi_data.get('exchanges', []),
                            oi_data.get('total_oi_usd', 0),
                            (time.time() - analysis_start) * 1000,
                            True
                        )
            except Exception as e:
                self.logger.error(f"Failed to aggregate OI: {e}")
                data_sources['oi_analysis'] = False
            
            # Calculate total analysis time
            total_time = (time.time() - analysis_start) * 1000
            result['analysis_time_ms'] = total_time
            
            # Log comprehensive analysis completion
            market_logger.log_comprehensive_analysis(
                symbol, analysis_components, total_time, True, data_sources
            )
            
            return result
            
        except Exception as e:
            total_time = (time.time() - analysis_start) * 1000
            
            market_logger.log_comprehensive_analysis(
                symbol, analysis_components, total_time, False, data_sources
            )
            
            self.logger.error(f"Comprehensive analysis failed: {e}")
            raise
    
    def _harmonize_symbol(self, symbol: str, exchange_name: str) -> str:
        """Harmonize symbol format for specific exchange"""
        # Simplified symbol harmonization
        # In practice, this would use the EXCHANGE_SYMBOL_MAPPING from the original code
        if exchange_name == 'binance':
            return symbol.replace('-', '')
        elif exchange_name == 'okx':
            if '-' not in symbol and 'USDT' in symbol:
                base = symbol.replace('USDT', '')
                return f"{base}-USDT"
        return symbol

# Initialize service
service = EnhancedMarketDataService()

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()
    
    # Log request
    market_logger.log_business_event('api_request_received', {
        'method': request.method,
        'url': str(request.url),
        'client_host': request.client.host if request.client else None,
        'user_agent': request.headers.get('user-agent'),
        'content_type': request.headers.get('content-type')
    })
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Log response
        market_logger.log_business_event('api_request_completed', {
            'method': request.method,
            'url': str(request.url),
            'status_code': response.status_code,
            'response_time_ms': response_time
        })
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
        
        return response
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        market_logger.log_business_event('api_request_failed', {
            'method': request.method,
            'url': str(request.url),
            'error': str(e),
            'response_time_ms': response_time
        })
        
        raise

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint with system status"""
    try:
        # Check exchange connections
        exchange_status = {}
        for exchange_name in service._get_supported_exchanges():
            try:
                exchange = await service.get_exchange(exchange_name)
                exchange_status[exchange_name] = exchange is not None
            except:
                exchange_status[exchange_name] = False
        
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'exchanges': exchange_status,
            'components': {
                'volume_engine': True,
                'technical_service': True,
                'oi_service': True,
                'oi_aggregator': True
            }
        }
        
        market_logger.log_business_event('health_check', status)
        
        return status
        
    except Exception as e:
        market_logger.log_error(e, {
            'error_type': 'HealthCheckError',
            'error_message': str(e),
            'stack_trace': '',
            'context': {'endpoint': '/health'},
            'severity': 'WARNING'
        })
        
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/price")
async def get_price(request: PriceRequest):
    """Get price data with logging"""
    try:
        start_time = time.time()
        
        market_logger.log_business_event('price_request', {
            'symbol': request.symbol,
            'exchange': request.exchange
        })
        
        ticker = await service.fetch_ticker_data(request.symbol, request.exchange or 'binance')
        
        response_time = (time.time() - start_time) * 1000
        
        result = {
            'success': True,
            'symbol': request.symbol,
            'exchange': request.exchange or 'binance',
            'data': ticker,
            'response_time_ms': response_time,
            'timestamp': datetime.now().isoformat()
        }
        
        market_logger.log_business_event('price_response', {
            'symbol': request.symbol,
            'exchange': request.exchange,
            'response_time_ms': response_time,
            'success': True
        })
        
        return result
        
    except Exception as e:
        market_logger.log_error(e, {
            'error_type': 'PriceDataError',
            'error_message': str(e),
            'stack_trace': '',
            'context': {'symbol': request.symbol, 'exchange': request.exchange},
            'severity': 'ERROR'
        })
        
        raise HTTPException(status_code=500, detail=f"Failed to fetch price data: {str(e)}")

@app.post("/comprehensive_analysis")
async def comprehensive_analysis(request: ComprehensiveRequest):
    """Get comprehensive market analysis"""
    try:
        result = await service.get_comprehensive_analysis(
            request.symbol, request.timeframe, request.exchange
        )
        return result
        
    except Exception as e:
        market_logger.log_error(e, {
            'error_type': 'ComprehensiveAnalysisError',
            'error_message': str(e),
            'stack_trace': '',
            'context': {
                'symbol': request.symbol, 
                'timeframe': request.timeframe,
                'exchange': request.exchange
            },
            'severity': 'ERROR'
        })
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    market_logger.log_business_event('service_startup', {
        'mode': 'api_server',
        'supported_exchanges': service._get_supported_exchanges()
    })
    
    # Initialize default exchanges
    for exchange_name in ['binance', 'bybit']:
        try:
            await service.initialize_exchange(exchange_name)
        except Exception as e:
            logger.error(f"Failed to initialize {exchange_name} on startup: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    market_logger.log_business_event('service_shutdown', {
        'reason': 'normal_shutdown'
    })
    
    # Close exchange connections
    for exchange in service.exchanges.values():
        try:
            await exchange.close()
        except:
            pass

if __name__ == "__main__":
    # Configure uvicorn with logging
    uvicorn.run(
        "main_with_logging:app",
        host="0.0.0.0",
        port=8001,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )