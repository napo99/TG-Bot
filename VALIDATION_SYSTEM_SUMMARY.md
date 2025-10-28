# HyperLiquid Liquidation Detection - Validation System

**Created:** October 28, 2025
**Branch:** `feature/liquidation-monitor`
**Commit:** `08f4d93` (29 minutes ago)

---

## 🎯 Executive Summary

A comprehensive validation system has been created to test and verify the HyperLiquid liquidation detection system against live data and external reference sources (CoinGlass).

### What Was Built

1. **Quick Validation Script** (2 minutes)
   - Fast system health check
   - Vault discovery verification
   - Recent liquidations test

2. **Extended Validation Script** (5-30 minutes)
   - Comprehensive real-time monitoring
   - Statistical analysis
   - CoinGlass comparison (optional)
   - JSON export capabilities

3. **Complete Documentation**
   - Validation guide with troubleshooting
   - Usage instructions
   - Expected benchmarks and accuracy metrics

---

## 🚀 Quick Start

### Option 1: Quick Validation (Recommended First Step)

```bash
cd /home/user/TG-Bot/services/liquidation-aggregator

# Install dependencies
pip install -r requirements.txt

# Run quick validation
python -m scripts.quick_validation
```

**Expected Output:**
```
======================================================================
HYPERLIQUID LIQUIDATION DETECTION - QUICK VALIDATION
======================================================================

[1/4] Testing API connectivity...
  ✅ HyperLiquid API is reachable

[2/4] Initializing liquidation registry...
  ✅ Registry initialized

[3/4] Discovering active liquidation vaults...
  ✅ Discovered 2 vault(s)
    • 0x2e3d94...dd14: 45 fills (last: 127s ago)
    • 0x5f8a...3c9a: 32 fills (last: 89s ago)

[4/4] Checking recent liquidations...
  ✅ Found 77 recent liquidation(s)

  Latest liquidations:
    1. BTC LONG liquidation: 0.0850 @ $95,234.50 ($8,094.93) - 89s ago
    2. ETH SHORT liquidation: 2.3400 @ $3,456.78 ($8,088.86) - 127s ago
    ...

🎯 VERDICT: PASS
```

---

### Option 2: Extended Validation

```bash
# 10-minute validation with statistical analysis
python -m scripts.validate_liquidation_accuracy --duration 10

# Export detailed report
python -m scripts.validate_liquidation_accuracy --duration 10 --export validation_report.json
```

---

### Option 3: CoinGlass Comparison

**Prerequisites:**
1. Get CoinGlass API key: https://www.coinglass.com/pricing
2. Choose plan with liquidation data access

**Run:**
```bash
python -m scripts.validate_liquidation_accuracy \
  --duration 10 \
  --coinglass-api-key YOUR_API_KEY_HERE \
  --export coinglass_comparison.json
```

**Expected Output:**
```
📊 COINGLASS COMPARISON
  Our Count: 156
  CoinGlass Count: 158
  Difference: 2 (1.3%)
  Match Rate: 98.7%

🎯 VERDICT: PASS
```

---

## 📁 Files Created

### Scripts

1. **`services/liquidation-aggregator/scripts/quick_validation.py`**
   - Fast 2-minute system check
   - Tests: API connectivity, vault discovery, liquidation detection
   - Usage: `python -m scripts.quick_validation`

2. **`services/liquidation-aggregator/scripts/validate_liquidation_accuracy.py`**
   - Comprehensive 5-30 minute validation
   - Features: Real-time monitoring, CoinGlass comparison, JSON export
   - Usage: `python -m scripts.validate_liquidation_accuracy --duration 10`

### Documentation

3. **`services/liquidation-aggregator/docs/VALIDATION_GUIDE.md`**
   - Complete validation guide
   - CoinGlass setup instructions
   - Troubleshooting guide
   - Expected accuracy benchmarks
   - Manual verification methods

