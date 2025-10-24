# 🏗️ Build Your Own Hyperliquid Liquidation Aggregator

**Goal:** Query Hyperliquid blockchain directly to get ALL market liquidations (like CoinGlass does)

**Total Effort:** 16-24 hours (2-3 days full-time)

---

## 📊 How CoinGlass/Coinalyze Does It

```
Hyperliquid Blockchain (Layer 1)
   ↓ Every 1 second (new block)
   ↓
Block Monitor Service
   ↓ Parse transactions
   ↓
Liquidation Detector
   ↓ Filter liquidation events
   ↓
Database (store all liquidations)
   ↓
API Server (serve aggregated data)
```

---

## 📋 Implementation Breakdown

### **Phase 1: Research & Setup (3-4 hours)**

**What you need to learn:**

1. **Hyperliquid Transaction Structure** (2 hours)
   - How are liquidations recorded on-chain?
   - What does a liquidation transaction look like?
   - Where in the block data are liquidations?

2. **Test API Access** (1 hour)
   - Test Hyperliquid RPC endpoints
   - Understand rate limits
   - Choose RPC provider (free or paid)

3. **Sample Data Collection** (1 hour)
   - Find known liquidation transactions
   - Inspect their structure
   - Document the data format

**Tasks:**
```bash
# 1. Read Hyperliquid docs
https://hyperliquid.gitbook.io/hyperliquid-docs/

# 2. Test block queries
curl -X POST https://api.hyperliquid.xyz/info \
  -d '{"type": "metaAndAssetCtxs"}'

# 3. Find liquidator address (0x2e3d94f0562703b25c83308a05046ddaf9a8dd14)
# Query its events to see liquidation format

# 4. Inspect blockchain explorer
https://app.hyperliquid.xyz/explorer
```

**Deliverable:** Document with transaction format and liquidation detection logic

---

### **Phase 2: Block Monitor Service (4-6 hours)**

**What to build:**

A service that polls Hyperliquid blockchain every 1 second for new blocks.

**Code Structure:**
```python
# block_monitor.py

import asyncio
import aiohttp
from typing import Callable, Optional

class HyperliquidBlockMonitor:
    """
    Polls Hyperliquid blockchain for new blocks
    Calls callback with each new block's data
    """

    def __init__(self, rpc_url: str, callback: Callable):
        self.rpc_url = rpc_url
        self.callback = callback
        self.last_block = 0
        self.running = False

    async def get_latest_block_height(self) -> int:
        """Get current block height"""
        # POST to info endpoint
        # Return blockHeight from response
        pass

    async def get_block_data(self, block_height: int) -> dict:
        """Get all data for a specific block"""
        # Query block fills/events
        # Return raw block data
        pass

    async def monitor_loop(self):
        """Main loop - poll every 1 second"""
        while self.running:
            try:
                # Get latest block
                latest = await self.get_latest_block_height()

                # Process new blocks
                if latest > self.last_block:
                    for block_num in range(self.last_block + 1, latest + 1):
                        block_data = await self.get_block_data(block_num)
                        await self.callback(block_num, block_data)
                        self.last_block = block_num

                # Wait 1 second
                await asyncio.sleep(1.0)

            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

    async def start(self):
        """Start monitoring"""
        self.running = True
        # Get starting block
        self.last_block = await self.get_latest_block_height()
        await self.monitor_loop()
```

**Challenges:**
- Rate limiting (10 req/sec on free tier)
- Error handling and retries
- Tracking which block was last processed
- Handling blockchain reorganizations (rare)

**Testing:**
```python
async def test_callback(block_num, block_data):
    print(f"Block {block_num}: {len(block_data)} events")

monitor = HyperliquidBlockMonitor(
    rpc_url="https://api.hyperliquid.xyz",
    callback=test_callback
)

await monitor.start()
```

**Deliverable:** Working block monitor that processes all new blocks

---

### **Phase 3: Liquidation Detector (4-6 hours)**

**What to build:**

Parse block data and extract liquidation events.

**Research Needed:**
1. **How are liquidations marked?**
   - Is there a `liquidation: true` flag?
   - Is there a specific transaction type?
   - Is it in event logs?

2. **What data is included?**
   - User address
   - Asset (BTC, ETH, etc.)
   - Side (long/short)
   - Price
   - Quantity
   - Timestamp

