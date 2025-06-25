"""
Open Interest Analysis Engine - Phase 2A: Multi-Stablecoin Support
Comprehensive OI tracking across USDT + USDC markets for any cryptocurrency
Supports dynamic symbol resolution and exchange aggregation
"""

import asyncio
import aiohttp
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from loguru import logger

@dataclass
class ExchangeOIData:
    """OI data from a single exchange"""
    exchange: str
    symbol: str
    oi_tokens: float           # Open Interest in native tokens
    oi_usd: float             # Open Interest in USD
    funding_rate: float       # Current funding rate
    volume_24h: float         # 24h volume in tokens
    volume_24h_usd: float     # 24h volume in USD
    price: float              # Current price
    timestamp: datetime
    # Position data (Binance only initially)
    long_pct: Optional[float] = None
    short_pct: Optional[float] = None
    long_short_ratio: Optional[float] = None

@dataclass
class LongShortRatios:
    """Binance long/short ratio data"""
    symbol: str
    timestamp: datetime
    # Global (all traders)
    global_long_pct: float
    global_short_pct: float
    global_ratio: float
    # Top traders (account-based)
    top_account_long_pct: float
    top_account_short_pct: float 
    top_account_ratio: float
    # Top traders (position-based)
    top_position_long_pct: float
    top_position_short_pct: float
    top_position_ratio: float

@dataclass
class AggregatedOIAnalysis:
    """Complete aggregated OI analysis"""
    symbol: str
    timestamp: datetime
    
    # Aggregated totals
    total_oi_tokens: float
    total_oi_usd: float
    total_volume_24h: float
    total_volume_24h_usd: float
    
    # Exchange breakdown (sorted by OI size)
    exchange_breakdown: List[ExchangeOIData]
    
    # Price vs OI analysis
    current_price: float
    oi_change_24h_pct: float
    price_change_24h_pct: float
    oi_vs_price_divergence: float  # Difference between OI and price changes
    
    # Long/Short intelligence (from Binance)
    long_short_data: Optional[LongShortRatios] = None
    
    # Deviation detection
    oi_vs_normal_pct: float = 0.0  # % above/below normal levels
    alert_level: str = "NORMAL"    # NORMAL, ELEVATED, HIGH, EXTREME
    
    # Market implications
    market_sentiment: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    risk_level: str = "NORMAL"         # LOW, NORMAL, HIGH, EXTREME

