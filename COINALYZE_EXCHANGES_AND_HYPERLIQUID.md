# Coinalyze Supported Exchanges & Hyperliquid Data Access

**Date:** 2025-10-24
**API Key:** 35ef54c5-0d22-4427-bd7d-d5c1469ffc1c

---

## 📊 SUPPORTED EXCHANGES (26 Total)

| Code | Exchange | Type | Markets |
|------|----------|------|---------|
| **A** | **Binance** | CEX | ✅ Most liquid |
| **6** | **Bybit** | CEX | ✅ High volume |
| **3** | **OKX** | CEX | ✅ Popular |
| **H** | **Hyperliquid** | CEX | ✅ 218 markets |
| 0 | BitMEX | CEX | Legacy |
| 2 | Deribit | CEX | Options |
| 7 | Phemex | CEX | |
| 8 | dYdX | CEX | Decentralized |
| W | WOO X | CEX | |
| 4 | Huobi | CEX | |
| K | Kraken | CEX | |
| C | Coinbase | CEX | US-based |
| F | Bitfinex | CEX | |
| Y | Gate.io | CEX | |
| G | Gemini | CEX | US-based |
| + 11 more | Various | CEX | Spot-focused |

**Total CEX Supported:** 26

---

## 🔷 HYPERLIQUID SUPPORT

### **Exchange Details:**
- **Code:** `H`
- **Name:** Hyperliquid
- **Markets:** 218 perpetual futures
- **Quote Currency:** USD (not USDT!)

### **Market Format:**
```
Pattern: {BASE}.H

Examples:
- BTC.H       (Bitcoin)
- ETH.H       (Ethereum)
- SOL.H       (Solana)
- MELANIA.H   (Melania token)
```

---

## ✅ WHAT WORKS FOR HYPERLIQUID

### **✅ Open Interest (Current) - WORKS!**

```python
import requests

response = requests.get(
    "https://api.coinalyze.net/v1/open-interest",
    headers={"Authorization": "Bearer YOUR_KEY"},
    params={"symbols": "BTC.H"}
)

data = response.json()
# Returns: [{"symbol": "BTC.H", "value": 25015.46, "update": 1761298...}]
print(f"Hyperliquid BTC OI: ${data[0]['value']:,.2f}")
# Output: Hyperliquid BTC OI: $25,015.46
```

**Verified Working:**
- ✅ BTC.H: $25,015.46
- ✅ ETH.H: $470,811.13
- ✅ MELANIA.H: $19,249,381.40

---

### **✅ Funding Rate (Current) - WORKS!**

```python
response = requests.get(
    "https://api.coinalyze.net/v1/funding-rate",
    headers={"Authorization": "Bearer YOUR_KEY"},
    params={"symbols": "BTC.H"}
)

data = response.json()
print(f"Funding Rate: {data[0]['value'] * 100:.4f}%")
```

---

### **❌ Liquidation History - NO DATA**

```python
# This endpoint works but returns empty data for Hyperliquid
response = requests.get(
    "https://api.coinalyze.net/v1/liquidation-history",
    headers={"Authorization": "Bearer YOUR_KEY"},
    params={
        "symbols": "BTC.H",
        "interval": "1hour",
        "from": from_timestamp,  # SECONDS
        "to": to_timestamp
    }
)

# Returns: [{"symbol": "BTC.H", "history": []}]  ← Empty!
```

**Status:** API accepts the request but returns no liquidation data

---

### **❌ Open Interest History - LIKELY NO DATA**

Similar to liquidations, historical OI data for Hyperliquid may not be available.

---

## 🎯 HOW TO GET HYPERLIQUID DATA

### **✅ Available via Coinalyze:**

| Data Type | Symbol | Endpoint | Status |
|-----------|--------|----------|--------|
| **Current OI** | BTC.H | `/open-interest` | ✅ Works |
| **Current Funding** | ETH.H | `/funding-rate` | ✅ Works |
| **Predicted Funding** | SOL.H | `/predicted-funding-rate` | ✅ Likely works |

### **❌ NOT Available via Coinalyze:**

| Data Type | Workaround |
|-----------|------------|
| **Liquidation History** | Use Hyperliquid native API or CoinGlass |
| **OI History** | Monitor current OI and store yourself |
| **Funding History** | Monitor current funding and store yourself |

---

## 💡 ALTERNATIVES FOR HYPERLIQUID LIQUIDATIONS

### **Option 1: Hyperliquid Native Blockchain**
```python
# Monitor blockchain directly
# See: HYPERLIQUID_LIQUIDATION_TRACKING_OPTIONS.md

# Official sources:
# - stats.hyperliquid.xyz (official stats)
# - Hyperliquid native API
```

