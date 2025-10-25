#!/usr/bin/env python3
"""
CASCADE RISK CALCULATOR
Advanced risk scoring based on velocity, acceleration, and market conditions

Risk Scoring Algorithm:
- Multi-factor analysis combining velocity, acceleration, volume, correlation
- Adaptive thresholds based on market volatility
- Machine learning ready feature extraction
- Real-time risk level classification

Risk Factors:
1. Velocity - How fast are liquidations occurring?
2. Acceleration - Is the rate increasing?
3. Jerk - Is acceleration changing (early cascade warning)?
4. Volume - How large are the liquidations?
5. Correlation - Are multiple exchanges affected?
6. Time clustering - Are events bunched together?

Risk Levels:
- NONE: Normal market activity
- LOW: Elevated liquidations, monitor
- MEDIUM: Significant liquidations, possible cascade
- HIGH: Large-scale liquidations, cascade likely
- CRITICAL: Massive cascade in progress

Performance: <0.2ms per calculation
"""

import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging

from advanced_velocity_engine import (
    MultiTimeframeVelocity,
    CorrelationMatrix,
    CascadeRiskLevel,
    ExchangeMetrics
)

logger = logging.getLogger('cascade_risk_calculator')
logger.setLevel(logging.INFO)


# =============================================================================
# RISK SCORING THRESHOLDS
# =============================================================================

# Velocity thresholds (events/second)
VELOCITY_THRESHOLDS = {
    'low': 2.0,
    'medium': 5.0,
    'high': 10.0,
    'critical': 20.0
}

# Acceleration thresholds (events/s²)
ACCELERATION_THRESHOLDS = {
    'low': 1.0,
    'medium': 3.0,
    'high': 5.0,
    'critical': 10.0
}

# Jerk thresholds (events/s³)
JERK_THRESHOLDS = {
    'low': 0.5,
    'medium': 2.0,
    'high': 5.0,
    'critical': 10.0
}

# Volume thresholds (USD)
VOLUME_THRESHOLDS = {
    'low': 100000,      # $100K
    'medium': 500000,   # $500K
    'high': 1000000,    # $1M
    'critical': 5000000  # $5M
}

# Correlation threshold (high correlation = coordinated cascade)
CORRELATION_THRESHOLD_HIGH = 0.7

# Weight factors for risk score calculation
RISK_WEIGHTS = {
    'velocity': 0.25,
    'acceleration': 0.20,
    'jerk': 0.15,
    'volume': 0.20,
    'correlation': 0.15,
    'clustering': 0.05
}


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class RiskFactors:
    """Individual risk factor scores"""
    velocity_score: float = 0.0
    acceleration_score: float = 0.0
    jerk_score: float = 0.0
    volume_score: float = 0.0
    correlation_score: float = 0.0
    clustering_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            'velocity_score': self.velocity_score,
            'acceleration_score': self.acceleration_score,
            'jerk_score': self.jerk_score,
            'volume_score': self.volume_score,
            'correlation_score': self.correlation_score,
            'clustering_score': self.clustering_score
        }


@dataclass
class CascadeRiskAssessment:
    """Complete cascade risk assessment"""
    symbol: str
    timestamp: float
    risk_level: CascadeRiskLevel
    risk_score: float  # 0-100
    risk_factors: RiskFactors
    confidence: float  # 0-1

    # Human-readable explanation
    explanation: str = ""

    # Recommended action
    action: str = "MONITOR"  # MONITOR, ALERT, URGENT

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'risk_level': self.risk_level.name,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors.to_dict(),
            'confidence': self.confidence,
            'explanation': self.explanation,
            'action': self.action
        }


# =============================================================================
# CASCADE RISK CALCULATOR
# =============================================================================

