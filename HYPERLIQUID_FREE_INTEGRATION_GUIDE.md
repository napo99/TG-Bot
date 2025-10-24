# 🚀 Hyperliquid Liquidation Data - FREE Implementation Guide

**Created:** 2025-10-24
**Goal:** Get Hyperliquid liquidation data for FREE using public aggregators and RPC providers

---

## 📊 FREE Options Summary

| Provider | Setup Time | Code Complexity | Real-Time | Historical | Rate Limit |
|----------|-----------|-----------------|-----------|------------|------------|
| **Coinalyze** | 30 min | ⭐ Easy | ✅ Yes | ✅ Yes | 40/min |
| **Hyperliquid Native API** | 1-2 hours | ⭐⭐ Moderate | ✅ Yes | ✅ Yes | 1200 weight/min |
| **Chainstack Free** | 2-4 hours | ⭐⭐⭐ Complex | ✅ Yes | ✅ Yes | 25 RPS (3M/month) |
| **Blockchain Monitor** | 12-20 hours | ⭐⭐⭐⭐ Advanced | ✅ Yes | ✅ Yes | Depends on RPC |

---

## ✅ OPTION 1: Coinalyze API (EASIEST - 30 MINUTES)

### Why Choose This?
- ✅ 100% FREE
- ✅ Simplest integration (10 endpoints)
- ✅ Real-time liquidations
- ✅ 40 requests/min (plenty for most needs)
- ✅ No credit card required

### Step 1: Get API Key (5 minutes)

```bash
# 1. Go to https://coinalyze.net/
# 2. Sign up (free account)
# 3. Go to Account Settings → API Key
# 4. Copy your API key
```

### Step 2: Install Dependencies (2 minutes)

```bash
pip install requests aiohttp python-dotenv
```

### Step 3: Create Implementation (20 minutes)

```python
# coinalyze_liquidations.py

import aiohttp
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Optional

class CoinalyzeLiquidationFeed:
    """
    Free Hyperliquid liquidation feed via Coinalyze API
    Rate Limit: 40 requests/minute (free tier)
    """

    BASE_URL = "https://api.coinalyze.net/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_timestamp = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={
            "Authorization": f"Bearer {self.api_key}"
        })
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def get_liquidations(
        self,
        symbol: str = "HYPERLIQUID:BTCUSDT",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent liquidations for a symbol

        Args:
            symbol: Exchange:Symbol format (e.g., "HYPERLIQUID:BTCUSDT")
            limit: Max number of liquidations to return

        Returns:
            List of liquidation events
        """
        url = f"{self.BASE_URL}/liquidation-history"
        params = {
            "symbols": symbol,
            "limit": limit
        }

        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("history", [])

    async def stream_liquidations(
        self,
        symbols: List[str],
        callback,
        poll_interval: float = 5.0
    ):
        """
        Poll for new liquidations and call callback

        Args:
            symbols: List of symbols to monitor (e.g., ["HYPERLIQUID:BTCUSDT"])
            callback: Async function to call with new liquidations
            poll_interval: Seconds between polls (min 1.5s for 40/min limit)
        """
        print(f"🚀 Starting Coinalyze liquidation monitor for {symbols}")

        while True:
            try:
                for symbol in symbols:
                    # Get recent liquidations
                    liquidations = await self.get_liquidations(symbol, limit=50)

                    # Filter to only new ones
                    new_liquidations = [
                        liq for liq in liquidations
                        if liq.get("timestamp", 0) > self.last_timestamp
                    ]

                    if new_liquidations:
                        # Update last timestamp
                        self.last_timestamp = max(
                            liq["timestamp"] for liq in new_liquidations
                        )

                        # Call callback for each new liquidation
                        for liq in new_liquidations:
                            await callback(liq)

                # Wait before next poll
                await asyncio.sleep(poll_interval)

            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(10)


# Example Usage
async def handle_liquidation(liq: Dict):
    """Process liquidation event"""
    symbol = liq.get("symbol", "")
    side = liq.get("side", "").upper()  # "long" or "short"
    value_usd = liq.get("value", 0)
    price = liq.get("price", 0)
    quantity = liq.get("quantity", 0)
    timestamp = liq.get("timestamp", 0)

    dt = datetime.fromtimestamp(timestamp / 1000)

    print(f"💥 {symbol} {side} Liquidation: ${value_usd:,.0f} | "
          f"{quantity:.4f} @ ${price:,.2f} | {dt.strftime('%H:%M:%S')}")


async def main():
    # Get API key from environment
    api_key = os.getenv("COINALYZE_API_KEY")
    if not api_key:
        print("❌ Set COINALYZE_API_KEY environment variable")
        return

    # Monitor Hyperliquid BTC and ETH
    symbols = [
        "HYPERLIQUID:BTCUSDT",
        "HYPERLIQUID:ETHUSDT"
    ]

    async with CoinalyzeLiquidationFeed(api_key) as feed:
        await feed.stream_liquidations(
            symbols=symbols,
            callback=handle_liquidation,
            poll_interval=2.0  # Poll every 2 seconds
        )


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Run It

```bash
# Set API key
export COINALYZE_API_KEY="your_api_key_here"