**Code Structure:**
```python
# liquidation_detector.py

from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Liquidation:
    """Parsed liquidation event"""
    timestamp_ms: int
    user: str
    asset: str
    side: str  # 'long' or 'short'
    price: float
    quantity: float
    value_usd: float
    block_height: int
    tx_hash: str

class LiquidationDetector:
    """
    Parses Hyperliquid block data to extract liquidations
    """

    def detect_liquidations(self, block_data: Dict) -> List[Liquidation]:
        """
        Parse block data and extract liquidation events

        Args:
            block_data: Raw block data from Hyperliquid

        Returns:
            List of detected liquidations
        """
        liquidations = []

        # METHOD 1: Check user fills for liquidation flag
        # Example structure (needs research):
        # {
        #   "fills": [
        #     {
        #       "user": "0x...",
        #       "coin": "BTC",
        #       "px": "67234.5",
        #       "sz": "2.5",
        #       "side": "B" or "A",
        #       "liquidation": true,  # <-- KEY FLAG
        #       "time": 1729800000000
        #     }
        #   ]
        # }

        fills = block_data.get("fills", [])

        for fill in fills:
            # Check if this is a liquidation
            if self._is_liquidation(fill):
                liq = self._parse_liquidation(fill)
                if liq:
                    liquidations.append(liq)

        return liquidations

    def _is_liquidation(self, fill: Dict) -> bool:
        """
        Determine if a fill is a liquidation

        Possible methods:
        1. Check for "liquidation": true flag
        2. Check transaction type
        3. Check if liquidator address is involved
        4. Check event logs for liquidation marker
        """
        # Method 1: Direct flag (most reliable if exists)
        if fill.get("liquidation") is True:
            return True

        # Method 2: Check if liquidator contract involved
        LIQUIDATOR_ADDRESS = "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"
        if fill.get("liquidator") == LIQUIDATOR_ADDRESS:
            return True

        # Method 3: Check transaction type
        if fill.get("type") == "liquidation":
            return True

        return False

    def _parse_liquidation(self, fill: Dict) -> Optional[Liquidation]:
        """
        Extract liquidation details from fill

        Needs research to understand exact structure
        """
        try:
            user = fill.get("user")
            coin = fill.get("coin")
            price = float(fill.get("px", 0))
            quantity = float(fill.get("sz", 0))
            timestamp = int(fill.get("time", 0))

            # Determine side
            # "B" = Buy (liquidated short) = SHORT liquidation
            # "A" = Ask/Sell (liquidated long) = LONG liquidation
            side_char = fill.get("side")
            if side_char == "B":
                side = "short"
            elif side_char == "A":
                side = "long"
            else:
                return None

            return Liquidation(
                timestamp_ms=timestamp,
                user=user,
                asset=coin,
                side=side,
                price=price,
                quantity=quantity,
                value_usd=price * quantity,
                block_height=fill.get("blockHeight", 0),
                tx_hash=fill.get("hash", "")
            )

        except (ValueError, KeyError) as e:
            print(f"Failed to parse liquidation: {e}")
            return None
```

**Research Tasks:**
1. Query liquidator address events:
   ```python
   POST https://api.hyperliquid.xyz/info
   {"type": "userFills", "user": "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14"}
   ```

2. Inspect returned data structure

3. Find liquidation markers/flags

4. Test with known liquidation events

**Deliverable:** Working liquidation detector with test cases

---

### **Phase 4: Data Storage (2-3 hours)**

**What to build:**

Store liquidations in a database for querying.

**Database Schema:**
```sql
CREATE TABLE hyperliquid_liquidations (
    id SERIAL PRIMARY KEY,
    timestamp_ms BIGINT NOT NULL,
    block_height BIGINT NOT NULL,
    tx_hash VARCHAR(66) NOT NULL,
    user_address VARCHAR(42) NOT NULL,
    asset VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    value_usd DECIMAL(20, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_timestamp (timestamp_ms),
    INDEX idx_asset (asset),
    INDEX idx_user (user_address)
);
```

