#!/usr/bin/env python3
"""
AWS Production Monitor - Specialized monitoring for AWS t3.micro production environment
Provides AWS-specific metrics, cost optimization analysis, and upgrade recommendations.
"""

import asyncio
import aiohttp
import json
import logging
import psutil
import boto3
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os
import subprocess

from docker_monitor import DockerMonitor
from resource_analyzer import ResourceAnalyzer

@dataclass
class AWSInstanceMetrics:
    """AWS EC2 instance metrics"""
    instance_id: str
    instance_type: str
    region: str
    availability_zone: str
    public_ip: str
    private_ip: str
    state: str
    launch_time: str
    uptime_hours: float
    cpu_credits_remaining: Optional[float]
    cpu_credits_balance: Optional[float]
    network_performance: str
    ebs_optimized: bool
    monitoring_enabled: bool

@dataclass
class CostAnalysis:
    """AWS cost analysis"""
    current_instance_type: str
    current_hourly_cost: float
    current_monthly_cost: float
    usage_efficiency: float
    recommended_instance_type: str
    recommended_hourly_cost: float
    recommended_monthly_cost: float
    potential_savings: float
    upgrade_justification: List[str]
    cost_optimization_score: float

@dataclass
class PerformanceMetrics:
    """Performance metrics specific to AWS t3.micro"""
    memory_utilization_percent: float
    memory_pressure_risk: str
    cpu_utilization_percent: float
    cpu_credits_exhaustion_risk: str
    network_utilization_mbps: float
    disk_utilization_percent: float
    baseline_performance_ratio: float
    burst_capacity_used: bool
    
@dataclass
class UpgradeRecommendation:
    """Instance upgrade recommendation"""
    current_instance: str
    recommended_instance: str
    reason: str
    benefits: List[str]
    costs: Dict[str, float]
    migration_complexity: str
    downtime_estimate: str
    roi_analysis: Dict[str, Any]

