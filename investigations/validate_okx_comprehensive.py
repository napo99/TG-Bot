#!/usr/bin/env python3
"""
OKX COMPREHENSIVE VALIDATION AGENT
Validates OKX data across different endpoints, methods, and symbol naming conventions
"""

import aiohttp
import asyncio
import json

class OKXComprehensiveValidator:
    def __init__(self):
        self.okx_base = "https://www.okx.com"
        
    async def test_all_okx_endpoints(self):
        """Test all possible OKX endpoints for BTC data"""
        print("🔍 COMPREHENSIVE OKX ENDPOINT VALIDATION")
        print("=" * 50)
        
        # Test multiple endpoint categories
        endpoints_to_test = [
            # Market data endpoints
            ("/api/v5/market/tickers?instType=SWAP", "All SWAP Tickers"),
            ("/api/v5/market/ticker?instId=BTC-USDT-SWAP", "BTC-USDT-SWAP Ticker"),
            ("/api/v5/market/ticker?instId=BTC-USDC-SWAP", "BTC-USDC-SWAP Ticker"), 
            ("/api/v5/market/ticker?instId=BTC-USD-SWAP", "BTC-USD-SWAP Ticker"),
            
            # Open Interest specific endpoints
            ("/api/v5/public/open-interest?instType=SWAP", "All SWAP Open Interest"),
            ("/api/v5/public/open-interest?instId=BTC-USDT-SWAP", "BTC-USDT OI Specific"),
            ("/api/v5/public/open-interest?instId=BTC-USDC-SWAP", "BTC-USDC OI Specific"),
            ("/api/v5/public/open-interest?instId=BTC-USD-SWAP", "BTC-USD OI Specific"),
            
            # Instruments endpoints
            ("/api/v5/public/instruments?instType=SWAP", "SWAP Instruments"),
            ("/api/v5/public/instruments?instType=FUTURES", "FUTURES Instruments"),
            ("/api/v5/public/instruments?instType=OPTION", "OPTION Instruments"),
            
            # Alternative naming conventions to test
            ("/api/v5/market/ticker?instId=BTCUSDT-SWAP", "BTCUSDT-SWAP (no dash)"),
            ("/api/v5/market/ticker?instId=BTC_USDT_SWAP", "BTC_USDT_SWAP (underscore)"),
            ("/api/v5/market/ticker?instId=BTC-USDT-PERP", "BTC-USDT-PERP (perp naming)"),
        ]
        
        btc_data_found = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints_to_test:
                try:
                    print(f"📊 Testing: {description}")
                    print(f"   Endpoint: {endpoint}")
                    
                    async with session.get(f"{self.okx_base}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('code') == '0' and data.get('data'):
                                response_data = data['data']
                                
                                if isinstance(response_data, list):
                                    # Look for BTC instruments
                                    btc_items = []
                                    for item in response_data:
                                        if isinstance(item, dict):
                                            inst_id = item.get('instId', '')
                                            if 'BTC' in inst_id:
                                                btc_items.append(item)
                                    
                                    print(f"   ✅ Found {len(btc_items)} BTC instruments")
                                    
                                    for item in btc_items:
                                        inst_id = item.get('instId', 'Unknown')
                                        print(f"     📋 {inst_id}:")
                                        
                                        # Extract all relevant fields
                                        relevant_fields = {}
                                        for key, value in item.items():
                                            if any(term in key.lower() for term in ['vol', 'oi', 'size', 'amount', 'last', 'price']):
                                                relevant_fields[key] = value
                                        
                                        # Display key metrics
                                        for field, value in relevant_fields.items():
                                            try:
                                                if isinstance(value, str) and value.replace('.', '').isdigit():
                                                    val = float(value)
                                                    if val > 0:
                                                        print(f"       {field}: {val:,.2f}")
                                                elif isinstance(value, (int, float)) and value > 0:
                                                    print(f"       {field}: {value:,.2f}")
                                            except (ValueError, TypeError):
                                                if value not in ['', '0', 0]:
                                                    print(f"       {field}: {value}")
                                        
                                        # Store for comparison
                                        btc_data_found[f"{endpoint}:{inst_id}"] = {
                                            'endpoint': endpoint,
                                            'inst_id': inst_id,
                                            'data': relevant_fields
                                        }
                                
                                elif isinstance(response_data, dict):
                                    # Single instrument response
                                    inst_id = response_data.get('instId', 'Unknown')
                                    print(f"   ✅ Single instrument: {inst_id}")
                                    
                                    relevant_fields = {}
                                    for key, value in response_data.items():
                                        if any(term in key.lower() for term in ['vol', 'oi', 'size', 'amount', 'last', 'price']):
                                            relevant_fields[key] = value
                                    
                                    for field, value in relevant_fields.items():
                                        print(f"     {field}: {value}")
                                    
                                    btc_data_found[f"{endpoint}:{inst_id}"] = {
                                        'endpoint': endpoint,
                                        'inst_id': inst_id,
                                        'data': relevant_fields
                                    }
                            else:
                                print(f"   ❌ API Error: {data.get('msg', 'Unknown error')}")
                        else:
                            print(f"   ❌ HTTP Status {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                
                print("")
        
        return btc_data_found
    
    async def validate_current_system_vs_alternatives(self):
        """Compare our current system data with alternative endpoints"""
        print("🔍 VALIDATING CURRENT SYSTEM VS ALTERNATIVES")
        print("=" * 45)
        
        # Get current system data
        print("📊 OUR CURRENT SYSTEM DATA:")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
                    system_data = await response.json()
            
            okx_data = None
            for exchange in system_data.get('exchange_breakdown', []):
                if exchange['exchange'].lower() == 'okx':
                    okx_data = exchange
                    break
            
            if okx_data:
                print(f"  Total OI: {okx_data['oi_tokens']:,.0f} BTC (${okx_data['oi_usd']/1e9:.1f}B)")
                print(f"  Total Volume: {sum(m['volume_24h'] for m in okx_data.get('market_breakdown', [])):,.0f} BTC")
                print(f"  Markets: {okx_data['markets']}")
                print("")
                
                for market in okx_data.get('market_breakdown', []):
                    symbol = market['symbol']
                    oi_tokens = market['oi_tokens']
                    volume_24h = market['volume_24h']
                    price = market['price']
                    
                    print(f"  {symbol}:")
                    print(f"    OI: {oi_tokens:,.0f} BTC")
                    print(f"    Volume: {volume_24h:,.0f} BTC")
                    print(f"    Price: ${price:,.2f}")
                
                return okx_data
            else:
                print("❌ No OKX data in current system")
                return None
                
        except Exception as e:
            print(f"❌ Error getting current system data: {e}")
            return None
    
    async def cross_validate_data_consistency(self, btc_data_found, current_system):
        """Cross-validate data consistency across different sources"""
        print("\n🔍 CROSS-VALIDATION ANALYSIS")
        print("=" * 35)
        
        if not current_system:
            print("❌ No current system data to compare")
            return
        
        print("📊 COMPARING DATA SOURCES:")
        
        # Look for matching symbols in different endpoints
        symbols_to_check = ['BTC-USDT-SWAP', 'BTC-USDC-SWAP', 'BTC-USD-SWAP']
        
        for symbol in symbols_to_check:
            print(f"\n🔍 SYMBOL: {symbol}")
            
            # Find this symbol in current system
            system_market = None
            for market in current_system.get('market_breakdown', []):
                if market['symbol'] == symbol:
                    system_market = market
                    break
            
            if system_market:
                print(f"  📊 Our System:")
                print(f"    OI: {system_market['oi_tokens']:,.0f} BTC")
                print(f"    Volume: {system_market['volume_24h']:,.0f} BTC")
                print(f"    Price: ${system_market['price']:,.2f}")
            
            # Find this symbol in alternative endpoints
            alternative_sources = []
            for key, data in btc_data_found.items():
                if data['inst_id'] == symbol:
                    alternative_sources.append(data)
            
            if alternative_sources:
                print(f"  📋 Alternative Sources Found: {len(alternative_sources)}")
                for i, source in enumerate(alternative_sources, 1):
                    print(f"    Source {i}: {source['endpoint']}")
                    data = source['data']
                    
                    # Extract comparable metrics
                    if 'oi' in data:
                        print(f"      OI (oi): {data['oi']}")
                    if 'oiCcy' in data:
                        print(f"      OI (oiCcy): {data['oiCcy']}")
                    if 'vol24h' in data:
                        print(f"      Volume (vol24h): {data['vol24h']}")
                    if 'volCcy24h' in data:
                        print(f"      Volume (volCcy24h): {data['volCcy24h']}")
                    if 'last' in data:
                        print(f"      Price (last): {data['last']}")
            else:
                print(f"  ⚠️ No alternative sources found for {symbol}")

async def main():
    validator = OKXComprehensiveValidator()
    
    print("🚨 OKX COMPREHENSIVE VALIDATION")
    print("=" * 40)
    print("📋 Goal: Validate OKX data across all endpoints and methods")
    print("📋 Check: Symbol naming, OI methods, volume calculations")
    print("📋 Verify: Data consistency and realistic numbers")
    print("")
    
    # Step 1: Test all possible endpoints
    btc_data_found = await validator.test_all_okx_endpoints()
    
    # Step 2: Get current system data
    current_system = await validator.validate_current_system_vs_alternatives()
    
    # Step 3: Cross-validate consistency
    await validator.cross_validate_data_consistency(btc_data_found, current_system)
    
    print("\n🎯 COMPREHENSIVE VALIDATION COMPLETE")
    print("Review findings above to confirm OKX data integrity")

if __name__ == "__main__":
    asyncio.run(main())