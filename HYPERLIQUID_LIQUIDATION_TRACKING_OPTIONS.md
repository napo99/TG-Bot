# Hyperliquid Liquidation Tracking - All Available Options

**Updated:** 2025-10-24
**Question:** Can we track liquidations from Hyperliquid website/dashboard/GUI?

**Answer:** ✅ YES! Multiple options available

---

## 🎯 Official Hyperliquid Tools

### **1. Hyperliquid Stats** ✅ OFFICIAL
**URL:** https://stats.hyperliquid.xyz/

**Features:**
- ✅ **Liquidations Section** with two views:
  - By coin (BTC, ETH, SOL, etc.)
  - By margin type
- ✅ **Total Notional Liquidated** - Aggregate liquidation volume
- ✅ **Largest Liquidated Users By USD** - Ranked table of addresses
- ✅ Filterable by coin selection
- ✅ Historical data available

**What You Can See:**
```
- Liquidation volumes per coin
- Largest liquidated addresses
- Total liquidations over time
- Filter by specific assets
```

**Access:** Free, no login required

---

### **2. Hyperliquid App/Explorer** ⚠️ LIMITED
**URL:** https://app.hyperliquid.xyz/explorer

**Features:**
- Block explorer functionality
- Transaction history
- ⚠️ No dedicated liquidations view
- ⚠️ Need to search specific addresses/transactions

**Use Case:** Good for researching specific liquidation events, not for monitoring

---

## 🎯 Third-Party Dashboards (FREE)

### **3. HyperDash** ✅ RECOMMENDED
**URL:** https://hyperdash.info/liqmap

**Features:**
- ✅ **Interactive Liquidation Heatmap**
- ✅ Visualize upcoming liquidation levels
- ✅ Real-time analytics
- ✅ Track successful traders
- ✅ Liquidation risk analysis
- ✅ Potential market impact visualization

**What You Can See:**
```
- Liquidation clusters at price levels
- Where liquidations will occur
- Market pressure zones
- Real-time position data
```

**Access:** Free, public dashboard

---

### **4. CoinGlass Hyperliquid Liquidation Map** ✅ COMPREHENSIVE
**URL:** https://www.coinglass.com/hyperliquid-liquidation-map

**Features:**
- ✅ **Real-time liquidation tracking**
- ✅ Whale liquidation monitoring
- ✅ Liquidation price distribution
- ✅ Liquidation amounts at different price levels
- ✅ Market dynamics analysis
- ✅ Historical liquidation data

**What You Can See:**
```
- Recent liquidations (long/short)
- Whale liquidation events
- Price levels with liquidation risk
- 24h liquidation volumes
- Liquidation heatmap
```

**Access:** Free basic access, premium features require subscription

---

### **5. HyperTracker** ✅ TRADER-FOCUSED
**URL:** https://coinmarketman.com/blog/hyperliquid-wallet-tracker/

**Features:**
- ✅ **Real-time wallet behavior tracking**
- ✅ Perps Pages (command center)
- ✅ Track sentiment and positioning
- ✅ Liquidation risk monitoring
- ✅ Successful trader tracking

**What You Can See:**
```
- Wallet-level liquidation risk
- Real-time position changes
- Trader performance metrics
- Liquidation risk alerts
```

**Access:** Free basic features

---

### **6. CoinAnk Hyperliquid Tracker** ✅ WHALE FOCUS
**URL:** https://coinank.com/hyperliquid

**Features:**
- ✅ **Whale tracking**
- ✅ Large trader monitoring
- ✅ Liquidation alerts
- ✅ Position tracking
- ✅ Real-time notifications

**What You Can See:**
```
- Whale liquidations
- Large position changes
- Liquidation events from major traders
```

**Access:** Freemium (basic free, premium features)

---

### **7. Coinalyze Hyperliquid** ✅ ANALYTICS
**URL:** https://coinalyze.net/hyperliquid/liquidations/

**Features:**
- ✅ Liquidation charts
- ✅ Historical liquidation data
- ✅ Long/short breakdown
- ✅ Volume analysis
- ✅ Multi-timeframe views

**What You Can See:**
```
- Liquidation volume charts
- Long vs short liquidations
- Historical trends
- Aggregated data
```

**Access:** Free with API key (for data access)

---

## 📊 Comparison Table

| Tool | Type | Liquidations | Real-Time | Historical | Free | Best For |
|------|------|-------------|-----------|------------|------|----------|
| **Hyperliquid Stats** | Official | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Official data |
| **HyperDash** | 3rd Party | ✅ Heatmap | ✅ Yes | ✅ Yes | ✅ Yes | Visualization |
| **CoinGlass** | 3rd Party | ✅ Comprehensive | ✅ Yes | ✅ Yes | ⚠️ Limited | Whale tracking |
| **HyperTracker** | 3rd Party | ✅ Risk-focused | ✅ Yes | ✅ Yes | ✅ Yes | Trader analysis |
| **CoinAnk** | 3rd Party | ✅ Whale-focused | ✅ Yes | ✅ Yes | ⚠️ Limited | Alerts |
| **Coinalyze** | 3rd Party | ✅ Charts | ✅ Yes | ✅ Yes | ✅ Yes | Analytics |

