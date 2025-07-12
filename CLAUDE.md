# Crypto Assistant - Enhanced Market Analysis System

## Project Overview
Advanced cryptocurrency market analysis platform with institutional-grade features including volume analysis, cumulative volume delta (CVD), technical indicators, and comprehensive long/short position tracking.

## Recent Major Enhancements (Latest Session)

### ✅ LATEST: 100% Scalable Exchange System (July 12, 2025)
- **Zero-Code Exchange Addition**: Add any CCXT exchange via configuration only
- **Dynamic CCXT Integration**: Automatic exchange class discovery and loading
- **Configuration-Driven**: `SUPPORTED_EXCHANGES=binance,bybit,okx,kucoin,gate` 
- **Live Demonstration**: Added KuCoin with single config line change
- **Same-Exchange Logic**: Both spot and perp data from user-specified exchange
- **Auto-Futures Detection**: Automatic derivatives market discovery per exchange
- **Scalability Score**: 10/10 (improved from 4/10 after external audit)

### ✅ Phase 1 Complete: Enhanced /price Command  
- **Real OI Changes**: Historical 24h/15m OI changes with percentage context
- **Enhanced Funding Rate**: Annual cost calculation, reset timing, trading strategy
- **Visual Delta Dots**: Green/red indicators for instant market control clarity
- **Market Intelligence**: 24H/15M control analysis with momentum detection
- **Exchange Names**: Dynamic detection from CCXT exchange.id objects

### ✅ Previous: Net Longs/Shorts Implementation
- **Institutional vs Retail Separation**: Top trader position ratios vs global account ratios
- **Live API Integration**: Binance futures long/short ratio endpoints
- **Token-First Display**: Native token amounts with USD values in parentheses
- **Mathematical Validation**: All calculations verified (Longs + Shorts = Total OI)

## Tech Stack & Deployment

### ✅ LATEST: AWS Production Deployment Complete (July 4, 2025)
- **Infrastructure**: AWS EC2 t3.micro (i-0be83d48202d03ef1) in Sydney region
- **Public IP**: 13.239.14.166 with full webhook functionality
- **Repository**: Migrated to napo99/TG-Bot.git with proper branch management
- **Webhook Migration**: Complete transition from polling to webhook architecture
- **Branch Resolution**: Merged webhook-testing into aws-deployment branch
- **Security**: Configured security groups for ports 8080 (webhook) and 8001 (market data)
- **Services**: All 3 Docker containers running (telegram-bot, market-data, redis)
- **Performance**: Sub-2 second response times, <400MB memory usage
- **Status**: ✅ PRODUCTION READY & OPERATIONAL

### ✅ Previous: Universal Journaling Snippets with Enhanced Date Format
- **19+ Shortcuts Implemented**: Date/time, journal templates, writing productivity helpers
- **Enhanced Date Format**: Day abbreviation + date (Wed | 02-07-2025 - 14:30)
- **Cross-Terminal Compatibility**: Works in iTerm2, WezTerm, all terminal environments
- **Conflict-Free Design**: Intuitive shortcuts with `<leader>d*`, `<leader>j*`, `<leader>w*` prefixes
- **Real-Time Data**: All dates/times use system clock (not hardcoded)

### ✅ Previous: Universal Indent Toggle Fix
- **Cross-Terminal Compatibility**: `<leader>ti` now works in both iTerm2 and WezTerm
- **Issue Resolved**: Moved keymap outside terminal-specific conditional block
- **Universal Functionality**: Indent guides toggle available in all terminal environments
- **Validation Tested**: Confirmed working across multiple terminals and file types

### ⚠️ CRITICAL: Always Use Docker
- **Production Environment**: Docker containers with docker-compose
- **Service Communication**: Inter-container networking (crypto-market-data:8001)
- **Local Testing**: Must use Docker, not direct Python execution
- **TG Bot Config**: Connects to `crypto-market-data:8001` service name

