"""
Open Interest (OI) Data Validation and Mathematical Verification System
===================================================================

Mission: Ensure all OI calculations are mathematically sound and realistic
Target: Cross-validate OI data across exchanges and verify calculations

Validation Framework:
1. Math Verification: BTC_tokens * BTC_price ≈ USD_value (within 1% tolerance)
2. Exchange Cross-Validation: Compare similar markets across exchanges
3. Data Quality Checks: Volume vs OI ratio, Market cap vs OI ratio
4. Symbol Format Validation: Standardize different symbol formats
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math
import statistics
from loguru import logger


class ValidationLevel(Enum):
    CRITICAL = "CRITICAL"  # Must fail validation
    WARNING = "WARNING"    # Should flag but not fail
    INFO = "INFO"         # Informational only


class ContractType(Enum):
    LINEAR = "LINEAR"      # USDT-margined (e.g., BTCUSDT)
    INVERSE = "INVERSE"    # Coin-margined (e.g., BTCUSD)
    QUANTO = "QUANTO"      # USD-denominated but settled in crypto


@dataclass
class OIDataPoint:
    """Standardized OI data structure for validation"""
    symbol: str
    exchange: str
    contract_type: ContractType
    
    # Core OI data
    open_interest_tokens: float  # OI in base tokens (BTC, ETH, etc.)
    open_interest_usd: float     # OI in USD value
    current_price: float         # Current mark/index price
    
    # Additional validation data
    volume_24h_tokens: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    funding_rate: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Calculated fields for validation
    calculated_usd_value: Optional[float] = field(init=False, default=None)
    price_deviation: Optional[float] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields for validation"""
        if self.open_interest_tokens and self.current_price:
            self.calculated_usd_value = self.open_interest_tokens * self.current_price
            
            if self.open_interest_usd:
                # Calculate percentage deviation from expected USD value
                expected = self.calculated_usd_value
                actual = self.open_interest_usd
                self.price_deviation = abs((actual - expected) / expected) * 100


@dataclass
class ValidationResult:
    """Result of OI data validation"""
    data_point: OIDataPoint
    is_valid: bool
    validation_level: ValidationLevel
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    def add_issue(self, level: ValidationLevel, message: str):
        """Add validation issue"""
        if level == ValidationLevel.CRITICAL:
            self.errors.append(message)
            self.is_valid = False
        elif level == ValidationLevel.WARNING:
            self.warnings.append(message)
        else:
            self.info.append(message)


@dataclass
class CrossExchangeComparison:
    """Comparison results across exchanges"""
    symbol: str
    exchange_data: Dict[str, OIDataPoint]
    total_oi_tokens: float
    total_oi_usd: float
    price_consensus: float
    price_deviation_max: float
    outliers: List[str] = field(default_factory=list)


