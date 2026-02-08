# S11 — Volume Spike Detection & CVD

## Scope
Pure computation module for volume analysis: spike detection and Cumulative Volume Delta. No I/O.

## Dependencies
- S01 (types: `Ohlcv`, `VolumeSpike`, `CvdData`, `SpikeLevel`, `Trend`)

## Files to Create

### `src/analysis/volume.rs`

```rust
use crate::types::*;
use chrono::Utc;

/// Detect volume spike for a symbol given OHLCV candles.
///
/// Algorithm (from Python `volume_analysis.py`):
/// 1. Extract volumes from candles (exclude the last/current candle from average)
/// 2. Remove outliers: drop top and bottom 5% of volumes
/// 3. Calculate median as baseline (robust to outliers)
/// 4. Spike percentage = (current_volume / median_volume - 1) * 100
/// 5. Classify:
///    - EXTREME: >500%
///    - HIGH: 200-500%
///    - MODERATE: 100-200%
///    - NORMAL: <100%
/// 6. is_significant = spike_pct > 150%
///
/// `price` is used to calculate volume_usd = current_volume * price
pub fn detect_spike(
    candles: &[Ohlcv],
    symbol: &str,
    timeframe: &str,
    price: f64,
) -> Option<VolumeSpike> {
    if candles.len() < 20 {
        return None; // Need minimum 20 candles for meaningful average
    }
    // Implementation...
}

/// Classify spike percentage into SpikeLevel.
pub fn classify_spike(pct: f64) -> SpikeLevel {
    if pct > 500.0 { SpikeLevel::Extreme }
    else if pct > 200.0 { SpikeLevel::High }
    else if pct > 100.0 { SpikeLevel::Moderate }
    else { SpikeLevel::Normal }
}

/// Calculate Cumulative Volume Delta from OHLCV data.
///
/// Algorithm (from Python `volume_analysis.py`):
/// For each candle:
///   close_position = (close - low) / (high - low)
///   buy_volume = volume * close_position
///   sell_volume = volume * (1 - close_position)
///   delta = buy_volume - sell_volume
/// CVD = cumulative sum of deltas
///
/// CVD trend:
///   - Last 20% of CVD values trending up → BULLISH
///   - Last 20% trending down → BEARISH
///   - Otherwise → NEUTRAL
///
/// Divergence: price_trend != cvd_trend
pub fn calculate_cvd(
    candles: &[Ohlcv],
    symbol: &str,
    timeframe: &str,
    price: f64,
) -> Option<CvdData> {
    if candles.is_empty() {
        return None;
    }
    // Implementation...
}

/// Calculate buy/sell volume split for a single candle.
/// Returns (buy_volume, sell_volume).
///
/// Method: close position within candle range
///   close_position = (close - low) / (high - low)
///   buy = volume * close_position
///   sell = volume * (1 - close_position)
///
/// Edge case: if high == low (doji), split 50/50.
pub fn split_volume(candle: &Ohlcv) -> (f64, f64) {
    let range = candle.high - candle.low;
    if range == 0.0 {
        return (candle.volume * 0.5, candle.volume * 0.5);
    }
    let close_pos = (candle.close - candle.low) / range;
    let buy = candle.volume * close_pos;
    let sell = candle.volume * (1.0 - close_pos);
    (buy, sell)
}

/// Determine trend from a series of values.
/// Compares mean of last 20% to mean of first 80%.
fn determine_trend(values: &[f64]) -> Trend {
    if values.len() < 5 { return Trend::Neutral; }
    let split = (values.len() as f64 * 0.8) as usize;
    let early_mean = values[..split].iter().sum::<f64>() / split as f64;
    let late_mean = values[split..].iter().sum::<f64>() / (values.len() - split) as f64;
    let diff_pct = if early_mean.abs() > 0.0 {
        (late_mean - early_mean) / early_mean.abs() * 100.0
    } else if late_mean > 0.0 { 100.0 } else { -100.0 };

    if diff_pct > 5.0 { Trend::Bullish }
    else if diff_pct < -5.0 { Trend::Bearish }
    else { Trend::Neutral }
}

/// Detect price trend from close prices.
fn price_trend(closes: &[f64]) -> Trend {
    determine_trend(closes)
}
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_split_volume_bullish_candle() {
        // Close at high → 100% buy
        let c = make_candle(100.0, 110.0, 90.0, 110.0, 1000.0);
        let (buy, sell) = split_volume(&c);
        assert!((buy - 1000.0).abs() < 0.01);
        assert!((sell - 0.0).abs() < 0.01);
    }

    #[test]
    fn test_split_volume_bearish_candle() {
        // Close at low → 0% buy
        let c = make_candle(100.0, 110.0, 90.0, 90.0, 1000.0);
        let (buy, sell) = split_volume(&c);
        assert!((buy - 0.0).abs() < 0.01);
        assert!((sell - 1000.0).abs() < 0.01);
    }

    #[test]
    fn test_split_volume_doji() {
        // High == Low → 50/50
        let c = make_candle(100.0, 100.0, 100.0, 100.0, 1000.0);
        let (buy, sell) = split_volume(&c);
        assert!((buy - 500.0).abs() < 0.01);
        assert!((sell - 500.0).abs() < 0.01);
    }

    #[test]
    fn test_split_volume_midpoint() {
        // Close at midpoint → 50/50
        let c = make_candle(100.0, 110.0, 90.0, 100.0, 1000.0);
        let (buy, sell) = split_volume(&c);
        assert!((buy - 500.0).abs() < 0.01);
        assert!((sell - 500.0).abs() < 0.01);
    }

    #[test]
    fn test_classify_spike_levels() {
        assert_eq!(classify_spike(600.0), SpikeLevel::Extreme);
        assert_eq!(classify_spike(300.0), SpikeLevel::High);
        assert_eq!(classify_spike(150.0), SpikeLevel::Moderate);
        assert_eq!(classify_spike(50.0), SpikeLevel::Normal);
        // Boundary values
        assert_eq!(classify_spike(500.1), SpikeLevel::Extreme);
        assert_eq!(classify_spike(200.1), SpikeLevel::High);
        assert_eq!(classify_spike(100.1), SpikeLevel::Moderate);
        assert_eq!(classify_spike(100.0), SpikeLevel::Normal);
    }

    #[test]
    fn test_detect_spike_normal_volume() {
        // 50 candles with volume=100, last candle volume=100 → no spike
        let mut candles = vec![make_candle(100.0, 110.0, 90.0, 105.0, 100.0); 50];
        candles.push(make_candle(100.0, 110.0, 90.0, 105.0, 100.0));
        let spike = detect_spike(&candles, "BTC", "15m", 43000.0).unwrap();
        assert_eq!(spike.spike_level, SpikeLevel::Normal);
        assert!(!spike.is_significant);
    }

    #[test]
    fn test_detect_spike_extreme() {
        // 50 candles with volume=100, last candle volume=1000 → 900% spike
        let mut candles = vec![make_candle(100.0, 110.0, 90.0, 105.0, 100.0); 50];
        candles.push(make_candle(100.0, 110.0, 90.0, 105.0, 1000.0));
        let spike = detect_spike(&candles, "BTC", "15m", 43000.0).unwrap();
        assert_eq!(spike.spike_level, SpikeLevel::Extreme);
        assert!(spike.is_significant);
        assert!(spike.volume_usd > 0.0);
    }

    #[test]
    fn test_detect_spike_insufficient_data() {
        let candles = vec![make_candle(100.0, 110.0, 90.0, 105.0, 100.0); 5];
        assert!(detect_spike(&candles, "BTC", "15m", 43000.0).is_none());
    }

    #[test]
    fn test_cvd_bullish() {
        // All candles close at high → all buy → CVD increasing → BULLISH
        let candles: Vec<Ohlcv> = (0..50).map(|_| {
            make_candle(100.0, 110.0, 90.0, 110.0, 100.0)
        }).collect();
        let cvd = calculate_cvd(&candles, "BTC", "15m", 43000.0).unwrap();
        assert_eq!(cvd.cvd_trend, Trend::Bullish);
        assert!(cvd.current_cvd > 0.0);
    }

    #[test]
    fn test_cvd_bearish() {
        // All candles close at low → all sell → CVD decreasing → BEARISH
        let candles: Vec<Ohlcv> = (0..50).map(|_| {
            make_candle(100.0, 110.0, 90.0, 90.0, 100.0)
        }).collect();
        let cvd = calculate_cvd(&candles, "BTC", "15m", 43000.0).unwrap();
        assert_eq!(cvd.cvd_trend, Trend::Bearish);
        assert!(cvd.current_cvd < 0.0);
    }

    #[test]
    fn test_cvd_divergence_detection() {
        // Price going up (close increasing) but CVD going down (close near low)
        let candles: Vec<Ohlcv> = (0..50).map(|i| {
            let base = 100.0 + i as f64; // price trending up
            // But close near low = bearish volume
            make_candle(base, base + 10.0, base - 10.0, base - 8.0, 100.0)
        }).collect();
        let cvd = calculate_cvd(&candles, "BTC", "15m", 43000.0).unwrap();
        // Price trend is bullish, CVD trend is bearish → divergence
        assert!(cvd.divergence_detected);
    }

    #[test]
    fn test_cvd_empty_data() {
        assert!(calculate_cvd(&[], "BTC", "15m", 43000.0).is_none());
    }

    // Helper
    fn make_candle(open: f64, high: f64, low: f64, close: f64, volume: f64) -> Ohlcv {
        Ohlcv { timestamp: chrono::Utc::now(), open, high, low, close, volume }
    }
}
```

## Exit Criteria

- [ ] `split_volume` handles bullish (close=high), bearish (close=low), doji (high=low), midpoint
- [ ] `classify_spike` boundary values correct (100 is Normal, 100.1 is Moderate, etc.)
- [ ] `detect_spike` returns None for <20 candles
- [ ] `detect_spike` returns Normal for average volume
- [ ] `detect_spike` returns Extreme for 10x volume
- [ ] `calculate_cvd` returns Bullish trend for all-buy candles
- [ ] `calculate_cvd` returns Bearish trend for all-sell candles
- [ ] Divergence detected when price trend and CVD trend oppose
- [ ] All 12 tests pass
- [ ] Zero async code in this module
