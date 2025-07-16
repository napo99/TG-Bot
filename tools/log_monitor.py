"""
Real-Time Log Monitor for Crypto Assistant
Provides real-time monitoring, alerting, and health checks
"""

import asyncio
import json
import time
import aiofiles
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
from collections import deque, defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import psutil
import threading
from dataclasses import dataclass, asdict
import queue
import os

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: str  # INFO, WARNING, ERROR, CRITICAL
    service: str
    module: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    resolved: bool = False
    acknowledged: bool = False

@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    window_minutes: int = 5

class RealTimeLogMonitor:
    """Real-time log monitoring and alerting system"""
    
    def __init__(self, log_directory: str = "/app/logs", config_file: str = None):
        self.log_directory = Path(log_directory)
        self.config = self._load_config(config_file)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.thresholds = self._setup_default_thresholds()
        self.webhook_urls = self.config.get('webhook_urls', [])
        self.email_config = self.config.get('email', {})
        self.running = False
        self.alert_callbacks: List[Callable] = []
        self._file_positions: Dict[str, int] = {}
        self._last_check_time = {}
        
    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "check_interval_seconds": 10,
            "alert_cooldown_minutes": 15,
            "max_alerts_per_hour": 20,
            "webhook_urls": [],
            "email": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "to_addresses": []
            },
            "log_files": ["*.log"],
            "exclude_patterns": ["DEBUG"],
            "custom_patterns": {}
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logging.error(f"Error loading config file: {e}")
        
        return default_config
    
    def _setup_default_thresholds(self) -> List[MetricThreshold]:
        """Setup default monitoring thresholds"""
        return [
            MetricThreshold("error_rate", 5.0, 10.0, "gt", 5),
            MetricThreshold("response_time_ms", 2000.0, 5000.0, "gt", 5),
            MetricThreshold("memory_usage_mb", 400.0, 800.0, "gt", 5),
            MetricThreshold("cpu_percent", 80.0, 95.0, "gt", 5),
            MetricThreshold("exchange_api_errors", 3.0, 10.0, "gt", 10),
            MetricThreshold("telegram_command_failures", 2.0, 5.0, "gt", 5),
            MetricThreshold("webhook_response_time", 3000.0, 10000.0, "gt", 3)
        ]
    
    async def start_monitoring(self):
        """Start the real-time monitoring system"""
        self.running = True
        logging.info("Starting real-time log monitor")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_log_files()),
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._process_alerts()),
            asyncio.create_task(self._check_service_health()),
            asyncio.create_task(self._cleanup_old_alerts())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logging.error(f"Error in monitoring tasks: {e}")
        finally:
            self.running = False
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        logging.info("Stopping real-time log monitor")
    
    async def _monitor_log_files(self):
        """Monitor log files for new entries"""
        while self.running:
            try:
                log_files = []
                for pattern in self.config['log_files']:
                    log_files.extend(self.log_directory.glob(pattern))
                
                for log_file in log_files:
                    await self._process_log_file(log_file)
                
                await asyncio.sleep(self.config['check_interval_seconds'])
                
            except Exception as e:
                logging.error(f"Error monitoring log files: {e}")
                await asyncio.sleep(5)
    
    async def _process_log_file(self, log_file: Path):
        """Process a single log file for new entries"""
        try:
            if not log_file.exists():
                return
            
            # Get current file position
            current_position = self._file_positions.get(str(log_file), 0)
            file_size = log_file.stat().st_size
            
            if file_size < current_position:
                # File was rotated or truncated
                current_position = 0
            
            if file_size == current_position:
                # No new content
                return
            
            # Read new content
            async with aiofiles.open(log_file, 'r') as f:
                await f.seek(current_position)
                new_content = await f.read()
                self._file_positions[str(log_file)] = await f.tell()
            
            # Process new log entries
            for line in new_content.strip().split('\n'):
                if line:
                    await self._analyze_log_entry(line, log_file.name)
                    
        except Exception as e:
            logging.error(f"Error processing log file {log_file}: {e}")
    
    async def _analyze_log_entry(self, log_line: str, source_file: str):
        """Analyze a single log entry for alerts"""
        try:
            log_entry = json.loads(log_line)
            
            # Check for error levels
            if log_entry.get('level') in ['ERROR', 'CRITICAL', 'FATAL']:
                await self._create_error_alert(log_entry, source_file)
            
            # Check for performance issues
            await self._check_performance_metrics(log_entry)
            
            # Check for specific patterns
            await self._check_custom_patterns(log_entry)
            
            # Update metrics buffer
            self._update_metrics_buffer(log_entry)
            
        except json.JSONDecodeError:
            # Handle non-JSON log entries
            if any(pattern in log_line for pattern in ['ERROR', 'CRITICAL', 'FATAL']):
                await self._create_text_error_alert(log_line, source_file)
        except Exception as e:
            logging.error(f"Error analyzing log entry: {e}")
    
    async def _create_error_alert(self, log_entry: Dict[str, Any], source_file: str):
        """Create alert for error log entries"""
        alert_id = f"error_{log_entry.get('service', 'unknown')}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            level=self._map_log_level_to_alert_level(log_entry.get('level', 'ERROR')),
            service=log_entry.get('service', 'unknown'),
            module=log_entry.get('module', 'unknown'),
            message=log_entry.get('message', 'Unknown error'),
            timestamp=datetime.fromisoformat(log_entry.get('timestamp', datetime.now().isoformat())),
            context={
                'source_file': source_file,
                'log_entry': log_entry,
                'error_type': log_entry.get('exception', {}).get('type', 'Unknown')
            }
        )
        
        await self._trigger_alert(alert)
    
    async def _check_performance_metrics(self, log_entry: Dict[str, Any]):
        """Check performance metrics against thresholds"""
        performance_data = log_entry.get('performance', {})
        
        if not performance_data:
            return
        
        for threshold in self.thresholds:
            metric_value = performance_data.get(threshold.metric_name.replace('_', ''), 
                                              performance_data.get(threshold.metric_name))
            
            if metric_value is not None:
                await self._check_threshold(threshold, metric_value, log_entry)
    
    async def _check_threshold(self, threshold: MetricThreshold, value: float, log_entry: Dict[str, Any]):
        """Check if a metric value exceeds threshold"""
        exceeded = False
        
        if threshold.comparison == 'gt' and value > threshold.critical_threshold:
            level = 'CRITICAL'
            exceeded = True
        elif threshold.comparison == 'gt' and value > threshold.warning_threshold:
            level = 'WARNING'
            exceeded = True
        elif threshold.comparison == 'lt' and value < threshold.critical_threshold:
            level = 'CRITICAL'
            exceeded = True
        elif threshold.comparison == 'lt' and value < threshold.warning_threshold:
            level = 'WARNING'
            exceeded = True
        
        if exceeded:
            alert_id = f"threshold_{threshold.metric_name}_{log_entry.get('service', 'unknown')}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                level=level,
                service=log_entry.get('service', 'unknown'),
                module=log_entry.get('module', 'unknown'),
                message=f"{threshold.metric_name} threshold exceeded: {value} > {threshold.warning_threshold if level == 'WARNING' else threshold.critical_threshold}",
                timestamp=datetime.now(),
                context={
                    'metric_name': threshold.metric_name,
                    'current_value': value,
                    'threshold': threshold.warning_threshold if level == 'WARNING' else threshold.critical_threshold,
                    'log_entry': log_entry
                }
            )
            
            await self._trigger_alert(alert)
    
    async def _monitor_system_metrics(self):
        """Monitor system-level metrics"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_usage_mb = memory.used / 1024 / 1024
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_usage_percent = disk.percent
                
                # Network stats
                network = psutil.net_io_counters()
                
                system_metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_usage_mb': memory_usage_mb,
                    'memory_percent': memory.percent,
                    'disk_usage_percent': disk_usage_percent,
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv
                }
                
                # Check system thresholds
                for threshold in self.thresholds:
                    if threshold.metric_name in system_metrics:
                        await self._check_system_threshold(threshold, system_metrics[threshold.metric_name])
                
                await asyncio.sleep(30)  # Check system metrics every 30 seconds
                
            except Exception as e:
                logging.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(30)
    
    async def _check_service_health(self):
        """Check service health via health endpoints"""
        health_endpoints = {
            'market-data': 'http://localhost:8001/health',
            'telegram-bot': 'http://localhost:8080/health'
        }
        
        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    for service, endpoint in health_endpoints.items():
                        try:
                            start_time = time.time()
                            async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                                response_time = (time.time() - start_time) * 1000
                                
                                if response.status != 200:
                                    await self._create_service_down_alert(service, response.status)
                                elif response_time > 5000:  # 5 second threshold
                                    await self._create_slow_response_alert(service, response_time)
                                    
                        except asyncio.TimeoutError:
                            await self._create_service_timeout_alert(service)
                        except Exception as e:
                            await self._create_service_error_alert(service, str(e))
                
                await asyncio.sleep(60)  # Check health every minute
                
            except Exception as e:
                logging.error(f"Error checking service health: {e}")
                await asyncio.sleep(60)
    
    async def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        # Check alert cooldown
        if self._is_alert_on_cooldown(alert):
            return
        
        # Check rate limiting
        if self._is_rate_limited():
            return
        
        # Add to active alerts
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Log the alert
        logging.warning(f"ALERT [{alert.level}] {alert.service}.{alert.module}: {alert.message}")
        
        # Send notifications
        await self._send_alert_notifications(alert)
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logging.error(f"Error in alert callback: {e}")
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications via configured channels"""
        # Send to webhooks
        for webhook_url in self.webhook_urls:
            await self._send_webhook_notification(webhook_url, alert)
        
        # Send email if configured
        if self.email_config.get('enabled', False):
            await self._send_email_notification(alert)
    
    async def _send_webhook_notification(self, webhook_url: str, alert: Alert):
        """Send alert to webhook"""
        try:
            payload = {
                'alert_id': alert.id,
                'level': alert.level,
                'service': alert.service,
                'module': alert.module,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'context': alert.context
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logging.error(f"Failed to send webhook notification: {response.status}")
                        
        except Exception as e:
            logging.error(f"Error sending webhook notification: {e}")
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logging.info(f"Alert {alert_id} acknowledged")
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            del self.active_alerts[alert_id]
            logging.info(f"Alert {alert_id} resolved")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        now = datetime.now()
        active_criticals = [a for a in self.active_alerts.values() if a.level == 'CRITICAL']
        active_warnings = [a for a in self.active_alerts.values() if a.level == 'WARNING']
        
        # Calculate recent alert rate
        recent_alerts = [a for a in self.alert_history if now - a.timestamp < timedelta(hours=1)]
        
        return {
            'timestamp': now.isoformat(),
            'status': 'CRITICAL' if active_criticals else 'WARNING' if active_warnings else 'OK',
            'active_alerts_count': len(self.active_alerts),
            'critical_alerts_count': len(active_criticals),
            'warning_alerts_count': len(active_warnings),
            'recent_alerts_per_hour': len(recent_alerts),
            'monitoring_active': self.running,
            'services_monitored': list(set(a.service for a in self.alert_history[-10:]))
        }
    
    def _is_alert_on_cooldown(self, alert: Alert) -> bool:
        """Check if alert is on cooldown"""
        cooldown_minutes = self.config.get('alert_cooldown_minutes', 15)
        cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)
        
        # Check for similar recent alerts
        for historical_alert in reversed(self.alert_history):
            if historical_alert.timestamp < cutoff_time:
                break
            if (historical_alert.service == alert.service and 
                historical_alert.module == alert.module and
                historical_alert.message == alert.message):
                return True
        
        return False
    
    def _is_rate_limited(self) -> bool:
        """Check if alert rate limit is exceeded"""
        max_alerts = self.config.get('max_alerts_per_hour', 20)
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        recent_alerts = [a for a in self.alert_history if a.timestamp > cutoff_time]
        return len(recent_alerts) >= max_alerts
    
    def _map_log_level_to_alert_level(self, log_level: str) -> str:
        """Map log level to alert level"""
        mapping = {
            'CRITICAL': 'CRITICAL',
            'FATAL': 'CRITICAL',
            'ERROR': 'WARNING',
            'WARNING': 'INFO',
            'WARN': 'INFO'
        }
        return mapping.get(log_level, 'INFO')
    
    def _update_metrics_buffer(self, log_entry: Dict[str, Any]):
        """Update metrics buffer with new data"""
        timestamp = datetime.now()
        
        # Extract metrics from log entry
        if 'performance' in log_entry:
            perf_data = log_entry['performance']
            for metric_name, value in perf_data.items():
                self.metrics_buffer[metric_name].append((timestamp, value))
        
        # Clean old entries (keep last hour)
        cutoff_time = timestamp - timedelta(hours=1)
        for metric_name in self.metrics_buffer:
            while (self.metrics_buffer[metric_name] and 
                   self.metrics_buffer[metric_name][0][0] < cutoff_time):
                self.metrics_buffer[metric_name].popleft()

async def main():
    """Main function for running the monitor"""
    monitor = RealTimeLogMonitor()
    
    # Register sample alert callback
    async def alert_callback(alert: Alert):
        print(f"ALERT: [{alert.level}] {alert.service} - {alert.message}")
    
    monitor.register_alert_callback(alert_callback)
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())