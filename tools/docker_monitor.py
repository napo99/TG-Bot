#!/usr/bin/env python3
"""
Docker Monitor - Comprehensive Docker container monitoring system
Provides real-time visibility into container health, resource usage, and operational status.
"""

import docker
import asyncio
import time
import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import sys
import os

@dataclass
class ContainerMetrics:
    """Comprehensive container metrics data structure"""
    container_id: str
    name: str
    status: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    memory_percent: float
    network_rx_mb: float
    network_tx_mb: float
    restart_count: int
    uptime_seconds: int
    health_status: str
    last_restart_time: Optional[str] = None
    ports: List[str] = None
    image: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []

@dataclass
class SystemMetrics:
    """Overall system metrics for AWS t3.micro analysis"""
    total_memory_mb: float
    available_memory_mb: float
    memory_pressure_percent: float
    container_count: int
    healthy_containers: int
    unhealthy_containers: int
    total_cpu_percent: float
    disk_usage_percent: float
    uptime_hours: float
    alerts_active: int

class DockerMonitor:
    """Comprehensive Docker container monitoring system"""
    
    def __init__(self, log_dir: str = "/Users/screener-m3/projects/crypto-assistant/data/logs"):
        """Initialize Docker monitor with enhanced logging"""
        try:
            self.client = docker.from_env()
            self.log_dir = log_dir
            self.setup_logging()
            
            # Alert thresholds optimized for AWS t3.micro (1GB RAM)
            self.alert_thresholds = {
                'memory_warning': 70,    # 70% memory usage warning
                'memory_critical': 85,   # 85% memory usage critical
                'cpu_warning': 80,       # 80% CPU usage warning
                'cpu_critical': 95,      # 95% CPU usage critical
                'restart_threshold': 3,  # Alert after 3 restarts
                'response_time_warning': 5.0,  # 5 second response time
                'disk_warning': 80,      # 80% disk usage
                'uptime_minimum': 300    # 5 minutes minimum uptime
            }
            
            # Target containers for crypto-assistant
            self.target_containers = [
                'crypto-telegram-bot',
                'crypto-market-data', 
                'redis'
            ]
            
            # Metrics history for trend analysis
            self.metrics_history: List[Dict] = []
            self.max_history_size = 1000  # Keep last 1000 measurements
            
            self.logger.info("Docker Monitor initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize Docker Monitor: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, "docker_monitor.log")
        
        # Create logger
        self.logger = logging.getLogger('docker_monitor')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler with rotation
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

    async def get_container_metrics(self, container_name: str) -> Optional[ContainerMetrics]:
        """Get comprehensive metrics for a specific container"""
        try:
            # Find container by name
            containers = self.client.containers.list(all=True)
            container = None
            
            for c in containers:
                if container_name in c.name or any(container_name in tag for tag in c.image.tags):
                    container = c
                    break
            
            if not container:
                self.logger.warning(f"Container {container_name} not found")
                return None
            
            # Get container stats
            stats = container.stats(stream=False)
            
            # Calculate metrics
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 0)
            memory_usage_mb = memory_usage / 1024 / 1024
            memory_limit_mb = memory_limit / 1024 / 1024
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
            
            # CPU calculation
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0
            
            # Network I/O
            networks = stats.get('networks', {})
            network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
            network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
            network_rx_mb = network_rx / 1024 / 1024
            network_tx_mb = network_tx / 1024 / 1024
            
            # Container info
            container.reload()
            restart_count = container.attrs.get('RestartCount', 0)
            created_time = datetime.fromisoformat(
                container.attrs['Created'].replace('Z', '+00:00')
            )
            uptime_seconds = (datetime.now().astimezone() - created_time).total_seconds()
            
            # Health status
            health_status = "unknown"
            if container.status == "running":
                health_status = "healthy"
            elif container.status in ["exited", "dead"]:
                health_status = "unhealthy"
            elif container.status == "restarting":
                health_status = "restarting"
            
            # Port mappings
            ports = []
            port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        ports.append(f"{binding['HostPort']}:{container_port}")
                else:
                    ports.append(container_port)
            
            # Last restart time
            last_restart = None
            if restart_count > 0:
                # Get from container logs if available
                try:
                    logs = container.logs(since=datetime.now() - timedelta(days=1))
                    # This is approximate - Docker doesn't expose exact restart times
                    last_restart = datetime.now().isoformat()
                except:
                    pass
            
            return ContainerMetrics(
                container_id=container.short_id,
                name=container.name,
                status=container.status,
                cpu_percent=round(cpu_percent, 2),
                memory_usage_mb=round(memory_usage_mb, 2),
                memory_limit_mb=round(memory_limit_mb, 2),
                memory_percent=round(memory_percent, 2),
                network_rx_mb=round(network_rx_mb, 2),
                network_tx_mb=round(network_tx_mb, 2),
                restart_count=restart_count,
                uptime_seconds=int(uptime_seconds),
                health_status=health_status,
                last_restart_time=last_restart,
                ports=ports,
                image=container.image.tags[0] if container.image.tags else container.image.id[:12],
                created_at=container.attrs['Created']
            )
            
        except Exception as e:
            self.logger.error(f"Error getting metrics for {container_name}: {e}")
            return None

    async def monitor_all_containers(self) -> List[ContainerMetrics]:
        """Monitor all crypto-assistant containers"""
        metrics = []
        
        try:
            # Get all containers
            containers = self.client.containers.list(all=True)
            
            # Filter for crypto-assistant containers
            target_containers = []
            for container in containers:
                if any(target in container.name.lower() for target in 
                      ['crypto', 'telegram', 'market', 'redis', 'bot']):
                    target_containers.append(container.name)
            
            # Get metrics for each container
            for container_name in target_containers:
                metric = await self.get_container_metrics(container_name)
                if metric:
                    metrics.append(metric)
            
            # Store in history
            metrics_snapshot = {
                'timestamp': datetime.now().isoformat(),
                'containers': [asdict(m) for m in metrics]
            }
            self.metrics_history.append(metrics_snapshot)
            
            # Trim history if needed
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            self.logger.info(f"Monitored {len(metrics)} containers")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error monitoring containers: {e}")
            return []

    async def check_service_dependencies(self) -> Dict[str, bool]:
        """Verify inter-service communication health"""
        dependencies = {}
        
        try:
            # Test Telegram Bot health endpoint
            try:
                response = requests.get('http://localhost:8080/health', timeout=5)
                dependencies['telegram_bot_health'] = response.status_code == 200
            except:
                dependencies['telegram_bot_health'] = False
            
            # Test Market Data health endpoint
            try:
                response = requests.get('http://localhost:8001/health', timeout=5)
                dependencies['market_data_health'] = response.status_code == 200
            except:
                dependencies['market_data_health'] = False
            
            # Test Market Data API endpoints
            try:
                response = requests.post(
                    'http://localhost:8001/comprehensive_analysis',
                    json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
                    timeout=10
                )
                dependencies['market_data_api'] = response.status_code == 200
            except:
                dependencies['market_data_api'] = False
            
            # Test Redis connectivity (if accessible)
            try:
                # Check if Redis container is running
                redis_containers = [c for c in self.client.containers.list() 
                                 if 'redis' in c.name.lower()]
                dependencies['redis_container'] = len(redis_containers) > 0 and \
                                                redis_containers[0].status == 'running'
            except:
                dependencies['redis_container'] = False
            
            # Test inter-service communication
            try:
                # Telegram bot should be able to reach market data
                response = requests.get('http://crypto-market-data:8001/health', timeout=5)
                dependencies['inter_service_communication'] = response.status_code == 200
            except:
                dependencies['inter_service_communication'] = False
            
            self.logger.info(f"Service dependencies check: {dependencies}")
            return dependencies
            
        except Exception as e:
            self.logger.error(f"Error checking service dependencies: {e}")
            return {}

    async def aws_t3_micro_analysis(self) -> Dict[str, Any]:
        """Specialized monitoring for AWS t3.micro constraints"""
        try:
            # AWS t3.micro specifications
            t3_micro_specs = {
                'total_memory_mb': 1024,     # 1GB RAM
                'available_memory_mb': 824,   # After OS overhead (~200MB)
                'cpu_credits': 'baseline',    # Burstable performance
                'network_baseline_mbps': 5    # Up to 5 Gbps
            }
            
            # Get current system metrics
            containers = await self.monitor_all_containers()
            
            # Calculate total usage
            total_memory_usage = sum(c.memory_usage_mb for c in containers)
            total_cpu_usage = sum(c.cpu_percent for c in containers) / len(containers) if containers else 0
            
            # Memory pressure analysis
            memory_pressure = (total_memory_usage / t3_micro_specs['available_memory_mb']) * 100
            
            # Efficiency analysis
            running_containers = [c for c in containers if c.status == 'running']
            healthy_containers = [c for c in containers if c.health_status == 'healthy']
            
            # Performance recommendations
            recommendations = []
            
            if memory_pressure > 85:
                recommendations.append("CRITICAL: Memory pressure > 85%. Consider upgrading to t3.small.")
            elif memory_pressure > 70:
                recommendations.append("WARNING: Memory pressure > 70%. Monitor closely.")
            
            if total_cpu_usage > 90:
                recommendations.append("CPU usage high. May exhaust CPU credits on t3.micro.")
            
            if len(running_containers) != len(self.target_containers):
                recommendations.append("Not all expected containers are running.")
            
            # Cost analysis
            cost_analysis = {
                'current_instance': 't3.micro',
                'monthly_cost_usd': 8.50,  # Approximate AWS pricing
                'memory_efficiency': f"{memory_pressure:.1f}%",
                'upgrade_recommendation': 't3.small' if memory_pressure > 85 else 'current_adequate'
            }
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'instance_specs': t3_micro_specs,
                'current_usage': {
                    'memory_mb': round(total_memory_usage, 2),
                    'memory_pressure_percent': round(memory_pressure, 2),
                    'cpu_percent': round(total_cpu_usage, 2),
                    'container_count': len(containers),
                    'running_containers': len(running_containers),
                    'healthy_containers': len(healthy_containers)
                },
                'recommendations': recommendations,
                'cost_analysis': cost_analysis,
                'performance_status': 'optimal' if memory_pressure < 70 and total_cpu_usage < 80 else 'stressed'
            }
            
            self.logger.info(f"AWS t3.micro analysis complete: {analysis['performance_status']}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in AWS t3.micro analysis: {e}")
            return {}

    def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        try:
            # Get latest metrics
            if not self.metrics_history:
                return "No metrics available"
            
            latest_metrics = self.metrics_history[-1]['containers']
            timestamp = self.metrics_history[-1]['timestamp']
            
            # Generate report
            report = []
            report.append("=" * 60)
            report.append("🐳 DOCKER CONTAINER HEALTH REPORT")
            report.append("=" * 60)
            report.append(f"📅 Generated: {timestamp}")
            report.append(f"📊 Containers Monitored: {len(latest_metrics)}")
            report.append("")
            
            # Container summary
            running_count = sum(1 for c in latest_metrics if c['status'] == 'running')
            healthy_count = sum(1 for c in latest_metrics if c['health_status'] == 'healthy')
            
            report.append("📋 SUMMARY")
            report.append(f"   ✅ Running: {running_count}/{len(latest_metrics)}")
            report.append(f"   💚 Healthy: {healthy_count}/{len(latest_metrics)}")
            report.append("")
            
            # Individual container details
            report.append("🔍 CONTAINER DETAILS")
            for container in latest_metrics:
                status_emoji = "✅" if container['status'] == 'running' else "❌"
                health_emoji = "💚" if container['health_status'] == 'healthy' else "⚠️"
                
                report.append(f"   {status_emoji} {container['name']}")
                report.append(f"      Status: {container['status']} {health_emoji}")
                report.append(f"      Memory: {container['memory_usage_mb']:.1f}MB ({container['memory_percent']:.1f}%)")
                report.append(f"      CPU: {container['cpu_percent']:.1f}%")
                report.append(f"      Uptime: {container['uptime_seconds']}s")
                report.append(f"      Restarts: {container['restart_count']}")
                if container['ports']:
                    report.append(f"      Ports: {', '.join(container['ports'])}")
                report.append("")
            
            # Resource summary
            total_memory = sum(c['memory_usage_mb'] for c in latest_metrics)
            avg_cpu = sum(c['cpu_percent'] for c in latest_metrics) / len(latest_metrics) if latest_metrics else 0
            
            report.append("📊 RESOURCE USAGE")
            report.append(f"   Memory Total: {total_memory:.1f}MB")
            report.append(f"   CPU Average: {avg_cpu:.1f}%")
            report.append("")
            
            # Alerts
            alerts = []
            for container in latest_metrics:
                if container['memory_percent'] > self.alert_thresholds['memory_critical']:
                    alerts.append(f"🚨 {container['name']}: Critical memory usage ({container['memory_percent']:.1f}%)")
                elif container['memory_percent'] > self.alert_thresholds['memory_warning']:
                    alerts.append(f"⚠️ {container['name']}: High memory usage ({container['memory_percent']:.1f}%)")
                
                if container['restart_count'] > self.alert_thresholds['restart_threshold']:
                    alerts.append(f"🔄 {container['name']}: Multiple restarts ({container['restart_count']})")
            
            if alerts:
                report.append("🚨 ALERTS")
                for alert in alerts:
                    report.append(f"   {alert}")
                report.append("")
            else:
                report.append("✅ NO ACTIVE ALERTS")
                report.append("")
            
            report.append("=" * 60)
            
            return "\n".join(report)
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return f"Error generating report: {e}"

    async def continuous_monitoring(self, interval_seconds: int = 30):
        """Run continuous monitoring loop"""
        self.logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Monitor containers
                metrics = await self.monitor_all_containers()
                
                # Check service dependencies
                dependencies = await self.check_service_dependencies()
                
                # AWS analysis
                aws_analysis = await self.aws_t3_micro_analysis()
                
                # Log summary
                healthy_count = sum(1 for m in metrics if m.health_status == 'healthy')
                total_memory = sum(m.memory_usage_mb for m in metrics)
                
                self.logger.info(
                    f"Monitoring cycle complete: {healthy_count}/{len(metrics)} healthy, "
                    f"{total_memory:.1f}MB total memory"
                )
                
                # Check for alerts
                for metric in metrics:
                    if metric.memory_percent > self.alert_thresholds['memory_critical']:
                        self.logger.error(
                            f"CRITICAL: {metric.name} memory usage {metric.memory_percent:.1f}%"
                        )
                
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Docker Container Monitor')
    parser.add_argument('--continuous', action='store_true', 
                       help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--report', action='store_true',
                       help='Generate health report')
    parser.add_argument('--aws-analysis', action='store_true',
                       help='Run AWS t3.micro analysis')
    parser.add_argument('--container', type=str,
                       help='Monitor specific container')
    
    args = parser.parse_args()
    
    monitor = DockerMonitor()
    
    if args.continuous:
        await monitor.continuous_monitoring(args.interval)
    elif args.report:
        print(monitor.generate_health_report())
    elif args.aws_analysis:
        analysis = await monitor.aws_t3_micro_analysis()
        print(json.dumps(analysis, indent=2))
    elif args.container:
        metric = await monitor.get_container_metrics(args.container)
        if metric:
            print(json.dumps(asdict(metric), indent=2))
        else:
            print(f"Container {args.container} not found")
    else:
        # Default: monitor all containers once
        metrics = await monitor.monitor_all_containers()
        dependencies = await monitor.check_service_dependencies()
        
        print(f"Monitored {len(metrics)} containers")
        print(f"Service dependencies: {dependencies}")
        print("\nHealth Report:")
        print(monitor.generate_health_report())

if __name__ == "__main__":
    asyncio.run(main())