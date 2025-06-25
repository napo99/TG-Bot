#!/usr/bin/env python3
"""
COUNTER-AGENT VALIDATION SYSTEM
Deploy independent verification agents to validate primary agent claims
PRINCIPLE: Never trust a single agent - always verify with independent agents
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class CounterAgentResult:
    agent_id: str
    validation_type: str
    primary_agent_claim: Any
    counter_agent_result: Any
    agreement_pct: float
    validation_status: str
    evidence: str
    timestamp: datetime

class CounterAgentValidationSystem:
    """
    Deploys independent counter-agents to validate primary agent work
    Each counter-agent uses different methods to reach the same conclusions
    """
    
    def __init__(self):
        self.counter_agents = {
            'price_validator': self._deploy_price_validation_agent,
            'calculation_validator': self._deploy_calculation_validation_agent,
            'api_validator': self._deploy_api_validation_agent,
            'logic_validator': self._deploy_logic_validation_agent
        }
    
    async def deploy_counter_agents(self, primary_agent_claims: Dict[str, Any]) -> List[CounterAgentResult]:
        """Deploy all counter-agents to validate primary agent claims"""
        validation_tasks = []
        
        for agent_id, agent_function in self.counter_agents.items():
            task = asyncio.create_task(agent_function(primary_agent_claims))
            validation_tasks.append(task)
        
        counter_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results
        validation_results = []
        for i, result in enumerate(counter_results):
            if isinstance(result, Exception):
                validation_results.append(CounterAgentResult(
                    agent_id=list(self.counter_agents.keys())[i],
                    validation_type='error',
                    primary_agent_claim='unknown',
                    counter_agent_result=str(result),
                    agreement_pct=0.0,
                    validation_status='FAILED',
                    evidence=f'Counter-agent error: {str(result)}',
                    timestamp=datetime.now()
                ))
            else:
                validation_results.extend(result)
        
        return validation_results
    
    async def _deploy_price_validation_agent(self, primary_claims: Dict[str, Any]) -> List[CounterAgentResult]:
        """Counter-agent: Validate prices using completely different APIs"""
        results = []
        
        try:
            # Primary agent's price claims
            if 'exchange_breakdown' not in primary_claims:
                return []
            
            for exchange_data in primary_claims['exchange_breakdown']:
                exchange = exchange_data.get('exchange', '')
                symbol = primary_claims.get('symbol', 'BTC')
                primary_price = exchange_data.get('price', 0)
                
                # Counter-agent uses different price source
                counter_price = await self._get_independent_price(symbol, exchange)
                
                if counter_price is not None:
                    agreement_pct = 100.0 - abs(primary_price - counter_price) / counter_price * 100
                    validation_status = 'AGREEMENT' if agreement_pct >= 95.0 else 'DISAGREEMENT'
                    
                    results.append(CounterAgentResult(
                        agent_id='price_validator',
                        validation_type='price_verification',
                        primary_agent_claim=primary_price,
                        counter_agent_result=counter_price,
                        agreement_pct=agreement_pct,
                        validation_status=validation_status,
                        evidence=f'{exchange} {symbol}: Primary ${primary_price:,.2f} vs Counter ${counter_price:,.2f}',
                        timestamp=datetime.now()
                    ))
        
        except Exception as e:
            results.append(CounterAgentResult(
                agent_id='price_validator',
                validation_type='error',
                primary_agent_claim='price_validation',
                counter_agent_result=str(e),
                agreement_pct=0.0,
                validation_status='ERROR',
                evidence=f'Price validation error: {str(e)}',
                timestamp=datetime.now()
            ))
        
        return results
    
    async def _deploy_calculation_validation_agent(self, primary_claims: Dict[str, Any]) -> List[CounterAgentResult]:
        """Counter-agent: Validate calculations using independent mathematical methods"""
        results = []
        
        try:
            if 'exchange_breakdown' not in primary_claims:
                return []
            
            for exchange_data in primary_claims['exchange_breakdown']:
                exchange = exchange_data.get('exchange', '')
                oi_tokens = exchange_data.get('oi_tokens', 0)
                oi_usd = exchange_data.get('oi_usd', 0)
                price = exchange_data.get('price', 0)
                
                # Counter-agent: Independent calculation
                if price > 0:
                    counter_oi_usd = oi_tokens * price
                    agreement_pct = 100.0 - abs(oi_usd - counter_oi_usd) / counter_oi_usd * 100 if counter_oi_usd > 0 else 0
                    validation_status = 'AGREEMENT' if agreement_pct >= 99.0 else 'DISAGREEMENT'
                    
                    results.append(CounterAgentResult(
                        agent_id='calculation_validator',
                        validation_type='usd_calculation',
                        primary_agent_claim=oi_usd,
                        counter_agent_result=counter_oi_usd,
                        agreement_pct=agreement_pct,
                        validation_status=validation_status,
                        evidence=f'{exchange}: Primary ${oi_usd/1e9:.1f}B vs Counter ${counter_oi_usd/1e9:.1f}B ({oi_tokens:,.0f} × ${price:,.0f})',
                        timestamp=datetime.now()
                    ))
        
        except Exception as e:
            results.append(CounterAgentResult(
                agent_id='calculation_validator',
                validation_type='error',
                primary_agent_claim='calculation_validation',
                counter_agent_result=str(e),
                agreement_pct=0.0,
                validation_status='ERROR',
                evidence=f'Calculation validation error: {str(e)}',
                timestamp=datetime.now()
            ))
        
        return results
    
    async def _deploy_api_validation_agent(self, primary_claims: Dict[str, Any]) -> List[CounterAgentResult]:
        """Counter-agent: Validate API data using direct exchange calls"""
        results = []
        
        try:
            symbol = primary_claims.get('symbol', 'BTC')
            
            if 'exchange_breakdown' not in primary_claims:
                return []
            
            for exchange_data in primary_claims['exchange_breakdown']:
                exchange = exchange_data.get('exchange', '').lower()
                primary_oi = exchange_data.get('oi_tokens', 0)
                
                # Counter-agent: Direct API validation
                counter_oi = await self._get_independent_oi(symbol, exchange)
                
                if counter_oi is not None:
                    agreement_pct = 100.0 - abs(primary_oi - counter_oi) / counter_oi * 100 if counter_oi > 0 else 0
                    validation_status = 'AGREEMENT' if agreement_pct >= 90.0 else 'DISAGREEMENT'
                    
                    results.append(CounterAgentResult(
                        agent_id='api_validator',
                        validation_type='oi_verification',
                        primary_agent_claim=primary_oi,
                        counter_agent_result=counter_oi,
                        agreement_pct=agreement_pct,
                        validation_status=validation_status,
                        evidence=f'{exchange} {symbol}: Primary {primary_oi:,.0f} vs Counter {counter_oi:,.0f}',
                        timestamp=datetime.now()
                    ))
        
        except Exception as e:
            results.append(CounterAgentResult(
                agent_id='api_validator',
                validation_type='error',
                primary_agent_claim='api_validation',
                counter_agent_result=str(e),
                agreement_pct=0.0,
                validation_status='ERROR',
                evidence=f'API validation error: {str(e)}',
                timestamp=datetime.now()
            ))
        
        return results
    
    async def _deploy_logic_validation_agent(self, primary_claims: Dict[str, Any]) -> List[CounterAgentResult]:
        """Counter-agent: Validate logical consistency and sanity checks"""
        results = []
        
        try:
            # Validate total OI consistency
            if 'exchange_breakdown' in primary_claims and 'aggregated_oi' in primary_claims:
                exchange_breakdown = primary_claims['exchange_breakdown']
                aggregated = primary_claims['aggregated_oi']
                
                # Sum individual exchange OI values
                sum_tokens = sum(ex.get('oi_tokens', 0) for ex in exchange_breakdown)
                sum_usd = sum(ex.get('oi_usd', 0) for ex in exchange_breakdown)
                
                primary_total_tokens = aggregated.get('total_tokens', 0)
                primary_total_usd = aggregated.get('total_usd', 0)
                
                # Check tokens consistency
                tokens_agreement = 100.0 - abs(sum_tokens - primary_total_tokens) / primary_total_tokens * 100 if primary_total_tokens > 0 else 0
                tokens_status = 'AGREEMENT' if tokens_agreement >= 99.0 else 'DISAGREEMENT'
                
                results.append(CounterAgentResult(
                    agent_id='logic_validator',
                    validation_type='total_consistency_tokens',
                    primary_agent_claim=primary_total_tokens,
                    counter_agent_result=sum_tokens,
                    agreement_pct=tokens_agreement,
                    validation_status=tokens_status,
                    evidence=f'Total tokens: Primary {primary_total_tokens:,.0f} vs Sum {sum_tokens:,.0f}',
                    timestamp=datetime.now()
                ))
                
                # Check USD consistency
                usd_agreement = 100.0 - abs(sum_usd - primary_total_usd) / primary_total_usd * 100 if primary_total_usd > 0 else 0
                usd_status = 'AGREEMENT' if usd_agreement >= 99.0 else 'DISAGREEMENT'
                
                results.append(CounterAgentResult(
                    agent_id='logic_validator',
                    validation_type='total_consistency_usd',
                    primary_agent_claim=primary_total_usd,
                    counter_agent_result=sum_usd,
                    agreement_pct=usd_agreement,
                    validation_status=usd_status,
                    evidence=f'Total USD: Primary ${primary_total_usd/1e9:.1f}B vs Sum ${sum_usd/1e9:.1f}B',
                    timestamp=datetime.now()
                ))
        
        except Exception as e:
            results.append(CounterAgentResult(
                agent_id='logic_validator',
                validation_type='error',
                primary_agent_claim='logic_validation',
                counter_agent_result=str(e),
                agreement_pct=0.0,
                validation_status='ERROR',
                evidence=f'Logic validation error: {str(e)}',
                timestamp=datetime.now()
            ))
        
        return results
    
    async def _get_independent_price(self, symbol: str, exchange: str) -> float:
        """Get price from independent source (different from primary agent)"""
        try:
            # Use CoinGecko as independent price source
            symbol_map = {'BTC': 'bitcoin', 'ETH': 'ethereum'}
            cg_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    return data[cg_id]['usd']
        except:
            return None
    
    async def _get_independent_oi(self, symbol: str, exchange: str) -> float:
        """Get OI from independent source (direct exchange API)"""
        try:
            if exchange == 'binance':
                return await self._get_binance_oi_direct(symbol)
            elif exchange == 'bybit':
                return await self._get_bybit_oi_direct(symbol)
            else:
                return None
        except:
            return None
    
    async def _get_binance_oi_direct(self, symbol: str) -> float:
        """Get Binance OI directly"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol.upper()}USDT"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    return float(data['openInterest'])
        except:
            return None
    
    async def _get_bybit_oi_direct(self, symbol: str) -> float:
        """Get Bybit OI directly"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol.upper()}USDT"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    if data['retCode'] == 0 and data['result']['list']:
                        return float(data['result']['list'][0]['openInterest'])
            return None
        except:
            return None
    
    def generate_validation_report(self, counter_results: List[CounterAgentResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report from counter-agent results"""
        total_validations = len(counter_results)
        agreements = sum(1 for r in counter_results if r.validation_status == 'AGREEMENT')
        disagreements = sum(1 for r in counter_results if r.validation_status == 'DISAGREEMENT')
        errors = sum(1 for r in counter_results if r.validation_status == 'ERROR')
        
        agreement_rate = agreements / total_validations * 100 if total_validations > 0 else 0
        
        # Overall validation status
        if agreement_rate >= 95.0:
            overall_status = 'TRUSTED'
        elif agreement_rate >= 80.0:
            overall_status = 'CAUTIOUS'
        elif agreement_rate >= 60.0:
            overall_status = 'SUSPICIOUS'
        else:
            overall_status = 'REJECTED'
        
        validation_report = {
            'validation_summary': {
                'total_validations': total_validations,
                'agreements': agreements,
                'disagreements': disagreements,
                'errors': errors,
                'agreement_rate_pct': agreement_rate,
                'overall_status': overall_status,
                'timestamp': datetime.now().isoformat()
            },
            'counter_agent_results': [
                {
                    'agent_id': r.agent_id,
                    'validation_type': r.validation_type,
                    'primary_claim': r.primary_agent_claim,
                    'counter_result': r.counter_agent_result,
                    'agreement_pct': r.agreement_pct,
                    'status': r.validation_status,
                    'evidence': r.evidence,
                    'timestamp': r.timestamp.isoformat()
                } for r in counter_results
            ],
            'recommendations': self._generate_recommendations(counter_results, overall_status)
        }
        
        return validation_report
    
    def _generate_recommendations(self, results: List[CounterAgentResult], overall_status: str) -> List[str]:
        """Generate recommendations based on counter-agent validation results"""
        recommendations = []
        
        if overall_status == 'TRUSTED':
            recommendations.append("✅ Primary agent results validated by independent counter-agents")
            recommendations.append("✅ Safe to proceed with agent recommendations")
        elif overall_status == 'CAUTIOUS':
            recommendations.append("⚠️ Some disagreements found - review specific validation failures")
            recommendations.append("⚠️ Consider additional validation before proceeding")
        elif overall_status == 'SUSPICIOUS':
            recommendations.append("🚨 Significant disagreements found - do not trust primary agent")
            recommendations.append("🚨 Require additional evidence and validation")
        else:  # REJECTED
            recommendations.append("❌ Primary agent results rejected by counter-agents")
            recommendations.append("❌ Do not proceed - investigate and fix underlying issues")
        
        # Specific recommendations based on validation types
        disagreements = [r for r in results if r.validation_status == 'DISAGREEMENT']
        for disagreement in disagreements:
            if disagreement.validation_type == 'usd_calculation':
                recommendations.append(f"🔧 Fix USD calculation logic for {disagreement.evidence}")
            elif disagreement.validation_type == 'price_verification':
                recommendations.append(f"🔧 Verify price sources for {disagreement.evidence}")
            elif disagreement.validation_type == 'oi_verification':
                recommendations.append(f"🔧 Check OI data source for {disagreement.evidence}")
        
        return recommendations

