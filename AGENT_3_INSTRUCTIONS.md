# Agent 3: Gate.io + Bitget OI Specialist - Instructions

## 🎯 AGENT IDENTITY
- **Name**: Agent 3 - Gate.io + Bitget OI Specialist
- **Workspace**: `/Users/screener-m3/projects/crypto-assistant-symbols/`
- **Branch**: `feature/symbol-mapping`
- **Specialization**: Gate.io and Bitget exchange implementation + symbol harmonization
- **Phase**: 2 (Expansion - starts after Agent 1 completes data structures)

## 🎯 MISSION STATEMENT
Implement Gate.io and Bitget Open Interest collection and solve symbol format harmonization across all 5 exchanges.

## 📋 DELIVERABLES
1. **Gate.io 3 Markets**: USDT, USDC, USD (inverse) with real-time data
2. **Bitget 3 Markets**: USDT, USDC, USD (inverse) with real-time data  
3. **Symbol Harmonization**: Unified symbol mapping across all exchanges
4. **Exchange Integration**: Seamless addition to Agent 2's performance framework
5. **Total Coverage**: 15 markets across 5 exchanges

## 🚨 DEPENDENCIES
- **WAIT FOR**: Agent 1 to complete Bybit fix and establish data structures (~30-45 minutes)
- **COORDINATE WITH**: Agent 2's performance framework
- **SIGNAL REQUIRED**: "🟢 AGENT 1 COMPLETE: Data structures ready"

## 🔧 TECHNICAL REQUIREMENTS

### **Gate.io Implementation**
```python
# Gate.io Direct API - Different endpoints per settlement
GATEIO_BASE = "https://api.gateio.ws/api/v4/futures"

# Settlement-specific endpoints
GATEIO_ENDPOINTS = {
    'USDT': f'{GATEIO_BASE}/usdt/tickers',     # Linear USDT
    'USDC': f'{GATEIO_BASE}/usdc/tickers',     # Linear USDC
    'USD': f'{GATEIO_BASE}/btc/tickers'        # Inverse BTC-settled
}

# Symbol Formats
GATEIO_SYMBOLS = {
    'USDT': 'BTC_USDT',    # Linear USDT
    'USDC': 'BTC_USDC',    # Linear USDC  
    'USD': 'BTC_USD'       # Inverse (BTC settlement)
}
```

### **Bitget Implementation**
```python
# Bitget Direct API
BITGET_OI_URL = "https://api.bitget.com/api/mix/v1/market/open-interest"

# Product-specific symbol formats
BITGET_SYMBOLS = {
    'USDT': 'BTCUSDT_UMCBL',    # Linear USDT (U-margined)
    'USDC': 'BTCUSDC_UMCBL',    # Linear USDC (U-margined)
    'USD': 'BTCUSD_DMCBL'       # Inverse USD (Coin-margined)
}

# Key Fields
# openInterest: Contract amount
# openInterestUsd: USD value (use for inverse)
```

### **Symbol Harmonization Matrix**
```python
EXCHANGE_SYMBOL_MAPPING = {
    'binance': {
        'linear_usdt': lambda base: f"{base}USDT",
        'linear_usdc': lambda base: f"{base}USDC", 
        'inverse': lambda base: f"{base}USD_PERP"
    },
    'bybit': {
        'linear_usdt': lambda base: f"{base}USDT",
        'linear_usdc': lambda base: f"{base}USDC",
        'inverse': lambda base: f"{base}USD"
    },
    'okx': {
        'linear_usdt': lambda base: f"{base}-USDT-SWAP",
        'linear_usdc': lambda base: f"{base}-USDC-SWAP",
        'inverse': lambda base: f"{base}-USD-SWAP"
    },
    'gateio': {
        'linear_usdt': lambda base: f"{base}_USDT",
        'linear_usdc': lambda base: f"{base}_USDC",
        'inverse': lambda base: f"{base}_USD"
    },
    'bitget': {
        'linear_usdt': lambda base: f"{base}USDT_UMCBL",
        'linear_usdc': lambda base: f"{base}USDC_UMCBL",
        'inverse': lambda base: f"{base}USD_DMCBL"
    }
}
```

## ✅ SUCCESS CRITERIA
- [ ] **Gate.io Markets**: 3 working markets with accurate data
- [ ] **Bitget Markets**: 3 working markets with accurate data
- [ ] **Symbol Mapping**: All 5 exchanges handle BTC, ETH, SOL consistently
- [ ] **Integration**: Seamless addition to performance framework
- [ ] **No Regression**: Existing exchanges continue working
- [ ] **Total Coverage**: 15 markets across 5 exchanges

## 🔧 EXCHANGE-SPECIFIC CHALLENGES

