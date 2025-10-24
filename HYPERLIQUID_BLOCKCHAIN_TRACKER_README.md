# Hyperliquid Blockchain Liquidation Tracker

## What This Is

A **blockchain-based liquidation monitoring system** that tracks ALL liquidations across ALL users on the Hyperliquid L1 blockchain by parsing on-chain transaction data.

## Key Difference from API Subscription

❌ **NOT**: Subscribing to WebSocket liquidation feeds
✅ **YES**: Querying blockchain data and parsing transactions to identify liquidations

## Architecture

### How Hyperliquid Liquidations Work On-Chain

1. **All liquidations happen on-chain** - Every liquidation is a transaction on Hyperliquid L1
2. **HLP Liquidator contract** executes liquidations at address: `0x2e3d94f0562703b25c83308a05046ddaf9a8dd14`
3. **Liquidations appear as trades** where HLP Liquidator is buyer or seller
4. **Transaction data** includes liquidation details in `extra_fields` JSON

### Detection Method

```python
# Liquidation = Trade where HLP Liquidator is involved

if buyer == "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14":
    # HLP buying = closing short position = SHORT liquidation
    liquidated_user = seller

elif seller == "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14":
    # HLP selling = closing long position = LONG liquidation
    liquidated_user = buyer
```

### Data Sources

#### Option 1: Hyperliquid Info API (Current Implementation)
```
POST https://api.hyperliquid.xyz/info
{
  "type": "recentTrades",
  "coin": "BTC"
}
```
- Returns up to 2000 recent trades
- Poll periodically for new trades
- Filter for liquidations by checking liquidator address

#### Option 2: Blockchain Explorer API
```
POST https://api.hyperliquid.xyz/explorer
{
  "type": "blockDetails",
  "height": 12345
}
```
- Query specific blocks
- Parse transactions for trades
- Identify liquidations

#### Option 3: Allium Blockchain Indexer (Recommended for Production)
```sql
SELECT *
FROM hyperliquid.dex.trades
WHERE BUYER_ADDRESS = '0x2e3d94f0562703b25c83308a05046ddaf9a8dd14'
   OR SELLER_ADDRESS = '0x2e3d94f0562703b25c83308a05046ddaf9a8dd14'
ORDER BY BLOCK_TIMESTAMP DESC
```
- Pre-indexed blockchain data
- SQL queries for liquidations
- Real-time datastreams available
- Requires Allium API key: https://www.allium.so/

#### Option 4: S3 Block Archive (Advanced)
```bash
aws s3 ls s3://hl-mainnet-evm-blocks/ --request-payer requester
```
- Raw blockchain data (MessagePack + LZ4)
- Full historical access
- Build custom indexer
- See: `hyperliquid-python-sdk/examples/evm_block_indexer.py`

## Usage

### Basic Usage

```python
import asyncio
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def main():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # Scan recent liquidations
    liquidations = await tracker.scan_recent_liquidations(coins=["BTC", "ETH", "SOL"])

    print(f"Found {len(liquidations)} liquidations")
    for liq in liquidations[:5]:
        print(f"  {liq.coin} {liq.liquidation_side}: ${liq.value_usd:,.0f}")
        print(f"    User: {liq.liquidated_user}")
        print(f"    Tx: {liq.tx_hash}")

    # Get statistics
    stats = tracker.get_statistics()
    print(f"\nTotal liquidations: {stats['total_liquidations']}")
    print(f"Total value: ${stats['total_value_usd']:,.0f}")
    print(f"Unique users liquidated: {stats['unique_users_liquidated']}")

    await tracker.close()

asyncio.run(main())
```

### Real-Time Monitoring

```python
async def monitor():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # Monitor in real-time
    async for liquidation in tracker.monitor_realtime(coins=["BTC", "ETH"], interval=10):
        print(f"💥 NEW LIQUIDATION:")
        print(f"   Coin: {liquidation.coin}")
        print(f"   Side: {liquidation.liquidation_side}")
        print(f"   Value: ${liquidation.value_usd:,.0f}")
        print(f"   User: {liquidation.liquidated_user}")

        # Send alert, store in database, etc.
        if liquidation.value_usd > 100_000:
            await send_telegram_alert(liquidation)

asyncio.run(monitor())
```

### Integration with Existing Bot

```python
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker
from shared.models.compact_liquidation import CompactLiquidation, LiquidationSide

async def integrate_blockchain_tracker(bot):
    tracker = HyperliquidBlockchainLiquidationTracker()

    async for blockchain_liq in tracker.monitor_realtime(interval=15):
        # Convert to CompactLiquidation format
        compact_liq = CompactLiquidation(
            timestamp=blockchain_liq.timestamp // 1000,
            symbol_hash=hash(f"{blockchain_liq.coin}-PERP") & 0xFFFFFFFF,
            side=LiquidationSide.LONG.value if blockchain_liq.liquidation_side == "LONG" else LiquidationSide.SHORT.value,
            price=int(blockchain_liq.price * 100),
            quantity=int(blockchain_liq.size * 1000000),
            value_usd=int(blockchain_liq.value_usd / 1000)
        )

        # Process through existing liquidation tracker
        alert = await bot.liquidation_tracker.add_liquidation(compact_liq)
        if alert:
            await bot.send_alert(alert)
```

## Data Structure

### BlockchainLiquidation

```python
@dataclass
class BlockchainLiquidation:
    # Transaction info
    tx_hash: str                    # "0x1234..."
    block_height: int               # Block number
    timestamp: int                  # Unix timestamp (ms)

    # Trade info
    coin: str                       # "BTC", "ETH", etc.
    side: str                       # "B" (buy) or "A" (sell)
    price: float                    # Liquidation price
    size: float                     # Position size
    value_usd: float                # USD value

    # User info
    liquidated_user: str            # User address
    liquidator: str                 # HLP_LIQUIDATOR_ADDRESS

    # Optional details
    closed_pnl: Optional[float]     # From extra_fields
    leverage: Optional[float]       # From extra_fields

    @property
    def liquidation_side(self) -> str:
        # "LONG" or "SHORT"
```