**Code:**
```python
# storage.py

import asyncpg
from typing import List

class LiquidationStorage:
    """Store liquidations in PostgreSQL"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None

    async def connect(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(self.db_url)

    async def save_liquidations(self, liquidations: List[Liquidation]):
        """Batch insert liquidations"""
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO hyperliquid_liquidations
                (timestamp_ms, block_height, tx_hash, user_address,
                 asset, side, price, quantity, value_usd)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (tx_hash) DO NOTHING
                """,
                [
                    (
                        liq.timestamp_ms, liq.block_height, liq.tx_hash,
                        liq.user, liq.asset, liq.side,
                        liq.price, liq.quantity, liq.value_usd
                    )
                    for liq in liquidations
                ]
            )

    async def get_recent_liquidations(
        self, asset: str, limit: int = 100
    ) -> List[Dict]:
        """Query recent liquidations"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM hyperliquid_liquidations
                WHERE asset = $1
                ORDER BY timestamp_ms DESC
                LIMIT $2
                """,
                asset, limit
            )
            return [dict(row) for row in rows]
```

**Deliverable:** Database schema and storage layer

---

### **Phase 5: Integration & Testing (3-4 hours)**

**What to build:**

Connect all components together.

**Main Application:**
```python
# main.py

import asyncio
from block_monitor import HyperliquidBlockMonitor
from liquidation_detector import LiquidationDetector
from storage import LiquidationStorage

class HyperliquidLiquidationAggregator:
    """
    Complete liquidation aggregator system
    """

    def __init__(self, rpc_url: str, db_url: str):
        self.detector = LiquidationDetector()
        self.storage = LiquidationStorage(db_url)
        self.monitor = HyperliquidBlockMonitor(
            rpc_url=rpc_url,
            callback=self.on_new_block
        )

    async def on_new_block(self, block_num: int, block_data: dict):
        """
        Called for each new block
        1. Detect liquidations
        2. Save to database
        3. Log statistics
        """
        try:
            # Detect liquidations in this block
            liquidations = self.detector.detect_liquidations(block_data)

            if liquidations:
                # Save to database
                await self.storage.save_liquidations(liquidations)

                # Log
                total_value = sum(liq.value_usd for liq in liquidations)
                print(f"Block {block_num}: {len(liquidations)} liquidations, "
                      f"${total_value:,.0f} total")

                for liq in liquidations:
                    print(f"  💥 {liq.asset} {liq.side.upper()} ${liq.value_usd:,.0f}")

        except Exception as e:
            print(f"Error processing block {block_num}: {e}")

    async def start(self):
        """Start the aggregator"""
        # Connect to database
        await self.storage.connect()

        # Start monitoring blockchain
        print("🚀 Starting Hyperliquid Liquidation Aggregator...")
        await self.monitor.start()


async def main():
    aggregator = HyperliquidLiquidationAggregator(
        rpc_url="https://api.hyperliquid.xyz",
        db_url="postgresql://user:pass@localhost/hyperliquid"
    )

    await aggregator.start()


if __name__ == "__main__":
    asyncio.run(main())
```

**Testing Tasks:**
1. Run for 1 hour and verify liquidations are captured
2. Compare with CoinGlass data for accuracy
3. Test error handling (network issues, rate limits)
4. Verify no duplicate liquidations
5. Check database performance

**Deliverable:** Working end-to-end system

---

### **Phase 6: API Server (Optional, 2-3 hours)**

**What to build:**

REST API to query your aggregated data.

```python
# api_server.py

from fastapi import FastAPI
from typing import List, Optional

app = FastAPI()

@app.get("/api/liquidations/{asset}")
async def get_liquidations(
    asset: str,
    limit: int = 100,
    start_time: Optional[int] = None
):
    """
    Get liquidations for an asset

    Example: /api/liquidations/BTC?limit=50
    """
    liquidations = await storage.get_recent_liquidations(asset, limit)
    return {"data": liquidations, "count": len(liquidations)}

@app.get("/api/liquidations/summary")
async def get_summary():
    """Get 24h liquidation summary"""
    # Query database for last 24h stats
    return {
        "total_liquidations": 1234,
        "total_value_usd": 12345678,
        "by_asset": {...},
        "long_short_ratio": 0.6
    }
```

**Deliverable:** REST API for querying liquidations

---

## 🎯 Total Effort Breakdown

