#!/usr/bin/env python3
"""
Resource Analyzer - Analyze container resource usage patterns and trends
Provides memory trend analysis, bottleneck identification, and optimization recommendations.
"""

import asyncio
import time
import json
import logging
import statistics
import docker
import psutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os
import pickle

@dataclass
class ResourceSnapshot:
    """Single resource usage snapshot"""
    timestamp: str
    container_name: str
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    network_rx_mb: float
    network_tx_mb: float
    disk_read_mb: float
    disk_write_mb: float
    container_status: str

@dataclass
class TrendAnalysis:
    """Resource usage trend analysis"""
    metric_name: str
    timeframe_hours: int
    current_value: float
    average_value: float
    min_value: float
    max_value: float
    trend_direction: str  # increasing, decreasing, stable
    trend_percentage: float
    volatility: float
    predicted_next_hour: float
    alert_level: str  # normal, warning, critical

@dataclass
class BottleneckAnalysis:
    """Resource bottleneck identification"""
    bottleneck_type: str  # memory, cpu, disk, network
    severity: str  # low, medium, high, critical
    affected_containers: List[str]
    root_cause: str
    impact_description: str
    recommendation: str
    estimated_improvement: str

@dataclass
class OptimizationRecommendation:
    """Resource optimization recommendation"""
    category: str  # memory, cpu, configuration, scaling
    priority: str  # low, medium, high, critical
    title: str
    description: str
    implementation_steps: List[str]
    expected_benefit: str
    estimated_effort: str
    cost_impact: str

