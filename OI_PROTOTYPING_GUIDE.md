# OI System Prototyping Guide

## 📋 Summary of Current System

### Core Files
- **Command**: `services/telegram-bot/main.py:947` - `/oi` command handler
- **Aggregator**: `services/market-data/unified_oi_aggregator.py` - Orchestrates all providers
- **Models**: `services/market-data/oi_engine_v2.py` - Data structures
- **Providers**: 6 exchange-specific files implementing `BaseExchangeOIProvider`

### Current Exchanges
1. **Binance** - 3 markets (USDT, USDC, USD inverse)
2. **Bybit** - 3 markets (USDT, USDC, USD inverse)
3. **OKX** - 3 markets (USDT, USDC, USD inverse)
4. **Gate.io** - 1 market (USDT)
5. **Bitget** - 2 markets (USDT, USD inverse)
6. **Hyperliquid** - 1 market (native)

**Total**: Up to 13 markets aggregated

### What Each Provider Does
1. Formats symbol for exchange API (e.g., `BTC` → `BTCUSDT`)
2. Fetches OI, price, funding rate, volume from exchange REST API
3. Calculates USD values (linear vs inverse contracts)
4. Returns `ExchangeOIResult` with validation

---

## 🎯 Recommended Prototyping Approaches

### **Option 1: Jupyter Notebook** (BEST for exploration)

**Pros:**
- ✅ Interactive REPL experience
- ✅ Easy to visualize data (pandas, matplotlib)
- ✅ Can run cells independently
- ✅ Save intermediate results
- ✅ Mix code, output, and markdown notes
- ✅ Can easily add/remove exchanges and rerun

**Cons:**
- ⚠️ Requires Jupyter installation
- ⚠️ Less portable than standalone script

**Best For:**
- Exploring exchange APIs
- Testing new providers
- Data analysis and visualization
- Rapid prototyping

---

### **Option 2: IPython REPL** (FAST for quick tests)

**Pros:**
- ✅ No setup needed (just `pip install ipython`)
- ✅ True REPL experience
- ✅ Auto-completion and magic commands
- ✅ Quick to test small changes
- ✅ Can paste/modify code on the fly

**Cons:**
- ⚠️ Less structured than notebook
- ⚠️ Harder to save/reproduce experiments

**Best For:**
- Quick API tests
- Debugging specific providers
- One-off queries

---

### **Option 3: Standalone Python Script** (BEST for automation)

**Pros:**
- ✅ No dependencies beyond Python
- ✅ Easy to version control
- ✅ Can be automated/scheduled
- ✅ Easy to share and run

**Cons:**
- ⚠️ Less interactive than notebook/REPL
- ⚠️ Need to rerun entire script for changes

**Best For:**
- Production-ready prototypes
- CI/CD integration
- Sharing with team

---

## 🚀 Recommended: **Jupyter Notebook**

Based on your requirements ("quickly prototype, add and remove exchanges, get their connection and explore the OI data"), **Jupyter Notebook** is the best choice.

### Why?
1. **Interactive**: Test each exchange independently
2. **REPL-like**: Run cells in any order
3. **Visual**: See results immediately with formatted output
4. **Flexible**: Easy to add/remove exchanges and rerun
5. **Documentation**: Mix code with notes about each exchange

---

## 📝 Example Implementations

I've created three prototyping templates for you:

### 1. `oi_prototype_notebook.ipynb` - Jupyter Notebook
Full interactive exploration with cells for:
- Testing individual providers
- Comparing exchanges
- Adding new exchanges
- Data visualization

### 2. `oi_prototype_repl.py` - IPython REPL Script
Paste-friendly code blocks for quick REPL testing

### 3. `oi_prototype_standalone.py` - Standalone Script
Complete runnable script for automation

---

## 🎨 Interactive Features Available

### In Jupyter Notebook:
```python
# Test a single exchange
provider = BinanceOIProvider()
result = await provider.get_oi_data("BTC")
display_oi_result(result)  # Pretty formatted output

# Add new exchange on the fly
class MyNewExchangeProvider(BaseExchangeOIProvider):
    # implement methods
    pass

# Test immediately
new_provider = MyNewExchangeProvider()
new_result = await new_provider.get_oi_data("BTC")

# Compare exchanges
compare_exchanges([binance_result, bybit_result, okx_result])

# Visualize
plot_oi_breakdown(result)
```

### REPL Features:
- Auto-complete provider methods
- `%timeit` for performance testing
- `?provider.get_oi_data` for documentation
- History search with arrow keys
- Easy error recovery

---

## 🔧 Quick Start

### For Jupyter Notebook:
```bash
cd services/market-data
pip install jupyter ipython pandas matplotlib
jupyter notebook oi_prototype_notebook.ipynb
```

### For IPython REPL:
```bash
cd services/market-data
pip install ipython
ipython
# Then paste code from oi_prototype_repl.py
```

### For Standalone Script:
```bash
cd services/market-data
python oi_prototype_standalone.py BTC
```

---

## 💡 Pro Tips

### 1. **Use Async Context Managers**
```python
async with BinanceOIProvider() as provider:
    result = await provider.get_oi_data("BTC")
    # Auto-closes session
```

### 2. **Test Multiple Symbols Easily**
```python
symbols = ["BTC", "ETH", "SOL"]
for symbol in symbols:
    result = await provider.get_oi_data(symbol)
    print(f"{symbol}: ${result.total_oi_usd/1e9:.1f}B")
```

### 3. **Debug Individual Markets**
```python
# Test just one market type
result = await provider._fetch_fapi_market("BTC", MarketType.USDT)
print(result)  # See raw data
```

### 4. **Compare Exchange APIs**
```python
# Side-by-side comparison
binance_result = await binance_provider.get_oi_data("BTC")
bybit_result = await bybit_provider.get_oi_data("BTC")

print(f"Binance USDT: ${binance_result.usdt_markets[0].oi_usd/1e9:.1f}B")
print(f"Bybit USDT:   ${bybit_result.usdt_markets[0].oi_usd/1e9:.1f}B")
```

---

## 🎯 Next Steps

1. **Start with Jupyter Notebook** - Most interactive
2. **Test existing providers** - Understand the patterns
3. **Add a new exchange** - Follow the provider template
4. **Compare results** - Validate new provider against existing ones
5. **Integrate** - Once validated, add to `unified_oi_aggregator.py`

---

## 📚 Reference Files

- **Architecture**: `OI_SYSTEM_ANALYSIS.md`
- **Jupyter Template**: `oi_prototype_notebook.ipynb`
- **REPL Template**: `oi_prototype_repl.py`
- **Standalone Template**: `oi_prototype_standalone.py`
- **Integration Guide**: `services/market-data/unified_oi_aggregator.py` (see `test_unified_system()`)
