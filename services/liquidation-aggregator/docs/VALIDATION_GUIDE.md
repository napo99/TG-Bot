# Liquidation Detection Validation Guide

This guide explains how to validate that the HyperLiquid liquidation detection system is working correctly and how to compare results against external data sources like CoinGlass.

## Table of Contents

1. [Quick Validation (2 minutes)](#quick-validation)
2. [Extended Validation (5-30 minutes)](#extended-validation)
3. [CoinGlass Comparison](#coinglass-comparison)
4. [Manual Verification](#manual-verification)
5. [Troubleshooting](#troubleshooting)

---

## Quick Validation

**Time Required:** ~2 minutes
**Purpose:** Verify basic functionality and API connectivity

### Steps

```bash
cd services/liquidation-aggregator

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run quick validation
python -m scripts.quick_validation
```

### Expected Output

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
    • 0x5f8a21...3c9a: 32 fills (last: 89s ago)

[4/4] Checking recent liquidations...
  ✅ Found 77 recent liquidation(s)

  Latest liquidations:
    1. BTC LONG liquidation: 0.0850 @ $95234.50 ($8,094.93) - 89s ago
    2. ETH SHORT liquidation: 2.3400 @ $3456.78 ($8,088.86) - 127s ago
    ...

======================================================================
VALIDATION SUMMARY
======================================================================
✅ PASS: System is operational
```

### What It Tests

- ✅ HyperLiquid API connectivity
- ✅ Registry initialization
- ✅ Dynamic vault discovery
- ✅ Liquidation data retrieval
- ✅ Per-vault health status

---

## Extended Validation

**Time Required:** 5-30 minutes
**Purpose:** Comprehensive testing with statistical analysis

### Steps

```bash
# 5-minute validation (recommended for quick checks)
python -m scripts.validate_liquidation_accuracy --duration 5

# 10-minute validation (better sample size)
python -m scripts.validate_liquidation_accuracy --duration 10

# 30-minute validation (comprehensive)
python -m scripts.validate_liquidation_accuracy --duration 30

# Export results to JSON
python -m scripts.validate_liquidation_accuracy --duration 10 --export validation_report.json
```

### Expected Output

```
🚀 Starting 10-minute liquidation validation
✅ HyperLiquid registry initialized
🔍 Testing vault discovery...
✅ Discovered 2 active vault(s)
  ✓ 0x2e3d...dd14: 45 fills (last fill 127s ago)
  ✓ 0x5f8a...3c9a: 32 fills (last fill 89s ago)

📊 Monitoring liquidations for 10 minute(s)...
⏱️  Progress: 10% | Liquidations: 12 | Remaining: 540s
⏱️  Progress: 20% | Liquidations: 28 | Remaining: 480s
...
✅ Monitoring complete. Detected 156 liquidations

================================================================================
LIQUIDATION VALIDATION REPORT
================================================================================

📅 Duration: 10 minutes
⏰ Start: 2025-10-28T10:30:00
⏰ End: 2025-10-28T10:40:00

🔍 VAULT DISCOVERY
  Vaults Found: 2
    • 0x2e3d...dd14
    • 0x5f8a...3c9a
  Health Checks: 60
  Errors: 0

💥 LIQUIDATION DETECTION
  Total Detected: 156
  Total Volume: $2,847,392.50
  Avg Size: $18,252.52

  By Coin:
    • BTC: 89
    • ETH: 54
    • SOL: 13

  By Side:
    • LONG: 87
    • SHORT: 69

🎯 VERDICT: PASS

Successes:
  ✅ Vault discovery working (2 vault(s) found)
  ✅ Liquidation detection working (156 detected)
  ✅ No vault errors

================================================================================
```

### What It Tests

- ✅ Vault discovery mechanism
- ✅ Real-time liquidation tracking
- ✅ Vault health monitoring over time
- ✅ Statistical analysis (volume, distribution, etc.)
- ✅ Error handling and recovery

---

## CoinGlass Comparison

**Time Required:** 10-30 minutes
**Purpose:** Validate accuracy against external reference data

### Prerequisites

1. **Get CoinGlass API Key**
   - Sign up at [coinglass.com](https://www.coinglass.com/pricing)
   - Choose a plan that includes liquidation data access
   - Copy your API key from the dashboard

2. **Set Environment Variable (Optional)**
   ```bash
   export COINGLASS_API_KEY="your_api_key_here"
   ```

### Steps

```bash
# Run validation with CoinGlass comparison
python -m scripts.validate_liquidation_accuracy \
  --duration 10 \
  --coinglass-api-key YOUR_API_KEY

# Or using environment variable
python -m scripts.validate_liquidation_accuracy \
  --duration 10 \
  --coinglass-api-key $COINGLASS_API_KEY \
  --export coinglass_comparison.json
```

### Expected Output (with CoinGlass)

```
================================================================================
LIQUIDATION VALIDATION REPORT
================================================================================

📅 Duration: 10 minutes
⏰ Start: 2025-10-28T10:30:00
⏰ End: 2025-10-28T10:40:00

🔍 VAULT DISCOVERY
  [... same as above ...]

💥 LIQUIDATION DETECTION
  Total Detected: 156
  Total Volume: $2,847,392.50
  Avg Size: $18,252.52

📊 COINGLASS COMPARISON
  Our Count: 156
  CoinGlass Count: 158
  Difference: 2 (1.3%)
  Detected 2 fewer liquidations than CoinGlass

🎯 VERDICT: PASS

Successes:
  ✅ Vault discovery working (2 vault(s) found)
  ✅ Liquidation detection working (156 detected)
  ✅ No vault errors
  ✅ 98.7% match rate with CoinGlass

================================================================================
```

### Understanding the Comparison

**Match Rate Guidelines:**

| Match Rate | Assessment | Action |
|------------|------------|--------|
| 95-100% | Excellent | System validated, production ready |
| 90-95% | Good | Minor discrepancies expected (timing/filtering) |
| 80-90% | Fair | Review implementation, check timing windows |
| <80% | Poor | Investigate data collection or vault discovery |

**Common Reasons for Differences:**

1. **Timing Windows**: CoinGlass and our system may use slightly different time boundaries
2. **Filtering**: CoinGlass may filter small liquidations differently
3. **Vault Discovery Lag**: Brief delay between vault rotation and discovery
4. **Data Source**: CoinGlass aggregates from multiple sources; slight differences expected

---

## Manual Verification

For ultimate confidence, manually verify liquidations against HyperLiquid's public data.

### Method 1: HyperLiquid Website

1. Visit [HyperLiquid Explorer](https://app.hyperliquid.xyz/)
2. Navigate to "Liquidations" section
3. Compare recent liquidations with our system output
4. Check: coin, side, size, price, timestamp

### Method 2: HyperLiquid API Direct

```bash
# Fetch vault info directly
curl -X POST https://api.hyperliquid.xyz/info \
  -H "Content-Type: application/json" \
  -d '{"type":"meta"}' | jq .

# Check specific vault fills
curl -X POST https://api.hyperliquid.xyz/info \
  -H "Content-Type: application/json" \
  -d '{"type":"userFills","user":"0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"}' | jq .
```

### Method 3: CoinGlass Website

1. Visit [CoinGlass HyperLiquid Liquidations](https://www.coinglass.com/hyperliquid-liquidation-map)
2. View real-time liquidation feed
3. Compare timestamps and values with our system
4. Note: CoinGlass updates every 1-5 seconds

### Verification Checklist

- [ ] Vault addresses match HyperLiquid's official vaults
- [ ] Liquidation timestamps are recent (within seconds)
- [ ] Liquidation sizes match across sources
- [ ] Long/short classification is correct
- [ ] Coin symbols are accurate
- [ ] No duplicate liquidations in our system

---

## Troubleshooting

### Issue: No Vaults Discovered

**Symptoms:**
```
🔍 VAULT DISCOVERY
  Vaults Found: 0
```

**Solutions:**

1. **Check API Connectivity**
   ```bash
   curl -X POST https://api.hyperliquid.xyz/info \
     -H "Content-Type: application/json" \
     -d '{"type":"meta"}'
   ```

2. **Verify Implementation**
   - Check `dex/hyperliquid_liquidation_registry.py`
   - Ensure `_discover_active_vaults()` is working
   - Review API endpoint changes

3. **Check Logs**
   ```bash
   # Run with debug logging
   python -c "from loguru import logger; logger.debug('Test')"
   ```

---

### Issue: All Vaults Stale

**Symptoms:**
```
⚠️  Warning: all tracked vaults are stale. HyperLiquid might be rotating vaults
```

**Solutions:**

1. **Check During Active Hours**
   - HyperLiquid has lower activity during Asian/European off-hours
   - Try validation during US/European trading hours

2. **Verify Market Volatility**
   - Liquidations occur during volatile markets
   - Check current BTC/ETH volatility

3. **Increase Monitoring Duration**
   ```bash
   # Run for 30 minutes to capture activity
   python -m scripts.validate_liquidation_accuracy --duration 30
   ```

---

### Issue: No Liquidations Detected

**Symptoms:**
```
💥 LIQUIDATION DETECTION
  Total Detected: 0
```

**Solutions:**

1. **Check Market Conditions**
   - Liquidations require high volatility
   - Verify if market is moving significantly

2. **Extend Monitoring Period**
   - 5-10 minutes may be too short during quiet periods
   - Try 30-60 minute validation

3. **Verify Vault Fills**
   ```bash
   # Check if vaults have recent fills
   python -m scripts.check_hyperliquid_registry
   ```

---

### Issue: Large Discrepancy with CoinGlass

**Symptoms:**
```
📊 COINGLASS COMPARISON
  Difference: 45 (30.5%)
```

**Solutions:**

1. **Check Time Synchronization**
   - Ensure system clock is accurate
   - CoinGlass uses specific time boundaries

2. **Verify CoinGlass API Response**
   - Check if API returned complete data
   - Review `coinglass_comparison` section in JSON export

3. **Review Filtering Logic**
   - Check if our system filters differently
   - Verify minimum liquidation size thresholds

4. **Extend Validation Period**
   - Longer periods provide better comparison
   - Try 30-60 minute validation

---

## Continuous Validation

### Recommended Schedule

| Frequency | Test Type | Purpose |
|-----------|-----------|---------|
| Every commit | Quick validation | Ensure no regressions |
| Daily | 10-min extended | Monitor accuracy |
| Weekly | 30-min with CoinGlass | Production validation |
| Before deployment | Full suite | Final verification |

### Automated Testing

```bash
# Add to CI/CD pipeline
pytest services/liquidation-aggregator/tests/

# Run validation suite
./run_validation_suite.sh
```

### Monitoring in Production

```bash
# Start monitoring dashboard
python monitor_liquidations_live.py

# Check health periodically
python -m scripts.check_hyperliquid_registry
```

---

## Expected Accuracy Benchmarks

Based on system design and testing:

| Metric | Expected Range | Notes |
|--------|----------------|-------|
| Vault Discovery Success | 95-100% | Should always find active vaults |
| Liquidation Detection Rate | 98-100% | May miss <1% due to timing |
| CoinGlass Match Rate | 90-100% | Minor timing differences expected |
| Vault Health Uptime | 98-100% | Occasional API timeouts acceptable |
| False Positives | 0% | Should never detect non-liquidations |
| Latency | <5 seconds | From exchange to our system |

---

## Support

If validation fails persistently:

1. **Check GitHub Issues**: [TG-Bot Issues](https://github.com/napo99/TG-Bot/issues)
2. **Review Documentation**: `docs/hyperliquid_liquidation_detection.md`
3. **Inspect Logs**: Check error messages in validation output
4. **Contact Team**: Include validation report JSON in bug reports

---

## Changelog

- **2025-10-28**: Added CoinGlass comparison and comprehensive validation suite
- **2025-10-28**: Implemented dynamic vault discovery validation
- **2025-10-21**: Initial validation framework