# Run
python coinalyze_liquidations.py
```

### Expected Output

```
🚀 Starting Coinalyze liquidation monitor for ['HYPERLIQUID:BTCUSDT', 'HYPERLIQUID:ETHUSDT']
💥 HYPERLIQUID:BTCUSDT SHORT Liquidation: $125,430 | 1.8632 @ $67,234.50 | 14:23:45
💥 HYPERLIQUID:ETHUSDT LONG Liquidation: $89,234 | 28.4521 @ $3,137.20 | 14:23:48
💥 HYPERLIQUID:BTCUSDT LONG Liquidation: $234,567 | 3.4891 @ $67,201.30 | 14:24:12
```

---

## ✅ OPTION 2: Hyperliquid Native API (MODERATE - 2 HOURS)

### Why Choose This?
- ✅ 100% FREE
- ✅ Direct from source (no middleman)
- ✅ Higher rate limits (1200 weight/min)
- ✅ Complete control

### Step 1: Understanding the API

**Endpoint:** `https://api.hyperliquid.xyz/info`

**Key Methods:**
- `allMids` - Get current prices (weight: 2)
- `userFills` - Get user trades/liquidations (weight: 20)
- `userNonFundingLedgerUpdates` - Get liquidation events (weight: 20)

**Rate Limit:** 1200 weight per minute

### Step 2: Implementation

```python
# hyperliquid_native_liquidations.py

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import time

class HyperliquidNativeAPI:
    """
    Direct Hyperliquid API integration for liquidation data
    Rate Limit: 1200 weight/minute
    """

    BASE_URL = "https://api.hyperliquid.xyz"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_weight = 1200  # per minute
        self.weight_used = 0
        self.weight_reset_time = time.time() + 60

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _check_rate_limit(self, weight: int):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()

        # Reset counter if minute has passed
        if current_time >= self.weight_reset_time:
            self.weight_used = 0
            self.weight_reset_time = current_time + 60

        # Wait if we're about to exceed limit
        if self.weight_used + weight > self.rate_limit_weight:
            wait_time = self.weight_reset_time - current_time
            print(f"⏸️  Rate limit reached, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            self.weight_used = 0
            self.weight_reset_time = time.time() + 60

        self.weight_used += weight

    async def _post(self, data: Dict) -> Dict:
        """Make API request"""
        url = f"{self.BASE_URL}/info"

        async with self.session.post(url, json=data) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_user_liquidations(
        self,
        user_address: str,
        start_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Get liquidations for a specific user

        Args:
            user_address: Ethereum address (0x...)
            start_time: Timestamp in milliseconds (optional)

        Returns:
            List of liquidation events
        """
        await self._check_rate_limit(20)  # userNonFundingLedgerUpdates weight

        data = {
            "type": "userNonFundingLedgerUpdates",
            "user": user_address
        }

        if start_time:
            data["startTime"] = start_time

        result = await self._post(data)

        # Filter to only liquidations
        liquidations = [
            event for event in result
            if event.get("delta", {}).get("type") == "liquidation"
        ]

        return liquidations

    async def get_user_fills(
        self,
        user_address: str,
        start_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all fills (trades) for user, including liquidations

        Args:
            user_address: Ethereum address
            start_time: Timestamp in milliseconds

        Returns:
            List of fills
        """
        await self._check_rate_limit(20)  # userFills weight

        data = {
            "type": "userFills",
            "user": user_address
        }

        if start_time:
            data["startTime"] = start_time

        result = await self._post(data)

        # Filter to liquidations only
        liquidations = [
            fill for fill in result
            if fill.get("liquidation", False) is True
        ]

        return liquidations

    async def get_meta(self) -> Dict:
        """Get market metadata"""
        await self._check_rate_limit(2)

        data = {"type": "metaAndAssetCtxs"}
        return await self._post(data)


# Example: Monitor known liquidatable addresses
async def main():
    """
    NOTE: This approach requires knowing user addresses in advance
    For market-wide liquidations, see Option 3 (Blockchain Monitoring)
    """

    # Example addresses (replace with real ones)
    # You can get these from on-chain explorers or WebSocket subscriptions
    monitored_addresses = [
        "0x1234567890abcdef1234567890abcdef12345678",
        # Add more addresses
    ]

    async with HyperliquidNativeAPI() as api:
        print("🚀 Monitoring Hyperliquid for liquidations...")

        # Get metadata
        meta = await api.get_meta()
        print(f"📊 Connected! Block height: {meta.get('blockHeight')}")

        # Poll for liquidations
        while True:
            try:
                for address in monitored_addresses:
                    # Get recent liquidations for this user
                    liquidations = await api.get_user_liquidations(address)

                    for liq in liquidations:
                        print(f"💥 Liquidation: {address[:10]}... | "
                              f"{liq.get('coin')} | ${liq.get('usdc', 0):,.0f}")

                await asyncio.sleep(5)  # Poll every 5 seconds

            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
```