class AWSProductionMonitor:
    """Specialized monitoring for AWS t3.micro production environment"""
    
    def __init__(self, log_dir: str = "/Users/screener-m3/projects/crypto-assistant/data/logs"):
        """Initialize AWS production monitor"""
        self.log_dir = log_dir
        self.setup_logging()
        
        # AWS instance specifications
        self.t3_micro_specs = {
            'instance_type': 't3.micro',
            'vcpus': 2,
            'memory_gb': 1.0,
            'memory_mb': 1024,
            'system_overhead_mb': 200,  # OS and system processes
            'available_memory_mb': 824,  # Available for applications
            'cpu_credits_per_hour': 12,
            'baseline_cpu_percent': 20,
            'max_cpu_percent': 100,  # During burst
            'network_baseline_mbps': 5,
            'network_burst_mbps': 5000,  # Up to 5 Gbps
            'hourly_cost_usd': 0.0116,  # US East pricing
            'monthly_cost_usd': 8.50
        }
        
        # Alternative instance types for comparison
        self.instance_options = {
            't3.small': {
                'vcpus': 2,
                'memory_gb': 2.0,
                'memory_mb': 2048,
                'cpu_credits_per_hour': 24,
                'baseline_cpu_percent': 20,
                'hourly_cost_usd': 0.0232,
                'monthly_cost_usd': 17.0
            },
            't3.medium': {
                'vcpus': 2,
                'memory_gb': 4.0,
                'memory_mb': 4096,
                'cpu_credits_per_hour': 24,
                'baseline_cpu_percent': 20,
                'hourly_cost_usd': 0.0464,
                'monthly_cost_usd': 34.0
            },
            't2.small': {
                'vcpus': 1,
                'memory_gb': 2.0,
                'memory_mb': 2048,
                'cpu_credits_per_hour': 12,
                'baseline_cpu_percent': 10,
                'hourly_cost_usd': 0.023,
                'monthly_cost_usd': 16.9
            }
        }
        
        # Initialize monitoring components
        self.docker_monitor = DockerMonitor(log_dir)
        self.resource_analyzer = ResourceAnalyzer(log_dir)
        
        # AWS credentials and region detection
        self.aws_region = self._detect_aws_region()
        self.instance_id = self._get_instance_id()
        
        # Initialize AWS clients (if available)
        self.ec2_client = None
        self.cloudwatch_client = None
        self._initialize_aws_clients()
        
        # Performance thresholds for t3.micro
        self.thresholds = {
            'memory_warning': 70,        # 70% of available memory
            'memory_critical': 85,       # 85% of available memory
            'cpu_sustained_high': 80,    # 80% CPU for extended periods
            'cpu_credits_low': 50,       # Low CPU credits warning
            'cpu_credits_critical': 10,  # Critical CPU credits
            'network_high': 3,           # 3 Mbps sustained
            'disk_warning': 80,          # 80% disk usage
            'burst_usage_warning': 0.7   # 70% of burst capacity used
        }
        
        self.logger.info("AWS Production Monitor initialized")

    def setup_logging(self):
        """Setup logging system"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, "aws_production_monitor.log")
        
        self.logger = logging.getLogger('aws_production_monitor')
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

    def _detect_aws_region(self) -> Optional[str]:
        """Detect AWS region from instance metadata"""
        try:
            # Try to get region from instance metadata
            response = subprocess.run([
                'curl', '-s', '--max-time', '2',
                'http://169.254.169.254/latest/meta-data/placement/region'
            ], capture_output=True, text=True)
            
            if response.returncode == 0 and response.stdout.strip():
                region = response.stdout.strip()
                self.logger.info(f"Detected AWS region: {region}")
                return region
                
        except Exception as e:
            self.logger.debug(f"Could not detect AWS region: {e}")
        
        # Fallback to environment variable or default
        return os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

    def _get_instance_id(self) -> Optional[str]:
        """Get EC2 instance ID from metadata"""
        try:
            response = subprocess.run([
                'curl', '-s', '--max-time', '2',
                'http://169.254.169.254/latest/meta-data/instance-id'
            ], capture_output=True, text=True)
            
            if response.returncode == 0 and response.stdout.strip().startswith('i-'):
                instance_id = response.stdout.strip()
                self.logger.info(f"Detected instance ID: {instance_id}")
                return instance_id
                
        except Exception as e:
            self.logger.debug(f"Could not get instance ID: {e}")
        
        return None

    def _initialize_aws_clients(self):
        """Initialize AWS clients if credentials are available"""
        try:
            # Try to initialize EC2 client
            self.ec2_client = boto3.client('ec2', region_name=self.aws_region)
            
            # Test the connection
            self.ec2_client.describe_instances(MaxResults=1, DryRun=True)
            
        except Exception as e:
            self.logger.debug(f"AWS EC2 client not available: {e}")
            self.ec2_client = None
        
        try:
            # Try to initialize CloudWatch client
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
            
            # Test the connection
            self.cloudwatch_client.list_metrics(MaxRecords=1)
            
        except Exception as e:
            self.logger.debug(f"AWS CloudWatch client not available: {e}")
            self.cloudwatch_client = None

    async def monitor_ec2_instance_health(self) -> Dict[str, Any]:
        """Monitor overall EC2 instance health"""
        try:
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'instance_metadata': {},
                'system_metrics': {},
                'aws_metrics': {},
                'health_status': 'unknown',
                'recommendations': []
            }
            
            # Get instance metadata
            metadata = await self._get_instance_metadata()
            health_data['instance_metadata'] = metadata
            
            # Get system metrics
            system_metrics = await self._get_system_metrics()
            health_data['system_metrics'] = system_metrics
            
            # Get AWS-specific metrics (if available)
            if self.ec2_client and self.instance_id:
                aws_metrics = await self._get_aws_cloudwatch_metrics()
                health_data['aws_metrics'] = aws_metrics
            
            # Determine health status
            health_status = self._determine_instance_health_status(
                system_metrics, health_data.get('aws_metrics', {})
            )
            health_data['health_status'] = health_status
            
            # Generate recommendations
            recommendations = self._generate_health_recommendations(health_data)
            health_data['recommendations'] = recommendations
            
            self.logger.info(f"EC2 instance health check complete: {health_status}")
            return health_data
            
        except Exception as e:
            self.logger.error(f"Error monitoring EC2 instance health: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def _get_instance_metadata(self) -> Dict[str, Any]:
        """Get EC2 instance metadata"""
        metadata = {}
        
        try:
            # Instance ID
            if self.instance_id:
                metadata['instance_id'] = self.instance_id
            
            # Instance type
            try:
                response = subprocess.run([
                    'curl', '-s', '--max-time', '2',
                    'http://169.254.169.254/latest/meta-data/instance-type'
                ], capture_output=True, text=True)
                
                if response.returncode == 0:
                    metadata['instance_type'] = response.stdout.strip()
            except:
                metadata['instance_type'] = 't3.micro'  # Assumed
            
            # Availability zone
            try:
                response = subprocess.run([
                    'curl', '-s', '--max-time', '2',
                    'http://169.254.169.254/latest/meta-data/placement/availability-zone'
                ], capture_output=True, text=True)
                
                if response.returncode == 0:
                    metadata['availability_zone'] = response.stdout.strip()
            except:
                pass
            
            # Public IP
            try:
                response = subprocess.run([
                    'curl', '-s', '--max-time', '2',
                    'http://169.254.169.254/latest/meta-data/public-ipv4'
                ], capture_output=True, text=True)
                
                if response.returncode == 0:
                    metadata['public_ip'] = response.stdout.strip()
            except:
                pass
            
            # Private IP
            try:
                response = subprocess.run([
                    'curl', '-s', '--max-time', '2',
                    'http://169.254.169.254/latest/meta-data/local-ipv4'
                ], capture_output=True, text=True)
                
                if response.returncode == 0:
                    metadata['private_ip'] = response.stdout.strip()
            except:
                pass
            
            # Region
            metadata['region'] = self.aws_region
            
            # Get additional EC2 metadata if client is available
            if self.ec2_client and self.instance_id:
                try:
                    response = self.ec2_client.describe_instances(
                        InstanceIds=[self.instance_id]
                    )
                    
                    if response['Reservations']:
                        instance = response['Reservations'][0]['Instances'][0]
                        metadata.update({
                            'launch_time': instance['LaunchTime'].isoformat(),
                            'state': instance['State']['Name'],
                            'monitoring': instance['Monitoring']['State'],
                            'instance_type': instance['InstanceType'],
                            'ebs_optimized': instance.get('EbsOptimized', False)
                        })
                        
                        # Calculate uptime
                        launch_time = instance['LaunchTime']
                        uptime = datetime.now(launch_time.tzinfo) - launch_time
                        metadata['uptime_hours'] = uptime.total_seconds() / 3600
                
                except Exception as e:
                    self.logger.debug(f"Error getting EC2 instance details: {e}")
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error getting instance metadata: {e}")
            return {}

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Load average
            load_avg = psutil.getloadavg()
            
            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            return {
                'memory': {
                    'total_mb': round(memory.total / 1024 / 1024, 2),
                    'available_mb': round(memory.available / 1024 / 1024, 2),
                    'used_mb': round(memory.used / 1024 / 1024, 2),
                    'percent': memory.percent,
                    'buffers_mb': round(memory.buffers / 1024 / 1024, 2) if hasattr(memory, 'buffers') else 0,
                    'cached_mb': round(memory.cached / 1024 / 1024, 2) if hasattr(memory, 'cached') else 0
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg_1m': load_avg[0],
                    'load_avg_5m': load_avg[1],
                    'load_avg_15m': load_avg[2]
                },
                'disk': {
                    'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'percent': round((disk.used / disk.total) * 100, 2)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'uptime_hours': round(uptime / 3600, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}

    async def _get_aws_cloudwatch_metrics(self) -> Dict[str, Any]:
        """Get AWS CloudWatch metrics"""
        if not self.cloudwatch_client or not self.instance_id:
            return {}
        
        try:
            # Define time range (last hour)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics_to_fetch = [
                ('CPUUtilization', 'AWS/EC2'),
                ('CPUCreditUsage', 'AWS/EC2'),
                ('CPUCreditBalance', 'AWS/EC2'),
                ('NetworkIn', 'AWS/EC2'),
                ('NetworkOut', 'AWS/EC2'),
                ('NetworkPacketsIn', 'AWS/EC2'),
                ('NetworkPacketsOut', 'AWS/EC2')
            ]
            
            cloudwatch_data = {}
            
            for metric_name, namespace in metrics_to_fetch:
                try:
                    response = self.cloudwatch_client.get_metric_statistics(
                        Namespace=namespace,
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'InstanceId',
                                'Value': self.instance_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,  # 5-minute periods
                        Statistics=['Average', 'Maximum']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        # Sort by timestamp and get latest
                        latest = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
                        cloudwatch_data[metric_name] = {
                            'average': latest.get('Average', 0),
                            'maximum': latest.get('Maximum', 0),
                            'timestamp': latest['Timestamp'].isoformat()
                        }
                
                except Exception as e:
                    self.logger.debug(f"Error fetching {metric_name}: {e}")
                    continue
            
            return cloudwatch_data
            
        except Exception as e:
            self.logger.error(f"Error getting CloudWatch metrics: {e}")
            return {}

    def _determine_instance_health_status(self, system_metrics: Dict, aws_metrics: Dict) -> str:
        """Determine overall instance health status"""
        try:
            issues = []
            
            # Check memory usage
            memory_percent = system_metrics.get('memory', {}).get('percent', 0)
            if memory_percent > self.thresholds['memory_critical']:
                issues.append('critical_memory')
            elif memory_percent > self.thresholds['memory_warning']:
                issues.append('warning_memory')
            
            # Check CPU usage
            cpu_percent = system_metrics.get('cpu', {}).get('percent', 0)
            if cpu_percent > self.thresholds['cpu_sustained_high']:
                issues.append('high_cpu')
            
            # Check CPU credits (if available)
            cpu_credit_balance = aws_metrics.get('CPUCreditBalance', {}).get('average', 100)
            if cpu_credit_balance < self.thresholds['cpu_credits_critical']:
                issues.append('critical_cpu_credits')
            elif cpu_credit_balance < self.thresholds['cpu_credits_low']:
                issues.append('low_cpu_credits')
            
            # Check disk usage
            disk_percent = system_metrics.get('disk', {}).get('percent', 0)
            if disk_percent > self.thresholds['disk_warning']:
                issues.append('high_disk')
            
            # Check load average
            load_avg = system_metrics.get('cpu', {}).get('load_avg_1m', 0)
            cpu_count = system_metrics.get('cpu', {}).get('count', 2)
            if load_avg > cpu_count * 1.5:  # Load average > 1.5 * CPU count
                issues.append('high_load')
            
            # Determine status based on issues
            if any(issue.startswith('critical') for issue in issues):
                return 'critical'
            elif len(issues) >= 3:
                return 'degraded'
            elif issues:
                return 'warning'
            else:
                return 'healthy'
                
        except Exception as e:
            self.logger.error(f"Error determining health status: {e}")
            return 'unknown'

    def _generate_health_recommendations(self, health_data: Dict) -> List[str]:
        """Generate health recommendations based on metrics"""
        recommendations = []
        
        try:
            system_metrics = health_data.get('system_metrics', {})
            aws_metrics = health_data.get('aws_metrics', {})
            
            # Memory recommendations
            memory_percent = system_metrics.get('memory', {}).get('percent', 0)
            if memory_percent > self.thresholds['memory_critical']:
                recommendations.append(
                    "CRITICAL: Memory usage above 85%. Consider upgrading to t3.small for 2GB RAM."
                )
            elif memory_percent > self.thresholds['memory_warning']:
                recommendations.append(
                    "WARNING: High memory usage. Monitor applications for memory leaks."
                )
            
            # CPU recommendations
            cpu_percent = system_metrics.get('cpu', {}).get('percent', 0)
            if cpu_percent > self.thresholds['cpu_sustained_high']:
                recommendations.append(
                    "High CPU usage detected. This will consume CPU credits on t3.micro."
                )
            
            # CPU credits recommendations
            cpu_credit_balance = aws_metrics.get('CPUCreditBalance', {}).get('average', 100)
            if cpu_credit_balance < self.thresholds['cpu_credits_critical']:
                recommendations.append(
                    "CRITICAL: CPU credits depleted. Performance is throttled to baseline 20%."
                )
            elif cpu_credit_balance < self.thresholds['cpu_credits_low']:
                recommendations.append(
                    "WARNING: Low CPU credits. Optimize applications or consider upgrading."
                )
            
            # Disk recommendations
            disk_percent = system_metrics.get('disk', {}).get('percent', 0)
            if disk_percent > self.thresholds['disk_warning']:
                recommendations.append(
                    f"Disk usage is {disk_percent:.1f}%. Clean up logs and temporary files."
                )
            
            # General optimization recommendations
            if not recommendations:
                recommendations.append(
                    "System is running well. Continue monitoring for trends."
                )
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]

    async def analyze_memory_efficiency(self) -> Dict[str, Any]:
        """Analyze memory usage efficiency"""
        try:
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'memory_analysis': {},
                'efficiency_score': 0.0,
                'optimization_opportunities': [],
                'recommendations': []
            }
            
            # Get current system metrics
            system_metrics = await self._get_system_metrics()
            memory = system_metrics.get('memory', {})
            
            # Get container metrics
            container_metrics = await self.docker_monitor.monitor_all_containers()
            
            # Calculate memory efficiency
            total_system_memory = memory.get('total_mb', 1024)
            used_system_memory = memory.get('used_mb', 0)
            available_memory = memory.get('available_mb', 824)
            
            # Container memory usage
            container_memory_total = sum(c.memory_usage_mb for c in container_metrics)
            
            # Analysis
            analysis['memory_analysis'] = {
                'total_system_memory_mb': total_system_memory,
                'used_system_memory_mb': used_system_memory,
                'available_memory_mb': available_memory,
                'system_memory_utilization': (used_system_memory / total_system_memory) * 100,
                'container_memory_total_mb': round(container_memory_total, 2),
                'container_memory_efficiency': (container_memory_total / used_system_memory) * 100 if used_system_memory > 0 else 0,
                'memory_fragmentation': memory.get('buffers_mb', 0) + memory.get('cached_mb', 0),
                't3_micro_memory_pressure': (used_system_memory / self.t3_micro_specs['available_memory_mb']) * 100
            }
            
            # Calculate efficiency score (0-100)
            memory_utilization = analysis['memory_analysis']['system_memory_utilization']
            container_efficiency = analysis['memory_analysis']['container_memory_efficiency']
            
            # Ideal utilization is 60-80% for good performance with room for bursts
            if 60 <= memory_utilization <= 80:
                utilization_score = 100
            elif memory_utilization < 60:
                utilization_score = (memory_utilization / 60) * 80  # Underutilized
            else:
                utilization_score = max(0, 100 - (memory_utilization - 80) * 5)  # Overutilized
            
            # Container efficiency should be high (containers using most of allocated memory)
            efficiency_score = min(100, container_efficiency)
            
            analysis['efficiency_score'] = round((utilization_score + efficiency_score) / 2, 1)
            
            # Optimization opportunities
            if memory_utilization > 85:
                analysis['optimization_opportunities'].append({
                    'type': 'memory_pressure',
                    'description': 'System memory usage is critically high',
                    'impact': 'high',
                    'action': 'Upgrade to t3.small or optimize container memory usage'
                })
            
            if container_efficiency < 70:
                analysis['optimization_opportunities'].append({
                    'type': 'container_overhead',
                    'description': 'Containers have high memory overhead',
                    'impact': 'medium',
                    'action': 'Review container memory limits and optimize applications'
                })
            
            if memory_utilization < 40:
                analysis['optimization_opportunities'].append({
                    'type': 'underutilization',
                    'description': 'Memory is underutilized',
                    'impact': 'low',
                    'action': 'Consider cost optimization or running additional services'
                })
            
            # Recommendations
            if analysis['efficiency_score'] > 80:
                analysis['recommendations'].append("Memory usage is well optimized")
            elif analysis['efficiency_score'] > 60:
                analysis['recommendations'].append("Memory usage is acceptable with room for improvement")
            else:
                analysis['recommendations'].append("Memory usage needs optimization")
            
            # Specific recommendations based on container analysis
            high_memory_containers = [c for c in container_metrics if c.memory_percent > 70]
            if high_memory_containers:
                analysis['recommendations'].append(
                    f"High memory containers detected: {', '.join(c.name for c in high_memory_containers)}"
                )
            
            self.logger.info(f"Memory efficiency analysis complete: score {analysis['efficiency_score']}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing memory efficiency: {e}")
            return {'error': str(e)}

    async def predict_memory_exhaustion(self) -> Dict[str, Any]:
        """Predict when system might run out of memory"""
        try:
            prediction = {
                'timestamp': datetime.now().isoformat(),
                'current_status': {},
                'trend_analysis': {},
                'prediction': {},
                'risk_level': 'unknown',
                'recommendations': []
            }
            
            # Get current memory status
            system_metrics = await self._get_system_metrics()
            memory = system_metrics.get('memory', {})
            
            prediction['current_status'] = {
                'available_memory_mb': memory.get('available_mb', 0),
                'used_memory_mb': memory.get('used_mb', 0),
                'memory_pressure_percent': memory.get('percent', 0),
                'free_memory_mb': round(memory.get('available_mb', 0), 2)
            }
            
            # Get memory trends from resource analyzer
            memory_trends = self.resource_analyzer.analyze_memory_trends(timeframe_hours=6)
            
            if memory_trends:
                # Analyze trends across all containers
                total_current_memory = sum(trend.current_value for trend in memory_trends.values())
                total_predicted_memory = sum(trend.predicted_next_hour for trend in memory_trends.values())
                
                # Calculate trend
                memory_growth_rate = total_predicted_memory - total_current_memory
                memory_growth_percent = (memory_growth_rate / total_current_memory * 100) if total_current_memory > 0 else 0
                
                prediction['trend_analysis'] = {
                    'current_container_memory_mb': round(total_current_memory, 2),
                    'predicted_container_memory_mb': round(total_predicted_memory, 2),
                    'memory_growth_rate_mb_per_hour': round(memory_growth_rate, 2),
                    'memory_growth_percent_per_hour': round(memory_growth_percent, 2),
                    'trending_containers': {
                        name: {
                            'current_mb': trend.current_value,
                            'predicted_mb': trend.predicted_next_hour,
                            'trend_direction': trend.trend_direction,
                            'alert_level': trend.alert_level
                        }
                        for name, trend in memory_trends.items()
                    }
                }
                
                # Prediction calculations
                available_memory = memory.get('available_mb', 824)
                current_used = memory.get('used_mb', 200)
                
                if memory_growth_rate > 0:
                    # Calculate time to exhaustion
                    memory_remaining = available_memory
                    hours_to_exhaustion = memory_remaining / memory_growth_rate
                    
                    if hours_to_exhaustion < 24:
                        risk_level = 'critical'
                    elif hours_to_exhaustion < 72:
                        risk_level = 'high'
                    elif hours_to_exhaustion < 168:  # 1 week
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'
                else:
                    hours_to_exhaustion = float('inf')
                    risk_level = 'low'
                
                prediction['prediction'] = {
                    'hours_to_memory_exhaustion': hours_to_exhaustion if hours_to_exhaustion != float('inf') else None,
                    'days_to_memory_exhaustion': round(hours_to_exhaustion / 24, 1) if hours_to_exhaustion != float('inf') else None,
                    'predicted_memory_usage_24h': round(current_used + (memory_growth_rate * 24), 2),
                    'memory_exhaustion_date': (datetime.now() + timedelta(hours=hours_to_exhaustion)).isoformat() if hours_to_exhaustion != float('inf') else None
                }
                
                prediction['risk_level'] = risk_level
                
                # Recommendations based on risk level
                if risk_level == 'critical':
                    prediction['recommendations'] = [
                        "CRITICAL: Memory exhaustion predicted within 24 hours",
                        "Immediate action required: Restart containers or upgrade instance",
                        "Consider emergency upgrade to t3.small"
                    ]
                elif risk_level == 'high':
                    prediction['recommendations'] = [
                        "HIGH RISK: Memory exhaustion predicted within 3 days",
                        "Plan maintenance window for optimization or upgrade",
                        "Monitor memory growth closely"
                    ]
                elif risk_level == 'medium':
                    prediction['recommendations'] = [
                        "MEDIUM RISK: Memory pressure trending upward",
                        "Investigate memory growth patterns",
                        "Consider optimization or planning upgrade"
                    ]
                else:
                    prediction['recommendations'] = [
                        "LOW RISK: Memory usage is stable or decreasing",
                        "Continue monitoring for changes"
                    ]
            
            else:
                prediction['trend_analysis'] = {'error': 'Insufficient historical data for trend analysis'}
                prediction['prediction'] = {'error': 'Cannot predict without trend data'}
                prediction['risk_level'] = 'unknown'
                prediction['recommendations'] = ['Collect more historical data for accurate predictions']
            
            self.logger.info(f"Memory exhaustion prediction complete: risk level {prediction['risk_level']}")
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error predicting memory exhaustion: {e}")
            return {'error': str(e)}

    async def suggest_instance_upgrade(self) -> Dict[str, Any]:
        """Analyze if instance upgrade is needed and provide recommendations"""
        try:
            upgrade_analysis = {
                'timestamp': datetime.now().isoformat(),
                'current_instance': self.t3_micro_specs,
                'performance_analysis': {},
                'cost_analysis': {},
                'upgrade_recommendations': [],
                'migration_plan': {},
                'decision_matrix': {}
            }
            
            # Get current performance metrics
            container_metrics = await self.docker_monitor.monitor_all_containers()
            system_metrics = await self._get_system_metrics()
            memory_analysis = await self.analyze_memory_efficiency()
            
            # Performance analysis
            memory_utilization = system_metrics.get('memory', {}).get('percent', 0)
            cpu_utilization = system_metrics.get('cpu', {}).get('percent', 0)
            container_memory_total = sum(c.memory_usage_mb for c in container_metrics)
            
            upgrade_analysis['performance_analysis'] = {
                'memory_utilization_percent': memory_utilization,
                'cpu_utilization_percent': cpu_utilization,
                'container_memory_total_mb': round(container_memory_total, 2),
                'memory_pressure_critical': memory_utilization > 85,
                'memory_pressure_high': memory_utilization > 70,
                'cpu_pressure_high': cpu_utilization > 80,
                'performance_score': memory_analysis.get('efficiency_score', 0)
            }
            
            # Upgrade decision logic
            upgrade_needed = False
            upgrade_reasons = []
            recommended_instance = 't3.micro'
            
            if memory_utilization > 85:
                upgrade_needed = True
                upgrade_reasons.append("Memory utilization critically high (>85%)")
                recommended_instance = 't3.small'
            
            if memory_utilization > 70 and cpu_utilization > 70:
                upgrade_needed = True
                upgrade_reasons.append("Both memory and CPU pressure detected")
                recommended_instance = 't3.small'
            
            if container_memory_total > 700:  # 700MB+ for containers alone
                upgrade_needed = True
                upgrade_reasons.append("Container memory usage exceeds safe limits for t3.micro")
                recommended_instance = 't3.small'
            
            # Cost analysis for recommended instance
            if recommended_instance in self.instance_options:
                current_cost = self.t3_micro_specs['monthly_cost_usd']
                new_cost = self.instance_options[recommended_instance]['monthly_cost_usd']
                cost_increase = new_cost - current_cost
                cost_increase_percent = (cost_increase / current_cost) * 100
                
                upgrade_analysis['cost_analysis'] = {
                    'current_monthly_cost_usd': current_cost,
                    'recommended_monthly_cost_usd': new_cost,
                    'monthly_cost_increase_usd': cost_increase,
                    'cost_increase_percent': round(cost_increase_percent, 1),
                    'annual_cost_increase_usd': cost_increase * 12,
                    'roi_analysis': self._calculate_upgrade_roi(
                        current_cost, new_cost, memory_utilization, cpu_utilization
                    )
                }
            
            # Generate upgrade recommendations
            if upgrade_needed:
                benefits = [
                    f"Double memory capacity ({self.instance_options[recommended_instance]['memory_gb']}GB vs 1GB)",
                    "Reduced memory pressure and OOM risk",
                    "Better performance during traffic spikes",
                    "Room for future growth"
                ]
                
                if recommended_instance == 't3.small':
                    benefits.append("Same CPU credits per hour (24) but more baseline capacity")
                
                upgrade_analysis['upgrade_recommendations'] = [{
                    'recommended_instance': recommended_instance,
                    'reasons': upgrade_reasons,
                    'benefits': benefits,
                    'urgency': 'high' if memory_utilization > 85 else 'medium',
                    'downtime_estimate': '5-15 minutes',
                    'complexity': 'low'
                }]
                
                # Migration plan
                upgrade_analysis['migration_plan'] = {
                    'steps': [
                        "1. Create AMI snapshot of current instance",
                        "2. Stop current t3.micro instance",
                        "3. Change instance type to t3.small",
                        "4. Start instance and verify services",
                        "5. Update monitoring thresholds",
                        "6. Validate application performance"
                    ],
                    'estimated_downtime_minutes': 10,
                    'backup_required': True,
                    'rollback_plan': "Revert to t3.micro if issues arise",
                    'best_time': "During low traffic period"
                }
            
            else:
                upgrade_analysis['upgrade_recommendations'] = [{
                    'recommended_instance': 't3.micro',
                    'reasons': ['Current performance is acceptable'],
                    'benefits': ['Cost optimization - no unnecessary upgrade'],
                    'urgency': 'none',
                    'action': 'Continue monitoring for future needs'
                }]
            
            # Decision matrix
            upgrade_analysis['decision_matrix'] = {
                'upgrade_needed': upgrade_needed,
                'confidence_level': 'high' if len(upgrade_reasons) >= 2 else 'medium',
                'primary_constraint': 'memory' if memory_utilization > cpu_utilization else 'cpu',
                'business_impact': 'high' if memory_utilization > 90 else 'medium',
                'technical_risk': 'low',  # Instance type changes are low risk
                'financial_impact': upgrade_analysis.get('cost_analysis', {}).get('monthly_cost_increase_usd', 0)
            }
            
            self.logger.info(f"Instance upgrade analysis complete: upgrade_needed={upgrade_needed}")
            return upgrade_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing instance upgrade: {e}")
            return {'error': str(e)}

    def _calculate_upgrade_roi(self, current_cost: float, new_cost: float, 
                              memory_util: float, cpu_util: float) -> Dict[str, Any]:
        """Calculate ROI for instance upgrade"""
        try:
            cost_increase = new_cost - current_cost
            
            # Estimate performance improvement benefits
            # These are rough estimates based on reduced memory pressure
            stability_improvement = max(0, (memory_util - 70) * 2)  # % improvement in stability
            performance_improvement = max(0, (memory_util - 60) * 1.5)  # % improvement in performance
            
            # Estimate cost of downtime prevention (very rough)
            downtime_cost_per_hour = 50  # Estimated cost of service downtime
            downtime_hours_prevented_per_month = (memory_util - 70) / 10 if memory_util > 70 else 0
            downtime_cost_savings = downtime_hours_prevented_per_month * downtime_cost_per_hour
            
            roi_months = cost_increase / downtime_cost_savings if downtime_cost_savings > 0 else float('inf')
            
            return {
                'monthly_cost_increase': cost_increase,
                'stability_improvement_percent': round(stability_improvement, 1),
                'performance_improvement_percent': round(performance_improvement, 1),
                'estimated_downtime_cost_savings_monthly': round(downtime_cost_savings, 2),
                'roi_payback_months': round(roi_months, 1) if roi_months != float('inf') else None,
                'recommendation': 'Upgrade justified' if roi_months <= 12 else 'Monitor longer'
            }
            
        except Exception as e:
            return {'error': f'ROI calculation failed: {e}'}

    async def comprehensive_aws_analysis(self) -> Dict[str, Any]:
        """Run comprehensive AWS production analysis"""
        try:
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'instance_health': {},
                'memory_efficiency': {},
                'memory_prediction': {},
                'upgrade_analysis': {},
                'overall_status': 'unknown',
                'priority_actions': [],
                'summary': {}
            }
            
            # Run all analysis components
            self.logger.info("Running comprehensive AWS analysis...")
            
            # Instance health
            health_data = await self.monitor_ec2_instance_health()
            analysis['instance_health'] = health_data
            
            # Memory efficiency
            memory_eff = await self.analyze_memory_efficiency()
            analysis['memory_efficiency'] = memory_eff
            
            # Memory prediction
            memory_pred = await self.predict_memory_exhaustion()
            analysis['memory_prediction'] = memory_pred
            
            # Upgrade analysis
            upgrade_data = await self.suggest_instance_upgrade()
            analysis['upgrade_analysis'] = upgrade_data
            
            # Determine overall status
            health_status = health_data.get('health_status', 'unknown')
            memory_risk = memory_pred.get('risk_level', 'unknown')
            upgrade_needed = upgrade_data.get('decision_matrix', {}).get('upgrade_needed', False)
            
            if health_status == 'critical' or memory_risk == 'critical':
                overall_status = 'critical'
            elif health_status == 'degraded' or memory_risk == 'high' or upgrade_needed:
                overall_status = 'warning'
            elif health_status == 'healthy' and memory_risk in ['low', 'medium']:
                overall_status = 'healthy'
            else:
                overall_status = 'unknown'
            
            analysis['overall_status'] = overall_status
            
            # Priority actions
            priority_actions = []
            
            if memory_risk == 'critical':
                priority_actions.append({
                    'priority': 1,
                    'action': 'URGENT: Address memory exhaustion risk',
                    'category': 'memory',
                    'timeframe': 'immediate'
                })
            
            if upgrade_needed:
                urgency = upgrade_data.get('upgrade_recommendations', [{}])[0].get('urgency', 'medium')
                priority_actions.append({
                    'priority': 2 if urgency == 'high' else 3,
                    'action': f'Upgrade to {upgrade_data.get("upgrade_recommendations", [{}])[0].get("recommended_instance", "t3.small")}',
                    'category': 'infrastructure',
                    'timeframe': 'planned' if urgency == 'medium' else 'urgent'
                })
            
            if health_status in ['degraded', 'warning']:
                priority_actions.append({
                    'priority': 3,
                    'action': 'Investigate performance issues',
                    'category': 'performance',
                    'timeframe': 'short-term'
                })
            
            analysis['priority_actions'] = sorted(priority_actions, key=lambda x: x['priority'])
            
            # Summary
            analysis['summary'] = {
                'overall_status': overall_status,
                'health_score': self._calculate_health_score(health_data, memory_eff, memory_pred),
                'primary_concern': self._identify_primary_concern(health_data, memory_pred, upgrade_data),
                'recommended_actions': len(priority_actions),
                'monitoring_recommendations': self._generate_monitoring_recommendations(analysis)
            }
            
            self.logger.info(f"Comprehensive AWS analysis complete: {overall_status}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive AWS analysis: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _calculate_health_score(self, health_data: Dict, memory_eff: Dict, memory_pred: Dict) -> float:
        """Calculate overall health score (0-100)"""
        try:
            scores = []
            
            # Health status score
            health_status = health_data.get('health_status', 'unknown')
            health_score = {
                'healthy': 100,
                'warning': 70,
                'degraded': 40,
                'critical': 20,
                'unknown': 50
            }.get(health_status, 50)
            scores.append(health_score)
            
            # Memory efficiency score
            memory_score = memory_eff.get('efficiency_score', 50)
            scores.append(memory_score)
            
            # Memory risk score
            risk_level = memory_pred.get('risk_level', 'unknown')
            risk_score = {
                'low': 100,
                'medium': 70,
                'high': 40,
                'critical': 20,
                'unknown': 50
            }.get(risk_level, 50)
            scores.append(risk_score)
            
            return round(sum(scores) / len(scores), 1)
            
        except:
            return 50.0

    def _identify_primary_concern(self, health_data: Dict, memory_pred: Dict, upgrade_data: Dict) -> str:
        """Identify the primary concern requiring attention"""
        try:
            # Check for critical issues first
            if memory_pred.get('risk_level') == 'critical':
                return 'memory_exhaustion_risk'
            
            if health_data.get('health_status') == 'critical':
                return 'system_health_critical'
            
            if upgrade_data.get('decision_matrix', {}).get('upgrade_needed'):
                memory_util = upgrade_data.get('performance_analysis', {}).get('memory_utilization_percent', 0)
                if memory_util > 85:
                    return 'memory_pressure_requires_upgrade'
            
            # Check for warning-level issues
            if memory_pred.get('risk_level') == 'high':
                return 'memory_growth_trend'
            
            if health_data.get('health_status') == 'degraded':
                return 'performance_degradation'
            
            return 'monitoring_and_optimization'
            
        except:
            return 'unknown'

    def _generate_monitoring_recommendations(self, analysis: Dict) -> List[str]:
        """Generate monitoring recommendations based on analysis"""
        recommendations = []
        
        try:
            overall_status = analysis.get('overall_status', 'unknown')
            
            if overall_status == 'critical':
                recommendations.extend([
                    "Increase monitoring frequency to every 5 minutes",
                    "Set up immediate alerts for memory and CPU thresholds",
                    "Enable detailed CloudWatch monitoring"
                ])
            elif overall_status == 'warning':
                recommendations.extend([
                    "Monitor memory trends closely",
                    "Set up predictive alerts for resource exhaustion",
                    "Review container resource allocation"
                ])
            else:
                recommendations.extend([
                    "Continue current monitoring schedule",
                    "Implement trend analysis for capacity planning",
                    "Set up monthly performance reviews"
                ])
            
            return recommendations
            
        except:
            return ["Enable comprehensive monitoring"]

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS Production Monitor')
    parser.add_argument('--health', action='store_true',
                       help='Check EC2 instance health')
    parser.add_argument('--memory', action='store_true',
                       help='Analyze memory efficiency')
    parser.add_argument('--predict', action='store_true',
                       help='Predict memory exhaustion')
    parser.add_argument('--upgrade', action='store_true',
                       help='Analyze instance upgrade needs')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive AWS analysis')
    
    args = parser.parse_args()
    
    monitor = AWSProductionMonitor()
    
    if args.health:
        result = await monitor.monitor_ec2_instance_health()
        print("🏥 EC2 Instance Health Check")
        print("=" * 40)
        print(f"Status: {result.get('health_status', 'unknown').upper()}")
        
        metadata = result.get('instance_metadata', {})
        if metadata:
            print(f"Instance: {metadata.get('instance_type', 'unknown')}")
            print(f"Region: {metadata.get('region', 'unknown')}")
            print(f"Uptime: {metadata.get('uptime_hours', 0):.1f} hours")
        
        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
    
    elif args.memory:
        result = await monitor.analyze_memory_efficiency()
        print("🧠 Memory Efficiency Analysis")
        print("=" * 40)
        print(f"Efficiency Score: {result.get('efficiency_score', 0)}/100")
        
        memory_analysis = result.get('memory_analysis', {})
        print(f"System Memory: {memory_analysis.get('system_memory_utilization', 0):.1f}%")
        print(f"Container Memory: {memory_analysis.get('container_memory_total_mb', 0):.1f}MB")
        
        opportunities = result.get('optimization_opportunities', [])
        if opportunities:
            print("\nOptimization Opportunities:")
            for opp in opportunities:
                print(f"  • {opp.get('description', 'Unknown')}")
    
    elif args.predict:
        result = await monitor.predict_memory_exhaustion()
        print("🔮 Memory Exhaustion Prediction")
        print("=" * 40)
        print(f"Risk Level: {result.get('risk_level', 'unknown').upper()}")
        
        prediction = result.get('prediction', {})
        if prediction.get('hours_to_memory_exhaustion'):
            hours = prediction['hours_to_memory_exhaustion']
            print(f"Time to Exhaustion: {hours:.1f} hours ({hours/24:.1f} days)")
        
        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
    
    elif args.upgrade:
        result = await monitor.suggest_instance_upgrade()
        print("⬆️ Instance Upgrade Analysis")
        print("=" * 40)
        
        decision = result.get('decision_matrix', {})
        print(f"Upgrade Needed: {'Yes' if decision.get('upgrade_needed') else 'No'}")
        
        if decision.get('upgrade_needed'):
            rec = result.get('upgrade_recommendations', [{}])[0]
            print(f"Recommended: {rec.get('recommended_instance', 'unknown')}")
            print(f"Urgency: {rec.get('urgency', 'unknown')}")
            
            cost = result.get('cost_analysis', {})
            if cost:
                print(f"Cost Increase: ${cost.get('monthly_cost_increase_usd', 0):.2f}/month")
        
    elif args.comprehensive:
        result = await monitor.comprehensive_aws_analysis()
        print("🔍 COMPREHENSIVE AWS ANALYSIS")
        print("=" * 50)
        
        summary = result.get('summary', {})
        print(f"Overall Status: {summary.get('overall_status', 'unknown').upper()}")
        print(f"Health Score: {summary.get('health_score', 0)}/100")
        print(f"Primary Concern: {summary.get('primary_concern', 'unknown').replace('_', ' ').title()}")
        
        actions = result.get('priority_actions', [])
        if actions:
            print("\nPriority Actions:")
            for action in actions[:3]:  # Show top 3
                print(f"  {action['priority']}. {action['action']} ({action['timeframe']})")
        
        print(f"\nDetailed analysis saved to logs")
    
    else:
        # Default: show current AWS status
        print("☁️ AWS Production Monitor Status")
        print("=" * 40)
        print(f"Region: {monitor.aws_region}")
        print(f"Instance ID: {monitor.instance_id or 'Not detected'}")
        print(f"Instance Type: {monitor.t3_micro_specs['instance_type']}")
        print(f"Memory Limit: {monitor.t3_micro_specs['memory_mb']}MB")
        print(f"CPU Credits/Hour: {monitor.t3_micro_specs['cpu_credits_per_hour']}")
        print(f"Monthly Cost: ${monitor.t3_micro_specs['monthly_cost_usd']}")
        
        print("\nMonitoring Capabilities:")
        print(f"  EC2 Client: {'✅' if monitor.ec2_client else '❌'}")
        print(f"  CloudWatch Client: {'✅' if monitor.cloudwatch_client else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())