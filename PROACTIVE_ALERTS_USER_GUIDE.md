# 🚨 PROACTIVE CRYPTO ALERTS - USER GUIDE

## 📋 Overview

The crypto assistant bot now includes **proactive alert monitoring** that watches for significant market events and sends real-time notifications to Telegram. This system monitors liquidation cascades and open interest explosions 24/7.

## 🚀 NEW FEATURES ADDED

### 1. **Real-time Liquidation Monitoring**
- Monitors Binance liquidation stream 24/7
- Detects large single liquidations
- Identifies liquidation cascades (multiple liquidations in 30 seconds)
- Configurable thresholds per asset

### 2. **OI Explosion Detection**  
- Monitors Open Interest changes across major exchanges
- Detects sudden OI surges (institutional positioning)
- Cross-exchange confirmation required
- 15-minute detection windows

### 3. **Smart Alert System**
- Priority-based message delivery
- Deduplication prevents spam
- Rate limiting (max alerts per hour)
- Rich formatted messages with emojis

---

## 🎯 ALERT THRESHOLDS

### **Liquidation Alerts**
| Asset | Single Liquidation | Cascade Value | Cascade Count |
|-------|-------------------|---------------|---------------|
| **BTC** | $100,000+ | $500,000+ | 5+ in 30s |
| **ETH** | $50,000+ | $250,000+ | 5+ in 30s |
| **SOL** | $25,000+ | $100,000+ | 4+ in 30s |
| **Others** | $10,000+ | $50,000+ | 5+ in 30s |

### **OI Explosion Alerts**
| Asset | OI Change | Time Window | Min OI Value |
|-------|-----------|-------------|--------------|
| **BTC** | 15%+ | 15 minutes | $50M+ |
| **ETH** | 18%+ | 15 minutes | $25M+ |
| **SOL** | 25%+ | 15 minutes | $10M+ |
| **Others** | 30%+ | 15 minutes | $5M+ |

---

## 📱 NEW TELEGRAM COMMANDS

### `/alerts` - Alert System Control
Shows current status and available commands.

**Subcommands:**
- `/alerts start` - Start proactive monitoring
- `/alerts stop` - Stop proactive monitoring  
- `/alerts status` - Show detailed monitoring status
- `/alerts recent` - Show recent liquidations/alerts

### `/liquidations` - Recent Liquidations
Shows the 5 most recent large liquidations that were tracked.

---

## 📖 USAGE EXAMPLES

### **Start Monitoring**
```
/alerts start
```
**Response:**
```
🚨 Proactive Alert Monitoring Started

✅ Liquidation cascade detection activated
✅ OI explosion monitoring activated

You'll receive real-time alerts for significant market events!
```

### **Check Status**
```
/alerts
```
**Response:**
```
🚨 Proactive Alert System Status

📉 Liquidation Monitor: ✅ Running
📊 OI Explosion Monitor: ✅ Running

Commands:
• /alerts start - Start proactive monitoring
• /alerts stop - Stop proactive monitoring  
• /alerts status - Show detailed status
• /alerts recent - Show recent alerts

Thresholds:
• BTC: $100k+ liquidations, 15%+ OI changes
• ETH: $50k+ liquidations, 18%+ OI changes
• SOL: $25k+ liquidations, 25%+ OI changes
```

### **View Recent Activity**
```
/liquidations
```
**Response:**
```
📊 Recent Large Liquidations:

📉 BTCUSDT LONG - $125,000 at 14:23:15
📈 ETHUSDT SHORT - $75,000 at 14:20:43
📉 SOLUSDT LONG - $45,000 at 14:18:22
```

---

## 🚨 SAMPLE ALERTS

### **Large Liquidation Alert**
```
🚨 BTC LIQUIDATION

📉 LONG position liquidated
💰 Value: $125,000
📊 Size: 2.5000 @ $50,000.00
🕐 Time: 14:23:15
```

### **Liquidation Cascade Alert**
```
🚨 BTC LIQUIDATION CASCADE

⚡ 7 liquidations in 30 seconds
💰 Total: $1,200,000 liquidated
📊 Breakdown: 5 longs, 2 shorts
⚠️ Potential price impact expected
```

### **OI Explosion Alert**
```
🚨 BTC OI EXPLOSION

📈 +18.5% change in 15 minutes
💰 Total OI: $2,500,000,000
🏦 3/3 exchanges confirming
⚡ Institutional positioning detected
```

---

## ⚙️ SYSTEM FEATURES

### **Memory Optimized**
- Uses only ~18 bytes per liquidation record
- Ring buffer prevents memory bloat
- Automatic cleanup of old data

### **Reliable Connectivity**
- Auto-reconnection to WebSocket streams
- Exponential backoff on failures
- Health monitoring and status reporting

### **Smart Filtering**
- Prevents duplicate alerts
- Rate limiting protects against spam
- Cross-exchange confirmation for OI alerts

### **Real-time Performance**
- <5 second alert delivery
- Continuous 24/7 monitoring
- No impact on existing bot commands

---

## 🔧 CONFIGURATION

The alert system is pre-configured with optimal thresholds, but can be customized via environment variables:

```bash
# Liquidation thresholds (USD)
LIQUIDATION_THRESHOLD_BTC=100000
LIQUIDATION_THRESHOLD_ETH=50000  
LIQUIDATION_THRESHOLD_SOL=25000

# OI change thresholds (%)
OI_THRESHOLD_BTC=15.0
OI_THRESHOLD_ETH=18.0
OI_THRESHOLD_SOL=25.0

# Alert rate limiting
ALERT_RATE_LIMIT_SECONDS=60
```

---

## 🚀 GETTING STARTED

1. **Start the alerts system:**
   ```
   /alerts start
   ```

2. **Test with recent data:**
   ```
   /liquidations
   ```

3. **Monitor real-time:**
   - Alerts will automatically appear in your chat
   - No additional setup required

4. **Check status anytime:**
   ```
   /alerts status
   ```

5. **Stop when needed:**
   ```
   /alerts stop
   ```

---

## 📊 MONITORING DASHBOARD

Use `/alerts status` for detailed monitoring information:

- **Connection status** (WebSocket, API)
- **Memory usage** and performance metrics  
- **Alert counts** and recent activity
- **Threshold configuration** verification

---

## 🔍 TROUBLESHOOTING

### **No Alerts Received**
1. Check monitoring status: `/alerts status`
2. Verify system is running: `/alerts`  
3. Restart if needed: `/alerts stop` then `/alerts start`

### **Too Many Alerts**
- The system has built-in rate limiting
- Max 10 alerts per hour per user
- Duplicate alerts are filtered automatically

### **Missing Market Events**
- System monitors 24/7 when started
- WebSocket reconnects automatically
- Check status to verify connection

---

## 🎯 BEST PRACTICES

1. **Keep monitoring active** during volatile market periods
2. **Check status regularly** to ensure system health
3. **Use `/liquidations`** to review recent market activity
4. **Combine with existing commands** for complete market analysis

---

## 🚨 IMPORTANT NOTES

- **Alerts are informational only** - not trading advice
- **System monitors public liquidation data** from Binance
- **OI data sourced** from your existing market data service
- **No trading functionality** - monitoring only
- **Real-time performance** depends on network connectivity

---

## 📞 SUPPORT

For technical issues or questions about the proactive alert system:

1. **Check status first:** `/alerts status`
2. **Review this guide** for usage instructions
3. **Restart monitoring:** `/alerts stop` then `/alerts start`
4. **Contact support** if issues persist

The proactive alert system enhances your existing crypto assistant with real-time market intelligence while maintaining all current functionality!