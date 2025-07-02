# 🚀 Rapid Iteration Project Structure
## Optimized for Weekly Priorities & 1-2 Day Delivery Cycles

## 🎯 **Key Requirements Addressed**
- **Team Scale**: 1 → 4-5 developers
- **Priority Changes**: Weekly (7-10 days)
- **Delivery Cycle**: 1-2 days
- **Quality Tools**: Ruff + pytest + mypy + agentic tools
- **File Discovery**: Everything has a clear place

---

## 📁 **Optimized Directory Structure**

```
crypto-assistant/
├── 📁 src/                           # Production code only
│   ├── exchanges/                    # Exchange integrations
│   │   ├── __init__.py
│   │   ├── base.py                  # Base provider interface
│   │   ├── binance.py               # One file per exchange
│   │   ├── bybit.py
│   │   ├── hyperliquid.py
│   │   └── unified_aggregator.py    # Main aggregation logic
│   ├── analysis/                     # Market analysis
│   │   ├── __init__.py
│   │   ├── volume.py                # Volume analysis
│   │   ├── cvd.py                   # CVD calculations
│   │   ├── indicators.py            # Technical indicators
│   │   └── sentiment.py             # Market sentiment
│   ├── services/                     # Service layer
│   │   ├── __init__.py
│   │   ├── api_server.py            # FastAPI server
│   │   ├── telegram_bot.py          # TG bot service
│   │   └── data_collector.py        # Background data collection
│   ├── utils/                        # Shared utilities
│   │   ├── __init__.py
│   │   ├── formatters.py            # Message formatting
│   │   ├── validators.py            # Data validation
│   │   └── cache.py                 # Caching utilities
│   └── config/                       # Configuration
│       ├── __init__.py
│       ├── settings.py              # App settings
│       └── exchanges.py             # Exchange configs
├── 📁 tests/                         # All testing
│   ├── conftest.py                  # pytest configuration
│   ├── unit/                        # Fast unit tests
│   │   ├── test_exchanges.py
│   │   ├── test_analysis.py
│   │   └── test_utils.py
│   ├── integration/                  # Integration tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_telegram_flows.py
│   │   └── test_exchange_integration.py
│   ├── e2e/                         # End-to-end tests
│   │   ├── test_user_scenarios.py
│   │   └── test_production_flows.py
│   └── fixtures/                    # Test data
│       ├── exchange_responses/
│       └── expected_outputs/
├── 📁 docs/                          # Documentation
│   ├── README.md                    # Quick start guide
│   ├── api.md                       # API documentation
│   ├── deployment.md                # Deployment guide
│   └── architecture.md              # System architecture
├── 📁 features/                      # 🔥 RAPID FEATURE TRACKING
│   ├── 📋 CURRENT_SPRINT.md         # Current week's work
│   ├── 📋 FEATURE_BOARD.md          # Kanban-style tracking
│   ├── 🟢 completed/                # Completed features
│   ├── 🟡 active/                   # Currently working (1-3 max)
│   ├── 🔴 next/                     # Next sprint candidates
│   └── 📝 ideas/                    # Future ideas (unrefined)
├── 📁 scripts/                       # Development automation
│   ├── setup.sh                    # Environment setup
│   ├── test.sh                     # Run all tests
│   ├── deploy.sh                   # Deploy to production
│   ├── lint.sh                     # Code quality checks
│   └── agent_generate.py           # 🤖 Agentic code generation
├── 📁 tools/                         # Development tools
│   ├── validation/                  # External validators
│   ├── monitoring/                  # Health checks
│   └── generators/                  # Code generators
├── 📁 tmp/                          # 🗑️ TEMPORARY DUMPING GROUND
│   ├── investigations/              # Debug scripts (auto-clean)
│   ├── experiments/                 # Quick tests (auto-clean)
│   ├── drafts/                     # Draft documents (auto-clean)
│   └── _cleanup_log.md             # What was cleaned when
├── 📁 deployment/                    # Deployment configs
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── docker-compose.prod.yml
│   └── k8s/                        # Future Kubernetes
├── 📁 archive/                       # Historical (read-only)
│   ├── 2025-06/                    # Archived by month
│   └── deprecated/                 # Old implementations
├── 📋 pyproject.toml                # Python project config
├── 📋 requirements.txt              # Dependencies
├── 📋 Makefile                     # Development commands
├── 📋 .pre-commit-config.yaml      # Quality hooks
├── 📋 .gitignore                   # Git ignore
├── 📋 CHANGELOG.md                 # Version history
└── 📋 README.md                    # Project overview
```

