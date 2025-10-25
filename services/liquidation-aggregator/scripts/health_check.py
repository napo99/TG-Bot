#!/usr/bin/env python3
"""Health check script for liquidation aggregator"""

import sys
import json
import redis
import psycopg2
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            health_status = check_health()
            
            if health_status['status'] == 'healthy':
                self.send_response(200)
            else:
                self.send_response(503)
            
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_status).encode())
        else:
            self.send_response(404)
            self.end_headers()

def check_health():
    """Check health of all components"""
    health = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'checks': {}
    }
    
    # Check Redis
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        health['checks']['redis'] = 'healthy'
    except:
        health['checks']['redis'] = 'unhealthy'
        health['status'] = 'unhealthy'
    
    # Check Postgres
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='liquidations',
            user='postgres'
        )
        conn.close()
        health['checks']['postgres'] = 'healthy'
    except:
        health['checks']['postgres'] = 'unhealthy'
        health['status'] = 'unhealthy'
    
    return health

def run_health_server():
    """Run health check HTTP server"""
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    server.serve_forever()

if __name__ == '__main__':
    # Quick health check
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        health = check_health()
        print(json.dumps(health, indent=2))
        sys.exit(0 if health['status'] == 'healthy' else 1)
    
    # Run health server
    print("Starting health check server on port 8080...")
    run_health_server()
