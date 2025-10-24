# 🏗️ CRYPTO ASSISTANT - SYSTEM ARCHITECTURE 

## 📊 **SINGLE SOURCE OF TRUTH - SYSTEM OVERVIEW**

### **🎯 CORE PRINCIPLE**
> **ONE FUNCTION = ONE AUTHORITATIVE SYSTEM**
> **NO COMPETING IMPLEMENTATIONS ALLOWED**

---

## 📦 **SERVICE ARCHITECTURE**

### **SERVICES/** 
**Domain-specific applications with clear boundaries**

```
services/
├── telegram-bot/           🤖 USER INTERFACE LAYER
│   ├── main.py            → Bot commands & user interaction
│   ├── formatting_utils.py → Display formatting only
│   └── technical_indicators.py → UI-specific calculations
│
├── market-data/           📈 EXTERNAL API INTEGRATION  
│   ├── main.py            → REST API server
│   ├── binance_client.py  → Exchange connectivity
│   └── data_models.py     → API response models
│
└── monitoring/            🚨 REAL-TIME ALERT PROCESSING
    └── [Future expansion]
```

### **SHARED/**
**Common business logic and infrastructure**

```
shared/
├── intelligence/          🧠 BUSINESS LOGIC & CALCULATIONS
│   ├── dynamic_thresholds.py → SINGLE SOURCE: All threshold calculations
│   └── real_time_pipeline.py → SINGLE SOURCE: Real-time data processing
│
├── models/               📋 DATA STRUCTURES
│   ├── liquidation.py    → Liquidation event models
│   └── market_data.py    → Market data structures
│
├── config/              ⚙️ CONFIGURATION MANAGEMENT
│   └── [Environment variables only - no hardcoded configs]
│
└── utils/               🛠️ UTILITY FUNCTIONS
    └── formatting.py    → Shared formatting utilities
```

---

## 🔒 **SYSTEM BOUNDARIES & OWNERSHIP**

### **STRICT RESPONSIBILITY MATRIX**

| **FUNCTION** | **OWNER** | **ALTERNATIVES FORBIDDEN** |
|-------------|-----------|---------------------------|
| **Threshold Calculations** | `shared/intelligence/dynamic_thresholds.py` | ❌ No hardcoded configs |
| **Real-time Processing** | `shared/intelligence/real_time_pipeline.py` | ❌ No duplicate processors |
| **User Interface** | `services/telegram-bot/main.py` | ❌ No business logic here |
| **Market Data** | `services/market-data/` | ❌ No data logic in telegram-bot |
| **Configuration** | Environment Variables + `.env` | ❌ No multiple config files |

### **INTEGRATION RULES**

```
✅ ALLOWED:
- services/telegram-bot/ imports shared/
- services/market-data/ imports shared/  
- shared/ modules import each other carefully

❌ FORBIDDEN:
- Service-to-service direct imports
- Business logic in UI layer
- Multiple systems for same function
- Hardcoded configurations
```

---

## 🎯 **FEATURE OWNERSHIP MAP**

### **LIQUIDATION MONITORING**
- **Primary Owner**: `shared/intelligence/dynamic_thresholds.py`
- **UI Integration**: `services/telegram-bot/main.py` (commands only)
- **Data Source**: `services/market-data/` (WebSocket feeds)
- **Configuration**: Environment variables only

### **OPEN INTEREST (OI) TRACKING**  
- **Primary Owner**: `shared/intelligence/real_time_pipeline.py`
- **UI Integration**: `services/telegram-bot/main.py` (/oi command)
- **Data Source**: `services/market-data/` (API aggregation)

### **TECHNICAL INDICATORS**
- **Primary Owner**: `services/telegram-bot/technical_indicators.py`
- **Scope**: UI-specific calculations only
- **Complex Logic**: Should move to `shared/intelligence/` if reused

---

## 🛡️ **ARCHITECTURAL CONSTRAINTS**

### **MANDATORY RULES**

1. **Single Responsibility**: One system per function, no exceptions
2. **No Duplication**: Before creating, check if functionality exists  
3. **Clear Boundaries**: Services handle UI/API, shared handles logic
4. **Configuration Unity**: Environment variables only, no multiple config systems
5. **Import Hierarchy**: shared/ ← services/, never services/ ← services/

### **FORBIDDEN PATTERNS**

```python
# ❌ WRONG: Multiple threshold systems
class LiquidationThresholds:     # in telegram-bot/
class DynamicThresholds:         # in shared/intelligence/
class AlertThresholds:           # in shared/config/

# ✅ RIGHT: Single authoritative system  
class UnifiedThresholdSystem:    # in shared/intelligence/ ONLY
```

### **APPROVED PATTERNS**

```python
# ✅ CORRECT: Service imports shared
from shared.intelligence.dynamic_thresholds import ThresholdCalculator

# ✅ CORRECT: Configuration via environment
threshold = float(os.getenv('LIQUIDATION_THRESHOLD_BTC', '500000'))

# ✅ CORRECT: UI formatting separate from business logic
formatted_value = format_large_number(business_calculation())
```

---

## 📋 **CHANGE MANAGEMENT PROTOCOL**

### **BEFORE ANY ARCHITECTURAL CHANGE:**

1. **🔍 Survey**: Check existing systems for functionality overlap
2. **📚 Read**: Examine all related existing code 
3. **🤔 Question**: Ask "enhance existing vs create new?"
4. **📋 Plan**: Document integration approach
5. **✅ Approve**: Get confirmation before implementation
6. **🧪 Test**: Verify integration works end-to-end
7. **📖 Document**: Update this architecture document

### **CURRENT STATE VALIDATION**

As of August 24, 2025:
- **BROKEN**: Multiple competing threshold systems causing conflicts
- **SOLUTION PENDING**: Consolidation to single authoritative system
- **LESSON LEARNED**: Architecture governance prevents system conflicts

---

## 🎯 **FUTURE EXPANSION GUIDELINES**

### **WHEN TO ADD NEW SERVICES:**
- Distinct user interface (new bot, web UI, API)  
- Independent deployment requirements
- Clear domain boundaries

### **WHEN TO ADD TO SHARED:**
- Logic used by multiple services
- Complex business calculations  
- Data models shared across services

### **WHEN TO ENHANCE EXISTING:**
- Similar functionality already exists
- Adding capabilities to existing system
- **DEFAULT CHOICE - Always prefer enhancement**

---

## 🚨 **DISASTER RECOVERY**

### **ROLLBACK STRATEGY:**
- Every major change creates backup branch
- Clean git history with descriptive commits  
- Architecture document updated with each change
- Integration tests validate system state

### **CONFLICT RESOLUTION:**
- Identify competing systems immediately
- Consolidate to single authoritative implementation
- Remove duplicates completely, don't disable
- Update all integration points

---

This architecture document serves as the **SINGLE SOURCE OF TRUTH** for system design decisions and must be updated with any architectural changes.