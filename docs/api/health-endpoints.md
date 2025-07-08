# Health Check Endpoints

All services provide standardized health check endpoints for monitoring and orchestration.

## Endpoints

### `GET /health`
Basic health status - lightweight check for load balancers.

**Response:**
```json
{
  "service": "market-data-service",
  "status": "healthy", 
  "timestamp": "2025-07-08T13:45:23.123456",
  "uptime_seconds": 86400,
  "version": "1.0.0",
  "environment": "local"
}
```

### `GET /health/detailed`
Detailed health with system metrics.

### `GET /health/readiness`
Kubernetes-style readiness probe.

## Usage

```bash
# Quick health check
curl http://localhost:8001/health

# Detailed health info
curl http://localhost:8001/health/detailed

# Readiness check
curl http://localhost:8001/health/readiness
```
