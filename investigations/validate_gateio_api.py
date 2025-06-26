#!/usr/bin/env python3
"""
EXTERNAL VALIDATION AGENT: Gate.io API Investigation
Validates Gate.io OI data against official API documentation and Coinglass
"""

import aiohttp
import asyncio
import json

class GateioAPIValidator:
    def __init__(self):
        self.base_url = "https://api.gateio.ws"
        
    async def fetch_gateio_official_oi(self):
        """Fetch OI data directly from Gate.io official API"""
        print("🔍 FETCHING GATE.IO OFFICIAL OI DATA")
        print("=" * 40)
        
        endpoints_to_test = [
            "/api/v4/futures/usdt/contracts",
            "/api/v4/futures/usdt/contracts/BTC_USDT",
            "/api/v4/futures/usdt/contracts/BTC_USDT/detail",
            "/api/v4/futures/btc/contracts",
            "/api/v4/futures/btc/contracts/BTC_USD",
            "/api/v4/delivery/usdt/contracts",
            "/api/v4/delivery/btc/contracts"
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints_to_test:
                try:
                    print(f"📊 Testing: {endpoint}")
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            results[endpoint] = {
                                "status": "✅ SUCCESS",
                                "data_type": type(data).__name__,
                                "count": len(data) if isinstance(data, list) else 1,
                                "sample": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                            }
                            
                            # Look for OI-related fields
                            if isinstance(data, list) and data:
                                for item in data[:3]:  # Check first 3 items
                                    if isinstance(item, dict):
                                        oi_fields = [k for k in item.keys() if 'open' in k.lower() or 'interest' in k.lower() or 'oi' in k.lower()]
                                        if oi_fields:
                                            print(f"  🎯 Found OI fields: {oi_fields}")
                                            print(f"  📋 Sample values: {[(f, item.get(f)) for f in oi_fields[:3]]}")
                            
                            elif isinstance(data, dict):
                                oi_fields = [k for k in data.keys() if 'open' in k.lower() or 'interest' in k.lower() or 'oi' in k.lower()]
                                if oi_fields:
                                    print(f"  🎯 Found OI fields: {oi_fields}")
                                    print(f"  📋 Sample values: {[(f, data.get(f)) for f in oi_fields[:3]]}")
                        else:
                            results[endpoint] = {
                                "status": f"❌ ERROR {response.status}",
                                "error": await response.text()
                            }
                            print(f"  ❌ Status {response.status}")
                            
                except Exception as e:
                    results[endpoint] = {
                        "status": f"❌ EXCEPTION",
                        "error": str(e)
                    }
                    print(f"  ❌ Exception: {e}")
                
                print("")
        
        return results
    
    async def check_our_gateio_implementation(self):
        """Check our current Gate.io implementation"""
        print("🔍 CHECKING OUR GATE.IO IMPLEMENTATION")
        print("=" * 40)
        
        # Check our market-data service
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8001/multi_oi", json={"base_symbol": "BTC"}) as response:
                    data = await response.json()
            
            # Find Gate.io data
            gateio_data = None
            for exchange in data.get('exchange_breakdown', []):
                if exchange['exchange'].lower() == 'gateio':
                    gateio_data = exchange
                    break
            
            if gateio_data:
                print("📊 OUR GATE.IO DATA:")
                print(f"  Total OI: {gateio_data['oi_tokens']:,.0f} BTC")
                print(f"  Total USD: ${gateio_data['oi_usd']/1e9:.2f}B")
                print(f"  Markets: {gateio_data['markets']}")
                print(f"  Percentage: {gateio_data['oi_percentage']:.2f}%")
                print("")
                
                print("📋 INDIVIDUAL MARKETS:")
                for market in gateio_data.get('market_breakdown', []):
                    print(f"  {market['symbol']}: {market['oi_tokens']:,.0f} BTC (${market['oi_usd']/1e6:.1f}M)")
                    print(f"    Type: {market['type']}, Funding: {market['funding_rate']*100:+.4f}%")
                print("")
                
                # Compare with Coinglass reference
                coinglass_oi_btc = 68820  # From the image
                coinglass_oi_usd = 7.38e9  # $7.38B
                
                our_oi_btc = gateio_data['oi_tokens']
                our_oi_usd = gateio_data['oi_usd']
                
                btc_diff_pct = abs(our_oi_btc - coinglass_oi_btc) / coinglass_oi_btc * 100
                usd_diff_pct = abs(our_oi_usd - coinglass_oi_usd) / coinglass_oi_usd * 100
                
                print("🔍 COMPARISON WITH COINGLASS:")
                print(f"  Coinglass: {coinglass_oi_btc:,.0f} BTC (${coinglass_oi_usd/1e9:.2f}B)")
                print(f"  Our data:  {our_oi_btc:,.0f} BTC (${our_oi_usd/1e9:.2f}B)")
                print(f"  BTC diff:  {btc_diff_pct:.1f}% {'✅ CLOSE' if btc_diff_pct < 20 else '❌ LARGE DISCREPANCY'}")
                print(f"  USD diff:  {usd_diff_pct:.1f}% {'✅ CLOSE' if usd_diff_pct < 20 else '❌ LARGE DISCREPANCY'}")
                
                if btc_diff_pct > 50:
                    print("\n🚨 CRITICAL ISSUE DETECTED:")
                    print("  Gate.io OI data shows major discrepancy with Coinglass")
                    print("  Likely causes:")
                    print("  1. Wrong API endpoint")
                    print("  2. Wrong data field extraction")
                    print("  3. Missing perpetual contract types")
                    print("  4. Incorrect settlement currency calculation")
                
            else:
                print("❌ No Gate.io data found in our system")
            
        except Exception as e:
            print(f"❌ Error checking our implementation: {e}")
    
    async def investigate_gateio_contracts(self):
        """Deep dive into Gate.io contract types"""
        print("🔍 DEEP DIVE: GATE.IO CONTRACT INVESTIGATION")
        print("=" * 45)
        
        # Test different contract endpoints
        contract_endpoints = [
            ("/api/v4/futures/usdt/contracts", "USDT Perpetuals"),
            ("/api/v4/futures/btc/contracts", "BTC Perpetuals"),
            ("/api/v4/delivery/usdt/contracts", "USDT Delivery"),
            ("/api/v4/delivery/btc/contracts", "BTC Delivery"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in contract_endpoints:
                try:
                    print(f"📊 {description}: {endpoint}")
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            contracts = await response.json()
                            btc_contracts = [c for c in contracts if 'BTC' in c.get('name', '')]
                            
                            print(f"  ✅ Found {len(btc_contracts)} BTC contracts")
                            
                            total_oi = 0
                            for contract in btc_contracts:
                                name = contract.get('name', 'Unknown')
                                
                                # Try to get OI data for each contract
                                try:
                                    detail_endpoint = f"{endpoint}/{name}"
                                    async with session.get(f"{self.base_url}{detail_endpoint}") as detail_response:
                                        if detail_response.status == 200:
                                            detail = await detail_response.json()
                                            
                                            # Look for OI fields
                                            for field, value in detail.items():
                                                if 'open' in field.lower() and 'interest' in field.lower():
                                                    print(f"    {name}: {field} = {value}")
                                                    if isinstance(value, (int, float)):
                                                        total_oi += value
                                                        
                                except Exception as e:
                                    print(f"    ❌ Error getting details for {name}: {e}")
                            
                            if total_oi > 0:
                                print(f"  📊 Total OI in this category: {total_oi:,.0f}")
                        else:
                            print(f"  ❌ Status {response.status}")
                except Exception as e:
                    print(f"  ❌ Exception: {e}")
                print("")

async def main():
    validator = GateioAPIValidator()
    
    print("🚨 GATE.IO OI VALIDATION INVESTIGATION")
    print("=" * 50)
    print("📋 Target: Coinglass shows 68.82K BTC ($7.38B)")
    print("📋 Our data: ~6K BTC ($0.7B)")
    print("📋 Discrepancy: ~90% missing data")
    print("")
    
    # Step 1: Check our current implementation
    await validator.check_our_gateio_implementation()
    
    # Step 2: Fetch official Gate.io API data
    await validator.fetch_gateio_official_oi()
    
    # Step 3: Deep investigation
    await validator.investigate_gateio_contracts()
    
    print("\n🎯 VALIDATION COMPLETE")
    print("Review the findings above to identify the root cause of Gate.io OI discrepancy")

if __name__ == "__main__":
    asyncio.run(main())