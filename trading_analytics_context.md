# Browser Automation with Claude Code - Trading Analytics Guide

## CVD Divergence Detection System

### Core Monitoring System (24/7 Automated)

```python
# monitoring_engine.py
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class MarketAlert:
    asset: str
    alert_type: str
    severity: int  # 1-10
    message: str
    data: Dict
    timestamp: datetime
    action_suggested: str

class IntelligentMonitor:
    def __init__(self, telegram_bot):
        self.tg_bot = telegram_bot
        self.oi_history = {}
        self.cvd_history = {}
        
    async def continuous_monitoring(self):
        """Runs 24/7 without manual intervention"""
        while True:
            # Every 30 seconds, check all conditions
            for asset in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
                await self.check_oi_spikes(asset)      # Auto-triggered
                await self.check_cvd_divergence(asset) # Auto-triggered  
                await self.check_momentum_shifts(asset) # Auto-triggered
            
            await asyncio.sleep(30)  # Check every 30 seconds
```

## CVD Calculation Methodology

### How CVD is Calculated

```python
# cvd_calculator.py
class CVDCalculator:
    def __init__(self):
        self.spot_exchanges = ['binance', 'coinbase', 'kraken']
        self.perp_exchanges = ['binance', 'bybit', 'okx']
        self.cvd_data = {}
        
    def calculate_trade_side(self, trade):
        """Determine if trade was a buy or sell based on trade data"""
        # Method 1: Use 'side' if available
        if 'side' in trade:
            return 1 if trade['side'] == 'buy' else -1
            
        # Method 2: Price comparison method (taker direction)
        if 'takerOrMaker' in trade:
            return 1 if trade['takerOrMaker'] == 'taker' else -1
            
        # Method 3: Bid/Ask comparison (most common for real-time)
        if 'price' in trade and 'bid' in trade and 'ask' in trade:
            mid_price = (trade['bid'] + trade['ask']) / 2
            return 1 if trade['price'] >= mid_price else -1
            
        return 0  # Unknown
```

## CVD Divergence Detection

### Pattern Recognition

```python
async def monitor_cvd_divergences(self, asset: str):
    """Detect CVD divergences between spot and futures"""
    spot_cvd = await self.get_spot_cvd(asset)
    futures_cvd = await self.get_futures_cvd(asset)
    
    # Store in history
    timestamp = datetime.now()
    if asset not in self.cvd_history:
        self.cvd_history[asset] = []
        
    self.cvd_history[asset].append({
        'timestamp': timestamp,
        'spot_cvd': spot_cvd,
        'futures_cvd': futures_cvd
    })
    
    # Detect divergences
    alerts = self.detect_cvd_divergences_patterns(asset)
    for alert in alerts:
        await self.send_intelligent_alert(alert)

def detect_cvd_divergences_patterns(self, asset: str) -> List[MarketAlert]:
    """Detect bullish/bearish CVD divergences"""
    alerts = []
    history = self.cvd_history[asset]
    
    if len(history) < 5:  # Need at least 5 data points
        return alerts
        
    # Get recent trend (last 5 minutes)
    recent_data = history[-5:]
    
    spot_trend = self.calculate_trend([d['spot_cvd'] for d in recent_data])
    futures_trend = self.calculate_trend([d['futures_cvd'] for d in recent_data])
    
    # Detect divergences
    if spot_trend > 0.1 and futures_trend < -0.1:  # Spot bullish, futures bearish
        alert = MarketAlert(
            asset=asset,
            alert_type="CVD_DIVERGENCE",
            severity=7,
            message=f"🔄 {asset} CVD DIVERGENCE: Spot BULLISH ({spot_trend:.2f}) vs Futures BEARISH ({futures_trend:.2f})",
            data={'spot_trend': spot_trend, 'futures_trend': futures_trend},
            timestamp=datetime.now(),
            action_suggested="⚡ Possible spot strength - Consider futures long or spot continuation"
        )
        alerts.append(alert)
        
    elif spot_trend < -0.1 and futures_trend > 0.1:  # Spot bearish, futures bullish
        alert = MarketAlert(
            asset=asset,
            alert_type="CVD_DIVERGENCE", 
            severity=7,
            message=f"🔄 {asset} CVD DIVERGENCE: Spot BEARISH ({spot_trend:.2f}) vs Futures BULLISH ({futures_trend:.2f})",
            data={'spot_trend': spot_trend, 'futures_trend': futures_trend},
            timestamp=datetime.now(),
            action_suggested="⚡ Possible futures strength - Consider spot short or futures continuation"
        )
        alerts.append(alert)
    
    return alerts

def calculate_trend(self, values: List[float]) -> float:
    """Calculate trend slope"""
    if len(values) < 2:
        return 0
    x = list(range(len(values)))
    slope = np.polyfit(x, values, 1)[0]
    return slope
```

## Net Long/Short Position Estimation

### Using Funding Rates

