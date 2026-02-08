# S03 — Exchange Trait & Manager

## Scope
Define the `Exchange` trait that all exchange clients implement, and the `ExchangeManager` that orchestrates concurrent calls across exchanges.

Does NOT implement any specific exchange. That's S04-S09.

## Dependencies
- S01 (types), S02 (config)

## Files to Create

### `src/exchange/mod.rs`

```rust
pub mod rate_limiter;
pub mod binance;
pub mod bybit;
pub mod okx;
pub mod gateio;
pub mod bitget;
pub mod hyperliquid;

use crate::types::*;
use crate::error::ExchangeError;
use crate::config::Config;
use std::sync::Arc;

/// Trait that all exchange implementations must satisfy.
/// All methods are async and return Result.
#[async_trait::async_trait]
pub trait Exchange: Send + Sync {
    /// Human-readable exchange name (e.g., "binance", "bybit")
    fn name(&self) -> &str;

    /// Fetch 24h ticker for a symbol.
    /// `symbol` is exchange-specific format (e.g., "BTCUSDT" for Binance).
    async fn fetch_ticker(&self, symbol: &str) -> Result<Ticker, ExchangeError>;

    /// Fetch OHLCV candles.
    /// `timeframe`: "1m", "5m", "15m", "1h", "4h", "1d"
    /// `limit`: number of candles (max 500)
    async fn fetch_ohlcv(
        &self,
        symbol: &str,
        timeframe: &str,
        limit: u32,
    ) -> Result<Vec<Ohlcv>, ExchangeError>;

    /// Fetch open interest for a futures symbol.
    async fn fetch_open_interest(&self, symbol: &str) -> Result<f64, ExchangeError>;

    /// Fetch current funding rate for a futures symbol.
    async fn fetch_funding_rate(&self, symbol: &str) -> Result<f64, ExchangeError>;

    /// Fetch account balance (requires API key).
    /// Returns empty vec if no API key configured.
    async fn fetch_balance(&self) -> Result<Vec<Balance>, ExchangeError>;

    /// Fetch open positions (requires API key).
    /// Returns empty vec if no API key configured.
    async fn fetch_positions(&self) -> Result<Vec<Position>, ExchangeError>;
}

/// Maps a base symbol (e.g., "BTC") to exchange-specific format.
pub struct SymbolMapper;

impl SymbolMapper {
    pub fn to_binance_usdt(base: &str) -> String { format!("{base}USDT") }
    pub fn to_binance_usdc(base: &str) -> String { format!("{base}USDC") }
    pub fn to_binance_inverse(base: &str) -> String { format!("{base}USD_PERP") }

    pub fn to_bybit_usdt(base: &str) -> String { format!("{base}USDT") }
    pub fn to_bybit_usdc(base: &str) -> String { format!("{base}USDC") }
    pub fn to_bybit_inverse(base: &str) -> String { format!("{base}USD") }

    pub fn to_okx_usdt(base: &str) -> String { format!("{base}-USDT-SWAP") }
    pub fn to_okx_usdc(base: &str) -> String { format!("{base}-USDC-SWAP") }
    pub fn to_okx_inverse(base: &str) -> String { format!("{base}-USD-SWAP") }

    pub fn to_gateio_usdt(base: &str) -> String { format!("{base}_USDT") }
    pub fn to_gateio_usdc(base: &str) -> String { format!("{base}_USDC") }
    pub fn to_gateio_inverse(base: &str) -> String { format!("{base}_USD") }

    pub fn to_bitget_usdt(base: &str) -> String { format!("{base}USDT_UMCBL") }
    pub fn to_bitget_usdc(base: &str) -> String { format!("{base}USDC_UMCBL") }
    pub fn to_bitget_inverse(base: &str) -> String { format!("{base}USD_DMCBL") }

    /// Returns all symbol variants for all exchanges for a base symbol.
    pub fn all_oi_symbols(base: &str) -> Vec<(&'static str, String, MarketType)> {
        vec![
            ("binance", Self::to_binance_usdt(base), MarketType::Usdt),
            ("binance", Self::to_binance_usdc(base), MarketType::Usdc),
            ("binance", Self::to_binance_inverse(base), MarketType::UsdInverse),
            ("bybit", Self::to_bybit_usdt(base), MarketType::Usdt),
            ("bybit", Self::to_bybit_usdc(base), MarketType::Usdc),
            ("bybit", Self::to_bybit_inverse(base), MarketType::UsdInverse),
            ("okx", Self::to_okx_usdt(base), MarketType::Usdt),
            ("okx", Self::to_okx_usdc(base), MarketType::Usdc),
            ("okx", Self::to_okx_inverse(base), MarketType::UsdInverse),
            ("gateio", Self::to_gateio_usdt(base), MarketType::Usdt),
            ("bitget", Self::to_bitget_usdt(base), MarketType::Usdt),
            ("bitget", Self::to_bitget_inverse(base), MarketType::UsdInverse),
        ]
    }
}

/// Manages all exchange clients and provides concurrent fetching.
pub struct ExchangeManager {
    exchanges: Vec<Arc<dyn Exchange>>,
    primary: Arc<dyn Exchange>,         // default exchange for single-symbol queries
}

impl ExchangeManager {
    /// Initialize all exchange clients from config.
    pub fn new(config: &Config, http: reqwest::Client) -> Self {
        // Build exchange clients based on available API keys
        // Primary = binance (always available, public data)
    }

    /// Get a specific exchange by name.
    pub fn get(&self, name: &str) -> Option<Arc<dyn Exchange>> {
        self.exchanges.iter().find(|e| e.name() == name).cloned()
    }

    /// Get the primary (default) exchange.
    pub fn primary(&self) -> &Arc<dyn Exchange> {
        &self.primary
    }

    /// Fetch ticker from primary exchange, with specified symbol format.
    pub async fn fetch_ticker(&self, symbol: &str) -> Result<Ticker, ExchangeError> {
        self.primary.fetch_ticker(symbol).await
    }

    /// Fetch OI from all exchanges concurrently for a base symbol.
    /// Returns results for each exchange (errors are logged, not propagated).
    pub async fn fetch_all_oi(&self, base_symbol: &str) -> Vec<ExchangeOi> {
        // Use tokio::join! or futures::join_all to fetch concurrently
        // Log errors per exchange, don't fail the whole request
    }

    /// Fetch combined spot + perp data for a base symbol.
    pub async fn fetch_combined_price(
        &self,
        base_symbol: &str,
    ) -> Result<CombinedPrice, ExchangeError> {
        // Fetch spot ticker + perp ticker concurrently from primary exchange
        // Fetch 15m candles for enhanced metrics
        // Calculate delta, ATR
    }
}
```

