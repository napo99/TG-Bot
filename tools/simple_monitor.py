#!/usr/bin/env python3
"""
Simple Docker Monitor - Quick health checks and problem detection
Focus: Fast, practical, reliable - no bells and whistles.
"""

import asyncio
import docker
import requests
import time
import psutil
from datetime import datetime
from typing import Dict, List, Tuple

class SimpleMonitor:
    """Simple, practical Docker monitoring"""
    
    def __init__(self):
        """Initialize simple monitor"""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"❌ Docker not available: {e}")
            self.docker_client = None
        
        # Expected services for crypto-assistant
        self.expected_services = [
            'crypto-telegram-bot',
            'crypto-market-data'
        ]
        
        # Health endpoints to test
        self.health_endpoints = [
            ('Telegram Bot', 'http://localhost:8080/health'),
            ('Market Data', 'http://localhost:8001/health'),
            ('Market Data API', 'http://localhost:8001/comprehensive_analysis')
        ]

    def check_system_resources(self) -> Dict[str, any]:
        """Quick system resource check"""
        try:
            # Memory
            memory = psutil.virtual_memory()
            
            # CPU
            cpu = psutil.cpu_percent(interval=1)
            
            # Disk
            disk = psutil.disk_usage('/')
            
            return {
                'memory_percent': round(memory.percent, 1),
                'memory_available_mb': round(memory.available / 1024**2, 0),
                'cpu_percent': round(cpu, 1),
                'disk_percent': round((disk.used / disk.total) * 100, 1),
                'disk_free_gb': round(disk.free / 1024**3, 1),
                'status': 'ok'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def check_docker_containers(self) -> List[Dict[str, any]]:
        """Check Docker container status"""
        if not self.docker_client:
            return [{'name': 'docker', 'status': 'unavailable', 'error': 'Docker client not available'}]
        
        containers = []
        
        try:
            # Get all containers
            all_containers = self.docker_client.containers.list(all=True)
            
            # Check expected services
            for service_name in self.expected_services:
                found = False
                
                for container in all_containers:
                    if service_name.lower() in container.name.lower():
                        found = True
                        
                        # Get basic stats if running
                        memory_mb = 0
                        cpu_percent = 0
                        
                        if container.status == 'running':
                            try:
                                stats = container.stats(stream=False)
                                memory_usage = stats['memory_stats'].get('usage', 0)
                                memory_mb = round(memory_usage / 1024**2, 1)
                                
                                # Simple CPU calculation
                                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                                           stats['precpu_stats']['cpu_usage']['total_usage']
                                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                              stats['precpu_stats']['system_cpu_usage']
                                cpu_percent = round((cpu_delta / system_delta * 100.0) if system_delta > 0 else 0, 1)
                            except:
                                pass  # Stats not critical for basic check
                        
                        containers.append({
                            'name': container.name,
                            'status': container.status,
                            'memory_mb': memory_mb,
                            'cpu_percent': cpu_percent,
                            'restart_count': container.attrs.get('RestartCount', 0)
                        })
                        break
                
                if not found:
                    containers.append({
                        'name': service_name,
                        'status': 'missing',
                        'error': 'Container not found'
                    })
            
            return containers
            
        except Exception as e:
            return [{'name': 'docker', 'status': 'error', 'error': str(e)}]

    def check_api_endpoints(self) -> List[Dict[str, any]]:
        """Check API endpoint health"""
        results = []
        
        for name, url in self.health_endpoints:
            try:
                start_time = time.time()
                
                if 'comprehensive_analysis' in url:
                    # POST endpoint
                    response = requests.post(
                        url, 
                        json={'symbol': 'BTC/USDT', 'timeframe': '15m'},
                        timeout=10
                    )
                else:
                    # GET endpoint
                    response = requests.get(url, timeout=5)
                
                response_time = round((time.time() - start_time) * 1000, 0)
                
                results.append({
                    'name': name,
                    'url': url,
                    'status': 'ok' if response.status_code == 200 else 'error',
                    'status_code': response.status_code,
                    'response_time_ms': response_time
                })
                
            except requests.exceptions.ConnectionError:
                results.append({
                    'name': name,
                    'url': url,
                    'status': 'connection_failed',
                    'error': 'Connection refused'
                })
            except requests.exceptions.Timeout:
                results.append({
                    'name': name,
                    'url': url,
                    'status': 'timeout',
                    'error': 'Request timeout'
                })
            except Exception as e:
                results.append({
                    'name': name,
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results

    def run_health_check(self) -> Dict[str, any]:
        """Run complete health check"""
        print("🔍 Running health check...")
        
        # System resources
        system = self.check_system_resources()
        
        # Docker containers
        containers = self.check_docker_containers()
        
        # API endpoints
        endpoints = self.check_api_endpoints()
        
        # Determine overall status
        issues = []
        
        # Check system resources
        if system.get('status') == 'error':
            issues.append(f"System metrics error: {system.get('error')}")
        else:
            if system.get('memory_percent', 0) > 85:
                issues.append(f"High memory usage: {system['memory_percent']}%")
            if system.get('cpu_percent', 0) > 90:
                issues.append(f"High CPU usage: {system['cpu_percent']}%")
            if system.get('disk_percent', 0) > 90:
                issues.append(f"High disk usage: {system['disk_percent']}%")
        
        # Check containers
        for container in containers:
            if container['status'] not in ['running']:
                issues.append(f"Container {container['name']}: {container['status']}")
            elif container.get('restart_count', 0) > 3:
                issues.append(f"Container {container['name']}: {container['restart_count']} restarts")
        
        # Check endpoints
        for endpoint in endpoints:
            if endpoint['status'] != 'ok':
                issues.append(f"API {endpoint['name']}: {endpoint.get('error', endpoint['status'])}")
        
        # Overall status
        if not issues:
            overall_status = 'healthy'
        elif any('error' in issue.lower() or 'failed' in issue.lower() for issue in issues):
            overall_status = 'error'
        else:
            overall_status = 'warning'
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_status': overall_status,
            'system': system,
            'containers': containers,
            'endpoints': endpoints,
            'issues': issues
        }

    def print_health_report(self, health_data: Dict[str, any]):
        """Print formatted health report"""
        print("\n" + "="*60)
        print("🏥 CRYPTO ASSISTANT HEALTH CHECK")
        print("="*60)
        print(f"📅 {health_data['timestamp']}")
        
        # Overall status
        status = health_data['overall_status']
        if status == 'healthy':
            print("✅ Overall Status: HEALTHY")
        elif status == 'warning':
            print("⚠️  Overall Status: WARNING")
        else:
            print("🚨 Overall Status: ERROR")
        
        print()
        
        # System resources
        system = health_data['system']
        if system.get('status') == 'ok':
            print("🖥️  SYSTEM RESOURCES")
            print(f"   Memory: {system['memory_percent']}% ({system['memory_available_mb']:.0f}MB available)")
            print(f"   CPU: {system['cpu_percent']}%")
            print(f"   Disk: {system['disk_percent']}% ({system['disk_free_gb']:.1f}GB free)")
        else:
            print(f"🖥️  SYSTEM RESOURCES: ❌ {system.get('error')}")
        
        print()
        
        # Containers
        print("📦 CONTAINERS")
        for container in health_data['containers']:
            name = container['name']
            status = container['status']
            
            if status == 'running':
                emoji = "✅"
                memory = container.get('memory_mb', 0)
                cpu = container.get('cpu_percent', 0)
                restarts = container.get('restart_count', 0)
                extra = f" | {memory}MB, {cpu}% CPU"
                if restarts > 0:
                    extra += f", {restarts} restarts"
            elif status == 'missing':
                emoji = "❌"
                extra = " | Container not found"
            else:
                emoji = "⚠️"
                extra = f" | {status}"
            
            print(f"   {emoji} {name}{extra}")
        
        print()
        
        # API Endpoints
        print("🌐 API ENDPOINTS")
        for endpoint in health_data['endpoints']:
            name = endpoint['name']
            status = endpoint['status']
            
            if status == 'ok':
                emoji = "✅"
                time_ms = endpoint.get('response_time_ms', 0)
                extra = f" | {time_ms}ms"
            else:
                emoji = "❌"
                error = endpoint.get('error', status)
                extra = f" | {error}"
            
            print(f"   {emoji} {name}{extra}")
        
        print()
        
        # Issues
        if health_data['issues']:
            print("🚨 ISSUES DETECTED")
            for issue in health_data['issues']:
                print(f"   • {issue}")
        else:
            print("✅ NO ISSUES DETECTED")
        
        print("\n" + "="*60)

    def suggest_fixes(self, health_data: Dict[str, any]) -> List[str]:
        """Suggest quick fixes for detected issues"""
        fixes = []
        
        for issue in health_data.get('issues', []):
            if 'high memory usage' in issue.lower():
                fixes.append("💡 High memory: Run 'docker system prune' to clean up")
                fixes.append("💡 Consider restarting containers: docker-compose restart")
            
            elif 'container' in issue.lower() and ('missing' in issue.lower() or 'exited' in issue.lower()):
                fixes.append("💡 Container issue: Run 'docker-compose up -d' to start services")
            
            elif 'api' in issue.lower() and 'connection' in issue.lower():
                fixes.append("💡 API connection issue: Check if containers are running")
                fixes.append("💡 Try restarting services: docker-compose restart")
            
            elif 'restart' in issue.lower():
                fixes.append("💡 Restart loop detected: Check logs with 'docker logs <container_name>'")
                fixes.append("💡 May need to fix configuration or increase resources")
        
        if not fixes:
            fixes.append("✅ System is healthy - no fixes needed")
        
        return fixes

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Docker Monitor')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Watch interval (seconds)')
    parser.add_argument('--fixes', action='store_true', help='Show suggested fixes')
    
    args = parser.parse_args()
    
    monitor = SimpleMonitor()
    
    if args.watch:
        print(f"👀 Starting continuous monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                health_data = monitor.run_health_check()
                monitor.print_health_report(health_data)
                
                if args.fixes and health_data.get('issues'):
                    fixes = monitor.suggest_fixes(health_data)
                    print("\n🔧 SUGGESTED FIXES")
                    for fix in fixes:
                        print(f"   {fix}")
                
                print(f"\n⏰ Next check in {args.interval} seconds...")
                await asyncio.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    
    else:
        # Single health check
        health_data = monitor.run_health_check()
        monitor.print_health_report(health_data)
        
        if args.fixes:
            fixes = monitor.suggest_fixes(health_data)
            print("\n🔧 SUGGESTED FIXES")
            for fix in fixes:
                print(f"   {fix}")

if __name__ == "__main__":
    asyncio.run(main())