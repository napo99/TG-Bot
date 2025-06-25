# Agent 1: Binance + Bybit OI Specialist - Instructions

## 🎯 AGENT IDENTITY
- **Name**: Agent 1 - Binance + Bybit OI Specialist
- **Workspace**: `/Users/screener-m3/projects/crypto-assistant-oi/`
- **Branch**: `feature/oi-analysis`
- **Specialization**: Exchange API implementation for Binance and Bybit
- **Phase**: 1 (Foundation - starts immediately)

## 🎯 MISSION STATEMENT
Implement complete Open Interest data collection from Binance and Bybit exchanges for any cryptocurrency symbol, with special focus on fixing the critical Bybit inverse contract issue.

## 📋 DELIVERABLES
1. **6 Working Markets**: Binance (USDT, USDC, USD) + Bybit (USDT, USDC, USD)
2. **Standardized Data Structure**: Format that other agents can consume
3. **Bybit Inverse Fix**: USD market shows >10,000 BTC (not $0)
4. **Real-time Data**: Live API integration with error handling
5. **Mathematical Validation**: oi_tokens * price ≈ oi_usd for all markets

## 🚨 CRITICAL ISSUE TO SOLVE
**Bybit USD Inverse Contract Bug**: Currently shows `0 BTC ($0.0B)` instead of expected ~15,000 BTC (~$1.5B)

**Root Cause**: Data fetched but not properly stored in markets_data structure
**Solution**: Use Bybit's `openInterestValue` field directly for USD calculations

## 🔧 TECHNICAL REQUIREMENTS

### **Binance Implementation**
```python
# FAPI (Linear Contracts)
BINANCE_FAPI_OI = "https://fapi.binance.com/fapi/v1/openInterest"
# Symbols: BTCUSDT, BTCUSDC

# DAPI (Inverse Contracts) 
BINANCE_DAPI_OI = "https://dapi.binance.com/dapi/v1/openInterest"
# Symbols: BTCUSD_PERP, ETHUSD_PERP
```

### **Bybit Implementation** 
```python
# CRITICAL: Use tickers endpoint with category parameter
BYBIT_TICKERS = "https://api.bybit.com/v5/market/tickers"

# Linear contracts
params_linear = {'category': 'linear', 'symbol': 'BTCUSDT'}

# Inverse contracts (CRITICAL FIX AREA)
params_inverse = {'category': 'inverse', 'symbol': 'BTCUSD'}
# MUST use: openInterestValue (pre-calculated USD value)
```

### **Target Data Structure**
```python
{
    "exchange": "binance",  # or "bybit"
    "symbol": "BTC",
    "markets": {
        "USDT": {
            "type": "linear",
            "category": "STABLE", 
            "oi_tokens": 78278.0,
            "oi_usd": 7900000000.0,
            "funding_rate": 0.0050,
            "volume_tokens": 223000.0,
            "symbol_exchange": "BTCUSDT"
        },
        "USDC": {
            "type": "linear",
            "category": "STABLE",
            "oi_tokens": 6377.0,
            "oi_usd": 600000000.0,
            "funding_rate": 0.0013,
            "volume_tokens": 34000.0,
            "symbol_exchange": "BTCUSDC"
        },
        "USD": {
            "type": "inverse",
            "category": "INVERSE",
            "oi_tokens": 21949.0,  # CRITICAL: NOT 0!
            "oi_usd": 2200000000.0,
            "funding_rate": 0.0026,
            "volume_tokens": 23219000.0,
            "symbol_exchange": "BTCUSD_PERP"  # or "BTCUSD" for Bybit
        }
    }
}
```

## ✅ SUCCESS CRITERIA
- [ ] **Bybit USD Fix**: Shows 15,000+ BTC (not 0)
- [ ] **All 6 Markets Working**: Real-time data from both exchanges
- [ ] **Data Validation**: Math checks pass (tokens * price ≈ USD)
- [ ] **Error Handling**: Graceful failures for missing markets
- [ ] **Performance**: Individual exchange calls complete in <5 seconds
- [ ] **Symbol Flexibility**: Works with BTC, ETH, SOL, etc.

## 🔍 VALIDATION COMMANDS
```bash
# Quick validation after changes
python3 tools/validation/quick_test.py

# Test specific exchange
curl -X POST http://localhost:8001/test_exchange_oi \
  -H "Content-Type: application/json" \
  -d '{"exchange": "bybit", "symbol": "BTC"}'

# Check Bybit inverse specifically
# Should show substantial BTC amount, not 0
```

## 📚 REFERENCE DOCUMENTATION
- `MULTI_EXCHANGE_OI_SPECIFICATIONS.md` - Technical specifications
- `DETAILED_AGENT_SPECIFICATIONS.md` - Detailed agent requirements  
- `BYBIT_INVERSE_SOLUTION.md` - Specific fix documentation
- `IMPLEMENTATION_CHECKLIST.md` - Step-by-step implementation

## 🤝 COORDINATION WITH OTHER AGENTS
- **Agent 2**: Coordinate data structure standards, work in parallel
- **Agent 3**: Provide data structure template once established
- **Agent 4**: Ensure data format is integration-ready

## 📊 PROGRESS TRACKING
- [ ] **Phase 1a**: Binance FAPI implementation (USDT, USDC)
- [ ] **Phase 1b**: Binance DAPI implementation (USD inverse)
- [ ] **Phase 1c**: Bybit linear implementation (USDT, USDC)  
- [ ] **Phase 1d**: Bybit inverse fix (USD - CRITICAL)
- [ ] **Phase 1e**: Integration testing and validation
- [ ] **Phase 1f**: Signal completion to Agent 3

## 🚨 BLOCKER ESCALATION
If stuck on Bybit inverse issue:
1. Check `BYBIT_INVERSE_SOLUTION.md` for previous debugging
2. Test direct API calls outside container
3. Verify `openInterestValue` field usage
4. Escalate if container deployment issues persist

## 📝 COMPLETION SIGNAL
When complete, update status:
```bash
echo "🟢 AGENT 1 COMPLETE: Bybit inverse fixed, 6 markets working"
echo "✅ Agent 3 can start Gate.io + Bitget implementation"
```

---
**Start Date**: [Fill when agent begins]
**Completion Date**: [Fill when agent completes]
**Status**: READY TO START