4. **`services/liquidation-aggregator/scripts/README.md`** (updated)
   - Added validation scripts documentation
   - Quick start guide
   - Usage examples

---

## 🔍 What Gets Validated

### 1. Vault Discovery
- ✅ Can the system discover active HyperLiquid liquidation vaults?
- ✅ Are multiple vaults detected (post-rotation)?
- ✅ Do vaults have recent fills?

### 2. Liquidation Detection
- ✅ Are liquidations being captured in real-time?
- ✅ Do liquidations include correct metadata (coin, side, size, price)?
- ✅ Is the volume calculation accurate?

### 3. System Health
- ✅ Are there any vault errors?
- ✅ How fresh is the latest data?
- ✅ Are any vaults stale (>5 minutes)?

### 4. External Validation (Optional)
- ✅ How does our data compare to CoinGlass?
- ✅ What's the match rate?
- ✅ Are discrepancies within acceptable ranges?

---

## 📊 Expected Results

### Accuracy Benchmarks

| Metric | Expected | Notes |
|--------|----------|-------|
| Vault Discovery | 95-100% | Should always find active vaults |
| Liquidation Detection | 98-100% | May miss <1% due to timing |
| CoinGlass Match Rate | 90-100% | Minor timing differences OK |
| False Positives | 0% | Never detect non-liquidations |
| Latency | <5 seconds | From exchange to our system |

### CoinGlass Comparison Guidelines

| Match Rate | Assessment | Action |
|------------|------------|--------|
| 95-100% | ✅ Excellent | Production ready |
| 90-95% | ✅ Good | Minor discrepancies expected |
| 80-90% | ⚠️ Fair | Review timing windows |
| <80% | ❌ Poor | Investigate implementation |

---

## 🔧 How to Compare with CoinGlass Manually

### Method 1: CoinGlass Website
1. Visit: https://www.coinglass.com/hyperliquid-liquidation-map
2. View real-time liquidation feed
3. Compare timestamps, sizes, and sides with our system output

### Method 2: HyperLiquid API Direct
```bash
# Check vault info
curl -X POST https://api.hyperliquid.xyz/info \
  -H "Content-Type: application/json" \
  -d '{"type":"meta"}' | jq .

# Check specific vault fills
curl -X POST https://api.hyperliquid.xyz/info \
  -H "Content-Type: application/json" \
  -d '{"type":"userFills","user":"0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"}' | jq .
```

### Method 3: CoinGlass API
```bash
# Requires API key
curl -X GET "https://open-api.coinglass.com/public/v2/liquidation_order?ex=Hyperliquid" \
  -H "coinglassSecret: YOUR_API_KEY" | jq .
```

---

## 🐛 Troubleshooting

### Issue: "No dependencies found"
```bash
cd /home/user/TG-Bot/services/liquidation-aggregator
pip install -r requirements.txt
```

### Issue: "No vaults discovered"
**Possible Causes:**
- No internet connectivity
- HyperLiquid API is down
- Implementation bug in vault discovery

**Solutions:**
1. Check API connectivity: `curl -X POST https://api.hyperliquid.xyz/info -H "Content-Type: application/json" -d '{"type":"meta"}'`
2. Try during active trading hours (US/EU daytime)
3. Review implementation in `dex/hyperliquid_liquidation_registry.py`

### Issue: "All vaults stale"
**Possible Causes:**
- Low market volatility (no liquidations happening)
- Quiet trading period
- API issues

**Solutions:**
1. Run during high volatility periods
2. Extend monitoring duration: `--duration 30`
3. Check market conditions on CoinGlass

### Issue: "No liquidations detected"
**Possible Causes:**
- Market is not volatile enough
- No forced liquidations occurring
- Short monitoring period

**Solutions:**
1. Extend validation: `--duration 30`
2. Run during volatile market conditions
3. Check CoinGlass to confirm low liquidation activity

---

## 📈 Recommended Testing Schedule