class ResourceAnalyzer:
    """Analyze container resource usage patterns and provide optimization insights"""
    
    def __init__(self, log_dir: str = "/Users/screener-m3/projects/crypto-assistant/data/logs"):
        """Initialize resource analyzer"""
        self.log_dir = log_dir
        self.data_dir = os.path.join(os.path.dirname(log_dir), "resource_data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.setup_logging()
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.error(f"Failed to connect to Docker: {e}")
            self.docker_client = None
        
        # Historical data storage
        self.historical_data: List[ResourceSnapshot] = []
        self.max_data_points = 2880  # 24 hours at 30-second intervals
        
        # Load existing data
        self._load_historical_data()
        
        # AWS t3.micro specifications
        self.aws_t3_micro = {
            'total_memory_mb': 1024,
            'available_memory_mb': 824,  # After OS overhead
            'cpu_credits_per_hour': 12,
            'baseline_cpu_percent': 20,
            'network_baseline_mbps': 5,
            'monthly_cost_usd': 8.50
        }
        
        # Optimization thresholds
        self.thresholds = {
            'memory_warning': 70,
            'memory_critical': 85,
            'cpu_sustained_high': 80,
            'cpu_credit_depletion_risk': 90,
            'trend_volatility_high': 20,
            'prediction_confidence_threshold': 0.8
        }
        
        self.logger.info("Resource Analyzer initialized")

    def setup_logging(self):
        """Setup logging system"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, "resource_analyzer.log")
        
        self.logger = logging.getLogger('resource_analyzer')
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

    def _load_historical_data(self):
        """Load historical data from disk"""
        data_file = os.path.join(self.data_dir, "historical_data.pkl")
        
        try:
            if os.path.exists(data_file):
                with open(data_file, 'rb') as f:
                    self.historical_data = pickle.load(f)
                self.logger.info(f"Loaded {len(self.historical_data)} historical data points")
            else:
                self.historical_data = []
                self.logger.info("No historical data found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            self.historical_data = []

    def _save_historical_data(self):
        """Save historical data to disk"""
        data_file = os.path.join(self.data_dir, "historical_data.pkl")
        
        try:
            with open(data_file, 'wb') as f:
                pickle.dump(self.historical_data, f)
        except Exception as e:
            self.logger.error(f"Error saving historical data: {e}")

    async def collect_resource_snapshot(self) -> List[ResourceSnapshot]:
        """Collect current resource usage snapshot for all containers"""
        snapshots = []
        
        try:
            if not self.docker_client:
                return snapshots
            
            containers = self.docker_client.containers.list(all=True)
            timestamp = datetime.now().isoformat()
            
            for container in containers:
                try:
                    # Skip if not crypto-assistant related
                    if not any(keyword in container.name.lower() 
                              for keyword in ['crypto', 'telegram', 'market', 'redis', 'bot']):
                        continue
                    
                    # Get container stats
                    if container.status != 'running':
                        snapshot = ResourceSnapshot(
                            timestamp=timestamp,
                            container_name=container.name,
                            cpu_percent=0.0,
                            memory_usage_mb=0.0,
                            memory_percent=0.0,
                            network_rx_mb=0.0,
                            network_tx_mb=0.0,
                            disk_read_mb=0.0,
                            disk_write_mb=0.0,
                            container_status=container.status
                        )
                        snapshots.append(snapshot)
                        continue
                    
                    stats = container.stats(stream=False)
                    
                    # Memory metrics
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 0)
                    memory_usage_mb = memory_usage / 1024 / 1024
                    memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
                    
                    # CPU metrics
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    cpu_percent = (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0
                    
                    # Network metrics
                    networks = stats.get('networks', {})
                    network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
                    network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
                    network_rx_mb = network_rx / 1024 / 1024
                    network_tx_mb = network_tx / 1024 / 1024
                    
                    # Disk metrics (if available)
                    disk_stats = stats.get('blkio_stats', {})
                    disk_read = sum(item.get('value', 0) for item in 
                                   disk_stats.get('io_service_bytes_recursive', [])
                                   if item.get('op') == 'Read')
                    disk_write = sum(item.get('value', 0) for item in 
                                    disk_stats.get('io_service_bytes_recursive', [])
                                    if item.get('op') == 'Write')
                    disk_read_mb = disk_read / 1024 / 1024
                    disk_write_mb = disk_write / 1024 / 1024
                    
                    snapshot = ResourceSnapshot(
                        timestamp=timestamp,
                        container_name=container.name,
                        cpu_percent=round(cpu_percent, 2),
                        memory_usage_mb=round(memory_usage_mb, 2),
                        memory_percent=round(memory_percent, 2),
                        network_rx_mb=round(network_rx_mb, 2),
                        network_tx_mb=round(network_tx_mb, 2),
                        disk_read_mb=round(disk_read_mb, 2),
                        disk_write_mb=round(disk_write_mb, 2),
                        container_status=container.status
                    )
                    
                    snapshots.append(snapshot)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting stats for {container.name}: {e}")
                    continue
            
            # Add to historical data
            self.historical_data.extend(snapshots)
            
            # Trim historical data if needed
            if len(self.historical_data) > self.max_data_points:
                self.historical_data = self.historical_data[-self.max_data_points:]
            
            # Save periodically
            if len(self.historical_data) % 100 == 0:
                self._save_historical_data()
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Error collecting resource snapshots: {e}")
            return []

    def analyze_memory_trends(self, timeframe_hours: int = 24) -> Dict[str, TrendAnalysis]:
        """Analyze memory usage trends and predict future usage"""
        trends = {}
        
        try:
            # Filter data by timeframe
            cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
            relevant_data = [
                snapshot for snapshot in self.historical_data
                if datetime.fromisoformat(snapshot.timestamp) >= cutoff_time
            ]
            
            if len(relevant_data) < 10:
                self.logger.warning(f"Insufficient data for trend analysis ({len(relevant_data)} points)")
                return trends
            
            # Group by container
            container_data = {}
            for snapshot in relevant_data:
                if snapshot.container_name not in container_data:
                    container_data[snapshot.container_name] = []
                container_data[snapshot.container_name].append(snapshot)
            
            # Analyze trends for each container
            for container_name, snapshots in container_data.items():
                if len(snapshots) < 5:
                    continue
                
                # Memory usage analysis
                memory_values = [s.memory_usage_mb for s in snapshots]
                memory_percentages = [s.memory_percent for s in snapshots]
                
                # Calculate trend metrics
                current_memory = memory_values[-1]
                avg_memory = statistics.mean(memory_values)
                min_memory = min(memory_values)
                max_memory = max(memory_values)
                
                # Calculate trend direction and percentage
                if len(memory_values) >= 10:
                    recent_avg = statistics.mean(memory_values[-5:])
                    earlier_avg = statistics.mean(memory_values[:5])
                    trend_percentage = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                    
                    if trend_percentage > 5:
                        trend_direction = "increasing"
                    elif trend_percentage < -5:
                        trend_direction = "decreasing"
                    else:
                        trend_direction = "stable"
                else:
                    trend_percentage = 0
                    trend_direction = "stable"
                
                # Calculate volatility (standard deviation as percentage of mean)
                volatility = (statistics.stdev(memory_values) / avg_memory * 100) if avg_memory > 0 else 0
                
                # Simple linear prediction for next hour
                if len(memory_values) >= 10:
                    # Use last 10 points for prediction
                    x_values = list(range(len(memory_values[-10:])))
                    y_values = memory_values[-10:]
                    
                    # Simple linear regression
                    n = len(x_values)
                    sum_x = sum(x_values)
                    sum_y = sum(y_values)
                    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
                    sum_x2 = sum(x * x for x in x_values)
                    
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    predicted_next = current_memory + slope * 2  # Predict 2 intervals ahead (1 hour if 30min intervals)
                else:
                    predicted_next = current_memory
                
                # Determine alert level
                current_percentage = memory_percentages[-1] if memory_percentages else 0
                if current_percentage > self.thresholds['memory_critical'] or predicted_next > max_memory * 1.2:
                    alert_level = "critical"
                elif current_percentage > self.thresholds['memory_warning'] or trend_direction == "increasing":
                    alert_level = "warning"
                else:
                    alert_level = "normal"
                
                trends[container_name] = TrendAnalysis(
                    metric_name="memory_usage_mb",
                    timeframe_hours=timeframe_hours,
                    current_value=current_memory,
                    average_value=round(avg_memory, 2),
                    min_value=min_memory,
                    max_value=max_memory,
                    trend_direction=trend_direction,
                    trend_percentage=round(trend_percentage, 2),
                    volatility=round(volatility, 2),
                    predicted_next_hour=round(predicted_next, 2),
                    alert_level=alert_level
                )
            
            self.logger.info(f"Analyzed memory trends for {len(trends)} containers")
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing memory trends: {e}")
            return {}

    def identify_resource_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Identify containers causing resource bottlenecks"""
        bottlenecks = []
        
        try:
            if len(self.historical_data) < 20:
                return bottlenecks
            
            # Get recent data (last hour)
            recent_time = datetime.now() - timedelta(hours=1)
            recent_data = [
                snapshot for snapshot in self.historical_data
                if datetime.fromisoformat(snapshot.timestamp) >= recent_time
            ]
            
            if not recent_data:
                return bottlenecks
            
            # Group by container
            container_stats = {}
            for snapshot in recent_data:
                if snapshot.container_name not in container_stats:
                    container_stats[snapshot.container_name] = []
                container_stats[snapshot.container_name].append(snapshot)
            
            # Analyze each container for bottlenecks
            for container_name, snapshots in container_stats.items():
                if len(snapshots) < 5:
                    continue
                
                # Memory bottleneck analysis
                avg_memory_percent = statistics.mean([s.memory_percent for s in snapshots])
                max_memory_percent = max([s.memory_percent for s in snapshots])
                
                if avg_memory_percent > 80:
                    severity = "critical" if avg_memory_percent > 90 else "high"
                    bottlenecks.append(BottleneckAnalysis(
                        bottleneck_type="memory",
                        severity=severity,
                        affected_containers=[container_name],
                        root_cause=f"Container consistently using {avg_memory_percent:.1f}% of allocated memory",
                        impact_description=f"High memory usage may cause OOM kills and service instability",
                        recommendation=f"Increase memory limit or optimize application memory usage",
                        estimated_improvement=f"Reducing to 70% would free {(avg_memory_percent - 70) * 10:.0f}MB"
                    ))
                
                # CPU bottleneck analysis
                avg_cpu_percent = statistics.mean([s.cpu_percent for s in snapshots])
                max_cpu_percent = max([s.cpu_percent for s in snapshots])
                
                if avg_cpu_percent > 80:
                    severity = "critical" if avg_cpu_percent > 95 else "high"
                    bottlenecks.append(BottleneckAnalysis(
                        bottleneck_type="cpu",
                        severity=severity,
                        affected_containers=[container_name],
                        root_cause=f"Container averaging {avg_cpu_percent:.1f}% CPU usage",
                        impact_description="High CPU usage on t3.micro will exhaust CPU credits",
                        recommendation="Optimize application performance or upgrade instance type",
                        estimated_improvement="CPU optimization could reduce costs and improve response times"
                    ))
                
                # Network bottleneck analysis
                total_network_mb = sum([s.network_rx_mb + s.network_tx_mb for s in snapshots])
                if total_network_mb > 100:  # 100MB in last hour
                    bottlenecks.append(BottleneckAnalysis(
                        bottleneck_type="network",
                        severity="medium",
                        affected_containers=[container_name],
                        root_cause=f"High network usage: {total_network_mb:.1f}MB in last hour",
                        impact_description="High network usage may indicate inefficient data transfer",
                        recommendation="Review API calls and data transfer patterns",
                        estimated_improvement="Optimizing network usage could reduce latency"
                    ))
            
            # System-wide bottleneck analysis
            total_memory_usage = sum([
                statistics.mean([s.memory_usage_mb for s in snapshots])
                for snapshots in container_stats.values()
            ])
            
            if total_memory_usage > self.aws_t3_micro['available_memory_mb'] * 0.85:
                bottlenecks.append(BottleneckAnalysis(
                    bottleneck_type="memory",
                    severity="critical",
                    affected_containers=list(container_stats.keys()),
                    root_cause=f"System memory usage {total_memory_usage:.1f}MB exceeds safe threshold",
                    impact_description="System approaching memory limits, risk of OOM conditions",
                    recommendation="Upgrade to t3.small or optimize container memory usage",
                    estimated_improvement="Upgrading would double available memory"
                ))
            
            self.logger.info(f"Identified {len(bottlenecks)} resource bottlenecks")
            return bottlenecks
            
        except Exception as e:
            self.logger.error(f"Error identifying bottlenecks: {e}")
            return []

    def aws_cost_optimization_analysis(self) -> Dict[str, Any]:
        """Analyze if current usage justifies t3.micro or needs upgrade"""
        try:
            analysis = {
                'current_instance': 't3.micro',
                'current_monthly_cost': self.aws_t3_micro['monthly_cost_usd'],
                'usage_analysis': {},
                'upgrade_recommendations': {},
                'cost_benefit_analysis': {},
                'optimization_opportunities': []
            }
            
            # Analyze recent usage patterns
            if len(self.historical_data) < 50:
                analysis['warning'] = "Insufficient data for comprehensive analysis"
                return analysis
            
            # Get last 24 hours of data
            recent_time = datetime.now() - timedelta(hours=24)
            recent_data = [
                snapshot for snapshot in self.historical_data
                if datetime.fromisoformat(snapshot.timestamp) >= recent_time
            ]
            
            if not recent_data:
                return analysis
            
            # Calculate usage statistics
            total_memory_usage = []
            total_cpu_usage = []
            
            # Group by timestamp to get system totals
            timestamp_groups = {}
            for snapshot in recent_data:
                ts = snapshot.timestamp
                if ts not in timestamp_groups:
                    timestamp_groups[ts] = []
                timestamp_groups[ts].append(snapshot)
            
            for timestamp, snapshots in timestamp_groups.items():
                running_snapshots = [s for s in snapshots if s.container_status == 'running']
                if running_snapshots:
                    total_memory = sum(s.memory_usage_mb for s in running_snapshots)
                    avg_cpu = statistics.mean([s.cpu_percent for s in running_snapshots])
                    
                    total_memory_usage.append(total_memory)
                    total_cpu_usage.append(avg_cpu)
            
            if not total_memory_usage:
                return analysis
            
            # Usage analysis
            avg_memory_usage = statistics.mean(total_memory_usage)
            max_memory_usage = max(total_memory_usage)
            avg_cpu_usage = statistics.mean(total_cpu_usage)
            max_cpu_usage = max(total_cpu_usage)
            
            memory_utilization = (avg_memory_usage / self.aws_t3_micro['available_memory_mb']) * 100
            peak_memory_utilization = (max_memory_usage / self.aws_t3_micro['available_memory_mb']) * 100
            
            analysis['usage_analysis'] = {
                'avg_memory_usage_mb': round(avg_memory_usage, 2),
                'max_memory_usage_mb': round(max_memory_usage, 2),
                'avg_memory_utilization_percent': round(memory_utilization, 2),
                'peak_memory_utilization_percent': round(peak_memory_utilization, 2),
                'avg_cpu_usage_percent': round(avg_cpu_usage, 2),
                'max_cpu_usage_percent': round(max_cpu_usage, 2),
                'memory_pressure_risk': 'high' if peak_memory_utilization > 85 else 'medium' if peak_memory_utilization > 70 else 'low'
            }
            
            # Upgrade recommendations
            upgrade_needed = False
            upgrade_reason = []
            
            if peak_memory_utilization > 85:
                upgrade_needed = True
                upgrade_reason.append("Memory usage exceeds safe limits")
            
            if avg_cpu_usage > 70:
                upgrade_needed = True
                upgrade_reason.append("High CPU usage will exhaust CPU credits")
            
            if memory_utilization > 80:
                upgrade_needed = True
                upgrade_reason.append("Average memory usage too high for reliable operation")
            
            # t3.small comparison
            t3_small_cost = 17.0  # Approximate monthly cost
            cost_increase = t3_small_cost - self.aws_t3_micro['monthly_cost_usd']
            cost_increase_percent = (cost_increase / self.aws_t3_micro['monthly_cost_usd']) * 100
            
            analysis['upgrade_recommendations'] = {
                'upgrade_needed': upgrade_needed,
                'reasons': upgrade_reason,
                'recommended_instance': 't3.small' if upgrade_needed else 't3.micro',
                'new_monthly_cost': t3_small_cost if upgrade_needed else self.aws_t3_micro['monthly_cost_usd'],
                'cost_increase': cost_increase if upgrade_needed else 0,
                'cost_increase_percent': cost_increase_percent if upgrade_needed else 0
            }
            
            # Cost-benefit analysis
            benefits_of_upgrade = []
            if upgrade_needed:
                benefits_of_upgrade = [
                    "Double the memory (2GB vs 1GB)",
                    "Higher CPU baseline performance",
                    "Reduced risk of OOM conditions",
                    "Better performance during peak loads",
                    "More room for future growth"
                ]
            
            analysis['cost_benefit_analysis'] = {
                'monthly_cost_increase': cost_increase if upgrade_needed else 0,
                'benefits': benefits_of_upgrade,
                'payback_period': 'Immediate' if upgrade_needed else 'N/A',
                'risk_reduction': 'High' if upgrade_needed else 'Low'
            }
            
            # Optimization opportunities
            optimization_opportunities = []
            
            if avg_memory_usage < 300:  # Less than 300MB average
                optimization_opportunities.append({
                    'type': 'memory_optimization',
                    'description': 'Current memory usage is low, could optimize container limits',
                    'potential_savings': 'Could reduce memory allocation by 20-30%'
                })
            
            if max_cpu_usage < 50:
                optimization_opportunities.append({
                    'type': 'cpu_optimization',
                    'description': 'CPU usage is well within limits',
                    'potential_savings': 'Current instance size is appropriate'
                })
            
            analysis['optimization_opportunities'] = optimization_opportunities
            
            self.logger.info(f"AWS cost optimization analysis complete: upgrade_needed={upgrade_needed}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in AWS cost optimization analysis: {e}")
            return {'error': str(e)}

    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        try:
            # Analyze recent trends
            memory_trends = self.analyze_memory_trends(timeframe_hours=24)
            bottlenecks = self.identify_resource_bottlenecks()
            cost_analysis = self.aws_cost_optimization_analysis()
            
            # Memory optimization recommendations
            for container, trend in memory_trends.items():
                if trend.alert_level in ['warning', 'critical']:
                    if trend.trend_direction == 'increasing':
                        recommendations.append(OptimizationRecommendation(
                            category='memory',
                            priority='high' if trend.alert_level == 'critical' else 'medium',
                            title=f'Memory leak detection in {container}',
                            description=f'Memory usage increasing {trend.trend_percentage:.1f}% over 24h',
                            implementation_steps=[
                                'Review application logs for memory leaks',
                                'Profile application memory usage',
                                'Implement memory monitoring alerts',
                                'Consider restarting container if trend continues'
                            ],
                            expected_benefit='Prevent memory exhaustion and improve stability',
                            estimated_effort='2-4 hours',
                            cost_impact='Prevents potential downtime costs'
                        ))
                
                if trend.volatility > 20:
                    recommendations.append(OptimizationRecommendation(
                        category='memory',
                        priority='medium',
                        title=f'Memory usage volatility in {container}',
                        description=f'High memory volatility ({trend.volatility:.1f}%) indicates inefficient usage',
                        implementation_steps=[
                            'Analyze memory allocation patterns',
                            'Implement garbage collection tuning',
                            'Review data processing algorithms',
                            'Consider memory pooling strategies'
                        ],
                        expected_benefit='More predictable memory usage and better performance',
                        estimated_effort='4-8 hours',
                        cost_impact='Improved resource efficiency'
                    ))
            
            # CPU optimization recommendations
            high_cpu_containers = []
            if len(self.historical_data) > 20:
                recent_data = self.historical_data[-20:]
                container_cpu = {}
                
                for snapshot in recent_data:
                    if snapshot.container_name not in container_cpu:
                        container_cpu[snapshot.container_name] = []
                    container_cpu[snapshot.container_name].append(snapshot.cpu_percent)
                
                for container, cpu_values in container_cpu.items():
                    avg_cpu = statistics.mean(cpu_values)
                    if avg_cpu > 60:
                        high_cpu_containers.append((container, avg_cpu))
            
            for container, avg_cpu in high_cpu_containers:
                recommendations.append(OptimizationRecommendation(
                    category='cpu',
                    priority='high' if avg_cpu > 80 else 'medium',
                    title=f'High CPU usage in {container}',
                    description=f'Average CPU usage {avg_cpu:.1f}% may exhaust t3.micro CPU credits',
                    implementation_steps=[
                        'Profile application CPU usage',
                        'Optimize algorithms and database queries',
                        'Implement caching strategies',
                        'Consider async processing for heavy tasks'
                    ],
                    expected_benefit='Reduced CPU credits consumption and better response times',
                    estimated_effort='4-12 hours',
                    cost_impact='Prevents need for instance upgrade'
                ))
            
            # Infrastructure optimization based on cost analysis
            if cost_analysis.get('upgrade_recommendations', {}).get('upgrade_needed'):
                reasons = cost_analysis['upgrade_recommendations'].get('reasons', [])
                recommendations.append(OptimizationRecommendation(
                    category='scaling',
                    priority='critical',
                    title='AWS instance upgrade required',
                    description=f'Current usage patterns require upgrade: {", ".join(reasons)}',
                    implementation_steps=[
                        'Plan maintenance window for upgrade',
                        'Backup current configuration',
                        'Upgrade to t3.small instance',
                        'Update monitoring thresholds',
                        'Validate performance improvements'
                    ],
                    expected_benefit='Eliminate resource constraints and improve reliability',
                    estimated_effort='2-4 hours',
                    cost_impact=f'+${cost_analysis["upgrade_recommendations"].get("cost_increase", 0):.2f}/month'
                ))
            
            # Configuration optimization
            if bottlenecks:
                memory_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == 'memory']
                if memory_bottlenecks:
                    recommendations.append(OptimizationRecommendation(
                        category='configuration',
                        priority='high',
                        title='Docker memory limits optimization',
                        description='Multiple containers showing memory pressure',
                        implementation_steps=[
                            'Review current Docker memory limits',
                            'Redistribute memory allocation based on usage patterns',
                            'Implement memory monitoring in docker-compose',
                            'Set up automated alerts for memory pressure'
                        ],
                        expected_benefit='Better resource distribution and reduced OOM risk',
                        estimated_effort='1-2 hours',
                        cost_impact='Improved efficiency without additional costs'
                    ))
            
            # General optimization if no critical issues
            if not recommendations:
                recommendations.append(OptimizationRecommendation(
                    category='monitoring',
                    priority='low',
                    title='Implement proactive monitoring',
                    description='System is running well, enhance monitoring for early issue detection',
                    implementation_steps=[
                        'Set up trend-based alerting',
                        'Implement resource usage dashboards',
                        'Create automated health reports',
                        'Establish baseline performance metrics'
                    ],
                    expected_benefit='Early issue detection and improved system visibility',
                    estimated_effort='2-3 hours',
                    cost_impact='Prevents future issues and downtime'
                ))
            
            self.logger.info(f"Generated {len(recommendations)} optimization recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating optimization recommendations: {e}")
            return []

    async def continuous_data_collection(self, interval_seconds: int = 30):
        """Continuously collect resource data for trend analysis"""
        self.logger.info(f"Starting continuous data collection (interval: {interval_seconds}s)")
        
        while True:
            try:
                snapshots = await self.collect_resource_snapshot()
                
                if snapshots:
                    self.logger.info(f"Collected {len(snapshots)} resource snapshots")
                    
                    # Periodic analysis
                    if len(self.historical_data) % 120 == 0:  # Every hour (if 30s intervals)
                        trends = self.analyze_memory_trends()
                        bottlenecks = self.identify_resource_bottlenecks()
                        
                        if bottlenecks:
                            self.logger.warning(f"Detected {len(bottlenecks)} resource bottlenecks")
                
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Data collection stopped by user")
                self._save_historical_data()
                break
            except Exception as e:
                self.logger.error(f"Error in data collection loop: {e}")
                await asyncio.sleep(interval_seconds)

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Resource Analyzer')
    parser.add_argument('--collect', action='store_true',
                       help='Start continuous data collection')
    parser.add_argument('--interval', type=int, default=30,
                       help='Collection interval in seconds (default: 30)')
    parser.add_argument('--trends', type=int, default=24,
                       help='Analyze memory trends for specified hours (default: 24)')
    parser.add_argument('--bottlenecks', action='store_true',
                       help='Identify resource bottlenecks')
    parser.add_argument('--aws-analysis', action='store_true',
                       help='Run AWS cost optimization analysis')
    parser.add_argument('--recommendations', action='store_true',
                       help='Generate optimization recommendations')
    parser.add_argument('--report', action='store_true',
                       help='Generate comprehensive analysis report')
    
    args = parser.parse_args()
    
    analyzer = ResourceAnalyzer()
    
    if args.collect:
        await analyzer.continuous_data_collection(args.interval)
    elif args.trends:
        trends = analyzer.analyze_memory_trends(args.trends)
        print(f"Memory Trends Analysis ({args.trends} hours)")
        print("=" * 50)
        for container, trend in trends.items():
            print(f"\n📊 {container}")
            print(f"   Current: {trend.current_value:.1f}MB")
            print(f"   Average: {trend.average_value:.1f}MB")
            print(f"   Trend: {trend.trend_direction} ({trend.trend_percentage:+.1f}%)")
            print(f"   Predicted: {trend.predicted_next_hour:.1f}MB")
            print(f"   Alert: {trend.alert_level.upper()}")
    elif args.bottlenecks:
        bottlenecks = analyzer.identify_resource_bottlenecks()
        print("Resource Bottleneck Analysis")
        print("=" * 50)
        if bottlenecks:
            for bottleneck in bottlenecks:
                severity_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
                print(f"\n{severity_emoji.get(bottleneck.severity, '⚪')} {bottleneck.bottleneck_type.upper()} - {bottleneck.severity.upper()}")
                print(f"   Affected: {', '.join(bottleneck.affected_containers)}")
                print(f"   Cause: {bottleneck.root_cause}")
                print(f"   Impact: {bottleneck.impact_description}")
                print(f"   Recommendation: {bottleneck.recommendation}")
        else:
            print("✅ No resource bottlenecks detected")
    elif args.aws_analysis:
        analysis = analyzer.aws_cost_optimization_analysis()
        print(json.dumps(analysis, indent=2))
    elif args.recommendations:
        recommendations = analyzer.generate_optimization_recommendations()
        print("Optimization Recommendations")
        print("=" * 50)
        for rec in recommendations:
            priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
            print(f"\n{priority_emoji.get(rec.priority, '⚪')} {rec.title} [{rec.priority.upper()}]")
            print(f"   Category: {rec.category}")
            print(f"   Description: {rec.description}")
            print(f"   Expected Benefit: {rec.expected_benefit}")
            print(f"   Effort: {rec.estimated_effort}")
            print(f"   Cost Impact: {rec.cost_impact}")
    elif args.report:
        # Comprehensive report
        print("🔍 COMPREHENSIVE RESOURCE ANALYSIS REPORT")
        print("=" * 60)
        
        # Basic stats
        snapshots = await analyzer.collect_resource_snapshot()
        print(f"📊 Current Status: {len(snapshots)} containers monitored")
        print(f"📈 Historical Data: {len(analyzer.historical_data)} data points")
        
        # Memory trends
        trends = analyzer.analyze_memory_trends()
        print(f"\n📈 Memory Trends ({len(trends)} containers)")
        for container, trend in trends.items():
            alert_emoji = {"normal": "✅", "warning": "⚠️", "critical": "🚨"}
            print(f"   {alert_emoji.get(trend.alert_level, '⚪')} {container}: {trend.current_value:.1f}MB ({trend.trend_direction})")
        
        # Bottlenecks
        bottlenecks = analyzer.identify_resource_bottlenecks()
        print(f"\n⚠️ Bottlenecks: {len(bottlenecks)} detected")
        for bottleneck in bottlenecks:
            print(f"   🔴 {bottleneck.bottleneck_type}: {bottleneck.severity}")
        
        # AWS analysis
        aws_analysis = analyzer.aws_cost_optimization_analysis()
        usage_analysis = aws_analysis.get('usage_analysis', {})
        upgrade_needed = aws_analysis.get('upgrade_recommendations', {}).get('upgrade_needed', False)
        
        print(f"\n💰 AWS Analysis")
        print(f"   Memory Usage: {usage_analysis.get('avg_memory_utilization_percent', 0):.1f}%")
        print(f"   CPU Usage: {usage_analysis.get('avg_cpu_usage_percent', 0):.1f}%")
        print(f"   Upgrade Needed: {'Yes' if upgrade_needed else 'No'}")
        
        # Recommendations
        recommendations = analyzer.generate_optimization_recommendations()
        print(f"\n💡 Recommendations: {len(recommendations)} generated")
        for rec in recommendations:
            priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
            print(f"   {priority_emoji.get(rec.priority, '⚪')} {rec.title}")
    else:
        # Default: collect one snapshot and show current status
        snapshots = await analyzer.collect_resource_snapshot()
        print(f"Resource Analysis - Current Status")
        print("=" * 40)
        
        total_memory = sum(s.memory_usage_mb for s in snapshots)
        avg_cpu = statistics.mean([s.cpu_percent for s in snapshots]) if snapshots else 0
        
        print(f"Containers: {len(snapshots)}")
        print(f"Total Memory: {total_memory:.1f}MB")
        print(f"Average CPU: {avg_cpu:.1f}%")
        print(f"Historical Data Points: {len(analyzer.historical_data)}")
        
        for snapshot in snapshots:
            status_emoji = "✅" if snapshot.container_status == 'running' else "❌"
            print(f"  {status_emoji} {snapshot.container_name}: {snapshot.memory_usage_mb:.1f}MB, {snapshot.cpu_percent:.1f}% CPU")

if __name__ == "__main__":
    asyncio.run(main())