| Phase | Tasks | Time | Difficulty |
|-------|-------|------|------------|
| **1. Research** | Understand blockchain structure | 3-4h | ⭐⭐⭐ |
| **2. Block Monitor** | Poll blockchain for new blocks | 4-6h | ⭐⭐ |
| **3. Liquidation Detector** | Parse and extract liquidations | 4-6h | ⭐⭐⭐⭐ |
| **4. Storage** | Database schema and queries | 2-3h | ⭐⭐ |
| **5. Integration** | Connect all components | 3-4h | ⭐⭐⭐ |
| **6. API (Optional)** | REST API server | 2-3h | ⭐⭐ |
| **TOTAL** | | **18-26 hours** | |

**Conservative Estimate:** 20-24 hours (3 days full-time)
**Aggressive Estimate:** 16-18 hours (2 days full-time)

---

## 🚧 Key Challenges

### 1. **Understanding Transaction Format** ⚠️ HARDEST
- Hyperliquid's blockchain structure is not fully documented
- Need to reverse-engineer liquidation detection
- Requires inspecting real liquidation events

### 2. **Rate Limits**
- Free RPC: ~10 requests/second
- Polling every 1 second = manageable
- But querying block data adds overhead

### 3. **Blockchain Reorganizations**
- Rare, but blocks can be reorganized
- Need to handle re-processing blocks

### 4. **Ongoing Maintenance**
- Blockchain structure may change
- API endpoints may update
- Need monitoring and alerting

---

## 💰 Infrastructure Costs

### Option A: Free Tier
- **RPC:** Hyperliquid public (free, rate limited)
- **Database:** PostgreSQL on Railway (free tier)
- **Server:** Your local machine or free Heroku dyno
- **Total:** $0/month

### Option B: Production Grade
- **RPC:** Chainstack Growth ($49/month)
- **Database:** Railway Pro ($5-20/month)
- **Server:** DigitalOcean droplet ($6/month)
- **Monitoring:** Sentry (free tier)
- **Total:** $60-75/month

---

## 📊 Performance Expectations

### With Free Infrastructure:
- **Blocks processed:** ~86,400/day (1 per second)
- **Latency:** 2-3 seconds behind blockchain
- **Liquidations captured:** 10-50/day (typical)
- **Database size:** ~1MB/day

### With Paid Infrastructure:
- **Blocks processed:** ~86,400/day
- **Latency:** <1 second behind blockchain
- **99.9% uptime**
- **Historical backfill possible**

---

## 🎯 Is It Worth It?

### ✅ Build It If:
- You want complete control over data
- You need custom features CoinGlass doesn't offer
- You're building a commercial product
- You enjoy the technical challenge
- You need unlimited API access

### ❌ Use Coinalyze If:
- You just need liquidation data
- 40 requests/min is enough
- You want to start in 5 minutes
- You don't want maintenance burden
- You value time over cost

---

## 📚 Resources You Need

1. **Hyperliquid Docs:** https://hyperliquid.gitbook.io/
2. **Blockchain Explorer:** https://app.hyperliquid.xyz/explorer
3. **Liquidator Address:** 0x2e3d94f0562703b25c83308a05046ddaf9a8dd14
4. **Your Existing Docs:**
   - `HYPERLIQUID_TECHNICAL_IMPLEMENTATION_GUIDE.md`
   - `HYPERLIQUID_DATA_PROVIDERS_COMPARISON.md`

---

## 🚀 Quick Start Path

If you decide to build it:

```bash
# Day 1: Research (4 hours)
1. Read Hyperliquid docs
2. Query liquidator address to see events
3. Document transaction structure
4. Write liquidation detection logic

# Day 2: Build Core (8 hours)
1. Implement block monitor
2. Implement liquidation detector
3. Test with real blockchain data
4. Fix bugs in detection logic

# Day 3: Complete System (8 hours)
1. Add database storage
2. Integrate all components
3. Run for 24 hours to validate
4. Compare with CoinGlass for accuracy
```

---

## 💡 My Recommendation

**Start with Coinalyze API** ($0, 5 minutes) while you:
1. Research Hyperliquid blockchain structure (Phase 1)
2. Build a proof-of-concept detector (Phase 3)
3. Validate it matches CoinGlass/Coinalyze data

**Then decide:**
- If POC works well → Build full system (20-24 hours)
- If POC is hard → Stick with Coinalyze

**Best of both worlds:**
- Use Coinalyze in production NOW
- Build your own as a side project
- Switch when it's production-ready

---

**Ready to start? Begin with Phase 1 research!** 🚀
