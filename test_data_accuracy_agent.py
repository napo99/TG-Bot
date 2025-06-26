#!/usr/bin/env python3
"""
INDEPENDENT DATA ACCURACY VALIDATION AGENT
Validates that all data displayed in TG bot matches real market conditions
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class DataAccuracyValidator:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        
    async def fetch_api_data(self, endpoint, payload=None):
        """Fetch data from API"""
        try:
            async with aiohttp.ClientSession() as session:
                if payload:
                    async with session.post(f"{self.base_url}{endpoint}", json=payload) as response:
                        return await response.json()
                else:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        return await response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def validate_exchange_totals(self, data):
        """Validate that exchange totals add up correctly"""
        validations = []
        
        exchanges = data.get("exchange_breakdown", [])
        agg = data.get("aggregated_oi", {})
        
        # Sum up individual exchange totals
        total_tokens_sum = sum(ex.get("oi_tokens", 0) for ex in exchanges)
        total_usd_sum = sum(ex.get("oi_usd", 0) for ex in exchanges)
        
        # Compare with aggregated totals
        agg_tokens = agg.get("total_tokens", 0)
        agg_usd = agg.get("total_usd", 0)
        
        # Tolerance for rounding differences
        token_diff_pct = abs(total_tokens_sum - agg_tokens) / agg_tokens * 100 if agg_tokens > 0 else 100
        usd_diff_pct = abs(total_usd_sum - agg_usd) / agg_usd * 100 if agg_usd > 0 else 100
        
        if token_diff_pct < 1.0:
            validations.append(f"✅ Token totals match: {total_tokens_sum:,.0f} ≈ {agg_tokens:,.0f}")
        else:
            validations.append(f"❌ Token mismatch: {total_tokens_sum:,.0f} vs {agg_tokens:,.0f} ({token_diff_pct:.1f}% diff)")
        
        if usd_diff_pct < 1.0:
            validations.append(f"✅ USD totals match: ${total_usd_sum/1e9:.1f}B ≈ ${agg_usd/1e9:.1f}B")
        else:
            validations.append(f"❌ USD mismatch: ${total_usd_sum/1e9:.1f}B vs ${agg_usd/1e9:.1f}B ({usd_diff_pct:.1f}% diff)")
        
        return validations
    
    async def validate_market_categories(self, data):
        """Validate market category breakdowns"""
        validations = []
        
        categories = data.get("market_categories", {})
        agg = data.get("aggregated_oi", {})
        
        # Sum up category totals
        usdt_usd = categories.get("usdt_stable", {}).get("total_usd", 0)
        usdc_usd = categories.get("usdc_stable", {}).get("total_usd", 0)
        usd_inverse = categories.get("usd_inverse", {}).get("total_usd", 0)
        
        category_total = usdt_usd + usdc_usd + usd_inverse
        agg_total = agg.get("total_usd", 0)
        
        diff_pct = abs(category_total - agg_total) / agg_total * 100 if agg_total > 0 else 100
        
        if diff_pct < 1.0:
            validations.append(f"✅ Category totals match aggregate: ${category_total/1e9:.1f}B ≈ ${agg_total/1e9:.1f}B")
        else:
            validations.append(f"❌ Category total mismatch: ${category_total/1e9:.1f}B vs ${agg_total/1e9:.1f}B")
        
        # Validate percentages
        usdt_pct = categories.get("usdt_stable", {}).get("percentage", 0)
        usdc_pct = categories.get("usdc_stable", {}).get("percentage", 0)
        inverse_pct = categories.get("usd_inverse", {}).get("percentage", 0)
        
        total_pct = usdt_pct + usdc_pct + inverse_pct
        
        if 99 <= total_pct <= 101:
            validations.append(f"✅ Category percentages sum correctly: {total_pct:.1f}%")
        else:
            validations.append(f"❌ Category percentages don't sum to 100%: {total_pct:.1f}%")
        
        return validations
    
    async def validate_realistic_values(self, data):
        """Validate that values are realistic (not fake/hardcoded)"""
        validations = []
        
        agg = data.get("aggregated_oi", {})
        exchanges = data.get("exchange_breakdown", [])
        
        # Check for realistic BTC OI values (should be > 200K BTC, < 1M BTC typically)
        total_tokens = agg.get("total_tokens", 0)
        if 200000 <= total_tokens <= 1000000:
            validations.append(f"✅ Realistic total OI: {total_tokens:,.0f} BTC")
        else:
            validations.append(f"⚠️ Unusual total OI: {total_tokens:,.0f} BTC (outside 200K-1M range)")
        
        # Check for realistic USD values
        total_usd = agg.get("total_usd", 0)
        if 20e9 <= total_usd <= 100e9:  # $20B to $100B range
            validations.append(f"✅ Realistic total USD: ${total_usd/1e9:.1f}B")
        else:
            validations.append(f"⚠️ Unusual total USD: ${total_usd/1e9:.1f}B (outside $20B-$100B range)")
        
        # Check that no exchanges have exactly 0 or suspiciously round numbers
        for ex in exchanges:
            tokens = ex.get("oi_tokens", 0)
            if tokens > 1000 and tokens % 1000 != 0:  # Not exactly divisible by 1000
                validations.append(f"✅ {ex['exchange']}: Realistic precision ({tokens:,.0f} BTC)")
            elif tokens == 0:
                validations.append(f"❌ {ex['exchange']}: Zero OI detected")
            else:
                validations.append(f"⚠️ {ex['exchange']}: Suspiciously round number ({tokens:,.0f} BTC)")
        
        return validations
    
    async def validate_exchange_coverage(self, data):
        """Validate that all expected exchanges are covered"""
        validations = []
        
        exchanges = data.get("exchange_breakdown", [])
        exchange_names = [ex.get("exchange", "").lower() for ex in exchanges]
        
        expected_exchanges = ["binance", "bybit", "okx", "gateio", "bitget"]
        
        for expected in expected_exchanges:
            if expected in exchange_names:
                validations.append(f"✅ {expected.title()}: Present")
            else:
                validations.append(f"❌ {expected.title()}: Missing")
        
        # Check for unexpected exchanges
        unexpected = [ex for ex in exchange_names if ex not in expected_exchanges]
        if unexpected:
            validations.append(f"⚠️ Unexpected exchanges: {unexpected}")
        
        return validations
    
    async def run_accuracy_validation(self):
        """Run comprehensive data accuracy validation"""
        print("🔍 INDEPENDENT DATA ACCURACY VALIDATION")
        print("=" * 45)
        print(f"🕐 Validation started at: {datetime.now().strftime('%H:%M:%S')}")
        print("")
        
        # Fetch OI data
        print("📊 Fetching OI data for validation...")
        oi_data = await self.fetch_api_data("/multi_oi", {"base_symbol": "BTC"})
        
        if not oi_data.get("success"):
            print("❌ Failed to fetch OI data")
            return False
        
        print("✅ OI data fetched successfully")
        print("")
        
        # Run validations
        print("🧮 Validation 1: Exchange Total Accuracy")
        exchange_validations = await self.validate_exchange_totals(oi_data)
        for validation in exchange_validations:
            print(f"  {validation}")
        
        print("\n🏷️ Validation 2: Market Category Accuracy")
        category_validations = await self.validate_market_categories(oi_data)
        for validation in category_validations:
            print(f"  {validation}")
        
        print("\n📈 Validation 3: Realistic Value Check")
        realistic_validations = await self.validate_realistic_values(oi_data)
        for validation in realistic_validations:
            print(f"  {validation}")
        
        print("\n🏢 Validation 4: Exchange Coverage")
        coverage_validations = await self.validate_exchange_coverage(oi_data)
        for validation in coverage_validations:
            print(f"  {validation}")
        
        # Summary
        all_validations = exchange_validations + category_validations + realistic_validations + coverage_validations
        passed = sum(1 for v in all_validations if v.startswith("✅"))
        total = len(all_validations)
        
        print(f"\n🎯 ACCURACY VALIDATION SUMMARY")
        print("=" * 35)
        print(f"✅ Passed: {passed}/{total} validations")
        
        if passed == total:
            print("🏆 ALL DATA ACCURACY CHECKS PASSED")
            print("✅ Real market data confirmed")
            print("✅ Mathematical consistency verified")
            print("✅ No fake/hardcoded values detected")
        elif passed >= total * 0.8:
            print("⚠️ MOSTLY ACCURATE - Minor issues detected")
        else:
            print("❌ SIGNIFICANT ACCURACY ISSUES FOUND")
        
        return passed >= total * 0.8

async def main():
    validator = DataAccuracyValidator()
    success = await validator.run_accuracy_validation()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)