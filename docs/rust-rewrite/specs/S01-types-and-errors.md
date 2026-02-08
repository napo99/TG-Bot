# S01 — Types and Errors

## Scope
Define ALL shared data types and error types used across the entire application. This is the single source of truth for data shapes. No other module defines public structs for cross-module data.

## Dependencies
- S00 (project compiles)

## Files to Create/Modify

### `src/types.rs`

All structs MUST derive `Debug, Clone, Serialize, Deserialize` unless noted.

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

// ──────────────────────────────────────────────
// Price & Market Data
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ticker {
    pub symbol: String,
    pub price: f64,
    pub volume_24h: f64,
    pub change_24h_pct: f64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ohlcv {
    pub timestamp: DateTime<Utc>,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpotData {
    pub symbol: String,
    pub price: f64,
    pub volume_24h: f64,
    pub change_24h_pct: f64,
    pub volume_15m: Option<f64>,
    pub change_15m_pct: Option<f64>,
    pub delta_24h: Option<f64>,
    pub delta_15m: Option<f64>,
    pub atr_24h: Option<f64>,
    pub atr_15m: Option<f64>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerpData {
    pub symbol: String,
    pub price: f64,
    pub volume_24h: f64,
    pub change_24h_pct: f64,
    pub open_interest: Option<f64>,
    pub funding_rate: Option<f64>,
    pub volume_15m: Option<f64>,
    pub change_15m_pct: Option<f64>,
    pub delta_24h: Option<f64>,
    pub delta_15m: Option<f64>,
    pub atr_24h: Option<f64>,
    pub atr_15m: Option<f64>,
    pub oi_change_24h: Option<f64>,
    pub oi_change_15m: Option<f64>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CombinedPrice {
    pub base_symbol: String,
    pub spot: Option<SpotData>,
    pub perp: Option<PerpData>,
    pub spot_exchange: String,
    pub perp_exchange: String,
    pub timestamp: DateTime<Utc>,
}

// ──────────────────────────────────────────────
// Account & Positions
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Balance {
    pub asset: String,
    pub total: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum PositionSide {
    Long,
    Short,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub symbol: String,
    pub side: PositionSide,
    pub size: f64,
    pub entry_price: f64,
    pub mark_price: f64,
    pub unrealized_pnl: f64,
    pub pnl_pct: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PnlSummary {
    pub total_unrealized_pnl: f64,
    pub average_pct: f64,
    pub position_count: usize,
}

// ──────────────────────────────────────────────
// Open Interest
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum MarketType {
    Usdt,
    Usdc,
    UsdInverse,
}

impl std::fmt::Display for MarketType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Usdt => write!(f, "USDT"),
            Self::Usdc => write!(f, "USDC"),
            Self::UsdInverse => write!(f, "USD"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketOi {
    pub exchange: String,
    pub symbol: String,         // exchange-specific symbol
    pub base_symbol: String,    // normalized: "BTC", "ETH"
    pub market_type: MarketType,
    pub oi_tokens: f64,
    pub oi_usd: f64,
    pub price: f64,
    pub funding_rate: f64,
    pub volume_24h_usd: f64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExchangeOi {
    pub exchange: String,
    pub base_symbol: String,
    pub markets: Vec<MarketOi>,
    pub total_oi_usd: f64,
    pub total_volume_24h_usd: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregatedOi {
    pub base_symbol: String,
    pub total_oi_usd: f64,
    pub total_oi_tokens: f64,
    pub usdt_oi_usd: f64,
    pub usdc_oi_usd: f64,
    pub inverse_oi_usd: f64,
    pub exchanges: Vec<ExchangeOi>,
    pub top_markets: Vec<MarketOi>,  // sorted by oi_usd desc
    pub exchanges_queried: usize,
    pub exchanges_succeeded: usize,
    pub timestamp: DateTime<Utc>,
}

// ──────────────────────────────────────────────
// Volume Analysis
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum SpikeLevel {
    Normal,
    Moderate,   // 100-200%
    High,       // 200-500%
    Extreme,    // >500%
}

impl std::fmt::Display for SpikeLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Normal => write!(f, "NORMAL"),
            Self::Moderate => write!(f, "MODERATE"),
            Self::High => write!(f, "HIGH"),
            Self::Extreme => write!(f, "EXTREME"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolumeSpike {
    pub symbol: String,
    pub timeframe: String,
    pub current_volume: f64,
    pub average_volume: f64,
    pub spike_pct: f64,
    pub spike_level: SpikeLevel,
    pub volume_usd: f64,
    pub is_significant: bool,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum Trend {
    Bullish,
    Bearish,
    Neutral,
}

impl std::fmt::Display for Trend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Bullish => write!(f, "BULLISH"),
            Self::Bearish => write!(f, "BEARISH"),
            Self::Neutral => write!(f, "NEUTRAL"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CvdData {
    pub symbol: String,
    pub timeframe: String,
    pub current_cvd: f64,
    pub cvd_change_24h: f64,
    pub cvd_trend: Trend,
    pub divergence_detected: bool,
    pub price_trend: Trend,
    pub current_delta: f64,
    pub current_delta_usd: f64,
    pub timestamp: DateTime<Utc>,
}

// ──────────────────────────────────────────────
// Technical Indicators
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Indicators {
    pub rsi_14: Option<f64>,
    pub vwap: Option<f64>,
    pub atr_14: Option<f64>,
    pub bb_upper: Option<f64>,
    pub bb_middle: Option<f64>,
    pub bb_lower: Option<f64>,
    pub volatility_24h: Option<f64>,
}

// ──────────────────────────────────────────────
// Volume Profile / TPO
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileLevel {
    pub price: f64,
    pub volume: f64,
    pub tpo_count: u32,
    pub is_poc: bool,       // Point of Control
    pub in_value_area: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolumeProfile {
    pub symbol: String,
    pub timeframe: String,
    pub vah: f64,           // Value Area High
    pub val: f64,           // Value Area Low
    pub poc: f64,           // Point of Control
    pub vwap: f64,
    pub vwap_distance_pct: f64,
    pub current_price: f64,
    pub levels: Vec<ProfileLevel>,
    pub timestamp: DateTime<Utc>,
}

// ──────────────────────────────────────────────
// Sentiment
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum MarketControl {
    BullsInControl,
    BearsInControl,
    Neutral,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum AggressionLevel {
    Low,
    Moderate,
    High,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sentiment {
    pub overall_score: f64,     // -100 to +100
    pub market_control: MarketControl,
    pub aggression: AggressionLevel,
    pub price_component: i8,    // -3 to +3
    pub volume_component: i8,
    pub cvd_component: i8,
    pub tech_component: i8,
    pub divergence_warning: bool,
}

// ──────────────────────────────────────────────
// Monitoring / Alerts
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum AlertPriority {
    High = 1,
    Medium = 2,
    Low = 3,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub id: String,
    pub priority: AlertPriority,
    pub alert_type: String,     // "oi_explosion", "liquidation_cascade"
    pub symbol: String,
    pub message: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum LiquidationSide {
    Long,
    Short,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Liquidation {
    pub symbol: String,
    pub side: LiquidationSide,
    pub price: f64,
    pub quantity: f64,
    pub value_usd: f64,
    pub timestamp: DateTime<Utc>,
}

// ──────────────────────────────────────────────
// Session Volume
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum TradingSession {
    NewYork,    // 13:00-22:00 UTC
    Asia,       // 22:00-06:00 UTC
    London,     // 06:00-13:00 UTC
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionVolume {
    pub session: TradingSession,
    pub volume: f64,
    pub volume_usd: f64,
    pub buy_volume: f64,
    pub sell_volume: f64,
    pub delta: f64,
    pub vwap: f64,
}

// ──────────────────────────────────────────────
// Comprehensive Analysis (combines everything)
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComprehensiveAnalysis {
    pub symbol: String,
    pub timeframe: String,
    pub price: CombinedPrice,
    pub volume: Option<VolumeSpike>,
    pub cvd: Option<CvdData>,
    pub indicators: Option<Indicators>,
    pub sentiment: Option<Sentiment>,
    pub oi: Option<AggregatedOi>,
    pub timestamp: DateTime<Utc>,
}
```

### `src/error.rs`

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Exchange error: {0}")]
    Exchange(#[from] ExchangeError),

    #[error("Telegram error: {0}")]
    Telegram(#[from] teloxide::RequestError),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Analysis error: {0}")]
    Analysis(String),
}

#[derive(Debug, Error)]
pub enum ExchangeError {
    #[error("HTTP request failed for {exchange}: {source}")]
    Http {
        exchange: String,
        #[source]
        source: reqwest::Error,
    },

    #[error("Failed to parse {exchange} response: {message}")]
    Parse {
        exchange: String,
        message: String,
    },

    #[error("Rate limit hit for {exchange}, retry after {retry_after_ms}ms")]
    RateLimited {
        exchange: String,
        retry_after_ms: u64,
    },

    #[error("Symbol {symbol} not found on {exchange}")]
    SymbolNotFound {
        exchange: String,
        symbol: String,
    },

    #[error("{exchange} API returned error: {code} - {message}")]
    ApiError {
        exchange: String,
        code: i64,
        message: String,
    },

    #[error("Timeout waiting for {exchange} response")]
    Timeout { exchange: String },
}
```

## Tests

### `tests/unit/types_test.rs`

```rust
use crypto_bot::types::*;
use chrono::Utc;

#[test]
fn test_market_type_display() {
    assert_eq!(MarketType::Usdt.to_string(), "USDT");
    assert_eq!(MarketType::Usdc.to_string(), "USDC");
    assert_eq!(MarketType::UsdInverse.to_string(), "USD");
}

#[test]
fn test_spike_level_display() {
    assert_eq!(SpikeLevel::Extreme.to_string(), "EXTREME");
    assert_eq!(SpikeLevel::Normal.to_string(), "NORMAL");
}

#[test]
fn test_trend_display() {
    assert_eq!(Trend::Bullish.to_string(), "BULLISH");
}

#[test]
fn test_alert_priority_ordering() {
    assert!(AlertPriority::High < AlertPriority::Medium);
    assert!(AlertPriority::Medium < AlertPriority::Low);
}

#[test]
fn test_ticker_serialization_roundtrip() {
    let ticker = Ticker {
        symbol: "BTCUSDT".to_string(),
        price: 43250.50,
        volume_24h: 1_500_000.0,
        change_24h_pct: 2.35,
        timestamp: Utc::now(),
    };
    let json = serde_json::to_string(&ticker).unwrap();
    let decoded: Ticker = serde_json::from_str(&json).unwrap();
    assert_eq!(decoded.symbol, "BTCUSDT");
    assert!((decoded.price - 43250.50).abs() < f64::EPSILON);
}

#[test]
fn test_position_side_equality() {
    assert_eq!(PositionSide::Long, PositionSide::Long);
    assert_ne!(PositionSide::Long, PositionSide::Short);
}

#[test]
fn test_combined_price_with_none_spot() {
    let cp = CombinedPrice {
        base_symbol: "BTC".to_string(),
        spot: None,
        perp: None,
        spot_exchange: "binance".to_string(),
        perp_exchange: "binance_futures".to_string(),
        timestamp: Utc::now(),
    };
    assert!(cp.spot.is_none());
    assert!(cp.perp.is_none());
}
```

## Exit Criteria

- [ ] All structs defined exactly as specified above
- [ ] All enums have `Display` implementations
- [ ] All types derive `Debug, Clone, Serialize, Deserialize`
- [ ] `ExchangeError` variants cover: Http, Parse, RateLimited, SymbolNotFound, ApiError, Timeout
- [ ] `AppError` wraps all module errors
- [ ] All 7 type tests pass
- [ ] `cargo build` succeeds
- [ ] `cargo clippy -- -D warnings` clean