### Trade Structure from API

```json
{
  "coin": "BTC",
  "side": "B",
  "px": "45000.5",
  "sz": "0.5",
  "time": 1702000000000,
  "hash": "0x...",
  "tid": 12345678,
  "users": ["0xbuyer...", "0xseller..."]
}
```

### Extra Fields Structure (when available)

```json
{
  "buyer": {
    "closed_pnl": "123.45",
    "liquidation": {...}
  },
  "seller": {
    "closed_pnl": "-456.78",
    "liquidation": {...}
  }
}
```

## API Endpoints Reference

### Info API

**Base URL**: `https://api.hyperliquid.xyz/info`

**Recent Trades**:
```json
{
  "type": "recentTrades",
  "coin": "BTC"
}
```
Returns: Array of up to 2000 recent trades

**User Fills** (requires user address):
```json
{
  "type": "userFills",
  "user": "0x..."
}
```
Returns: User's trade fills with extra_fields

### Explorer API

**Base URL**: `https://api.hyperliquid.xyz/explorer`

**Block Details**:
```json
{
  "type": "blockDetails",
  "height": 12345
}
```
Returns: Block metadata + transactions

**Transaction Details**:
```json
{
  "type": "txDetails",
  "hash": "0x..."
}
```
Returns: Specific transaction details

## Production Recommendations

### For Small Scale (< 1000 liquidations/day)
✅ Use `recentTrades` API polling
✅ Current implementation works
✅ No additional dependencies

### For Medium Scale (1K-10K liquidations/day)
✅ Use Allium indexer with datastreams
✅ SQL queries for analytics
✅ Real-time webhooks available

### For Large Scale (10K+ liquidations/day)
✅ Run own blockchain node
✅ Index from S3 bucket or local node
✅ Custom database schema

## Limitations & Considerations

### API Rate Limits
- Info API: ~100 requests/minute (public endpoint)
- Consider caching and throttling
- Use exponential backoff on errors

### Data Completeness
- `recentTrades` returns ~2000 trades
- May miss liquidations during high volume
- Use block-level indexing for completeness

### Extra Fields Availability
- `recentTrades` may not include `extra_fields`
- Need separate `userFills` query for PnL data
- Allium indexer includes complete data

### Historical Data
- `recentTrades` only returns recent data
- For historical: use Allium or S3 archive
- Block explorer has limited history

## Testing

### Unit Test

```python
async def test_liquidation_detection():
    tracker = HyperliquidBlockchainLiquidationTracker()

    # Mock trade with liquidator as buyer
    trade = {
        "coin": "BTC",
        "side": "B",
        "px": "45000",
        "sz": "1.5",
        "time": 1702000000000,
        "hash": "0xtest",
        "tid": 12345,
        "users": [
            "0x2e3d94f0562703b25c83308a05046ddaf9a8dd14",  # HLP Liquidator (buyer)
            "0xuser123..."  # Liquidated user (seller)
        ]
    }

    is_liq, user = tracker.is_liquidation_trade(trade)
    assert is_liq == True
    assert user == "0xuser123..."

    liq = tracker.parse_liquidation(trade)
    assert liq.liquidation_side == "SHORT"  # HLP buying = short liquidation
    assert liq.value_usd == 67500.0  # 45000 * 1.5
```

### Integration Test

```bash
python3 -c "
import asyncio
from hyperliquid_blockchain_liquidation_tracker import HyperliquidBlockchainLiquidationTracker

async def test():
    tracker = HyperliquidBlockchainLiquidationTracker()
    liquidations = await tracker.scan_recent_liquidations(['BTC'])
    print(f'Found {len(liquidations)} BTC liquidations')
    await tracker.close()

asyncio.run(test())
"
```

## Comparison: Old vs New Implementation

### ❌ Old Implementation (INCORRECT)
- Assumed WebSocket `liquidation` field exists
- Subscribed to public trades stream
- Filtered by non-existent field
- Would never detect any liquidations

### ✅ New Implementation (CORRECT)
- Queries blockchain trade data
- Identifies liquidations by HLP Liquidator address
- Parses actual on-chain transactions
- Tracks ALL users, not individual subscriptions

## Resources

### Official Documentation
- **Hyperliquid API**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **Info Endpoint**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
- **Explorer API**: https://hexdocs.pm/hyperliquid/Hyperliquid.Api.Explorer.html

### Third-Party Indexers
- **Allium**: https://www.allium.so/ | https://hyperliquid.allium.so/liquidations
- **CoinGlass**: https://www.coinglass.com/hyperliquid-liquidation-map
- **Coinalyze**: https://coinalyze.net/hyperliquid/liquidations/

### Block Data
- **S3 Bucket**: `s3://hl-mainnet-evm-blocks/`
- **Python SDK Example**: `hyperliquid-python-sdk/examples/evm_block_indexer.py`
- **RPC Nodes**: https://chainstack.com/hyperliquid-rpc-node/

## Next Steps

1. **Test current implementation** with live API
2. **Verify liquidation detection** logic
3. **Add Allium integration** for production
4. **Implement block-level indexing** for completeness
5. **Add database storage** for historical queries
6. **Create analytics dashboard** for liquidation metrics

---

**Status**: ✅ Blockchain-based implementation
**Last Updated**: 2025-10-24
**Version**: 2.0.0 (Corrected Architecture)