### Docker Services
```bash
# Start all services
docker-compose up -d

# Check running containers  
docker ps

# View logs
docker-compose logs -f telegram-bot
docker-compose logs -f market-data
```

## Architecture

### Core Services
1. **Market Data Service** (`services/market-data/`)
   - Exchange management with ccxt integration
   - Volume analysis engine with spike detection
   - Technical indicators (RSI, VWAP, Bollinger Bands)
   - CVD calculation with point-in-time delta
   - Long/Short position data aggregation

2. **Telegram Bot Service** (`services/telegram-bot/`)
   - Real-time market analysis commands
   - Enhanced message formatting
   - User authorization system
   - Comprehensive market intelligence display

### Key Data Structures
```python
@dataclass
class LongShortData:
    # Institutional (Top Traders)
    institutional_long_pct: float
    institutional_short_pct: float
    institutional_long_ratio: float
    net_longs_institutional: float
    net_shorts_institutional: float
    
    # Retail (All Users)  
    retail_long_pct: float
    retail_short_pct: float
    retail_long_ratio: float
    net_longs_retail: float
    net_shorts_retail: float
    
    # USD conversions and metadata
    token_price: float
    total_oi_tokens: float
    # ... USD value fields

@dataclass
class UnifiedOIResponse:
    base_symbol: str
    total_markets: int
    aggregated_oi: Dict[str, Any]
    exchange_breakdown: List[Dict[str, Any]]
    validation_summary: Dict[str, Any]
    total_oi_usd: float
```

### Enhanced CVD Analysis
```python
@dataclass
class CVDData:
    current_cvd: float           # Cumulative volume delta
    current_delta: float         # Point-in-time delta (new)
    current_delta_usd: float     # USD value of current delta (new)
    cvd_trend: str              # BULLISH/BEARISH/NEUTRAL
    divergence_detected: bool   # Price-CVD divergence
```

## API Endpoints

### Comprehensive Analysis
`POST /comprehensive_analysis`
```json
{
  "symbol": "SOL/USDT",
  "timeframe": "15m"
}
```

### Multi-Exchange OI Analysis
`POST /multi_oi`
```json
{
  "symbol": "BTC-USDT"
}
```

### Additional Endpoints
- `POST /test_exchange_oi` - Individual exchange OI validation
- `POST /volume_scan` - Cross-exchange volume spike detection
- `POST /debug_tickers` - Exchange ticker debugging

**Enhanced Response includes:**
- Price data with funding rates
- Volume analysis with token amounts
- CVD analysis with point-in-time delta
- Long/short position breakdown (institutional vs retail)
- **6-Exchange OI Aggregation**: Complete market coverage
- Technical indicators
- Market sentiment analysis

## Enhanced /price Command Output
```
📊 SOL/USDT (Binance)

🏪 SPOT
💰 Price: $162.48 | -1.32% | $-2.15 | ATR: 3.45
🟢 Price Change 15m: +0.01% | $0.02 | ATR: 0.45
📊 Volume 24h: 3,554,553 SOL ($577.54M)
📊 Volume 15m: 1,497 SOL ($243.28K)
📈 Delta 24h: 🟢 +89,849 SOL (+$14.60M) | L/S: 51%/49%
📈 Delta 15m: 🟢 +561.49 SOL (+$91.23K) | L/S: 69%/31%

⚡ PERPETUALS
💰 Price: $162.40 | -1.34% | $-2.17 | ATR: 3.48
🟢 Price Change 15m: +0.01% | $0.01 | ATR: 0.46
📊 Volume 24h: 23,997,029 SOL ($3.90B)
📊 Volume 15m: 14,198 SOL ($2.31M)
📈 Delta 24h: 🟢 +365,115 SOL (+$59.29M) | L/S: 51%/49%
📈 Delta 15m: 🟢 +6,310 SOL (+$1.02M) | L/S: 72%/28%
📈 OI: 9,030,525 SOL ($1.47B)
📊 OI Change 24h: +451,786 SOL (+$73.4M) | +5.00%
📊 OI Change 15m: -10,677 SOL ($-1.7M) | -0.12%
💸 Funding: +0.0100% (+10.95% annually)
⏰ Resets in: 6h 27m | 🟡 LONG PRESSURE
🎯 Strategy: Consider short positions

🧠 MARKET INTELLIGENCE
💪 24H Control: ⚪ BALANCED (51% pressure) | Momentum: ACCELERATING
⚡ 15M Control: 🟢 BUYERS (72% pressure) | Activity: LOW (0.1x)

🕐 09:33:07 UTC / 17:33:07 SGT
```