---

## 🔥 **Rapid Feature Management System**

### **FEATURE_BOARD.md (Kanban Style)**
```markdown
# 📋 Feature Board - Week of Jan 15-21, 2025

## 🟡 ACTIVE (Max 3) - Current Sprint
| Feature | Owner | Status | ETA | Priority |
|---------|-------|--------|-----|----------|
| Multi-Exchange Long/Short | @dev1 | 80% | 1 day | Critical |
| Performance Optimization | @dev2 | 30% | 2 days | High |

## 🔴 NEXT (Ready for Sprint) - Next Week
| Feature | Effort | Priority | Dependencies |
|---------|--------|----------|--------------|
| Historical Analytics | Large | Medium | Database setup |
| Advanced Alerts | Medium | High | Performance opt |
| Mobile API | Small | Low | None |

## 🟢 COMPLETED (This Week)
- ✅ Hyperliquid Integration (3 days)
- ✅ Docker Deployment Fix (1 day)

## 📝 IDEAS (Unrefined)
- Voice alerts
- AI-powered predictions
- Arbitrage detection
```

### **CURRENT_SPRINT.md (Daily Tracking)**
```markdown
# 🚀 Current Sprint: Jan 15-21, 2025

## 🎯 Sprint Goals
1. Complete Multi-Exchange Long/Short integration
2. Optimize response times <1s
3. Deploy performance improvements

## 📅 Daily Progress

### Monday Jan 15
**@dev1**: Started Bybit long/short API integration
**@dev2**: Profiling current response times
**Blockers**: None

### Tuesday Jan 16  
**@dev1**: Bybit + OKX APIs working, testing accuracy
**@dev2**: Identified 3 major bottlenecks, fixing async calls
**Blockers**: Waiting for OKX API keys

### Wednesday Jan 17
**@dev1**: All 6 exchanges integrated, external validation pending
**@dev2**: Response time down to 0.8s average
**Blockers**: None - ready for deployment
```

---

## 🛠️ **Rapid Development Toolchain**

### **Quality Tools Configuration**
```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = ["E501", "B008", "B904"]

[tool.ruff.per-file-ignores]
"tests/*" = ["B018", "S101"]
"scripts/*" = ["T201"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing:skip-covered",
    "--cov-fail-under=80",
]
```

### **Agentic Development Tools**
```python
# scripts/agent_generate.py
"""
🤖 Agentic Code Generation for Rapid Development
Integrates with Claude Code for automated implementation
"""

import subprocess
import json
from pathlib import Path

class AgenticGenerator:
    def __init__(self):
        self.templates = Path("tools/generators/templates")
        self.test_templates = Path("tools/generators/test_templates")
    
    def generate_exchange_provider(self, exchange_name: str):
        """Generate new exchange provider with tests"""
        template = self.templates / "exchange_provider.py.j2"
        test_template = self.test_templates / "test_exchange.py.j2"
        
        # Generate provider
        provider_path = f"src/exchanges/{exchange_name}.py"
        self._render_template(template, provider_path, {"exchange": exchange_name})
        
        # Generate tests
        test_path = f"tests/unit/test_{exchange_name}.py"
        self._render_template(test_template, test_path, {"exchange": exchange_name})
        
        # Generate integration test
        integration_path = f"tests/integration/test_{exchange_name}_integration.py"
        self._render_template(self.test_templates / "integration.py.j2", 
                            integration_path, {"exchange": exchange_name})
        
        print(f"✅ Generated {exchange_name} provider with full test suite")
    
    def generate_feature_scaffold(self, feature_name: str):
        """Generate complete feature scaffold"""
        # Create feature documentation
        feature_doc = f"features/active/{feature_name}.md"
        self._create_feature_doc(feature_doc, feature_name)
        
        # Generate code scaffold
        self._generate_code_scaffold(feature_name)
        
        # Generate test scaffold
        self._generate_test_scaffold(feature_name)
        
        print(f"✅ Generated complete scaffold for {feature_name}")
    
    def validate_with_external_llm(self, feature_path: str):
        """Validate implementation with external LLM"""
        # Integration point for external validation
        pass

# Usage examples:
# python scripts/agent_generate.py --exchange kraken
# python scripts/agent_generate.py --feature advanced-alerts
# python scripts/agent_generate.py --validate src/exchanges/new_exchange.py
```

