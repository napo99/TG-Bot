#!/usr/bin/env python3
"""
QUARTERLY/DELIVERY CONTRACTS INVESTIGATION
Shows current perpetual tracking vs available quarterly contracts across all exchanges
"""

import aiohttp
import asyncio
import json

class QuarterlyContractsInvestigator:
    def __init__(self):
        self.exchanges = {
            'binance': 'https://fapi.binance.com',
            'bybit': 'https://api.bybit.com',
            'okx': 'https://www.okx.com',
            'gateio': 'https://api.gateio.ws',
            'bitget': 'https://api.bitget.com'
        }
        
    async def show_current_perpetual_tracking(self):
        """Show what we currently track (perpetuals only)"""
        print("📊 CURRENT PERPETUAL CONTRACTS TRACKING")
        print("=" * 50)
        
        print("🔄 PERPETUAL SWAPS ONLY:")
        print("  📋 LINEAR CONTRACTS (settle in stablecoin):")
        print("    • USDT-margined: BTC/USDT perpetuals")
        print("    • USDC-margined: BTC/USDC perpetuals") 
        print("  📋 INVERSE CONTRACTS (settle in base currency):")
        print("    • USD-margined: BTC/USD perpetuals (coin-margined)")
        print("")
        
        print("❌ NOT CURRENTLY TRACKING:")
        print("  📅 QUARTERLY/DELIVERY CONTRACTS:")
        print("    • Fixed expiry dates (weekly, monthly, quarterly)")
        print("    • Settlement at expiration")
        print("    • Different risk profiles")
        print("")
        
    async def investigate_okx_futures(self):
        """Investigate OKX futures contracts we found"""
        print("🔍 OKX FUTURES CONTRACTS INVESTIGATION")
        print("=" * 45)
        
        okx_base = "https://www.okx.com"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get all futures instruments
                async with session.get(f"{okx_base}/api/v5/public/instruments?instType=FUTURES") as response:
                    data = await response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    futures = data['data']
                    btc_futures = [f for f in futures if 'BTC' in f.get('instId', '')]
                    
                    print(f"📊 Found {len(btc_futures)} BTC futures contracts:")
                    print("")
                    
                    # Group by settlement currency
                    usdt_futures = []
                    usd_futures = []
                    usdc_futures = []
                    
                    for contract in btc_futures:
                        inst_id = contract['instId']
                        if 'USDT' in inst_id:
                            usdt_futures.append(contract)
                        elif 'USDC' in inst_id:
                            usdc_futures.append(contract)
                        elif 'USD' in inst_id:
                            usd_futures.append(contract)
                    
                    # Show USDT futures
                    if usdt_futures:
                        print(f"📋 USDT-MARGINED FUTURES ({len(usdt_futures)} contracts):")
                        for contract in usdt_futures:
                            inst_id = contract['instId']
                            expiry = contract.get('expTime', 'Unknown')
                            print(f"  • {inst_id} - Expires: {expiry}")
                        print("")
                    
                    # Show USD futures  
                    if usd_futures:
                        print(f"📋 USD-MARGINED FUTURES ({len(usd_futures)} contracts):")
                        for contract in usd_futures:
                            inst_id = contract['instId']
                            expiry = contract.get('expTime', 'Unknown')
                            print(f"  • {inst_id} - Expires: {expiry}")
                        print("")
                    
                    # Show USDC futures
                    if usdc_futures:
                        print(f"📋 USDC-MARGINED FUTURES ({len(usdc_futures)} contracts):")
                        for contract in usdc_futures:
                            inst_id = contract['instId']
                            expiry = contract.get('expTime', 'Unknown')
                            print(f"  • {inst_id} - Expires: {expiry}")
                        print("")
                    
                    # Get OI data for some futures
                    await self._get_okx_futures_oi_sample(session, btc_futures[:5])
                    
        except Exception as e:
            print(f"❌ Error investigating OKX futures: {e}")
    
    async def _get_okx_futures_oi_sample(self, session, sample_contracts):
        """Get OI data for sample futures contracts"""
        print("📊 SAMPLE FUTURES OPEN INTEREST DATA:")
        print("")
        
        for contract in sample_contracts:
            inst_id = contract['instId']
            try:
                async with session.get(f"https://www.okx.com/api/v5/public/open-interest?instId={inst_id}") as response:
                    data = await response.json()
                    
                    if data.get('code') == '0' and data.get('data'):
                        oi_data = data['data'][0]
                        oi_ccy = float(oi_data.get('oiCcy', 0))
                        oi_usd = float(oi_data.get('oiUsd', 0))
                        
                        print(f"  {inst_id}:")
                        print(f"    OI: {oi_ccy:,.0f} BTC (${oi_usd/1e6:.1f}M)")
                        
            except Exception as e:
                print(f"  {inst_id}: Error getting OI - {e}")
        print("")
    
    async def investigate_other_exchanges_futures(self):
        """Check if other exchanges have quarterly contracts"""
        print("🔍 OTHER EXCHANGES FUTURES INVESTIGATION")
        print("=" * 45)
        
        # Binance futures
        print("📊 BINANCE:")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://fapi.binance.com/fapi/v1/exchangeInfo") as response:
                    data = await response.json()
                    
                    symbols = data.get('symbols', [])
                    btc_symbols = [s for s in symbols if s['baseAsset'] == 'BTC']
                    
                    perpetuals = [s for s in btc_symbols if s['contractType'] == 'PERPETUAL']
                    delivery = [s for s in btc_symbols if s['contractType'] in ['CURRENT_QUARTER', 'NEXT_QUARTER', 'CURRENT_MONTH']]
                    
                    print(f"  ✅ Perpetuals: {len(perpetuals)} contracts")
                    print(f"  📅 Delivery: {len(delivery)} contracts")
                    
                    if delivery:
                        print("  📋 Available delivery contracts:")
                        for contract in delivery[:5]:  # Show first 5
                            symbol = contract['symbol']
                            contract_type = contract['contractType']
                            delivery_date = contract.get('deliveryDate', 'Unknown')
                            print(f"    • {symbol} ({contract_type}) - Delivery: {delivery_date}")
                        if len(delivery) > 5:
                            print(f"    ... and {len(delivery) - 5} more")
                    print("")
                    
        except Exception as e:
            print(f"  ❌ Error checking Binance: {e}")
            print("")
        
        # Bybit futures
        print("📊 BYBIT:")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.bybit.com/v5/market/instruments-info?category=linear") as response:
                    data = await response.json()
                    
                    if data.get('retCode') == 0:
                        instruments = data.get('result', {}).get('list', [])
                        btc_instruments = [i for i in instruments if i['baseCoin'] == 'BTC']
                        
                        perpetuals = [i for i in btc_instruments if i['contractType'] == 'LinearPerpetual']
                        delivery = [i for i in btc_instruments if i['contractType'] in ['LinearFutures']]
                        
                        print(f"  ✅ Linear Perpetuals: {len(perpetuals)} contracts")
                        print(f"  📅 Linear Futures: {len(delivery)} contracts")
                        
                        if delivery:
                            print("  📋 Available linear futures:")
                            for contract in delivery[:3]:
                                symbol = contract['symbol']
                                delivery_time = contract.get('deliveryTime', 'Unknown')
                                print(f"    • {symbol} - Delivery: {delivery_time}")
                        print("")
                        
        except Exception as e:
            print(f"  ❌ Error checking Bybit: {e}")
            print("")
        
        # Gate.io check
        print("📊 GATE.IO:")
        try:
            async with aiohttp.ClientSession() as session:
                # Check delivery contracts
                async with session.get("https://api.gateio.ws/api/v4/delivery/usdt/contracts") as response:
                    if response.status == 200:
                        data = await response.json()
                        btc_contracts = [c for c in data if 'BTC' in c.get('name', '')]
                        print(f"  📅 USDT Delivery contracts: {len(btc_contracts)} BTC contracts")
                        
                        if btc_contracts:
                            for contract in btc_contracts[:3]:
                                name = contract['name']
                                settle_time = contract.get('settle_time', 'Unknown')
                                print(f"    • {name} - Settlement: {settle_time}")
                    else:
                        print("  ❌ No delivery contracts endpoint accessible")
        except Exception as e:
            print(f"  ❌ Error checking Gate.io: {e}")
        print("")
        
        # Bitget check
        print("📊 BITGET:")
        print("  📋 Currently only checking perpetual swaps")
        print("  📅 May have quarterly contracts in separate endpoints")
        print("")
    
    async def estimate_total_missing_oi(self):
        """Estimate potential OI from missing quarterly contracts"""
        print("💡 ESTIMATED IMPACT OF MISSING CONTRACTS")
        print("=" * 45)
        
        print("📊 CURRENT PERPETUAL TOTALS:")
        print("  Total: ~275K BTC (~$29.6B)")
        print("  Coverage: 5 exchanges, 13 markets")
        print("")
        
        print("🤔 POTENTIAL QUARTERLY/DELIVERY IMPACT:")
        print("  📈 Typical futures OI is 10-30% of perpetual OI")
        print("  📈 Conservative estimate: +20-80K BTC (+$2-8B)")
        print("  📈 Aggressive estimate: +50-150K BTC (+$5-16B)")
        print("")
        
        print("📋 PRIORITIES FOR FUTURE IMPLEMENTATION:")
        print("  1. 🔥 HIGH: CME Bitcoin futures ($16.22B missing)")
        print("  2. 🔥 HIGH: Binance quarterly contracts")
        print("  3. 🔥 HIGH: OKX futures (14 contracts available)")
        print("  4. 🔶 MED: Bybit linear futures")
        print("  5. 🔶 MED: Gate.io delivery contracts")
        print("  6. 🔶 MED: Bitget quarterly (if available)")
        print("")

async def main():
    investigator = QuarterlyContractsInvestigator()
    
    print("🔍 QUARTERLY/DELIVERY CONTRACTS INVESTIGATION")
    print("=" * 55)
    print("📋 Goal: Map current perpetual vs missing quarterly contracts")
    print("📋 Focus: Identify potential additional OI sources")
    print("")
    
    # Step 1: Show current perpetual tracking
    await investigator.show_current_perpetual_tracking()
    
    # Step 2: Investigate OKX futures in detail
    await investigator.investigate_okx_futures()
    
    # Step 3: Check other exchanges
    await investigator.investigate_other_exchanges_futures()
    
    # Step 4: Estimate impact
    await investigator.estimate_total_missing_oi()
    
    print("🎯 INVESTIGATION COMPLETE")
    print("📝 Ready to document findings for future implementation")

if __name__ == "__main__":
    asyncio.run(main())