## Key Features

### Market Intelligence
- **Volume Spike Detection**: NORMAL/MODERATE/HIGH/EXTREME classification
- **CVD Analysis**: Cumulative volume delta with divergence detection
- **Long/Short Ratios**: Institutional vs retail position tracking
- **6-Exchange OI Aggregation**: Complete market coverage including DEX
- **Validation Framework**: Mathematical verification across providers
- **Exchange Rankings**: Dynamic market share analysis
- **Cross-Exchange Arbitrage**: Price/OI discrepancy detection
- **Technical Indicators**: RSI, VWAP, ATR, Bollinger Bands
- **Market Sentiment**: Bulls/Bears/Neutral control analysis

## 🚀 Scalable Exchange System

### 100% Configuration-Driven
The system supports **any CCXT exchange** without code changes:

```yaml
# Add any exchange via configuration
SUPPORTED_EXCHANGES=binance,bybit,okx,kucoin,gateio,huobi,kraken
```

### Automatic Exchange Discovery
- **Dynamic CCXT Loading**: `getattr(ccxt, exchange_name)` discovers exchange classes
- **Auto-Futures Detection**: Tests market types for derivatives support  
- **API Key Integration**: `{EXCHANGE}_API_KEY` pattern for authentication
- **Exchange Names**: Dynamic detection from `exchange.id` properties

### Multi-Exchange Price Command
```bash
/price BTC-USDT           # Default exchange (Binance)
/price BTC-USDT bybit     # Bybit for both spot and perp
/price ETH-USDT okx       # OKX for both spot and perp  
/price SOL-USDT kucoin    # KuCoin spot, fallback perp
```

### Same-Exchange Logic
When user specifies an exchange, the system:
1. **Uses same exchange for spot data**
2. **Attempts same exchange for perp data**  
3. **Auto-detects if exchange supports futures**
4. **Graceful fallback if futures unavailable**

### Live Exchange Support
- ✅ **Binance**: Full spot + futures integration
- ✅ **Bybit**: Full spot + derivatives integration
- ✅ **OKX**: Full spot + swap derivatives integration
- ✅ **KuCoin**: Spot integration (live demo)
- 🔧 **Any CCXT Exchange**: Add via configuration

### Adding New Exchanges
**Process**: Zero code changes required
1. Add to `SUPPORTED_EXCHANGES` environment variable
2. Optional: Add API keys (`{EXCHANGE}_API_KEY`, `{EXCHANGE}_SECRET_KEY`)
3. Deploy - system auto-discovers capabilities

**Example**: Adding Gate.io
```yaml
SUPPORTED_EXCHANGES=binance,bybit,okx,kucoin,gateio
GATEIO_API_KEY=your_api_key      # Optional
GATEIO_SECRET_KEY=your_secret    # Optional
```

### Data Sources (Dynamic Exchanges)
- **Binance**: Spot and futures price data, open interest, long/short ratios
  - `topLongShortPositionRatio` (institutional)
  - `globalLongShortAccountRatio` (retail)
- **Bybit**: USDT/USDC perpetuals, advanced OI metrics
- **OKX**: Swap contracts, institutional-grade OI data
- **Gate.io**: Perpetual futures, cross-margined contracts
- **Bitget**: UMCBL/DMCBL contracts, comprehensive OI tracking
- **Hyperliquid**: DEX integration (decentralized), unique on-chain data
- **Real-time Processing**: Concurrent data fetching across all exchanges