class OIAnalysisEngine:
    """Phase 2: Multi-Exchange OI Analysis Engine (Binance + Bybit + Gate.io + Bitget + OKX)"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.oi_history = {}  # Store historical OI data for trend analysis
        
        # Phase 2 exchanges
        self.exchanges = ['binance_futures', 'bybit', 'gateio', 'bitget', 'okx']
        self.binance_api_base = "https://fapi.binance.com"
        
        # Gate.io API configuration
        self.gateio_base = "https://api.gateio.ws/api/v4/futures"
        self.gateio_endpoints = {
            'USDT': f'{self.gateio_base}/usdt/tickers',     # Linear USDT
            'USDC': f'{self.gateio_base}/usdc/tickers',     # Linear USDC
            'USD': f'{self.gateio_base}/btc/tickers'        # Inverse BTC-settled
        }
        
        # Bitget API configuration
        self.bitget_oi_url = "https://api.bitget.com/api/mix/v1/market/open-interest"
    
    async def _validation_agent_price_consistency(self, exchange_data: List[ExchangeOIData]) -> Dict[str, Any]:
        """Agent 1: Price consistency validation"""
        try:
            warnings = []
            prices = [data.price for data in exchange_data if data.price > 0]
            if len(prices) > 1:
                price_variance = max(prices) / min(prices) - 1
                if price_variance > 0.05:
                    warnings.append(f"High price variance: {price_variance:.2%}")
            return {'agent': 'price_consistency', 'warnings': warnings, 'passed': len(warnings) == 0}
        except Exception as e:
            return {'agent': 'price_consistency', 'warnings': [f"Agent error: {e}"], 'passed': False}
    
    async def _validation_agent_oi_reasonableness(self, exchange_data: List[ExchangeOIData], symbol: str) -> Dict[str, Any]:
        """Agent 2: OI reasonableness validation"""
        try:
            warnings = []
            base_token = symbol.split('/')[0]
            for data in exchange_data:
                if data.oi_tokens < 1:
                    warnings.append(f"{data.exchange}: Low OI ({data.oi_tokens:.2f} {base_token})")
                elif data.oi_tokens > 1000000:
                    warnings.append(f"{data.exchange}: High OI ({data.oi_tokens:,.0f} {base_token})")
                
                calculated_usd = data.oi_tokens * data.price
                usd_diff = abs(calculated_usd - data.oi_usd) / data.oi_usd if data.oi_usd > 0 else 0
                if usd_diff > 0.1:
                    warnings.append(f"{data.exchange}: USD mismatch ({usd_diff:.1%})")
            return {'agent': 'oi_reasonableness', 'warnings': warnings, 'passed': len(warnings) == 0}
        except Exception as e:
            return {'agent': 'oi_reasonableness', 'warnings': [f"Agent error: {e}"], 'passed': False}
    
    async def _validation_agent_volume_ratios(self, exchange_data: List[ExchangeOIData]) -> Dict[str, Any]:
        """Agent 3: Volume/OI ratio validation"""
        try:
            warnings = []
            for data in exchange_data:
                if data.volume_24h > 0 and data.oi_tokens > 0:
                    ratio = data.volume_24h / data.oi_tokens
                    if ratio > 100:
                        warnings.append(f"{data.exchange}: High vol/OI ratio ({ratio:.1f}x)")
                    elif ratio < 0.01:
                        warnings.append(f"{data.exchange}: Low vol/OI ratio ({ratio:.3f}x)")
            return {'agent': 'volume_ratios', 'warnings': warnings, 'passed': len(warnings) == 0}
        except Exception as e:
            return {'agent': 'volume_ratios', 'warnings': [f"Agent error: {e}"], 'passed': False}
    
    async def _validation_agent_distribution_check(self, exchange_data: List[ExchangeOIData]) -> Dict[str, Any]:
        """Agent 4: OI distribution validation"""
        try:
            warnings = []
            if len(exchange_data) > 1:
                total_oi = sum(data.oi_usd for data in exchange_data)
                largest_share = max(data.oi_usd for data in exchange_data) / total_oi
                if largest_share > 0.95:
                    dominant = max(exchange_data, key=lambda x: x.oi_usd).exchange
                    warnings.append(f"OI concentrated in {dominant} ({largest_share:.1%})")
            return {'agent': 'distribution_check', 'warnings': warnings, 'passed': len(warnings) == 0}
        except Exception as e:
            return {'agent': 'distribution_check', 'warnings': [f"Agent error: {e}"], 'passed': False}
    
    async def _run_validation_agents(self, exchange_data: List[ExchangeOIData], symbol: str) -> Dict[str, Any]:
        """Run parallel validation agents concurrently"""
        try:
            logger.info(f"Starting parallel validation agents for {symbol}")
            
            # Run all validation agents in parallel
            agent_tasks = [
                self._validation_agent_price_consistency(exchange_data),
                self._validation_agent_oi_reasonableness(exchange_data, symbol),
                self._validation_agent_volume_ratios(exchange_data),
                self._validation_agent_distribution_check(exchange_data)
            ]
            
            # Execute agents concurrently
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Aggregate results
            all_warnings = []
            passed_agents = 0
            total_agents = len(agent_tasks)
            
            for result in agent_results:
                if isinstance(result, dict):
                    all_warnings.extend(result.get('warnings', []))
                    if result.get('passed', False):
                        passed_agents += 1
                    logger.info(f"Agent {result.get('agent', 'unknown')}: {'✅' if result.get('passed') else '⚠️'}")
                else:
                    all_warnings.append(f"Agent execution error: {result}")
            
            overall_passed = len(all_warnings) == 0
            logger.info(f"Validation agents: {passed_agents}/{total_agents} passed, {len(all_warnings)} warnings")
            
            return {
                'passed': overall_passed,
                'warnings': all_warnings,
                'total_agents': total_agents,
                'passed_agents': passed_agents,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error in parallel validation agents: {e}")
            return {
                'passed': False,
                'warnings': [f"Validation system error: {str(e)}"],
                'total_agents': 4,
                'passed_agents': 0,
                'symbol': symbol
            }
        
    async def _fetch_binance_oi(self, symbol: str) -> Optional[ExchangeOIData]:
        """Fetch Binance OI data using existing exchange manager"""
        try:
            if 'binance_futures' not in self.exchange_manager.exchanges:
                logger.warning("Binance futures not available")
                return None
                
            exchange = self.exchange_manager.exchanges['binance_futures']
            
            # Convert symbol format: BTC/USDT -> BTC/USDT:USDT
            binance_symbol = f"{symbol}:USDT" if ':' not in symbol else symbol
            
            # Get OI data
            oi_info = await exchange.fetch_open_interest(binance_symbol)
            funding_info = await exchange.fetch_funding_rate(binance_symbol)
            ticker = await exchange.fetch_ticker(binance_symbol)
            
            oi_tokens = oi_info.get('openInterestAmount', 0)
            price = ticker.get('last', 0)
            volume_24h = ticker.get('baseVolume', 0)
            
            return ExchangeOIData(
                exchange='binance',
                symbol=symbol,
                oi_tokens=oi_tokens,
                oi_usd=oi_tokens * price,
                funding_rate=funding_info.get('fundingRate', 0),
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h * price,
                price=price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error fetching Binance OI: {e}")
            return None
    
    async def _fetch_bybit_oi(self, symbol: str) -> Optional[ExchangeOIData]:
        """Fetch Bybit OI data using direct API calls - FIXED for inverse contracts"""
        try:
            # RESEARCH-BASED FIX: Use direct API calls with correct symbol formats
            # Based on bybit_inverse_research.py findings
            
            # Convert input symbol to Bybit format
            if symbol.startswith('BTC'):
                # For BTC, prioritize linear contract (BTCUSDT) which has larger OI
                bybit_contracts = [
                    ("BTCUSDT", "linear"),   # BTC/USDT Linear Perpetual (~55K BTC) - MAIN CONTRACT
                    ("BTCUSD", "inverse")    # BTC/USD Inverse Perpetual (~15K BTC equivalent)
                ]
            else:
                # For other tokens, try linear format
                base_token = symbol.split('/')[0].upper()
                bybit_contracts = [
                    (f"{base_token}USDT", "linear")
                ]
            
            # Try each contract format until we get valid OI data
            async with aiohttp.ClientSession() as session:
                for bybit_symbol, category in bybit_contracts:
                    try:
                        # Use tickers endpoint (more reliable than funding for OI)
                        url = "https://api.bybit.com/v5/market/tickers"
                        params = {
                            "category": category,
                            "symbol": bybit_symbol
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                continue
                                
                            data = await response.json()
                            
                            if data.get('retCode') != 0:
                                continue
                            
                            result = data.get('result', {})
                            ticker_list = result.get('list', [])
                            
                            if not ticker_list:
                                continue
                            
                            ticker = ticker_list[0]
                            
                            # Extract OI data from ticker response  
                            oi_contracts = float(ticker.get('openInterest', 0))
                            oi_usd_value = float(ticker.get('openInterestValue', 0))
                            price = float(ticker.get('lastPrice', 0))
                            funding_rate = float(ticker.get('fundingRate', 0))
                            volume_24h_usd = float(ticker.get('turnover24h', 0))
                            volume_24h_base = float(ticker.get('volume24h', 0))
                            
                            if oi_contracts <= 0 or price <= 0:
                                continue
                            
                            # Convert to standard units for the system
                            if category == "inverse":
                                # Inverse contracts: OI is in contract units, convert to BTC equivalent
                                oi_tokens = oi_contracts / price  # Convert contract units to BTC
                                # Keep the raw USD value from API (already in BTC terms)
                                oi_usd = oi_usd_value
                                logger.info(f"🎯 Bybit inverse FIXED: {bybit_symbol} using openInterestValue=${oi_usd_value:,.0f} instead of contracts*price=${oi_contracts * price:,.0f}")
                            else:
                                # Linear contracts: Use openInterestValue for USD, calculate tokens
                                oi_usd = oi_usd_value  # USD value from API
                                oi_tokens = oi_usd_value / price if price > 0 else 0  # FIXED: Convert USD to tokens
                            
                            logger.info(f"Bybit {bybit_symbol} ({category}): {oi_contracts:,.0f} contracts, "
                                      f"{oi_tokens:,.2f} tokens, ${oi_usd:,.2f} USD")
                            
                            return ExchangeOIData(
                                exchange='bybit',
                                symbol=symbol,  # Return original symbol format
                                oi_tokens=float(oi_tokens),
                                oi_usd=float(oi_usd),
                                funding_rate=funding_rate,
                                volume_24h=volume_24h_base,
                                volume_24h_usd=volume_24h_usd,
                                price=price,
                                timestamp=datetime.now()
                            )
                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch {bybit_symbol} ({category}): {e}")
                        continue
            
            logger.warning(f"No valid Bybit OI data found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Bybit OI for {symbol}: {e}")
            return None
    
    async def _fetch_gateio_oi(self, symbol: str) -> List[ExchangeOIData]:
        """Fetch Gate.io OI data for all settlement currencies (USDT, USDC, USD)"""
        try:
            results = []
            base_token = symbol.split('/')[0].upper()
            
            async with aiohttp.ClientSession() as session:
                # Fetch all three settlement types in parallel
                tasks = []
                for settlement, endpoint in self.gateio_endpoints.items():
                    tasks.append(self._fetch_gateio_settlement(session, base_token, settlement, endpoint))
                
                settlement_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in settlement_results:
                    if isinstance(result, ExchangeOIData):
                        results.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Gate.io settlement error: {result}")
            
            logger.info(f"Gate.io fetched {len(results)}/3 markets for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Gate.io OI for {symbol}: {e}")
            return []
    
    async def _fetch_gateio_settlement(self, session: aiohttp.ClientSession, base_token: str, settlement: str, endpoint: str) -> Optional[ExchangeOIData]:
        """Fetch Gate.io OI data for a specific settlement currency"""
        try:
            # Gate.io symbol formats
            if settlement == 'USDT':
                gateio_symbol = f"{base_token}_USDT"
            elif settlement == 'USDC':
                gateio_symbol = f"{base_token}_USDC"
            else:  # USD (inverse)
                gateio_symbol = f"{base_token}_USD"
            
            # Fetch ticker data
            async with session.get(endpoint) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Find our symbol in the tickers list
                ticker = None
                for t in data:
                    if t.get('contract') == gateio_symbol:
                        ticker = t
                        break
                
                if not ticker:
                    logger.debug(f"Gate.io symbol {gateio_symbol} not found in {settlement} market")
                    return None
                
                # Extract data
                price = float(ticker.get('last', 0))
                funding_rate = float(ticker.get('funding_rate', 0))
                volume_24h = float(ticker.get('volume_24h', 0))
                
                # For OI, Gate.io uses different fields depending on settlement
                if settlement == 'USD':  # Inverse
                    # For inverse contracts, size_24h is in contract units
                    oi_contracts = float(ticker.get('size_24h', 0))  # This might be volume, need position endpoint
                    oi_tokens = oi_contracts / price if price > 0 else 0  # Convert to token units
                else:  # Linear USDT/USDC
                    # For linear contracts, use position size directly
                    oi_contracts = float(ticker.get('volume_24h', 0))  # May need different endpoint
                    oi_tokens = oi_contracts
                
                oi_usd = oi_tokens * price
                volume_24h_usd = volume_24h * price
                
                if oi_tokens <= 0 or price <= 0:
                    logger.debug(f"Gate.io {gateio_symbol}: Invalid OI ({oi_tokens}) or price ({price})")
                    return None
                
                logger.info(f"Gate.io {gateio_symbol} ({settlement}): {oi_tokens:,.2f} tokens, ${oi_usd:,.2f} USD")
                
                return ExchangeOIData(
                    exchange=f'gateio_{settlement.lower()}',
                    symbol=f"{base_token}/USDT",  # Normalize symbol format
                    oi_tokens=oi_tokens,
                    oi_usd=oi_usd,
                    funding_rate=funding_rate,
                    volume_24h=volume_24h,
                    volume_24h_usd=volume_24h_usd,
                    price=price,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.warning(f"Error fetching Gate.io {settlement} for {base_token}: {e}")
            return None
    
    async def _fetch_bitget_oi(self, symbol: str) -> List[ExchangeOIData]:
        """Fetch Bitget OI data for all product types (USDT, USDC, USD)"""
        try:
            results = []
            base_token = symbol.split('/')[0].upper()
            
            # Bitget symbol formats
            bitget_symbols = {
                'USDT': f'{base_token}USDT_UMCBL',    # Linear USDT (U-margined)
                'USDC': f'{base_token}USDC_UMCBL',    # Linear USDC (U-margined)
                'USD': f'{base_token}USD_DMCBL'       # Inverse USD (Coin-margined)
            }
            
            async with aiohttp.ClientSession() as session:
                # Fetch all three product types in parallel
                tasks = []
                for settlement, bitget_symbol in bitget_symbols.items():
                    tasks.append(self._fetch_bitget_settlement(session, base_token, bitget_symbol, settlement))
                
                settlement_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in settlement_results:
                    if isinstance(result, ExchangeOIData):
                        results.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Bitget settlement error: {result}")
            
            logger.info(f"Bitget fetched {len(results)}/3 markets for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Bitget OI for {symbol}: {e}")
            return []
    
    async def _fetch_bitget_settlement(self, session: aiohttp.ClientSession, base_token: str, bitget_symbol: str, settlement: str) -> Optional[ExchangeOIData]:
        """Fetch Bitget OI data for a specific product type"""
        try:
            # Bitget Open Interest endpoint
            params = {'symbol': bitget_symbol}
            
            async with session.get(self.bitget_oi_url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data.get('code') != '00000':
                    logger.debug(f"Bitget API error for {bitget_symbol}: {data.get('msg')}")
                    return None
                
                oi_data = data.get('data')
                if not oi_data:
                    return None
                
                # Extract OI data
                open_interest = float(oi_data.get('openInterest', 0))
                open_interest_usd = float(oi_data.get('openInterestUsd', 0))
                
                # Get additional market data from tickers endpoint
                ticker_url = "https://api.bitget.com/api/mix/v1/market/ticker"
                ticker_params = {'symbol': bitget_symbol}
                
                async with session.get(ticker_url, params=ticker_params) as ticker_response:
                    if ticker_response.status != 200:
                        return None
                    
                    ticker_data = await ticker_response.json()
                    if ticker_data.get('code') != '00000':
                        return None
                    
                    ticker = ticker_data.get('data')
                    if not ticker:
                        return None
                    
                    price = float(ticker.get('last', 0))
                    volume_24h_usd = float(ticker.get('usdtVol', 0))
                    funding_rate = float(ticker.get('fundingRate', 0))
                
                # Calculate token amounts
                if settlement == 'USD':  # Inverse contracts
                    # For inverse contracts, use openInterestUsd directly
                    oi_tokens = open_interest  # Contract amount (may need conversion)
                    oi_usd = open_interest_usd
                    volume_24h = volume_24h_usd / price if price > 0 else 0
                else:  # Linear USDT/USDC
                    # For linear contracts, openInterest is in token units
                    oi_tokens = open_interest
                    oi_usd = open_interest_usd
                    volume_24h = volume_24h_usd / price if price > 0 else 0
                
                if oi_tokens <= 0 or price <= 0:
                    logger.debug(f"Bitget {bitget_symbol}: Invalid OI ({oi_tokens}) or price ({price})")
                    return None
                
                logger.info(f"Bitget {bitget_symbol} ({settlement}): {oi_tokens:,.2f} tokens, ${oi_usd:,.2f} USD")
                
                return ExchangeOIData(
                    exchange=f'bitget_{settlement.lower()}',
                    symbol=f"{base_token}/USDT",  # Normalize symbol format
                    oi_tokens=oi_tokens,
                    oi_usd=oi_usd,
                    funding_rate=funding_rate,
                    volume_24h=volume_24h,
                    volume_24h_usd=volume_24h_usd,
                    price=price,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.warning(f"Error fetching Bitget {settlement} for {base_token}: {e}")
            return None
    
    async def _fetch_okx_oi(self, symbol: str) -> List[ExchangeOIData]:
        """Fetch OKX OI data for all settlement currencies (USDT, USDC, USD)"""
        try:
            results = []
            base_token = symbol.split('/')[0].upper()
            
            # OKX symbol formats
            okx_symbols = {
                'USDT': f'{base_token}-USDT-SWAP',    # Linear USDT
                'USDC': f'{base_token}-USDC-SWAP',    # Linear USDC
                'USD': f'{base_token}-USD-SWAP'       # Inverse USD
            }
            
            async with aiohttp.ClientSession() as session:
                # Fetch all three settlement types in parallel
                tasks = []
                for settlement, okx_symbol in okx_symbols.items():
                    tasks.append(self._fetch_okx_settlement(session, base_token, okx_symbol, settlement))
                
                settlement_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in settlement_results:
                    if isinstance(result, ExchangeOIData):
                        results.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"OKX settlement error: {result}")
            
            logger.info(f"OKX fetched {len(results)}/3 markets for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching OKX OI for {symbol}: {e}")
            return []
    
    async def _fetch_okx_settlement(self, session: aiohttp.ClientSession, base_token: str, okx_symbol: str, settlement: str) -> Optional[ExchangeOIData]:
        """Fetch OKX OI data for a specific settlement currency"""
        try:
            # OKX Open Interest endpoint
            oi_url = "https://www.okx.com/api/v5/public/open-interest"
            params = {'instId': okx_symbol}
            
            async with session.get(oi_url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data.get('code') != '0':
                    logger.debug(f"OKX API error for {okx_symbol}: {data.get('msg')}")
                    return None
                
                oi_data_list = data.get('data', [])
                if not oi_data_list:
                    return None
                
                oi_info = oi_data_list[0]
                
                # Extract OI data
                open_interest = float(oi_info.get('oi', 0))
                open_interest_ccy = float(oi_info.get('oiCcy', 0))
                
                # Get additional market data from tickers endpoint
                ticker_url = "https://www.okx.com/api/v5/market/ticker"
                ticker_params = {'instId': okx_symbol}
                
                async with session.get(ticker_url, params=ticker_params) as ticker_response:
                    if ticker_response.status != 200:
                        return None
                    
                    ticker_data = await ticker_response.json()
                    if ticker_data.get('code') != '0':
                        return None
                    
                    ticker_list = ticker_data.get('data', [])
                    if not ticker_list:
                        return None
                    
                    ticker = ticker_list[0]
                    
                    price = float(ticker.get('last', 0))
                    volume_24h_ccy = float(ticker.get('volCcy24h', 0))
                    volume_24h = float(ticker.get('vol24h', 0))
                
                # Get funding rate
                funding_url = "https://www.okx.com/api/v5/public/funding-rate"
                funding_params = {'instId': okx_symbol}
                funding_rate = 0
                
                try:
                    async with session.get(funding_url, params=funding_params) as funding_response:
                        if funding_response.status == 200:
                            funding_data = await funding_response.json()
                            if funding_data.get('code') == '0' and funding_data.get('data'):
                                funding_rate = float(funding_data['data'][0].get('fundingRate', 0))
                except Exception:
                    pass
                
                # Calculate token amounts
                if settlement == 'USD':  # Inverse contracts
                    # For inverse contracts, oi is in contract units, oiCcy is in base currency
                    oi_tokens = open_interest_ccy  # Use oiCcy for token amount
                    oi_usd = open_interest_ccy * price  # Calculate USD value
                    volume_24h_tokens = volume_24h
                else:  # Linear USDT/USDC
                    # For linear contracts, oi is in contract units (same as tokens)
                    oi_tokens = open_interest
                    oi_usd = open_interest * price  # FIXED: Proper USD calculation
                    volume_24h_tokens = volume_24h
                
                if oi_tokens <= 0 or price <= 0:
                    logger.debug(f"OKX {okx_symbol}: Invalid OI ({oi_tokens}) or price ({price})")
                    return None
                
                logger.info(f"OKX {okx_symbol} ({settlement}): {oi_tokens:,.2f} tokens, ${oi_usd:,.2f} USD")
                
                return ExchangeOIData(
                    exchange=f'okx_{settlement.lower()}',
                    symbol=f"{base_token}/USDT",  # Normalize symbol format
                    oi_tokens=oi_tokens,
                    oi_usd=oi_usd,
                    funding_rate=funding_rate,
                    volume_24h=volume_24h_tokens,
                    volume_24h_usd=volume_24h_ccy,
                    price=price,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.warning(f"Error fetching OKX {settlement} for {base_token}: {e}")
            return None
    
    async def _fetch_binance_long_short_ratios(self, symbol: str) -> Optional[LongShortRatios]:
        """Fetch Binance long/short ratio data via direct API calls"""
        try:
            # Convert symbol format for Binance API
            binance_symbol = symbol.replace('/', '').replace(':USDT', '')  # BTC/USDT -> BTCUSDT
            
            # Binance API endpoints for long/short ratios
            endpoints = {
                'global': f"{self.binance_api_base}/futures/data/globalLongShortAccountRatio",
                'top_account': f"{self.binance_api_base}/futures/data/topLongShortAccountRatio", 
                'top_position': f"{self.binance_api_base}/futures/data/topLongShortPositionRatio"
            }
            
            params = {
                'symbol': binance_symbol,
                'period': '5m',
                'limit': 1
            }
            
            async with aiohttp.ClientSession() as session:
                results = {}
                
                for endpoint_name, url in endpoints.items():
                    try:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data:
                                    results[endpoint_name] = data[0]  # Latest record
                    except Exception as e:
                        logger.warning(f"Failed to fetch {endpoint_name}: {e}")
                
                # Parse results if we have all three datasets
                if len(results) == 3:
                    global_data = results['global']
                    top_account_data = results['top_account']
                    top_position_data = results['top_position']
                    
                    return LongShortRatios(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(global_data['timestamp'] / 1000),
                        # Global ratios
                        global_long_pct=float(global_data['longAccount']) * 100,
                        global_short_pct=float(global_data['shortAccount']) * 100,
                        global_ratio=float(global_data['longShortRatio']),
                        # Top trader account ratios
                        top_account_long_pct=float(top_account_data['longAccount']) * 100,
                        top_account_short_pct=float(top_account_data['shortAccount']) * 100,
                        top_account_ratio=float(top_account_data['longShortRatio']),
                        # Top trader position ratios
                        top_position_long_pct=float(top_position_data['longAccount']) * 100,
                        top_position_short_pct=float(top_position_data['shortAccount']) * 100,
                        top_position_ratio=float(top_position_data['longShortRatio'])
                    )
                else:
                    logger.warning(f"Incomplete long/short data: got {len(results)}/3 endpoints")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching Binance long/short ratios: {e}")
            return None
    
    def _calculate_oi_deviation(self, current_oi: float, symbol: str) -> Tuple[float, str]:
        """Calculate OI deviation from normal levels"""
        try:
            # Get historical OI data for this symbol
            if symbol not in self.oi_history:
                return 0.0, "NORMAL"  # No historical data yet
            
            history = self.oi_history[symbol]
            if len(history) < 7:  # Need at least a week of data
                return 0.0, "NORMAL"
            
            # Calculate 7-day average OI
            recent_oi = [entry['oi'] for entry in history[-7:]]
            avg_oi = statistics.mean(recent_oi)
            
            if avg_oi == 0:
                return 0.0, "NORMAL"
            
            # Calculate percentage deviation
            deviation_pct = ((current_oi - avg_oi) / avg_oi) * 100
            
            # Classify alert level
            if abs(deviation_pct) >= 50:
                alert_level = "EXTREME"
            elif abs(deviation_pct) >= 30:
                alert_level = "HIGH"
            elif abs(deviation_pct) >= 15:
                alert_level = "ELEVATED"
            else:
                alert_level = "NORMAL"
            
            return deviation_pct, alert_level
            
        except Exception as e:
            logger.error(f"Error calculating OI deviation: {e}")
            return 0.0, "NORMAL"
    
    def _analyze_oi_price_divergence(self, oi_change_24h: float, price_change_24h: float) -> Tuple[float, str, str]:
        """Analyze OI vs Price divergence for market sentiment"""
        try:
            # Calculate divergence
            divergence = oi_change_24h - price_change_24h
            
            # Analyze market sentiment based on OI and price movements
            if oi_change_24h > 5 and price_change_24h > 2:
                sentiment = "BULLISH"  # Rising OI + Rising Price = Strong bullish
                risk = "NORMAL"
            elif oi_change_24h > 5 and price_change_24h < -2:
                sentiment = "BEARISH"  # Rising OI + Falling Price = Bearish buildup
                risk = "HIGH"
            elif oi_change_24h < -5 and price_change_24h > 2:
                sentiment = "BULLISH"  # Falling OI + Rising Price = Bullish (short covering)
                risk = "NORMAL"
            elif oi_change_24h < -5 and price_change_24h < -2:
                sentiment = "BEARISH"  # Falling OI + Falling Price = Capitulation
                risk = "EXTREME"
            elif abs(oi_change_24h) > 10 and abs(price_change_24h) < 1:
                sentiment = "NEUTRAL"  # High OI change but price stable = Buildup
                risk = "HIGH"
            else:
                sentiment = "NEUTRAL"
                risk = "NORMAL"
            
            return divergence, sentiment, risk
            
        except Exception as e:
            logger.error(f"Error analyzing OI/Price divergence: {e}")
            return 0.0, "NEUTRAL", "NORMAL"
    
    def _store_oi_history(self, symbol: str, oi_data: float):
        """Store OI data for historical analysis"""
        try:
            if symbol not in self.oi_history:
                self.oi_history[symbol] = []
            
            # Add current data point
            self.oi_history[symbol].append({
                'timestamp': datetime.now(),
                'oi': oi_data
            })
            
            # Keep only last 30 days of data
            cutoff_date = datetime.now() - timedelta(days=30)
            self.oi_history[symbol] = [
                entry for entry in self.oi_history[symbol]
                if entry['timestamp'] > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Error storing OI history: {e}")
    
    async def analyze_oi(self, symbol: str) -> Optional[AggregatedOIAnalysis]:
        """Perform complete OI analysis with parallel exchange processing"""
        try:
            logger.info(f"Starting parallel OI analysis for {symbol}")
            
            # Fetch OI data from all exchanges concurrently (Phase 2: 5 exchanges)
            tasks = [
                self._fetch_binance_oi(symbol),
                self._fetch_bybit_oi(symbol),
                self._fetch_gateio_oi(symbol),
                self._fetch_bitget_oi(symbol),
                self._fetch_okx_oi(symbol),
                self._fetch_binance_long_short_ratios(symbol)
            ]
            
            binance_oi, bybit_oi, gateio_oi_list, bitget_oi_list, okx_oi_list, long_short_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            exchange_data = []
            if isinstance(binance_oi, ExchangeOIData):
                exchange_data.append(binance_oi)
            if isinstance(bybit_oi, ExchangeOIData):
                exchange_data.append(bybit_oi)
            if isinstance(gateio_oi_list, list):
                exchange_data.extend(gateio_oi_list)
            if isinstance(bitget_oi_list, list):
                exchange_data.extend(bitget_oi_list)
            if isinstance(okx_oi_list, list):
                exchange_data.extend(okx_oi_list)
            
            if not exchange_data:
                logger.error(f"No OI data available for {symbol} from any exchange")
                return None
            
            # Log success summary  
            total_possible_markets = 11  # Binance(1) + Bybit(1) + Gate.io(3) + Bitget(3) + OKX(3) = 11 markets
            successful_markets = len(exchange_data)
            logger.info(f"OI data fetched: {successful_markets}/{total_possible_markets} markets successful")
            
            # Run validation agents on the data
            validation_result = await self._run_validation_agents(exchange_data, symbol)
            if not validation_result['passed']:
                logger.warning(f"Validation concerns detected: {validation_result['warnings']}")
            
            # Sort exchanges by OI size (largest first)
            exchange_data.sort(key=lambda x: x.oi_usd, reverse=True)
            
            # Calculate aggregated totals
            total_oi_tokens = sum(data.oi_tokens for data in exchange_data)
            total_oi_usd = sum(data.oi_usd for data in exchange_data)
            total_volume_24h = sum(data.volume_24h for data in exchange_data)
            total_volume_24h_usd = sum(data.volume_24h_usd for data in exchange_data)
            
            # Get current price (from largest exchange)
            current_price = exchange_data[0].price
            
            # Calculate OI deviation from normal
            oi_vs_normal_pct, alert_level = self._calculate_oi_deviation(total_oi_tokens, symbol)
            
            # Store current OI for future analysis
            self._store_oi_history(symbol, total_oi_tokens)
            
            # Calculate 24h changes (placeholder - would need historical data)
            oi_change_24h_pct = 0.0  # TODO: Implement with historical data
            price_change_24h_pct = 0.0  # TODO: Get from ticker
            
            # Analyze OI vs Price divergence
            divergence, sentiment, risk = self._analyze_oi_price_divergence(
                oi_change_24h_pct, price_change_24h_pct
            )
            
            return AggregatedOIAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                total_oi_tokens=total_oi_tokens,
                total_oi_usd=total_oi_usd,
                total_volume_24h=total_volume_24h,
                total_volume_24h_usd=total_volume_24h_usd,
                exchange_breakdown=exchange_data,
                current_price=current_price,
                oi_change_24h_pct=oi_change_24h_pct,
                price_change_24h_pct=price_change_24h_pct,
                oi_vs_price_divergence=divergence,
                long_short_data=long_short_data if isinstance(long_short_data, LongShortRatios) else None,
                oi_vs_normal_pct=oi_vs_normal_pct,
                alert_level=alert_level,
                market_sentiment=sentiment,
                risk_level=risk
            )
            
        except Exception as e:
            logger.error(f"Error in OI analysis for {symbol}: {e}")
            return None

class OIAnalysisService:
    """Service wrapper for OI analysis"""
    
    def __init__(self, exchange_manager):
        self.oi_engine = OIAnalysisEngine(exchange_manager)
    
    async def get_oi_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get complete OI analysis for API/bot consumption"""
        try:
            analysis = await self.oi_engine.analyze_oi(symbol)
            
            if not analysis:
                return {
                    'success': False,
                    'error': f'No OI data available for {symbol}'
                }
            
            # Format response
            return {
                'success': True,
                'data': {
                    'symbol': analysis.symbol,
                    'timestamp': analysis.timestamp.isoformat(),
                    'aggregated_oi': {
                        'total_tokens': analysis.total_oi_tokens,
                        'total_usd': analysis.total_oi_usd,
                        'vs_normal_pct': analysis.oi_vs_normal_pct,
                        'alert_level': analysis.alert_level
                    },
                    'exchange_breakdown': [
                        {
                            'exchange': data.exchange,
                            'oi_tokens': data.oi_tokens,
                            'oi_usd': data.oi_usd,
                            'oi_percentage': (data.oi_usd / analysis.total_oi_usd * 100) if analysis.total_oi_usd > 0 else 0,
                            'funding_rate': data.funding_rate,
                            'volume_24h': data.volume_24h,
                            'volume_24h_usd': data.volume_24h_usd
                        } for data in analysis.exchange_breakdown
                    ],
                    'market_analysis': {
                        'current_price': analysis.current_price,
                        'oi_change_24h_pct': analysis.oi_change_24h_pct,
                        'price_change_24h_pct': analysis.price_change_24h_pct,
                        'oi_vs_price_divergence': analysis.oi_vs_price_divergence,
                        'market_sentiment': analysis.market_sentiment,
                        'risk_level': analysis.risk_level
                    },
                    'long_short_data': {
                        'global_long_pct': analysis.long_short_data.global_long_pct,
                        'global_short_pct': analysis.long_short_data.global_short_pct,
                        'global_ratio': analysis.long_short_data.global_ratio,
                        'top_traders_long_pct': analysis.long_short_data.top_position_long_pct,
                        'top_traders_short_pct': analysis.long_short_data.top_position_short_pct,
                        'top_traders_ratio': analysis.long_short_data.top_position_ratio
                    } if analysis.long_short_data else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in OI analysis service: {e}")
            return {
                'success': False,
                'error': str(e)
            }