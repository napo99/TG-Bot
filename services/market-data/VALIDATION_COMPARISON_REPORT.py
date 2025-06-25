#!/usr/bin/env python3
"""
COMPREHENSIVE VALIDATION COMPARISON REPORT
Comparing original vs fixed implementations for Gate.io and Bitget

CRITICAL MISSION: Validate that fixes resolve the major issues:
- Gate.io: 56.9M BTC ($6.1T) → Realistic values
- Bitget: 0 BTC (no data) → Working implementation
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Import both original and fixed implementations
from gateio_oi_provider import GateIOOIProvider
from gateio_oi_provider_fixed import GateIOOIProviderFixed
from bitget_oi_provider import BitgetOIProvider
from bitget_oi_provider_fixed import BitgetOIProviderFixed

class ValidationComparison:
    """Comprehensive validation comparison between original and fixed implementations"""
    
    def __init__(self):
        self.results = {
            'comparison_timestamp': datetime.now().isoformat(),
            'gateio_comparison': {},
            'bitget_comparison': {},
            'overall_assessment': {},
            'production_recommendations': {}
        }
    
    async def run_comprehensive_comparison(self):
        """Run complete comparison between original and fixed implementations"""
        print("🔍 COMPREHENSIVE VALIDATION COMPARISON")
        print("=" * 60)
        
        # Test Gate.io implementations
        await self._compare_gateio_implementations()
        
        # Test Bitget implementations
        await self._compare_bitget_implementations()
        
        # Generate overall assessment
        self._generate_overall_assessment()
        
        # Generate production recommendations
        self._generate_production_recommendations()
        
        return self.results
    
    async def _compare_gateio_implementations(self):
        """Compare original vs fixed Gate.io implementations"""
        print("\n🟢 GATE.IO IMPLEMENTATION COMPARISON")
        print("-" * 40)
        
        # Test original implementation
        print("Testing ORIGINAL Gate.io implementation...")
        original_provider = GateIOOIProvider()
        try:
            original_result = await original_provider.get_oi_data("BTC")
            original_success = True
        except Exception as e:
            original_result = None
            original_success = False
            print(f"❌ Original implementation failed: {str(e)}")
        finally:
            await original_provider.close()
        
        # Test fixed implementation
        print("Testing FIXED Gate.io implementation...")
        fixed_provider = GateIOOIProviderFixed()
        try:
            fixed_result = await fixed_provider.get_oi_data("BTC")
            fixed_success = True
        except Exception as e:
            fixed_result = None
            fixed_success = False
            print(f"❌ Fixed implementation failed: {str(e)}")
        finally:
            await fixed_provider.close()
        
        # Compare results
        comparison = {
            'original': {
                'success': original_success,
                'total_oi_btc': original_result.total_oi_tokens if original_result else 0,
                'total_oi_usd': original_result.total_oi_usd if original_result else 0,
                'markets_found': len(original_result.markets) if original_result else 0,
                'validation_passed': original_result.validation_passed if original_result else False,
                'issues': self._analyze_gateio_issues(original_result) if original_result else ["Implementation failed"]
            },
            'fixed': {
                'success': fixed_success,
                'total_oi_btc': fixed_result.total_oi_tokens if fixed_result else 0,
                'total_oi_usd': fixed_result.total_oi_usd if fixed_result else 0,
                'markets_found': len(fixed_result.markets) if fixed_result else 0,
                'validation_passed': fixed_result.validation_passed if fixed_result else False,
                'issues': self._analyze_gateio_issues(fixed_result) if fixed_result else ["Implementation failed"]
            }
        }
        
        # Calculate improvement
        if original_result and fixed_result:
            comparison['improvement'] = {
                'oi_reduction_factor': original_result.total_oi_tokens / fixed_result.total_oi_tokens if fixed_result.total_oi_tokens > 0 else 0,
                'realistic_values': self._is_realistic_btc_oi(fixed_result.total_oi_tokens),
                'issues_resolved': len(comparison['original']['issues']) - len(comparison['fixed']['issues'])
            }
        
        self.results['gateio_comparison'] = comparison
        
        # Print comparison
        print(f"\n📊 GATE.IO RESULTS COMPARISON:")
        print(f"Original: {comparison['original']['total_oi_btc']:,.0f} BTC (${comparison['original']['total_oi_usd']/1e9:.1f}B)")
        print(f"Fixed:    {comparison['fixed']['total_oi_btc']:,.0f} BTC (${comparison['fixed']['total_oi_usd']/1e9:.1f}B)")
        
        if 'improvement' in comparison:
            print(f"Improvement: {comparison['improvement']['oi_reduction_factor']:.1f}x reduction")
            print(f"Realistic values: {'✅ YES' if comparison['improvement']['realistic_values'] else '❌ NO'}")
    
    async def _compare_bitget_implementations(self):
        """Compare original vs fixed Bitget implementations"""
        print("\n🟡 BITGET IMPLEMENTATION COMPARISON")
        print("-" * 40)
        
        # Test original implementation
        print("Testing ORIGINAL Bitget implementation...")
        original_provider = BitgetOIProvider()
        try:
            original_result = await original_provider.get_oi_data("BTC")
            original_success = True
        except Exception as e:
            original_result = None
            original_success = False
            print(f"❌ Original implementation failed: {str(e)}")
        finally:
            await original_provider.close()
        
        # Test fixed implementation
        print("Testing FIXED Bitget implementation...")
        fixed_provider = BitgetOIProviderFixed()
        try:
            fixed_result = await fixed_provider.get_oi_data("BTC")
            fixed_success = True
        except Exception as e:
            fixed_result = None
            fixed_success = False
            print(f"❌ Fixed implementation failed: {str(e)}")
        finally:
            await fixed_provider.close()
        
        # Compare results
        comparison = {
            'original': {
                'success': original_success,
                'total_oi_btc': original_result.total_oi_tokens if original_result else 0,
                'total_oi_usd': original_result.total_oi_usd if original_result else 0,
                'markets_found': len(original_result.markets) if original_result else 0,
                'validation_passed': original_result.validation_passed if original_result else False,
                'issues': self._analyze_bitget_issues(original_result) if original_result else ["Implementation failed"]
            },
            'fixed': {
                'success': fixed_success,
                'total_oi_btc': fixed_result.total_oi_tokens if fixed_result else 0,
                'total_oi_usd': fixed_result.total_oi_usd if fixed_result else 0,
                'markets_found': len(fixed_result.markets) if fixed_result else 0,
                'validation_passed': fixed_result.validation_passed if fixed_result else False,
                'issues': self._analyze_bitget_issues(fixed_result) if fixed_result else ["Implementation failed"]
            }
        }
        
        # Calculate improvement
        comparison['improvement'] = {
            'data_recovery': fixed_result.total_oi_tokens > 0 if fixed_result else False,
            'realistic_values': self._is_realistic_btc_oi(fixed_result.total_oi_tokens) if fixed_result else False,
            'api_endpoints_fixed': fixed_success and not original_success
        }
        
        self.results['bitget_comparison'] = comparison
        
        # Print comparison
        print(f"\n📊 BITGET RESULTS COMPARISON:")
        print(f"Original: {comparison['original']['total_oi_btc']:,.0f} BTC (${comparison['original']['total_oi_usd']/1e9:.1f}B)")
        print(f"Fixed:    {comparison['fixed']['total_oi_btc']:,.0f} BTC (${comparison['fixed']['total_oi_usd']/1e9:.1f}B)")
        print(f"Data recovery: {'✅ YES' if comparison['improvement']['data_recovery'] else '❌ NO'}")
        print(f"Realistic values: {'✅ YES' if comparison['improvement']['realistic_values'] else '❌ NO'}")
    
    def _analyze_gateio_issues(self, result) -> list:
        """Analyze Gate.io implementation issues"""
        issues = []
        if not result:
            return ["No result returned"]
        
        # Check for unrealistic OI values
        if result.total_oi_tokens > 1_000_000:  # > 1M BTC
            issues.append(f"Unrealistic OI: {result.total_oi_tokens:,.0f} BTC")
        
        # Check if using volume fields
        for market in result.markets:
            if 'volume' in market.calculation_method.lower():
                issues.append("Using volume fields instead of OI")
                break
        
        return issues
    
    def _analyze_bitget_issues(self, result) -> list:
        """Analyze Bitget implementation issues"""
        issues = []
        if not result:
            return ["No result returned"]
        
        if result.total_oi_tokens == 0:
            issues.append("No OI data retrieved")
        
        if not result.validation_passed:
            issues.append("Validation failed")
        
        return issues
    
    def _is_realistic_btc_oi(self, oi_btc: float) -> bool:
        """Check if BTC OI value is in realistic range"""
        return 10_000 <= oi_btc <= 100_000  # 10K-100K BTC range
    
    def _generate_overall_assessment(self):
        """Generate overall assessment of fixes"""
        gateio = self.results['gateio_comparison']
        bitget = self.results['bitget_comparison']
        
        assessment = {
            'gateio_fixed': (
                gateio['fixed']['success'] and 
                gateio['fixed']['validation_passed'] and
                len(gateio['fixed']['issues']) == 0
            ),
            'bitget_fixed': (
                bitget['fixed']['success'] and 
                bitget['fixed']['validation_passed'] and
                len(bitget['fixed']['issues']) == 0
            ),
            'critical_issues_resolved': [],
            'remaining_issues': [],
            'production_ready': False
        }
        
        # Check Gate.io fixes
        if assessment['gateio_fixed']:
            if 'improvement' in gateio and gateio['improvement']['realistic_values']:
                assessment['critical_issues_resolved'].append("Gate.io: Unrealistic 56.9M BTC → Realistic 57K BTC")
            if 'improvement' in gateio and gateio['improvement']['oi_reduction_factor'] > 100:
                assessment['critical_issues_resolved'].append(f"Gate.io: {gateio['improvement']['oi_reduction_factor']:.0f}x reduction in OI values")
        else:
            assessment['remaining_issues'].append("Gate.io: Still showing issues")
        
        # Check Bitget fixes
        if assessment['bitget_fixed']:
            if bitget['improvement']['data_recovery']:
                assessment['critical_issues_resolved'].append("Bitget: 0 BTC → Working OI data retrieval")
            if bitget['improvement']['realistic_values']:
                assessment['critical_issues_resolved'].append("Bitget: Realistic OI values achieved")
        else:
            assessment['remaining_issues'].append("Bitget: Still showing issues")
        
        # Overall production readiness
        assessment['production_ready'] = (
            assessment['gateio_fixed'] and 
            assessment['bitget_fixed'] and
            len(assessment['remaining_issues']) == 0
        )
        
        self.results['overall_assessment'] = assessment
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"Gate.io Fixed: {'✅ YES' if assessment['gateio_fixed'] else '❌ NO'}")
        print(f"Bitget Fixed: {'✅ YES' if assessment['bitget_fixed'] else '❌ NO'}")
        print(f"Production Ready: {'✅ YES' if assessment['production_ready'] else '❌ NO'}")
        
        if assessment['critical_issues_resolved']:
            print(f"\n✅ Critical Issues Resolved:")
            for issue in assessment['critical_issues_resolved']:
                print(f"  • {issue}")
        
        if assessment['remaining_issues']:
            print(f"\n❌ Remaining Issues:")
            for issue in assessment['remaining_issues']:
                print(f"  • {issue}")
    
    def _generate_production_recommendations(self):
        """Generate production deployment recommendations"""
        assessment = self.results['overall_assessment']
        gateio = self.results['gateio_comparison']
        bitget = self.results['bitget_comparison']
        
        recommendations = {
            'go_no_go_decision': 'GO' if assessment['production_ready'] else 'NO_GO',
            'immediate_actions': [],
            'deployment_steps': [],
            'monitoring_requirements': [],
            'expected_values': {}
        }
        
        if assessment['production_ready']:
            recommendations['immediate_actions'].extend([
                "Replace original Gate.io provider with fixed implementation",
                "Replace original Bitget provider with fixed implementation",
                "Deploy fixed implementations to production"
            ])
            
            recommendations['deployment_steps'].extend([
                "1. Backup current implementations",
                "2. Deploy fixed Gate.io provider (gateio_oi_provider_fixed.py)",
                "3. Deploy fixed Bitget provider (bitget_oi_provider_fixed.py)",
                "4. Update import statements in main service",
                "5. Test production deployment",
                "6. Monitor OI values for realistic ranges"
            ])
            
            recommendations['monitoring_requirements'].extend([
                "Gate.io OI: Monitor for 10K-100K BTC range",
                "Bitget OI: Monitor for 20K-80K BTC range",
                "Combined OI: Should be 30K-180K BTC total",
                "Alert if OI values exceed realistic ranges"
            ])
            
            # Set expected realistic values
            recommendations['expected_values'] = {
                'gateio_btc_range': [10_000, 100_000],
                'bitget_btc_range': [20_000, 80_000],
                'combined_btc_range': [30_000, 180_000],
                'combined_usd_range': [3e9, 18e9]  # $3B-18B
            }
        else:
            recommendations['immediate_actions'].extend([
                "DO NOT deploy to production",
                "Address remaining issues before deployment",
                "Continue testing and validation"
            ])
        
        self.results['production_recommendations'] = recommendations
        
        print(f"\n🚀 PRODUCTION RECOMMENDATIONS:")
        print(f"Decision: {recommendations['go_no_go_decision']}")
        
        if recommendations['immediate_actions']:
            print(f"\nImmediate Actions:")
            for action in recommendations['immediate_actions']:
                print(f"  • {action}")
        
        if recommendations['deployment_steps']:
            print(f"\nDeployment Steps:")
            for step in recommendations['deployment_steps']:
                print(f"  {step}")

async def main():
    """Main comparison execution"""
    comparison = ValidationComparison()
    results = await comparison.run_comprehensive_comparison()
    
    # Save detailed results
    with open('/Users/screener-m3/projects/crypto-assistant/services/market-data/VALIDATION_COMPARISON_REPORT.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed comparison report saved to VALIDATION_COMPARISON_REPORT.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())