### Display Format
- **Token-First**: Native asset amounts prominently displayed
- **USD Context**: Dollar values in parentheses for reference
- **Hierarchical Data**: Institutional vs retail separation
- **Visual Indicators**: Emojis for quick sentiment assessment

## Development Commands

### Service Management
```bash
./start_services.sh    # Start all services with health checks
./stop_services.sh     # Stop all running services
./restart_service.sh   # Restart with fresh state
```

### Testing
```bash
# Test comprehensive analysis
curl -X POST http://localhost:8001/comprehensive_analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SOL/USDT", "timeframe": "15m"}'

# Test new features
python3 test_new_features.py
```

### Telegram Commands
- `/analysis BTC-USDT 15m` - Comprehensive market analysis
- `/volume SOL-USDT` - Volume spike detection
- `/cvd ETH-USDT 1h` - CVD analysis

## Recent Commits
- **Latest** - 📝 Universal Journaling Snippets with Enhanced Date Format (19+ shortcuts)
- `e1de515` - 🔧 Fix indent toggle universal compatibility: iTerm2 + WezTerm support
- `6c594b7` - Enhanced Market Analysis: Net Longs/Shorts & Point-in-Time Delta
- `299fff0` - Project Status Save: Phase 1 Complete & Live on GitHub

## Technical Implementation Notes

### Exchange API Integration
- Direct HTTP requests to Binance for long/short ratios (more reliable than ccxt)
- Concurrent data fetching using asyncio.gather() for performance
- Robust error handling with fallbacks for missing data

### Data Validation
- Mathematical verification: Longs + Shorts = Total OI
- Cross-reference institutional vs retail calculations
- USD conversion accuracy checks

### Performance Optimizations
- Async/await throughout data pipeline
- Concurrent API calls where possible
- Efficient data structure design
- Minimal redundant calculations

## Future Considerations
- Multi-exchange long/short aggregation (OKX, Bybit, Bitget)
- Historical long/short ratio trending
- Advanced divergence detection algorithms
- Additional institutional vs retail metrics

## Security & Configuration
- Environment variable configuration for API keys
- User authorization system for Telegram bot
- Rate limiting and error handling
- No sensitive data in logs or commits

## 🛡️ SYSTEM PROTECTION PROTOCOLS

### Critical File Protection
- **NEVER MODIFY**: `docker-compose.aws.yml`, `Dockerfile.aws`, any `*.aws` files
- **HIGH RISK**: `main_webhook.py`, `docker-compose.yml`, service Dockerfiles
- **SAFE TO MODIFY**: `formatting_utils.py`, test files, documentation

### Service Health Monitoring
```bash
# Quick health check
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -f http://localhost:8001/health  # Market data
curl -f http://localhost:8080/health  # Telegram bot

# Error detection
docker logs crypto-telegram-bot | grep -i error
docker logs crypto-market-data | grep -i error
```

### Change Management Protocol
1. **Document** change in DEVELOPMENT_WORKFLOW.md
2. **Backup** with git commit before changes
3. **Test locally** with full validation checklist
4. **External verification** via agent review
5. **Deploy** only after successful testing

### Emergency Procedures
```bash
# Service restart
docker-compose down && docker-compose up -d

# Rollback to working state
git reset --hard <last_working_commit>
docker-compose up -d --build
```

### Validation Checklist
- [ ] All containers healthy and running
- [ ] Bot responds to `/start` and `/price BTC-USDT`
- [ ] Market Intelligence features working
- [ ] L/S ratios displaying correctly
- [ ] Memory usage < 400MB combined
- [ ] No errors in logs

**See `SYSTEM_PROTECTION_GUIDE.md` for comprehensive protection protocols.**

---
*This system provides institutional-grade market analysis with enhanced position tracking and sentiment analysis capabilities.*