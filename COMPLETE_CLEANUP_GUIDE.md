# Complete Docker Cleanup Guide - Crypto Assistant

## Overview
This guide provides a complete solution to remove ALL Docker cache and health check dependencies from the crypto-assistant project.

## Current Health Check Locations Found

### 1. Docker Compose Files
- `docker-compose.yml` - Lines 26-31 (market-data service)
- `docker-compose.yml.working` - Lines 18-23 (market-data service)
- `services/telegram-bot/docker-compose.production.yml` - Lines 19-24 (market-data service)

### 2. Dockerfiles
- `services/market-data/Dockerfile` - Lines 32-33 (HEALTHCHECK command)
- `services/telegram-bot/Dockerfile` - curl dependency (line 7)
- `services/telegram-bot/Dockerfile.aws` - No health checks (already clean)

## Step-by-Step Cleanup Process

### Step 1: Make Scripts Executable
```bash
cd /Users/screener-m3/projects/crypto-assistant
chmod +x complete_docker_cleanup.sh
chmod +x remove_health_checks.sh
chmod +x verify_health_checks_removed.sh
chmod +x clean_rebuild.sh
```

### Step 2: Remove Health Checks from Configuration
```bash
# This script removes all health check configurations
./remove_health_checks.sh
```

**What this does:**
- Backs up all Docker files with timestamp
- Removes healthcheck sections from all docker-compose files
- Removes HEALTHCHECK commands from Dockerfiles
- Removes curl dependencies (only needed for health checks)
- Creates clean configurations ready for rebuild

### Step 3: Verify Health Checks Are Gone
```bash
# This script verifies complete removal
./verify_health_checks_removed.sh
```

**What this checks:**
- All Docker configuration files for health check patterns
- Running containers for health status
- Any remaining health endpoint implementations
- Provides clear pass/fail results

### Step 4: Complete Docker Cleanup
```bash
# This script removes ALL Docker cache and containers
./complete_docker_cleanup.sh
```

**What this does:**
- Stops all running containers
- Removes all containers (including stopped ones)
- Removes all images
- Removes all networks
- Removes all volumes
- Clears all build cache
- Performs system-wide Docker cleanup

### Step 5: Clean Rebuild
```bash
# This script performs a complete clean rebuild
./clean_rebuild.sh
```

**What this does:**
- Runs final health check verification
- Performs targeted project cleanup
- Builds services with no cache
- Starts services with clean configuration
- Verifies services are running properly
- Provides detailed status report

## Manual Verification Commands

### Check Docker System Status
```bash
# View Docker disk usage
docker system df

# List all containers
docker ps -a

# List all images
docker images

# List all networks
docker network ls

# List all volumes
docker volume ls
```

### Check Container Status (After Rebuild)
```bash
# Check running containers
docker-compose ps

# View service logs
docker-compose logs -f

# Test market-data service
curl http://localhost:8001/health

# Check for health status in container output
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

## Expected Results After Cleanup

### ✅ Successful Cleanup Indicators
- No "healthy" or "unhealthy" status in `docker ps` output
- Containers show "Up" status instead of "Up (healthy)"
- No healthcheck sections in any Docker files
- No curl dependencies in Dockerfiles (unless needed for other purposes)
- Clean Docker system with minimal disk usage

### ❌ Issues That Indicate Incomplete Cleanup
- Containers still showing "unhealthy" status
- Health check configurations found in Docker files
- Large Docker cache still present
- Build failures due to cached layers

## Production Deployment Checklist

Before deploying to production, ensure:

- [ ] All health checks removed from Docker configurations
- [ ] Complete Docker cleanup performed
- [ ] Clean rebuild successful
- [ ] Services start and run without health check dependencies
- [ ] Container status shows "Up" not "healthy"
- [ ] No health check errors in logs
- [ ] API endpoints still functional

## Emergency Rollback

If issues occur, rollback files are available in:
```
docker-backup-YYYYMMDD-HHMMSS/
├── docker-compose.yml.backup
├── docker-compose.yml.working.backup
├── docker-compose.production.yml.backup
├── market-data-Dockerfile.backup
└── telegram-bot-Dockerfile.backup
```

To rollback:
```bash
# Find backup directory
ls -la docker-backup-*

# Restore files (replace TIMESTAMP with actual timestamp)
cp docker-backup-TIMESTAMP/docker-compose.yml.backup docker-compose.yml
cp docker-backup-TIMESTAMP/market-data-Dockerfile.backup services/market-data/Dockerfile
cp docker-backup-TIMESTAMP/telegram-bot-Dockerfile.backup services/telegram-bot/Dockerfile
```

## Key Files Modified

### docker-compose.yml
- **Removed:** healthcheck section from market-data service
- **Result:** Clean service definition without health monitoring

### services/market-data/Dockerfile
- **Removed:** HEALTHCHECK command
- **Removed:** curl dependency
- **Result:** Minimal container image

### services/telegram-bot/Dockerfile
- **Removed:** curl dependency
- **Result:** Minimal container image

## Production Safety Notes

1. **No Health Checks**: Containers will show "Up" status instead of "healthy"
2. **Monitoring**: Use external monitoring instead of Docker health checks
3. **Logging**: Monitor application logs for health status
4. **Testing**: Verify API endpoints respond correctly

## Script Execution Order

```bash
# 1. Remove health checks
./remove_health_checks.sh

# 2. Verify removal
./verify_health_checks_removed.sh

# 3. Complete cleanup
./complete_docker_cleanup.sh

# 4. Clean rebuild
./clean_rebuild.sh

# 5. Final verification
./verify_health_checks_removed.sh
```

## Troubleshooting

### Build Failures
- Check Docker daemon is running
- Verify internet connection
- Review Dockerfile syntax
- Check available disk space

### Service Failures
- Review application logs
- Check environment variables
- Verify port availability
- Ensure dependencies are met

### Health Check Remnants
- Re-run verification script
- Check for cached Docker layers
- Verify all configuration files updated
- Perform complete system cleanup

---

**⚠️ CRITICAL**: This cleanup removes ALL Docker cache and will require rebuilding all images. Only proceed when you have time for a complete rebuild process.

**✅ PRODUCTION READY**: After successful completion, the system will be completely clean and ready for production deployment without health check dependencies.