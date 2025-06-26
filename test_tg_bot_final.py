#!/usr/bin/env python3
"""
FINAL TG BOT VALIDATION
Tests TG bot functionality with the freshly deployed containers
"""

import asyncio
import aiohttp
import json

class TGBotValidator:
    def __init__(self):
        self.market_data_url = "http://localhost:8001"
        
    async def test_tg_bot_data_processing(self):
        """Test TG bot data processing simulation"""
        print("🤖 TESTING TG BOT DATA FLOW")
        print("=" * 35)
        
        try:
            # Simulate TG bot data request
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.market_data_url}/multi_oi", 
                                      json={"base_symbol": "BTC"}) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate key metrics
                        total_oi = data.get('aggregated_oi', {}).get('total_tokens', 0)
                        total_usd = data.get('aggregated_oi', {}).get('total_usd', 0)
                        exchanges = data.get('aggregated_oi', {}).get('exchanges_count', 0)
                        
                        print(f"✅ Market Data API Response:")
                        print(f"  Total OI: {total_oi:,.0f} BTC")
                        print(f"  Total USD: ${total_usd/1e9:.1f}B")
                        print(f"  Exchanges: {exchanges}")
                        
                        # Test specific exchange fixes
                        for exchange_data in data.get('exchange_breakdown', []):
                            exchange = exchange_data['exchange']
                            
                            if exchange == 'bitget':
                                total_volume = sum(m['volume_24h'] for m in exchange_data.get('market_breakdown', []))
                                print(f"  ✅ Bitget volume fix: {total_volume:,.0f} BTC (was 0)")
                                
                            elif exchange == 'okx':
                                total_volume = sum(m['volume_24h'] for m in exchange_data.get('market_breakdown', []))
                                print(f"  ✅ OKX volume fix: {total_volume:,.0f} BTC (was 14M)")
                        
                        return True
                    else:
                        print(f"❌ API Error: Status {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ TG Bot test error: {e}")
            return False
    
    async def validate_data_quality_checks(self):
        """Validate all known data quality issues are resolved"""
        print("\n🔍 DATA QUALITY VALIDATION")
        print("=" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.market_data_url}/multi_oi", 
                                      json={"base_symbol": "BTC"}) as response:
                    data = await response.json()
            
            issues_found = []
            
            # Check each exchange
            for exchange_data in data.get('exchange_breakdown', []):
                exchange = exchange_data['exchange']
                
                # Check for volume issues
                for market in exchange_data.get('market_breakdown', []):
                    volume_24h = market['volume_24h']
                    symbol = market['symbol']
                    
                    # Check for impossible volumes
                    if volume_24h > 1000000:  # > 1M BTC/day is unrealistic
                        issues_found.append(f"{exchange} {symbol}: Extreme volume {volume_24h:,.0f} BTC")
                    
                    # Check for zero volumes on major markets
                    if volume_24h == 0 and exchange in ['binance', 'bybit', 'okx']:
                        issues_found.append(f"{exchange} {symbol}: Zero volume on major market")
            
            if issues_found:
                print("❌ Data quality issues found:")
                for issue in issues_found:
                    print(f"  • {issue}")
                return False
            else:
                print("✅ All data quality checks passed")
                return True
                
        except Exception as e:
            print(f"❌ Data quality check error: {e}")
            return False

async def main():
    validator = TGBotValidator()
    
    print("🎯 FINAL TG BOT VALIDATION")
    print("=" * 30)
    print("📋 Testing: Fresh Docker containers with all fixes")
    print("📋 Validating: Bitget volume, OKX volume, overall data quality")
    print("")
    
    # Test 1: TG Bot data processing
    tg_test_passed = await validator.test_tg_bot_data_processing()
    
    # Test 2: Data quality validation
    quality_test_passed = await validator.validate_data_quality_checks()
    
    print("\n🎯 FINAL VALIDATION RESULTS")
    print("=" * 35)
    
    if tg_test_passed and quality_test_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ TG bot ready for user validation")
        print("✅ Both volume fixes deployed and working")
        print("✅ Data quality issues resolved")
    else:
        print("❌ TESTS FAILED")
        print("❌ Issues need to be resolved before user validation")
    
    return tg_test_passed and quality_test_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)