class SymbolStandardizer:
    """Standardize symbol formats across exchanges"""
    
    EXCHANGE_FORMATS = {
        'binance': {
            'spot': '{base}{quote}',           # BTCUSDT
            'linear': '{base}{quote}',         # BTCUSDT (futures)
            'inverse': '{base}USD_PERP'        # BTCUSD_PERP
        },
        'bybit': {
            'spot': '{base}{quote}',           # BTCUSDT
            'linear': '{base}USDT',            # BTCUSDT
            'inverse': '{base}USD'             # BTCUSD
        },
        'okx': {
            'spot': '{base}-{quote}',          # BTC-USDT
            'linear': '{base}-{quote}-SWAP',   # BTC-USDT-SWAP
            'inverse': '{base}-USD-SWAP'       # BTC-USD-SWAP
        },
        'deribit': {
            'linear': '{base}-PERPETUAL',      # BTC-PERPETUAL
            'inverse': '{base}-PERPETUAL'      # BTC-PERPETUAL
        }
    }
    
    @classmethod
    def standardize_symbol(cls, symbol: str, exchange: str, contract_type: str) -> str:
        """Convert symbol to standardized format"""
        # Extract base and quote from various formats
        base, quote = cls._extract_base_quote(symbol)
        
        # Use exchange-specific format
        format_template = cls.EXCHANGE_FORMATS.get(exchange, {}).get(contract_type)
        if format_template:
            return format_template.format(base=base, quote=quote)
        
        return symbol  # Return original if no format found
    
    @classmethod
    def _extract_base_quote(cls, symbol: str) -> Tuple[str, str]:
        """Extract base and quote currencies from symbol"""
        # Handle different separators
        separators = ['/', '-', '_', ':']
        
        for sep in separators:
            if sep in symbol:
                parts = symbol.split(sep)
                if len(parts) >= 2:
                    base = parts[0].upper()
                    quote = parts[1].upper().replace('USDT', 'USDT').replace('USD', 'USD')
                    return base, quote
        
        # Handle concatenated formats (BTCUSDT)
        if 'USDT' in symbol:
            base = symbol.replace('USDT', '').replace('PERP', '').replace('SWAP', '').strip()
            return base, 'USDT'
        elif 'USD' in symbol:
            base = symbol.replace('USD', '').replace('PERP', '').replace('SWAP', '').strip()
            return base, 'USD'
        
        return symbol, 'UNKNOWN'
    
    @classmethod
    def detect_contract_type(cls, symbol: str, exchange: str) -> ContractType:
        """Detect contract type from symbol format"""
        symbol_upper = symbol.upper()
        
        if 'USDT' in symbol_upper or 'USDC' in symbol_upper:
            return ContractType.LINEAR
        elif 'USD' in symbol_upper and 'USDT' not in symbol_upper:
            return ContractType.INVERSE
        else:
            return ContractType.LINEAR  # Default assumption


