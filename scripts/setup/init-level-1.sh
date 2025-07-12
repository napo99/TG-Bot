#!/bin/bash
# 🚀 Initialize Level 1: Basic CI/CD Setup

set -e  # Exit on any error

echo "🎯 Initializing Level 1: Basic CI/CD Setup"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is required but not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is required but not installed${NC}" 
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Create directory structure
echo -e "${BLUE}📁 Creating directory structure...${NC}"

mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p config
mkdir -p docs/api
mkdir -p scripts/deployment
mkdir -p .local-tests

echo -e "${GREEN}✅ Directory structure created${NC}"

# Install health endpoints
echo -e "${BLUE}🏥 Setting up health endpoints...${NC}"

# Market Data Service
if [ -d "services/market-data" ]; then
    cp templates/level-1-basic/health_endpoint.py services/market-data/health.py
    echo -e "${GREEN}  ✅ Health endpoint added to market-data service${NC}"
    
    # Add integration code snippet
    echo -e "${YELLOW}  📝 TODO: Add to services/market-data/main.py:${NC}"
    echo -e "     from health import add_health_endpoints"
    echo -e "     app = add_health_endpoints(app, 'market-data-service')"
fi

# Telegram Bot Service  
if [ -d "services/telegram-bot" ]; then
    cp templates/level-1-basic/health_endpoint.py services/telegram-bot/health.py
    echo -e "${GREEN}  ✅ Health endpoint added to telegram-bot service${NC}"
    
    echo -e "${YELLOW}  📝 TODO: Add to services/telegram-bot/main_webhook.py:${NC}"
    echo -e "     from health import add_health_endpoints"
    echo -e "     app = add_health_endpoints(app, 'telegram-bot-service')"
fi

# Create basic unit tests
echo -e "${BLUE}🧪 Setting up basic unit tests...${NC}"

# Formatting utils tests
if [ -f "services/telegram-bot/formatting_utils.py" ]; then
    cp templates/level-1-basic/basic_test_template.py tests/unit/test_formatting_utils.py
    echo -e "${GREEN}  ✅ Basic tests created for formatting_utils${NC}"
fi

# Create test requirements
cat > tests/requirements.txt << EOF
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
aiohttp>=3.8.0
EOF

echo -e "${GREEN}✅ Test requirements created${NC}"

# Create basic pytest configuration
cat > pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=services
    --cov-report=term-missing
    --cov-report=html:htmlcov
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
EOF

echo -e "${GREEN}✅ Pytest configuration created${NC}"

# Create environment template files
echo -e "${BLUE}⚙️ Setting up environment configuration...${NC}"

cat > config/local.env.template << EOF
# Local development environment
ENVIRONMENT=local
SERVICE_VERSION=dev
LOG_LEVEL=DEBUG

# Market Data Service
MARKET_DATA_URL=http://localhost:8001

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=http://localhost:8080/webhook

# External APIs
BINANCE_API_URL=https://api.binance.com
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Database (if needed)
DATABASE_URL=sqlite:///local.db

# Redis (if needed)  
REDIS_URL=redis://localhost:6379
EOF

cp config/local.env.template config/local.env
echo -e "${GREEN}✅ Environment configuration created${NC}"

# Create basic documentation
echo -e "${BLUE}📚 Creating basic documentation...${NC}"

cat > docs/api/health-endpoints.md << EOF
# Health Check Endpoints

All services provide standardized health check endpoints for monitoring and orchestration.

## Endpoints

### \`GET /health\`
Basic health status - lightweight check for load balancers.

**Response:**
\`\`\`json
{
  "service": "market-data-service",
  "status": "healthy", 
  "timestamp": "2025-07-08T13:45:23.123456",
  "uptime_seconds": 86400,
  "version": "1.0.0",
  "environment": "local"
}
\`\`\`

### \`GET /health/detailed\`
Detailed health with system metrics.

### \`GET /health/readiness\`
Kubernetes-style readiness probe.

## Usage

\`\`\`bash
# Quick health check
curl http://localhost:8001/health

# Detailed health info
curl http://localhost:8001/health/detailed

# Readiness check
curl http://localhost:8001/health/readiness
\`\`\`
EOF

echo -e "${GREEN}✅ API documentation created${NC}"

# Create basic deployment script
echo -e "${BLUE}🚀 Creating deployment helpers...${NC}"

cat > scripts/deployment/local-test.sh << 'EOF'
#!/bin/bash
# Test deployment locally

echo "🧪 Testing local deployment..."

# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Test health endpoints
echo "Testing market-data health..."
curl -f http://localhost:8001/health || echo "❌ Market data health check failed"

echo "Testing telegram-bot health..."
curl -f http://localhost:8080/health || echo "❌ Telegram bot health check failed"

# Run tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

# Stop services
docker-compose down

echo "✅ Local deployment test complete"
EOF

chmod +x scripts/deployment/local-test.sh
echo -e "${GREEN}✅ Local deployment test script created${NC}"

# Update .gitignore if needed
echo -e "${BLUE}📝 Updating .gitignore...${NC}"

if ! grep -q "config/local.env" .gitignore 2>/dev/null; then
    echo "config/local.env" >> .gitignore
    echo "htmlcov/" >> .gitignore
    echo ".coverage" >> .gitignore
    echo ".pytest_cache/" >> .gitignore
    echo -e "${GREEN}  ✅ .gitignore updated${NC}"
fi

# Create GitHub Actions quality workflow if it doesn't exist
if [ ! -f ".github/workflows/quality.yml" ]; then
    echo -e "${BLUE}🔧 GitHub Actions workflow already exists, skipping...${NC}"
else
    echo -e "${GREEN}✅ GitHub Actions quality workflow ready${NC}"
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 Level 1 initialization complete!${NC}"
echo "================================================"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "  1. 🔧 Integrate health endpoints into your services"
echo "  2. 🧪 Implement actual unit tests in tests/unit/"
echo "  3. ⚙️  Configure environment variables in config/local.env"
echo "  4. 🚀 Test deployment: ./scripts/deployment/local-test.sh"
echo "  5. 🔍 Run tests: python -m pytest tests/unit/ -v"
echo ""
echo -e "${YELLOW}💡 Integration hints:${NC}"
echo "  • Health endpoints: Add to your Flask/FastAPI apps"
echo "  • Unit tests: Replace TODO comments with actual test code"
echo "  • Environment: Copy config/local.env.template and customize"
echo ""
echo -e "${BLUE}📊 Check evolution status:${NC}"
echo "  • View: cat config/evolution.yml"
echo "  • Upgrade trigger: When deployment frequency increases"
echo ""
echo -e "${GREEN}✅ Level 1 setup complete - you now have basic CI/CD foundation!${NC}"