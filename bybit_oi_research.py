#!/usr/bin/env python3
"""
Bybit Open Interest Research Script
Research and test Bybit OI API endpoints for BTC contracts
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class BybitOIResearcher:
    """Research Bybit Open Interest API endpoints and data structure."""
    
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_instruments(self, category: str) -> List[Dict]:
        """Get all available instruments for a category."""
        url = f"{self.base_url}/v5/market/instruments-info"
        params = {"category": category}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result", {}).get("list", [])
            else:
                print(f"Error getting instruments for {category}: {response.status}")
                return []
    
    async def get_open_interest(self, category: str, symbol: str, interval: str = "1d") -> Dict:
        """Get open interest data for a specific symbol."""
        url = f"{self.base_url}/v5/market/open-interest"
        params = {
            "category": category,
            "symbol": symbol,
            "intervalTime": interval,
            "limit": 1  # Just get the latest data point
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"Error getting OI for {symbol} ({category}): {response.status}")
                text = await response.text()
                print(f"Error response: {text}")
                return {}
    
    async def get_tickers(self, category: str) -> List[Dict]:
        """Get ticker data for a category."""
        url = f"{self.base_url}/v5/market/tickers"
        params = {"category": category}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result", {}).get("list", [])
            else:
                print(f"Error getting tickers for {category}: {response.status}")
                return []
    
    async def research_btc_contracts(self) -> Dict[str, Any]:
        """Research all BTC-related contracts on Bybit."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "linear_contracts": [],
            "inverse_contracts": [],
            "oi_data": {},
            "ticker_data": {}
        }
        
        # Research linear contracts (USDT/USDC)
        print("🔍 Researching linear contracts...")
        linear_instruments = await self.get_instruments("linear")
        btc_linear = [inst for inst in linear_instruments if 'BTC' in inst.get('symbol', '')]
        
        for instrument in btc_linear:
            symbol = instrument.get('symbol')
            if symbol and 'BTC' in symbol:
                results['linear_contracts'].append({
                    'symbol': symbol,
                    'status': instrument.get('status'),
                    'contractType': instrument.get('contractType'),
                    'quoteCoin': instrument.get('quoteCoin'),
                    'baseCoin': instrument.get('baseCoin'),
                    'settleCoin': instrument.get('settleCoin')
                })
                print(f"  Linear: {symbol} (quote: {instrument.get('quoteCoin')}, settle: {instrument.get('settleCoin')})")
        
        # Research inverse contracts (BTC-margined)
        print("\n🔍 Researching inverse contracts...")
        inverse_instruments = await self.get_instruments("inverse")
        btc_inverse = [inst for inst in inverse_instruments if 'BTC' in inst.get('symbol', '')]
        
        for instrument in btc_inverse:
            symbol = instrument.get('symbol')
            if symbol and 'BTC' in symbol:
                results['inverse_contracts'].append({
                    'symbol': symbol,
                    'status': instrument.get('status'),
                    'contractType': instrument.get('contractType'),
                    'quoteCoin': instrument.get('quoteCoin'),
                    'baseCoin': instrument.get('baseCoin'),
                    'settleCoin': instrument.get('settleCoin')
                })
                print(f"  Inverse: {symbol} (quote: {instrument.get('quoteCoin')}, settle: {instrument.get('settleCoin')})")
        
        # Get OI data for key BTC contracts
        print("\n📊 Fetching Open Interest data...")
        target_contracts = [
            ('linear', 'BTCUSDT'),
            ('linear', 'BTCUSDC'), 
            ('inverse', 'BTCUSD')
        ]
        
        for category, symbol in target_contracts:
            print(f"  Getting OI for {symbol} ({category})...")
            oi_data = await self.get_open_interest(category, symbol)
            if oi_data:
                results['oi_data'][f"{symbol}_{category}"] = oi_data
                
                # Extract latest OI value
                result = oi_data.get('result', {})
                if result and 'list' in result and result['list']:
                    latest_oi = result['list'][0]
                    oi_value = latest_oi.get('openInterest', 0)
                    print(f"    OI: {oi_value}")
        
        # Get ticker data for price context
        print("\n💰 Fetching ticker data for price context...")
        for category in ['linear', 'inverse']:
            tickers = await self.get_tickers(category)
            btc_tickers = [t for t in tickers if 'BTC' in t.get('symbol', '')]
            
            for ticker in btc_tickers:
                symbol = ticker.get('symbol')
                if symbol and 'BTC' in symbol:
                    results['ticker_data'][f"{symbol}_{category}"] = {
                        'symbol': symbol,
                        'lastPrice': ticker.get('lastPrice'),
                        'volume24h': ticker.get('volume24h'),
                        'turnover24h': ticker.get('turnover24h'),
                        'openInterest': ticker.get('openInterest'),  # Some tickers include OI
                        'openInterestValue': ticker.get('openInterestValue')
                    }
                    print(f"    {symbol}: ${ticker.get('lastPrice')} (OI: {ticker.get('openInterest')})")
        
        return results

async def main():
    """Main research function."""
    print("🚀 Starting Bybit Open Interest Research...")
    print("=" * 60)
    
    async with BybitOIResearcher() as researcher:
        results = await researcher.research_btc_contracts()
    
    # Save results to file
    output_file = "/Users/screener-m3/projects/crypto-assistant/bybit_oi_research_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    # Summary analysis
    print("\n📊 SUMMARY ANALYSIS:")
    print("=" * 40)
    
    print(f"Linear contracts found: {len(results['linear_contracts'])}")
    for contract in results['linear_contracts']:
        print(f"  - {contract['symbol']} (settle: {contract['settleCoin']})")
    
    print(f"\nInverse contracts found: {len(results['inverse_contracts'])}")
    for contract in results['inverse_contracts']:
        print(f"  - {contract['symbol']} (settle: {contract['settleCoin']})")
    
    print(f"\nOI data collected: {len(results['oi_data'])}")
    for key, data in results['oi_data'].items():
        result = data.get('result', {})
        if result and 'list' in result and result['list']:
            oi_value = result['list'][0].get('openInterest', 'N/A')
            print(f"  - {key}: {oi_value}")
    
    print(f"\nTicker data collected: {len(results['ticker_data'])}")
    for key, data in results['ticker_data'].items():
        price = data.get('lastPrice', 'N/A')
        oi = data.get('openInterest', 'N/A')
        oi_value = data.get('openInterestValue', 'N/A')
        print(f"  - {key}: ${price} (OI: {oi}, OI Value: {oi_value})")

if __name__ == "__main__":
    asyncio.run(main())