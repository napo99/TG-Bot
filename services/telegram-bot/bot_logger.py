"""
Telegram Bot Service Logger
Provides specialized logging for telegram bot operations
"""

import time
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

from ..shared.structured_logger import (
    StructuredLogger, 
    TelegramInteractionData, 
    APIRequestData, 
    APIResponseData,
    ErrorContext,
    PerformanceMetric
)

class TelegramBotLogger(StructuredLogger):
    """Enhanced logger specifically for Telegram bot operations"""
    
    def __init__(self):
        super().__init__('telegram-bot', 'bot')
        self._command_start_times: Dict[str, float] = {}
    
    def log_command_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
        """Log the start of a command execution"""
        user = update.effective_user
        chat = update.effective_chat
        
        command_id = f"{user.id}_{command}_{time.time()}"
        self._command_start_times[command_id] = time.time()
        
        self.log_business_event('command_started', {
            'command': command,
            'user_id': str(user.id),
            'username': user.username,
            'first_name': user.first_name,
            'chat_id': str(chat.id),
            'chat_type': chat.type,
            'command_id': command_id,
            'message_text': update.message.text if update.message else '',
            'is_bot': user.is_bot
        })
        
        return command_id
    
    def log_command_complete(self, command_id: str, update: Update, 
                           response_text: str, success: bool = True, error: str = None):
        """Log the completion of a command execution"""
        start_time = self._command_start_times.get(command_id, time.time())
        response_time_ms = (time.time() - start_time) * 1000
        
        user = update.effective_user
        chat = update.effective_chat
        command = update.message.text.split()[0][1:] if update.message else 'unknown'
        
        interaction_data = TelegramInteractionData(
            user_id=str(user.id),
            username=user.username,
            command=command,
            chat_id=str(chat.id),
            chat_type=chat.type,
            message_text=update.message.text if update.message else '',
            success=success,
            response_time_ms=response_time_ms,
            error=error,
            response_length=len(response_text) if response_text else 0
        )
        
        self.log_telegram_command(interaction_data)
        
        # Log performance metric
        self.log_performance_metric(PerformanceMetric(
            metric_name='command_response_time',
            value=response_time_ms,
            unit='milliseconds',
            tags={
                'command': command,
                'success': str(success),
                'user_id': str(user.id)
            },
            timestamp=time.time(),
            memory_usage_mb=self._get_current_performance().get('memory_usage_mb', 0),
            cpu_percent=self._get_current_performance().get('cpu_percent', 0)
        ))
        
        # Clean up
        if command_id in self._command_start_times:
            del self._command_start_times[command_id]
    
    def log_market_data_request(self, endpoint: str, symbol: str, exchange: str = None, 
                               timeframe: str = None):
        """Log market data service request"""
        request_data = APIRequestData(
            endpoint=f"/market-data{endpoint}",
            method='POST',
            headers={'Content-Type': 'application/json'},
            payload={
                'symbol': symbol,
                'exchange': exchange,
                'timeframe': timeframe
            }
        )
        
        self.log_api_request(request_data)
    
    def log_market_data_response(self, endpoint: str, response_time_ms: float, 
                                success: bool, data_size: int = None, error: str = None):
        """Log market data service response"""
        response_data = APIResponseData(
            endpoint=f"/market-data{endpoint}",
            status_code=200 if success else 500,
            response_time_ms=response_time_ms,
            response_size_bytes=data_size or 0,
            error=error
        )
        
        self.log_api_response(response_data)
    
    def log_user_authorization_attempt(self, user_id: str, username: str = None, 
                                     authorized: bool = False, reason: str = None):
        """Log user authorization attempts"""
        self.log_security_event('user_authorization_attempt', {
            'user_id': str(user_id),
            'username': username,
            'authorized': authorized,
            'reason': reason,
            'timestamp': time.time()
        }, severity='INFO' if authorized else 'WARNING')
    
    def log_message_processing_error(self, update: Update, error: Exception, 
                                   command: str = None):
        """Log message processing errors"""
        user = update.effective_user
        chat = update.effective_chat
        
        context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=self._format_exception(error),
            context={
                'user_id': str(user.id),
                'username': user.username,
                'chat_id': str(chat.id),
                'chat_type': chat.type,
                'command': command,
                'message_text': update.message.text if update.message else '',
                'timestamp': time.time()
            },
            severity='ERROR',
            user_id=str(user.id)
        )
        
        self.log_error(error, context)
    
    def log_webhook_event(self, event_type: str, data: Dict[str, Any], 
                         processing_time_ms: float = None):
        """Log webhook events"""
        self.log_business_event('webhook_event', {
            'event_type': event_type,
            'data': data,
            'processing_time_ms': processing_time_ms,
            'timestamp': time.time()
        })
    
    def log_rate_limit_event(self, user_id: str, command: str, limit_type: str):
        """Log rate limiting events"""
        self.log_security_event('rate_limit_triggered', {
            'user_id': str(user_id),
            'command': command,
            'limit_type': limit_type,
            'timestamp': time.time()
        }, severity='WARNING')
    
    def log_formatting_operation(self, operation: str, input_size: int, 
                               output_size: int, processing_time_ms: float):
        """Log message formatting operations"""
        self.log_business_event('message_formatting', {
            'operation': operation,
            'input_size_bytes': input_size,
            'output_size_bytes': output_size,
            'processing_time_ms': processing_time_ms,
            'compression_ratio': output_size / input_size if input_size > 0 else 0
        })
    
    def _format_exception(self, error: Exception) -> str:
        """Format exception for logging"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

# Global bot logger instance
bot_logger = TelegramBotLogger()