| Frequency | Test Type | Command | Purpose |
|-----------|-----------|---------|---------|
| Every commit | Quick validation | `python -m scripts.quick_validation` | Regression check |
| Daily | 10-min validation | `python -m scripts.validate_liquidation_accuracy --duration 10` | Monitor accuracy |
| Weekly | CoinGlass comparison | `python -m scripts.validate_liquidation_accuracy --duration 30 --coinglass-api-key KEY` | Production validation |
| Pre-deployment | Full suite | All of the above + manual verification | Final check |

---

## 📚 Documentation Links

- **Validation Guide**: `services/liquidation-aggregator/docs/VALIDATION_GUIDE.md`
- **Scripts README**: `services/liquidation-aggregator/scripts/README.md`
- **HyperLiquid Detection**: `docs/hyperliquid_liquidation_detection.md`
- **Main README**: `services/liquidation-aggregator/README.md`

---

## 🎓 Understanding the System

### What is a Liquidation Vault?
HyperLiquid doesn't expose a dedicated liquidation stream. Instead, liquidations are executed by the HyperLiquid Protections (HLP) vault and appear in the regular trade channel. The vault address rotates periodically.

### How Does Detection Work?
1. System discovers active liquidation vault addresses via `/info` API
2. Polls each vault's `userFills` to get liquidation trade IDs
3. Matches trade IDs from WebSocket feed against vault fills
4. Classifies matched trades as liquidations with correct side (LONG/SHORT)

### Why Dynamic Discovery?
HyperLiquid recently started rotating between multiple vault addresses. The old single-vault hardcoded approach stopped working. Our dynamic discovery system automatically finds active vaults and survives rotations.

---

## ✅ Next Steps

1. **Run Quick Validation**
   ```bash
   cd /home/user/TG-Bot/services/liquidation-aggregator
   python -m scripts.quick_validation
   ```

2. **If PASS, Run Extended Validation**
   ```bash
   python -m scripts.validate_liquidation_accuracy --duration 10 --export report.json
   ```

3. **Optional: Get CoinGlass Comparison**
   - Sign up at https://www.coinglass.com/pricing
   - Get API key
   - Run: `python -m scripts.validate_liquidation_accuracy --duration 30 --coinglass-api-key YOUR_KEY`

4. **Review Report**
   ```bash
   cat report.json | jq .verdict
   ```

5. **Start Live Monitoring**
   ```bash
   python monitor_liquidations_live.py
   ```

---

## 🤝 Support

- **Documentation**: See `docs/VALIDATION_GUIDE.md` for comprehensive guide
- **GitHub Issues**: Report issues with validation output
- **API Status**: Check HyperLiquid API at https://api.hyperliquid.xyz/info

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Validation System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │  Quick Validation│      │Extended Validation│           │
│  │    (2 minutes)   │      │   (5-30 minutes) │           │
│  │                  │      │                  │           │
│  │ • API Check      │      │ • Real-time      │           │
│  │ • Vault Discovery│      │   Monitoring     │           │
│  │ • Recent Liq.    │      │ • Statistics     │           │
│  └────────┬─────────┘      │ • CoinGlass Comp.│           │
│           │                └────────┬─────────┘           │
│           │                         │                      │
│           └─────────┬───────────────┘                      │
│                     ▼                                      │
│          ┌──────────────────────┐                         │
│          │ HyperLiquid Registry │                         │
│          │  (Dynamic Discovery) │                         │
│          └──────────┬───────────┘                         │
│                     │                                      │
│          ┌──────────▼───────────┐                         │
│          │  HyperLiquid API     │                         │
│          │  /info (vault list)  │                         │
│          │  /userFills          │                         │
│          └──────────────────────┘                         │
│                                                             │
│          ┌──────────────────────┐                         │
│          │  CoinGlass API       │                         │
│          │  (Optional)          │                         │
│          └──────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

**Status:** ✅ Ready for testing
**Tested:** No (awaiting dependency installation and live API test)
**Production Ready:** Yes (pending successful validation)
