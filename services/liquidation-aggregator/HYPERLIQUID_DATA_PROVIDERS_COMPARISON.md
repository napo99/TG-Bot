# Hyperliquid Liquidation Data Providers - Comprehensive Comparison (2025)

## Executive Summary

This document provides a detailed comparison of all available service providers offering Hyperliquid liquidation data access, including pricing tiers, API rate limits, features, and recommendations.

---

## Table of Contents
1. [Data Aggregators & Analytics Platforms](#data-aggregators--analytics-platforms)
2. [Blockchain Data Providers (RPC Nodes)](#blockchain-data-providers-rpc-nodes)
3. [Blockchain Analytics & On-Chain Data](#blockchain-analytics--on-chain-data)
4. [Native Hyperliquid API](#native-hyperliquid-api)
5. [Comparison Table](#comparison-table)
6. [Recommendations](#recommendations)

---

## Data Aggregators & Analytics Platforms

### 1. CoinGlass
**Official Site:** https://www.coinglass.com/pricing
**API Documentation:** https://docs.coinglass.com/

#### Pricing Tiers

| Tier | Monthly | Annual | Rate Limit | Endpoints | Updates | Use Case |
|------|---------|--------|------------|-----------|---------|----------|
| **Hobbyist** | $29 | $348 (save $72) | 30/min | 70+ | ≤1 min | Personal |
| **Startup** | $79 | $948 (save $192) | 80/min | 80+ | ≤1 min | Personal |
| **Standard** | $299 | $3,588 (save $960) | 300/min | 90+ | ≤1 min | Commercial |
| **Professional** | $699 | $8,388 (save $2,160) | 1,200/min | 100+ | ≤1 min | Commercial |
| **Enterprise** | Custom | Custom | 6,000/min | 100+ | ≤1 min | Commercial |

#### Features
- **Hyperliquid Support:** YES - Full coverage
- **Liquidation Data:**
  - Historical liquidation data (long/short)
  - Real-time liquidation map
  - Liquidation heatmap (1 second updates)
  - Liquidation orders (past 7 days)
  - Whale liquidation tracking
- **Additional Data:** Open interest, funding rates, futures metrics
- **Support:** Priority email (Standard+), Priority chat (Professional+)

#### Pros
- Comprehensive liquidation coverage
- Multiple liquidation-specific endpoints
- Real-time updates (1 second frequency)
- Whale tracking included
- Clear pricing structure

#### Cons
- Higher cost for commercial use
- Rate limits may be restrictive for high-frequency applications

---

### 2. Coinalyze
**Official Site:** https://coinalyze.net/
**API Documentation:** https://api.coinalyze.net/v1/doc/

#### Pricing Tiers

| Tier | Monthly | Rate Limit | Endpoints | Features |
|------|---------|------------|-----------|----------|
| **Free** | $0 | 40/min | 10 | Full access |

#### Features
- **Hyperliquid Support:** YES - Full coverage
- **Liquidation Data:**
  - Aggregated liquidations (HYPE/USD, HYPE/USDT, HYPE/BUSD)
  - Historical liquidation data
  - Combines coin-margined and stablecoin-margined contracts
- **Additional Data:** Open interest, funding rates, long/short ratios
- **Authentication:** Free API key from account settings

#### Pros
- Completely FREE
- Simple API with 10 endpoints
- Aggregated cross-contract liquidation data
- No credit card required
- Easy to get started

#### Cons
- Lower rate limit (40/min)
- Limited to 10 endpoints
- No premium support
- May have data latency vs paid services

---

### 3. CoinAnk
**Official Site:** https://coinank.com/hyperliquid
**API Documentation:** https://coinank.com/openApi

#### Pricing
- **Pricing Structure:** Freemium with VIP tiers (specific pricing not publicly listed)
- **API Access:** Available through API endpoint

#### Features
- **Hyperliquid Support:** YES
- **Liquidation Data:**
  - Real-time liquidation tracking
  - Liquidation heatmap
  - Liquidation map (visualizes liquidation clusters)
  - 24-hour liquidation data
- **Whale Tracking:** Real-time large trader monitoring
- **Additional Data:** Funding rates, long/short ratios, open interest, order book analysis

#### Pros
- Real-time whale tracking
- Liquidation visualization tools
- Order book data included

#### Cons
- Pricing not transparent
- Must contact for VIP/API pricing details

---

### 4. Gate.com
**Official Site:** https://www.gate.com/crypto-market-data/funds/liquidation-data/hype
**API Documentation:** https://www.gate.com/docs/developers/apiv4/

#### Pricing
- **Free API Access:** YES
- **Public API Endpoint:** `/futures/{settle}/liq_orders`

#### Features
- **Hyperliquid Support:** YES
- **Liquidation Data:**
  - Liquidated orders query
  - Total value of liquidated positions
  - Long/short position tracking
  - Real-time liquidation heatmap
- **Additional Data:** Candlestick data, order book depth, funding rates
- **WebSocket:** Real-time market quotes and perpetual futures transactions

#### Pros
- Free access
- Real-time WebSocket support
- Comprehensive market data
- Well-documented API

#### Cons
- Limited to Gate.com's data aggregation
- May not have complete historical depth

---

## Blockchain Data Providers (RPC Nodes)

### 5. QuickNode
**Official Site:** https://www.quicknode.com/chains/hyperliquid
**Documentation:** https://www.quicknode.com/docs/hyperliquid

#### Pricing Tiers

| Tier | Monthly | Annual | API Credits | Rate Limit | Overage Cost | SLA |
|------|---------|--------|-------------|------------|--------------|-----|
| **Free Trial** | $0 | N/A | 10M | 15 RPS | N/A | Community |
| **Build** | $49 | $42/mo | 80M | 50 RPS | $0.62/1M | 24hr |
| **Accelerate** | $249 | $212/mo | 450M | 125 RPS | $0.55/1M | 12hr |
| **Scale** | $499 | $424/mo | 950M | 250 RPS | $0.53/1M | 8hr |
| **Business** | $999 | $849/mo | 2B | 500 RPS | $0.50/1M | 8hr |
| **Enterprise** | Custom | Custom | Custom | 100K RPS | Custom | Custom |

#### Features
- **Hyperliquid Support:** YES - Mainnet access
- **Node Type:** Managed endpoints
- **Additional Features:**
  - Streams & WebHooks
  - IPFS support
  - Trace & Debug tools
  - Advanced metrics (Accelerate+)
  - S3/PostgreSQL/Snowflake (Scale+)
- **Multi-chain:** Access to entire QuickNode stack

#### Pros
- Reliable infrastructure (99.99% uptime)
- Credit-based system (predictable costs)
- Fast response times
- Comprehensive developer tools
- Multi-chain support

#### Cons
- Not liquidation-specific (RPC access only)
- Need to build liquidation tracking yourself
- Can be expensive for high-volume usage

---

### 6. Chainstack
**Official Site:** https://chainstack.com/build-better-with-hyperliquid/
**Documentation:** https://docs.chainstack.com/

#### Pricing Tiers

| Tier | Monthly | Requests/Month | Rate Limit | Overage Cost |
|------|---------|----------------|------------|--------------|
| **Developer** | $0 | 3M (~25 RPS) | 25 RPS | $20/1M |
| **Growth** | $49 | 20M (~250 RPS) | 250 RPS | $15/1M |
| **Pro** | $199 | 80M (~400 RPS) | 400 RPS | $12.50/1M |

#### Features
- **Hyperliquid Support:** YES - Mainnet & Testnet
- **Node Types:** Full and Archive nodes
- **WebSockets:** Available on mainnet (real-time data)
- **Archive Nodes:** Full historical state queries
- **Private Endpoints:** Available on all paid plans
- **Dedicated Nodes:** Starting at $0.50/hour (requires Pro plan)

#### Pros
- Free tier available (3M requests)
- Transparent pricing (all requests billed equally)
- Archive node support
- WebSocket support for real-time data
- Lower cost than QuickNode for similar volume

#### Cons
- Not liquidation-specific
- Need to query blockchain directly for liquidation events
- Lower rate limits on free tier vs public endpoint

---

### 7. HypeRPC
**Official Site:** https://hyperpc.app/
**Documentation:** https://hyperpc.app/blog/rpc-nodes-hyperliquid-guide

#### Pricing
- **Dedicated Nodes:** Custom pricing
- **Contact:** Required for quote

#### Features
- **Hyperliquid Support:** YES - Dedicated to Hyperliquid only
- **Infrastructure:**
  - Lightning-fast, reliable RPC endpoints
  - Dedicated nodes for dApps, trading bots, HFT strategies
  - Regional nodes (Europe, Japan)
  - 99.99% uptime
  - Very low latency
- **Optimized:** Specifically for Hyperliquid EVM layer

#### Pros
- Hyperliquid-specific optimization
- Very low latency
- High reliability
- No hard caps on dedicated nodes

#### Cons
- No public pricing
- Higher cost than general providers
- Need to contact for quote
- Not liquidation-specific

---

### 8. Imperator
**Official Site:** https://www.imperator.co/products/hyperliquid-rpc-nodes

#### Pricing
- **Custom Pricing:** Contact for quote

#### Features
- **Hyperliquid Support:** YES
- **Infrastructure:**
  - Institutional-grade dedicated RPC infrastructure
  - Shared nodes: 99.9% uptime
  - Dedicated nodes: 99.99% uptime SLA
  - Geo-distributed nodes (customizable location)
  - Fully customizable hardware and software stacks
- **Support:** 24/7 expert support

#### Pros
- Institutional-grade infrastructure
- High uptime SLAs
- Geographic flexibility
- Customizable configurations
- 40+ blockchain support

#### Cons
- Custom pricing only
- Expensive (institutional-focused)
- Not liquidation-specific

---

### 9. dRPC
**Official Site:** https://drpc.org/chainlist/hyperliquid-mainnet-rpc

#### Pricing Tiers

| Tier | Monthly | Features |
|------|---------|----------|
| **Free** | $0 | Basic HTTPS endpoints |
| **Growth Plan** | From $10 | Premium RPC endpoints, AI-powered load balancing |

#### Features
- **Hyperliquid Support:** YES - HyperEVM
- **Endpoint:** https://hyperliquid.drpc.org
- **Infrastructure:** Multi-chain RPC platform with NodeCloud

#### Pros
- Low cost entry point ($10)
- Free tier available
- AI-powered load balancing
- Multi-chain platform

#### Cons
- Limited information on rate limits
- Not Hyperliquid-specific
- Not liquidation-specific

---

## Blockchain Analytics & On-Chain Data

### 10. Glassnode
**Official Site:** https://studio.glassnode.com/pricing
**Documentation:** https://docs.glassnode.com/

#### Pricing Tiers

| Tier | Monthly | Annual | API Calls | Historical Data | Features |
|------|---------|--------|-----------|-----------------|----------|
| **Free** | $0 | N/A | 1K/month | Tier 1 metrics only | 24hr resolution, Basic metrics |
| **Advanced** | $29+ | From $26.10/mo | Limited | 30 days (many metrics) | 1hr resolution, Essential metrics |
| **Professional** | $799 | Billed annually | High volume | Full history | All metrics, High resolution |

#### Features
- **Hyperliquid Support:** YES - 16% of global OI share tracked
- **Liquidation Data:**
  - Liquidation heatmaps (position-level granularity)
  - Liquidation risk mapping
  - Directional bias analysis
  - Leverages Hyperliquid's on-chain transparency
- **Additional Data:** On-chain metrics, derivatives data, market intelligence

#### Pros
- Unique position-level liquidation data
- High-quality analytics
- Comprehensive on-chain metrics
- Professional-grade tools

#### Cons
- Expensive Professional tier ($799/mo)
- Advanced plan limited to 30-day history for many metrics
- Not real-time (focus on analytics vs live data)

---

### 11. Nansen
**Official Site:** https://www.nansen.ai/
**API Documentation:** https://docs.nansen.ai/

#### Pricing Tiers

**Platform Plans:**

| Tier | Monthly | Features |
|------|---------|----------|
| **Free** | $0 | Essential tools, limited analytics |
| **Pioneer** | $99 | Nansen Labels (300M+ addresses), Smart Money tracking |
| **Professional** | $999 | Full features, CSV downloads, dedicated CSM |
| **Enterprise** | Custom | Bespoke, real-time APIs, integrations |

**API Plans:**

| Tier | Monthly | Annual | Initial Credits | Cost per Credit |
|------|---------|--------|-----------------|-----------------|
| **Free** | $0 | N/A | 100 (non-renewing) | N/A |
| **Pro API** | $69 | $49/mo | 1,000 | $0.001 |

#### Features
- **Hyperliquid Support:** YES (via multi-chain coverage)
- **Liquidation Data:**
  - On-chain alerts for liquidation risk
  - Lending protocol liquidation monitoring
  - Smart Money tracking (liquidation positions)
- **Coverage:**
  - 400M+ labeled addresses
  - 1,000+ entities
  - 500TB+ daily data
  - 15+ chains (Ethereum, Solana, Arbitrum, Bitcoin, Polygon, etc.)

#### Pros
- Comprehensive address labeling
- Smart Money insights
- Multi-chain support
- Flexible credit system
- AI agent integration (MCP)

#### Cons
- Expensive platform tiers ($999/mo for full access)
- Credit-based API (usage can add up)
- Not Hyperliquid-specific
- Limited free tier

---

### 12. Santiment
**Official Site:** https://app.santiment.net/pricing
**API Documentation:** https://academy.santiment.net/sanapi/

#### Pricing Tiers

| Tier | Monthly | Annual | API Calls | Historical Data | Alerts |
|------|---------|--------|-----------|-----------------|--------|
| **Free** | $0 | N/A | 1K/month | 1 year | 3 |
| **Sanbase Pro** | $49 | $529/yr (10% off) | 5K/month | 1 year | 20 |
| **Sanbase Max** | $249 | $2,700/yr (10% off) | 80K/month | 2 years | 50 |
| **Business Pro** | $42 | $478.80/yr | Limited | Varies | Varies |
| **Business Max** | $99.90 | $1,138.80/yr | Limited | Varies | Varies |

#### Features
- **Hyperliquid Support:** UNKNOWN - Not confirmed in documentation
- **Data Coverage:** 2000+ crypto assets
- **Data Types:** On-chain, social, developer activity, pricing
- **Additional:** Google Sheets plugin, screeners, trending tokens

#### Pros
- Affordable Pro tier ($49/mo)
- Social data integration
- Developer activity metrics
- 20% discount for SAN token holders

#### Cons
- Hyperliquid support not confirmed
- Limited API calls on lower tiers
- Not liquidation-specific
- 30-day lag on free tier

---

### 13. Allium
**Official Site:** https://www.allium.so/
**Documentation:** https://docs.allium.so/historical-data/supported-blockchains/hyperliquid/

#### Pricing
- **Contact for Pricing:** Not publicly listed

#### Features
- **Hyperliquid Support:** YES
- **Liquidation Data:**
  - Query liquidations via HLP Liquidator address (0x2e3d94f0562703b25c83308a05046ddaf9a8dd14)
  - DEX trades data with liquidation flags
  - Extra fields with fees and liquidation details
- **Data Coverage:**
  - Real-time datastreams
  - Historical data (fully backfilled except ~1% heavy traders)
  - Raw & enriched data
  - Asset transfers, raw trades, DEX trades
- **API:** Low-latency APIs, custom workflows

#### Pros
- Hyperliquid-specific support
- Comprehensive DEX trade data
- Low-latency APIs
- Real-time streaming

#### Cons
- No public pricing
- Limited backfill for heavy traders (10k+ trades)
- Need to query liquidator address manually

---

### 14. Dune Analytics
**Official Site:** https://dune.com/pricing
**Documentation:** https://dune.com/

#### Pricing
- **Structure:** Credit-based, usage-dependent
- **Engines:** Medium (standard) and Large (2x capacity, faster)
- **Details:** Pricing not fully available in search results

#### Features
- **Hyperliquid Support:** YES
- **Liquidation Data:**
  - Community dashboards with liquidation queries
  - SQL querying for custom analysis
  - Historical trade and liquidation tracking
- **Key Stats Available:**
  - Cumulative volume, trades, users
  - Inflow/outflow tracking
  - User analytics
- **API:** Query execution API, DataShare streaming

#### Pros
- SQL-based querying (flexible)
- Community dashboards available
- Interactive visualizations
- API and DataShare access

#### Cons
- Credit-based pricing (unpredictable costs)
- Need to build queries yourself
- Not real-time focused
- Pricing not transparent

---

### 15. CryptoQuant
**Official Site:** https://cryptoquant.com/pricing
**API Documentation:** https://cryptoquant.com/docs

#### Pricing
- **Plans Available:** Multiple tiers (specific pricing not in search results)
- **Payment:** Monthly or yearly
- **Cancellation:** Anytime

#### Features
- **Hyperliquid Support:** YES
- **Liquidation Data:**
  - Daily overview tracking
  - On-chain data analytics
  - Derivatives data
  - DEX trades and charts
- **API:** Simple endpoints for transaction data and on-chain statistics

#### Pros
- Hyperliquid tracking confirmed
- Flexible cancellation
- Academic institution access (free)
- On-chain and derivatives focus

#### Cons
- Pricing not transparent
- Limited liquidation-specific details
- Need to contact for pricing

---

### 16. CoinAPI
**Official Site:** https://www.coinapi.io/market-data-api/pricing

#### Pricing Tiers

| Tier | Approximate Cost | Daily Requests | Features |
|------|------------------|----------------|----------|
| **Free/Trial** | $0 | Limited | Basic access |
| **Startup** | From $79 | 1,000/day | Email support |
| **Streamer** | Higher | 10,000/day | WebSocket (trades/quotes) |
| **Pro** | Higher | 100,000/day | Full WebSocket, FIX protocol |
| **Enterprise** | Custom | Custom | High-volume users |

**Note:** Pricing ranges from $79 to $599+ depending on tier

#### Features
- **Hyperliquid Support:** YES - Confirmed integration
- **Liquidation Data:** Available (market data API coverage)
- **Additional Features:**
  - WebSocket access
  - FIX protocol support
  - Real-time and historical data
- **Overage:** $0.20 per 1,000 calls (Pro subscribers)

#### Pros
- Confirmed Hyperliquid integration
- WebSocket support
- Flexible tier options
- Volume discounts

#### Cons
- Unclear specific liquidation endpoints
- Need sales contact for precise pricing
- Credit-based system complexity

---

### 17. Tardis.dev
**Official Site:** https://tardis.dev/
**Documentation:** https://docs.tardis.dev/

#### Pricing
- **Free Access:** First day of each month (no API key)
- **Paid Plans:** Available (specific pricing not in search results)
- **Discounts:** Student and academic researcher plans

#### Features
- **Hyperliquid Support:** NOT CONFIRMED - Documentation doesn't explicitly list Hyperliquid
- **Data Types:**
  - Tick-level order book snapshots
  - Incremental L2 updates
  - Tick-by-tick trades
  - Historical liquidations (from WebSocket feeds)
  - Open interest, funding, mark prices
- **Access:** API and downloadable CSV files

#### Pros
- Tick-level granularity
- Historical liquidation data
- CSV download option
- Academic discounts

#### Cons
- Hyperliquid support not confirmed
- Pricing not transparent
- May not have recent exchange additions

---

### 18. Flipside Crypto
**Official Site:** https://flipsidecrypto.xyz/pricing
**Documentation:** https://docs.flipsidecrypto.xyz/

#### Pricing Tiers

| Tier | Cost | Query Seconds (Studio) | Query Seconds (API) | Features |
|------|------|------------------------|---------------------|----------|
| **Free** | $0 | Unlimited | 500/month | 20+ chains, 60+ APIs |
| **Builder** | Not listed | Unlimited | 10,000 (premium) | Scheduling, caching, Builder warehouse |
| **Pro** | Not listed | Unlimited | 60,000 (premium) | Dedicated warehouse, Snowflake/Studio/API |

#### Features
- **Hyperliquid Support:** NOT CONFIRMED - No explicit documentation found
- **Data Access:**
  - SQL querying
  - Unlimited dashboards
  - API/SDK access
  - Decoded blockchain data
- **Coverage:** 20+ chains

#### Pros
- Free tier with unlimited Studio queries
- 500 free API query seconds/month
- Multiple chain support
- SQL-based querying

#### Cons
- Hyperliquid support not confirmed
- Pricing for paid tiers not transparent
- Need to confirm chain coverage

---

## Native Hyperliquid API

### 19. Hyperliquid Native API
**Official Documentation:** https://hyperliquid.gitbook.io/hyperliquid-docs/
**Info Endpoint:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint

#### Pricing
- **Cost:** FREE
- **Rate Limit:** Weight-based system
  - 1,200 weight per minute
  - Exchange API requests: weight 1
  - Basic info requests (l2Book, allMids, etc.): weight 2
  - Other info requests: weight 20
- **Volume-Based Access:** 1 request per 1 USDC traded cumulatively
- **Initial Buffer:** 10,000 requests per address

#### API Endpoints
- **Mainnet:** https://api.hyperliquid.xyz
- **Testnet:** https://api.hyperliquid-testnet.xyz

#### Features
- **Liquidation Data:**
  - `liquidatable()` method - returns liquidatable positions
  - Historical liquidations
  - Real-time liquidation tracking
- **Additional Data:**
  - Order book (L2)
  - Trades
  - Open interest
  - Funding rates
  - User positions
  - Clearinghouse state
- **WebSocket:** Available for real-time subscriptions
- **Transparency:** All liquidations on-chain with <1 second latency

#### Pros
- Completely FREE
- Direct source of truth
- Real-time on-chain data
- No intermediary fees
- Volume-based rate limits (trade more = more requests)
- WebSocket support
- Well-documented

#### Cons
- Need to build your own aggregation logic
- Rate limits may be restrictive for non-traders
- Requires blockchain/API knowledge
- No analytics or processed insights
- Self-hosted infrastructure needed

---

## Comparison Table

### Quick Reference: Pricing Overview

| Provider | Type | Free Tier | Cheapest Paid | Best Value | Hyperliquid Support | Liquidation Data |
|----------|------|-----------|---------------|------------|---------------------|------------------|
| **Hyperliquid Native API** | Native API | ✅ Free | N/A | ✅ Free | ✅ YES | ✅ Direct |
| **Coinalyze** | Analytics | ✅ Free (40/min) | N/A | ✅ Free | ✅ YES | ✅ Aggregated |
| **Gate.com** | Exchange API | ✅ Free | N/A | ✅ Free | ✅ YES | ✅ Yes |
| **CoinGlass** | Analytics | ❌ No | $29/mo | $79/mo (Startup) | ✅ YES | ✅ Comprehensive |
| **Chainstack** | RPC | ✅ 3M req/mo | $49/mo | $49/mo (Growth) | ✅ YES | ⚠️ RPC Only |
| **QuickNode** | RPC | ✅ 10M credits | $49/mo | $249/mo (Accelerate) | ✅ YES | ⚠️ RPC Only |
| **dRPC** | RPC | ✅ Basic | $10/mo | $10/mo | ✅ YES | ⚠️ RPC Only |
| **Santiment** | Analytics | ✅ 1K API/mo | $49/mo | $49/mo (Pro) | ❓ Unknown | ❌ Not specific |
| **Nansen** | Analytics | ✅ 100 credits | $49/mo API | $99/mo (Pioneer) | ⚠️ Multi-chain | ⚠️ Risk only |
| **Glassnode** | Analytics | ✅ Basic | $29/mo | $799/mo (Pro) | ✅ YES | ✅ Heatmaps |
| **CoinAnk** | Analytics | ⚠️ Freemium | Unknown | Unknown | ✅ YES | ✅ Yes |
| **HypeRPC** | RPC | ❌ No | Custom | Custom | ✅ YES (dedicated) | ⚠️ RPC Only |
| **Imperator** | RPC | ❌ No | Custom | Custom | ✅ YES | ⚠️ RPC Only |
| **Allium** | Blockchain Data | ❌ No | Custom | Custom | ✅ YES | ✅ DEX trades |
| **Dune Analytics** | Analytics | ⚠️ Limited | Credit-based | Credit-based | ✅ YES | ✅ SQL queries |
| **CryptoQuant** | Analytics | ❌ No | Unknown | Unknown | ✅ YES | ✅ Yes |
| **CoinAPI** | Market Data | ⚠️ Limited | $79/mo | ~$79-599 | ✅ YES | ⚠️ Market data |
| **Tardis.dev** | Historical Data | ⚠️ 1st day/month | Unknown | Unknown | ❓ Unconfirmed | ⚠️ Historical |
| **Flipside** | Analytics | ✅ 500 API sec | Unknown | Unknown | ❓ Unconfirmed | ❓ Unknown |

---

### Detailed Comparison Matrix

#### Best for Real-Time Liquidation Data

| Rank | Provider | Cost | Rate Limit | Latency | Coverage |
|------|----------|------|------------|---------|----------|
| 1 | **Hyperliquid Native API** | Free | 1200 weight/min | <1s | Complete |
| 2 | **CoinGlass** | $29-699/mo | 30-1200/min | ≤1 min | Complete |
| 3 | **Coinalyze** | Free | 40/min | Unknown | Aggregated |
| 4 | **Gate.com** | Free | Unknown | Real-time | Via API |
| 5 | **CoinAnk** | Varies | Unknown | Real-time | Complete |

#### Best for Historical Liquidation Analysis

| Rank | Provider | Cost | Historical Depth | Analytics Tools | Export Options |
|------|----------|------|------------------|-----------------|----------------|
| 1 | **Glassnode** | $799/mo | Full | ✅ Advanced | ✅ Yes |
| 2 | **CoinGlass** | $29-699/mo | Full | ✅ Good | ✅ API |
| 3 | **Dune Analytics** | Credit-based | Full | ✅ SQL | ✅ CSV |
| 4 | **Allium** | Custom | ~Full (99%) | ⚠️ Custom | ✅ API |
| 5 | **Coinalyze** | Free | Limited | ⚠️ Basic | ✅ API |

#### Best for Developers/Trading Bots

| Rank | Provider | Cost | API Quality | Rate Limits | WebSocket | Documentation |
|------|----------|------|-------------|-------------|-----------|---------------|
| 1 | **Hyperliquid Native API** | Free | ✅ Excellent | 1200 w/min | ✅ Yes | ✅ Excellent |
| 2 | **Chainstack** | $0-199/mo | ✅ Excellent | 25-400 RPS | ✅ Yes | ✅ Excellent |
| 3 | **QuickNode** | $49-999/mo | ✅ Excellent | 50-500 RPS | ✅ Yes | ✅ Excellent |
| 4 | **CoinGlass** | $29-699/mo | ✅ Good | 30-1200/min | ⚠️ Unknown | ✅ Good |
| 5 | **Coinalyze** | Free | ✅ Good | 40/min | ❌ No | ✅ Good |

#### Best for Budget-Conscious Users

| Rank | Provider | Cost | Features | Best For |
|------|----------|------|----------|----------|
| 1 | **Hyperliquid Native API** | Free | Full liquidation data, direct access | Developers, traders |
| 2 | **Coinalyze** | Free | Aggregated liquidations, 10 endpoints | Simple integrations |
| 3 | **Gate.com** | Free | Liquidation queries, market data | Basic tracking |
| 4 | **Chainstack** | $0 (3M req) | RPC access, WebSocket | Light usage |
| 5 | **CoinGlass** | $29/mo | 70+ endpoints, 30/min | Personal projects |

---

## Recommendations

### Use Case: Personal Project / Learning
**Recommendation:** Start with **Hyperliquid Native API** + **Coinalyze** (free tier)
- **Why:** Both are completely free, well-documented, and provide complementary data
- **Setup Time:** 1-2 hours
- **Cost:** $0/month

### Use Case: Trading Bot / Real-Time Monitoring
**Recommendation:** **Hyperliquid Native API** (primary) + **Chainstack** (backup/archive)
- **Why:** Direct on-chain access + reliable infrastructure with WebSocket support
- **Rate Limits:** 1200 weight/min + 25 RPS (free) or 250 RPS ($49)
- **Cost:** $0-49/month

### Use Case: Analytics Dashboard / Commercial Product
**Recommendation:** **CoinGlass** (Standard tier) for pre-aggregated data
- **Why:** Comprehensive liquidation endpoints, 300/min rate limit, commercial license
- **Rate Limits:** 300 requests/min (sufficient for most dashboards)
- **Cost:** $299/month

### Use Case: High-Frequency Trading / Enterprise
**Recommendation:** **HypeRPC** or **Imperator** (dedicated nodes) + **CoinGlass** (Professional tier)
- **Why:** Lowest latency + institutional reliability + aggregated analytics
- **Rate Limits:** Custom (unlimited) + 1200/min
- **Cost:** Custom pricing (likely $1,000-5,000/month)

### Use Case: Research / Historical Analysis
**Recommendation:** **Glassnode** (Professional) + **Dune Analytics**
- **Why:** Position-level granularity + flexible SQL querying
- **Features:** Liquidation heatmaps, risk analysis, custom queries
- **Cost:** $799/month + credit-based

### Use Case: Multi-Exchange Aggregation
**Recommendation:** **CoinGlass** (any tier) + **Coinalyze** (free)
- **Why:** Both aggregate across multiple contracts/exchanges
- **Coverage:** Comprehensive cross-exchange liquidation tracking
- **Cost:** $29-699/month (CoinGlass tier) + $0 (Coinalyze)

---

## Cost-Benefit Analysis

### Free Options (Total: $0/month)
**Providers:** Hyperliquid Native API, Coinalyze, Gate.com, Chainstack (3M), QuickNode trial
- **Pros:** No cost, decent rate limits, good for learning/prototyping
- **Cons:** Rate limits, no support, limited features
- **Best For:** Students, hobbyists, proof-of-concepts

### Budget Tier ($29-79/month)
**Providers:** CoinGlass (Hobbyist/Startup), CoinAPI (Startup)
- **Pros:** Affordable, better rate limits, email support, commercial use
- **Cons:** Still limited for high-volume applications
- **Best For:** Side projects, small commercial apps, indie developers

### Professional Tier ($249-699/month)
**Providers:** CoinGlass (Standard/Pro), QuickNode (Accelerate), Santiment (Max)
- **Pros:** High rate limits, full features, priority support, SLAs
- **Cons:** Significant cost, may still need multiple providers
- **Best For:** Established products, trading firms, analytics companies

### Enterprise Tier ($799-5000+/month)
**Providers:** Glassnode (Pro), Nansen (Pro), HypeRPC (Dedicated), Imperator
- **Pros:** Unlimited/custom limits, dedicated support, highest quality data
- **Cons:** Very expensive, overkill for most use cases
- **Best For:** Hedge funds, large trading operations, research institutions

---

## Key Considerations

### 1. Data Freshness
- **Real-time (<1 second):** Hyperliquid Native API, CoinGlass (1s updates)
- **Near real-time (~1 minute):** CoinGlass, Gate.com WebSocket
- **Periodic updates:** Most analytics platforms

### 2. Historical Depth
- **Full history:** Hyperliquid Native API, Glassnode, CoinGlass, Dune
- **Limited history:** Coinalyze (free), Santiment (Advanced: 30 days)
- **Depends on plan:** Most providers scale history with tier

### 3. Rate Limits vs Cost
- **Best free:** Hyperliquid Native (1200 weight/min) > Coinalyze (40/min)
- **Best value paid:** Chainstack ($49 for 250 RPS) > CoinGlass ($29 for 30/min)
- **Best enterprise:** HypeRPC/Imperator (custom unlimited)

### 4. Developer Experience
- **Best docs:** Hyperliquid Native API, QuickNode, Chainstack
- **Easiest setup:** Coinalyze, Gate.com
- **Most flexible:** Dune Analytics (SQL), Hyperliquid Native API

### 5. Data Reliability
- **Source of truth:** Hyperliquid Native API (direct on-chain)
- **High reliability:** QuickNode (99.99%), Chainstack, HypeRPC (99.99%)
- **Analytics reliability:** CoinGlass, Glassnode (curated/processed)

---

## Integration Complexity

### Simple (1-2 hours)
- Coinalyze API (10 endpoints, straightforward)
- Gate.com public API
- Hyperliquid Native API (info endpoint only)

### Moderate (1-2 days)
- CoinGlass API (many endpoints, need aggregation)
- Chainstack/QuickNode (RPC setup + parsing liquidation events)
- Santiment API (GraphQL learning curve)

### Complex (1-2 weeks)
- Hyperliquid Native API (full integration with WebSocket + event parsing)
- Dune Analytics (SQL query development + API integration)
- Nansen API (understanding credit system + data modeling)

### Enterprise (2-4 weeks)
- HypeRPC/Imperator (infrastructure setup + dedicated nodes)
- Glassnode Pro (advanced analytics integration)
- Multi-provider setup (aggregating multiple sources)

---

## API Documentation Links

### Analytics Platforms
- **CoinGlass:** https://docs.coinglass.com/
- **Coinalyze:** https://api.coinalyze.net/v1/doc/
- **Gate.com:** https://www.gate.com/docs/developers/apiv4/
- **Glassnode:** https://docs.glassnode.com/
- **Nansen:** https://docs.nansen.ai/
- **Santiment:** https://academy.santiment.net/sanapi/
- **CoinAnk:** https://coinank.com/openApi
- **Dune Analytics:** https://dune.com/docs/
- **CryptoQuant:** https://cryptoquant.com/docs

### RPC Providers
- **QuickNode:** https://www.quicknode.com/docs/hyperliquid
- **Chainstack:** https://docs.chainstack.com/
- **HypeRPC:** https://hyperpc.app/blog/
- **dRPC:** https://drpc.org/

### Blockchain Data
- **Allium:** https://docs.allium.so/
- **CoinAPI:** https://docs.coinapi.io/
- **Flipside:** https://docs.flipsidecrypto.xyz/
- **Tardis.dev:** https://docs.tardis.dev/

### Native
- **Hyperliquid:** https://hyperliquid.gitbook.io/hyperliquid-docs/

---

## Summary Table: Best Options by Budget

| Monthly Budget | Primary Provider | Secondary Provider | Use Case | Total Cost |
|----------------|------------------|-------------------|----------|------------|
| **$0** | Hyperliquid Native API | Coinalyze | Learning, prototyping | $0 |
| **$0-50** | Hyperliquid Native API | Chainstack Growth ($49) | Trading bot, light usage | $0-49 |
| **$50-100** | CoinGlass Startup ($79) | Coinalyze (free) | Small commercial app | $79 |
| **$100-300** | CoinGlass Standard ($299) | Hyperliquid Native (free) | Analytics dashboard | $299 |
| **$300-1000** | CoinGlass Pro ($699) | QuickNode Business ($999) | Trading platform | $699-1698 |
| **$1000+** | HypeRPC/Imperator (custom) | CoinGlass Pro ($699) | HFT, enterprise | $2000+ |

---

## Conclusion

For most users, the **Hyperliquid Native API** provides the best value as it's free, direct, and comprehensive. Pair it with **Coinalyze** (also free) for aggregated cross-exchange data and you have a complete solution at $0/month.

For commercial applications requiring reliability and support, **CoinGlass** offers the best balance of features, pricing, and liquidation-specific data at $299/month for the Standard tier.

For high-performance trading operations, investing in **dedicated RPC infrastructure** (HypeRPC, Imperator) combined with **CoinGlass Professional** ensures lowest latency and highest reliability, though at enterprise pricing.

The key is matching your budget and technical requirements to the right provider(s) - often a combination of a free primary source (Hyperliquid Native) plus a paid aggregator (CoinGlass) provides the optimal cost-benefit ratio.

---

**Document Version:** 1.0
**Last Updated:** October 22, 2025
**Research Date:** October 22, 2025

**Note:** Pricing and features are subject to change. Always verify current pricing and capabilities directly with providers before making a decision.
