import asyncio
import ccxt.pro as ccxt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from loguru import logger
import pytz
from binance_bybit_oi_service import BinanceBybitOIService

@dataclass
class OIMarketData:
    """Open Interest data for a single market"""
    exchange: str
    symbol: str
    base_token: str
    market_type: str  # "stablecoin-margined" or "coin-margined"
    oi_tokens: float
    oi_usd: float
    price: float
    funding_rate: Optional[float] = None
    volume_24h: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    rank: Optional[int] = None

@dataclass
class OIAnalysisResult:
    """Complete OI analysis result"""
    base_token: str
    timestamp: datetime
    total_oi_tokens: float
    total_oi_usd: float
    stablecoin_margined_usd: float
    coin_margined_usd: float
    stablecoin_percentage: float
    coin_margined_percentage: float
    top_markets: List[OIMarketData]
    utc_time: str
    sgt_time: str

class OIAnalysisEngine:
    """Open Interest Analysis Engine"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.binance_bybit_service = BinanceBybitOIService()
        self.supported_exchanges = {
            'binance': {
                'stablecoin_margined': True,
                'coin_margined': True,  # Now includes USD inverse via our service
                'oi_endpoint': 'fetch_open_interest'
            },
            'bybit': {
                'stablecoin_margined': True,
                'coin_margined': True,
                'oi_endpoint': 'fetch_open_interest'
            }
        }
    
    async def analyze_oi(self, base_token: str = "BTC") -> OIAnalysisResult:
        """
        Analyze Open Interest across all major exchanges and market types
        """
        try:
            base_token = base_token.upper()
            logger.info(f"Starting OI analysis for {base_token}")
            
            # Gather OI data from all sources concurrently
            all_markets = await self._gather_oi_data(base_token)
            
            if not all_markets:
                raise ValueError(f"No OI data found for {base_token}")
            
            # Calculate totals and percentages
            total_oi_usd = sum(market.oi_usd for market in all_markets)
            stablecoin_margined_usd = sum(
                market.oi_usd for market in all_markets 
                if market.market_type == "stablecoin-margined"
            )
            coin_margined_usd = sum(
                market.oi_usd for market in all_markets 
                if market.market_type == "coin-margined"
            )
            
            # Calculate percentages
            stablecoin_percentage = (stablecoin_margined_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
            coin_margined_percentage = (coin_margined_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0
            
            # Sort markets by OI USD value and rank them
            all_markets.sort(key=lambda x: x.oi_usd, reverse=True)
            for i, market in enumerate(all_markets, 1):
                market.rank = i
            
            # Calculate total OI in tokens (use first market's price for conversion)
            total_oi_tokens = total_oi_usd / all_markets[0].price if all_markets else 0
            
            # Generate timestamps
            utc_time = datetime.now(pytz.UTC)
            sgt_time = utc_time.astimezone(pytz.timezone('Asia/Singapore'))
            
            return OIAnalysisResult(
                base_token=base_token,
                timestamp=utc_time,
                total_oi_tokens=total_oi_tokens,
                total_oi_usd=total_oi_usd,
                stablecoin_margined_usd=stablecoin_margined_usd,
                coin_margined_usd=coin_margined_usd,
                stablecoin_percentage=stablecoin_percentage,
                coin_margined_percentage=coin_margined_percentage,
                top_markets=all_markets,
                utc_time=utc_time.strftime('%H:%M:%S'),
                sgt_time=sgt_time.strftime('%H:%M:%S')
            )
            
        except Exception as e:
            logger.error(f"Error in OI analysis for {base_token}: {e}")
            raise
    
    async def _gather_oi_data(self, base_token: str) -> List[OIMarketData]:
        """Gather OI data from all supported exchanges"""
        all_markets = []
        
        # First, get comprehensive Binance + Bybit data using our specialized service
        try:
            logger.info(f"Fetching Binance + Bybit OI data for {base_token} using specialized service")
            binance_bybit_data = await self.binance_bybit_service.get_combined_oi_analysis(base_token)
            
            if binance_bybit_data['success']:
                # Convert our service data to OIMarketData format
                for market in binance_bybit_data['data']['individual_markets']:
                    # Determine market type
                    market_type = 'coin-margined' if market['category'] == 'INVERSE' else 'stablecoin-margined'
                    
                    # Format exchange name
                    exchange_name = f"{market['exchange'].title()} {market['market_type']}"
                    
                    oi_market = OIMarketData(
                        exchange=exchange_name,
                        symbol=market['symbol_exchange'],
                        base_token=base_token,
                        market_type=market_type,
                        oi_tokens=market['oi_tokens'],
                        oi_usd=market['oi_usd'],
                        price=market['oi_usd'] / market['oi_tokens'] if market['oi_tokens'] > 0 else 0,
                        funding_rate=market['funding_rate'],
                        volume_24h=market['volume_tokens'],
                        volume_24h_usd=market['volume_tokens'] * (market['oi_usd'] / market['oi_tokens']) if market['oi_tokens'] > 0 else 0
                    )
                    all_markets.append(oi_market)
                    logger.info(f"Added {exchange_name}: {oi_market.oi_tokens:,.0f} {base_token}")
        except Exception as e:
            logger.warning(f"Failed to fetch Binance+Bybit data via specialized service: {e}")
        finally:
            # Ensure the specialized service session is closed
            await self.binance_bybit_service.close()
        
        # Define additional markets to fetch from other exchanges
        additional_markets = [
            # OKX
            {'exchange': 'okx', 'symbol': f'{base_token}-USDT-SWAP', 'market_type': 'stablecoin-margined'},
            {'exchange': 'okx', 'symbol': f'{base_token}-USD-SWAP', 'market_type': 'coin-margined'},
            
            # Coinbase (if available)
            {'exchange': 'coinbase', 'symbol': f'{base_token}-USD', 'market_type': 'stablecoin-margined'},
            
            # Kraken
            {'exchange': 'kraken', 'symbol': f'{base_token}/USD', 'market_type': 'stablecoin-margined'},
            
            # Bitfinex
            {'exchange': 'bitfinex', 'symbol': f'{base_token}USD', 'market_type': 'stablecoin-margined'},
            
            # Deribit (BTC only)
            {'exchange': 'deribit', 'symbol': f'{base_token}-PERPETUAL', 'market_type': 'coin-margined'},
        ]
        
        # Only add additional markets if they make sense for the token
        additional_markets_to_fetch = []
        if base_token in ['BTC', 'ETH']:
            additional_markets_to_fetch = additional_markets
        
        # Fetch additional data concurrently
        if additional_markets_to_fetch:
            tasks = []
            for market_info in additional_markets_to_fetch:
                task = self._fetch_market_oi(
                    market_info['exchange'],
                    market_info['symbol'],
                    base_token,
                    market_info['market_type']
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            for result in results:
                if isinstance(result, OIMarketData):
                    all_markets.append(result)
                    logger.info(f"Added {result.exchange}: {result.oi_tokens:,.0f} {base_token}")
                elif isinstance(result, Exception):
                    logger.warning(f"Failed to fetch additional OI data: {result}")
        
        return all_markets
    
    async def _fetch_market_oi(self, exchange_name: str, symbol: str, base_token: str, market_type: str) -> Optional[OIMarketData]:
        """Fetch OI data for a specific market"""
        try:
            # Handle different exchange implementations
            if exchange_name == 'binance':
                return await self._fetch_binance_oi(symbol, base_token, market_type)
            elif exchange_name == 'bybit':
                return await self._fetch_bybit_oi(symbol, base_token, market_type)
            else:
                # For other exchanges, try using ccxt if available
                return await self._fetch_generic_oi(exchange_name, symbol, base_token, market_type)
                
        except Exception as e:
            logger.warning(f"Failed to fetch OI from {exchange_name} for {symbol}: {e}")
            return None
    
    async def _fetch_binance_oi(self, symbol: str, base_token: str, market_type: str) -> Optional[OIMarketData]:
        """Fetch OI data from Binance Futures"""
        try:
            # Use the futures exchange
            if 'binance_futures' not in self.exchange_manager.exchanges:
                logger.warning("Binance futures exchange not available")
                return None
                
            exchange = self.exchange_manager.exchanges['binance_futures']
            
            # Fetch OI and ticker data
            oi_data = await exchange.fetch_open_interest(symbol)
            ticker = await exchange.fetch_ticker(symbol)
            
            if not oi_data or not ticker:
                return None
            
            oi_tokens = oi_data.get('openInterestAmount', 0)
            price = ticker.get('last', 0)
            
            if not oi_tokens or not price:
                return None
            
            # Try to get funding rate
            funding_rate = None
            try:
                funding_data = await exchange.fetch_funding_rate(symbol)
                funding_rate = funding_data.get('fundingRate', 0)
            except:
                pass
            
            return OIMarketData(
                exchange='Binance USDT',
                symbol=symbol,
                base_token=base_token,
                market_type=market_type,
                oi_tokens=oi_tokens,
                oi_usd=oi_tokens * price,
                price=price,
                funding_rate=funding_rate,
                volume_24h=ticker.get('baseVolume'),
                volume_24h_usd=ticker.get('quoteVolume')
            )
            
        except Exception as e:
            logger.warning(f"Failed to fetch Binance OI for {symbol}: {e}")
            return None
    
    async def _fetch_bybit_oi(self, symbol: str, base_token: str, market_type: str) -> Optional[OIMarketData]:
        """Fetch OI data from Bybit using direct API calls"""
        try:
            async with aiohttp.ClientSession() as session:
                # Bybit v5 API endpoint
                if market_type == 'stablecoin-margined':
                    url = f"https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol}"
                    exchange_name = 'Bybit USDT'
                else:
                    url = f"https://api.bybit.com/v5/market/open-interest?category=inverse&symbol={symbol}"
                    exchange_name = 'Bybit USD'
                
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if data.get('retCode') != 0 or not data.get('result', {}).get('list'):
                        return None
                    
                    oi_info = data['result']['list'][0]
                    oi_value = float(oi_info.get('openInterest', 0))
                    
                    if not oi_value:
                        return None
                
                # Get ticker data for price
                ticker_url = f"https://api.bybit.com/v5/market/tickers?category={'linear' if market_type == 'stablecoin-margined' else 'inverse'}&symbol={symbol}"
                async with session.get(ticker_url) as response:
                    if response.status != 200:
                        return None
                    
                    ticker_data = await response.json()
                    
                    if ticker_data.get('retCode') != 0 or not ticker_data.get('result', {}).get('list'):
                        return None
                    
                    ticker_info = ticker_data['result']['list'][0]
                    price = float(ticker_info.get('lastPrice', 0))
                    volume_24h = float(ticker_info.get('volume24h', 0))
                    
                    if not price:
                        return None
                    
                    # For coin-margined, OI is in USD, convert to tokens
                    if market_type == 'coin-margined':
                        oi_tokens = oi_value / price  # Convert USD to tokens
                        oi_usd = oi_value
                    else:
                        oi_tokens = oi_value  # Already in tokens
                        oi_usd = oi_value * price
                    
                    return OIMarketData(
                        exchange=exchange_name,
                        symbol=symbol,
                        base_token=base_token,
                        market_type=market_type,
                        oi_tokens=oi_tokens,
                        oi_usd=oi_usd,
                        price=price,
                        volume_24h=volume_24h,
                        volume_24h_usd=volume_24h * price
                    )
                        
        except Exception as e:
            logger.warning(f"Failed to fetch Bybit OI for {symbol}: {e}")
            return None
    
    async def _fetch_generic_oi(self, exchange_name: str, symbol: str, base_token: str, market_type: str) -> Optional[OIMarketData]:
        """Fetch OI data from other exchanges using ccxt"""
        try:
            # Create exchange instance for public data
            exchange_class = getattr(ccxt, exchange_name, None)
            if not exchange_class:
                return None
            
            exchange = exchange_class({
                'enableRateLimit': True,
            })
            
            # Try to fetch OI data
            oi_data = await exchange.fetch_open_interest(symbol)
            ticker = await exchange.fetch_ticker(symbol)
            
            if not oi_data or not ticker:
                await exchange.close()
                return None
            
            oi_tokens = oi_data.get('openInterestAmount', 0)
            price = ticker.get('last', 0)
            
            if not oi_tokens or not price:
                await exchange.close()
                return None
            
            await exchange.close()
            
            return OIMarketData(
                exchange=exchange_name.title(),
                symbol=symbol,
                base_token=base_token,
                market_type=market_type,
                oi_tokens=oi_tokens,
                oi_usd=oi_tokens * price,
                price=price,
                volume_24h=ticker.get('baseVolume'),
                volume_24h_usd=ticker.get('quoteVolume')
            )
            
        except Exception as e:
            logger.warning(f"Failed to fetch generic OI from {exchange_name} for {symbol}: {e}")
            return None
    
    def format_oi_analysis(self, analysis: OIAnalysisResult) -> str:
        """Format OI analysis into the target output format"""
        try:
            # Format the exact target output
            message = f"""📊 OPEN INTEREST ANALYSIS - {analysis.base_token}

