use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fmt;

// ── Price & Market Data ──

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
pub struct PerpData {
    pub symbol: String,
    pub price: f64,
    pub volume_24h: f64,
    pub change_24h_pct: f64,
    pub open_interest: Option<f64>,
    pub funding_rate: Option<f64>,
    pub timestamp: DateTime<Utc>,
}

// ── Open Interest ──

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum MarketType {
    Usdt,
    Usdc,
    UsdInverse,
}

impl fmt::Display for MarketType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
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
    pub symbol: String,
    pub base_symbol: String,
    pub market_type: MarketType,
    pub oi_contracts: f64,
    pub oi_usd: f64,
    pub price: f64,
    pub funding_rate: f64,
    pub volume_24h_usd: f64,
    pub timestamp: DateTime<Utc>,
}

// ── Volume Analysis ──

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum SpikeLevel {
    Normal,
    Moderate,
    High,
    Extreme,
}

impl fmt::Display for SpikeLevel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
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

impl fmt::Display for Trend {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
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
    pub cvd_change_pct: f64,
    pub cvd_trend: Trend,
    pub divergence_detected: bool,
    pub price_trend: Trend,
    pub current_delta: f64,
    pub current_delta_usd: f64,
    pub timestamp: DateTime<Utc>,
}

// ── Technical Indicators ──

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Indicators {
    pub rsi_14: Option<f64>,
    pub vwap: Option<f64>,
    pub atr_14: Option<f64>,
    pub bb_upper: Option<f64>,
    pub bb_middle: Option<f64>,
    pub bb_lower: Option<f64>,
    pub volatility_pct: Option<f64>,
}

// ── Comprehensive Result ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceFullAnalysis {
    pub symbol: String,
    pub timeframe: String,
    pub ticker: Ticker,
    pub perp: PerpData,
    pub indicators: Indicators,
    pub volume_spike: VolumeSpike,
    pub cvd: CvdData,
    pub oi_markets: Vec<MarketOi>,
    pub total_oi_usd: f64,
    pub latency_ms: LatencyBreakdown,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatencyBreakdown {
    pub ticker_ms: u128,
    pub ohlcv_ms: u128,
    pub oi_ms: u128,
    pub funding_ms: u128,
    pub indicators_calc_ms: u128,
    pub volume_calc_ms: u128,
    pub cvd_calc_ms: u128,
    pub total_ms: u128,
}
