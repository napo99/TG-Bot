# S12-S15 — OI Aggregator, Volume Profile, Session Volume, Sentiment

---

## S12 — OI Aggregator (`src/analysis/oi.rs`)

### Scope
Aggregates Open Interest data from all exchanges into a unified view. Uses `ExchangeManager` to fetch OI concurrently.

### Dependencies
- S01 (types), S03 (ExchangeManager), S04-S09 (exchange clients)

### Key Function

```rust
use crate::types::*;
use crate::exchange::ExchangeManager;

/// Fetch and aggregate OI across all exchanges for a base symbol.
///
/// 1. Use SymbolMapper to get all exchange-specific symbols
/// 2. Fetch OI + ticker + funding from each exchange concurrently
/// 3. Aggregate into AggregatedOi
/// 4. Sort top_markets by oi_usd descending
/// 5. Log errors per exchange, don't fail the whole request
pub async fn aggregate_oi(
    manager: &ExchangeManager,
    base_symbol: &str,
) -> AggregatedOi {
    // For each exchange:
    //   For each market type (USDT, USDC, Inverse):
    //     Try fetch_open_interest + fetch_ticker + fetch_funding_rate
    //     If any fails, skip that market (log warning)
    //     Build MarketOi from results
    //
    // Group by exchange → ExchangeOi
    // Sum across all → AggregatedOi totals
    // Sort top_markets by oi_usd desc, take top 13
}
```

### Tests (minimum 3)

```rust
#[tokio::test]
async fn test_aggregate_oi_all_succeed() {
    // Mock ExchangeManager with fake clients that return known OI values
    // Verify: total_oi_usd = sum of all markets
    // Verify: exchanges_succeeded matches count
    // Verify: top_markets sorted by oi_usd desc
}

#[tokio::test]
async fn test_aggregate_oi_partial_failure() {
    // Mock: 2 exchanges succeed, 1 fails
    // Verify: still returns data from successful exchanges
    // Verify: exchanges_succeeded = 2
}

#[tokio::test]
async fn test_aggregate_oi_market_type_breakdown() {
    // Mock: known USDT/USDC/Inverse values
    // Verify: usdt_oi_usd, usdc_oi_usd, inverse_oi_usd correct
}
```

### Exit Criteria
- [ ] Concurrent fetching (tokio::join or join_all)
- [ ] Partial failures don't crash the aggregation
- [ ] Market type breakdown sums correctly
- [ ] Top markets sorted by OI descending
- [ ] All 3 tests pass

---

## S13 — Volume Profile / TPO (`src/analysis/profile.rs`)

### Scope
Calculate Volume Profile and Time-at-Price (TPO) analysis. Pure computation.

### Dependencies
- S01 (types: `VolumeProfile`, `ProfileLevel`)

### Key Functions

```rust
/// Calculate volume profile from OHLCV candles.
///
/// Algorithm:
/// 1. Determine price range (min low to max high)
/// 2. Divide into `num_bins` equal-sized levels
/// 3. For each candle, distribute its volume across the levels it spans
///    (proportional to how much of the candle's range overlaps each level)
/// 4. Count TPO blocks (each candle touching a level = 1 TPO)
/// 5. POC = level with highest volume
/// 6. Value Area = levels containing 70% of total volume, expanding from POC
/// 7. VAH = highest price in value area, VAL = lowest
///
/// Timeframe configs:
///   1m  → 20 bins, 1h lookback
///   15m → 24 bins, 24h lookback
///   1h  → 24 bins, 7d lookback
///   4h  → 30 bins, 14d lookback
///   1d  → 50 bins, 30d lookback
pub fn calculate_profile(
    candles: &[Ohlcv],
    symbol: &str,
    timeframe: &str,
    current_price: f64,
) -> Option<VolumeProfile> { ... }

/// Calculate the Value Area (70% of volume) expanding outward from POC.
///
/// Algorithm:
/// 1. Start at POC level
/// 2. Look one level above and one below
/// 3. Add the level with more volume
/// 4. Repeat until cumulative volume >= 70% of total
/// 5. Return (vah_price, val_price)
fn calculate_value_area(
    levels: &[ProfileLevel],
    poc_idx: usize,
    total_volume: f64,
) -> (f64, f64) { ... }
```

### Tests (minimum 5)

```rust
#[test]
fn test_profile_poc_is_highest_volume() {
    // Create candles clustered around one price → POC should be at that price
}

#[test]
fn test_value_area_contains_70_pct() {
    // Verify sum of volume in value_area levels >= 70% of total
}

#[test]
fn test_profile_vah_above_val() {
    // Always: VAH >= POC >= VAL
}

#[test]
fn test_profile_vwap_distance() {
    // vwap_distance_pct = (current_price - vwap) / vwap * 100
}

#[test]
fn test_profile_empty_candles() {
    assert!(calculate_profile(&[], "BTC", "15m", 43000.0).is_none());
}
```

### Exit Criteria
- [ ] POC is the level with highest volume
- [ ] Value Area contains >= 70% of total volume
- [ ] VAH >= POC >= VAL always holds
- [ ] VWAP distance percentage calculated correctly
- [ ] Returns None for empty input
- [ ] All 5 tests pass

---

## S14 — Session Volume (`src/analysis/session.rs`)

### Scope
LuxAlgo-style 4-session volume analysis. Identifies which trading session is active and provides per-session volume breakdown.

