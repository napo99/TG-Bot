#!/usr/bin/env python3
"""
UNIFIED OI AGGREGATOR: Complete 13-market system aggregation
Combines all 5 exchanges with external validation and target spec formatting
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger

# Import all working providers
from binance_oi_provider import BinanceOIProvider
from bybit_oi_provider import BybitOIProvider
from okx_oi_provider import OKXOIProvider
from gateio_oi_provider_working import GateIOOIProviderWorking
from bitget_oi_provider_working import BitgetOIProviderWorking

from oi_engine_v2 import ExchangeOIResult, MarketType

@dataclass
class UnifiedOIResponse:
    """Unified response matching target specification format"""
    base_symbol: str
    timestamp: datetime
    total_markets: int
    
    # Aggregated totals
    aggregated_oi: Dict[str, Any]
    
    # Exchange breakdown
    exchange_breakdown: List[Dict[str, Any]]
    
    # Market category breakdown  
    market_categories: Dict[str, Any]
    
    # Validation status
    validation_summary: Dict[str, Any]

class UnifiedOIAggregator:
    """
    Unified OI Aggregator for complete 13-market system
    Aggregates data from all 5 exchanges with validation
    """
    
    def __init__(self):
        # Initialize all providers
        self.providers = {
            'binance': BinanceOIProvider(),
            'bybit': BybitOIProvider(), 
            'okx': OKXOIProvider(),
            'gateio': GateIOOIProviderWorking(),
            'bitget': BitgetOIProviderWorking()
        }
        
        self.exchange_priority = ['binance', 'bybit', 'okx', 'gateio', 'bitget']
    
    async def get_unified_oi_data(self, base_symbol: str) -> UnifiedOIResponse:
        """Get unified OI data from all exchanges"""
        logger.info(f"🎯 Starting unified OI aggregation for {base_symbol}")
        
        # Fetch data from all exchanges in parallel
        exchange_tasks = {}
        for exchange, provider in self.providers.items():
            exchange_tasks[exchange] = provider.get_oi_data(base_symbol)
        
        exchange_results = await asyncio.gather(
            *exchange_tasks.values(), 
            return_exceptions=True
        )
        
        # Process results
        successful_exchanges = {}
        failed_exchanges = {}
        
        for i, (exchange, result) in enumerate(zip(exchange_tasks.keys(), exchange_results)):
            if isinstance(result, Exception):
                failed_exchanges[exchange] = str(result)
                logger.error(f"❌ {exchange.title()} failed: {result}")
            elif result.validation_passed:
                successful_exchanges[exchange] = result
                logger.info(f"✅ {exchange.title()}: {result.total_oi_tokens:,.0f} {base_symbol} (${result.total_oi_usd/1e9:.1f}B)")
            else:
                failed_exchanges[exchange] = f"Validation failed: {result.validation_errors}"
                logger.warning(f"⚠️ {exchange.title()}: Validation failed")
        
        # Build unified response
        return self._build_unified_response(
            base_symbol, 
            successful_exchanges, 
            failed_exchanges
        )
    
    def _build_unified_response(self, base_symbol: str, successful_exchanges: Dict, failed_exchanges: Dict) -> UnifiedOIResponse:
        """Build unified response matching target specification"""
        
        # Calculate aggregated totals
        total_oi_tokens = sum(result.total_oi_tokens for result in successful_exchanges.values())
        total_oi_usd = sum(result.total_oi_usd for result in successful_exchanges.values())
        total_volume_24h = sum(result.total_volume_24h for result in successful_exchanges.values())
        total_volume_24h_usd = sum(result.total_volume_24h_usd for result in successful_exchanges.values())
        
        # Build exchange breakdown
        exchange_breakdown = []
        for exchange in self.exchange_priority:
            if exchange in successful_exchanges:
                result = successful_exchanges[exchange]
                
                # Calculate weighted average funding rate
                total_oi_for_funding = sum(m.oi_usd for m in result.markets if m.funding_rate != 0)
                if total_oi_for_funding > 0:
                    weighted_funding = sum(
                        m.funding_rate * m.oi_usd for m in result.markets if m.funding_rate != 0
                    ) / total_oi_for_funding
                else:
                    weighted_funding = 0.0
                
                exchange_data = {
                    "exchange": exchange,
                    "oi_tokens": result.total_oi_tokens,
                    "oi_usd": result.total_oi_usd,
                    "oi_percentage": (result.total_oi_usd / total_oi_usd * 100) if total_oi_usd > 0 else 0,
                    "funding_rate": weighted_funding,
                    "volume_24h": result.total_volume_24h,
                    "volume_24h_usd": result.total_volume_24h_usd,
                    "markets": len(result.markets),
                    "market_breakdown": [
                        {
                            "type": market.market_type.value,
                            "symbol": market.symbol,
                            "oi_tokens": market.oi_tokens,
                            "oi_usd": market.oi_usd,
                            "price": market.price,
                            "funding_rate": market.funding_rate,
                            "volume_24h": market.volume_24h,
                            "volume_24h_usd": market.volume_24h_usd
                        }
                        for market in result.markets
                    ]
                }
                exchange_breakdown.append(exchange_data)
        
        # Build market category breakdown (USDT/USDC/USD aggregated across exchanges)
        market_categories = self._calculate_market_categories(successful_exchanges, total_oi_usd)
        
        # Build validation summary
        validation_summary = {
            "successful_exchanges": len(successful_exchanges),
            "failed_exchanges": len(failed_exchanges), 
            "total_markets": sum(len(result.markets) for result in successful_exchanges.values()),
            "validation_passed": len(successful_exchanges) >= 3,  # At least 3 exchanges working
            "failed_details": failed_exchanges
        }
        
        aggregated_oi = {
            "total_tokens": total_oi_tokens,
            "total_usd": total_oi_usd,
            "total_volume_24h": total_volume_24h,
            "total_volume_24h_usd": total_volume_24h_usd,
            "exchanges_count": len(successful_exchanges)
        }
        
        return UnifiedOIResponse(
            base_symbol=base_symbol,
            timestamp=datetime.now(),
            total_markets=validation_summary["total_markets"],
            aggregated_oi=aggregated_oi,
            exchange_breakdown=exchange_breakdown,
            market_categories=market_categories,
            validation_summary=validation_summary
        )
    
    def _calculate_market_categories(self, successful_exchanges: Dict, total_oi_usd: float) -> Dict[str, Any]:
        """Calculate aggregated market categories across all exchanges"""
        
        category_totals = {
            MarketType.USDT: {"tokens": 0, "usd": 0, "exchanges": 0},
            MarketType.USDC: {"tokens": 0, "usd": 0, "exchanges": 0}, 
            MarketType.USD: {"tokens": 0, "usd": 0, "exchanges": 0}
        }
        
        for exchange, result in successful_exchanges.items():
            for market in result.markets:
                category_totals[market.market_type]["tokens"] += market.oi_tokens
                category_totals[market.market_type]["usd"] += market.oi_usd
            
            # Count unique exchanges per category
            if result.usdt_markets:
                category_totals[MarketType.USDT]["exchanges"] += 1
            if result.usdc_markets:
                category_totals[MarketType.USDC]["exchanges"] += 1  
            if result.usd_markets:
                category_totals[MarketType.USD]["exchanges"] += 1
        
        return {
            "usdt_stable": {
                "total_tokens": category_totals[MarketType.USDT]["tokens"],
                "total_usd": category_totals[MarketType.USDT]["usd"],
                "percentage": (category_totals[MarketType.USDT]["usd"] / total_oi_usd * 100) if total_oi_usd > 0 else 0,
                "exchanges": category_totals[MarketType.USDT]["exchanges"]
            },
            "usdc_stable": {
                "total_tokens": category_totals[MarketType.USDC]["tokens"], 
                "total_usd": category_totals[MarketType.USDC]["usd"],
                "percentage": (category_totals[MarketType.USDC]["usd"] / total_oi_usd * 100) if total_oi_usd > 0 else 0,
                "exchanges": category_totals[MarketType.USDC]["exchanges"]
            },
            "usd_inverse": {
                "total_tokens": category_totals[MarketType.USD]["tokens"],
                "total_usd": category_totals[MarketType.USD]["usd"], 
                "percentage": (category_totals[MarketType.USD]["usd"] / total_oi_usd * 100) if total_oi_usd > 0 else 0,
                "exchanges": category_totals[MarketType.USD]["exchanges"]
            }
        }
    
    async def close(self):
        """Close all provider sessions"""
        for provider in self.providers.values():
            await provider.close()

# Testing and validation function
async def test_unified_system():
    """Test the complete unified 13-market system"""
    print("🚀 Testing UNIFIED 13-Market OI System")
    print("=" * 60)
    
    aggregator = UnifiedOIAggregator()
    
    try:
        result = await aggregator.get_unified_oi_data("BTC")
        
        print(f"\n📊 UNIFIED SYSTEM RESULTS:")
        print(f"Base Symbol: {result.base_symbol}")
        print(f"Total Markets: {result.total_markets}")
        print(f"Total OI: {result.aggregated_oi['total_tokens']:,.0f} BTC (${result.aggregated_oi['total_usd']/1e9:.1f}B)")
        print(f"Successful Exchanges: {result.validation_summary['successful_exchanges']}/5")
        
        print(f"\n📈 EXCHANGE BREAKDOWN:")
        for exchange_data in result.exchange_breakdown:
            exchange = exchange_data['exchange']
            oi_tokens = exchange_data['oi_tokens']
            oi_usd = exchange_data['oi_usd']
            percentage = exchange_data['oi_percentage']
            markets = exchange_data['markets']
            
            print(f"  {exchange.upper()}: {oi_tokens:,.0f} BTC (${oi_usd/1e9:.1f}B) - {percentage:.1f}% - {markets} markets")
            
            for market in exchange_data['market_breakdown']:
                market_type = market['type']
                symbol = market['symbol']
                tokens = market['oi_tokens']
                usd = market['oi_usd']
                print(f"    └── {market_type}: {symbol} - {tokens:,.0f} BTC (${usd/1e9:.1f}B)")
        
        print(f"\n🏷️ MARKET CATEGORIES:")
        categories = result.market_categories
        
        usdt = categories['usdt_stable']
        usdc = categories['usdc_stable'] 
        usd = categories['usd_inverse']
        
        print(f"  USDT Stable: {usdt['total_tokens']:,.0f} BTC (${usdt['total_usd']/1e9:.1f}B) - {usdt['percentage']:.1f}% - {usdt['exchanges']} exchanges")
        print(f"  USDC Stable: {usdc['total_tokens']:,.0f} BTC (${usdc['total_usd']/1e9:.1f}B) - {usdc['percentage']:.1f}% - {usdc['exchanges']} exchanges")
        print(f"  USD Inverse: {usd['total_tokens']:,.0f} BTC (${usd['total_usd']/1e9:.1f}B) - {usd['percentage']:.1f}% - {usd['exchanges']} exchanges")
        
        print(f"\n✅ VALIDATION SUMMARY:")
        validation = result.validation_summary
        print(f"  Status: {'✅ PASSED' if validation['validation_passed'] else '❌ FAILED'}")
        print(f"  Working: {validation['successful_exchanges']}/5 exchanges")
        print(f"  Total Markets: {validation['total_markets']}")
        
        if validation['failed_details']:
            print(f"  Failed Exchanges: {list(validation['failed_details'].keys())}")
        
        # Save detailed results
        output_file = "/Users/screener-m3/projects/crypto-assistant/unified_oi_results.json"
        with open(output_file, 'w') as f:
            # Convert to JSON-serializable format
            result_dict = asdict(result)
            result_dict['timestamp'] = result_dict['timestamp'].isoformat()
            json.dump(result_dict, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: unified_oi_results.json")
        
        return result
        
    except Exception as e:
        print(f"❌ Unified system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await aggregator.close()

if __name__ == "__main__":
    asyncio.run(test_unified_system())