### **Rapid Development Makefile**
```makefile
# Makefile - Optimized for 1-2 day delivery cycles
.PHONY: help setup quick-test full-test lint format validate deploy clean tmp-clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup development environment (5 min)
	pip install -r requirements.txt
	pre-commit install
	chmod +x scripts/*.sh
	docker-compose up -d
	@echo "✅ Environment ready for development"

quick-test: ## Run quick tests only (30 seconds)
	pytest tests/unit/ -x -q --disable-warnings
	ruff check src/ --quiet
	@echo "✅ Quick validation passed"

full-test: ## Run complete test suite (2-3 minutes)
	pytest tests/ -v --cov=src --cov-report=term-missing
	ruff check src/ tests/
	mypy src/
	@echo "✅ Full validation passed"

lint: ## Fix code style (10 seconds)
	ruff format src/ tests/
	ruff check src/ tests/ --fix
	@echo "✅ Code formatted and linted"

validate: ## External validation for production (5 minutes)
	make full-test
	python tools/validation/external_validator.py
	python tools/validation/security_scan.py
	@echo "✅ Production validation complete"

deploy: ## Deploy to production (2 minutes)
	make validate
	docker-compose -f deployment/docker/docker-compose.prod.yml up -d --build
	python tools/monitoring/health_check.py
	@echo "✅ Deployed to production"

clean: ## Clean up build artifacts
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ .ruff_cache/

tmp-clean: ## Clean temporary files (run weekly)
	@echo "🗑️ Cleaning tmp/ directory..."
	find tmp/ -type f -name "*.py" -mtime +7 -delete
	find tmp/ -type f -name "*.md" -mtime +3 -delete
	find tmp/ -empty -type d -delete
	echo "$(date): Auto-cleaned tmp/ directory" >> tmp/_cleanup_log.md
	@echo "✅ Temporary files cleaned"

# Rapid development shortcuts
dev: setup quick-test ## Setup + quick test (ready to code)
ship: validate deploy ## Full validation + deploy to production
feature: ## Generate new feature scaffold
	@read -p "Feature name: " name; python scripts/agent_generate.py --feature "$$name"
exchange: ## Generate new exchange provider
	@read -p "Exchange name: " name; python scripts/agent_generate.py --exchange "$$name"
```

---

## 🗑️ **Temporary File Management Strategy**

### **tmp/ Directory Structure**
```
tmp/                                  # Auto-cleaned regularly
├── investigations/                   # Debug scripts (7-day TTL)
├── experiments/                     # Quick prototypes (3-day TTL)  
├── drafts/                         # Draft documents (3-day TTL)
├── agent_outputs/                  # LLM generated code (5-day TTL)
├── _cleanup_log.md                 # Track what was cleaned
└── .gitignore                      # Ignore tmp/ contents
```

### **Auto-Cleanup Rules**
```bash
# scripts/tmp_cleanup.sh (runs weekly via cron)
#!/bin/bash
echo "🗑️ Weekly tmp/ cleanup - $(date)"

# Clean old investigation scripts
find tmp/investigations/ -name "*.py" -mtime +7 -delete
find tmp/investigations/ -name "*.md" -mtime +7 -delete

# Clean old experiments  
find tmp/experiments/ -name "*" -mtime +3 -delete

# Clean old drafts
find tmp/drafts/ -name "*.md" -mtime +3 -delete

# Clean old agent outputs
find tmp/agent_outputs/ -name "*" -mtime +5 -delete

# Remove empty directories
find tmp/ -empty -type d -delete

# Log cleanup
echo "$(date): Auto-cleanup completed" >> tmp/_cleanup_log.md
echo "✅ tmp/ directory cleaned"
```

---

## 🚀 **Migration Plan: Current → Rapid Structure**

