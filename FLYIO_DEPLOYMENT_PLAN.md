# 🚀 Fly.io Deployment Plan: Professional Dev/Prod Setup

## 🎯 **Overview**
Deploy crypto trading bot to Fly.io with complete dev/prod separation, ensuring zero downtime and professional workflow.

---

## 📋 **Pre-Deployment Analysis**

### **Current Project State**
- ✅ **Architecture**: 2-service microservices (market-data + telegram-bot)
- ✅ **Containerization**: Docker-ready with health checks
- ✅ **Environment Config**: .env structure established
- ✅ **Exchange Integration**: 6 exchanges (Binance, Bybit, OKX, Gate.io, Bitget, Hyperliquid)
- ✅ **Git Status**: Clean working tree, ready for deployment

### **Services to Deploy**
```
┌─ market-data ────────────────────┐
│ • Port: 8001                     │
│ • API endpoints for market data  │
│ • 6-exchange integration         │
│ • Health checks enabled          │
└──────────────────────────────────┘

┌─ telegram-bot ───────────────────┐
│ • Depends on market-data         │
│ • Telegram integration           │
│ • User command processing        │
│ • Real-time market analysis      │
└──────────────────────────────────┘
```

---

## 🔧 **Phase 1: Dev/Prod Bot Separation**

### **Step 1.1: Create Development Bot**
```bash
# Go to @BotFather in Telegram
# Use /newbot command
# Name: CryptoAssistantDevBot
# Username: @your_crypto_dev_bot
# Save the new token for dev environment
```

### **Step 1.2: Environment File Structure**
```
crypto-assistant/
├── .env                 # Current (will become backup)
├── dev.env             # Development environment
├── prod.env            # Production environment
├── .env.example        # Template (already exists)
└── .gitignore          # Ensure *.env is ignored
```

### **Step 1.3: Create Environment Files**

#### **dev.env (Local Development)**
```bash
# Telegram Bot Configuration (DEV)
TELEGRAM_BOT_TOKEN=your_NEW_dev_bot_token_here
TELEGRAM_CHAT_ID=your_dev_chat_id_here

# Exchange API Keys (Same as prod - read-only)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true

BYBIT_API_KEY=your_bybit_api_key
BYBIT_SECRET_KEY=your_bybit_secret_key
BYBIT_TESTNET=true

# Development Settings
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///data/crypto_assistant_dev.db
REDIS_URL=redis://localhost:6379
```

#### **prod.env (Production Reference)**
```bash
# Telegram Bot Configuration (PROD)
TELEGRAM_BOT_TOKEN=your_ORIGINAL_prod_bot_token_here
TELEGRAM_CHAT_ID=your_prod_chat_id_here

# Exchange API Keys (Same as dev - read-only)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=false

BYBIT_API_KEY=your_bybit_api_key
BYBIT_SECRET_KEY=your_bybit_secret_key
BYBIT_TESTNET=false

# Production Settings
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///data/crypto_assistant.db
REDIS_URL=redis://localhost:6379
```

---

## 🐋 **Phase 2: Fly.io Configuration**

### **Step 2.1: Install Fly.io CLI**
```bash
# macOS
brew install flyctl

# Or direct download
curl -L https://fly.io/install.sh | sh

# Authenticate
flyctl auth login
```

### **Step 2.2: Create Fly.io App Configuration**

#### **fly.toml (Main Configuration)**
```toml
app = "crypto-assistant-prod"
primary_region = "iad"  # US East (Virginia)

[build]
  dockerfile = "fly.Dockerfile"

[env]
  LOG_LEVEL = "INFO"
  MARKET_DATA_URL = "http://localhost:8001"

[experimental]
  auto_rollback = true

[[services]]
  internal_port = 8001
  protocol = "tcp"
  
  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [services.tcp_checks]
    grace_period = "10s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

[checks]
  [checks.market_data_health]
    grace_period = "30s"
    interval = "15s"
    method = "get"
    path = "/health"
    port = 8001
    protocol = "http"
    restart_limit = 0
    timeout = "10s"
```

### **Step 2.3: Create Fly.io Dockerfile**

#### **fly.Dockerfile**
```dockerfile
# Multi-stage build for Fly.io deployment
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY services/market-data/requirements.txt ./market-data-requirements.txt
COPY services/telegram-bot/requirements.txt ./telegram-bot-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r market-data-requirements.txt
RUN pip install --no-cache-dir -r telegram-bot-requirements.txt

# Copy application code
COPY services/ ./services/
COPY data/ ./data/

# Create startup script
COPY start-fly.sh ./start-fly.sh
RUN chmod +x start-fly.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Start services
CMD ["./start-fly.sh"]
```

### **Step 2.4: Create Startup Script**

#### **start-fly.sh**
```bash
#!/bin/bash
set -e

echo "🚀 Starting Crypto Assistant on Fly.io..."

# Start market-data service in background
echo "📊 Starting market-data service..."
cd /app/services/market-data
python main.py &
MARKET_DATA_PID=$!

# Wait for market-data to be ready
echo "⏳ Waiting for market-data service..."
sleep 10

# Check if market-data is healthy
for i in {1..30}; do
  if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Market-data service is healthy"
    break
  fi
  echo "⏳ Waiting for market-data... ($i/30)"
  sleep 2
done

# Start telegram-bot service
echo "🤖 Starting telegram-bot service..."
cd /app/services/telegram-bot
python main.py &
TELEGRAM_BOT_PID=$!

echo "🎯 All services started successfully!"
echo "📊 Market-data PID: $MARKET_DATA_PID"
echo "🤖 Telegram-bot PID: $TELEGRAM_BOT_PID"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
```

