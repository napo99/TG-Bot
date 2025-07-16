"""
Market Data Service Logger
Provides specialized logging for market data operations
"""

import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from ..shared.structured_logger import (
    StructuredLogger,
    ExchangeAPIData,
    APIRequestData,
    APIResponseData,
    ErrorContext,
    PerformanceMetric
)

class MarketDataLogger(StructuredLogger):
    """Enhanced logger specifically for market data service operations"""
    
    def __init__(self):
        super().__init__('market-data', 'api')
        self._operation_timers: Dict[str, float] = {}
    
    def log_exchange_connection(self, exchange: str, success: bool, 
                              connection_time_ms: float = None, error: str = None):
        """Log exchange connection attempts"""
        self.log_business_event('exchange_connection', {
            'exchange': exchange,
            'success': success,
            'connection_time_ms': connection_time_ms,
            'error': error,
            'timestamp': time.time()
        })
    
    def log_symbol_harmonization(self, original_symbol: str, exchange: str, 
                               harmonized_symbol: str, market_type: str):
        """Log symbol harmonization process"""
        self.log_business_event('symbol_harmonization', {
            'original_symbol': original_symbol,
            'exchange': exchange,
            'harmonized_symbol': harmonized_symbol,
            'market_type': market_type,
            'timestamp': time.time()
        })
    
    def log_price_data_fetch(self, symbol: str, exchange: str, market_type: str,
                           success: bool, response_time_ms: float, data_points: int = None,
                           error: str = None):
        """Log price data fetching operations"""
        api_data = ExchangeAPIData(
            exchange=exchange,
            endpoint=f'ticker/{market_type}',
            method='GET',
            symbol=symbol,
            success=success,
            response_time_ms=response_time_ms,
            error=error,
            response_size=data_points
        )
        
        self.log_exchange_api_call(api_data)
        
        # Log business metrics
        self.log_business_event('price_data_fetch', {
            'symbol': symbol,
            'exchange': exchange,
            'market_type': market_type,
            'data_points': data_points,
            'cache_status': 'miss'  # TODO: Add cache hit/miss tracking
        })
    
    def log_oi_aggregation(self, symbol: str, exchanges: List[str], 
                          total_oi_usd: float, processing_time_ms: float,
                          success: bool, errors: List[str] = None):
        """Log open interest aggregation operations"""
        self.log_business_event('oi_aggregation', {
            'symbol': symbol,
            'exchanges_count': len(exchanges),
            'exchanges': exchanges,
            'total_oi_usd': total_oi_usd,
            'processing_time_ms': processing_time_ms,
            'success': success,
            'errors': errors or [],
            'oi_per_exchange': total_oi_usd / len(exchanges) if exchanges else 0
        })
        
        # Performance metric
        self.log_performance_metric(PerformanceMetric(
            metric_name='oi_aggregation_time',
            value=processing_time_ms,
            unit='milliseconds',
            tags={
                'symbol': symbol,
                'exchanges_count': str(len(exchanges)),
                'success': str(success)
            },
            timestamp=time.time(),
            memory_usage_mb=self._get_current_performance().get('memory_usage_mb', 0),
            cpu_percent=self._get_current_performance().get('cpu_percent', 0)
        ))
    
    def log_volume_analysis(self, symbol: str, timeframe: str, volume_spike: str,
                           cvd_trend: str, analysis_time_ms: float):
        """Log volume analysis operations"""
        self.log_business_event('volume_analysis', {
            'symbol': symbol,
            'timeframe': timeframe,
            'volume_spike': volume_spike,
            'cvd_trend': cvd_trend,
            'analysis_time_ms': analysis_time_ms,
            'timestamp': time.time()
        })
    
    def log_technical_indicators(self, symbol: str, indicators: Dict[str, Any],
                               calculation_time_ms: float):
        """Log technical indicator calculations"""
        self.log_business_event('technical_indicators', {
            'symbol': symbol,
            'indicators': indicators,
            'calculation_time_ms': calculation_time_ms,
            'indicator_count': len(indicators),
            'timestamp': time.time()
        })
    
    def log_long_short_data_fetch(self, symbol: str, exchange: str,
                                 institutional_ratio: float, retail_ratio: float,
                                 fetch_time_ms: float, success: bool, error: str = None):
        """Log long/short ratio data fetching"""
        api_data = ExchangeAPIData(
            exchange=exchange,
            endpoint='long_short_ratio',
            method='GET',
            symbol=symbol,
            success=success,
            response_time_ms=fetch_time_ms,
            error=error
        )
        
        self.log_exchange_api_call(api_data)
        
        self.log_business_event('long_short_data_fetch', {
            'symbol': symbol,
            'exchange': exchange,
            'institutional_ratio': institutional_ratio,
            'retail_ratio': retail_ratio,
            'data_quality': 'high' if success and institutional_ratio > 0 else 'low'
        })
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None,
                           size_bytes: int = None, ttl_seconds: int = None,
                           eviction_reason: str = None):
        """Log cache operations with enhanced context"""
        super().log_cache_operation(operation, key, hit, size_bytes, ttl_seconds)
        
        if operation == 'eviction':
            self.log_business_event('cache_eviction', {
                'key': key,
                'reason': eviction_reason,
                'size_bytes': size_bytes,
                'timestamp': time.time()
            })
    
    def log_api_rate_limit(self, exchange: str, endpoint: str, remaining: int,
                          reset_time: int, retry_after: int = None):
        """Log API rate limiting information"""
        self.log_business_event('api_rate_limit', {
            'exchange': exchange,
            'endpoint': endpoint,
            'remaining_requests': remaining,
            'reset_time': reset_time,
            'retry_after_seconds': retry_after,
            'utilization_pct': ((1000 - remaining) / 1000) * 100 if remaining < 1000 else 0
        })
        
        if remaining < 100:  # Low remaining requests
            self.log_security_event('rate_limit_warning', {
                'exchange': exchange,
                'endpoint': endpoint,
                'remaining': remaining,
                'action': 'throttling_recommended'
            }, severity='WARNING')
    
    def log_data_validation_error(self, data_type: str, symbol: str, exchange: str,
                                 validation_error: str, raw_data: Any = None):
        """Log data validation errors"""
        error_context = ErrorContext(
            error_type='DataValidationError',
            error_message=validation_error,
            stack_trace='',
            context={
                'data_type': data_type,
                'symbol': symbol,
                'exchange': exchange,
                'raw_data_sample': str(raw_data)[:500] if raw_data else None,
                'timestamp': time.time()
            },
            severity='WARNING',
            related_symbols=[symbol]
        )
        
        self.log_error(Exception(validation_error), error_context)
    
    def log_exchange_outage(self, exchange: str, endpoints_affected: List[str],
                           outage_duration_seconds: float = None, 
                           recovery_time: float = None):
        """Log exchange outages and recovery"""
        self.log_business_event('exchange_outage', {
            'exchange': exchange,
            'endpoints_affected': endpoints_affected,
            'outage_duration_seconds': outage_duration_seconds,
            'recovery_time': recovery_time,
            'severity': 'critical' if len(endpoints_affected) > 3 else 'moderate',
            'timestamp': time.time()
        })
    
    def log_comprehensive_analysis(self, symbol: str, analysis_components: List[str],
                                  total_time_ms: float, success: bool,
                                  data_sources: Dict[str, bool]):
        """Log comprehensive analysis operations"""
        self.log_business_event('comprehensive_analysis', {
            'symbol': symbol,
            'components': analysis_components,
            'component_count': len(analysis_components),
            'total_time_ms': total_time_ms,
            'success': success,
            'data_sources': data_sources,
            'data_source_success_rate': sum(data_sources.values()) / len(data_sources) if data_sources else 0,
            'timestamp': time.time()
        })
        
        # Performance tracking
        self.log_performance_metric(PerformanceMetric(
            metric_name='comprehensive_analysis_time',
            value=total_time_ms,
            unit='milliseconds',
            tags={
                'symbol': symbol,
                'components': str(len(analysis_components)),
                'success': str(success)
            },
            timestamp=time.time(),
            memory_usage_mb=self._get_current_performance().get('memory_usage_mb', 0),
            cpu_percent=self._get_current_performance().get('cpu_percent', 0)
        ))
    
    def log_websocket_event(self, exchange: str, event_type: str, symbol: str = None,
                           data_size: int = None, processing_time_ms: float = None):
        """Log WebSocket events"""
        self.log_business_event('websocket_event', {
            'exchange': exchange,
            'event_type': event_type,
            'symbol': symbol,
            'data_size_bytes': data_size,
            'processing_time_ms': processing_time_ms,
            'timestamp': time.time()
        })

# Global market data logger instance  
market_logger = MarketDataLogger()