```python
# Funding Rate Formula (Simplified)
funding_rate = position_imbalance * multiplier + interest_rate

# Where:
position_imbalance = (net_long_value - net_short_value) / total_open_interest
multiplier = exchange_specific_constant (varies 800-1200)
interest_rate = base_daily_rate (typically 0.01% = 0.0001)

# Reverse Engineering Position Imbalance:
adjusted_funding = funding_rate - interest_rate
position_imbalance = adjusted_funding / multiplier
long_percentage = 50% + (position_imbalance * 50%)
```

### Professional Approach to Position Estimation

```python
professional_approach = {
    'binance_official_ratio': 40,    # Highest weight - official data
    'multi_exchange_funding': 30,    # Cross-exchange funding analysis
    'real_time_order_flow': 20,      # Live buy/sell pressure
    'liquidation_patterns': 10       # Historical positioning clues
}
```

## OI Spike Detection

### Monitoring Open Interest Changes

```python
def analyze_oi_change_significance(self, change: float) -> str:
    """Determine significance of OI change"""
    if abs(change) > 25:
        if change > 0:
            return "🚀 MASSIVE WHALE ACCUMULATION - Monitor for rejection."
        else:
            return "💀 MASSIVE LIQUIDATION EVENT - Look for bounce opportunities."
    elif abs(change) > 15:
        if change > 0:
            return "📈 Heavy positioning - Watch for momentum continuation or reversal."
        else:
            return "📉 Position unwinding - Potential volatility incoming."
    return "Monitor closely"
```

## Real-Time Alert Examples

### Automated Alert Format

```
🚀 AUTOMATED ALERT - BTC/USDT

⚡ MOMENTUM_BURST_30S
🚀 BULLISH MOMENTUM: 2.3% in 30s with 4.2x volume

📊 TIMEFRAME ANALYSIS:
• 30s: Strong bullish momentum burst
• 1m: CVD turning positive  
• 5m: Breaking above resistance

🎯 SUGGESTED ACTION:
⚡ SCALP OPPORTUNITY - Quick momentum trade

📈 FOLLOW-UP ANALYSIS:
• Entry: $43,250 (current)
• Stop: $43,100 (-0.35%)
• Target: $43,500 (+0.58%)
• Risk/Reward: 1:1.65

⏱️ 14:23:47 UTC | Severity: 8/10

[🟢 Quick Long] [📊 Full Analysis] [❌ Ignore]
```

## Architecture Overview

### Docker Container Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  # Existing bot (keep as-is)
  telegram-bot:
    build: .
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
    restart: unless-stopped
    
  # NEW: Market monitoring service
  market-monitor:
    build: ./monitor
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - CHAT_ID=${YOUR_CHAT_ID}
    depends_on:
      - telegram-bot
    restart: unless-stopped
```

## MCP Server for Browser Control

```typescript
// browser-mcp-server.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import puppeteer from 'puppeteer';

const server = new Server(
  {
    name: "browser-automation",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// Tool for taking screenshots
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "take_screenshot",
        description: "Take a screenshot of a webpage",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string" },
            selector: { type: "string", description: "Optional CSS selector" }
          },
          required: ["url"]
        }
      },
      {
        name: "monitor_page",
        description: "Set up periodic monitoring of a page",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string" },
            interval: { type: "number", description: "Minutes between checks" },
            selector: { type: "string" }
          }
        }
      }
    ]
  };
});
```

## Key Monitoring Metrics

### What to Monitor

1. **OI Spikes**: >15% changes in 5-15 minute windows
2. **CVD Divergences**: Spot vs Perps directional conflicts
3. **Funding Rate Extremes**: >0.01% or <-0.01%
4. **Volume Bursts**: 3x+ normal volume in short timeframes
5. **Liquidation Clusters**: Multiple liquidations at same price level

### Alert Thresholds

```python
alert_thresholds = {
    'oi_spike': {
        'critical': 25,  # % change
        'high': 15,
        'moderate': 10
    },
    'cvd_divergence': {
        '1m': {'strong': 0.5, 'moderate': 0.3},
        '5m': {'strong': 0.4, 'moderate': 0.2}, 
        '15m': {'strong': 0.3, 'moderate': 0.15}
    },
    'funding_rate': {
        'extreme_long': 0.01,   # Longs overpaying
        'extreme_short': -0.01  # Shorts overpaying
    }
}
```

## Summary

This system provides:
- **24/7 Automated Monitoring** - No manual commands needed
- **Multi-Timeframe Analysis** - 30s to daily timeframes
- **Intelligent Alerts** - Context-aware notifications with action suggestions
- **CVD Divergence Detection** - Spot vs futures flow analysis
- **Position Estimation** - Net long/short calculations from funding rates
- **Real-time Execution** - Sub-minute reaction times

The architecture extends your existing TG bot with a monitoring service that runs continuously and sends proactive alerts when market conditions warrant attention.