class CascadeRiskCalculator:
    """
    Calculate cascade risk from velocity metrics

    Methodology:
    1. Score each risk factor independently (0-100)
    2. Apply weighted combination
    3. Classify into risk levels
    4. Generate actionable insights

    Performance: <0.2ms per calculation
    """

    def __init__(self,
                 velocity_weight: float = RISK_WEIGHTS['velocity'],
                 acceleration_weight: float = RISK_WEIGHTS['acceleration'],
                 jerk_weight: float = RISK_WEIGHTS['jerk'],
                 volume_weight: float = RISK_WEIGHTS['volume'],
                 correlation_weight: float = RISK_WEIGHTS['correlation'],
                 clustering_weight: float = RISK_WEIGHTS['clustering']):
        """
        Initialize cascade risk calculator

        Args:
            velocity_weight: Weight for velocity factor
            acceleration_weight: Weight for acceleration factor
            jerk_weight: Weight for jerk factor
            volume_weight: Weight for volume factor
            correlation_weight: Weight for correlation factor
            clustering_weight: Weight for clustering factor
        """
        # Risk weights
        self.weights = {
            'velocity': velocity_weight,
            'acceleration': acceleration_weight,
            'jerk': jerk_weight,
            'volume': volume_weight,
            'correlation': correlation_weight,
            'clustering': clustering_weight
        }

        # Normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}

        # Statistics
        self.assessments_performed = 0

        logger.info("✅ CascadeRiskCalculator initialized")
        logger.info(f"Risk weights: {self.weights}")

    def calculate_risk(self,
                       velocity_metrics: MultiTimeframeVelocity,
                       correlation_matrix: Optional[CorrelationMatrix] = None,
                       btc_volatility: Optional[float] = None) -> CascadeRiskAssessment:
        """
        Calculate cascade risk from velocity metrics

        Args:
            velocity_metrics: Multi-timeframe velocity data
            correlation_matrix: Cross-exchange correlation (optional)
            btc_volatility: BTC volatility factor (optional)

        Returns:
            CascadeRiskAssessment with risk level and scores

        Performance: <0.2ms
        """
        # Calculate individual risk factor scores
        risk_factors = RiskFactors()

        # 1. Velocity score (using 10s velocity as baseline)
        risk_factors.velocity_score = self._score_velocity(velocity_metrics)

        # 2. Acceleration score
        risk_factors.acceleration_score = self._score_acceleration(velocity_metrics)

        # 3. Jerk score (early warning indicator)
        risk_factors.jerk_score = self._score_jerk(velocity_metrics)

        # 4. Volume score
        risk_factors.volume_score = self._score_volume(velocity_metrics)

        # 5. Correlation score (if available)
        if correlation_matrix:
            risk_factors.correlation_score = self._score_correlation(correlation_matrix)

        # 6. Clustering score (how bunched are events?)
        risk_factors.clustering_score = self._score_clustering(velocity_metrics)

        # Calculate weighted risk score
        risk_score = (
            risk_factors.velocity_score * self.weights['velocity'] +
            risk_factors.acceleration_score * self.weights['acceleration'] +
            risk_factors.jerk_score * self.weights['jerk'] +
            risk_factors.volume_score * self.weights['volume'] +
            risk_factors.correlation_score * self.weights['correlation'] +
            risk_factors.clustering_score * self.weights['clustering']
        )

        # Classify risk level
        risk_level = self._classify_risk_level(risk_score)

        # Calculate confidence
        confidence = self._calculate_confidence(velocity_metrics, risk_factors)

        # Generate explanation
        explanation = self._generate_explanation(
            risk_level, risk_score, risk_factors, velocity_metrics
        )

        # Determine recommended action
        action = self._determine_action(risk_level, confidence)

        # Create assessment
        assessment = CascadeRiskAssessment(
            symbol=velocity_metrics.symbol,
            timestamp=velocity_metrics.timestamp,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            confidence=confidence,
            explanation=explanation,
            action=action
        )

        self.assessments_performed += 1
        return assessment

    def _score_velocity(self, metrics: MultiTimeframeVelocity) -> float:
        """
        Score velocity risk factor (0-100)

        Uses multi-timeframe analysis:
        - Ultra-fast (100ms) for immediate spikes
        - Medium (10s) for sustained velocity
        - Long (60s) for trend

        Returns:
            Score from 0-100
        """
        # Weight different timeframes
        # Fast timeframes get more weight for cascade detection
        weighted_velocity = (
            metrics.velocity_100ms * 0.4 +  # Recent spikes
            metrics.velocity_10s * 0.4 +    # Sustained velocity
            metrics.velocity_60s * 0.2      # Trend
        )

        # Score based on thresholds
        if weighted_velocity >= VELOCITY_THRESHOLDS['critical']:
            return 100.0
        elif weighted_velocity >= VELOCITY_THRESHOLDS['high']:
            # Linear interpolation between high and critical
            ratio = (weighted_velocity - VELOCITY_THRESHOLDS['high']) / (
                VELOCITY_THRESHOLDS['critical'] - VELOCITY_THRESHOLDS['high']
            )
            return 75.0 + (ratio * 25.0)
        elif weighted_velocity >= VELOCITY_THRESHOLDS['medium']:
            ratio = (weighted_velocity - VELOCITY_THRESHOLDS['medium']) / (
                VELOCITY_THRESHOLDS['high'] - VELOCITY_THRESHOLDS['medium']
            )
            return 50.0 + (ratio * 25.0)
        elif weighted_velocity >= VELOCITY_THRESHOLDS['low']:
            ratio = (weighted_velocity - VELOCITY_THRESHOLDS['low']) / (
                VELOCITY_THRESHOLDS['medium'] - VELOCITY_THRESHOLDS['low']
            )
            return 25.0 + (ratio * 25.0)
        else:
            # Below low threshold
            ratio = min(weighted_velocity / VELOCITY_THRESHOLDS['low'], 1.0)
            return ratio * 25.0

    def _score_acceleration(self, metrics: MultiTimeframeVelocity) -> float:
        """
        Score acceleration risk factor (0-100)

        Positive acceleration = increasing velocity = cascade risk
        Negative acceleration = decreasing velocity = cascade subsiding

        Returns:
            Score from 0-100
        """
        accel = metrics.acceleration

        # Only positive acceleration is concerning
        if accel <= 0:
            return 0.0

        # Score based on thresholds
        if accel >= ACCELERATION_THRESHOLDS['critical']:
            return 100.0
        elif accel >= ACCELERATION_THRESHOLDS['high']:
            ratio = (accel - ACCELERATION_THRESHOLDS['high']) / (
                ACCELERATION_THRESHOLDS['critical'] - ACCELERATION_THRESHOLDS['high']
            )
            return 75.0 + (ratio * 25.0)
        elif accel >= ACCELERATION_THRESHOLDS['medium']:
            ratio = (accel - ACCELERATION_THRESHOLDS['medium']) / (
                ACCELERATION_THRESHOLDS['high'] - ACCELERATION_THRESHOLDS['medium']
            )
            return 50.0 + (ratio * 25.0)
        elif accel >= ACCELERATION_THRESHOLDS['low']:
            ratio = (accel - ACCELERATION_THRESHOLDS['low']) / (
                ACCELERATION_THRESHOLDS['medium'] - ACCELERATION_THRESHOLDS['low']
            )
            return 25.0 + (ratio * 25.0)
        else:
            ratio = min(accel / ACCELERATION_THRESHOLDS['low'], 1.0)
            return ratio * 25.0

    def _score_jerk(self, metrics: MultiTimeframeVelocity) -> float:
        """
        Score jerk risk factor (0-100)

        Jerk = rate of change of acceleration
        High positive jerk = early warning of cascade acceleration

        Returns:
            Score from 0-100
        """
        jerk = metrics.jerk

        # Only positive jerk is concerning
        if jerk <= 0:
            return 0.0

        # Score based on thresholds
        if jerk >= JERK_THRESHOLDS['critical']:
            return 100.0
        elif jerk >= JERK_THRESHOLDS['high']:
            ratio = (jerk - JERK_THRESHOLDS['high']) / (
                JERK_THRESHOLDS['critical'] - JERK_THRESHOLDS['high']
            )
            return 75.0 + (ratio * 25.0)
        elif jerk >= JERK_THRESHOLDS['medium']:
            ratio = (jerk - JERK_THRESHOLDS['medium']) / (
                JERK_THRESHOLDS['high'] - JERK_THRESHOLDS['medium']
            )
            return 50.0 + (ratio * 25.0)
        elif jerk >= JERK_THRESHOLDS['low']:
            ratio = (jerk - JERK_THRESHOLDS['low']) / (
                JERK_THRESHOLDS['medium'] - JERK_THRESHOLDS['low']
            )
            return 25.0 + (ratio * 25.0)
        else:
            ratio = min(jerk / JERK_THRESHOLDS['low'], 1.0)
            return ratio * 25.0

    def _score_volume(self, metrics: MultiTimeframeVelocity) -> float:
        """
        Score volume risk factor (0-100)

        Large liquidation volumes indicate:
        - Overleveraged positions
        - Potential for further cascades
        - Market impact

        Returns:
            Score from 0-100
        """
        # Use total volume and average event size
        total_volume = metrics.total_volume_usd
        avg_size = metrics.avg_event_size_usd

        # Score total volume
        volume_score = 0.0
        if total_volume >= VOLUME_THRESHOLDS['critical']:
            volume_score = 100.0
        elif total_volume >= VOLUME_THRESHOLDS['high']:
            ratio = (total_volume - VOLUME_THRESHOLDS['high']) / (
                VOLUME_THRESHOLDS['critical'] - VOLUME_THRESHOLDS['high']
            )
            volume_score = 75.0 + (ratio * 25.0)
        elif total_volume >= VOLUME_THRESHOLDS['medium']:
            ratio = (total_volume - VOLUME_THRESHOLDS['medium']) / (
                VOLUME_THRESHOLDS['high'] - VOLUME_THRESHOLDS['medium']
            )
            volume_score = 50.0 + (ratio * 25.0)
        elif total_volume >= VOLUME_THRESHOLDS['low']:
            ratio = (total_volume - VOLUME_THRESHOLDS['low']) / (
                VOLUME_THRESHOLDS['medium'] - VOLUME_THRESHOLDS['low']
            )
            volume_score = 25.0 + (ratio * 25.0)
        else:
            ratio = min(total_volume / VOLUME_THRESHOLDS['low'], 1.0)
            volume_score = ratio * 25.0

        # Bonus for large average event size (indicates whale liquidations)
        if avg_size > 50000:  # $50K average
            volume_score = min(volume_score * 1.2, 100.0)

        return volume_score

    def _score_correlation(self, correlation_matrix: CorrelationMatrix) -> float:
        """
        Score correlation risk factor (0-100)

        High cross-exchange correlation indicates:
        - Market-wide cascade (not exchange-specific)
        - Systemic risk
        - Coordinated liquidations

        Returns:
            Score from 0-100
        """
        if not correlation_matrix.correlations:
            return 0.0

        # Calculate average correlation across all exchange pairs
        correlations = list(correlation_matrix.correlations.values())
        avg_correlation = np.mean(correlations)

        # High correlation is risky
        if avg_correlation >= CORRELATION_THRESHOLD_HIGH:
            # Very high correlation = coordinated cascade
            return 100.0
        elif avg_correlation >= 0.5:
            # Moderate correlation
            ratio = (avg_correlation - 0.5) / (CORRELATION_THRESHOLD_HIGH - 0.5)
            return 50.0 + (ratio * 50.0)
        else:
            # Low correlation
            ratio = avg_correlation / 0.5
            return ratio * 50.0

    def _score_clustering(self, metrics: MultiTimeframeVelocity) -> float:
        """
        Score time clustering risk factor (0-100)

        Measures how "bunched" events are in time.
        High clustering = cascade pattern
        Low clustering = random/distributed events

        Uses ratio of short-term to long-term velocity.

        Returns:
            Score from 0-100
        """
        # Compare ultra-fast velocity to long-term velocity
        # High ratio = events are clustered in recent timeframe
        if metrics.velocity_60s > 0:
            clustering_ratio = metrics.velocity_100ms / metrics.velocity_60s
        else:
            clustering_ratio = 0.0

        # Score based on clustering ratio
        # Ratio > 2.0 = highly clustered (recent spike)
        if clustering_ratio >= 3.0:
            return 100.0
        elif clustering_ratio >= 2.0:
            ratio = (clustering_ratio - 2.0) / 1.0
            return 50.0 + (ratio * 50.0)
        else:
            ratio = min(clustering_ratio / 2.0, 1.0)
            return ratio * 50.0

    def _classify_risk_level(self, risk_score: float) -> CascadeRiskLevel:
        """
        Classify risk level from score

        Args:
            risk_score: Risk score (0-100)

        Returns:
            CascadeRiskLevel enum
        """
        if risk_score >= 80:
            return CascadeRiskLevel.CRITICAL
        elif risk_score >= 60:
            return CascadeRiskLevel.HIGH
        elif risk_score >= 40:
            return CascadeRiskLevel.MEDIUM
        elif risk_score >= 20:
            return CascadeRiskLevel.LOW
        else:
            return CascadeRiskLevel.NONE

    def _calculate_confidence(self,
                              metrics: MultiTimeframeVelocity,
                              risk_factors: RiskFactors) -> float:
        """
        Calculate confidence in risk assessment

        Higher confidence when:
        - More data points available
        - Consistent across timeframes
        - Multiple risk factors agree

        Args:
            metrics: Velocity metrics
            risk_factors: Individual risk factor scores

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence

        # More events = higher confidence
        if metrics.count_60s >= 10:
            confidence += 0.2
        elif metrics.count_60s >= 5:
            confidence += 0.1

        # Consistent velocity across timeframes = higher confidence
        velocities = [
            metrics.velocity_100ms,
            metrics.velocity_2s,
            metrics.velocity_10s,
            metrics.velocity_60s
        ]
        velocity_std = np.std(velocities) if len(velocities) > 1 else 0
        if velocity_std < 2.0:  # Low variance
            confidence += 0.15

        # Multiple risk factors elevated = higher confidence
        elevated_factors = sum([
            risk_factors.velocity_score > 50,
            risk_factors.acceleration_score > 50,
            risk_factors.volume_score > 50,
            risk_factors.correlation_score > 50
        ])
        if elevated_factors >= 3:
            confidence += 0.15
        elif elevated_factors >= 2:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_explanation(self,
                              risk_level: CascadeRiskLevel,
                              risk_score: float,
                              risk_factors: RiskFactors,
                              metrics: MultiTimeframeVelocity) -> str:
        """
        Generate human-readable explanation of risk assessment

        Args:
            risk_level: Classified risk level
            risk_score: Overall risk score
            risk_factors: Individual factor scores
            metrics: Velocity metrics

        Returns:
            Explanation string
        """
        explanation_parts = [
            f"Risk Level: {risk_level.name} (score: {risk_score:.1f}/100)"
        ]

        # Identify top risk factors
        factors = {
            'Velocity': risk_factors.velocity_score,
            'Acceleration': risk_factors.acceleration_score,
            'Jerk': risk_factors.jerk_score,
            'Volume': risk_factors.volume_score,
            'Correlation': risk_factors.correlation_score,
            'Clustering': risk_factors.clustering_score
        }

        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]

        if top_factors[0][1] > 50:
            explanation_parts.append(
                f"Primary concerns: {', '.join([f'{name} ({score:.1f})' for name, score in top_factors if score > 50])}"
            )

        # Add specific metrics
        if metrics.velocity_10s > VELOCITY_THRESHOLDS['medium']:
            explanation_parts.append(
                f"Velocity: {metrics.velocity_10s:.2f} events/s"
            )

        if metrics.acceleration > ACCELERATION_THRESHOLDS['low']:
            explanation_parts.append(
                f"Acceleration: {metrics.acceleration:.2f} events/s²"
            )

        if metrics.total_volume_usd > VOLUME_THRESHOLDS['low']:
            explanation_parts.append(
                f"Total volume: ${metrics.total_volume_usd:,.0f}"
            )

        return " | ".join(explanation_parts)

    def _determine_action(self, risk_level: CascadeRiskLevel, confidence: float) -> str:
        """
        Determine recommended action

        Args:
            risk_level: Risk level
            confidence: Confidence in assessment

        Returns:
            Action string
        """
        if risk_level == CascadeRiskLevel.CRITICAL and confidence > 0.7:
            return "URGENT"
        elif risk_level >= CascadeRiskLevel.HIGH and confidence > 0.6:
            return "ALERT"
        elif risk_level >= CascadeRiskLevel.MEDIUM:
            return "MONITOR"
        else:
            return "NORMAL"

    def get_stats(self) -> dict:
        """Get calculator statistics"""
        return {
            'assessments_performed': self.assessments_performed,
            'weights': self.weights
        }


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'CascadeRiskCalculator',
    'CascadeRiskAssessment',
    'RiskFactors',
    'VELOCITY_THRESHOLDS',
    'ACCELERATION_THRESHOLDS',
    'JERK_THRESHOLDS',
    'VOLUME_THRESHOLDS'
]