class OIMathValidator:
    """Mathematical validation of OI data"""
    
    # Global OI constants for validation (approximate values)
    GLOBAL_BTC_OI_RANGE = (300_000, 350_000)  # BTC tokens
    GLOBAL_BTC_OI_USD_RANGE = (30_000_000_000, 35_000_000_000)  # ~$32.5B
    
    # Validation tolerances
    PRICE_TOLERANCE_PERCENT = 1.0  # 1% tolerance for price calculations
    FUNDING_RATE_RANGE = (-0.001, 0.001)  # -0.1% to +0.1%
    
    @classmethod
    def validate_price_consistency(cls, data_point: OIDataPoint) -> ValidationResult:
        """Validate BTC_tokens * BTC_price ≈ USD_value"""
        result = ValidationResult(data_point, True, ValidationLevel.INFO)
        
        if not all([data_point.open_interest_tokens, data_point.current_price, data_point.open_interest_usd]):
            result.add_issue(ValidationLevel.WARNING, "Missing data for price consistency check")
            return result
        
        expected_usd = data_point.open_interest_tokens * data_point.current_price
        actual_usd = data_point.open_interest_usd
        
        deviation_percent = abs((actual_usd - expected_usd) / expected_usd) * 100
        
        if deviation_percent > cls.PRICE_TOLERANCE_PERCENT:
            result.add_issue(
                ValidationLevel.CRITICAL,
                f"Price inconsistency: {deviation_percent:.2f}% deviation "
                f"(expected: ${expected_usd:,.0f}, actual: ${actual_usd:,.0f})"
            )
        else:
            result.add_issue(
                ValidationLevel.INFO,
                f"Price consistent: {deviation_percent:.2f}% deviation within tolerance"
            )
        
        return result
    
    @classmethod
    def validate_funding_rate(cls, data_point: OIDataPoint) -> ValidationResult:
        """Validate funding rate is within reasonable range"""
        result = ValidationResult(data_point, True, ValidationLevel.INFO)
        
        if data_point.funding_rate is None:
            result.add_issue(ValidationLevel.INFO, "No funding rate data available")
            return result
        
        min_rate, max_rate = cls.FUNDING_RATE_RANGE
        
        if not (min_rate <= data_point.funding_rate <= max_rate):
            result.add_issue(
                ValidationLevel.WARNING,
                f"Unusual funding rate: {data_point.funding_rate:.4f} "
                f"(normal range: {min_rate:.3f} to {max_rate:.3f})"
            )
        else:
            result.add_issue(
                ValidationLevel.INFO,
                f"Funding rate normal: {data_point.funding_rate:.4f}"
            )
        
        return result
    
    @classmethod
    def validate_oi_magnitude(cls, data_point: OIDataPoint) -> ValidationResult:
        """Validate OI magnitude is realistic"""
        result = ValidationResult(data_point, True, ValidationLevel.INFO)
        
        if data_point.symbol.startswith('BTC') and data_point.open_interest_tokens:
            min_oi, max_oi = cls.GLOBAL_BTC_OI_RANGE
            
            if data_point.open_interest_tokens > max_oi:
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"BTC OI unusually high: {data_point.open_interest_tokens:,.0f} tokens "
                    f"(expected range: {min_oi:,.0f} - {max_oi:,.0f})"
                )
            elif data_point.open_interest_tokens < min_oi * 0.1:  # Less than 10% of minimum
                result.add_issue(
                    ValidationLevel.WARNING,
                    f"BTC OI unusually low: {data_point.open_interest_tokens:,.0f} tokens"
                )
        
        # Zero OI check
        if data_point.open_interest_tokens == 0:
            result.add_issue(ValidationLevel.CRITICAL, "Zero open interest detected")
        
        # Negative OI check
        if data_point.open_interest_tokens < 0:
            result.add_issue(ValidationLevel.CRITICAL, "Negative open interest detected")
        
        return result
    
    @classmethod
    def validate_volume_oi_ratio(cls, data_point: OIDataPoint) -> ValidationResult:
        """Validate volume to OI ratio is reasonable"""
        result = ValidationResult(data_point, True, ValidationLevel.INFO)
        
        if not all([data_point.volume_24h_tokens, data_point.open_interest_tokens]):
            result.add_issue(ValidationLevel.INFO, "Insufficient data for volume/OI ratio check")
            return result
        
        if data_point.open_interest_tokens == 0:
            result.add_issue(ValidationLevel.CRITICAL, "Cannot calculate volume/OI ratio: zero OI")
            return result
        
        ratio = data_point.volume_24h_tokens / data_point.open_interest_tokens
        
        # Typical daily volume/OI ratios:
        # - Active markets: 0.5 - 2.0 (50% - 200% of OI trades daily)
        # - Less active: 0.1 - 0.5
        # - Unusual: > 3.0 or < 0.05
        
        if ratio > 3.0:
            result.add_issue(
                ValidationLevel.WARNING,
                f"Very high volume/OI ratio: {ratio:.2f} (possible data error or unusual activity)"
            )
        elif ratio < 0.05:
            result.add_issue(
                ValidationLevel.WARNING,
                f"Very low volume/OI ratio: {ratio:.2f} (possible stale market or data error)"
            )
        else:
            result.add_issue(
                ValidationLevel.INFO,
                f"Volume/OI ratio normal: {ratio:.2f}"
            )
        
        return result


