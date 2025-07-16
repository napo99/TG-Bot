# 🛠️ Staging Deployment Troubleshooting Guide

## 🎯 **Deployment Context**
**Goal**: Deploy enhanced webhook features to staging environment (port 9443) for safe testing before production

## 🚧 **Issues Encountered & Solutions**

### 1. SSH Authentication Issues ✅ SOLVED
**Problem**: 
```bash
ssh -i ~/.ssh/key.pem ubuntu@13.239.14.166
# Permission denied (publickey,gssapi-keyex,gssapi-with-mic)
```

**Root Cause**: Wrong username - AWS instance uses `ec2-user`, not `ubuntu`

**Solution**: 
```bash
# Correct SSH command
ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166
```

**Prevention**: Always check deployment documentation for correct SSH user

### 2. Git Merge Conflicts on AWS ✅ SOLVED
**Problem**:
```bash
error: Your local changes to the following files would be overwritten by merge:
    services/telegram-bot/main_webhook.py
```

**Root Cause**: Local changes on AWS instance conflicting with new commits

**Solution**:
```bash
git stash && git pull origin aws-deployment
```

**Prevention**: Always stash or commit changes before pulling updates

### 3. Docker Network Configuration Issues ✅ SOLVED
**Problem**:
```bash
pull access denied for crypto-market-data, repository does not exist
```

**Root Cause**: Original docker-compose.staging.yml tried to pull non-existent external image

**Solution**: Use existing network and container references:
```yaml
# Instead of external image reference
networks:
  tg-bot_crypto-network:
    external: true

# Reference existing container by name
- MARKET_DATA_URL=http://tg-bot-market-data-1:8001
```

### 4. SSL Port Configuration Issues ⚠️ IN PROGRESS
**Problem**: 
- Staging container running on port 5000 (HTTP) instead of 9443 (HTTPS)
- SSL configuration not applied to staging environment

**Current Status**: 
```bash
curl -k https://13.239.14.166:9443/health  # FAILS - No SSL listener
```

**Root Cause Analysis**:
- Container shows: `Listening at: http://0.0.0.0:5000 (1)`
- Expected: SSL listener on port 9443
- Environment variables may not be properly passed

**Solutions to Try**:
1. **Check Environment Variables**:
   ```bash
   docker exec crypto-telegram-bot-staging env | grep SSL
   ```

2. **Verify SSL Certificate Mount**:
   ```bash
   docker exec crypto-telegram-bot-staging ls -la /app/*.pem
   ```

3. **Update main_webhook.py for Dynamic SSL Port**:
   ```python
   SSL_PORT = os.getenv('SSL_PORT', '8443')
   app.run(host='0.0.0.0', port=int(SSL_PORT), ssl_context=context)
   ```

### 5. AWS Security Group Rules ✅ SOLVED
**Command Used**:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-0d979f270dae48425 \
  --protocol tcp --port 9443 --cidr 0.0.0.0/0 \
  --region ap-southeast-2
```

## 📋 **Deployment Checklist for Future Reference**

### Pre-Deployment Verification
- [ ] ✅ Local changes committed and pushed to GitHub
- [ ] ✅ SSH key located: `~/.ssh/crypto-bot-key.pem`
- [ ] ✅ Correct SSH user: `ec2-user` (not `ubuntu`)
- [ ] ✅ AWS instance health: `curl -k https://13.239.14.166:8443/health`

### Staging Deployment Steps
1. **Connect to AWS**: `ssh -i ~/.ssh/crypto-bot-key.pem ec2-user@13.239.14.166`
2. **Navigate to project**: `cd /home/ec2-user/TG-Bot`
3. **Stash local changes**: `git stash`
4. **Pull latest code**: `git pull origin aws-deployment`
5. **Add security group rule**: 
   ```bash
   aws ec2 authorize-security-group-ingress \
     --group-id sg-0d979f270dae48425 \
     --protocol tcp --port 9443 --cidr 0.0.0.0/0 \
     --region ap-southeast-2
   ```
6. **Deploy staging**: `docker-compose -f docker-compose.staging-simple.yml up -d`
7. **Verify containers**: `docker ps | grep staging`
8. **Check logs**: `docker logs crypto-telegram-bot-staging`
9. **Test health**: `curl -k https://13.239.14.166:9443/health`

### Troubleshooting Commands
```bash
# Container status
docker ps | grep staging

# Container logs
docker logs crypto-telegram-bot-staging --tail 50

# Environment variables
docker exec crypto-telegram-bot-staging env

# SSL certificate verification
docker exec crypto-telegram-bot-staging ls -la /app/*.pem

# Port listening verification
docker exec crypto-telegram-bot-staging netstat -tulpn

# Network connectivity
docker network ls
docker network inspect tg-bot_crypto-network
```

## 🔧 **Current Issue Resolution Strategy**

### SSL Port Configuration Fix
**Next Steps**:
1. Verify webhook code reads SSL_PORT environment variable
2. Ensure SSL certificates are properly mounted
3. Check if Flask app starts with SSL context
4. Compare with working production configuration

### Production vs Staging Differences
| Component | Production (8443) | Staging (9443) | Status |
|-----------|------------------|----------------|---------|
| SSL Certificate | ✅ Working | ❓ Mounted but not used | Investigating |
| Port Mapping | ✅ 8443:8443 | ✅ 9443:9443 | Configured |
| Environment Variables | ✅ SSL_PORT=8443 | ✅ SSL_PORT=9443 | Set |
| Flask SSL Context | ✅ Active | ❌ Missing | **TO FIX** |

## 📚 **Key Learnings**

1. **User Authentication**: AWS instances use `ec2-user`, documentation often shows `ubuntu`
2. **Git Workflow**: Always stash changes on target server before pulling
3. **Docker Networks**: Use existing networks, avoid creating external image dependencies  
4. **SSL Configuration**: Environment variables must be read by application code
5. **Port Mapping**: Container internal port must match SSL port configuration

## 🎯 **Success Criteria**
- [ ] Staging health endpoint responds: `curl -k https://13.239.14.166:9443/health`
- [ ] Enhanced features visible in staging bot responses
- [ ] Production remains unaffected on port 8443
- [ ] Zero downtime deployment achieved