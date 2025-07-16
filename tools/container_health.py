#!/usr/bin/env python3
"""
Container Health Checker - Advanced container health validation system
Performs deep health checks beyond Docker's basic health monitoring.
"""

import asyncio
import aiohttp
import time
import json
import logging
import psutil
import docker
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

@dataclass
class HealthCheckResult:
    """Health check result structure"""
    service_name: str
    endpoint: str
    status: str  # healthy, unhealthy, degraded, unknown
    response_time_ms: float
    status_code: Optional[int]
    error_message: Optional[str]
    timestamp: str
    additional_info: Dict[str, Any] = None

@dataclass
class ServiceDependency:
    """Service dependency mapping"""
    service_name: str
    internal_host: str
    external_host: str
    port: int
    health_endpoint: str
    api_endpoints: List[str]
    critical: bool = True

class ContainerHealthChecker:
    """Advanced container health validation system"""
    
    def __init__(self, log_dir: str = "/Users/screener-m3/projects/crypto-assistant/data/logs"):
        """Initialize health checker"""
        self.log_dir = log_dir
        self.setup_logging()
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.error(f"Failed to connect to Docker: {e}")
            self.docker_client = None
        
        # Service definitions for crypto-assistant
        self.services = {
            'telegram-bot': ServiceDependency(
                service_name='telegram-bot',
                internal_host='crypto-telegram-bot',
                external_host='localhost',
                port=8080,
                health_endpoint='/health',
                api_endpoints=['/start', '/help'],
                critical=True
            ),
            'market-data': ServiceDependency(
                service_name='market-data',
                internal_host='crypto-market-data',
                external_host='localhost',
                port=8001,
                health_endpoint='/health',
                api_endpoints=['/comprehensive_analysis', '/multi_oi', '/volume_scan'],
                critical=True
            ),
            'redis': ServiceDependency(
                service_name='redis',
                internal_host='redis',
                external_host='localhost',
                port=6379,
                health_endpoint='',  # Redis doesn't have HTTP health endpoint
                api_endpoints=[],
                critical=False
            )
        }
        
        # Health check history
        self.health_history: List[Dict] = []
        self.max_history_size = 500
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning_ms': 2000,    # 2 seconds
            'response_time_critical_ms': 5000,   # 5 seconds
            'memory_pressure_warning': 70,       # 70% memory usage
            'memory_pressure_critical': 85,      # 85% memory usage
            'cpu_pressure_warning': 80,          # 80% CPU usage
            'disk_pressure_warning': 85,         # 85% disk usage
            'error_rate_warning': 0.05,          # 5% error rate
            'uptime_minimum_minutes': 5          # 5 minutes minimum uptime
        }
        
        self.logger.info("Container Health Checker initialized")

    def setup_logging(self):
        """Setup logging system"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, "container_health.log")
        
        self.logger = logging.getLogger('container_health')
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

    async def check_http_endpoint(self, url: str, timeout: int = 10, 
                                 method: str = 'GET', payload: dict = None) -> HealthCheckResult:
        """Check HTTP endpoint health"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                if method.upper() == 'GET':
                    async with session.get(url) as response:
                        response_time = (time.time() - start_time) * 1000
                        return HealthCheckResult(
                            service_name=url.split('/')[2].split(':')[0],
                            endpoint=url,
                            status='healthy' if response.status == 200 else 'unhealthy',
                            response_time_ms=round(response_time, 2),
                            status_code=response.status,
                            error_message=None if response.status == 200 else f"HTTP {response.status}",
                            timestamp=datetime.now().isoformat(),
                            additional_info={'response_size': len(await response.text())}
                        )
                
                elif method.upper() == 'POST':
                    async with session.post(url, json=payload) as response:
                        response_time = (time.time() - start_time) * 1000
                        return HealthCheckResult(
                            service_name=url.split('/')[2].split(':')[0],
                            endpoint=url,
                            status='healthy' if response.status == 200 else 'unhealthy',
                            response_time_ms=round(response_time, 2),
                            status_code=response.status,
                            error_message=None if response.status == 200 else f"HTTP {response.status}",
                            timestamp=datetime.now().isoformat(),
                            additional_info={'method': 'POST', 'payload_sent': bool(payload)}
                        )
        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=url.split('/')[2].split(':')[0],
                endpoint=url,
                status='unhealthy',
                response_time_ms=round(response_time, 2),
                status_code=None,
                error_message='Timeout',
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=url.split('/')[2].split(':')[0],
                endpoint=url,
                status='unhealthy',
                response_time_ms=round(response_time, 2),
                status_code=None,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def deep_health_check(self, service_name: str) -> Dict[str, Any]:
        """Perform deep health validation beyond Docker's basic checks"""
        if service_name not in self.services:
            return {'error': f'Unknown service: {service_name}'}
        
        service = self.services[service_name]
        results = {
            'service_name': service_name,
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'unknown',
            'performance_metrics': {},
            'recommendations': []
        }
        
        try:
            # 1. Container existence and status check
            container_status = await self._check_container_status(service_name)
            results['checks']['container_status'] = container_status
            
            # 2. Resource usage check
            resource_check = await self._check_resource_usage(service_name)
            results['checks']['resource_usage'] = resource_check
            results['performance_metrics'] = resource_check.get('metrics', {})
            
            # 3. Network connectivity check
            network_check = await self._check_network_connectivity(service)
            results['checks']['network_connectivity'] = network_check
            
            # 4. Health endpoint check
            if service.health_endpoint:
                health_endpoint_check = await self._check_health_endpoint(service)
                results['checks']['health_endpoint'] = health_endpoint_check
            
            # 5. API endpoint functionality check
            if service.api_endpoints:
                api_check = await self._check_api_endpoints(service)
                results['checks']['api_endpoints'] = api_check
            
            # 6. Memory pressure analysis
            memory_analysis = await self._analyze_memory_pressure(service_name)
            results['checks']['memory_analysis'] = memory_analysis
            
            # 7. Determine overall status
            results['overall_status'] = self._determine_overall_status(results['checks'])
            
            # 8. Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
            
        except Exception as e:
            self.logger.error(f"Error in deep health check for {service_name}: {e}")
            results['error'] = str(e)
        
        return results

    async def _check_container_status(self, service_name: str) -> Dict[str, Any]:
        """Check container existence and basic status"""
        if not self.docker_client:
            return {'status': 'error', 'message': 'Docker client not available'}
        
        try:
            containers = self.docker_client.containers.list(all=True)
            matching_containers = [c for c in containers if service_name.lower() in c.name.lower()]
            
            if not matching_containers:
                return {
                    'status': 'error',
                    'message': f'No containers found matching {service_name}',
                    'container_count': 0
                }
            
            container = matching_containers[0]  # Use first match
            container.reload()
            
            # Get detailed container info
            return {
                'status': 'healthy' if container.status == 'running' else 'unhealthy',
                'container_status': container.status,
                'container_id': container.short_id,
                'container_name': container.name,
                'image': container.image.tags[0] if container.image.tags else container.image.id[:12],
                'created': container.attrs['Created'],
                'restart_count': container.attrs.get('RestartCount', 0),
                'uptime_seconds': (datetime.now() - datetime.fromisoformat(
                    container.attrs['Created'].replace('Z', '+00:00')
                )).total_seconds()
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    async def _check_resource_usage(self, service_name: str) -> Dict[str, Any]:
        """Check container resource usage"""
        if not self.docker_client:
            return {'status': 'error', 'message': 'Docker client not available'}
        
        try:
            containers = self.docker_client.containers.list()
            matching_containers = [c for c in containers if service_name.lower() in c.name.lower()]
            
            if not matching_containers:
                return {'status': 'error', 'message': 'Container not running'}
            
            container = matching_containers[0]
            stats = container.stats(stream=False)
            
            # Calculate metrics
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 0)
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
            
            # CPU calculation
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0
            
            # Determine status based on thresholds
            status = 'healthy'
            if memory_percent > self.thresholds['memory_pressure_critical']:
                status = 'critical'
            elif memory_percent > self.thresholds['memory_pressure_warning']:
                status = 'warning'
            elif cpu_percent > self.thresholds['cpu_pressure_warning']:
                status = 'warning'
            
            return {
                'status': status,
                'metrics': {
                    'memory_usage_mb': round(memory_usage / 1024 / 1024, 2),
                    'memory_limit_mb': round(memory_limit / 1024 / 1024, 2),
                    'memory_percent': round(memory_percent, 2),
                    'cpu_percent': round(cpu_percent, 2)
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    async def _check_network_connectivity(self, service: ServiceDependency) -> Dict[str, Any]:
        """Check network connectivity to service"""
        try:
            # Check external connectivity
            external_url = f"http://{service.external_host}:{service.port}"
            external_result = await self.check_http_endpoint(external_url, timeout=5)
            
            # For internal connectivity, we'd need to be inside Docker network
            # For now, we'll use external as proxy for internal
            
            return {
                'status': external_result.status,
                'external_connectivity': {
                    'host': service.external_host,
                    'port': service.port,
                    'reachable': external_result.status == 'healthy',
                    'response_time_ms': external_result.response_time_ms
                },
                'message': external_result.error_message
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    async def _check_health_endpoint(self, service: ServiceDependency) -> Dict[str, Any]:
        """Check service health endpoint"""
        if not service.health_endpoint:
            return {'status': 'skipped', 'message': 'No health endpoint defined'}
        
        url = f"http://{service.external_host}:{service.port}{service.health_endpoint}"
        result = await self.check_http_endpoint(url)
        
        return {
            'status': result.status,
            'response_time_ms': result.response_time_ms,
            'status_code': result.status_code,
            'message': result.error_message
        }

    async def _check_api_endpoints(self, service: ServiceDependency) -> Dict[str, Any]:
        """Check API endpoint functionality"""
        if not service.api_endpoints:
            return {'status': 'skipped', 'message': 'No API endpoints defined'}
        
        results = {}
        overall_status = 'healthy'
        
        for endpoint in service.api_endpoints:
            url = f"http://{service.external_host}:{service.port}{endpoint}"
            
            # Special handling for different endpoints
            if 'comprehensive_analysis' in endpoint:
                # POST endpoint with payload
                payload = {'symbol': 'BTC/USDT', 'timeframe': '15m'}
                result = await self.check_http_endpoint(url, method='POST', payload=payload)
            else:
                # GET endpoint
                result = await self.check_http_endpoint(url)
            
            results[endpoint] = {
                'status': result.status,
                'response_time_ms': result.response_time_ms,
                'status_code': result.status_code
            }
            
            if result.status != 'healthy':
                overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'endpoints': results
        }

    async def _analyze_memory_pressure(self, service_name: str) -> Dict[str, Any]:
        """Analyze memory pressure and fragmentation"""
        try:
            # System-wide memory analysis
            memory = psutil.virtual_memory()
            
            # Container-specific analysis (if available)
            container_memory = None
            if self.docker_client:
                try:
                    containers = self.docker_client.containers.list()
                    matching_containers = [c for c in containers if service_name.lower() in c.name.lower()]
                    
                    if matching_containers:
                        container = matching_containers[0]
                        stats = container.stats(stream=False)
                        memory_usage = stats['memory_stats'].get('usage', 0)
                        memory_limit = stats['memory_stats'].get('limit', 0)
                        
                        container_memory = {
                            'usage_mb': round(memory_usage / 1024 / 1024, 2),
                            'limit_mb': round(memory_limit / 1024 / 1024, 2),
                            'percent': round((memory_usage / memory_limit * 100), 2) if memory_limit > 0 else 0
                        }
                except:
                    pass
            
            # Determine status
            system_pressure = memory.percent
            status = 'healthy'
            
            if system_pressure > 90:
                status = 'critical'
            elif system_pressure > 80:
                status = 'warning'
            
            return {
                'status': status,
                'system_memory': {
                    'total_mb': round(memory.total / 1024 / 1024, 2),
                    'available_mb': round(memory.available / 1024 / 1024, 2),
                    'used_percent': memory.percent,
                    'pressure_level': 'high' if system_pressure > 80 else 'normal'
                },
                'container_memory': container_memory
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _determine_overall_status(self, checks: Dict[str, Any]) -> str:
        """Determine overall service health status"""
        statuses = []
        
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict) and 'status' in check_result:
                statuses.append(check_result['status'])
        
        # Priority: error > critical > unhealthy > warning > degraded > healthy
        if 'error' in statuses or 'critical' in statuses:
            return 'critical'
        elif 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'warning' in statuses:
            return 'warning'
        elif 'degraded' in statuses:
            return 'degraded'
        elif 'healthy' in statuses:
            return 'healthy'
        else:
            return 'unknown'

    def _generate_recommendations(self, health_results: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        checks = health_results.get('checks', {})
        
        # Container status recommendations
        container_check = checks.get('container_status', {})
        if container_check.get('status') == 'unhealthy':
            recommendations.append("Container is not running. Check logs and restart if necessary.")
        
        restart_count = container_check.get('restart_count', 0)
        if restart_count > 3:
            recommendations.append(f"Container has restarted {restart_count} times. Investigate underlying issues.")
        
        # Resource usage recommendations
        resource_check = checks.get('resource_usage', {})
        if resource_check.get('status') in ['warning', 'critical']:
            metrics = resource_check.get('metrics', {})
            memory_percent = metrics.get('memory_percent', 0)
            
            if memory_percent > 85:
                recommendations.append("Critical memory usage. Consider increasing memory limits or optimizing application.")
            elif memory_percent > 70:
                recommendations.append("High memory usage detected. Monitor closely.")
        
        # API endpoint recommendations
        api_check = checks.get('api_endpoints', {})
        if api_check.get('status') == 'degraded':
            recommendations.append("Some API endpoints are failing. Check application logs.")
        
        # Memory pressure recommendations
        memory_analysis = checks.get('memory_analysis', {})
        if memory_analysis.get('status') in ['warning', 'critical']:
            system_memory = memory_analysis.get('system_memory', {})
            if system_memory.get('used_percent', 0) > 85:
                recommendations.append("System memory pressure detected. Consider upgrading instance size.")
        
        if not recommendations:
            recommendations.append("Service is healthy. No immediate action required.")
        
        return recommendations

    async def test_api_endpoints(self) -> Dict[str, bool]:
        """Test all API endpoints are responding correctly"""
        results = {}
        
        try:
            # Test Telegram Bot endpoints
            telegram_endpoints = [
                'http://localhost:8080/health'
            ]
            
            for endpoint in telegram_endpoints:
                result = await self.check_http_endpoint(endpoint)
                results[endpoint] = result.status == 'healthy'
            
            # Test Market Data endpoints
            market_data_endpoints = [
                ('http://localhost:8001/health', 'GET', None),
                ('http://localhost:8001/comprehensive_analysis', 'POST', 
                 {'symbol': 'BTC/USDT', 'timeframe': '15m'}),
                ('http://localhost:8001/multi_oi', 'POST', 
                 {'symbol': 'BTC-USDT'})
            ]
            
            for endpoint_data in market_data_endpoints:
                url, method, payload = endpoint_data
                result = await self.check_http_endpoint(url, method=method, payload=payload)
                results[url] = result.status == 'healthy'
            
            self.logger.info(f"API endpoint test results: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing API endpoints: {e}")
            return {}

    async def validate_service_communication(self) -> Dict[str, str]:
        """Test inter-service communication health"""
        communication_results = {}
        
        try:
            # Test Telegram Bot -> Market Data communication
            telegram_to_market_data = await self.check_http_endpoint(
                'http://crypto-market-data:8001/health'
            )
            communication_results['telegram_to_market_data'] = telegram_to_market_data.status
            
            # Test external access to both services
            external_telegram = await self.check_http_endpoint('http://localhost:8080/health')
            external_market_data = await self.check_http_endpoint('http://localhost:8001/health')
            
            communication_results['external_telegram'] = external_telegram.status
            communication_results['external_market_data'] = external_market_data.status
            
            # Test if services can communicate with Redis (if applicable)
            # This would require application-level testing
            
            self.logger.info(f"Service communication validation: {communication_results}")
            return communication_results
            
        except Exception as e:
            self.logger.error(f"Error validating service communication: {e}")
            return {}

    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all services"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'api_endpoints': {},
            'service_communication': {},
            'overall_system_status': 'unknown',
            'summary': {}
        }
        
        try:
            # Deep health check for each service
            for service_name in self.services.keys():
                self.logger.info(f"Running deep health check for {service_name}")
                service_health = await self.deep_health_check(service_name)
                results['services'][service_name] = service_health
            
            # API endpoint testing
            api_results = await self.test_api_endpoints()
            results['api_endpoints'] = api_results
            
            # Service communication validation
            comm_results = await self.validate_service_communication()
            results['service_communication'] = comm_results
            
            # Generate summary
            healthy_services = sum(1 for s in results['services'].values() 
                                 if s.get('overall_status') == 'healthy')
            total_services = len(results['services'])
            
            working_endpoints = sum(1 for working in api_results.values() if working)
            total_endpoints = len(api_results)
            
            results['summary'] = {
                'healthy_services': f"{healthy_services}/{total_services}",
                'working_endpoints': f"{working_endpoints}/{total_endpoints}",
                'critical_issues': sum(1 for s in results['services'].values() 
                                     if s.get('overall_status') in ['critical', 'error']),
                'warnings': sum(1 for s in results['services'].values() 
                              if s.get('overall_status') == 'warning')
            }
            
            # Determine overall system status
            if results['summary']['critical_issues'] > 0:
                results['overall_system_status'] = 'critical'
            elif results['summary']['warnings'] > 0:
                results['overall_system_status'] = 'warning'
            elif healthy_services == total_services and working_endpoints == total_endpoints:
                results['overall_system_status'] = 'healthy'
            else:
                results['overall_system_status'] = 'degraded'
            
            # Store in history
            self.health_history.append(results)
            if len(self.health_history) > self.max_history_size:
                self.health_history = self.health_history[-self.max_history_size:]
            
            self.logger.info(f"Comprehensive health check complete: {results['overall_system_status']}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive health check: {e}")
            results['error'] = str(e)
            return results

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Container Health Checker')
    parser.add_argument('--service', type=str, choices=['telegram-bot', 'market-data', 'redis'],
                       help='Check specific service')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive health check on all services')
    parser.add_argument('--api-test', action='store_true',
                       help='Test API endpoints')
    parser.add_argument('--communication', action='store_true',
                       help='Test service communication')
    
    args = parser.parse_args()
    
    checker = ContainerHealthChecker()
    
    if args.service:
        result = await checker.deep_health_check(args.service)
        print(json.dumps(result, indent=2))
    elif args.comprehensive:
        result = await checker.run_comprehensive_health_check()
        print(json.dumps(result, indent=2))
    elif args.api_test:
        result = await checker.test_api_endpoints()
        print("API Endpoint Test Results:")
        for endpoint, status in result.items():
            status_emoji = "✅" if status else "❌"
            print(f"  {status_emoji} {endpoint}")
    elif args.communication:
        result = await checker.validate_service_communication()
        print("Service Communication Test Results:")
        for comm, status in result.items():
            status_emoji = "✅" if status == 'healthy' else "❌"
            print(f"  {status_emoji} {comm}: {status}")
    else:
        # Default: run comprehensive check
        result = await checker.run_comprehensive_health_check()
        
        print("=" * 60)
        print("🔍 COMPREHENSIVE HEALTH CHECK RESULTS")
        print("=" * 60)
        print(f"Overall Status: {result['overall_system_status'].upper()}")
        print(f"Timestamp: {result['timestamp']}")
        print()
        
        summary = result['summary']
        print("📊 SUMMARY")
        print(f"  Healthy Services: {summary['healthy_services']}")
        print(f"  Working Endpoints: {summary['working_endpoints']}")
        print(f"  Critical Issues: {summary['critical_issues']}")
        print(f"  Warnings: {summary['warnings']}")
        print()
        
        print("🏥 SERVICE HEALTH")
        for service_name, service_data in result['services'].items():
            status = service_data.get('overall_status', 'unknown')
            status_emoji = {
                'healthy': '✅',
                'warning': '⚠️',
                'degraded': '🟡',
                'unhealthy': '❌',
                'critical': '🚨',
                'error': '💥'
            }.get(status, '❓')
            
            print(f"  {status_emoji} {service_name}: {status.upper()}")
            
            # Show recommendations if any
            recommendations = service_data.get('recommendations', [])
            if recommendations and status != 'healthy':
                for rec in recommendations:
                    print(f"    💡 {rec}")

if __name__ == "__main__":
    asyncio.run(main())