# Deployment Verification Checklist

## Problem Identified
Claude should automatically verify deployments are working before marking them complete, rather than requiring user to manually check.

## Mandatory Verification Steps

### 1. Container Status Check
```bash
docker ps | grep crypto-
# Verify both containers running with recent "Up" times
```

### 2. Service Health Check
```bash
curl -f http://localhost:8001/health
# Verify market-data service responding
```

### 3. Functionality Verification
```bash
curl -X POST http://localhost:8001/market_profile -H "Content-Type: application/json" -d '{"symbol": "BTC-USDT"}'
# Verify API returns expected data structure
```

### 4. Code Change Validation
- Check session periods show expected reset times
- Verify new features (30m profile) are present
- Test accuracy improvements are active

### 5. User-Facing Validation
- Test telegram bot responds to commands
- Verify output format matches expectations
- Check no regressions in functionality

## Automation Strategy

### Required: Always verify before claiming "deployment complete"
1. Run health checks automatically
2. Test core functionality
3. Validate specific changes made
4. Report verification results to user
5. Only mark complete after verification passes

### Process Improvement
- Build verification into deployment workflow
- Automate testing of changes
- Provide evidence of working deployment
- Don't require user to manually validate

## Lesson Learned
Never claim deployment is complete without automated verification that the changes are actually working as expected.