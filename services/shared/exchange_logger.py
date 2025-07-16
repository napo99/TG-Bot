"""
Exchange API Logger
Provides specialized logging for external exchange interactions
"""

import time
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from .structured_logger import (
    StructuredLogger,
    ExchangeAPIData,
    ErrorContext,
    PerformanceMetric
)

@dataclass
class ExchangeMetrics:
    """Exchange performance metrics"""
    exchange: str
    avg_response_time_ms: float
    success_rate: float
    total_requests: int
    error_count: int
    rate_limit_hits: int
    last_error: Optional[str] = None

class ExchangeLogger(StructuredLogger):
    """Enhanced logger for exchange API interactions"""
    
    def __init__(self):
        super().__init__('exchange-api', 'client')
        self._exchange_metrics: Dict[str, ExchangeMetrics] = {}
        self._request_counters: Dict[str, int] = {}
        self._response_times: Dict[str, List[float]] = {}
    
    def log_ccxt_operation(self, exchange_name: str, operation: str, symbol: str = None,
                          timeframe: str = None, success: bool = True, 
                          response_time_ms: float = None, error: str = None,
                          data_size: int = None):
        """Log CCXT exchange operations"""
        api_data = ExchangeAPIData(
            exchange=exchange_name,
            endpoint=operation,
            method='GET',  # Most CCXT operations are GET
            symbol=symbol,
            success=success,
            response_time_ms=response_time_ms or 0,
            error=error,
            response_size=data_size
        )
        
        self.log_exchange_api_call(api_data)
        
        # Update exchange metrics
        self._update_exchange_metrics(exchange_name, success, response_time_ms or 0, error)
        
        # Log operation details
        self.log_business_event('ccxt_operation', {
            'exchange': exchange_name,
            'operation': operation,
            'symbol': symbol,
            'timeframe': timeframe,
            'success': success,
            'response_time_ms': response_time_ms,
            'data_size_bytes': data_size,
            'error': error
        })
    
    def log_exchange_initialization(self, exchange_name: str, config: Dict[str, Any],
                                  success: bool, initialization_time_ms: float,
                                  error: str = None):
        """Log exchange initialization"""
        safe_config = {k: '***' if 'key' in k.lower() or 'secret' in k.lower() 
                      else v for k, v in config.items()}
        
        self.log_business_event('exchange_initialization', {
            'exchange': exchange_name,
            'config': safe_config,
            'success': success,
            'initialization_time_ms': initialization_time_ms,
            'error': error,
            'sandbox_mode': config.get('sandbox', False),
            'rate_limit': config.get('rateLimit', 'unknown')
        })
    
    def log_market_data_request(self, exchange_name: str, symbol: str, 
                               data_type: str, params: Dict[str, Any] = None,
                               response_time_ms: float = None, success: bool = True,
                               data_points: int = None, error: str = None):
        """Log market data requests"""
        self.log_ccxt_operation(
            exchange_name=exchange_name,
            operation=f'fetch_{data_type}',
            symbol=symbol,
            success=success,
            response_time_ms=response_time_ms,
            error=error,
            data_size=data_points
        )
        
        # Additional context for market data
        self.log_business_event('market_data_request', {
            'exchange': exchange_name,
            'symbol': symbol,
            'data_type': data_type,
            'params': params or {},
            'data_points_received': data_points,
            'data_freshness_score': self._calculate_freshness_score(response_time_ms),
            'timestamp': time.time()
        })
    
    def log_orderbook_request(self, exchange_name: str, symbol: str, 
                             depth: int, response_time_ms: float,
                             bid_levels: int, ask_levels: int, success: bool = True,
                             error: str = None):
        """Log orderbook requests"""
        self.log_ccxt_operation(
            exchange_name=exchange_name,
            operation='fetch_order_book',
            symbol=symbol,
            success=success,
            response_time_ms=response_time_ms,
            error=error,
            data_size=bid_levels + ask_levels
        )
        
        self.log_business_event('orderbook_request', {
            'exchange': exchange_name,
            'symbol': symbol,
            'requested_depth': depth,
            'actual_bid_levels': bid_levels,
            'actual_ask_levels': ask_levels,
            'spread_quality': 'good' if bid_levels >= depth * 0.8 else 'poor',
            'timestamp': time.time()
        })
    
    def log_trading_fees_query(self, exchange_name: str, symbol: str,
                              maker_fee: float, taker_fee: float,
                              response_time_ms: float, success: bool = True):
        """Log trading fees queries"""
        self.log_business_event('trading_fees_query', {
            'exchange': exchange_name,
            'symbol': symbol,
            'maker_fee_pct': maker_fee * 100,
            'taker_fee_pct': taker_fee * 100,
            'fee_competitiveness': self._assess_fee_competitiveness(maker_fee, taker_fee),
            'response_time_ms': response_time_ms,
            'success': success
        })
    
    def log_rate_limit_event(self, exchange_name: str, endpoint: str,
                            limit_type: str, retry_after: int = None,
                            requests_remaining: int = None):
        """Log rate limiting events"""
        self.log_security_event('exchange_rate_limit', {
            'exchange': exchange_name,
            'endpoint': endpoint,
            'limit_type': limit_type,
            'retry_after_seconds': retry_after,
            'requests_remaining': requests_remaining,
            'severity': 'high' if retry_after and retry_after > 60 else 'medium'
        }, severity='WARNING')
        
        # Update metrics
        if exchange_name in self._exchange_metrics:
            self._exchange_metrics[exchange_name].rate_limit_hits += 1
    
    def log_connection_error(self, exchange_name: str, error_type: str, 
                           error_message: str, retry_attempt: int = None,
                           max_retries: int = None):
        """Log connection errors"""
        error_context = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            stack_trace='',
            context={
                'exchange': exchange_name,
                'retry_attempt': retry_attempt,
                'max_retries': max_retries,
                'connection_failure': True,
                'timestamp': time.time()
            },
            severity='ERROR' if retry_attempt is None or retry_attempt >= (max_retries or 3) else 'WARNING'
        )
        
        self.log_error(Exception(error_message), error_context)
    
    def log_websocket_connection(self, exchange_name: str, event_type: str,
                               connection_id: str = None, channels: List[str] = None,
                               success: bool = True, error: str = None):
        """Log WebSocket connection events"""
        self.log_business_event('websocket_connection', {
            'exchange': exchange_name,
            'event_type': event_type,  # connect, disconnect, subscribe, unsubscribe
            'connection_id': connection_id,
            'channels': channels or [],
            'channel_count': len(channels) if channels else 0,
            'success': success,
            'error': error,
            'timestamp': time.time()
        })
    
    def log_data_quality_check(self, exchange_name: str, symbol: str,
                              data_type: str, quality_score: float,
                              quality_issues: List[str] = None):
        """Log data quality assessments"""
        self.log_business_event('data_quality_check', {
            'exchange': exchange_name,
            'symbol': symbol,
            'data_type': data_type,
            'quality_score': quality_score,  # 0-100
            'quality_grade': self._get_quality_grade(quality_score),
            'issues': quality_issues or [],
            'issue_count': len(quality_issues) if quality_issues else 0,
            'timestamp': time.time()
        })
    
    def log_arbitrage_opportunity(self, symbol: str, exchanges: List[str],
                                 price_diff_pct: float, volume_available: float,
                                 profit_estimate: float):
        """Log arbitrage opportunities"""
        self.log_business_event('arbitrage_opportunity', {
            'symbol': symbol,
            'exchanges': exchanges,
            'exchange_count': len(exchanges),
            'price_difference_pct': price_diff_pct,
            'volume_available': volume_available,
            'estimated_profit_usd': profit_estimate,
            'opportunity_grade': self._grade_arbitrage_opportunity(price_diff_pct, profit_estimate),
            'timestamp': time.time()
        })
    
    def get_exchange_performance_summary(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """Get performance summary for an exchange"""
        if exchange_name not in self._exchange_metrics:
            return None
        
        metrics = self._exchange_metrics[exchange_name]
        return {
            'exchange': exchange_name,
            'avg_response_time_ms': metrics.avg_response_time_ms,
            'success_rate_pct': metrics.success_rate * 100,
            'total_requests': metrics.total_requests,
            'error_count': metrics.error_count,
            'rate_limit_hits': metrics.rate_limit_hits,
            'reliability_score': self._calculate_reliability_score(metrics),
            'last_error': metrics.last_error
        }
    
    def log_performance_summary(self):
        """Log performance summary for all exchanges"""
        summary = {}
        for exchange_name in self._exchange_metrics:
            summary[exchange_name] = self.get_exchange_performance_summary(exchange_name)
        
        self.log_business_event('exchange_performance_summary', {
            'exchanges': summary,
            'total_exchanges': len(summary),
            'best_performer': self._find_best_performer(summary),
            'worst_performer': self._find_worst_performer(summary),
            'summary_timestamp': time.time()
        })
    
    def _update_exchange_metrics(self, exchange_name: str, success: bool, 
                               response_time_ms: float, error: str = None):
        """Update internal exchange metrics"""
        if exchange_name not in self._exchange_metrics:
            self._exchange_metrics[exchange_name] = ExchangeMetrics(
                exchange=exchange_name,
                avg_response_time_ms=0,
                success_rate=0,
                total_requests=0,
                error_count=0,
                rate_limit_hits=0
            )
        
        metrics = self._exchange_metrics[exchange_name]
        metrics.total_requests += 1
        
        if not success:
            metrics.error_count += 1
            metrics.last_error = error
        
        # Update response time average
        if exchange_name not in self._response_times:
            self._response_times[exchange_name] = []
        
        self._response_times[exchange_name].append(response_time_ms)
        if len(self._response_times[exchange_name]) > 100:  # Keep last 100
            self._response_times[exchange_name] = self._response_times[exchange_name][-100:]
        
        metrics.avg_response_time_ms = sum(self._response_times[exchange_name]) / len(self._response_times[exchange_name])
        metrics.success_rate = (metrics.total_requests - metrics.error_count) / metrics.total_requests
    
    def _calculate_freshness_score(self, response_time_ms: float) -> str:
        """Calculate data freshness score"""
        if response_time_ms is None:
            return 'unknown'
        elif response_time_ms < 100:
            return 'excellent'
        elif response_time_ms < 500:
            return 'good'
        elif response_time_ms < 1000:
            return 'fair'
        else:
            return 'poor'
    
    def _assess_fee_competitiveness(self, maker_fee: float, taker_fee: float) -> str:
        """Assess fee competitiveness"""
        avg_fee = (maker_fee + taker_fee) / 2
        if avg_fee < 0.001:  # < 0.1%
            return 'excellent'
        elif avg_fee < 0.002:  # < 0.2%
            return 'good'
        elif avg_fee < 0.005:  # < 0.5%
            return 'average'
        else:
            return 'expensive'
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _grade_arbitrage_opportunity(self, price_diff_pct: float, profit_estimate: float) -> str:
        """Grade arbitrage opportunity"""
        if price_diff_pct > 2.0 and profit_estimate > 1000:
            return 'excellent'
        elif price_diff_pct > 1.0 and profit_estimate > 500:
            return 'good'
        elif price_diff_pct > 0.5 and profit_estimate > 100:
            return 'moderate'
        else:
            return 'poor'
    
    def _calculate_reliability_score(self, metrics: ExchangeMetrics) -> float:
        """Calculate overall reliability score"""
        success_weight = 0.6
        speed_weight = 0.3
        stability_weight = 0.1
        
        # Success rate component (0-100)
        success_score = metrics.success_rate * 100
        
        # Speed component (inverse of response time, normalized)
        speed_score = max(0, 100 - (metrics.avg_response_time_ms / 10))
        
        # Stability component (inverse of rate limit hits)
        stability_score = max(0, 100 - (metrics.rate_limit_hits * 5))
        
        return (success_score * success_weight + 
                speed_score * speed_weight + 
                stability_score * stability_weight)
    
    def _find_best_performer(self, summary: Dict[str, Any]) -> Optional[str]:
        """Find best performing exchange"""
        if not summary:
            return None
        
        best_exchange = None
        best_score = 0
        
        for exchange_name, metrics in summary.items():
            if metrics and metrics.get('reliability_score', 0) > best_score:
                best_score = metrics['reliability_score']
                best_exchange = exchange_name
        
        return best_exchange
    
    def _find_worst_performer(self, summary: Dict[str, Any]) -> Optional[str]:
        """Find worst performing exchange"""
        if not summary:
            return None
        
        worst_exchange = None
        worst_score = 100
        
        for exchange_name, metrics in summary.items():
            if metrics and metrics.get('reliability_score', 100) < worst_score:
                worst_score = metrics['reliability_score']
                worst_exchange = exchange_name
        
        return worst_exchange

# Global exchange logger instance
exchange_logger = ExchangeLogger()