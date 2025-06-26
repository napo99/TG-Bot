#!/usr/bin/env python3
"""
HYPERLIQUID OI PROVIDER: DEX-based perpetuals tracking
Direct API integration for the largest decentralized derivatives exchange
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger

from oi_engine_v2 import (
    BaseExchangeOIProvider, 
    MarketOIData, 
    ExchangeOIResult, 
    MarketType
)

class HyperliquidOIProvider(BaseExchangeOIProvider):
    """
    Hyperliquid OI Provider for DEX perpetuals
    
    Key Features:
    - Largest decentralized derivatives exchange
    - Direct L1 blockchain-based perpetuals
    - Single unified market structure (no separate USDT/USD)
    - Real-time on-chain data
    """
    
    def __init__(self):
        super().__init__("hyperliquid")
        self.api_base = "https://api.hyperliquid.xyz"
        
        # Hyperliquid API endpoints
        self.endpoints = {
            'info': f"{self.api_base}/info",
        }
    
    def get_supported_market_types(self) -> List[MarketType]:
        """Hyperliquid uses USDC as native settlement currency"""
        return [MarketType.USDC]  # Native USDC settlement on L1
    
    def format_symbol(self, base_symbol: str, market_type: MarketType) -> str:
        """
        Hyperliquid symbol formatting - returns the symbol name for universe lookup
        
        Args:
            base_symbol: e.g. "BTC", "ETH", "SOL"
            market_type: MarketType.USDC (native)
            
        Returns:
            Symbol name for universe lookup
        """
        return base_symbol.upper()
    
    async def get_oi_data(self, base_symbol: str) -> Optional[ExchangeOIResult]:
        """
        Fetch comprehensive OI data from Hyperliquid DEX
        
        Hyperliquid API Structure:
        - metaAndAssetCtxs: Returns [meta, asset_contexts]
        - asset_contexts[0]: BTC perpetual data
        - Fields: openInterest, dayNtlVlm, dayBaseVlm, markPx, funding
        """
        logger.info(f"🟣 Fetching Hyperliquid OI for {base_symbol}")
        
        try:
            session = await self.get_session()
            
            # Get asset contexts (includes OI, volume, price, funding)
            async with session.post(self.endpoints['info'], 
                                  json={"type": "metaAndAssetCtxs"}) as response:
                if response.status != 200:
                    logger.error(f"Hyperliquid API error: HTTP {response.status}")
                    return None
                
                data = await response.json()
                
                if not isinstance(data, list) or len(data) < 2:
                    logger.error("Hyperliquid API: Invalid response structure")
                    return None
                
                meta, asset_contexts = data[0], data[1]
                
                # Find asset index by symbol in universe
                universe = meta.get('universe', [])
                asset_index = None
                
                target_symbol = base_symbol.upper()
                for i, asset in enumerate(universe):
                    if asset.get('name') == target_symbol:
                        asset_index = i
                        break
                
                if asset_index is None:
                    logger.error(f"Hyperliquid: Asset {target_symbol} not found in universe")
                    return None
                
                if asset_index >= len(asset_contexts):
                    logger.error(f"Hyperliquid: Asset context for {target_symbol} not available")
                    return None
                
                asset_data = asset_contexts[asset_index]
                
                # Extract perpetual data for this asset
                market_data = await self._process_perpetual_data(asset_data, base_symbol, target_symbol)
                
                if not market_data:
                    logger.error(f"Failed to process Hyperliquid {target_symbol} data")
                    return None
                
                # Create exchange result
                total_oi_tokens = market_data.oi_tokens
                total_oi_usd = market_data.oi_usd
                total_volume_24h = market_data.volume_24h
                total_volume_24h_usd = market_data.volume_24h_usd
                
                logger.info(f"✅ Hyperliquid {target_symbol}: {total_oi_tokens:,.0f} {target_symbol} (${total_oi_usd/1e9:.1f}B)")
                
                return ExchangeOIResult(
                    exchange="hyperliquid",
                    base_symbol=base_symbol,
                    markets=[market_data],
                    total_oi_tokens=total_oi_tokens,
                    total_oi_usd=total_oi_usd,
                    total_volume_24h=total_volume_24h,
                    total_volume_24h_usd=total_volume_24h_usd,
                    usdt_markets=[],  # No USDT markets
                    usdc_markets=[market_data],  # Native USDC settlement
                    usd_markets=[],   # No inverse markets
                    validation_passed=True,
                    validation_errors=[]
                )
                
        except Exception as e:
            logger.error(f"❌ Hyperliquid error: {str(e)}")
            return None
    
    async def _process_perpetual_data(self, asset_data: Dict[str, Any], base_symbol: str, symbol_name: str) -> Optional[MarketOIData]:
        """
        Process perpetual data from Hyperliquid API for any asset
        
        API Fields:
        - openInterest: OI in base currency (e.g. BTC, ETH, SOL)
        - dayNtlVlm: 24h notional volume in USD
        - dayBaseVlm: 24h base volume in base currency
        - markPx: Mark price in USD
        - funding: Funding rate
        - oraclePx: Oracle price
        """
        try:
            # Extract raw data
            oi_tokens = float(asset_data.get('openInterest', 0))
            volume_24h = float(asset_data.get('dayBaseVlm', 0))  # Volume in base currency
            volume_24h_usd = float(asset_data.get('dayNtlVlm', 0))  # USD volume
            mark_price = float(asset_data.get('markPx', 0))
            funding_rate = float(asset_data.get('funding', 0))
            oracle_price = float(asset_data.get('oraclePx', 0))
            
            # Use mark price as primary, oracle as backup
            price = mark_price if mark_price > 0 else oracle_price
            
            if oi_tokens <= 0 or price <= 0:
                logger.warning(f"Hyperliquid {symbol_name}: Invalid data - OI: {oi_tokens}, Price: {price}")
                return None
            
            # Calculate USD OI
            oi_usd = oi_tokens * price
            
            # Validation: Cross-check volume calculations
            if volume_24h > 0 and volume_24h_usd > 0:
                implied_price = volume_24h_usd / volume_24h
                price_diff_pct = abs(price - implied_price) / price * 100
                if price_diff_pct > 10:  # >10% difference is suspicious
                    logger.warning(f"Hyperliquid price validation: Mark={price}, Implied={implied_price:.2f}, Diff={price_diff_pct:.1f}%")
            
            return MarketOIData(
                exchange="hyperliquid",
                symbol=f"{symbol_name}-PERP",  # Generic perpetual naming
                base_symbol=base_symbol,
                market_type=MarketType.USDC,  # Native USDC settlement
                oi_tokens=oi_tokens,
                oi_usd=oi_usd,
                price=price,
                funding_rate=funding_rate,
                volume_24h=volume_24h,
                volume_24h_usd=volume_24h_usd,
                timestamp=datetime.now(),
                api_source="metaAndAssetCtxs",
                calculation_method=f"dex: {oi_tokens:,.0f} {symbol_name} × ${price:,.2f}",
                price_validated=price_diff_pct < 10 if 'price_diff_pct' in locals() else False,
                calculation_validated=True,
                api_validated=True
            )
            
        except Exception as e:
            logger.error(f"❌ Hyperliquid {symbol_name} processing error: {str(e)}")
            return None

    async def get_funding_rates(self, base_symbol: str) -> Dict[str, float]:
        """Get funding rates for specified Hyperliquid asset"""
        try:
            session = await self.get_session()
            
            async with session.post(self.endpoints['info'], 
                                  json={"type": "metaAndAssetCtxs"}) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) >= 2:
                        meta, asset_contexts = data[0], data[1]
                        
                        # Find asset index by symbol in universe
                        universe = meta.get('universe', [])
                        target_symbol = base_symbol.upper()
                        
                        for i, asset in enumerate(universe):
                            if asset.get('name') == target_symbol:
                                if i < len(asset_contexts):
                                    asset_data = asset_contexts[i]
                                    funding_rate = float(asset_data.get('funding', 0))
                                    
                                    return {
                                        f'{target_symbol}-PERP': funding_rate
                                    }
                                break
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Hyperliquid funding rates error: {str(e)}")
            return {}

    async def validate_api_connection(self) -> bool:
        """Validate Hyperliquid API connectivity"""
        try:
            session = await self.get_session()
            
            async with session.post(self.endpoints['info'], 
                                  json={"type": "meta"}) as response:
                if response.status == 200:
                    data = await response.json()
                    # Should return universe of assets
                    return 'universe' in data
                    
            return False
            
        except Exception as e:
            logger.error(f"❌ Hyperliquid API validation error: {str(e)}")
            return False

# Export for unified aggregator
__all__ = ['HyperliquidOIProvider']