### Limitation of Native API

⚠️ **Important:** The Hyperliquid Native API requires **user addresses** to query liquidations. For **market-wide** liquidations, you need to:

1. **Use Coinalyze** (aggregated data) - EASIEST
2. **Monitor blockchain blocks** (see Option 3) - ADVANCED
3. **Use WebSocket subscriptions** (per-user only)

---

## ✅ OPTION 3: Blockchain Monitoring (ADVANCED - 12-20 HOURS)

### Why Choose This?
- ✅ 100% FREE (with public RPC)
- ✅ Market-wide liquidations (all users)
- ✅ Complete control and transparency
- ⚠️ Requires significant development effort

### Free RPC Providers

| Provider | Monthly Limit | Rate Limit | Setup |
|----------|--------------|------------|-------|
| **Chainstack Developer** | 3M requests (25 RPS) | 25 RPS | Easy |
| **Hyperliquid Public** | Unlimited | ~10 RPS | Very Easy |
| **QuickNode Free Trial** | 10M credits | 15 RPS | Easy |

### Architecture

```
┌─────────────────────────────────────┐
│   Hyperliquid Blockchain (L1)       │
│   Block time: ~1 second             │
└──────────────┬──────────────────────┘
               │
               ↓ Poll every 1s
┌──────────────────────────────────────┐
│   Block Monitor (Python)             │
│   - Get latest block                 │
│   - Parse transactions               │
│   - Filter liquidations              │
└──────────────┬──────────────────────┘
               │
               ↓
┌──────────────────────────────────────┐
│   Your Liquidation Handler           │
│   - Normalize data                   │
│   - Store in database                │
│   - Send to dashboard                │
└──────────────────────────────────────┘
```

### Implementation (Simplified)

```python
# hyperliquid_blockchain_monitor.py

import aiohttp
import asyncio
from typing import Optional, Callable, Dict, List

class HyperliquidBlockchainMonitor:
    """
    Monitor Hyperliquid blockchain for liquidation events
    Uses FREE public RPC or Chainstack free tier
    """

    def __init__(self, rpc_url: str = "https://api.hyperliquid.xyz"):
        self.rpc_url = rpc_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_block = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def get_latest_block_height(self) -> int:
        """Get current block height"""
        url = f"{self.rpc_url}/info"
        data = {"type": "metaAndAssetCtxs"}

        async with self.session.post(url, json=data) as resp:
            resp.raise_for_status()
            result = await resp.json()
            return result.get("blockHeight", 0)

    async def get_block_liquidations(self, block_height: int) -> List[Dict]:
        """
        Get liquidations from a specific block

        NOTE: This is a SIMPLIFIED example. Actual implementation
        requires understanding Hyperliquid transaction structure.
        See HYPERLIQUID_TECHNICAL_IMPLEMENTATION_GUIDE.md for details.
        """
        # This is where you'd parse block data for liquidations
        # Real implementation needs more work (see technical guide)

        # Placeholder - replace with actual block parsing
        liquidations = []

        return liquidations

    async def monitor(self, callback: Callable):
        """
        Monitor blockchain for new blocks and liquidations

        Args:
            callback: Async function to call with liquidations
        """
        print(f"🚀 Starting blockchain monitor...")

        # Get starting block
        self.last_block = await self.get_latest_block_height()
        print(f"📊 Starting from block {self.last_block}")

        while True:
            try:
                # Get latest block
                latest_block = await self.get_latest_block_height()

                # Process new blocks
                if latest_block > self.last_block:
                    for block_num in range(self.last_block + 1, latest_block + 1):
                        # Get liquidations from block
                        liquidations = await self.get_block_liquidations(block_num)

                        # Call callback for each liquidation
                        for liq in liquidations:
                            await callback(liq)

                        self.last_block = block_num

                        if block_num % 100 == 0:
                            print(f"✅ Processed block {block_num}")

                # Wait 1 second (block time)
                await asyncio.sleep(1.0)

            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)


async def handle_liquidation(liq: Dict):
    """Process liquidation event"""
    print(f"💥 Liquidation: {liq}")


async def main():
    """
    ⚠️ WARNING: This is a SKELETON implementation

    Full implementation requires:
    1. Understanding Hyperliquid transaction format (research)
    2. Parsing block data for liquidation events (4-6 hours)
    3. Testing and validation (2-4 hours)

    See HYPERLIQUID_TECHNICAL_IMPLEMENTATION_GUIDE.md for complete guide
    """

    async with HyperliquidBlockchainMonitor() as monitor:
        await monitor.monitor(callback=handle_liquidation)


if __name__ == "__main__":
    print("⚠️  This is a skeleton. See HYPERLIQUID_TECHNICAL_IMPLEMENTATION_GUIDE.md")
    print("⚠️  For production use, start with Option 1 (Coinalyze) instead!")
    # asyncio.run(main())
```