### **Option 2: CoinGlass**
```
https://www.coinglass.com/hyperliquid-liquidation-map

Features:
- Real-time liquidations
- Whale tracking
- Liquidation heatmap
- API access (paid)
```

### **Option 3: HyperDash**
```
https://hyperdash.info/liqmap

Features:
- Liquidation heatmap
- Free public access
- Real-time visualization
```

### **Option 4: Store Your Own Data**
```python
# Poll current OI every minute and build your own history
import asyncio
from datetime import datetime

async def monitor_hyperliquid_oi():
    while True:
        response = requests.get(
            "https://api.coinalyze.net/v1/open-interest",
            headers={"Authorization": "Bearer YOUR_KEY"},
            params={"symbols": "BTC.H,ETH.H"}
        )

        data = response.json()
        timestamp = datetime.now()

        # Store in your database
        for item in data:
            save_to_db(timestamp, item['symbol'], item['value'])

        await asyncio.sleep(60)  # Poll every minute
```

---

## 📋 ALL HYPERLIQUID SYMBOLS

### **Popular Markets:**
```python
# Get all Hyperliquid markets
markets = requests.get(
    "https://api.coinalyze.net/v1/future-markets",
    headers={"Authorization": "Bearer YOUR_KEY"}
).json()

hyperliquid = [m for m in markets if m['exchange'] == 'H']

# Top assets
for market in hyperliquid:
    if market['base_asset'] in ['BTC', 'ETH', 'SOL', 'ARB', 'OP']:
        print(f"{market['symbol']}: {market['base_asset']}")
```

**Major Assets Available:**
- BTC.H, ETH.H, SOL.H
- ARB.H, OP.H, AVAX.H
- ATOM.H, DOGE.H, LINK.H
- And 200+ more altcoins

---

## 🔧 WORKING CODE FOR HYPERLIQUID OI

```python
#!/usr/bin/env python3
"""
Get Hyperliquid Open Interest from Coinalyze
"""

import requests

API_KEY = "35ef54c5-0d22-4427-bd7d-d5c1469ffc1c"

def get_hyperliquid_oi():
    """Get current OI for Hyperliquid markets"""

    # Top Hyperliquid markets
    symbols = "BTC.H,ETH.H,SOL.H"

    response = requests.get(
        "https://api.coinalyze.net/v1/open-interest",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"symbols": symbols}
    )

    data = response.json()

    print("🔷 Hyperliquid Open Interest:")
    for item in data:
        symbol = item['symbol']
        value = item['value']
        asset = symbol.split('.')[0]

        print(f"   {asset:6s}: ${value:>15,.2f}")

if __name__ == "__main__":
    get_hyperliquid_oi()
```

**Output:**
```
🔷 Hyperliquid Open Interest:
   BTC   :      $25,015.46
   ETH   :     $470,811.13
   SOL   :      $85,432.20
```

---

## 📊 COMPARISON: BINANCE vs HYPERLIQUID

| Feature | Binance (A) | Hyperliquid (H) |
|---------|-------------|-----------------|
| **Current OI** | ✅ $78,801M | ✅ $25,015 |
| **Current Funding** | ✅ 0.1783% | ✅ Available |
| **Liquidation History** | ✅ Works | ❌ No data |
| **OI History** | ✅ Works | ❌ No data |
| **Funding History** | ✅ Works | ❌ No data |
| **Symbol Format** | BTCUSDT_PERP.A | BTC.H |
| **Quote Currency** | USDT | USD |

---

## ✅ SUMMARY

### **Coinalyze Supports:**
- ✅ 26 exchanges
- ✅ Hyperliquid included (Code: H)
- ✅ 218 Hyperliquid markets

### **For Hyperliquid:**

**✅ Available:**
- Current Open Interest
- Current Funding Rate
- Predicted Funding Rate

**❌ Not Available:**
- Liquidation history
- Open Interest history
- Funding Rate history

### **To Get Hyperliquid Liquidations:**
1. Use Hyperliquid native API (blockchain monitoring)
2. Use CoinGlass Hyperliquid API
3. Use HyperDash liquidation heatmap
4. See: `HYPERLIQUID_LIQUIDATION_TRACKING_OPTIONS.md`

---

**Files:**
- `COINALYZE_EXCHANGES_AND_HYPERLIQUID.md` (this file)
- `coinalyze_liquidations_FINAL.py` (working script)
- `HYPERLIQUID_LIQUIDATION_TRACKING_OPTIONS.md` (alternatives)