# Usage Example
async def validate_primary_agent_with_counters():
    """Example of validating primary agent with independent counter-agents"""
    validator = CounterAgentValidationSystem()
    
    # Primary agent claims (from our current system)
    primary_agent_claims = {
        'symbol': 'BTC',
        'aggregated_oi': {
            'total_tokens': 2556394,
            'total_usd': 39249268700  # This should be validated
        },
        'exchange_breakdown': [
            {
                'exchange': 'okx',
                'oi_tokens': 2542569,
                'oi_usd': 25425688700,
                'price': 106577
            },
            {
                'exchange': 'bybit',
                'oi_tokens': 13825,
                'oi_usd': 13823580,
                'price': 106577
            }
        ]
    }
    
    print("🚀 Deploying Counter-Agents for Independent Validation...")
    counter_results = await validator.deploy_counter_agents(primary_agent_claims)
    
    validation_report = validator.generate_validation_report(counter_results)
    
    print("\n📊 COUNTER-AGENT VALIDATION REPORT:")
    print(json.dumps(validation_report, indent=2))
    
    return validation_report

if __name__ == "__main__":
    validation_report = asyncio.run(validate_primary_agent_with_counters())
    print(f"\n🎯 FINAL VERDICT: {validation_report['validation_summary']['overall_status']}")
    print(f"Agreement Rate: {validation_report['validation_summary']['agreement_rate_pct']:.1f}%")