### Dependencies
- S01 (types: `TradingSession`, `SessionVolume`)
- S11 (split_volume function)

### Key Functions

```rust
use chrono::{DateTime, Utc, Timelike};

/// Determine which trading session a timestamp falls in.
///
/// Sessions (UTC):
///   NewYork: 13:00 - 22:00
///   Asia:    22:00 - 06:00 (next day)
///   London:  06:00 - 13:00
pub fn current_session(ts: DateTime<Utc>) -> TradingSession {
    let hour = ts.hour();
    match hour {
        13..=21 => TradingSession::NewYork,
        22..=23 | 0..=5 => TradingSession::Asia,
        6..=12 => TradingSession::London,
        _ => unreachable!(),
    }
}

/// Calculate volume breakdown by session from OHLCV candles.
/// Assigns each candle to a session based on its timestamp.
pub fn session_breakdown(candles: &[Ohlcv]) -> Vec<SessionVolume> { ... }
```

### Tests (minimum 4)

```rust
#[test]
fn test_session_new_york() {
    let ts = chrono::Utc.with_ymd_and_hms(2025, 1, 15, 15, 30, 0).unwrap();
    assert_eq!(current_session(ts), TradingSession::NewYork);
}

#[test]
fn test_session_asia() {
    let ts = chrono::Utc.with_ymd_and_hms(2025, 1, 15, 23, 0, 0).unwrap();
    assert_eq!(current_session(ts), TradingSession::Asia);
}

#[test]
fn test_session_london() {
    let ts = chrono::Utc.with_ymd_and_hms(2025, 1, 15, 8, 0, 0).unwrap();
    assert_eq!(current_session(ts), TradingSession::London);
}

#[test]
fn test_session_breakdown_totals() {
    // Sum of session volumes should equal sum of candle volumes
}
```

### Exit Criteria
- [ ] All 24 hours mapped to correct session
- [ ] Session breakdown sums equal total volume
- [ ] All 4 tests pass

---

## S15 — Market Sentiment (`src/analysis/sentiment.rs`)

### Scope
Compute market sentiment score from price, volume, CVD, and technical indicator data.

### Dependencies
- S01 (types: `Sentiment`, `MarketControl`, `AggressionLevel`)
- S10 (Indicators), S11 (VolumeSpike, CvdData)

### Algorithm (from Python `main.py:1357-1420`)

```rust
/// Calculate market sentiment score.
///
/// Components (each -3 to +3):
///
/// 1. Price Sentiment (based on 24h change %):
///    >5%: +3, 2-5%: +2, 0-2%: +1, 0 to -2%: -1, -2 to -5%: -2, <-5%: -3
///
/// 2. Volume Sentiment (based on spike level):
///    EXTREME: +2, HIGH or MODERATE: +1, NORMAL: 0
///
/// 3. CVD Sentiment (based on trend + 24h change):
///    BULLISH + positive change: +2, BULLISH only: +1
///    BEARISH + negative change: -2, BEARISH only: -1
///    NEUTRAL: 0
///    If divergence_detected: -1 penalty
///
/// 4. Technical Sentiment (based on RSI):
///    RSI > 70: -1 (overbought)
///    RSI < 30: +1 (oversold)
///    RSI > 50: +1 (bullish momentum)
///    RSI < 50: -1 (bearish momentum)
///
/// Overall:
///   total = sum of components
///   max_possible = 3 + 2 + 2 + 2 = 9 (per component signs)
///   score = (total / 9.0) * 100.0  → range -100 to +100
///
/// Market Control:
///   score > 30  → BullsInControl
///   score < -30 → BearsInControl
///   else        → Neutral
///
/// Aggression:
///   No spike + low CVD change → Low
///   Spike OR CVD change > 500 → Moderate
///   Spike + CVD change > 1000 → High
pub fn calculate_sentiment(
    change_24h_pct: f64,
    volume_spike: Option<&VolumeSpike>,
    cvd: Option<&CvdData>,
    indicators: Option<&Indicators>,
) -> Sentiment { ... }
```

### Tests (minimum 5)

```rust
#[test]
fn test_sentiment_strong_bull() {
    // change=+6%, EXTREME spike, BULLISH CVD, RSI=65
    // Expected: score > 50, BullsInControl, High aggression
}

#[test]
fn test_sentiment_strong_bear() {
    // change=-6%, no spike, BEARISH CVD with divergence, RSI=25
    // Expected: score < -30, BearsInControl
}

#[test]
fn test_sentiment_neutral() {
    // change=+0.5%, no spike, NEUTRAL CVD, RSI=50
    // Expected: -30 <= score <= 30, Neutral
}

#[test]
fn test_sentiment_divergence_penalty() {
    // BULLISH CVD but with divergence → lower score than without
}

#[test]
fn test_sentiment_none_inputs() {
    // All optional inputs are None → still returns valid Sentiment
    let s = calculate_sentiment(0.0, None, None, None);
    assert!(s.overall_score >= -100.0 && s.overall_score <= 100.0);
}
```

### Exit Criteria
- [ ] Score range always -100 to +100
- [ ] Strong bull inputs produce score > 50
- [ ] Strong bear inputs produce score < -30
- [ ] Divergence reduces score by ~11 points
- [ ] None inputs handled gracefully
- [ ] All 5 tests pass
