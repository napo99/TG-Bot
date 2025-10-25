# Coinalyze Real-Time Data - Quick Reference

**API Key:** 35ef54c5-0d22-4427-bd7d-d5c1469ffc1c
**What Works:** Real-time current data only (no history)

---

## ⭐ 3 REAL-TIME ENDPOINTS THAT WORK

### **1. Current Open Interest** 💰
**Updates:** Every few seconds
**Use:** Monitor liquidation risk

```python
import requests

response = requests.get(
    "https://api.coinalyze.net/v1/open-interest",
    headers={"Authorization": "Bearer 35ef54c5-0d22-4427-bd7d-d5c1469ffc1c"},
    params={"symbols": "BTCUSDT_PERP.A"}  # Binance BTC
)

data = response.json()[0]
# Returns:
# {
#   "symbol": "BTCUSDT_PERP.A",
#   "value": 78621.542,        # OI in millions
#   "update": 1761295460764    # Unix timestamp (ms)
# }

print(f"BTC Open Interest: ${data['value']:,.0f}M")
# Output: BTC Open Interest: $78,622M
```

---

### **2. Current Funding Rate** 💸
**Updates:** Every few seconds
**Use:** Track position costs, predict liquidations

```python
response = requests.get(
    "https://api.coinalyze.net/v1/funding-rate",
    headers={"Authorization": "Bearer 35ef54c5-0d22-4427-bd7d-d5c1469ffc1c"},
    params={"symbols": "BTCUSDT_PERP.A"}
)

data = response.json()[0]
# Returns:
# {
#   "symbol": "BTCUSDT_PERP.A",
#   "value": 0.001783,           # Funding rate (decimal)
#   "update": 1761295466766      # Unix timestamp (ms)
# }

funding_pct = data['value'] * 100
print(f"Funding Rate: {funding_pct:.4f}% per 8 hours")
# Output: Funding Rate: 0.1783% per 8 hours

# Calculate daily cost
daily_rate = data['value'] * 3 * 100  # 3 fundings per day
print(f"Daily Rate: {daily_rate:.4f}%")
# Output: Daily Rate: 0.5349%
```

---

### **3. Predicted Funding Rate** 🔮
**Updates:** Constantly (real-time prediction)
**Use:** Predict next funding payment, plan positions

```python
response = requests.get(
    "https://api.coinalyze.net/v1/predicted-funding-rate",
    headers={"Authorization": "Bearer 35ef54c5-0d22-4427-bd7d-d5c1469ffc1c"},
    params={"symbols": "BTCUSDT_PERP.A"}
)

data = response.json()[0]
# Returns:
# {
#   "symbol": "BTCUSDT_PERP.A",
#   "value": 0.003469,           # Predicted rate
#   "update": 1761295467269
# }

predicted_pct = data['value'] * 100
print(f"Predicted: {predicted_pct:.4f}%")
# Output: Predicted: 0.3469%
```

---

## 📋 BONUS: Discovery Endpoints

### **Get All Exchanges**
```python
response = requests.get(
    "https://api.coinalyze.net/v1/exchanges",
    headers={"Authorization": "Bearer YOUR_KEY"}
)

exchanges = response.json()
# Returns: [{"name": "Binance", "code": "A"}, {"name": "Hyperliquid", "code": "H"}, ...]

# Find exchange codes
for ex in exchanges:
    if ex['name'] in ['Binance', 'Bybit', 'Hyperliquid']:
        print(f"{ex['name']}: {ex['code']}")
# Output:
# Binance: A
# Bybit: B
# Hyperliquid: H
```

### **Get All Markets**
```python
response = requests.get(
    "https://api.coinalyze.net/v1/future-markets",
    headers={"Authorization": "Bearer YOUR_KEY"}
)

markets = response.json()
# Returns: 3737 markets with full metadata

# Find Hyperliquid markets
hyperliquid = [m for m in markets if m['exchange'] == 'H']
print(f"Hyperliquid has {len(hyperliquid)} markets")
# Output: Hyperliquid has 218 markets

# Get symbols
for market in hyperliquid[:5]:
    print(f"{market['base_asset']}: {market['symbol']}")
# Output:
# MELANIA: MELANIA.H
# FTT: FTT.H
# NEIROETH: NEIROETH.H
```

---

## 🎯 PRODUCTION USE CASES

### **1. Liquidation Risk Monitor**
```python
def check_liquidation_risk(symbol):
    """Check if OI and funding suggest liquidation risk"""

    # Get OI
    oi_resp = requests.get(
        "https://api.coinalyze.net/v1/open-interest",
        headers={"Authorization": "Bearer YOUR_KEY"},
        params={"symbols": symbol}
    )
    oi = oi_resp.json()[0]['value']

    # Get funding
    fr_resp = requests.get(
        "https://api.coinalyze.net/v1/funding-rate",
        headers={"Authorization": "Bearer YOUR_KEY"},
        params={"symbols": symbol}
    )
    funding = fr_resp.json()[0]['value'] * 100

    # Risk logic
    if oi > 100000 and abs(funding) > 0.5:
        return "HIGH RISK"
    elif oi > 50000 and abs(funding) > 0.3:
        return "MEDIUM RISK"
    else:
        return "LOW RISK"

risk = check_liquidation_risk("BTCUSDT_PERP.A")
print(f"Liquidation Risk: {risk}")
```

