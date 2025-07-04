# Crypto Assistant - Enhanced Market Analysis System

## Project Overview
Advanced cryptocurrency market analysis platform with institutional-grade features including volume analysis, cumulative volume delta (CVD), technical indicators, and comprehensive long/short position tracking.

## Recent Major Enhancements (Latest Session)

### ✅ Net Longs/Shorts Implementation
- **Institutional vs Retail Separation**: Top trader position ratios vs global account ratios
- **Live API Integration**: Binance futures long/short ratio endpoints
- **Token-First Display**: Native token amounts with USD values in parentheses
- **Mathematical Validation**: All calculations verified (Longs + Shorts = Total OI)

### ✅ Point-in-Time Delta Analysis
- **Current Candle Delta**: Volume delta for immediate timeframe (separate from cumulative CVD)
- **USD Conversion**: Real-time dollar value calculations
- **Enhanced Momentum Detection**: Immediate sentiment analysis alongside long-term trends

### ✅ Enhanced Message Formatting
- **Improved Readability**: Token values first, USD in parentheses format
- **Comprehensive Display**: All market data in single coherent view
- **Institutional Intelligence**: Separate tracking of smart money vs retail sentiment

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

## Example Enhanced Output
```
🎯 MARKET ANALYSIS - SOL/USDT (15m)

💰 PRICE: $147.55 🔴 -3.2%
📊 VOLUME: 😴 NORMAL 117,444 SOL (-56%, $10.1M)
📈 CVD: 🔴📉 BEARISH -5,061,000 SOL ($-747M)
📊 DELTA: -117,444 SOL ($-17.3M)
📈 OI: 8,249,000 SOL ($1,218M) | 💸 Funding: -0.0012%
🏛️ INSTITUTIONAL: L: 5,632,000 SOL ($831M) | S: 2,617,000 SOL ($387M) | Ratio: 2.15
🏪 RETAIL: L: 6,007,000 SOL ($887M) | S: 2,242,000 SOL ($331M) | Ratio: 2.68

📉 TECHNICAL:
• RSI: 59 (Neutral)
• VWAP: $148.00 (Above VWAP ✅)
• Volatility: 2.3% (MODERATE)
• Rel Volume: 0.3x

🎯 MARKET CONTROL:
⚪🦀 NEUTRAL IN CONTROL (50% confidence)
⚡ Aggression: MODERATE
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

### Data Sources (6 Exchanges)
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

---
*This system provides institutional-grade market analysis with enhanced position tracking and sentiment analysis capabilities.*