class CrossExchangeValidator:
    """Cross-exchange OI data validation and comparison"""
    
    MAX_PRICE_DEVIATION_PERCENT = 0.5  # 0.5% max price deviation between exchanges
    
    @classmethod
    def compare_exchanges(cls, symbol: str, data_points: List[OIDataPoint]) -> CrossExchangeComparison:
        """Compare OI data across exchanges"""
        
        if not data_points:
            raise ValueError("No data points provided for comparison")
        
        # Group by exchange
        exchange_data = {dp.exchange: dp for dp in data_points}
        
        # Calculate totals
        total_oi_tokens = sum(dp.open_interest_tokens for dp in data_points if dp.open_interest_tokens)
        total_oi_usd = sum(dp.open_interest_usd for dp in data_points if dp.open_interest_usd)
        
        # Calculate price consensus (median to avoid outliers)
        prices = [dp.current_price for dp in data_points if dp.current_price]
        price_consensus = statistics.median(prices) if prices else 0
        
        # Find price outliers
        outliers = []
        max_deviation = 0
        
        for dp in data_points:
            if dp.current_price and price_consensus:
                deviation = abs((dp.current_price - price_consensus) / price_consensus) * 100
                max_deviation = max(max_deviation, deviation)
                
                if deviation > cls.MAX_PRICE_DEVIATION_PERCENT:
                    outliers.append(f"{dp.exchange}: {deviation:.2f}% deviation")
        
        return CrossExchangeComparison(
            symbol=symbol,
            exchange_data=exchange_data,
            total_oi_tokens=total_oi_tokens,
            total_oi_usd=total_oi_usd,
            price_consensus=price_consensus,
            price_deviation_max=max_deviation,
            outliers=outliers
        )
    
    @classmethod
    def validate_cross_exchange_consistency(cls, comparison: CrossExchangeComparison) -> List[ValidationResult]:
        """Validate consistency across exchanges"""
        results = []
        
        for exchange, data_point in comparison.exchange_data.items():
            result = ValidationResult(data_point, True, ValidationLevel.INFO)
            
            # Check price deviation from consensus
            if data_point.current_price and comparison.price_consensus:
                deviation = abs((data_point.current_price - comparison.price_consensus) / comparison.price_consensus) * 100
                
                if deviation > cls.MAX_PRICE_DEVIATION_PERCENT:
                    result.add_issue(
                        ValidationLevel.WARNING,
                        f"Price deviates {deviation:.2f}% from cross-exchange consensus "
                        f"(${data_point.current_price:,.2f} vs ${comparison.price_consensus:,.2f})"
                    )
            
            # Check for zero OI while others have data
            if data_point.open_interest_tokens == 0:
                other_exchanges_have_data = any(
                    dp.open_interest_tokens > 0 for ex, dp in comparison.exchange_data.items() if ex != exchange
                )
                
                if other_exchanges_have_data:
                    result.add_issue(
                        ValidationLevel.WARNING,
                        f"Zero OI on {exchange} while other exchanges report active markets"
                    )
            
            results.append(result)
        
        return results