---

## 🔐 **Phase 3: Security & Secrets Management**

### **Step 3.1: Set Production Secrets**
```bash
# Navigate to project directory
cd /Users/screener-m3/projects/crypto-assistant

# Create Fly.io app
flyctl apps create crypto-assistant-prod

# Set production secrets (DO NOT commit these)
flyctl secrets set TELEGRAM_BOT_TOKEN="your_prod_bot_token" --app crypto-assistant-prod
flyctl secrets set TELEGRAM_CHAT_ID="your_prod_chat_id" --app crypto-assistant-prod
flyctl secrets set BINANCE_API_KEY="your_binance_key" --app crypto-assistant-prod
flyctl secrets set BINANCE_SECRET_KEY="your_binance_secret" --app crypto-assistant-prod
flyctl secrets set BYBIT_API_KEY="your_bybit_key" --app crypto-assistant-prod
flyctl secrets set BYBIT_SECRET_KEY="your_bybit_secret" --app crypto-assistant-prod

# Set production flags
flyctl secrets set BINANCE_TESTNET="false" --app crypto-assistant-prod
flyctl secrets set BYBIT_TESTNET="false" --app crypto-assistant-prod
```

### **Step 3.2: Update .gitignore**
```bash
# Ensure sensitive files are never committed
echo "*.env" >> .gitignore
echo ".env.*" >> .gitignore
echo "fly.toml" >> .gitignore  # Optional: if contains sensitive info
```

---

## 🧪 **Phase 4: Testing Protocol**

### **Step 4.1: Local Development Testing**
```bash
# Test with development environment
docker-compose --env-file dev.env up

# Verify dev bot responds in Telegram
# Test all major commands:
# /start, /analysis BTC-USDT 15m, /volume SOL-USDT, etc.
```

### **Step 4.2: Production Deployment Testing**
```bash
# Deploy to Fly.io
flyctl deploy --app crypto-assistant-prod

# Monitor deployment
flyctl logs --app crypto-assistant-prod

# Test production bot
flyctl ssh console --app crypto-assistant-prod

# Health check
flyctl status --app crypto-assistant-prod
```

### **Step 4.3: Validation Checklist**
- [ ] ✅ Dev bot works locally with dev.env
- [ ] ✅ Prod bot deploys successfully to Fly.io
- [ ] ✅ Both bots can run simultaneously
- [ ] ✅ Market data service health checks pass
- [ ] ✅ All Telegram commands work in both environments
- [ ] ✅ Exchange API connections successful
- [ ] ✅ No sensitive data in git repository

---

## 📈 **Phase 5: Monitoring & Maintenance**

### **Step 5.1: Monitoring Setup**
```bash
# Real-time monitoring
flyctl logs --app crypto-assistant-prod -f

# App metrics
flyctl metrics --app crypto-assistant-prod

# Health status
flyctl status --app crypto-assistant-prod
```

### **Step 5.2: Update Workflow**
```bash
# Development workflow
1. Test changes locally: docker-compose --env-file dev.env up
2. Validate with dev bot in Telegram
3. Commit changes: git add . && git commit -m "feature: description"
4. Deploy to production: flyctl deploy --app crypto-assistant-prod
5. Verify production bot functionality
```

---

## 🎯 **Deployment Commands Summary**

### **Development (Local)**
```bash
# Start dev environment
docker-compose --env-file dev.env up

# Stop dev environment
docker-compose --env-file dev.env down
```

### **Production (Fly.io)**
```bash
# Initial deployment
flyctl deploy --app crypto-assistant-prod

# Update deployment
flyctl deploy --app crypto-assistant-prod

# Check status
flyctl status --app crypto-assistant-prod

# View logs
flyctl logs --app crypto-assistant-prod

# SSH into production
flyctl ssh console --app crypto-assistant-prod
```

---

## 🔄 **Deployment Methods**

### **Method 1: Direct Deployment (Recommended for Start)**
- ✅ **How**: From your PC directly to Fly.io
- ✅ **Command**: `flyctl deploy`
- ✅ **Pros**: Simple, immediate feedback, full control
- ❌ **Cons**: Manual process, requires local flyctl setup

### **Method 2: GitHub Actions (Future Enhancement)**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Fly.io
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

---

## 🎖️ **Success Criteria**

### **Development Environment**
- [ ] ✅ Dev bot token configured and working
- [ ] ✅ Local Docker containers start successfully
- [ ] ✅ Dev bot responds to Telegram commands
- [ ] ✅ Market data service accessible on localhost:8001

### **Production Environment**
- [ ] ✅ Fly.io app created and configured
- [ ] ✅ Production secrets set securely
- [ ] ✅ Health checks passing
- [ ] ✅ Production bot responds to Telegram commands
- [ ] ✅ 24/7 uptime achieved

### **Operational Excellence**
- [ ] ✅ Zero production downtime during updates
- [ ] ✅ Clear separation between dev and prod
- [ ] ✅ Comprehensive monitoring and logging
- [ ] ✅ Secure secret management
- [ ] ✅ Reliable deployment process

---

**Ready for systematic implementation!** 🚀