🔢 MARKET TYPE BREAKDOWN:
• Total OI: {analysis.total_oi_tokens:,.0f} {analysis.base_token} (${analysis.total_oi_usd/1e9:.1f}B)
• Stablecoin-Margined: ${analysis.stablecoin_margined_usd/1e9:.1f}B | {analysis.stablecoin_percentage:.1f}%
• Coin-Margined (Inverse): ${analysis.coin_margined_usd/1e9:.1f}B | {analysis.coin_margined_percentage:.1f}%

📈 TOP MARKETS:"""
            
            # Add top markets (limit to 13 as per target format)
            for i, market in enumerate(analysis.top_markets[:13], 1):
                market_type_label = "STABLE" if market.market_type == "stablecoin-margined" else "INVERSE"
                percentage = (market.oi_usd / analysis.total_oi_usd * 100) if analysis.total_oi_usd > 0 else 0
                
                message += f"\n{i}. {market.exchange}: {market.oi_tokens:,.0f} {analysis.base_token} (${market.oi_usd/1e9:.1f}B) | {percentage:.1f}% {market_type_label}"
            
            # Add timestamp
            message += f"\n\n🕐 {analysis.utc_time} UTC / {analysis.sgt_time} SGT"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting OI analysis: {e}")
            return f"❌ Error formatting OI analysis: {str(e)}"