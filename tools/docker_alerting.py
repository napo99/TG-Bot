#!/usr/bin/env python3
"""
Docker Alerting System - Automated alerting for Docker container issues
Provides threshold-based alerts, notifications, and comprehensive health summaries.
"""

import asyncio
import aiohttp
import json
import logging
import smtplib
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import time

from docker_monitor import DockerMonitor, ContainerMetrics
from container_health import ContainerHealthChecker
from resource_analyzer import ResourceAnalyzer

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    alert_type: str  # memory, cpu, container_down, restart_loop, health_check_failed
    severity: str    # low, medium, high, critical
    service_name: str
    message: str
    details: Dict[str, Any]
    timestamp: str
    resolved: bool = False
    resolved_timestamp: Optional[str] = None
    notification_sent: bool = False

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    name: str
    condition: str
    threshold: float
    severity: str
    cooldown_minutes: int
    enabled: bool = True

@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    channel_type: str  # file, webhook, email, slack
    enabled: bool
    configuration: Dict[str, Any]

class DockerAlerting:
    """Automated alerting system for Docker container issues"""
    
    def __init__(self, config_file: str = None, log_dir: str = "/Users/screener-m3/projects/crypto-assistant/data/logs"):
        """Initialize alerting system"""
        self.log_dir = log_dir
        self.alerts_dir = os.path.join(os.path.dirname(log_dir), "alerts")
        os.makedirs(self.alerts_dir, exist_ok=True)
        
        self.setup_logging()
        
        # Initialize monitoring components
        self.docker_monitor = DockerMonitor(log_dir)
        self.health_checker = ContainerHealthChecker(log_dir)
        self.resource_analyzer = ResourceAnalyzer(log_dir)
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history_size = 1000
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Alert rules
        self.alert_rules = self._setup_default_alert_rules()
        
        # Notification channels
        self.notification_channels = self._setup_notification_channels()
        
        # Cooldown tracking (prevent spam)
        self.last_alert_times: Dict[str, datetime] = {}
        
        self.logger.info("Docker Alerting System initialized")

    def setup_logging(self):
        """Setup logging system"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, "docker_alerting.log")
        
        self.logger = logging.getLogger('docker_alerting')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'monitoring_interval': 30,
            'alert_retention_days': 30,
            'max_alerts_per_hour': 10,
            'enable_email_notifications': False,
            'enable_webhook_notifications': False,
            'enable_file_notifications': True
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.error(f"Error loading config file {config_file}: {e}")
        
        return default_config

    def _setup_default_alert_rules(self) -> List[AlertRule]:
        """Setup default alert rules optimized for AWS t3.micro"""
        return [
            AlertRule(
                rule_id="memory_warning",
                name="Memory Usage Warning",
                condition="memory_percent > threshold",
                threshold=70.0,
                severity="medium",
                cooldown_minutes=15
            ),
            AlertRule(
                rule_id="memory_critical",
                name="Memory Usage Critical",
                condition="memory_percent > threshold",
                threshold=85.0,
                severity="critical",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="cpu_warning",
                name="CPU Usage Warning",
                condition="cpu_percent > threshold",
                threshold=80.0,
                severity="medium",
                cooldown_minutes=10
            ),
            AlertRule(
                rule_id="cpu_critical",
                name="CPU Usage Critical",
                condition="cpu_percent > threshold",
                threshold=95.0,
                severity="critical",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="container_restart_loop",
                name="Container Restart Loop",
                condition="restart_count > threshold",
                threshold=3.0,
                severity="high",
                cooldown_minutes=30
            ),
            AlertRule(
                rule_id="container_down",
                name="Container Down",
                condition="status != running",
                threshold=0.0,
                severity="critical",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="health_check_failed",
                name="Health Check Failed",
                condition="health_status != healthy",
                threshold=0.0,
                severity="high",
                cooldown_minutes=10
            ),
            AlertRule(
                rule_id="system_memory_pressure",
                name="System Memory Pressure",
                condition="system_memory_percent > threshold",
                threshold=85.0,
                severity="critical",
                cooldown_minutes=15
            ),
            AlertRule(
                rule_id="response_time_slow",
                name="Slow Response Time",
                condition="response_time_ms > threshold",
                threshold=5000.0,
                severity="medium",
                cooldown_minutes=20
            )
        ]

    def _setup_notification_channels(self) -> List[NotificationChannel]:
        """Setup notification channels"""
        channels = []
        
        # File notification (always enabled)
        channels.append(NotificationChannel(
            channel_type="file",
            enabled=True,
            configuration={
                "alert_file": os.path.join(self.alerts_dir, "active_alerts.json"),
                "history_file": os.path.join(self.alerts_dir, "alert_history.json")
            }
        ))
        
        # Webhook notification (if configured)
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if webhook_url:
            channels.append(NotificationChannel(
                channel_type="webhook",
                enabled=True,
                configuration={
                    "url": webhook_url,
                    "timeout": 10,
                    "retry_count": 3
                }
            ))
        
        # Email notification (if configured)
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        alert_emails = os.getenv('ALERT_EMAILS', '').split(',')
        
        if smtp_server and smtp_user and smtp_password and alert_emails[0]:
            channels.append(NotificationChannel(
                channel_type="email",
                enabled=True,
                configuration={
                    "smtp_server": smtp_server,
                    "smtp_port": int(os.getenv('SMTP_PORT', '587')),
                    "smtp_user": smtp_user,
                    "smtp_password": smtp_password,
                    "from_email": smtp_user,
                    "to_emails": [email.strip() for email in alert_emails if email.strip()],
                    "use_tls": True
                }
            ))
        
        # Slack notification (if configured)
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            channels.append(NotificationChannel(
                channel_type="slack",
                enabled=True,
                configuration={
                    "webhook_url": slack_webhook,
                    "channel": os.getenv('SLACK_CHANNEL', '#alerts'),
                    "username": "Docker Monitor",
                    "icon_emoji": ":warning:"
                }
            ))
        
        return channels

    def _generate_alert_id(self, alert_type: str, service_name: str) -> str:
        """Generate unique alert ID"""
        timestamp = int(time.time())
        return f"{alert_type}_{service_name}_{timestamp}"

    def _check_cooldown(self, rule_id: str, service_name: str) -> bool:
        """Check if alert is in cooldown period"""
        key = f"{rule_id}_{service_name}"
        
        if key not in self.last_alert_times:
            return True
        
        rule = next((r for r in self.alert_rules if r.rule_id == rule_id), None)
        if not rule:
            return True
        
        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        time_since_last = datetime.now() - self.last_alert_times[key]
        
        return time_since_last >= cooldown_period

    async def check_alert_conditions(self, metrics: List[ContainerMetrics]):
        """Check all containers against alert thresholds"""
        try:
            new_alerts = []
            
            # Get system metrics for system-wide alerts
            system_memory = None
            try:
                import psutil
                memory = psutil.virtual_memory()
                system_memory = memory.percent
            except:
                pass
            
            for metric in metrics:
                service_name = metric.name
                
                # Check each alert rule
                for rule in self.alert_rules:
                    if not rule.enabled:
                        continue
                    
                    alert_triggered = False
                    alert_details = {}
                    
                    # Evaluate rule conditions
                    if rule.rule_id == "memory_warning" and metric.memory_percent > rule.threshold:
                        alert_triggered = True
                        alert_details = {
                            "current_memory_percent": metric.memory_percent,
                            "threshold": rule.threshold,
                            "memory_usage_mb": metric.memory_usage_mb
                        }
                    
                    elif rule.rule_id == "memory_critical" and metric.memory_percent > rule.threshold:
                        alert_triggered = True
                        alert_details = {
                            "current_memory_percent": metric.memory_percent,
                            "threshold": rule.threshold,
                            "memory_usage_mb": metric.memory_usage_mb
                        }
                    
                    elif rule.rule_id == "cpu_warning" and metric.cpu_percent > rule.threshold:
                        alert_triggered = True
                        alert_details = {
                            "current_cpu_percent": metric.cpu_percent,
                            "threshold": rule.threshold
                        }
                    
                    elif rule.rule_id == "cpu_critical" and metric.cpu_percent > rule.threshold:
                        alert_triggered = True
                        alert_details = {
                            "current_cpu_percent": metric.cpu_percent,
                            "threshold": rule.threshold
                        }
                    
                    elif rule.rule_id == "container_restart_loop" and metric.restart_count > rule.threshold:
                        alert_triggered = True
                        alert_details = {
                            "restart_count": metric.restart_count,
                            "threshold": rule.threshold,
                            "uptime_seconds": metric.uptime_seconds
                        }
                    
                    elif rule.rule_id == "container_down" and metric.status != "running":
                        alert_triggered = True
                        alert_details = {
                            "current_status": metric.status,
                            "expected_status": "running"
                        }
                    
                    elif rule.rule_id == "health_check_failed" and metric.health_status != "healthy":
                        alert_triggered = True
                        alert_details = {
                            "health_status": metric.health_status,
                            "expected_status": "healthy"
                        }
                    
                    # System-wide alerts
                    elif rule.rule_id == "system_memory_pressure" and system_memory and system_memory > rule.threshold:
                        alert_triggered = True
                        alert_details = {
                            "system_memory_percent": system_memory,
                            "threshold": rule.threshold
                        }
                        service_name = "system"  # Override for system-wide alerts
                    
                    # Create alert if triggered and not in cooldown
                    if alert_triggered and self._check_cooldown(rule.rule_id, service_name):
                        alert = Alert(
                            alert_id=self._generate_alert_id(rule.rule_id, service_name),
                            alert_type=rule.rule_id,
                            severity=rule.severity,
                            service_name=service_name,
                            message=f"{rule.name}: {service_name}",
                            details=alert_details,
                            timestamp=datetime.now().isoformat()
                        )
                        
                        new_alerts.append(alert)
                        self.active_alerts[alert.alert_id] = alert
                        self.last_alert_times[f"{rule.rule_id}_{service_name}"] = datetime.now()
                        
                        self.logger.warning(f"Alert triggered: {alert.message}")
            
            # Send notifications for new alerts
            for alert in new_alerts:
                await self._send_alert_notifications(alert)
            
            # Check for resolved alerts
            await self._check_resolved_alerts(metrics)
            
            return new_alerts
            
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
            return []

    async def _check_resolved_alerts(self, current_metrics: List[ContainerMetrics]):
        """Check if any active alerts have been resolved"""
        resolved_alerts = []
        
        try:
            for alert_id, alert in list(self.active_alerts.items()):
                if alert.resolved:
                    continue
                
                # Find corresponding metric
                metric = next((m for m in current_metrics if m.name == alert.service_name), None)
                
                # Check if alert condition is resolved
                resolved = False
                
                if alert.alert_type == "memory_warning" or alert.alert_type == "memory_critical":
                    threshold = alert.details.get("threshold", 0)
                    resolved = metric and metric.memory_percent <= threshold * 0.95  # 5% hysteresis
                
                elif alert.alert_type == "cpu_warning" or alert.alert_type == "cpu_critical":
                    threshold = alert.details.get("threshold", 0)
                    resolved = metric and metric.cpu_percent <= threshold * 0.95
                
                elif alert.alert_type == "container_down":
                    resolved = metric and metric.status == "running"
                
                elif alert.alert_type == "health_check_failed":
                    resolved = metric and metric.health_status == "healthy"
                
                if resolved:
                    alert.resolved = True
                    alert.resolved_timestamp = datetime.now().isoformat()
                    resolved_alerts.append(alert)
                    
                    self.logger.info(f"Alert resolved: {alert.message}")
                    
                    # Move to history
                    self.alert_history.append(alert)
                    del self.active_alerts[alert_id]
            
            # Send resolution notifications
            for alert in resolved_alerts:
                await self._send_resolution_notifications(alert)
                
            return resolved_alerts
            
        except Exception as e:
            self.logger.error(f"Error checking resolved alerts: {e}")
            return []

    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through all enabled channels"""
        try:
            for channel in self.notification_channels:
                if not channel.enabled:
                    continue
                
                try:
                    if channel.channel_type == "file":
                        await self._send_file_notification(alert, channel)
                    elif channel.channel_type == "webhook":
                        await self._send_webhook_notification(alert, channel)
                    elif channel.channel_type == "email":
                        await self._send_email_notification(alert, channel)
                    elif channel.channel_type == "slack":
                        await self._send_slack_notification(alert, channel)
                    
                except Exception as e:
                    self.logger.error(f"Error sending {channel.channel_type} notification: {e}")
            
            alert.notification_sent = True
            
        except Exception as e:
            self.logger.error(f"Error sending alert notifications: {e}")

    async def _send_file_notification(self, alert: Alert, channel: NotificationChannel):
        """Send alert to file"""
        try:
            alert_file = channel.configuration["alert_file"]
            
            # Update active alerts file
            active_alerts_data = {alert_id: asdict(alert) for alert_id, alert in self.active_alerts.items()}
            
            with open(alert_file, 'w') as f:
                json.dump(active_alerts_data, f, indent=2)
            
            # Append to history file
            history_file = channel.configuration["history_file"]
            history_entry = {
                "timestamp": alert.timestamp,
                "alert": asdict(alert)
            }
            
            # Read existing history
            history_data = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        history_data = json.load(f)
                except:
                    history_data = []
            
            history_data.append(history_entry)
            
            # Keep only recent history
            cutoff_time = datetime.now() - timedelta(days=self.config['alert_retention_days'])
            history_data = [
                entry for entry in history_data
                if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
            ]
            
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error sending file notification: {e}")

    async def _send_webhook_notification(self, alert: Alert, channel: NotificationChannel):
        """Send alert via webhook"""
        try:
            url = channel.configuration["url"]
            timeout = channel.configuration.get("timeout", 10)
            
            payload = {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "service_name": alert.service_name,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=timeout) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook notification sent successfully")
                    else:
                        self.logger.error(f"Webhook notification failed: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")

    async def _send_email_notification(self, alert: Alert, channel: NotificationChannel):
        """Send alert via email"""
        try:
            config = channel.configuration
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"[{alert.severity.upper()}] Docker Alert: {alert.service_name}"
            
            # Email body
            body = f"""
Docker Container Alert

Alert ID: {alert.alert_id}
Service: {alert.service_name}
Severity: {alert.severity.upper()}
Type: {alert.alert_type}
Time: {alert.timestamp}

Message: {alert.message}

Details:
{json.dumps(alert.details, indent=2)}

Please investigate and take appropriate action.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls', True):
                server.starttls()
            server.login(config['smtp_user'], config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")

    async def _send_slack_notification(self, alert: Alert, channel: NotificationChannel):
        """Send alert via Slack webhook"""
        try:
            config = channel.configuration
            
            # Severity color mapping
            color_map = {
                "low": "#36a64f",      # Green
                "medium": "#ff9500",   # Orange
                "high": "#ff6b6b",     # Red
                "critical": "#ff0000"  # Bright Red
            }
            
            # Create Slack message
            payload = {
                "channel": config.get("channel", "#alerts"),
                "username": config.get("username", "Docker Monitor"),
                "icon_emoji": config.get("icon_emoji", ":warning:"),
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#808080"),
                        "title": f"Docker Alert: {alert.service_name}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Alert Type",
                                "value": alert.alert_type.replace("_", " ").title(),
                                "short": True
                            },
                            {
                                "title": "Service",
                                "value": alert.service_name,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp,
                                "short": True
                            }
                        ],
                        "footer": "Docker Monitoring System",
                        "ts": int(time.time())
                    }
                ]
            }
            
            # Add details if available
            if alert.details:
                details_text = "\n".join([f"• {k}: {v}" for k, v in alert.details.items()])
                payload["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": details_text,
                    "short": False
                })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(config["webhook_url"], json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack notification sent successfully")
                    else:
                        self.logger.error(f"Slack notification failed: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")

    async def _send_resolution_notifications(self, alert: Alert):
        """Send alert resolution notifications"""
        try:
            # Only send resolution notifications for critical and high severity alerts
            if alert.severity not in ['critical', 'high']:
                return
            
            for channel in self.notification_channels:
                if not channel.enabled:
                    continue
                
                if channel.channel_type == "slack":
                    # Send resolution message to Slack
                    config = channel.configuration
                    payload = {
                        "channel": config.get("channel", "#alerts"),
                        "username": config.get("username", "Docker Monitor"),
                        "icon_emoji": ":white_check_mark:",
                        "text": f"✅ RESOLVED: {alert.message}",
                        "attachments": [
                            {
                                "color": "#36a64f",  # Green
                                "title": f"Alert Resolved: {alert.service_name}",
                                "text": f"The {alert.alert_type.replace('_', ' ')} alert has been resolved.",
                                "fields": [
                                    {
                                        "title": "Resolution Time",
                                        "value": alert.resolved_timestamp,
                                        "short": True
                                    }
                                ],
                                "footer": "Docker Monitoring System"
                            }
                        ]
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        await session.post(config["webhook_url"], json=payload)
                
                elif channel.channel_type == "email":
                    # Send resolution email for critical alerts
                    if alert.severity == 'critical':
                        config = channel.configuration
                        
                        msg = MimeMultipart()
                        msg['From'] = config['from_email']
                        msg['To'] = ', '.join(config['to_emails'])
                        msg['Subject'] = f"[RESOLVED] Docker Alert: {alert.service_name}"
                        
                        body = f"""