### **🔥 Phase 1: Emergency Cleanup (1 Day)**
```bash
# Create new structure
mkdir -p src/{exchanges,analysis,services,utils,config}
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p features/{completed,active,next,ideas}
mkdir -p tmp/{investigations,experiments,drafts,agent_outputs}
mkdir -p scripts tools docs deployment archive

# Emergency file sorting
echo "🚨 EMERGENCY CLEANUP - Moving scattered files"

# Move production code
mv *_provider.py src/exchanges/ 2>/dev/null || true
mv unified_oi_aggregator.py src/exchanges/ 2>/dev/null || true
mv *_analysis.py src/analysis/ 2>/dev/null || true

# Move test files
mv test_*.py tests/integration/ 2>/dev/null || true

# Move investigation files to tmp
mv debug_*.py tmp/investigations/ 2>/dev/null || true
mv investigate_*.py tmp/investigations/ 2>/dev/null || true
mv validate_*.py tmp/investigations/ 2>/dev/null || true

# Move documentation
mv PROJECT_ROADMAP.md docs/ 2>/dev/null || true
mv TECHNICAL_ASSESSMENT_ANALYSIS.md docs/ 2>/dev/null || true
mv DEPLOYMENT_SUCCESS.md docs/ 2>/dev/null || true

# Archive session files
mkdir -p archive/2025-06-agent-sessions
mv AGENT_*_INSTRUCTIONS.md archive/2025-06-agent-sessions/ 2>/dev/null || true
mv SESSION_*.md archive/2025-06-agent-sessions/ 2>/dev/null || true
mv *_COMPLETION_REPORT.md archive/2025-06-agent-sessions/ 2>/dev/null || true

echo "✅ Emergency cleanup complete - structure established"
```

### **⚡ Phase 2: Rapid Tooling Setup (1 Day)**
```bash
# Setup development toolchain
cat > pyproject.toml << EOF
[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--cov=src", "--cov-fail-under=80"]
EOF

# Setup pre-commit hooks
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
EOF

# Create rapid development commands
cat > Makefile << 'EOF'
# ... (Makefile content from above)
EOF

# Setup agentic generation tools
python scripts/agent_generate.py --setup

echo "✅ Rapid development toolchain ready"
```

### **📋 Phase 3: Feature Board Setup (1 Day)**
```bash
# Create current sprint tracking
cat > features/CURRENT_SPRINT.md << EOF
# 🚀 Current Sprint: Week of $(date +%b\ %d-%d,\ %Y)

## 🎯 Sprint Goals
1. Complete project restructure
2. Establish rapid development workflow
3. Validate new structure with team

## 📅 Daily Progress
### $(date +%A\ %b\ %d)
**Restructure**: Emergency cleanup complete
**Tooling**: Development toolchain operational
**Status**: Ready for team onboarding
EOF

# Create feature board
cat > features/FEATURE_BOARD.md << EOF
# 📋 Feature Board

## 🟡 ACTIVE (Current Sprint)
| Feature | Owner | Status | ETA | Priority |
|---------|-------|--------|-----|----------|
| Project Restructure | @lead | 90% | 1 day | Critical |

## 🔴 NEXT (Ready for Sprint)
| Feature | Effort | Priority | Dependencies |
|---------|--------|----------|--------------|
| Multi-Exchange Long/Short | Medium | High | Structure complete |
| Performance Optimization | Small | Medium | None |

## 📝 IDEAS (Unrefined)
- Historical analytics with database
- Advanced alert system
- Mobile API endpoints
EOF

echo "✅ Feature tracking system operational"
```

---

## 🎯 **Team Scaling Preparation**

### **Developer Onboarding (5 minutes)**
```bash
# New developer setup
git clone <repo>
cd crypto-assistant
make setup          # 5 minute automated setup
make quick-test     # Verify everything works
code .              # Start coding
```

### **Team Workflow**
```markdown
## Daily Workflow (Each Developer)
1. **Check Sprint Board**: features/CURRENT_SPRINT.md
2. **Pick Task**: From features/FEATURE_BOARD.md  
3. **Quick Start**: make dev (setup + test)
4. **Code**: Implement feature with agentic help
5. **Validate**: make quick-test (30 seconds)
6. **Ship**: make ship (full validation + deploy)
7. **Update Board**: Mark progress in sprint doc

## Weekly Workflow (Team)
1. **Sprint Review**: What shipped this week?
2. **Retrospective**: What can improve?
3. **Planning**: Move features from next → active
4. **Cleanup**: make tmp-clean
```

---

## 📊 **Success Metrics**

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| **File Discovery Time** | 2-5 minutes | <30 seconds | Immediate |
| **New Feature Setup** | 1-2 hours | 5 minutes | 1 week |
| **Test Running** | Manual, slow | 30 seconds automated | 1 week |
| **Deploy Time** | 30+ minutes | 2 minutes | 1 week |
| **Team Onboarding** | Days | 5 minutes | 2 weeks |
| **Code Quality** | Inconsistent | Automated enforcement | 1 week |

**Ready to execute?** This structure transforms your project into a **high-velocity development machine** optimized for weekly priority changes and 1-2 day delivery cycles.