### **Gate.io Challenges**
1. **Different Endpoints**: Separate URLs per settlement currency
2. **Settlement Logic**: BTC-settled for inverse, USDT/USDC for linear
3. **Position Data**: May need positions endpoint for OI calculation
4. **Rate Limiting**: Different limits per endpoint

### **Bitget Challenges**
1. **Product Types**: UMCBL (U-margined) vs DMCBL (Coin-margined)
2. **Multiple Endpoints**: OI, ticker, and funding rate endpoints
3. **USD Calculation**: Use `openInterestUsd` for inverse contracts
4. **API Response Format**: Different from other exchanges

## 🔍 VALIDATION COMMANDS
```bash
# Test Gate.io implementation
curl -X POST http://localhost:8001/test_exchange_oi \
  -H "Content-Type: application/json" \
  -d '{"exchange": "gateio", "symbol": "BTC"}'

# Test Bitget implementation  
curl -X POST http://localhost:8001/test_exchange_oi \
  -H "Content-Type: application/json" \
  -d '{"exchange": "bitget", "symbol": "BTC"}'

# Test full multi-exchange (should show 5 exchanges)
curl -X POST http://localhost:8001/multi_oi \
  -H "Content-Type: application/json" \
  -d '{"base_symbol": "BTC"}'
```

## 📈 EXPECTED DATA OUTPUT

### **Gate.io Target Data**
```python
{
    "exchange": "gateio",
    "symbol": "BTC", 
    "markets": {
        "USDT": {
            "oi_tokens": 60353.0,    # ~$6.1B
            "oi_usd": 6100000000.0,
            "funding_rate": 0.0000,
            "volume_tokens": 869675.0
        },
        "USDC": {
            "oi_tokens": 2800.0,     # ~$280M
            "oi_usd": 280000000.0,
            "funding_rate": 0.0005,
            "volume_tokens": 12500.0
        },
        "USD": {
            "oi_tokens": 9200.0,     # ~$920M (inverse)
            "oi_usd": 920000000.0,
            "funding_rate": -0.0012,
            "volume_tokens": 185000.0
        }
    }
}
```

### **Bitget Target Data**
```python
{
    "exchange": "bitget",
    "symbol": "BTC",
    "markets": {
        "USDT": {
            "oi_tokens": 41500.0,    # ~$4.2B
            "oi_usd": 4200000000.0,
            "funding_rate": 0.0018,
            "volume_tokens": 95000.0
        },
        "USDC": {
            "oi_tokens": 1850.0,     # ~$185M
            "oi_usd": 185000000.0,
            "funding_rate": 0.0011,
            "volume_tokens": 8500.0
        },
        "USD": {
            "oi_tokens": 7200.0,     # ~$720M (inverse)
            "oi_usd": 720000000.0,
            "funding_rate": 0.0000,
            "volume_tokens": 98000.0
        }
    }
}
```

## 🤝 COORDINATION WITH OTHER AGENTS
- **Agent 1**: Use established data structure format
- **Agent 2**: Integrate with performance framework
- **Agent 4**: Provide complete 15-market dataset

## 📚 REFERENCE DOCUMENTATION
- `MULTI_EXCHANGE_OI_SPECIFICATIONS.md` - Gate.io and Bitget specs
- `IMPLEMENTATION_CHECKLIST.md` - Step-by-step guide
- Agent 1's completed implementation for reference

## 📊 PROGRESS TRACKING
- [ ] **Phase 3a**: WAIT for Agent 1 completion signal
- [ ] **Phase 3b**: Gate.io linear implementation (USDT, USDC)
- [ ] **Phase 3c**: Gate.io inverse implementation (USD)
- [ ] **Phase 3d**: Bitget linear implementation (USDT, USDC)
- [ ] **Phase 3e**: Bitget inverse implementation (USD)
- [ ] **Phase 3f**: Symbol harmonization across all exchanges
- [ ] **Phase 3g**: Integration testing with all 5 exchanges

## 🚨 START CONDITION
**DO NOT START until Agent 1 signals completion:**
```bash
# Wait for this signal:
echo "🟢 AGENT 1 COMPLETE: Bybit inverse fixed, data structures ready"
echo "✅ Agent 3 can start Gate.io + Bitget implementation"
```

## 📝 COMPLETION SIGNAL
When complete, update status:
```bash
echo "🟢 AGENT 3 COMPLETE: Gate.io + Bitget working, 15 markets total"
echo "✅ Agent 4 can start integration and bot implementation"
```

---
**Start Date**: [Fill when agent begins - AFTER Agent 1 completes]
**Completion Date**: [Fill when agent completes]
**Status**: WAITING FOR AGENT 1 COMPLETION