### `src/exchange/rate_limiter.rs`

```rust
use std::collections::VecDeque;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;

/// Per-exchange rate limiter using sliding window.
pub struct RateLimiter {
    window: Duration,
    max_requests: u32,
    timestamps: Mutex<VecDeque<Instant>>,
}

impl RateLimiter {
    pub fn new(max_requests: u32, window: Duration) -> Self {
        Self {
            window,
            max_requests,
            timestamps: Mutex::new(VecDeque::new()),
        }
    }

    /// Wait until a request can be made within the rate limit.
    /// Returns immediately if under the limit.
    pub async fn acquire(&self) {
        loop {
            let mut ts = self.timestamps.lock().await;
            let now = Instant::now();
            // Remove timestamps outside window
            while ts.front().map_or(false, |t| now.duration_since(*t) > self.window) {
                ts.pop_front();
            }
            if (ts.len() as u32) < self.max_requests {
                ts.push_back(now);
                return;
            }
            // Wait until oldest timestamp exits the window
            let wait = self.window - now.duration_since(*ts.front().unwrap());
            drop(ts);
            tokio::time::sleep(wait).await;
        }
    }
}
```

## Async Trait Note

Add to `Cargo.toml`:
```toml
async-trait = "0.1"
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_symbol_mapper_binance() {
        assert_eq!(SymbolMapper::to_binance_usdt("BTC"), "BTCUSDT");
        assert_eq!(SymbolMapper::to_binance_usdc("ETH"), "ETHUSDC");
        assert_eq!(SymbolMapper::to_binance_inverse("BTC"), "BTCUSD_PERP");
    }

    #[test]
    fn test_symbol_mapper_okx() {
        assert_eq!(SymbolMapper::to_okx_usdt("BTC"), "BTC-USDT-SWAP");
        assert_eq!(SymbolMapper::to_okx_inverse("ETH"), "ETH-USD-SWAP");
    }

    #[test]
    fn test_symbol_mapper_all_oi() {
        let symbols = SymbolMapper::all_oi_symbols("BTC");
        assert!(symbols.len() >= 12);
        // Verify each exchange is represented
        assert!(symbols.iter().any(|(e, _, _)| *e == "binance"));
        assert!(symbols.iter().any(|(e, _, _)| *e == "bybit"));
        assert!(symbols.iter().any(|(e, _, _)| *e == "okx"));
    }

    #[tokio::test]
    async fn test_rate_limiter_allows_under_limit() {
        let limiter = RateLimiter::new(5, Duration::from_secs(1));
        for _ in 0..5 {
            limiter.acquire().await; // Should not block
        }
    }

    #[tokio::test]
    async fn test_rate_limiter_blocks_over_limit() {
        let limiter = RateLimiter::new(2, Duration::from_millis(100));
        limiter.acquire().await;
        limiter.acquire().await;
        let start = Instant::now();
        limiter.acquire().await; // Should block ~100ms
        let elapsed = start.elapsed();
        assert!(elapsed >= Duration::from_millis(50)); // Some tolerance
    }
}
```

## Exit Criteria

- [ ] `Exchange` trait compiles with all 6 methods
- [ ] `SymbolMapper` correctly maps all 5 exchanges * 3 market types
- [ ] `ExchangeManager::new()` compiles (exchange clients can be stubs)
- [ ] `RateLimiter` correctly throttles concurrent requests
- [ ] All 5 tests pass
- [ ] No `async_trait` warnings from clippy
