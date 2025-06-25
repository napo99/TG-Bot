#!/usr/bin/env python3
"""
MANDATORY EVIDENCE REQUIREMENTS FOR AGENT CLAIMS
Never trust agent self-validation - require external proof
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib

@dataclass
class EvidenceRequirement:
    claim_type: str
    required_evidence: List[str]
    validation_method: str
    external_sources: List[str]
    min_proof_threshold: float

class EvidenceValidator:
    """
    Validates agent claims against mandatory evidence requirements
    PRINCIPLE: Extraordinary claims require extraordinary evidence
    """
    
    def __init__(self):
        self.evidence_requirements = {
            'usd_calculation_accuracy': EvidenceRequirement(
                claim_type='USD Calculation Accuracy',
                required_evidence=[
                    'external_price_verification',
                    'mathematical_proof',
                    'cross_exchange_validation',
                    'historical_comparison'
                ],
                validation_method='external_api_comparison',
                external_sources=['coingecko', 'binance', 'coinmarketcap'],
                min_proof_threshold=95.0  # 95% accuracy required
            ),
            'exchange_coverage_claims': EvidenceRequirement(
                claim_type='Exchange Coverage Claims',
                required_evidence=[
                    'direct_api_responses',
                    'response_timestamps',
                    'raw_data_hashes',
                    'api_endpoint_verification'
                ],
                validation_method='direct_api_verification',
                external_sources=['exchange_direct_apis'],
                min_proof_threshold=100.0  # Must be 100% verifiable
            ),
            'mathematical_validation_claims': EvidenceRequirement(
                claim_type='Mathematical Validation Claims',
                required_evidence=[
                    'calculation_formula_proof',
                    'step_by_step_verification',
                    'external_calculation_comparison',
                    'edge_case_testing'
                ],
                validation_method='mathematical_verification',
                external_sources=['independent_calculators'],
                min_proof_threshold=99.9  # Mathematical precision required
            )
        }
    
    def generate_evidence_checklist(self, agent_claims: List[str]) -> Dict[str, Any]:
        """Generate mandatory evidence checklist for agent claims"""
        checklist = {
            'validation_timestamp': datetime.now().isoformat(),
            'claims_analyzed': agent_claims,
            'evidence_requirements': {},
            'validation_status': 'PENDING'
        }
        
        for claim in agent_claims:
            claim_key = self._categorize_claim(claim)
            if claim_key in self.evidence_requirements:
                req = self.evidence_requirements[claim_key]
                checklist['evidence_requirements'][claim] = {
                    'claim_type': req.claim_type,
                    'required_evidence': req.required_evidence,
                    'validation_method': req.validation_method,
                    'external_sources': req.external_sources,
                    'min_proof_threshold': req.min_proof_threshold,
                    'evidence_provided': [],
                    'evidence_status': 'MISSING',
                    'proof_score': 0.0
                }
        
        return checklist
    
    def validate_evidence_submission(self, claim: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Validate evidence submitted for a specific claim"""
        claim_key = self._categorize_claim(claim)
        
        if claim_key not in self.evidence_requirements:
            return {
                'status': 'REJECTED',
                'reason': 'Unknown claim type',
                'evidence_score': 0.0
            }
        
        req = self.evidence_requirements[claim_key]
        evidence_score = 0.0
        validated_evidence = []
        missing_evidence = []
        
        for required_item in req.required_evidence:
            if required_item in evidence:
                # Validate the evidence item
                validation_result = self._validate_evidence_item(required_item, evidence[required_item])
                if validation_result['valid']:
                    evidence_score += 100.0 / len(req.required_evidence)
                    validated_evidence.append({
                        'item': required_item,
                        'status': 'VALIDATED',
                        'proof': validation_result['proof']
                    })
                else:
                    validated_evidence.append({
                        'item': required_item,
                        'status': 'INVALID',
                        'reason': validation_result['reason']
                    })
            else:
                missing_evidence.append(required_item)
        
        validation_status = 'TRUSTED' if evidence_score >= req.min_proof_threshold else 'INSUFFICIENT'
        
        return {
            'claim': claim,
            'validation_status': validation_status,
            'evidence_score': evidence_score,
            'required_threshold': req.min_proof_threshold,
            'validated_evidence': validated_evidence,
            'missing_evidence': missing_evidence,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    def _categorize_claim(self, claim: str) -> str:
        """Categorize claim to determine evidence requirements"""
        claim_lower = claim.lower()
        
        if 'usd' in claim_lower and ('calculation' in claim_lower or 'accurate' in claim_lower):
            return 'usd_calculation_accuracy'
        elif 'exchange' in claim_lower and ('coverage' in claim_lower or 'working' in claim_lower):
            return 'exchange_coverage_claims'
        elif 'mathematical' in claim_lower and ('validation' in claim_lower or 'verified' in claim_lower):
            return 'mathematical_validation_claims'
        else:
            return 'unknown_claim'
    
    def _validate_evidence_item(self, evidence_type: str, evidence_data: Any) -> Dict[str, Any]:
        """Validate specific evidence item"""
        if evidence_type == 'external_price_verification':
            return self._validate_price_evidence(evidence_data)
        elif evidence_type == 'mathematical_proof':
            return self._validate_mathematical_proof(evidence_data)
        elif evidence_type == 'direct_api_responses':
            return self._validate_api_response_evidence(evidence_data)
        elif evidence_type == 'calculation_formula_proof':
            return self._validate_formula_proof(evidence_data)
        else:
            return {'valid': False, 'reason': f'Unknown evidence type: {evidence_type}'}
    
    def _validate_price_evidence(self, evidence_data: Any) -> Dict[str, Any]:
        """Validate external price verification evidence"""
        try:
            if not isinstance(evidence_data, dict):
                return {'valid': False, 'reason': 'Price evidence must be a dictionary'}
            
            required_fields = ['external_sources', 'price_values', 'timestamps', 'verification_urls']
            for field in required_fields:
                if field not in evidence_data:
                    return {'valid': False, 'reason': f'Missing required field: {field}'}
            
            # Validate at least 2 external sources
            if len(evidence_data['external_sources']) < 2:
                return {'valid': False, 'reason': 'At least 2 external price sources required'}
            
            # Validate price consistency (within 5%)
            prices = evidence_data['price_values']
            if len(prices) < 2:
                return {'valid': False, 'reason': 'At least 2 price values required for validation'}
            
            avg_price = sum(prices) / len(prices)
            max_deviation = max(abs(p - avg_price) / avg_price * 100 for p in prices)
            
            if max_deviation > 5.0:
                return {'valid': False, 'reason': f'Price deviation too high: {max_deviation:.1f}% > 5%'}
            
            return {
                'valid': True,
                'proof': f'Price validated across {len(prices)} sources with max {max_deviation:.1f}% deviation'
            }
            
        except Exception as e:
            return {'valid': False, 'reason': f'Price validation error: {str(e)}'}
    
    def _validate_mathematical_proof(self, evidence_data: Any) -> Dict[str, Any]:
        """Validate mathematical proof evidence"""
        try:
            if not isinstance(evidence_data, dict):
                return {'valid': False, 'reason': 'Mathematical proof must be a dictionary'}
            
            required_fields = ['formula', 'sample_calculation', 'expected_result', 'actual_result']
            for field in required_fields:
                if field not in evidence_data:
                    return {'valid': False, 'reason': f'Missing required field: {field}'}
            
            # Validate calculation accuracy
            expected = float(evidence_data['expected_result'])
            actual = float(evidence_data['actual_result'])
            
            if expected == 0:
                return {'valid': False, 'reason': 'Expected result cannot be zero for percentage calculation'}
            
            error_pct = abs(actual - expected) / expected * 100
            
            if error_pct > 0.1:  # Max 0.1% error for mathematical proof
                return {'valid': False, 'reason': f'Mathematical error too high: {error_pct:.3f}% > 0.1%'}
            
            return {
                'valid': True,
                'proof': f'Mathematical calculation verified with {error_pct:.3f}% error'
            }
            
        except Exception as e:
            return {'valid': False, 'reason': f'Mathematical validation error: {str(e)}'}
    
    def _validate_api_response_evidence(self, evidence_data: Any) -> Dict[str, Any]:
        """Validate API response evidence"""
        try:
            if not isinstance(evidence_data, dict):
                return {'valid': False, 'reason': 'API response evidence must be a dictionary'}
            
            required_fields = ['endpoint_url', 'response_data', 'timestamp', 'response_hash']
            for field in required_fields:
                if field not in evidence_data:
                    return {'valid': False, 'reason': f'Missing required field: {field}'}
            
            # Validate response hash for integrity
            response_str = json.dumps(evidence_data['response_data'], sort_keys=True)
            calculated_hash = hashlib.sha256(response_str.encode()).hexdigest()
            
            if calculated_hash != evidence_data['response_hash']:
                return {'valid': False, 'reason': 'Response hash mismatch - data may be tampered'}
            
            # Validate timestamp is recent (within 24 hours)
            evidence_time = datetime.fromisoformat(evidence_data['timestamp'])
            time_diff = datetime.now() - evidence_time
            
            if time_diff.total_seconds() > 86400:  # 24 hours
                return {'valid': False, 'reason': 'Evidence timestamp too old (>24 hours)'}
            
            return {
                'valid': True,
                'proof': f'API response verified with hash {calculated_hash[:8]}... at {evidence_data["timestamp"]}'
            }
            
        except Exception as e:
            return {'valid': False, 'reason': f'API response validation error: {str(e)}'}
    
    def _validate_formula_proof(self, evidence_data: Any) -> Dict[str, Any]:
        """Validate formula proof evidence"""
        try:
            if not isinstance(evidence_data, dict):
                return {'valid': False, 'reason': 'Formula proof must be a dictionary'}
            
            required_fields = ['formula_text', 'variable_definitions', 'test_cases', 'verification_source']
            for field in required_fields:
                if field not in evidence_data:
                    return {'valid': False, 'reason': f'Missing required field: {field}'}
            
            # Validate test cases
            test_cases = evidence_data['test_cases']
            if not isinstance(test_cases, list) or len(test_cases) < 3:
                return {'valid': False, 'reason': 'At least 3 test cases required for formula validation'}
            
            # Validate each test case
            for i, test_case in enumerate(test_cases):
                if not all(key in test_case for key in ['inputs', 'expected_output', 'actual_output']):
                    return {'valid': False, 'reason': f'Test case {i+1} missing required fields'}
                
                expected = float(test_case['expected_output'])
                actual = float(test_case['actual_output'])
                
                if expected != 0:
                    error_pct = abs(actual - expected) / expected * 100
                    if error_pct > 0.01:  # Max 0.01% error for formula validation
                        return {'valid': False, 'reason': f'Test case {i+1} error too high: {error_pct:.4f}%'}
            
            return {
                'valid': True,
                'proof': f'Formula validated across {len(test_cases)} test cases with max error <0.01%'
            }
            
        except Exception as e:
            return {'valid': False, 'reason': f'Formula validation error: {str(e)}'}

# Usage Example: Mandatory Evidence Validation
def validate_agent_claims_with_evidence():
    """Example of validating agent claims with mandatory evidence"""
    validator = EvidenceValidator()
    
    # Agent makes claims
    agent_claims = [
        "USD calculation accuracy verified with 100% mathematical validation",
        "All 5 exchanges working with direct API verification",
        "Mathematical validation confirmed across all calculations"
    ]
    
    # Generate evidence requirements
    checklist = validator.generate_evidence_checklist(agent_claims)
    print("📋 MANDATORY EVIDENCE CHECKLIST:")
    print(json.dumps(checklist, indent=2))
    
    # Agent must provide evidence for each claim
    sample_evidence = {
        'external_price_verification': {
            'external_sources': ['coingecko', 'binance', 'coinmarketcap'],
            'price_values': [106500.0, 106520.0, 106480.0],
            'timestamps': ['2025-06-25T17:00:00', '2025-06-25T17:00:05', '2025-06-25T17:00:10'],
            'verification_urls': ['https://api.coingecko.com/...', 'https://api.binance.com/...']
        },
        'mathematical_proof': {
            'formula': 'OI_USD = OI_TOKENS × PRICE_USD',
            'sample_calculation': '78278 BTC × $106500 = $8,336,607,000',
            'expected_result': 8336607000.0,
            'actual_result': 8336607000.0
        }
    }
    
    # Validate evidence
    validation_result = validator.validate_evidence_submission(
        "USD calculation accuracy verified with 100% mathematical validation",
        sample_evidence
    )
    
    print("\n🔍 EVIDENCE VALIDATION RESULT:")
    print(json.dumps(validation_result, indent=2))
    
    return validation_result

if __name__ == "__main__":
    validate_agent_claims_with_evidence()