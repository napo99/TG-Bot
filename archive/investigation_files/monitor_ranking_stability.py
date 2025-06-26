#!/usr/bin/env python3
"""
COMPREHENSIVE RANKING STABILITY MONITOR

Investigates why Gate.io and Bybit rankings might occasionally flip, despite expected consistent order.
This script performs deep analysis to identify:
- Multi-sample ranking consistency validation
- Individual market contribution analysis  
- Direct API cross-validation
- OI value fluctuation detection
- Data quality and calculation auditing

Expected: Gate.io should be consistently ~1K BTC below Bybit per CoinGlass data.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import traceback
from loguru import logger

@dataclass
class MarketSample:
    """Single market data sample"""
    timestamp: datetime
    symbol: str
    oi_tokens: float
    oi_usd: float
    price: float
    volume_24h: float = 0.0
    source: str = "system"

@dataclass
class ExchangeSample:
    """Single exchange sample with all markets"""
    timestamp: datetime
    exchange: str
    total_oi_tokens: float
    total_oi_usd: float
    markets: List[MarketSample]
    market_count: int
    source: str = "system"

@dataclass
class RankingSample:
    """Single ranking snapshot"""
    timestamp: datetime
    rankings: List[Tuple[str, float]]  # (exchange, oi_tokens)
    sample_id: int
    source: str = "system"

@dataclass
class StabilityAnalysis:
    """Comprehensive stability analysis results"""
    total_samples: int
    sampling_duration: float
    ranking_consistency: Dict[str, Any]
    exchange_stability: Dict[str, Dict[str, Any]]
    market_fluctuations: Dict[str, List[Dict[str, Any]]]
    data_quality_issues: List[Dict[str, Any]]
    cross_validation_results: Dict[str, Any]
    recommendations: List[str]

class RankingStabilityMonitor:
    """Comprehensive ranking stability monitor and analyzer"""
    
    def __init__(self):
        self.our_system_base = "http://localhost:8001"
        self.samples = []
        self.exchange_samples = defaultdict(list)
        self.market_samples = defaultdict(lambda: defaultdict(list))
        
        # Expected CoinGlass rankings for comparison
        self.expected_rankings = {
            'binance': {'btc': 110780, 'rank': 1},
            'bybit': {'btc': 70790, 'rank': 2}, 
            'gateio': {'btc': 69060, 'rank': 3}
        }
        
        # Direct API endpoints for cross-validation
        self.direct_apis = {
            'binance': {
                'fapi_oi': 'https://fapi.binance.com/fapi/v1/openInterest',
                'dapi_oi': 'https://dapi.binance.com/dapi/v1/openInterest',
                'fapi_ticker': 'https://fapi.binance.com/fapi/v1/ticker/24hr',
                'dapi_ticker': 'https://dapi.binance.com/dapi/v1/ticker/24hr'
            },
            'bybit': {
                'oi': 'https://api.bybit.com/v5/market/open-interest',
                'ticker': 'https://api.bybit.com/v5/market/tickers'
            },
            'gateio': {
                'usdt_tickers': 'https://api.gateio.ws/api/v4/futures/usdt/tickers',
                'usdc_tickers': 'https://api.gateio.ws/api/v4/futures/usdc/tickers',
                'usd_tickers': 'https://api.gateio.ws/api/v4/futures/btc/tickers'
            }
        }
        
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'CryptoAssistant-StabilityMonitor/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_comprehensive_stability_analysis(self, base_symbol: str = "BTC") -> StabilityAnalysis:
        """Run comprehensive ranking stability analysis"""
        
        print("🔍 COMPREHENSIVE RANKING STABILITY MONITOR")
        print("=" * 80)
        print(f"Base Symbol: {base_symbol}")
        print(f"Expected Order: Binance > Bybit > Gate.io")
        print(f"Sample Count: 10 samples over 30 seconds")
        print("=" * 80)
        print()
        
        start_time = time.time()
        
        # Phase 1: Multi-sample validation
        print("📊 Phase 1: Multi-sample ranking validation...")
        await self._collect_ranking_samples(base_symbol, samples=10, interval=3.0)
        
        # Phase 2: Individual market analysis  
        print("\n🔬 Phase 2: Individual market contribution analysis...")
        await self._analyze_market_contributions(base_symbol)
        
        # Phase 3: Direct API cross-validation
        print("\n🔗 Phase 3: Direct API cross-validation...")
        await self._cross_validate_with_direct_apis(base_symbol)
        
        # Phase 4: Fluctuation detection
        print("\n📈 Phase 4: OI value fluctuation detection...")
        fluctuation_analysis = self._detect_oi_fluctuations()
        
        # Phase 5: Data quality audit
        print("\n🔍 Phase 5: Data quality audit...")
        quality_issues = self._audit_data_quality()
        
        # Phase 6: Comprehensive analysis
        print("\n📋 Phase 6: Generating comprehensive analysis...")
        analysis = self._generate_stability_analysis(
            time.time() - start_time,
            fluctuation_analysis,
            quality_issues
        )
        
        # Generate detailed report
        self._generate_detailed_report(analysis)
        
        return analysis
    
    async def _collect_ranking_samples(self, base_symbol: str, samples: int, interval: float):
        """Collect multiple ranking samples over time"""
        
        for i in range(samples):
            print(f"  📡 Collecting sample {i+1}/{samples}...")
            
            try:
                # Get our system data
                system_data = await self._get_our_system_data(base_symbol)
                
                if system_data.get('success'):
                    # Extract ranking
                    ranking = self._extract_ranking_from_system_data(system_data, i+1)
                    self.samples.append(ranking)
                    
                    # Extract individual exchange data
                    for exchange_data in system_data.get('exchange_breakdown', []):
                        exchange = exchange_data.get('exchange')
                        if exchange in ['binance', 'bybit', 'gateio']:
                            sample = ExchangeSample(
                                timestamp=datetime.now(),
                                exchange=exchange,
                                total_oi_tokens=exchange_data.get('oi_tokens', 0),
                                total_oi_usd=exchange_data.get('oi_usd', 0),
                                markets=self._extract_markets_from_exchange_data(exchange_data),
                                market_count=len(exchange_data.get('market_breakdown', [])),
                                source="system"
                            )
                            self.exchange_samples[exchange].append(sample)
                    
                    print(f"    ✅ Sample {i+1} collected successfully")
                else:
                    print(f"    ❌ Sample {i+1} failed: {system_data.get('error', 'Unknown error')}")
            
            except Exception as e:
                print(f"    ❌ Sample {i+1} error: {str(e)}")
            
            if i < samples - 1:  # Don't wait after last sample
                await asyncio.sleep(interval)
    
    async def _analyze_market_contributions(self, base_symbol: str):
        """Analyze individual market contributions for Bybit and Gate.io"""
        
        print("  🏛️ Analyzing Bybit market breakdown...")
        await self._analyze_exchange_markets('bybit', base_symbol)
        
        print("  🏛️ Analyzing Gate.io market breakdown...")
        await self._analyze_exchange_markets('gateio', base_symbol)
    
    async def _analyze_exchange_markets(self, exchange: str, base_symbol: str):
        """Deep analysis of individual exchange markets"""
        
        if exchange not in self.exchange_samples:
            print(f"    ⚠️ No samples available for {exchange}")
            return
        
        # Get the latest sample for detailed analysis
        latest_sample = self.exchange_samples[exchange][-1] if self.exchange_samples[exchange] else None
        
        if not latest_sample:
            print(f"    ⚠️ No valid sample for {exchange}")
            return
        
        print(f"  📊 {exchange.upper()} Market Analysis:")
        print(f"    Total OI: {latest_sample.total_oi_tokens:,.0f} {base_symbol} (${latest_sample.total_oi_usd/1e9:.2f}B)")
        print(f"    Market Count: {latest_sample.market_count}")
        print(f"    Markets:")
        
        # Sort markets by OI contribution
        sorted_markets = sorted(latest_sample.markets, key=lambda m: m.oi_tokens, reverse=True)
        
        for market in sorted_markets:
            pct_contribution = (market.oi_tokens / latest_sample.total_oi_tokens * 100) if latest_sample.total_oi_tokens > 0 else 0
            print(f"      • {market.symbol}: {market.oi_tokens:,.0f} {base_symbol} ({pct_contribution:.1f}%)")
    
    async def _cross_validate_with_direct_apis(self, base_symbol: str):
        """Cross-validate key markets with direct exchange APIs"""
        
        # Focus on Bybit and Gate.io since they're the ones that might flip
        exchanges_to_validate = ['bybit', 'gateio']
        
        for exchange in exchanges_to_validate:
            print(f"  🔗 Cross-validating {exchange.upper()} with direct API...")
            
            try:
                direct_oi, direct_markets = await self._get_direct_exchange_oi(exchange, base_symbol)
                
                # Compare with our system data
                our_latest = self.exchange_samples[exchange][-1] if self.exchange_samples[exchange] else None
                
                if our_latest and direct_oi > 0:
                    discrepancy = abs(our_latest.total_oi_tokens - direct_oi)
                    discrepancy_pct = (discrepancy / our_latest.total_oi_tokens * 100) if our_latest.total_oi_tokens > 0 else 0
                    
                    print(f"    Our System: {our_latest.total_oi_tokens:,.0f} {base_symbol}")
                    print(f"    Direct API: {direct_oi:,.0f} {base_symbol}")
                    print(f"    Discrepancy: {discrepancy:,.0f} {base_symbol} ({discrepancy_pct:.1f}%)")
                    
                    if discrepancy_pct > 5:
                        print(f"    ⚠️ Significant discrepancy detected!")
                    else:
                        print(f"    ✅ Data consistent within tolerance")
                        
                    # Store cross-validation results
                    self._store_cross_validation_result(exchange, our_latest.total_oi_tokens, direct_oi, direct_markets)
                
                else:
                    print(f"    ❌ No valid data for comparison")
            
            except Exception as e:
                print(f"    ❌ Cross-validation failed: {str(e)}")
    
    async def _get_direct_exchange_oi(self, exchange: str, base_symbol: str) -> Tuple[float, List[Dict]]:
        """Get OI data directly from exchange APIs"""
        
        if exchange == 'bybit':
            return await self._get_bybit_direct_oi(base_symbol)
        elif exchange == 'gateio':
            return await self._get_gateio_direct_oi(base_symbol)
        else:
            return 0.0, []
    
    async def _get_bybit_direct_oi(self, base_symbol: str) -> Tuple[float, List[Dict]]:
        """Get Bybit OI directly"""
        total_oi = 0.0
        markets = []
        
        try:
            # Linear USDT markets
            symbols = ['BTCUSDT', 'BTCPERP']
            
            for symbol in symbols:
                try:
                    async with self.session.get(
                        self.direct_apis['bybit']['oi'],
                        params={'category': 'linear', 'symbol': symbol}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            result = data.get('result', {})
                            if result.get('list'):
                                oi_data = result['list'][0]
                                oi_amount = float(oi_data.get('openInterest', 0))
                                total_oi += oi_amount
                                
                                markets.append({
                                    'symbol': symbol,
                                    'oi_tokens': oi_amount,
                                    'market_type': 'USDT'
                                })
                except Exception as e:
                    print(f"      ⚠️ {symbol} error: {str(e)}")
            
            # Inverse USD market
            try:
                async with self.session.get(
                    self.direct_apis['bybit']['oi'],
                    params={'category': 'inverse', 'symbol': 'BTCUSD'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result', {})
                        if result.get('list'):
                            oi_data = result['list'][0]
                            oi_contracts = float(oi_data.get('openInterest', 0))
                            
                            # Get price for conversion
                            async with self.session.get(
                                self.direct_apis['bybit']['ticker'],
                                params={'category': 'inverse', 'symbol': 'BTCUSD'}
                            ) as ticker_response:
                                if ticker_response.status == 200:
                                    ticker_data = await ticker_response.json()
                                    ticker_result = ticker_data.get('result', {})
                                    if ticker_result.get('list'):
                                        ticker_info = ticker_result['list'][0]
                                        price = float(ticker_info.get('lastPrice', 0))
                                        
                                        # Inverse: each contract is $1 USD, convert to BTC
                                        oi_btc = oi_contracts / price if price > 0 else 0
                                        total_oi += oi_btc
                                        
                                        markets.append({
                                            'symbol': 'BTCUSD',
                                            'oi_tokens': oi_btc,
                                            'market_type': 'USD'
                                        })
            except Exception as e:
                print(f"      ⚠️ BTCUSD inverse error: {str(e)}")
        
        except Exception as e:
            print(f"    ❌ Bybit direct API error: {str(e)}")
        
        return total_oi, markets
    
    async def _get_gateio_direct_oi(self, base_symbol: str) -> Tuple[float, List[Dict]]:
        """Get Gate.io OI directly"""
        total_oi = 0.0
        markets = []
        
        try:
            # Check different settlement types
            settlements = {
                'usdt_tickers': ('USDT', 'BTC_USDT'),
                'usdc_tickers': ('USDC', 'BTC_USDC'),
                'usd_tickers': ('USD', 'BTC_USD')
            }
            
            for endpoint_key, (settlement_type, symbol) in settlements.items():
                try:
                    async with self.session.get(
                        self.direct_apis['gateio'][endpoint_key]
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Find BTC contract
                            for ticker in data:
                                if ticker.get('contract') == symbol:
                                    oi_size = float(ticker.get('total_size', 0))
                                    last_price = float(ticker.get('last', 0))
                                    
                                    if settlement_type in ['USDT', 'USDC']:
                                        # Linear contracts: oi_size is in BTC
                                        oi_btc = oi_size
                                    else:
                                        # USD inverse: oi_size is in USD, convert to BTC
                                        oi_btc = oi_size / last_price if last_price > 0 else 0
                                    
                                    total_oi += oi_btc
                                    markets.append({
                                        'symbol': symbol,
                                        'oi_tokens': oi_btc,
                                        'market_type': settlement_type
                                    })
                                    break
                except Exception as e:
                    print(f"      ⚠️ {settlement_type} error: {str(e)}")
        
        except Exception as e:
            print(f"    ❌ Gate.io direct API error: {str(e)}")
        
        return total_oi, markets
    
    def _detect_oi_fluctuations(self) -> Dict[str, Any]:
        """Detect OI value fluctuations across samples"""
        
        fluctuation_analysis = {}
        
        for exchange in ['binance', 'bybit', 'gateio']:
            if exchange not in self.exchange_samples:
                continue
                
            samples = self.exchange_samples[exchange]
            if len(samples) < 2:
                continue
            
            # Calculate OI fluctuations
            oi_values = [s.total_oi_tokens for s in samples]
            
            if len(oi_values) > 1:
                mean_oi = statistics.mean(oi_values)
                stdev_oi = statistics.stdev(oi_values) if len(oi_values) > 1 else 0
                min_oi = min(oi_values)
                max_oi = max(oi_values)
                range_oi = max_oi - min_oi
                cv_oi = (stdev_oi / mean_oi * 100) if mean_oi > 0 else 0
                
                fluctuation_analysis[exchange] = {
                    'mean_oi': mean_oi,
                    'stdev_oi': stdev_oi,
                    'min_oi': min_oi,
                    'max_oi': max_oi,
                    'range_oi': range_oi,
                    'coefficient_of_variation': cv_oi,
                    'stability_rating': self._rate_stability(cv_oi),
                    'sample_count': len(oi_values)
                }
        
        return fluctuation_analysis
    
    def _rate_stability(self, cv: float) -> str:
        """Rate stability based on coefficient of variation"""
        if cv < 0.5:
            return "VERY_STABLE"
        elif cv < 1.0:
            return "STABLE"
        elif cv < 2.0:
            return "MODERATELY_STABLE"
        elif cv < 5.0:
            return "UNSTABLE"
        else:
            return "VERY_UNSTABLE"
    
    def _audit_data_quality(self) -> List[Dict[str, Any]]:
        """Audit data quality and identify potential issues"""
        
        issues = []
        
        # Check for missing data
        for exchange in ['binance', 'bybit', 'gateio']:
            if exchange not in self.exchange_samples or not self.exchange_samples[exchange]:
                issues.append({
                    'type': 'MISSING_DATA',
                    'exchange': exchange,
                    'description': f"No valid samples collected for {exchange}",
                    'severity': 'HIGH'
                })
        
        # Check for extreme values
        for exchange, samples in self.exchange_samples.items():
            for sample in samples:
                if sample.total_oi_tokens > 1000000:  # > 1M BTC is suspicious
                    issues.append({
                        'type': 'EXTREME_VALUE',
                        'exchange': exchange,
                        'description': f"Extreme OI value detected: {sample.total_oi_tokens:,.0f} BTC",
                        'severity': 'HIGH',
                        'timestamp': sample.timestamp.isoformat()
                    })
                
                if sample.total_oi_tokens == 0:
                    issues.append({
                        'type': 'ZERO_VALUE',
                        'exchange': exchange,
                        'description': f"Zero OI value detected",
                        'severity': 'MEDIUM',
                        'timestamp': sample.timestamp.isoformat()
                    })
        
        # Check for calculation errors
        for exchange, samples in self.exchange_samples.items():
            for sample in samples:
                # Verify USD calculation consistency
                if sample.markets:
                    calculated_usd = sum(m.oi_tokens * m.price for m in sample.markets)
                    reported_usd = sample.total_oi_usd
                    
                    if abs(calculated_usd - reported_usd) > reported_usd * 0.05:  # 5% tolerance
                        issues.append({
                            'type': 'CALCULATION_INCONSISTENCY',
                            'exchange': exchange,
                            'description': f"USD calculation mismatch: calculated {calculated_usd/1e9:.2f}B vs reported {reported_usd/1e9:.2f}B",
                            'severity': 'MEDIUM',
                            'timestamp': sample.timestamp.isoformat()
                        })
        
        return issues
    
    def _generate_stability_analysis(self, duration: float, fluctuation_analysis: Dict, quality_issues: List) -> StabilityAnalysis:
        """Generate comprehensive stability analysis"""
        
        # Analyze ranking consistency
        ranking_consistency = self._analyze_ranking_consistency()
        
        # Analyze exchange stability
        exchange_stability = {}
        for exchange in ['binance', 'bybit', 'gateio']:
            if exchange in fluctuation_analysis:
                exchange_stability[exchange] = fluctuation_analysis[exchange]
        
        # Analyze market fluctuations
        market_fluctuations = self._analyze_market_level_fluctuations()
        
        # Cross-validation results
        cross_validation_results = getattr(self, 'cross_validation_results', {})
        
        # Generate recommendations
        recommendations = self._generate_recommendations(ranking_consistency, exchange_stability, quality_issues)
        
        return StabilityAnalysis(
            total_samples=len(self.samples),
            sampling_duration=duration,
            ranking_consistency=ranking_consistency,
            exchange_stability=exchange_stability,
            market_fluctuations=market_fluctuations,
            data_quality_issues=quality_issues,
            cross_validation_results=cross_validation_results,
            recommendations=recommendations
        )
    
    def _analyze_ranking_consistency(self) -> Dict[str, Any]:
        """Analyze ranking consistency across samples"""
        
        if not self.samples:
            return {'error': 'No samples available'}
        
        # Track ranking positions
        position_tracking = defaultdict(list)
        all_rankings = []
        
        for sample in self.samples:
            ranking_dict = {exchange: oi for exchange, oi in sample.rankings}
            all_rankings.append(ranking_dict)
            
            # Sort by OI and assign positions
            sorted_exchanges = sorted(sample.rankings, key=lambda x: x[1], reverse=True)
            for position, (exchange, oi) in enumerate(sorted_exchanges, 1):
                position_tracking[exchange].append(position)
        
        # Calculate consistency metrics
        consistency_metrics = {}
        for exchange in ['binance', 'bybit', 'gateio']:
            if exchange in position_tracking:
                positions = position_tracking[exchange]
                most_common_position = max(set(positions), key=positions.count)
                consistency_rate = positions.count(most_common_position) / len(positions) * 100
                
                consistency_metrics[exchange] = {
                    'most_common_position': most_common_position,
                    'consistency_rate': consistency_rate,
                    'position_variance': statistics.variance(positions) if len(positions) > 1 else 0,
                    'all_positions': positions
                }
        
        # Check for ranking flips specifically between Bybit and Gate.io
        bybit_gate_flips = 0
        for sample in self.samples:
            ranking_dict = {exchange: oi for exchange, oi in sample.rankings}
            if 'bybit' in ranking_dict and 'gateio' in ranking_dict:
                if ranking_dict['gateio'] > ranking_dict['bybit']:
                    bybit_gate_flips += 1
        
        flip_rate = (bybit_gate_flips / len(self.samples) * 100) if self.samples else 0
        
        return {
            'total_samples': len(self.samples),
            'exchange_consistency': consistency_metrics,
            'bybit_gateio_flip_count': bybit_gate_flips,
            'bybit_gateio_flip_rate': flip_rate,
            'ranking_stable': flip_rate < 10,  # Less than 10% flip rate is considered stable
            'all_rankings': all_rankings
        }
    
    def _analyze_market_level_fluctuations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze fluctuations at individual market level"""
        
        market_fluctuations = {}
        
        for exchange in ['bybit', 'gateio']:
            if exchange not in self.exchange_samples:
                continue
            
            # Track individual markets across samples
            market_tracking = defaultdict(list)
            
            for sample in self.exchange_samples[exchange]:
                for market in sample.markets:
                    market_tracking[market.symbol].append({
                        'timestamp': sample.timestamp,
                        'oi_tokens': market.oi_tokens,
                        'price': market.price
                    })
            
            # Analyze fluctuations for each market
            exchange_fluctuations = []
            for symbol, data_points in market_tracking.items():
                if len(data_points) > 1:
                    oi_values = [dp['oi_tokens'] for dp in data_points]
                    mean_oi = statistics.mean(oi_values)
                    stdev_oi = statistics.stdev(oi_values)
                    cv = (stdev_oi / mean_oi * 100) if mean_oi > 0 else 0
                    
                    exchange_fluctuations.append({
                        'symbol': symbol,
                        'mean_oi': mean_oi,
                        'stdev_oi': stdev_oi,
                        'coefficient_of_variation': cv,
                        'stability_rating': self._rate_stability(cv),
                        'data_points': len(data_points)
                    })
            
            market_fluctuations[exchange] = exchange_fluctuations
        
        return market_fluctuations
    
    def _generate_recommendations(self, ranking_consistency: Dict, exchange_stability: Dict, quality_issues: List) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Ranking consistency recommendations
        if ranking_consistency.get('bybit_gateio_flip_rate', 0) > 10:
            recommendations.append(
                f"🚨 CRITICAL: Bybit/Gate.io ranking flips detected in {ranking_consistency['bybit_gateio_flip_rate']:.1f}% of samples. "
                "This indicates data instability or calculation errors."
            )
        
        # Exchange stability recommendations
        for exchange, stability in exchange_stability.items():
            if stability['stability_rating'] in ['UNSTABLE', 'VERY_UNSTABLE']:
                recommendations.append(
                    f"⚠️ {exchange.upper()} shows {stability['stability_rating']} OI values "
                    f"(CV: {stability['coefficient_of_variation']:.2f}%). Review provider implementation."
                )
        
        # Data quality recommendations
        high_severity_issues = [issue for issue in quality_issues if issue.get('severity') == 'HIGH']
        if high_severity_issues:
            recommendations.append(
                f"🔧 HIGH PRIORITY: {len(high_severity_issues)} high-severity data quality issues detected. "
                "Immediate provider fixes required."
            )
        
        # Specific recommendations based on analysis
        if not recommendations:
            recommendations.append("✅ No critical issues detected. Rankings appear stable and consistent.")
        
        return recommendations
    
    def _generate_detailed_report(self, analysis: StabilityAnalysis):
        """Generate comprehensive detailed report"""
        
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE RANKING STABILITY ANALYSIS REPORT")
        print("=" * 80)
        
        # Executive Summary
        print(f"\n🎯 EXECUTIVE SUMMARY:")
        print(f"   Samples Collected: {analysis.total_samples}")
        print(f"   Analysis Duration: {analysis.sampling_duration:.1f} seconds")
        print(f"   Ranking Stability: {'✅ STABLE' if analysis.ranking_consistency.get('ranking_stable') else '❌ UNSTABLE'}")
        
        # Ranking Consistency Analysis
        print(f"\n📊 RANKING CONSISTENCY ANALYSIS:")
        consistency = analysis.ranking_consistency
        
        print(f"   Bybit/Gate.io Ranking Flips: {consistency.get('bybit_gateio_flip_count', 0)}/{analysis.total_samples} samples")
        print(f"   Flip Rate: {consistency.get('bybit_gateio_flip_rate', 0):.1f}%")
        
        if 'exchange_consistency' in consistency:
            for exchange, metrics in consistency['exchange_consistency'].items():
                print(f"   {exchange.title()} Position Consistency: {metrics['consistency_rate']:.1f}% (Position {metrics['most_common_position']})")
        
        # Exchange Stability Analysis
        print(f"\n🏛️ EXCHANGE STABILITY ANALYSIS:")
        for exchange, stability in analysis.exchange_stability.items():
            print(f"   {exchange.upper()}:")
            print(f"      OI Range: {stability['min_oi']:,.0f} - {stability['max_oi']:,.0f} BTC")
            print(f"      Coefficient of Variation: {stability['coefficient_of_variation']:.2f}%")
            print(f"      Stability Rating: {stability['stability_rating']}")
        
        # Cross-Validation Results
        if analysis.cross_validation_results:
            print(f"\n🔗 CROSS-VALIDATION RESULTS:")
            for exchange, result in analysis.cross_validation_results.items():
                discrepancy_pct = abs(result['our_system'] - result['direct_api']) / result['our_system'] * 100 if result['our_system'] > 0 else 0
                print(f"   {exchange.upper()}:")
                print(f"      Our System: {result['our_system']:,.0f} BTC")
                print(f"      Direct API: {result['direct_api']:,.0f} BTC")
                print(f"      Discrepancy: {discrepancy_pct:.1f}%")
        
        # Data Quality Issues
        if analysis.data_quality_issues:
            print(f"\n🔍 DATA QUALITY ISSUES ({len(analysis.data_quality_issues)} found):")
            for issue in analysis.data_quality_issues:
                severity_icon = "🚨" if issue['severity'] == 'HIGH' else "⚠️"
                print(f"   {severity_icon} {issue['type']}: {issue['description']}")
        
        # Market-Level Analysis
        if analysis.market_fluctuations:
            print(f"\n📈 MARKET-LEVEL FLUCTUATION ANALYSIS:")
            for exchange, markets in analysis.market_fluctuations.items():
                print(f"   {exchange.upper()} Markets:")
                for market in markets[:5]:  # Show top 5 most fluctuating
                    print(f"      {market['symbol']}: CV {market['coefficient_of_variation']:.1f}% ({market['stability_rating']})")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Root Cause Analysis
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        
        flip_rate = consistency.get('bybit_gateio_flip_rate', 0)
        if flip_rate > 10:
            print(f"   🚨 PRIMARY ISSUE: Bybit/Gate.io ranking instability ({flip_rate:.1f}% flip rate)")
            print(f"      Potential causes:")
            print(f"      • Data provider calculation errors")
            print(f"      • API response timing differences") 
            print(f"      • Field interpretation inconsistencies")
            print(f"      • Missing market coverage")
        elif flip_rate > 0:
            print(f"   ⚠️ MINOR ISSUE: Occasional ranking flips detected ({flip_rate:.1f}% rate)")
            print(f"      This is within acceptable variance for real-time data")
        else:
            print(f"   ✅ NO RANKING ISSUES: Consistent order maintained across all samples")
            print(f"      Expected ranking order (Binance > Bybit > Gate.io) is stable")
        
        # Expected vs Actual Analysis
        print(f"\n📊 EXPECTED vs ACTUAL COMPARISON:")
        print(f"   CoinGlass Expected Order:")
        for exchange, data in self.expected_rankings.items():
            print(f"      {data['rank']}. {exchange.title()}: {data['btc']:,.0f} BTC")
        
        if analysis.ranking_consistency.get('all_rankings'):
            # Show average values from our samples
            avg_rankings = {}
            for exchange in ['binance', 'bybit', 'gateio']:
                values = []
                for ranking in analysis.ranking_consistency['all_rankings']:
                    if exchange in ranking:
                        values.append(ranking[exchange])
                if values:
                    avg_rankings[exchange] = statistics.mean(values)
            
            if avg_rankings:
                sorted_actual = sorted(avg_rankings.items(), key=lambda x: x[1], reverse=True)
                print(f"   Our System Average Order:")
                for i, (exchange, avg_oi) in enumerate(sorted_actual, 1):
                    print(f"      {i}. {exchange.title()}: {avg_oi:,.0f} BTC")
        
        # Save detailed report to file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'analysis': asdict(analysis),
            'raw_samples': [asdict(sample) for sample in self.samples],
            'exchange_samples': {
                exchange: [asdict(sample) for sample in samples]
                for exchange, samples in self.exchange_samples.items()
            }
        }
        
        report_file = "/Users/screener-m3/projects/crypto-assistant/ranking_stability_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed analysis data saved to: ranking_stability_report.json")
        print("\n✅ Ranking stability analysis complete!")
    
    # Helper methods
    async def _get_our_system_data(self, base_symbol: str) -> Dict[str, Any]:
        """Get data from our system's multi-OI endpoint"""
        try:
            async with self.session.post(
                f"{self.our_system_base}/multi_oi",
                json={"base_symbol": base_symbol}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_ranking_from_system_data(self, system_data: Dict, sample_id: int) -> RankingSample:
        """Extract ranking from system response"""
        rankings = []
        
        if system_data.get('success') and 'exchange_breakdown' in system_data:
            for exchange_data in system_data['exchange_breakdown']:
                exchange = exchange_data.get('exchange')
                oi_tokens = exchange_data.get('oi_tokens', 0)
                if exchange in ['binance', 'bybit', 'gateio']:
                    rankings.append((exchange, oi_tokens))
        
        # Sort by OI descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return RankingSample(
            timestamp=datetime.now(),
            rankings=rankings,
            sample_id=sample_id,
            source="system"
        )
    
    def _extract_markets_from_exchange_data(self, exchange_data: Dict) -> List[MarketSample]:
        """Extract market data from exchange breakdown"""
        markets = []
        
        for market_data in exchange_data.get('market_breakdown', []):
            market = MarketSample(
                timestamp=datetime.now(),
                symbol=market_data.get('symbol', ''),
                oi_tokens=market_data.get('oi_tokens', 0),
                oi_usd=market_data.get('oi_usd', 0),
                price=market_data.get('price', 0),
                volume_24h=market_data.get('volume_24h', 0),
                source="system"
            )
            markets.append(market)
        
        return markets
    
    def _store_cross_validation_result(self, exchange: str, our_system: float, direct_api: float, markets: List):
        """Store cross-validation results"""
        if not hasattr(self, 'cross_validation_results'):
            self.cross_validation_results = {}
        
        self.cross_validation_results[exchange] = {
            'our_system': our_system,
            'direct_api': direct_api,
            'markets': markets,
            'timestamp': datetime.now().isoformat()
        }

async def main():
    """Main monitoring function"""
    try:
        async with RankingStabilityMonitor() as monitor:
            analysis = await monitor.run_comprehensive_stability_analysis("BTC")
            return analysis
    except Exception as e:
        print(f"❌ Monitoring failed: {str(e)}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())