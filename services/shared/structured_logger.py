"""
Structured Logger Implementation for Crypto Assistant
Provides specialized logging methods for different types of events
"""

import logging
import time
import json
import traceback
import psutil
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from .logging_config import get_logger

@dataclass
class APIRequestData:
    """Data structure for API request logging"""
    endpoint: str
    method: str
    headers: Dict[str, str]
    payload: Dict[str, Any]
    user_agent: Optional[str] = None
    client_ip: Optional[str] = None
    request_id: Optional[str] = None

@dataclass
class APIResponseData:
    """Data structure for API response logging"""
    endpoint: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

@dataclass
class TelegramInteractionData:
    """Data structure for Telegram bot interaction logging"""
    user_id: str
    username: Optional[str]
    command: str
    chat_id: str
    chat_type: str
    message_text: str
    success: bool
    response_time_ms: float
    error: Optional[str] = None
    response_length: Optional[int] = None

@dataclass
class ExchangeAPIData:
    """Data structure for exchange API call logging"""
    exchange: str
    endpoint: str
    method: str
    symbol: Optional[str]
    success: bool
    response_time_ms: float
    error: Optional[str] = None
    response_size: Optional[int] = None
    rate_limit_remaining: Optional[int] = None

@dataclass
class PerformanceMetric:
    """Data structure for performance metrics"""
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]
    timestamp: float
    memory_usage_mb: float
    cpu_percent: float

@dataclass
class ErrorContext:
    """Data structure for error context"""
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    severity: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    related_symbols: Optional[List[str]] = None

