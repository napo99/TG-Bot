#!/usr/bin/env python3
"""
GATE.IO OI FIX INVESTIGATION AGENT
Deep investigation into Gate.io API to find missing $6B in OI data
"""

import aiohttp
import asyncio
import json

class GateIOOIFixer:
    def __init__(self):
        self.base_url = "https://api.gateio.ws"
        
    async def investigate_gateio_api_endpoints(self):
        """Investigate all Gate.io API endpoints for BTC contracts"""
        print("🔍 COMPREHENSIVE GATE.IO API INVESTIGATION")
        print("=" * 45)
        print("🎯 Goal: Find missing $6B in OI data")
        print("📊 Current: $0.7B | Target: ~$6.7B (Coinglass)")
        print("")
        
        endpoints_to_test = [
            # Futures endpoints
            ("/api/v4/futures/usdt/contracts", "USDT Perpetual Contracts"),
            ("/api/v4/futures/btc/contracts", "BTC Perpetual Contracts"),
            ("/api/v4/futures/usdt/tickers", "USDT Perpetual Tickers"),
            ("/api/v4/futures/btc/tickers", "BTC Perpetual Tickers"),
            
            # Delivery endpoints (quarterly/expiry contracts)
            ("/api/v4/delivery/usdt/contracts", "USDT Delivery Contracts"),
            ("/api/v4/delivery/btc/contracts", "BTC Delivery Contracts"),
            ("/api/v4/delivery/usdt/tickers", "USDT Delivery Tickers"),
            ("/api/v4/delivery/btc/tickers", "BTC Delivery Tickers"),
            
            # Spot margin (if applicable)
            ("/api/v4/margin/currencies", "Margin Currencies"),
            ("/api/v4/margin/currency_pairs", "Margin Pairs"),
        ]
        
        btc_contracts_found = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints_to_test:
                try:
                    print(f"📊 Testing: {description}")
                    print(f"   Endpoint: {endpoint}")
                    
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if isinstance(data, list):
                                # Look for BTC contracts
                                btc_items = []
                                for item in data:
                                    if isinstance(item, dict):
                                        name = item.get('name', '')
                                        contract = item.get('contract', '')
                                        if 'BTC' in name or 'BTC' in contract:
                                            btc_items.append(item)
                                
                                print(f"   ✅ Status 200 - Found {len(btc_items)} BTC-related items")
                                
                                for item in btc_items:
                                    contract_name = item.get('name', item.get('contract', 'Unknown'))
                                    
                                    # Look for size/OI related fields
                                    oi_fields = []
                                    for key, value in item.items():
                                        if any(term in key.lower() for term in ['size', 'open', 'interest', 'amount', 'volume']):
                                            oi_fields.append((key, value))
                                    
                                    contract_info = {
                                        'endpoint': endpoint,
                                        'contract': contract_name,
                                        'data': item,
                                        'oi_fields': oi_fields
                                    }
                                    btc_contracts_found.append(contract_info)
                                    
                                    print(f"     📋 {contract_name}")
                                    if oi_fields:
                                        print(f"       OI-related fields: {[f[0] for f in oi_fields[:3]]}")
                                        print(f"       Sample values: {[(f[0], f[1]) for f in oi_fields[:2]]}")
                            
                            elif isinstance(data, dict):
                                print(f"   ✅ Status 200 - Dict response")
                                # Check if it contains BTC data
                                if any('BTC' in str(v) for v in data.values() if isinstance(v, str)):
                                    print(f"     📋 Contains BTC references")
                            
                        else:
                            print(f"   ❌ Status {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                
                print("")
        
        return btc_contracts_found
    
    async def analyze_contract_details(self, btc_contracts):
        """Analyze found contracts in detail"""
        print("🔍 DETAILED CONTRACT ANALYSIS")
        print("=" * 35)
        
        if not btc_contracts:
            print("❌ No BTC contracts found to analyze")
            return
        
        print(f"📊 Found {len(btc_contracts)} BTC contracts across all endpoints")
        print("")
        
        # Group by endpoint
        by_endpoint = {}
        for contract in btc_contracts:
            endpoint = contract['endpoint']
            if endpoint not in by_endpoint:
                by_endpoint[endpoint] = []
            by_endpoint[endpoint].append(contract)
        
        total_estimated_oi = 0
        
        for endpoint, contracts in by_endpoint.items():
            print(f"📊 {endpoint} ({len(contracts)} contracts):")
            
            for contract in contracts:
                contract_name = contract['contract']
                data = contract['data']
                oi_fields = contract['oi_fields']
                
                print(f"  📋 {contract_name}:")
                
                # Try to extract OI data
                potential_oi = 0
                oi_field_used = None
                
                # Look for the most likely OI field
                for field_name, field_value in oi_fields:
                    if field_name in ['total_size', 'open_interest', 'size']:
                        try:
                            potential_oi = float(field_value)
                            oi_field_used = field_name
                            break
                        except (ValueError, TypeError):
                            continue
                
                if potential_oi > 0:
                    # Try to convert to USD value
                    price = 0
                    for field_name, field_value in data.items():
                        if field_name in ['last', 'price', 'mark_price']:
                            try:
                                price = float(field_value)
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    if price == 0:
                        price = 107000  # Approximate BTC price
                    
                    # Estimate USD value
                    if 'USD' in contract_name and 'USDT' not in contract_name and 'USDC' not in contract_name:
                        # Inverse contract - size is in USD
                        oi_usd = potential_oi
                        oi_btc = oi_usd / price
                    else:
                        # Linear contract - size is in quote currency
                        oi_btc = potential_oi / price
                        oi_usd = potential_oi
                    
                    total_estimated_oi += oi_usd
                    
                    print(f"    Field: {oi_field_used} = {potential_oi:,.0f}")
                    print(f"    Price: ${price:,.2f}")
                    print(f"    Estimated OI: {oi_btc:,.0f} BTC (${oi_usd/1e6:.1f}M)")
                else:
                    print(f"    ⚠️ No clear OI data found")
                    print(f"    Available fields: {[f[0] for f in oi_fields]}")
                
                print("")
        
        print(f"🎯 TOTAL ESTIMATED OI FROM ALL CONTRACTS: ${total_estimated_oi/1e9:.2f}B")
        
        # Compare with current system
        current_oi = 0.71e9  # $0.71B
        coinglass_oi = 6.68e9  # $6.68B
        
        print(f"📊 COMPARISON:")
        print(f"  Current system: ${current_oi/1e9:.2f}B")
        print(f"  Found contracts: ${total_estimated_oi/1e9:.2f}B")
        print(f"  Coinglass target: ${coinglass_oi/1e9:.2f}B")
        
        if total_estimated_oi > current_oi * 2:
            print(f"✅ SIGNIFICANT IMPROVEMENT POSSIBLE")
            print(f"  Potential gain: ${(total_estimated_oi - current_oi)/1e9:.2f}B")
        else:
            print(f"⚠️ May need to investigate other data sources")
    
    async def test_specific_tickers(self):
        """Test specific ticker endpoints that might have OI data"""
        print("🔍 TESTING SPECIFIC TICKER ENDPOINTS FOR OI")
        print("=" * 45)
        
        ticker_endpoints = [
            "/api/v4/futures/usdt/tickers",
            "/api/v4/futures/btc/tickers", 
            "/api/v4/delivery/usdt/tickers",
            "/api/v4/delivery/btc/tickers"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in ticker_endpoints:
                try:
                    print(f"📊 Testing: {endpoint}")
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            tickers = await response.json()
                            
                            btc_tickers = [t for t in tickers if 'BTC' in t.get('contract', '')]
                            print(f"  ✅ Found {len(btc_tickers)} BTC tickers")
                            
                            total_oi_found = 0
                            for ticker in btc_tickers:
                                contract = ticker.get('contract', 'Unknown')
                                total_size = ticker.get('total_size', 0)
                                
                                try:
                                    total_size_float = float(total_size)
                                    if total_size_float > 0:
                                        print(f"    {contract}: total_size = {total_size_float:,.0f}")
                                        total_oi_found += total_size_float
                                except (ValueError, TypeError):
                                    print(f"    {contract}: total_size = {total_size} (non-numeric)")
                            
                            print(f"  📊 Total size in this endpoint: {total_oi_found:,.0f}")
                        else:
                            print(f"  ❌ Status {response.status}")
                except Exception as e:
                    print(f"  ❌ Exception: {e}")
                print("")

async def main():
    fixer = GateIOOIFixer()
    
    print("🚨 GATE.IO OI DATA FIX INVESTIGATION")
    print("=" * 40)
    print("📋 Current issue: Missing $6B in Gate.io OI data")
    print("📋 Our data: $0.7B | Coinglass: $6.68B")
    print("📋 Goal: Identify missing contracts/endpoints")
    print("")
    
    # Step 1: Comprehensive API investigation
    btc_contracts = await fixer.investigate_gateio_api_endpoints()
    
    # Step 2: Analyze found contracts
    await fixer.analyze_contract_details(btc_contracts)
    
    # Step 3: Test specific ticker endpoints
    await fixer.test_specific_tickers()
    
    print("\n🎯 INVESTIGATION COMPLETE")
    print("Use findings above to implement Gate.io OI fix")

if __name__ == "__main__":
    asyncio.run(main())