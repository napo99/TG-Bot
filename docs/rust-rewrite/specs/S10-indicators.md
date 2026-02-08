# S10 — Technical Indicators

## Scope
Pure computation module. No I/O, no async. Takes OHLCV data, returns indicator values. Uses `ta` crate where possible, implements custom calculations where needed.

## Dependencies
- S01 (types: `Ohlcv`, `Indicators`)

## Files to Create

### `src/analysis/mod.rs`
```rust
pub mod indicators;
pub mod volume;
pub mod oi;
pub mod profile;
pub mod session;
pub mod sentiment;
```

### `src/analysis/indicators.rs`

```rust
use crate::types::{Ohlcv, Indicators};

/// Calculate RSI (Relative Strength Index) from close prices.
/// Uses Wilder's smoothing method.
/// Returns None if fewer than `period + 1` data points.
pub fn calculate_rsi(closes: &[f64], period: usize) -> Option<f64> {
    if closes.len() < period + 1 {
        return None;
    }
    // Algorithm:
    // 1. Calculate price changes: changes[i] = closes[i] - closes[i-1]
    // 2. Separate into gains and losses
    // 3. First average: simple mean of first `period` gains/losses
    // 4. Subsequent: smoothed = (prev_avg * (period-1) + current) / period
    // 5. RS = avg_gain / avg_loss
    // 6. RSI = 100 - (100 / (1 + RS))
    // Edge case: if avg_loss == 0, RSI = 100
}

/// Calculate VWAP (Volume Weighted Average Price) from OHLCV data.
/// Formula: Sum(typical_price * volume) / Sum(volume)
/// Typical price = (high + low + close) / 3
pub fn calculate_vwap(candles: &[Ohlcv]) -> Option<f64> {
    if candles.is_empty() {
        return None;
    }
    let (sum_pv, sum_v) = candles.iter().fold((0.0, 0.0), |(pv, v), c| {
        let tp = (c.high + c.low + c.close) / 3.0;
        (pv + tp * c.volume, v + c.volume)
    });
    if sum_v == 0.0 { None } else { Some(sum_pv / sum_v) }
}

/// Calculate ATR (Average True Range).
/// True Range = max(high-low, |high-prev_close|, |low-prev_close|)
/// ATR = Wilder's smoothed average of TR over `period`.
/// Returns None if fewer than `period + 1` data points.
pub fn calculate_atr(candles: &[Ohlcv], period: usize) -> Option<f64> {
    if candles.len() < period + 1 {
        return None;
    }
    // 1. Calculate true ranges
    // 2. First ATR = simple mean of first `period` true ranges
    // 3. Subsequent: atr = (prev_atr * (period-1) + current_tr) / period
}

/// Calculate Bollinger Bands.
/// Middle = SMA(close, period)
/// Upper = Middle + (multiplier * StdDev)
/// Lower = Middle - (multiplier * StdDev)
/// Returns (upper, middle, lower) or None if insufficient data.
pub fn calculate_bollinger_bands(
    closes: &[f64],
    period: usize,
    multiplier: f64,
) -> Option<(f64, f64, f64)> {
    if closes.len() < period {
        return None;
    }
    let window = &closes[closes.len() - period..];
    let mean = window.iter().sum::<f64>() / period as f64;
    let variance = window.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / period as f64;
    let std_dev = variance.sqrt();
    Some((mean + multiplier * std_dev, mean, mean - multiplier * std_dev))
}

/// Calculate volume ratio: current volume / average volume.
/// `lookback` is the number of periods for the average.
pub fn calculate_volume_ratio(volumes: &[f64], lookback: usize) -> Option<f64> {
    if volumes.len() < 2 || lookback == 0 {
        return None;
    }
    let current = *volumes.last()?;
    let avg_window = if volumes.len() > lookback + 1 {
        &volumes[volumes.len() - lookback - 1..volumes.len() - 1]
    } else {
        &volumes[..volumes.len() - 1]
    };
    let avg = avg_window.iter().sum::<f64>() / avg_window.len() as f64;
    if avg == 0.0 { None } else { Some(current / avg) }
}

/// Calculate 24h volatility as percentage standard deviation of returns.
pub fn calculate_volatility(closes: &[f64]) -> Option<f64> {
    if closes.len() < 2 {
        return None;
    }
    let returns: Vec<f64> = closes.windows(2)
        .map(|w| (w[1] / w[0] - 1.0) * 100.0)
        .collect();
    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / returns.len() as f64;
    Some(variance.sqrt())
}

/// Calculate all indicators from OHLCV data.
pub fn calculate_all(candles: &[Ohlcv]) -> Indicators {
    let closes: Vec<f64> = candles.iter().map(|c| c.close).collect();
    let volumes: Vec<f64> = candles.iter().map(|c| c.volume).collect();

    Indicators {
        rsi_14: calculate_rsi(&closes, 14),
        vwap: calculate_vwap(candles),
        atr_14: calculate_atr(candles, 14),
        bb_upper: calculate_bollinger_bands(&closes, 20, 2.0).map(|b| b.0),
        bb_middle: calculate_bollinger_bands(&closes, 20, 2.0).map(|b| b.1),
        bb_lower: calculate_bollinger_bands(&closes, 20, 2.0).map(|b| b.2),
        volatility_24h: calculate_volatility(&closes),
    }
}
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    // Known RSI test vector:
    // 14-period RSI on closes that are strictly increasing by 1.0
    // gains = [1,1,1,...,1] (14 values), losses = [0,0,...,0]
    // RS = 1.0/0.0 → RSI = 100
    #[test]
    fn test_rsi_all_gains() {
        let closes: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let rsi = calculate_rsi(&closes, 14).unwrap();
        assert_relative_eq!(rsi, 100.0, epsilon = 0.01);
    }

    // All losses → RSI = 0
    #[test]
    fn test_rsi_all_losses() {
        let closes: Vec<f64> = (0..20).map(|i| 120.0 - i as f64).collect();
        let rsi = calculate_rsi(&closes, 14).unwrap();
        assert_relative_eq!(rsi, 0.0, epsilon = 0.01);
    }

    // Alternating gains/losses → RSI ≈ 50
    #[test]
    fn test_rsi_neutral() {
        let mut closes = vec![100.0];
        for i in 1..30 {
            if i % 2 == 0 { closes.push(closes[i-1] + 1.0); }
            else { closes.push(closes[i-1] - 1.0); }
        }
        let rsi = calculate_rsi(&closes, 14).unwrap();
        assert!(rsi > 40.0 && rsi < 60.0, "RSI should be near 50, got {rsi}");
    }

    #[test]
    fn test_rsi_insufficient_data() {
        let closes = vec![100.0; 10]; // need 15 for period=14
        assert!(calculate_rsi(&closes, 14).is_none());
    }

    #[test]
    fn test_vwap_simple() {
        // Two candles: TP1 = (110+90+100)/3 = 100, vol=10
        //              TP2 = (120+80+110)/3 = 103.33, vol=20
        // VWAP = (100*10 + 103.33*20) / (10+20) = 3066.6/30 = 102.22
        let candles = vec![
            make_ohlcv(100.0, 110.0, 90.0, 100.0, 10.0),
            make_ohlcv(100.0, 120.0, 80.0, 110.0, 20.0),
        ];
        let vwap = calculate_vwap(&candles).unwrap();
        assert_relative_eq!(vwap, 102.222, epsilon = 0.01);
    }

    #[test]
    fn test_vwap_empty() {
        assert!(calculate_vwap(&[]).is_none());
    }

    #[test]
    fn test_atr_known_values() {
        // 3 candles: need period=2
        // TR1 = max(10, |110-100|, |90-100|) = 20 (high-low=20)
        // wait — first candle has no prev_close so TR = high - low
        // For simplicity test with period=2 and 4 candles
        let candles = vec![
            make_ohlcv(100.0, 110.0, 90.0, 105.0, 100.0),  // TR=20
            make_ohlcv(105.0, 115.0, 95.0, 110.0, 100.0),  // TR=max(20,|115-105|,|95-105|)=20
            make_ohlcv(110.0, 125.0, 100.0, 120.0, 100.0), // TR=max(25,|125-110|,|100-110|)=25
        ];
        let atr = calculate_atr(&candles, 2).unwrap();
        // First ATR (period=2): mean of TR[1], TR[2] — but algorithm uses Wilder's smoothing
        // ATR_first = (20 + 25) / 2 = 22.5 ... then smoothed
        assert!(atr > 0.0);
    }

    #[test]
    fn test_bollinger_bands() {
        // 20 identical values → std_dev = 0 → bands collapse to price
        let closes = vec![100.0; 25];
        let (upper, middle, lower) = calculate_bollinger_bands(&closes, 20, 2.0).unwrap();
        assert_relative_eq!(middle, 100.0, epsilon = 0.001);
        assert_relative_eq!(upper, 100.0, epsilon = 0.001);
        assert_relative_eq!(lower, 100.0, epsilon = 0.001);
    }

    #[test]
    fn test_bollinger_bands_with_spread() {
        // Known: [98, 99, 100, 101, 102] period=5
        // Mean = 100, StdDev = sqrt(2) ≈ 1.414
        // Upper = 100 + 2*1.414 = 102.828
        // Lower = 100 - 2*1.414 = 97.172
        let closes = vec![98.0, 99.0, 100.0, 101.0, 102.0];
        let (upper, middle, lower) = calculate_bollinger_bands(&closes, 5, 2.0).unwrap();
        assert_relative_eq!(middle, 100.0, epsilon = 0.001);
        assert_relative_eq!(upper, 102.828, epsilon = 0.01);
        assert_relative_eq!(lower, 97.172, epsilon = 0.01);
    }

    #[test]
    fn test_volume_ratio() {
        let volumes = vec![100.0, 100.0, 100.0, 100.0, 200.0];
        let ratio = calculate_volume_ratio(&volumes, 4).unwrap();
        assert_relative_eq!(ratio, 2.0, epsilon = 0.01);
    }

    #[test]
    fn test_volatility_constant_price() {
        let closes = vec![100.0; 20];
        let vol = calculate_volatility(&closes).unwrap();
        assert_relative_eq!(vol, 0.0, epsilon = 0.001);
    }

    #[test]
    fn test_calculate_all_returns_populated() {
        let candles = generate_sample_ohlcv(100); // helper
        let ind = calculate_all(&candles);
        assert!(ind.rsi_14.is_some());
        assert!(ind.vwap.is_some());
        assert!(ind.atr_14.is_some());
        assert!(ind.bb_upper.is_some());
    }

    // ── Test Helpers ──

    fn make_ohlcv(open: f64, high: f64, low: f64, close: f64, volume: f64) -> Ohlcv {
        Ohlcv {
            timestamp: chrono::Utc::now(),
            open, high, low, close, volume,
        }
    }

    fn generate_sample_ohlcv(n: usize) -> Vec<Ohlcv> {
        (0..n).map(|i| {
            let base = 100.0 + (i as f64 * 0.1).sin() * 10.0;
            make_ohlcv(base, base + 2.0, base - 2.0, base + 0.5, 1000.0 + i as f64)
        }).collect()
    }
}
```

## Exit Criteria

- [ ] `calculate_rsi` returns 100 for all-gain, 0 for all-loss, ~50 for neutral
- [ ] `calculate_rsi` returns None for insufficient data
- [ ] `calculate_vwap` computes correct weighted average
- [ ] `calculate_atr` returns positive values for volatile data
- [ ] `calculate_bollinger_bands` collapses to price for constant input
- [ ] `calculate_bollinger_bands` produces correct spread for known input
- [ ] `calculate_volume_ratio` returns 2.0 when current is 2x average
- [ ] `calculate_volatility` returns 0.0 for constant prices
- [ ] `calculate_all` populates all fields for 100+ candles
- [ ] All 12 tests pass
- [ ] No floating point comparisons use `==` (use `approx` crate)
- [ ] Zero async code in this module (pure computation)
