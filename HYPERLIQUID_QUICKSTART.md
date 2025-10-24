# 🚀 Hyperliquid Liquidations - 5-Minute Quickstart

**Get Hyperliquid liquidation data in 5 minutes - 100% FREE**

---

## ⚡ Fastest Method: Coinalyze API

### Step 1: Get Free API Key (2 minutes)
1. Go to https://coinalyze.net/
2. Sign up (no credit card)
3. Account Settings → API Key → Copy

### Step 2: Test It (3 minutes)

```python
import requests

API_KEY = "your_api_key_here"

url = "https://api.coinalyze.net/v1/liquidation-history"
headers = {"Authorization": f"Bearer {API_KEY}"}
params = {
    "symbols": "HYPERLIQUID:BTCUSDT",
    "limit": 20
}

response = requests.get(url, headers=headers, params=params)
liquidations = response.json().get("history", [])

for liq in liquidations:
    print(f"💥 {liq['symbol']}: {liq['side'].upper()} ${liq['value']:,.0f}")
```

### Expected Output
```
💥 HYPERLIQUID:BTCUSDT: LONG $125,430
💥 HYPERLIQUID:BTCUSDT: SHORT $89,234
💥 HYPERLIQUID:ETHUSDT: SHORT $234,567
```

---

## 🎯 FREE Options Comparison

| Provider | Setup Time | Rate Limit | Best For |
|----------|-----------|------------|----------|
| **Coinalyze** | 5 min | 40/min | Quick start, simple projects |
| **Hyperliquid Native** | 30 min | 1200 weight/min | Need higher limits |
| **Chainstack RPC** | 1 hour | 25 RPS (3M/mo) | Blockchain monitoring |
| **Build from scratch** | 12-20 hours | Unlimited | Full control |

---

## 📚 Full Documentation

- **`HYPERLIQUID_FREE_INTEGRATION_GUIDE.md`** ← **START HERE**
  - Complete code examples for all 3 FREE options
  - Working implementations you can copy/paste
  - Rate limit handling, error handling, async support

- **`HYPERLIQUID_LIQUIDATION_DATA_ANALYSIS.md`**
  - How CoinGlass gets the data (blockchain monitoring)
  - Why there's no simple WebSocket like Binance
  - Technical deep dive

- **`HYPERLIQUID_DATA_PROVIDERS_COMPARISON.md`**
  - All 19 providers compared
  - Pricing, features, rate limits
  - Recommendations by use case

- **`HYPERLIQUID_COST_COMPARISON.md`**
  - Free vs paid options
  - Cost-benefit analysis
  - ROI calculations

- **`HYPERLIQUID_TECHNICAL_IMPLEMENTATION_GUIDE.md`**
  - Full blockchain monitoring implementation (12-20 hours)
  - Step-by-step guide
  - Production-ready code

---

## 💡 Recommendation

**For most users:** Start with **Coinalyze** (5 minutes, free, works great)

**If you need more:** Add **Hyperliquid Native API** (30 minutes, higher limits)

**If you're ambitious:** Build **Blockchain Monitor** (12-20 hours, unlimited, complete control)

---

## 🔗 Quick Links

- Coinalyze API Docs: https://api.coinalyze.net/v1/doc/
- Hyperliquid Docs: https://hyperliquid.gitbook.io/
- Your Integration Guide: `HYPERLIQUID_FREE_INTEGRATION_GUIDE.md`

---

**Next Step:** Open `HYPERLIQUID_FREE_INTEGRATION_GUIDE.md` and copy Option 1 code! 🚀
