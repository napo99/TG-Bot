# Agent 2: Performance + OKX OI Specialist - Instructions

## 🎯 AGENT IDENTITY
- **Name**: Agent 2 - Performance + OKX OI Specialist
- **Workspace**: `/Users/screener-m3/projects/crypto-assistant-perf/`
- **Branch**: `feature/performance-opt`
- **Specialization**: OKX exchange implementation + system performance optimization
- **Phase**: 1 (Foundation - starts immediately, parallel with Agent 1)

## 🎯 MISSION STATEMENT
Implement OKX Open Interest collection and optimize the entire multi-exchange system for <3 second response times across all exchanges.

## 📋 DELIVERABLES
1. **OKX 3 Markets**: USDT, USDC, USD (inverse) with real-time data
2. **Performance Engine**: Parallel async processing for 5+ exchanges
3. **Sub-3 Second Response**: Full multi-exchange OI analysis optimization
4. **Connection Management**: Pooling, timeouts, error recovery
5. **Scalable Architecture**: Ready for additional exchanges

## 🚨 CRITICAL PERFORMANCE TARGET
**Response Time**: Complete multi-exchange OI analysis in <3 seconds (currently 10+ seconds)

## 🔧 TECHNICAL REQUIREMENTS

### **OKX Implementation**
```python
# OKX Direct API
OKX_OI_URL = "https://www.okx.com/api/v5/public/open-interest"

# Symbol Formats
OKX_SYMBOLS = {
    'USDT': 'BTC-USDT-SWAP',    # Linear USDT
    'USDC': 'BTC-USDC-SWAP',    # Linear USDC
    'USD': 'BTC-USD-SWAP'       # Inverse USD
}

# Key Fields
# oi: Open Interest in contracts
# oiCcy: Open Interest in base currency  
# Contract sizes vary by instrument
```

### **Performance Optimization Architecture**
```python
async def fetch_all_exchanges_oi(base_symbol: str):
    """Parallel fetch from all exchanges with timeout control"""
    tasks = [
        fetch_binance_multi_oi(base_symbol),    # Agent 1
        fetch_bybit_multi_oi(base_symbol),      # Agent 1  
        fetch_okx_multi_oi(base_symbol),        # Agent 2 ← YOU
        fetch_gateio_multi_oi(base_symbol),     # Agent 3
        fetch_bitget_multi_oi(base_symbol)      # Agent 3
    ]
    
    # Execute with timeout control
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return filter_successful_results(results)
```

### **Connection Optimization**
```python
# Connection pooling
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=5),
    connector=aiohttp.TCPConnector(limit=100)
) as session:
    # Reuse connections across multiple API calls
```

## ✅ SUCCESS CRITERIA
- [ ] **OKX Markets**: 3 working markets with accurate data
- [ ] **Performance Target**: <3 second response for full analysis
- [ ] **Parallel Processing**: All exchanges fetch concurrently
- [ ] **Error Recovery**: Graceful handling of exchange timeouts
- [ ] **Connection Efficiency**: Pooled connections, no connection leaks
- [ ] **Scalability**: Ready for Agent 3's additional exchanges

## 🔧 OKX-SPECIFIC CHALLENGES
1. **Contract Size Variations**: Different contract sizes per symbol
2. **Symbol Format**: Dash-separated format (BTC-USDT-SWAP)
3. **Field Mapping**: `oi` vs `oiCcy` field usage
4. **USD Calculations**: Proper inverse contract math

### **Expected OKX Data**
```python
{
    "exchange": "okx",
    "symbol": "BTC",
    "markets": {
        "USDT": {
            "oi_tokens": 45000.0,    # ~$4.5B
            "oi_usd": 4500000000.0,
            "funding_rate": 0.0012,
            "volume_tokens": 89000.0
        },
        "USDC": {
            "oi_tokens": 2500.0,     # ~$250M
            "oi_usd": 250000000.0,
            "funding_rate": 0.0008,
            "volume_tokens": 5200.0
        },
        "USD": {
            "oi_tokens": 8500.0,     # ~$850M (inverse)
            "oi_usd": 850000000.0,
            "funding_rate": -0.0005,
            "volume_tokens": 125000.0
        }
    }
}
```

## 🔍 VALIDATION COMMANDS
```bash
# Performance testing
time curl -X POST http://localhost:8001/multi_oi \
  -H "Content-Type: application/json" \
  -d '{"base_symbol": "BTC"}'
# Target: <3 seconds total

# OKX specific testing  
curl -X POST http://localhost:8001/test_exchange_oi \
  -H "Content-Type: application/json" \
  -d '{"exchange": "okx", "symbol": "BTC"}'
```

## 📈 PERFORMANCE OPTIMIZATION CHECKLIST
- [ ] **Async Implementation**: All API calls use async/await
- [ ] **Parallel Execution**: asyncio.gather() for concurrent requests
- [ ] **Connection Pooling**: Reuse HTTP connections
- [ ] **Timeout Control**: 5-second max per exchange
- [ ] **Error Isolation**: One exchange failure doesn't break others
- [ ] **Resource Management**: Proper session cleanup

## 🤝 COORDINATION WITH OTHER AGENTS
- **Agent 1**: Share data structure standards, work in parallel
- **Agent 3**: Provide performance framework for additional exchanges
- **Agent 4**: Ensure optimized system ready for integration testing

## 📚 REFERENCE DOCUMENTATION
- `MULTI_EXCHANGE_OI_SPECIFICATIONS.md` - OKX technical specs
- `ENHANCED_OI_ANALYSIS_STRATEGY.md` - Performance requirements
- Previous OKX research files in workspace

## 📊 PROGRESS TRACKING
- [ ] **Phase 2a**: OKX linear implementation (USDT, USDC)
- [ ] **Phase 2b**: OKX inverse implementation (USD)
- [ ] **Phase 2c**: Performance optimization framework
- [ ] **Phase 2d**: Parallel processing implementation
- [ ] **Phase 2e**: Connection pooling and timeout handling
- [ ] **Phase 2f**: Integration testing with Agent 1's exchanges

## 🚨 DEPENDENCIES & COORDINATION
- **Start**: Immediately (parallel with Agent 1)
- **Data Structure**: Coordinate with Agent 1 for consistency
- **Performance Target**: Must handle Agent 3's additional exchanges

## 📝 COMPLETION SIGNAL
When complete, update status:
```bash
echo "🟢 AGENT 2 COMPLETE: OKX working, <3s performance achieved"
echo "✅ Performance framework ready for Agent 3's exchanges"
```

---
**Start Date**: [Fill when agent begins]
**Completion Date**: [Fill when agent completes]  
**Status**: READY TO START