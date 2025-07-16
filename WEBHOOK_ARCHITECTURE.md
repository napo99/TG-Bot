# Webhook Architecture Documentation

## 🏗️ Current Architecture: Polling vs Webhook

### **Why We Preserve Both Architectures**

Currently, both local and production environments use **polling mode** for simplicity and reliability. However, we maintain webhook architecture for future transition to **AWS Lambda/serverless** deployment if resource constraints become an issue.

## 📁 File Structure

### **Polling Architecture (Currently Active)**
```
services/telegram-bot/
├── main.py              # Current polling implementation
├── Dockerfile           # Standard Docker build
└── requirements.txt     # Polling dependencies
```

### **Webhook Architecture (Future Migration)**
```
services/telegram-bot/
├── main_webhook.py      # Webhook implementation (Flask/Gunicorn)
├── Dockerfile.webhook   # Memory-optimized Docker build
├── Dockerfile.aws       # AWS-optimized build
└── deploy_webhook.sh    # Webhook deployment script
```

## ⚡ Webhook Implementation Details

### **main_webhook.py Features:**
- **Flask-based webhook endpoint** (`/webhook`)
- **Gunicorn WSGI server** for production
- **Memory optimization** for serverless environments
- **Same feature parity** as polling version
- **Health check endpoint** (`/health`)

### **When to Transition:**
1. **Resource Constraints**: EC2 costs become prohibitive
2. **Scaling Requirements**: Need auto-scaling capabilities
3. **Lambda Benefits**: Pay-per-request pricing model
4. **Traffic Patterns**: Low-frequency usage patterns

## 🔧 Migration Path

### **Local Testing:**
```bash
# Test webhook locally
cd services/telegram-bot
python main_webhook.py

# Set webhook URL
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=https://your-domain.com/webhook"
```

### **AWS Lambda Deployment:**
```bash
# Build webhook image
docker build -f Dockerfile.webhook -t crypto-bot-webhook .

# Deploy to AWS Lambda (future)
./deploy_webhook.sh production
```

## 📊 Architecture Comparison

| Feature | Polling (Current) | Webhook (Future) |
|---------|------------------|------------------|
| **Resource Usage** | Constant CPU | On-demand |
| **Response Time** | 1-30s delay | Instant |
| **Costs** | Fixed EC2 | Pay-per-request |
| **Complexity** | Simple | Moderate |
| **Reliability** | High | Requires HTTPS |
| **Scaling** | Manual | Automatic |

## 🛡️ Preservation Strategy

### **Files Preserved:**
- ✅ `main_webhook.py` - Complete webhook implementation
- ✅ `Dockerfile.webhook` - Optimized webhook container
- ✅ `Dockerfile.aws` - AWS-specific optimizations
- ✅ `deploy_webhook.sh` - Deployment automation

### **Files Removed:**
- ❌ `fly.toml`, `fly.Dockerfile` - Fly.io specific configurations
- ❌ `main_with_logging.py` - Temporary logging experiments
- ❌ Test and debugging webhook files

## 🎯 Future Migration Considerations

### **Technical Requirements:**
1. **SSL Certificate**: Webhook requires HTTPS endpoint
2. **Domain Setup**: Public domain for webhook URL
3. **Lambda Packaging**: Containerized Lambda deployment
4. **Environment Variables**: Same configuration as polling

### **Migration Steps:**
1. Test webhook locally with ngrok/localhost
2. Deploy webhook to staging environment
3. Gradually shift traffic from polling to webhook
4. Monitor performance and reliability
5. Complete migration once stable

### **Rollback Plan:**
- Webhook and polling implementations are identical in functionality
- Can switch back to polling by changing deployment configuration
- No data loss or feature regression during transition

## 📋 Maintenance Notes

- **Keep webhook code synchronized** with polling implementation
- **Test webhook functionality** during major feature updates
- **Monitor AWS Lambda pricing** for cost optimization opportunities
- **Review webhook security** for production readiness

---

*This documentation ensures we can transition to webhook/Lambda architecture when needed while maintaining current polling reliability.*