class ComprehensiveOIValidator:
    """Main OI validation orchestrator"""
    
    def __init__(self):
        self.math_validator = OIMathValidator()
        self.cross_validator = CrossExchangeValidator()
        self.symbol_standardizer = SymbolStandardizer()
    
    async def validate_single_datapoint(self, data_point: OIDataPoint) -> List[ValidationResult]:
        """Run comprehensive validation on a single OI data point"""
        results = []
        
        # Mathematical validations
        results.append(self.math_validator.validate_price_consistency(data_point))
        results.append(self.math_validator.validate_funding_rate(data_point))
        results.append(self.math_validator.validate_oi_magnitude(data_point))
        results.append(self.math_validator.validate_volume_oi_ratio(data_point))
        
        return results
    
    async def validate_cross_exchange(self, symbol: str, data_points: List[OIDataPoint]) -> Tuple[CrossExchangeComparison, List[ValidationResult]]:
        """Run cross-exchange validation"""
        comparison = self.cross_validator.compare_exchanges(symbol, data_points)
        results = self.cross_validator.validate_cross_exchange_consistency(comparison)
        
        return comparison, results
    
    async def comprehensive_validation_report(self, symbol: str, data_points: List[OIDataPoint]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        # Individual validations
        individual_results = []
        for dp in data_points:
            results = await self.validate_single_datapoint(dp)
            individual_results.extend(results)
        
        # Cross-exchange validation
        comparison, cross_results = await self.validate_cross_exchange(symbol, data_points)
        
        # Compile summary
        total_errors = sum(len(r.errors) for r in individual_results + cross_results)
        total_warnings = sum(len(r.warnings) for r in individual_results + cross_results)
        
        validation_passed = total_errors == 0
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'validation_passed': validation_passed,
            'summary': {
                'total_exchanges': len(data_points),
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'total_oi_tokens': comparison.total_oi_tokens,
                'total_oi_usd': comparison.total_oi_usd,
                'price_consensus': comparison.price_consensus,
                'max_price_deviation': comparison.price_deviation_max,
                'outlier_exchanges': comparison.outliers
            },
            'individual_validations': [
                {
                    'exchange': r.data_point.exchange,
                    'is_valid': r.is_valid,
                    'errors': r.errors,
                    'warnings': r.warnings,
                    'info': r.info
                } for r in individual_results
            ],
            'cross_exchange_validations': [
                {
                    'exchange': r.data_point.exchange,
                    'is_valid': r.is_valid,
                    'errors': r.errors,
                    'warnings': r.warnings,
                    'info': r.info
                } for r in cross_results
            ],
            'data_points': [
                {
                    'exchange': dp.exchange,
                    'symbol': dp.symbol,
                    'contract_type': dp.contract_type.value,
                    'open_interest_tokens': dp.open_interest_tokens,
                    'open_interest_usd': dp.open_interest_usd,
                    'current_price': dp.current_price,
                    'calculated_usd_value': dp.calculated_usd_value,
                    'price_deviation': dp.price_deviation,
                    'funding_rate': dp.funding_rate,
                    'volume_24h_tokens': dp.volume_24h_tokens,
                    'timestamp': dp.timestamp.isoformat()
                } for dp in data_points
            ]
        }


# Example usage and testing functions
async def test_oi_validation():
    """Test the OI validation system"""
    
    # Create test data points
    test_data = [
        OIDataPoint(
            symbol="BTCUSDT",
            exchange="binance",
            contract_type=ContractType.LINEAR,
            open_interest_tokens=150000,
            open_interest_usd=15000000000,  # $15B
            current_price=100000,
            funding_rate=0.0001,
            volume_24h_tokens=75000
        ),
        OIDataPoint(
            symbol="BTCUSDT",
            exchange="bybit",
            contract_type=ContractType.LINEAR,
            open_interest_tokens=120000,
            open_interest_usd=12000000000,  # $12B
            current_price=100050,  # Slight price difference
            funding_rate=0.0002,
            volume_24h_tokens=60000
        ),
        OIDataPoint(
            symbol="BTCUSD",
            exchange="bybit",
            contract_type=ContractType.INVERSE,
            open_interest_tokens=50000,
            open_interest_usd=5000000000,  # $5B
            current_price=100000,
            funding_rate=-0.0001,
            volume_24h_tokens=25000
        )
    ]
    
    validator = ComprehensiveOIValidator()
    report = await validator.comprehensive_validation_report("BTC", test_data)
    
    print("🔍 OI Validation Report")
    print("=" * 50)
    print(f"Symbol: {report['symbol']}")
    print(f"Validation Passed: {report['validation_passed']}")
    print(f"Total OI: {report['summary']['total_oi_tokens']:,.0f} BTC (${report['summary']['total_oi_usd']:,.0f})")
    print(f"Price Consensus: ${report['summary']['price_consensus']:,.2f}")
    print(f"Errors: {report['summary']['total_errors']}, Warnings: {report['summary']['total_warnings']}")
    
    if report['summary']['outlier_exchanges']:
        print(f"Price Outliers: {', '.join(report['summary']['outlier_exchanges'])}")
    
    return report


if __name__ == "__main__":
    # Run test
    asyncio.run(test_oi_validation())