---

## 📊 Comparison & Recommendation

### Which Option Should You Choose?

| Your Situation | Recommended Option | Time Investment | Why |
|----------------|-------------------|-----------------|-----|
| **Quick prototype** | Option 1 (Coinalyze) | 30 min | Easiest, works immediately |
| **Personal project** | Option 1 (Coinalyze) | 30 min | Free + simple = perfect |
| **Need higher rate limits** | Option 2 (Native API) | 2 hours | 1200 weight/min vs 40/min |
| **Need per-user tracking** | Option 2 (Native API) | 2 hours | Built for user queries |
| **Want complete control** | Option 3 (Blockchain) | 12-20 hours | Most flexible, no limits |
| **Building trading bot** | Option 1 + Option 2 | 3 hours | Best of both worlds |

### My Recommendation: Start with Coinalyze

```python
# Quick Start (5 minutes)

import requests

def get_hyperliquid_liquidations():
    """Get Hyperliquid liquidations - SIMPLEST POSSIBLE"""
    url = "https://api.coinalyze.net/v1/liquidation-history"
    headers = {"Authorization": "Bearer YOUR_API_KEY"}
    params = {
        "symbols": "HYPERLIQUID:BTCUSDT",
        "limit": 100
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()

# That's it! You're done!
liquidations = get_hyperliquid_liquidations()
for liq in liquidations.get("history", []):
    print(f"{liq['symbol']}: {liq['side']} ${liq['value']:,.0f}")
```

---

## 🔗 Additional Resources

### Documentation
- Coinalyze API: https://api.coinalyze.net/v1/doc/
- Hyperliquid Docs: https://hyperliquid.gitbook.io/
- Chainstack Guide: https://docs.chainstack.com/

### Your Project Files
- `HYPERLIQUID_LIQUIDATION_DATA_ANALYSIS.md` - Overview & research
- `HYPERLIQUID_TECHNICAL_IMPLEMENTATION_GUIDE.md` - Full blockchain monitoring guide
- `HYPERLIQUID_DATA_PROVIDERS_COMPARISON.md` - All 19 providers analyzed
- `HYPERLIQUID_COST_COMPARISON.md` - Detailed cost analysis

### Next Steps
1. Start with **Option 1 (Coinalyze)** - get it working in 30 minutes
2. If you need more rate limits, add **Option 2 (Native API)**
3. If you need complete control, read the Technical Implementation Guide for **Option 3**

---

## 💡 Pro Tips

1. **Rate Limits:** Respect them to avoid getting blocked
   - Coinalyze: Max 40/min = 1 request every 1.5 seconds
   - Hyperliquid: 1200 weight/min = track your weight usage

2. **Error Handling:** APIs can fail, always retry with backoff
   ```python
   from backoff import on_exception, expo
   import aiohttp

   @on_exception(expo, aiohttp.ClientError, max_tries=3)
   async def fetch_with_retry():
       # Your API call here
       pass
   ```

3. **Testing:** Start with small limits before going production
   ```python
   # Test with 10 requests first
   liquidations = await feed.get_liquidations(symbol, limit=10)
   ```

4. **Monitoring:** Log everything for debugging
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   logger.info(f"Fetched {len(liquidations)} liquidations")
   ```

---

**Ready to start?** Copy Option 1 code and run it in 5 minutes! 🚀