class StructuredLogger:
    """Enhanced structured logger with specialized methods"""
    
    def __init__(self, service_name: str, module_name: str):
        self.service_name = service_name
        self.module_name = module_name
        self.logger = get_logger(service_name, module_name)
        self._start_times: Dict[str, float] = {}
        
    def _get_current_performance(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            process = psutil.Process()
            return {
                'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'thread_count': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
        except Exception:
            return {'memory_usage_mb': 0, 'cpu_percent': 0}
    
    def _add_extra_data(self, data: Any) -> Dict[str, Any]:
        """Add extra data to log record"""
        extra = {'extra_data': data}
        extra['performance'] = self._get_current_performance()
        return extra
    
    def log_api_request(self, request_data: APIRequestData):
        """Log API request details"""
        self.logger.info(
            f"API Request: {request_data.method} {request_data.endpoint}",
            extra=self._add_extra_data({
                'api_data': asdict(request_data),
                'event_type': 'api_request'
            })
        )
    
    def log_api_response(self, response_data: APIResponseData):
        """Log API response details"""
        level = logging.ERROR if response_data.status_code >= 400 else logging.INFO
        self.logger.log(
            level,
            f"API Response: {response_data.endpoint} - {response_data.status_code} - {response_data.response_time_ms:.2f}ms",
            extra=self._add_extra_data({
                'api_data': asdict(response_data),
                'event_type': 'api_response'
            })
        )
    
    def log_telegram_command(self, interaction_data: TelegramInteractionData):
        """Log Telegram bot command interaction"""
        level = logging.ERROR if not interaction_data.success else logging.INFO
        self.logger.log(
            level,
            f"Telegram Command: {interaction_data.command} from user {interaction_data.user_id}",
            extra=self._add_extra_data({
                'user_data': asdict(interaction_data),
                'event_type': 'telegram_interaction'
            })
        )
    
    def log_exchange_api_call(self, api_data: ExchangeAPIData):
        """Log external exchange API call"""
        level = logging.ERROR if not api_data.success else logging.INFO
        self.logger.log(
            level,
            f"Exchange API: {api_data.exchange} {api_data.endpoint} - {api_data.response_time_ms:.2f}ms",
            extra=self._add_extra_data({
                'exchange_data': asdict(api_data),
                'event_type': 'exchange_api_call'
            })
        )
    
    def log_error(self, error: Exception, context: ErrorContext):
        """Log error with comprehensive context"""
        self.logger.error(
            f"Error in {self.module_name}: {context.error_message}",
            extra=self._add_extra_data({
                'error_data': asdict(context),
                'event_type': 'error'
            }),
            exc_info=error
        )
    
    def log_performance_metric(self, metric: PerformanceMetric):
        """Log performance metric"""
        self.logger.info(
            f"Performance Metric: {metric.metric_name} = {metric.value} {metric.unit}",
            extra=self._add_extra_data({
                'performance_metric': asdict(metric),
                'event_type': 'performance_metric'
            })
        )
    
    def log_business_event(self, event_name: str, event_data: Dict[str, Any]):
        """Log business logic event"""
        self.logger.info(
            f"Business Event: {event_name}",
            extra=self._add_extra_data({
                'business_event': {
                    'event_name': event_name,
                    'event_data': event_data
                },
                'event_type': 'business_event'
            })
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "WARNING"):
        """Log security-related event"""
        level = getattr(logging, severity.upper(), logging.WARNING)
        self.logger.log(
            level,
            f"Security Event: {event_type}",
            extra=self._add_extra_data({
                'security_event': {
                    'event_type': event_type,
                    'details': details,
                    'severity': severity
                },
                'event_type': 'security_event'
            })
        )
    
    @contextmanager
    def time_operation(self, operation_name: str, context: Dict[str, Any] = None):
        """Context manager to time operations"""
        start_time = time.time()
        operation_id = f"{operation_name}_{start_time}"
        
        try:
            self.logger.info(
                f"Starting operation: {operation_name}",
                extra=self._add_extra_data({
                    'operation': {
                        'name': operation_name,
                        'operation_id': operation_id,
                        'context': context or {},
                        'status': 'started'
                    },
                    'event_type': 'operation_start'
                })
            )
            yield
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"Completed operation: {operation_name} in {duration_ms:.2f}ms",
                extra=self._add_extra_data({
                    'operation': {
                        'name': operation_name,
                        'operation_id': operation_id,
                        'duration_ms': duration_ms,
                        'context': context or {},
                        'status': 'completed'
                    },
                    'event_type': 'operation_complete'
                })
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Failed operation: {operation_name} after {duration_ms:.2f}ms",
                extra=self._add_extra_data({
                    'operation': {
                        'name': operation_name,
                        'operation_id': operation_id,
                        'duration_ms': duration_ms,
                        'context': context or {},
                        'status': 'failed',
                        'error': str(e)
                    },
                    'event_type': 'operation_failed'
                }),
                exc_info=e
            )
            raise
    
    def log_data_flow(self, flow_name: str, source: str, destination: str, 
                      data_type: str, record_count: int, size_bytes: int):
        """Log data flow events"""
        self.logger.info(
            f"Data Flow: {flow_name} - {record_count} {data_type} records ({size_bytes} bytes) from {source} to {destination}",
            extra=self._add_extra_data({
                'data_flow': {
                    'flow_name': flow_name,
                    'source': source,
                    'destination': destination,
                    'data_type': data_type,
                    'record_count': record_count,
                    'size_bytes': size_bytes
                },
                'event_type': 'data_flow'
            })
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, 
                           size_bytes: int = None, ttl_seconds: int = None):
        """Log cache operations"""
        self.logger.debug(
            f"Cache {operation}: {key}",
            extra=self._add_extra_data({
                'cache_operation': {
                    'operation': operation,
                    'key': key,
                    'hit': hit,
                    'size_bytes': size_bytes,
                    'ttl_seconds': ttl_seconds
                },
                'event_type': 'cache_operation'
            })
        )
    
    def log_configuration_change(self, setting: str, old_value: Any, new_value: Any, 
                                user: str = None):
        """Log configuration changes"""
        self.logger.warning(
            f"Configuration changed: {setting} = {new_value} (was: {old_value})",
            extra=self._add_extra_data({
                'configuration_change': {
                    'setting': setting,
                    'old_value': old_value,
                    'new_value': new_value,
                    'changed_by': user
                },
                'event_type': 'configuration_change'
            })
        )

# Factory function for easy logger creation
def create_structured_logger(service_name: str, module_name: str) -> StructuredLogger:
    """Create a structured logger instance"""
    return StructuredLogger(service_name, module_name)