"""
Monitoring Coordinator Service
Coordinates all monitoring services and provides health checks
Central coordination point for the monitoring system
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import subprocess
from aiohttp import web

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class MonitoringCoordinator:
    """
    Coordinates monitoring services and provides health monitoring
    Central point for system health checks and service management
    """
    
    def __init__(self):
        # Configuration
        self.port = 8002
        self.health_check_interval = 30  # seconds
        self.max_failure_count = 3
        
        # Service status tracking
        self.service_status = {
            "liquidation_monitor": {"healthy": False, "failures": 0, "last_check": None},
            "oi_detector": {"healthy": False, "failures": 0, "last_check": None},
            "alert_dispatcher": {"healthy": False, "failures": 0, "last_check": None}
        }
        
        # System metrics
        self.system_metrics = {
            "start_time": datetime.now(),
            "total_checks": 0,
            "alerts_processed": 0,
            "memory_usage": 0
        }
        
        # Web app
        self.app = web.Application()
        self.setup_routes()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_routes(self) -> None:
        """Setup web routes for health checks and metrics"""
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/status', self.status_handler)
        self.app.router.add_get('/metrics', self.metrics_handler)
        self.app.router.add_post('/restart-service', self.restart_service_handler)
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        health_status = await self.get_overall_health()
        
        status_code = 200 if health_status["healthy"] else 503
        
        return web.json_response(health_status, status=status_code)
    
    async def status_handler(self, request: web.Request) -> web.Response:
        """Detailed status endpoint"""
        status = {
            "coordinator": {
                "uptime_seconds": (datetime.now() - self.system_metrics["start_time"]).total_seconds(),
                "total_checks": self.system_metrics["total_checks"],
                "memory_usage_mb": await self.get_memory_usage()
            },
            "services": self.service_status,
            "alerts": await self.get_alert_statistics()
        }
        
        return web.json_response(status)
    
    async def metrics_handler(self, request: web.Request) -> web.Response:
        """Prometheus-style metrics endpoint"""
        metrics = []
        
        # System metrics
        uptime = (datetime.now() - self.system_metrics["start_time"]).total_seconds()
        metrics.append(f"crypto_monitoring_uptime_seconds {uptime}")
        metrics.append(f"crypto_monitoring_checks_total {self.system_metrics['total_checks']}")
        
        # Service health metrics
        for service_name, status in self.service_status.items():
            healthy = 1 if status["healthy"] else 0
            metrics.append(f"crypto_service_healthy{{service=\"{service_name}\"}} {healthy}")
            metrics.append(f"crypto_service_failures_total{{service=\"{service_name}\"}} {status['failures']}")
        
        # Memory usage
        memory_mb = await self.get_memory_usage()
        metrics.append(f"crypto_monitoring_memory_usage_mb {memory_mb}")
        
        return web.Response(text="\n".join(metrics), content_type="text/plain")
    
    async def restart_service_handler(self, request: web.Request) -> web.Response:
        """Restart a specific service"""
        data = await request.json()
        service_name = data.get("service")
        
        if service_name not in self.service_status:
            return web.json_response({"error": "Invalid service name"}, status=400)
        
        try:
            success = await self.restart_service(service_name)
            return web.json_response({"success": success})
        except Exception as e:
            self.logger.error(f"Error restarting service {service_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def start(self) -> None:
        """Start the monitoring coordinator"""
        self.logger.info("Starting monitoring coordinator...")
        
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        self.logger.info(f"Health monitoring API started on port {self.port}")
        
        try:
            # Start health monitoring loop
            await self.health_monitoring_loop()
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested")
        finally:
            await runner.cleanup()
    
    async def health_monitoring_loop(self) -> None:
        """Main health monitoring loop"""
        while True:
            try:
                await self.check_all_services()
                await self.update_system_metrics()
                
                self.system_metrics["total_checks"] += 1
                
                # Log overall status
                overall_health = await self.get_overall_health()
                if overall_health["healthy"]:
                    self.logger.info(f"All services healthy - Check #{self.system_metrics['total_checks']}")
                else:
                    unhealthy = [s for s, status in self.service_status.items() if not status["healthy"]]
                    self.logger.warning(f"Unhealthy services: {', '.join(unhealthy)}")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def check_all_services(self) -> None:
        """Check health of all monitoring services"""
        # Check liquidation monitor
        await self.check_liquidation_monitor()
        
        # Check OI detector
        await self.check_oi_detector()
        
        # Check alert dispatcher
        await self.check_alert_dispatcher()
    
    async def check_liquidation_monitor(self) -> None:
        """Check liquidation monitor health"""
        service_name = "liquidation_monitor"
        
        try:
            # Check if alert file is being updated
            alert_file = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/liquidation_alerts.json"
            
            if os.path.exists(alert_file):
                # File exists, service is likely running
                file_age = time.time() - os.path.getmtime(alert_file)
                healthy = file_age < 3600  # File updated within last hour
            else:
                # File doesn't exist yet, check if it's a new service
                healthy = True  # Give it time to create the file
            
            self.update_service_status(service_name, healthy)
            
        except Exception as e:
            self.logger.error(f"Error checking {service_name}: {e}")
            self.update_service_status(service_name, False)
    
    async def check_oi_detector(self) -> None:
        """Check OI detector health"""
        service_name = "oi_detector"
        
        try:
            # Check if service can reach market-data API
            market_data_url = os.getenv("MARKET_DATA_URL", "http://market-data:8001")
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{market_data_url}/health", timeout=5) as response:
                        api_healthy = response.status == 200
                except:
                    api_healthy = False
            
            # Check if alert file exists and is recent
            alert_file = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/oi_alerts.json"
            file_healthy = True  # OI alerts are less frequent
            
            if os.path.exists(alert_file):
                file_age = time.time() - os.path.getmtime(alert_file)
                file_healthy = file_age < 7200  # 2 hours for OI alerts
            
            healthy = api_healthy and file_healthy
            self.update_service_status(service_name, healthy)
            
        except Exception as e:
            self.logger.error(f"Error checking {service_name}: {e}")
            self.update_service_status(service_name, False)
    
    async def check_alert_dispatcher(self) -> None:
        """Check alert dispatcher health"""
        service_name = "alert_dispatcher"
        
        try:
            # Check if database file exists and is accessible
            db_file = "/Users/screener-m3/projects/crypto-assistant/data/alerts.db"
            
            healthy = True
            
            if os.path.exists(db_file):
                # Try to access database
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM alert_history LIMIT 1")
                    conn.close()
                    healthy = True
                except:
                    healthy = False
            else:
                # Database doesn't exist yet, might be starting up
                healthy = True
            
            self.update_service_status(service_name, healthy)
            
        except Exception as e:
            self.logger.error(f"Error checking {service_name}: {e}")
            self.update_service_status(service_name, False)
    
    def update_service_status(self, service_name: str, healthy: bool) -> None:
        """Update service status and handle failures"""
        status = self.service_status[service_name]
        
        status["last_check"] = datetime.now()
        
        if healthy:
            status["healthy"] = True
            status["failures"] = 0
        else:
            status["failures"] += 1
            
            if status["failures"] >= self.max_failure_count:
                status["healthy"] = False
                self.logger.error(f"Service {service_name} marked as unhealthy after {status['failures']} failures")
                
                # TODO: Implement auto-restart logic here
                # For now, just log the failure
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific monitoring service"""
        try:
            # Map service names to container names
            container_mapping = {
                "liquidation_monitor": "crypto-liquidation-monitor",
                "oi_detector": "crypto-oi-detector", 
                "alert_dispatcher": "crypto-alert-dispatcher"
            }
            
            container_name = container_mapping.get(service_name)
            if not container_name:
                return False
            
            # Restart the container
            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully restarted {service_name}")
                # Reset failure count
                self.service_status[service_name]["failures"] = 0
                return True
            else:
                self.logger.error(f"Failed to restart {service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting {service_name}: {e}")
            return False
    
    async def get_overall_health(self) -> Dict:
        """Get overall system health status"""
        healthy_services = sum(1 for status in self.service_status.values() if status["healthy"])
        total_services = len(self.service_status)
        
        overall_healthy = healthy_services == total_services
        
        return {
            "healthy": overall_healthy,
            "services_healthy": f"{healthy_services}/{total_services}",
            "uptime_seconds": (datetime.now() - self.system_metrics["start_time"]).total_seconds(),
            "last_check": datetime.now().isoformat()
        }
    
    async def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            # Get memory usage of monitoring containers
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.MemUsage}}", 
                 "crypto-liquidation-monitor", "crypto-oi-detector", "crypto-alert-dispatcher"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse memory usage (simplified)
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                total_mb = 0
                
                for line in lines:
                    if 'MiB' in line:
                        mb_value = float(line.split('MiB')[0].split()[-1])
                        total_mb += mb_value
                
                return total_mb
            
        except Exception as e:
            self.logger.warning(f"Could not get memory usage: {e}")
        
        return 0.0
    
    async def get_alert_statistics(self) -> Dict:
        """Get alert processing statistics"""
        stats = {
            "liquidation_alerts": 0,
            "oi_alerts": 0,
            "total_processed": 0,
            "last_liquidation_alert": None,
            "last_oi_alert": None
        }
        
        try:
            # Count liquidation alerts
            liq_file = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/liquidation_alerts.json"
            if os.path.exists(liq_file):
                with open(liq_file, 'r') as f:
                    liq_alerts = json.load(f)
                    stats["liquidation_alerts"] = len(liq_alerts)
                    if liq_alerts:
                        stats["last_liquidation_alert"] = liq_alerts[-1].get("timestamp")
            
            # Count OI alerts
            oi_file = "/Users/screener-m3/projects/crypto-assistant/shared/alerts/oi_alerts.json"
            if os.path.exists(oi_file):
                with open(oi_file, 'r') as f:
                    oi_alerts = json.load(f)
                    stats["oi_alerts"] = len(oi_alerts)
                    if oi_alerts:
                        stats["last_oi_alert"] = oi_alerts[-1].get("timestamp")
            
            stats["total_processed"] = stats["liquidation_alerts"] + stats["oi_alerts"]
            
        except Exception as e:
            self.logger.error(f"Error getting alert statistics: {e}")
        
        return stats


async def main():
    """Main entry point"""
    coordinator = MonitoringCoordinator()
    
    try:
        await coordinator.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")


if __name__ == "__main__":
    asyncio.run(main())