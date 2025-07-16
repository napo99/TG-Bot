"""
Centralized Logging Configuration for Crypto Assistant System
Provides comprehensive, structured logging across all services
"""

import logging
import json
import sys
import os
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from pathlib import Path
import socket
import threading
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import time

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, service_name: str, module_name: str = None):
        super().__init__()
        self.service_name = service_name
        self.module_name = module_name
        self.hostname = socket.gethostname()
        self.git_commit = self._get_git_commit()
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.docker_container = os.getenv('HOSTNAME', 'local')
        
    def _get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except Exception:
            return 'unknown'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'service': self.service_name,
            'module': self.module_name or record.module,
            'level': record.levelname,
            'message': record.getMessage(),
            'logger_name': record.name,
            'file': record.filename,
            'line': record.lineno,
            'function': record.funcName,
            'thread_id': record.thread,
            'thread_name': record.threadName,
            'process_id': record.process,
            'hostname': self.hostname,
            'docker_container': self.docker_container,
            'git_commit': self.git_commit,
            'environment': self.environment
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_data'):
            log_entry['context'] = record.extra_data
        
        # Add performance metrics if present
        if hasattr(record, 'performance'):
            log_entry['performance'] = record.performance
        
        # Add API request/response data if present
        if hasattr(record, 'api_data'):
            log_entry['api'] = record.api_data
        
        # Add user interaction data if present
        if hasattr(record, 'user_data'):
            log_entry['user'] = record.user_data
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)

class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""
    
    def filter(self, record):
        if not hasattr(record, 'performance'):
            record.performance = {
                'timestamp': time.time(),
                'memory_usage_mb': self._get_memory_usage()
            }
        return True
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

class LoggingConfig:
    """Centralized logging configuration manager"""
    
    def __init__(self, service_name: str, log_level: str = None):
        self.service_name = service_name
        self.log_level = log_level or os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_dir = Path(os.getenv('LOG_DIR', '/app/logs'))
        self.max_file_size = int(os.getenv('LOG_MAX_FILE_SIZE', '50')) * 1024 * 1024  # 50MB default
        self.backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        self.enable_console = os.getenv('LOG_CONSOLE', 'true').lower() == 'true'
        self.enable_file = os.getenv('LOG_FILE', 'true').lower() == 'true'
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self, module_name: str = None) -> logging.Logger:
        """Setup logging for a specific module"""
        logger_name = f"{self.service_name}.{module_name}" if module_name else self.service_name
        logger = logging.getLogger(logger_name)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        logger.setLevel(getattr(logging, self.log_level))
        
        # JSON formatter
        formatter = JSONFormatter(self.service_name, module_name)
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(PerformanceFilter())
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.enable_file:
            log_file = self.log_dir / f"{self.service_name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(PerformanceFilter())
            logger.addHandler(file_handler)
        
        # Error file handler
        if self.enable_file:
            error_log_file = self.log_dir / f"{self.service_name}_errors.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            error_handler.addFilter(PerformanceFilter())
            logger.addHandler(error_handler)
        
        return logger
    
    def setup_uvicorn_logging(self):
        """Setup logging for uvicorn/fastapi"""
        # Configure uvicorn loggers to use our format
        for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error']:
            uvicorn_logger = logging.getLogger(logger_name)
            uvicorn_logger.handlers.clear()
            uvicorn_logger.propagate = True
        
        # Set uvicorn log level
        logging.getLogger('uvicorn').setLevel(getattr(logging, self.log_level))

# Global logging configuration instance
_logging_config: Optional[LoggingConfig] = None

def get_logging_config(service_name: str = None) -> LoggingConfig:
    """Get or create global logging configuration"""
    global _logging_config
    if _logging_config is None:
        if service_name is None:
            service_name = os.getenv('SERVICE_NAME', 'crypto-assistant')
        _logging_config = LoggingConfig(service_name)
    return _logging_config

def setup_service_logging(service_name: str, module_name: str = None) -> logging.Logger:
    """Setup logging for a service/module"""
    config = get_logging_config(service_name)
    return config.setup_logging(module_name)

# Convenience function for quick logger setup
def get_logger(service_name: str, module_name: str = None) -> logging.Logger:
    """Get a configured logger instance"""
    return setup_service_logging(service_name, module_name)