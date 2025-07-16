# Technical Debt Analysis - January 15, 2025

## Executive Summary
The crypto-assistant system currently uses ~655MB/904MB (72%) on AWS t3.micro instance. Analysis reveals that inefficient library loading and data structures contribute more to memory usage than code duplication.

## Memory Usage Breakdown

### Current State (Docker Containers)
- **market-data**: 110.9 MB (66% of container memory)
- **telegram-bot**: 59.9 MB (23% of container memory)  
- **redis**: 6.5 MB (10% of container memory) - UNUSED

### Root Causes of High Memory Usage

#### 1. Inefficient Library Loading (20-30MB waste)
**Problem**: All libraries loaded at startup even when not needed
```python
# Current: Eager loading
import pandas as pd  # ~20MB loaded even if unused
import numpy as np   # ~15MB loaded even if unused
import ccxt         # ~10MB per exchange object
```

**Solution**: Implement lazy loading pattern
```python
# Optimized: Lazy loading
def get_pandas():
    global _pandas
    if _pandas is None:
        import pandas as pd
        _pandas = pd
    return _pandas
```

#### 2. Poor Data Structure Choices (10-15MB waste)
**Problem**: Using dictionaries for large datasets instead of optimized structures
```python
# Current: Memory-heavy dictionaries
market_data = {
    'symbol': 'BTC/USDT',
    'price': 45000.0,
    'volume': 1234567890.0,
    # ... many more fields
}
```

**Solution**: Use dataclasses or named tuples
```python
# Optimized: Memory-efficient dataclass
@dataclass(slots=True)
class MarketData:
    symbol: str
    price: float
    volume: float
```

#### 3. Multiple Exchange Objects (5-10MB per exchange)
**Problem**: Loading all exchange objects at startup
```python
# Current: All exchanges loaded
self.exchanges = {
    'binance': ccxt.binance(),
    'bybit': ccxt.bybit(),
    'okx': ccxt.okx(),
    # ... 6 exchanges = 30-60MB
}
```

**Solution**: Load exchanges on-demand
```python
# Optimized: On-demand loading
def get_exchange(name):
    if name not in self._exchange_cache:
        self._exchange_cache[name] = getattr(ccxt, name)()
    return self._exchange_cache[name]
```

#### 4. Code Duplication (<1MB but high maintenance cost)
**Problem**: main.py (1,300 lines) and main_webhook.py (1,467 lines) share 92% code
- Minimal memory impact but creates maintenance burden
- Bug fixes must be applied twice
- Feature additions require double implementation

**Solution**: Extract shared code to common module
```python
# telegram_bot_common.py - shared functionality
# main.py - polling-specific code (imports common)
# main_webhook.py - webhook-specific code (imports common)
```

## Optimization Roadmap

### Phase 1: Quick Wins (1-2 days, save 35-50MB)
1. **Remove unused Redis container** (save 6.5MB + overhead)
   ```bash
   # Remove redis service from docker-compose.aws.yml
   ```

2. **Implement lazy loading for pandas/numpy** (save 20-30MB)
   - Create lazy loading utilities
   - Update market-data service to use lazy imports
   - Test memory usage reduction

3. **Optimize exchange loading** (save 20-40MB)
   - Load only requested exchange, not all 6
   - Cache loaded exchanges for reuse
   - Clear unused exchanges after timeout

### Phase 2: Structural Improvements (3-5 days, save 10-15MB)
1. **Optimize data structures**
   - Convert dictionaries to dataclasses with __slots__
   - Use array.array for numeric data instead of lists
   - Implement object pooling for frequently created objects

2. **Memory profiling and monitoring**
   ```python
   # Add memory profiling
   import tracemalloc
   tracemalloc.start()
   # ... code execution ...
   snapshot = tracemalloc.take_snapshot()
   ```

3. **Implement memory limits**
   ```python
   # Set soft limits to prevent runaway memory
   import resource
   resource.setrlimit(resource.RLIMIT_AS, (400 * 1024 * 1024, -1))
   ```

### Phase 3: Architecture Refactoring (1-2 weeks)
1. **Consolidate main.py and main_webhook.py**
   - Extract 92% shared code to common module
   - Reduce maintenance burden
   - Enable easier testing

2. **Consider Rust migration for market-data service**
   - Pros: 70-80% memory reduction, better performance
   - Cons: Learning curve, rewrite effort
   - Alternative: Use PyPy for 30-40% memory reduction

3. **Implement proper caching strategy**
   - Use Redis for actual caching (currently unused)
   - Cache market data with TTL
   - Reduce API calls and processing

## Expected Results

### Memory Savings
- **Phase 1**: 35-50MB (60-80% reduction in market-data)
- **Phase 2**: Additional 10-15MB 
- **Total**: 45-65MB reduction (bringing total usage to ~590MB from 655MB)

### Performance Improvements
- Faster startup time (lazy loading)
- Reduced GC pressure (better data structures)
- Lower latency (less memory allocation)

### Maintenance Benefits
- Single codebase for bot logic
- Easier testing and debugging
- Reduced bug surface area

## Implementation Priority

1. **CRITICAL**: Remove Redis container (immediate 6.5MB saving)
2. **HIGH**: Lazy load pandas/numpy in market-data service
3. **HIGH**: On-demand exchange loading
4. **MEDIUM**: Data structure optimization
5. **LOW**: Code consolidation (main.py/main_webhook.py)
6. **FUTURE**: Consider Rust migration if memory remains an issue

## Monitoring and Validation

### Memory Monitoring Commands
```bash
# Container memory usage
docker stats --no-stream

# Detailed memory breakdown
docker exec crypto-market-data cat /proc/self/status | grep -E "VmRSS|VmSize"

# Python memory profiling
python -m memory_profiler your_script.py
```

### Success Metrics
- [ ] Market-data service < 70MB (from 110.9MB)
- [ ] Total system memory < 600MB (from 655MB)
- [ ] No performance degradation
- [ ] All tests passing

## Notes

1. **File duplication impact**: While main.py and main_webhook.py duplication adds <1MB to memory, the maintenance cost is significant. Prioritize based on team pain points.

2. **Docker overhead**: Each container has ~10-15MB overhead. Consider combining services if memory remains critical.

3. **AWS t3.micro limits**: With 1GB RAM and ~300MB for OS, we have ~700MB for applications. Current 655MB usage is dangerously close to limits.

4. **Webhook vs Polling**: Webhook mode is more memory efficient but requires HTTPS. Current polling mode works but uses more CPU/memory for constant checking.

## References
- AWS t3.micro specifications: 1 vCPU, 1 GB RAM
- Python memory profiling: https://docs.python.org/3/library/tracemalloc.html
- Docker resource limits: https://docs.docker.com/config/containers/resource_constraints/

---
*Generated from production analysis on January 15, 2025*