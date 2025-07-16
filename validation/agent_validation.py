#!/usr/bin/env python3
"""
AGENT VALIDATION FRAMEWORK
Individual agent work validation for autonomous implementation
"""

import os
from typing import Dict, Any, List
from datetime import datetime

class AgentWorkValidator:
    """Validates individual agent implementations"""
    
    def __init__(self):
        self.base_path = '/Users/screener-m3/projects/crypto-assistant'
        self.validation_results = {}
    
    def validate_agent_1_phase1_fix(self) -> Dict[str, Any]:
        """Validate Agent 1's Phase 1 OI fix implementation"""
        print("🔍 VALIDATING AGENT 1 - PHASE 1 OI FIX")
        print("-" * 50)
        
        results = {
            'agent': 'Agent 1',
            'objective': 'Fix Gate.io & Bitget OI providers',
            'status': 'UNKNOWN',
            'files_created': [],
            'files_validated': {},
            'issues_found': [],
            'recommendations': []
        }
        
        # Check required files
        required_files = [
            'services/market-data/gateio_oi_provider_working.py',
            'services/market-data/bitget_oi_provider_working.py'
        ]
        
        for rel_path in required_files:
            full_path = os.path.join(self.base_path, rel_path)
            exists = os.path.exists(full_path)
            results['files_validated'][rel_path] = exists
            
            if exists:
                results['files_created'].append(rel_path)
                print(f"✅ Found: {rel_path}")
                
                # Validate file content
                with open(full_path, 'r') as f:
                    content = f.read()
                    
                # Check for key implementation elements
                if 'BaseExchangeOIProvider' in content:
                    print(f"  ✅ Inherits from BaseExchangeOIProvider")
                else:
                    results['issues_found'].append(f"{rel_path}: Missing BaseExchangeOIProvider inheritance")
                
                if 'async def get_oi_data' in content:
                    print(f"  ✅ Implements async get_oi_data method")
                else:
                    results['issues_found'].append(f"{rel_path}: Missing get_oi_data method")
                
                if 'MarketType.USDT' in content and 'MarketType.USD' in content:
                    print(f"  ✅ Supports USDT and USD market types")
                else:
                    results['issues_found'].append(f"{rel_path}: Missing market type support")
                    
            else:
                print(f"❌ Missing: {rel_path}")
                results['issues_found'].append(f"Missing required file: {rel_path}")
        
        # Check unified_oi_aggregator exists
        aggregator_path = 'services/market-data/unified_oi_aggregator.py'
        aggregator_full_path = os.path.join(self.base_path, aggregator_path)
        if os.path.exists(aggregator_full_path):
            print(f"✅ unified_oi_aggregator.py exists (import resolution ready)")
            results['files_validated'][aggregator_path] = True
        else:
            print(f"❌ unified_oi_aggregator.py missing")
            results['files_validated'][aggregator_path] = False
            results['issues_found'].append("Missing unified_oi_aggregator.py")
        
        # Determine status
        if len(results['files_created']) == len(required_files) and len(results['issues_found']) == 0:
            results['status'] = 'COMPLETE_SUCCESS'
            results['recommendations'].append("Ready for manual testing after docker restart")
        elif len(results['files_created']) > 0:
            results['status'] = 'PARTIAL_SUCCESS'
            results['recommendations'].append("Some issues found, review before testing")
        else:
            results['status'] = 'FAILED'
            results['recommendations'].append("Major issues found, requires rework")
        
        print(f"📊 Agent 1 Status: {results['status']}")
        return results
    
    def validate_agent_4_api_monitoring(self) -> Dict[str, Any]:
        """Validate Agent 4's API monitoring tools"""
        print("\n🔍 VALIDATING AGENT 4 - API MONITORING")
        print("-" * 50)
        
        results = {
            'agent': 'Agent 4',
            'objective': 'Implement API health monitoring tools',
            'status': 'UNKNOWN',
            'files_created': [],
            'files_validated': {},
            'issues_found': [],
            'recommendations': []
        }
        
        # Check monitoring tools
        monitoring_files = [
            'tools/simple_health_check.py',
            'tools/api_tester.py',
            'tools/exchange_monitor.py'
        ]
        
        for rel_path in monitoring_files:
            full_path = os.path.join(self.base_path, rel_path)
            exists = os.path.exists(full_path)
            results['files_validated'][rel_path] = exists
            
            if exists:
                results['files_created'].append(rel_path)
                print(f"✅ Found: {rel_path}")
                
                # Basic content validation
                with open(full_path, 'r') as f:
                    content = f.read()
                
                if 'class' in content and 'def' in content:
                    print(f"  ✅ Contains class definitions and methods")
                else:
                    results['issues_found'].append(f"{rel_path}: Incomplete implementation")
                    
            else:
                print(f"⚠️ Missing: {rel_path}")
        
        # Determine status
        if len(results['files_created']) >= 2:  # At least 2 tools available
            results['status'] = 'SUCCESS'
            results['recommendations'].append("Monitoring tools ready for use")
        elif len(results['files_created']) > 0:
            results['status'] = 'PARTIAL_SUCCESS'
            results['recommendations'].append("Some monitoring tools available")
        else:
            results['status'] = 'FAILED'
            results['recommendations'].append("No monitoring tools found")
        
        print(f"📊 Agent 4 Status: {results['status']}")
        return results
    
    def validate_agent_2_logging(self) -> Dict[str, Any]:
        """Validate Agent 2's logging system"""
        print("\n🔍 VALIDATING AGENT 2 - LOGGING SYSTEM")
        print("-" * 50)
        
        results = {
            'agent': 'Agent 2',
            'objective': 'Implement enhanced logging system',
            'status': 'UNKNOWN',
            'files_created': [],
            'files_validated': {},
            'issues_found': [],
            'recommendations': []
        }
        
        logging_files = [
            'services/market-data/market_logger.py',
            'services/market-data/main_with_logging.py'
        ]
        
        for rel_path in logging_files:
            full_path = os.path.join(self.base_path, rel_path)
            exists = os.path.exists(full_path)
            results['files_validated'][rel_path] = exists
            
            if exists:
                results['files_created'].append(rel_path)
                print(f"✅ Found: {rel_path}")
            else:
                print(f"⚠️ Missing: {rel_path}")
        
        # Determine status based on files found
        if len(results['files_created']) >= 1:
            results['status'] = 'SUCCESS'
            results['recommendations'].append("Logging system components available")
        else:
            results['status'] = 'FAILED'
            results['recommendations'].append("Logging system needs implementation")
        
        print(f"📊 Agent 2 Status: {results['status']}")
        return results
    
    def generate_overall_assessment(self) -> Dict[str, Any]:
        """Generate overall autonomous implementation assessment"""
        print("\n🎯 OVERALL AUTONOMOUS IMPLEMENTATION ASSESSMENT")
        print("=" * 60)
        
        # Calculate success metrics
        total_agents = len(self.validation_results)
        successful_agents = sum(1 for r in self.validation_results.values() 
                              if r['status'] in ['COMPLETE_SUCCESS', 'SUCCESS'])
        
        success_rate = (successful_agents / total_agents * 100) if total_agents > 0 else 0
        
        # Determine overall status
        if success_rate >= 80:
            overall_status = "AUTONOMOUS_SUCCESS"
            confidence = "HIGH"
        elif success_rate >= 60:
            overall_status = "PARTIAL_SUCCESS"
            confidence = "MEDIUM"
        else:
            overall_status = "NEEDS_WORK"
            confidence = "LOW"
        
        assessment = {
            'timestamp': datetime.now().isoformat(),
            'total_agents': total_agents,
            'successful_agents': successful_agents,
            'success_rate': f"{success_rate:.0f}%",
            'overall_status': overall_status,
            'confidence_level': confidence,
            'agent_results': self.validation_results,
            'ready_for_manual_execution': success_rate >= 70,
            'critical_success': self.validation_results.get('agent_1', {}).get('status') == 'COMPLETE_SUCCESS'
        }
        
        print(f"📊 Success Rate: {assessment['success_rate']}")
        print(f"🎯 Overall Status: {overall_status}")
        print(f"🔍 Confidence: {confidence}")
        print(f"✅ Ready for Manual Execution: {assessment['ready_for_manual_execution']}")
        
        return assessment
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete agent validation suite"""
        print("🚀 AUTONOMOUS AGENT VALIDATION SUITE")
        print("=" * 60)
        
        # Validate each agent's work
        self.validation_results['agent_1'] = self.validate_agent_1_phase1_fix()
        self.validation_results['agent_4'] = self.validate_agent_4_api_monitoring()
        self.validation_results['agent_2'] = self.validate_agent_2_logging()
        
        # Generate overall assessment
        assessment = self.generate_overall_assessment()
        
        # Add recommendations
        print(f"\n📋 AUTONOMOUS IMPLEMENTATION RECOMMENDATIONS:")
        
        if assessment['critical_success']:
            print("  ✅ Phase 1 OI fix ready - proceed with manual testing")
        else:
            print("  ❌ Phase 1 OI fix needs attention before testing")
        
        if assessment['ready_for_manual_execution']:
            print("  🚀 System ready for manual docker restart and validation")
            print("  📝 Git commit recommended for autonomous work preservation")
        else:
            print("  ⚠️ Address identified issues before manual execution")
        
        return assessment


def main():
    """Run complete agent validation"""
    validator = AgentWorkValidator()
    assessment = validator.run_complete_validation()
    
    print(f"\n💾 Validation complete - {assessment['overall_status']}")
    return assessment

if __name__ == "__main__":
    main()