### **2. Funding Rate Arbitrage**
```python
def find_funding_arbitrage():
    """Find exchanges with different funding rates"""

    symbols = [
        "BTCUSDT_PERP.A",  # Binance
        "BTCUSDT_PERP.B",  # Bybit
        "BTCUSDT_PERP.6",  # OKX
    ]

    rates = {}
    for symbol in symbols:
        resp = requests.get(
            "https://api.coinalyze.net/v1/funding-rate",
            headers={"Authorization": "Bearer YOUR_KEY"},
            params={"symbols": symbol}
        )
        if resp.json():
            rates[symbol] = resp.json()[0]['value'] * 100

    # Find spread
    max_symbol = max(rates, key=rates.get)
    min_symbol = min(rates, key=rates.get)
    spread = rates[max_symbol] - rates[min_symbol]

    print(f"Funding spread: {spread:.4f}%")
    print(f"  Long {min_symbol}: {rates[min_symbol]:.4f}%")
    print(f"  Short {max_symbol}: {rates[max_symbol]:.4f}%")

    return spread
```

### **3. Real-Time Dashboard**
```python
import time
from datetime import datetime

def realtime_dashboard():
    """Live updating dashboard"""

    symbols = {
        "BTCUSDT_PERP.A": "BTC",
        "ETHUSDT_PERP.A": "ETH",
        "SOLUSDT_PERP.A": "SOL"
    }

    while True:
        print("\033[2J\033[H")  # Clear screen
        print(f"🚀 Crypto Futures Dashboard - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 70)
        print(f"{'Asset':6s} | {'OI ($M)':>12s} | {'Funding %':>10s} | {'Predicted %':>12s}")
        print("-" * 70)

        for symbol, name in symbols.items():
            try:
                # Get OI
                oi = requests.get(
                    "https://api.coinalyze.net/v1/open-interest",
                    headers={"Authorization": "Bearer YOUR_KEY"},
                    params={"symbols": symbol}
                ).json()[0]['value']

                # Get funding
                fr = requests.get(
                    "https://api.coinalyze.net/v1/funding-rate",
                    headers={"Authorization": "Bearer YOUR_KEY"},
                    params={"symbols": symbol}
                ).json()[0]['value'] * 100

                # Get predicted
                pfr = requests.get(
                    "https://api.coinalyze.net/v1/predicted-funding-rate",
                    headers={"Authorization": "Bearer YOUR_KEY"},
                    params={"symbols": symbol}
                ).json()[0]['value'] * 100

                print(f"{name:6s} | ${oi:>11,.0f} | {fr:>9.4f}% | {pfr:>11.4f}%")

            except:
                print(f"{name:6s} | Error fetching data")

        time.sleep(5)  # Update every 5 seconds
```

---

## 🔥 LIVE DATA FROM DEMO

**Binance BTC (BTCUSDT_PERP.A):**
```
Open Interest:   $78,622M
Funding Rate:    0.1783% (per 8 hours)
Daily Cost:      0.5349%
Annual Cost:     195.24%
Predicted:       0.3469%
```

**Interpretation:**
- ✅ Healthy OI ($78B)
- ✅ Low positive funding (longs paying shorts)
- ⚠️  Predicted funding nearly 2x current (bullish pressure building)
- 💡 Consider: Long positions will pay ~0.5%/day funding

---

## 📊 SYMBOL FORMAT GUIDE

**Pattern:** `{BASE}{QUOTE}_PERP.{EXCHANGE_CODE}`

| Exchange | Code | BTC Symbol | ETH Symbol |
|----------|------|------------|------------|
| Binance | A | BTCUSDT_PERP.A | ETHUSDT_PERP.A |
| Bybit | B | BTCUSDT_PERP.B | ETHUSDT_PERP.B |
| Hyperliquid | H | BTC.H | ETH.H |
| OKX | 6 | BTCUSDT_PERP.6 | ETHUSDT_PERP.6 |

**Get full list:** `/v1/exchanges` and `/v1/future-markets`

---

## ⚡ RATE LIMITS

**Free Tier:** 40 requests/minute

**Best Practices:**
- Query multiple symbols in one request (comma-separated)
- Cache exchange/market lists (they don't change often)
- Poll real-time data every 5-10 seconds (not faster)
- Use async/await for parallel requests

**Example - Multiple Symbols:**
```python
# ✅ Good: One request for multiple symbols
params = {"symbols": "BTCUSDT_PERP.A,ETHUSDT_PERP.A,SOLUSDT_PERP.A"}
response = requests.get("https://api.coinalyze.net/v1/open-interest", ...)

# ❌ Bad: Three separate requests
for symbol in symbols:
    response = requests.get(..., params={"symbols": symbol})
```

---

## ❌ WHAT DOESN'T WORK

**Historical Endpoints (return empty):**
- `/open-interest-history` ❌
- `/funding-rate-history` ❌
- `/liquidation-history` ❌

**Likely Reason:** Free tier limitation or genuinely no data

**Solution:** Use real-time endpoints and store data yourself

---

## ✅ SUMMARY

**Your API key provides:**
- ✅ Real-time Open Interest
- ✅ Real-time Funding Rates
- ✅ Predicted Funding Rates
- ✅ Market discovery
- ✅ 40 requests/minute

**Perfect for:**
- Live monitoring dashboards
- Funding rate arbitrage
- Liquidation risk analysis
- Position cost tracking

**Not available:**
- ❌ Historical data
- ❌ Liquidation history
- ❌ Time-series analysis

---

**Demo Script:** `coinalyze_realtime_demo.py`
**Test Results:** `coinalyze_endpoint_test_results.json`
**Full Guide:** `COINALYZE_WORKING_ENDPOINTS.md`