Alert Resolution Notice

The following Docker alert has been resolved:

Alert ID: {alert.alert_id}
Service: {alert.service_name}
Severity: {alert.severity.upper()}
Type: {alert.alert_type}
Original Time: {alert.timestamp}
Resolved Time: {alert.resolved_timestamp}

The issue has been automatically resolved and the service is now operating normally.
                        """
                        
                        msg.attach(MimeText(body, 'plain'))
                        
                        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
                        if config.get('use_tls', True):
                            server.starttls()
                        server.login(config['smtp_user'], config['smtp_password'])
                        server.send_message(msg)
                        server.quit()
        
        except Exception as e:
            self.logger.error(f"Error sending resolution notifications: {e}")

    async def send_memory_pressure_alert(self, container: str, usage_percent: float):
        """Send alert for memory pressure"""
        if not self._check_cooldown("memory_pressure", container):
            return
        
        severity = "critical" if usage_percent > 90 else "high"
        
        alert = Alert(
            alert_id=self._generate_alert_id("memory_pressure", container),
            alert_type="memory_pressure",
            severity=severity,
            service_name=container,
            message=f"Memory pressure detected in {container}: {usage_percent:.1f}%",
            details={
                "memory_usage_percent": usage_percent,
                "threshold_exceeded": True,
                "recommendation": "Investigate memory leaks or increase memory allocation"
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.last_alert_times[f"memory_pressure_{container}"] = datetime.now()
        
        await self._send_alert_notifications(alert)
        self.logger.warning(f"Memory pressure alert sent for {container}")

    async def send_container_restart_alert(self, container: str, restart_count: int):
        """Send alert for excessive container restarts"""
        if not self._check_cooldown("restart_loop", container):
            return
        
        alert = Alert(
            alert_id=self._generate_alert_id("restart_loop", container),
            alert_type="restart_loop",
            severity="high",
            service_name=container,
            message=f"Container restart loop detected: {container} restarted {restart_count} times",
            details={
                "restart_count": restart_count,
                "threshold": 3,
                "recommendation": "Check container logs and fix underlying issue"
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.last_alert_times[f"restart_loop_{container}"] = datetime.now()
        
        await self._send_alert_notifications(alert)
        self.logger.warning(f"Container restart alert sent for {container}")

    async def send_service_down_alert(self, service: str, downtime_minutes: int):
        """Send alert for service downtime"""
        if not self._check_cooldown("service_down", service):
            return
        
        alert = Alert(
            alert_id=self._generate_alert_id("service_down", service),
            alert_type="service_down",
            severity="critical",
            service_name=service,
            message=f"Service down: {service} has been offline for {downtime_minutes} minutes",
            details={
                "downtime_minutes": downtime_minutes,
                "service_status": "down",
                "recommendation": "Restart service and investigate root cause"
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.last_alert_times[f"service_down_{service}"] = datetime.now()
        
        await self._send_alert_notifications(alert)
        self.logger.error(f"Service down alert sent for {service}")

    def generate_daily_health_summary(self) -> str:
        """Generate daily system health summary"""
        try:
            # Get current time
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            
            # Filter alerts from last 24 hours
            recent_alerts = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert.timestamp) >= yesterday
            ]
            
            # Count alerts by severity
            severity_counts = {}
            for alert in recent_alerts:
                severity = alert.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count alerts by type
            type_counts = {}
            for alert in recent_alerts:
                alert_type = alert.alert_type
                type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            
            # Generate summary
            summary = []
            summary.append("=" * 60)
            summary.append("📊 DAILY DOCKER HEALTH SUMMARY")
            summary.append("=" * 60)
            summary.append(f"📅 Date: {now.strftime('%Y-%m-%d')}")
            summary.append(f"⏰ Generated: {now.strftime('%H:%M:%S')}")
            summary.append("")
            
            # Alert statistics
            summary.append("🚨 ALERT STATISTICS (24h)")
            summary.append(f"   Total Alerts: {len(recent_alerts)}")
            summary.append(f"   Active Alerts: {len(self.active_alerts)}")
            
            if severity_counts:
                summary.append("   By Severity:")
                for severity, count in severity_counts.items():
                    emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(severity, "⚪")
                    summary.append(f"     {emoji} {severity.capitalize()}: {count}")
            
            if type_counts:
                summary.append("   By Type:")
                for alert_type, count in sorted(type_counts.items()):
                    summary.append(f"     • {alert_type.replace('_', ' ').title()}: {count}")
            
            summary.append("")
            
            # Current active alerts
            if self.active_alerts:
                summary.append("⚠️ ACTIVE ALERTS")
                for alert in self.active_alerts.values():
                    severity_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(alert.severity, "⚪")
                    summary.append(f"   {severity_emoji} {alert.service_name}: {alert.message}")
                summary.append("")
            else:
                summary.append("✅ NO ACTIVE ALERTS")
                summary.append("")
            
            # Health recommendations
            summary.append("💡 RECOMMENDATIONS")
            if len(recent_alerts) == 0:
                summary.append("   • System is running smoothly")
                summary.append("   • Continue current monitoring schedule")
            elif len(recent_alerts) < 5:
                summary.append("   • Few alerts detected - system is stable")
                summary.append("   • Review resolved alerts for patterns")
            else:
                summary.append("   • Multiple alerts detected")
                summary.append("   • Review system resources and optimization opportunities")
                summary.append("   • Consider increasing monitoring frequency")
            
            summary.append("")
            summary.append("=" * 60)
            
            result = "\n".join(summary)
            
            # Save summary to file
            summary_file = os.path.join(self.alerts_dir, f"daily_summary_{now.strftime('%Y%m%d')}.txt")
            with open(summary_file, 'w') as f:
                f.write(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating daily health summary: {e}")
            return f"Error generating summary: {e}"

    async def continuous_monitoring(self, interval_seconds: int = 30):
        """Run continuous monitoring and alerting"""
        self.logger.info(f"Starting continuous alerting monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Get current metrics
                metrics = await self.docker_monitor.monitor_all_containers()
                
                # Check alert conditions
                new_alerts = await self.check_alert_conditions(metrics)
                
                if new_alerts:
                    self.logger.info(f"Generated {len(new_alerts)} new alerts")
                
                # Periodic health check
                if len(self.alert_history) % 120 == 0:  # Every hour
                    health_results = await self.health_checker.run_comprehensive_health_check()
                    system_status = health_results.get('overall_system_status', 'unknown')
                    
                    if system_status in ['critical', 'unhealthy']:
                        await self.send_service_down_alert("system", 5)
                
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Alerting monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in alerting monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Docker Alerting System')
    parser.add_argument('--monitor', action='store_true',
                       help='Start continuous monitoring and alerting')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--check', action='store_true',
                       help='Run single alert check')
    parser.add_argument('--summary', action='store_true',
                       help='Generate daily health summary')
    parser.add_argument('--test-alerts', action='store_true',
                       help='Test alert notification system')
    
    args = parser.parse_args()
    
    alerting = DockerAlerting()
    
    if args.monitor:
        await alerting.continuous_monitoring(args.interval)
    elif args.check:
        metrics = await alerting.docker_monitor.monitor_all_containers()
        alerts = await alerting.check_alert_conditions(metrics)
        print(f"Alert check complete: {len(alerts)} new alerts generated")
        
        if alerts:
            for alert in alerts:
                print(f"  🚨 {alert.severity.upper()}: {alert.message}")
    elif args.summary:
        summary = alerting.generate_daily_health_summary()
        print(summary)
    elif args.test_alerts:
        # Test notification system
        test_alert = Alert(
            alert_id="test_alert_123",
            alert_type="test",
            severity="medium",
            service_name="test-service",
            message="Test alert message",
            details={"test": True, "timestamp": datetime.now().isoformat()},
            timestamp=datetime.now().isoformat()
        )
        
        await alerting._send_alert_notifications(test_alert)
        print("Test alert sent through all configured notification channels")
    else:
        # Default: show current status
        print("Docker Alerting System Status")
        print("=" * 40)
        print(f"Active Alerts: {len(alerting.active_alerts)}")
        print(f"Alert History: {len(alerting.alert_history)}")
        print(f"Notification Channels: {len(alerting.notification_channels)}")
        
        for channel in alerting.notification_channels:
            status = "✅" if channel.enabled else "❌"
            print(f"  {status} {channel.channel_type.title()}")
        
        if alerting.active_alerts:
            print("\nActive Alerts:")
            for alert in alerting.active_alerts.values():
                severity_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(alert.severity, "⚪")
                print(f"  {severity_emoji} {alert.service_name}: {alert.message}")

if __name__ == "__main__":
    asyncio.run(main())