---

## 🎯 Recommended Workflow

### **For General Monitoring:**
1. **Hyperliquid Stats** - Official source
2. **HyperDash** - Visual heatmap
3. **CoinGlass** - Comprehensive tracking

### **For Trading:**
1. **HyperDash** - Liquidation levels
2. **HyperTracker** - Risk analysis
3. **CoinAnk** - Whale alerts

### **For Data Collection/API:**
1. **Coinalyze API** - Programmatic access
2. **Hyperliquid Native API** - Direct blockchain
3. **Build your own** - Full control

---

## 💡 What Data Each Shows

### **Hyperliquid Stats (Official):**
```json
{
  "totalLiquidated": "$12.5M",
  "byAsset": {
    "BTC": "$8.2M",
    "ETH": "$3.1M",
    "SOL": "$1.2M"
  },
  "largestUsers": [
    {"address": "0x123...", "amount": "$250,000"},
    {"address": "0x456...", "amount": "$180,000"}
  ]
}
```

### **HyperDash Heatmap:**
```
Visual representation:
- Red zones: High liquidation risk
- Price levels with clusters
- Real-time position density
```

### **CoinGlass:**
```json
{
  "recentLiquidations": [
    {"time": "14:23", "side": "LONG", "value": "$125,430", "asset": "BTC"},
    {"time": "14:22", "side": "SHORT", "value": "$89,234", "asset": "ETH"}
  ],
  "24hTotal": "$4.2M",
  "longShortRatio": "1.3"
}
```

---

## 🚀 How to Access Each

### **Hyperliquid Stats:**
```
1. Go to https://stats.hyperliquid.xyz/
2. Scroll to "Liquidations" section
3. Select coins to filter
4. View "Total Notional Liquidated"
5. Check "Largest Liquidated Users"
```

### **HyperDash:**
```
1. Go to https://hyperdash.info/liqmap
2. View liquidation heatmap
3. See price levels with liquidation clusters
4. Analyze market impact zones
```

### **CoinGlass:**
```
1. Go to https://www.coinglass.com/hyperliquid-liquidation-map
2. View real-time liquidation map
3. Check recent liquidations
4. Analyze whale liquidations
5. Track price levels
```

---

## 📋 Data You Can Extract

### **From GUI (Manual):**
- ✅ Recent liquidations (last 24h)
- ✅ Liquidation volumes by asset
- ✅ Largest liquidated addresses
- ✅ Liquidation heatmap zones
- ✅ Long/short breakdowns

### **From API (Programmatic):**
- ✅ Historical liquidation data
- ✅ Real-time liquidation stream
- ✅ Per-user liquidation history
- ✅ Aggregated metrics
- ✅ Custom time ranges

---

## 💡 Key Insights

### **How Hyperliquid Liquidations Work:**
1. **Mark Price Based** - Uses CEX prices + Hyperliquid book
2. **Two-Stage Process:**
   - Stage 1: Market orders to close position
   - Stage 2: Backstop via liquidator vault (HLP)
3. **No Clearance Fee** - Trader-friendly
4. **HLP Benefits** - Liquidation profits go to vault holders

### **What Makes Hyperliquid Different:**
- ✅ On-chain transparency (all liquidations visible)
- ✅ Robust mark price (not single source)
- ✅ Community benefits (HLP profits)
- ✅ No hidden fees

---

## 🎯 Best Option for Your Use Case

### **If you want to:**

**Just monitor visually:**
→ Use **Hyperliquid Stats** + **HyperDash**

**Track specific traders:**
→ Use **HyperTracker** or **CoinAnk**

**Build your own system:**
→ Use **Coinalyze API** or **Hyperliquid Native API**

**Get alerts:**
→ Use **CoinAnk** or **CoinGlass** (premium)

**Analyze historical data:**
→ Use **Coinalyze** or **CoinGlass**

---

## ✅ Summary

**Can you track Hyperliquid liquidations from GUI?**
→ **YES!** Multiple free options available

**Best free dashboards:**
1. **Hyperliquid Stats** (official)
2. **HyperDash** (heatmap)
3. **CoinGlass** (comprehensive)

**All show:**
- ✅ Recent liquidations
- ✅ Liquidation volumes
- ✅ Asset breakdowns
- ✅ Real-time data
- ✅ Historical trends

**No coding required** - Just open the website and view!

---

**Recommendation:** Start with **Hyperliquid Stats** (official) and **HyperDash** (visual heatmap) to monitor liquidations manually while you build API integration! 🎯
