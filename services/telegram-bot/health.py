# 🏥 Basic Health Endpoint Template
# Copy to services/{service}/health.py and integrate

from flask import jsonify
from datetime import datetime
import os
import psutil
import asyncio

class HealthChecker:
    def __init__(self, service_name):
        self.service_name = service_name
        self.start_time = datetime.utcnow()
    
    def get_basic_health(self):
        """Basic health status - always implement this"""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            'service': self.service_name,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': int(uptime.total_seconds()),
            'version': os.getenv('SERVICE_VERSION', 'unknown'),
            'environment': os.getenv('ENVIRONMENT', 'local')
        }
    
    def get_detailed_health(self):
        """Detailed health with system metrics"""
        basic = self.get_basic_health()
        
        # System metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        basic.update({
            'system': {
                'memory_usage_percent': memory.percent,
                'memory_available_mb': memory.available // 1024 // 1024,
                'cpu_usage_percent': cpu_percent,
                'disk_usage_percent': psutil.disk_usage('/').percent
            },
            'checks': self._run_health_checks()
        })
        
        return basic
    
    def _run_health_checks(self):
        """Override this method with service-specific checks"""
        # TODO: Implement service-specific health checks
        # Examples:
        # - Database connection: self._check_database()
        # - External API: self._check_external_apis()
        # - Cache: self._check_redis()
        
        return {
            'database': True,  # TODO: Implement actual check
            'external_apis': True,  # TODO: Implement actual check
            'cache': True  # TODO: Implement actual check
        }
    
    async def get_readiness(self):
        """Readiness check for container orchestration"""
        checks = {
            'service_ready': True,  # TODO: Implement actual readiness logic
            'dependencies_ready': True,  # TODO: Check dependencies
            'configuration_loaded': True  # TODO: Check config
        }
        
        all_ready = all(checks.values())
        
        return {
            'ready': all_ready,
            'checks': checks,
            'timestamp': datetime.utcnow().isoformat()
        }

# Integration example for Flask app:
def add_health_endpoints(app, service_name):
    """Add health endpoints to Flask app"""
    health_checker = HealthChecker(service_name)
    
    @app.route('/health')
    def health():
        return jsonify(health_checker.get_basic_health())
    
    @app.route('/health/detailed') 
    def health_detailed():
        return jsonify(health_checker.get_detailed_health())
    
    @app.route('/health/readiness')
    async def readiness():
        result = await health_checker.get_readiness()
        status_code = 200 if result['ready'] else 503
        return jsonify(result), status_code
    
    return app

# TODO: Integration steps:
# 1. Copy this file to services/{your-service}/health.py
# 2. In your main.py, add:
#    from health import add_health_endpoints
#    app = add_health_endpoints(app, 'your-service-name')
# 3. Customize _run_health_checks() for your service
# 4. Test: curl http://localhost:8001/health