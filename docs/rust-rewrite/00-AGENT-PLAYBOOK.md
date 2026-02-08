# Agent Playbook: Crypto-Bot Rust Rewrite

## Purpose

This playbook governs all AI agent work on the Rust rewrite of the crypto-bot. Every agent MUST read this file before writing any code.

---

## 1. Project Structure (Target)

```
crypto-bot/
├── Cargo.toml
├── Containerfile
├── .env.example
├── src/
│   ├── main.rs
│   ├── config.rs
│   ├── types.rs                    # All shared types/structs
│   ├── error.rs                    # Error types
│   ├── exchange/
│   │   ├── mod.rs                  # Exchange trait + ExchangeManager
│   │   ├── rate_limiter.rs
│   │   ├── binance.rs
│   │   ├── bybit.rs
│   │   ├── okx.rs
│   │   ├── gateio.rs
│   │   ├── bitget.rs
│   │   └── hyperliquid.rs
│   ├── analysis/
│   │   ├── mod.rs
│   │   ├── indicators.rs           # RSI, ATR, VWAP, Bollinger
│   │   ├── volume.rs               # Volume spike, CVD
│   │   ├── oi.rs                   # OI aggregation
│   │   ├── profile.rs              # Volume Profile, TPO
│   │   ├── session.rs              # LuxAlgo 4-session
│   │   └── sentiment.rs            # Sentiment scoring
│   ├── telegram/
│   │   ├── mod.rs                  # Bot setup, dispatch
│   │   ├── commands/
│   │   │   ├── mod.rs
│   │   │   ├── price.rs
│   │   │   ├── analysis.rs
│   │   │   ├── oi.rs
│   │   │   ├── profile.rs
│   │   │   ├── account.rs
│   │   │   └── help.rs
│   │   └── formatting.rs
│   ├── monitoring/
│   │   ├── mod.rs
│   │   ├── oi_detector.rs
│   │   ├── liquidation.rs
│   │   └── alerts.rs
│   └── db.rs
└── tests/
    ├── common/
    │   └── mod.rs                  # Test helpers, mock exchange
    ├── unit/
    │   ├── indicators_test.rs
    │   ├── volume_test.rs
    │   ├── oi_test.rs
    │   ├── profile_test.rs
    │   ├── sentiment_test.rs
    │   ├── formatting_test.rs
    │   └── config_test.rs
    ├── integration/
    │   ├── exchange_test.rs
    │   ├── telegram_test.rs
    │   └── monitoring_test.rs
    └── fixtures/
        ├── ohlcv_btc_15m.json
        ├── ohlcv_btc_1h.json
        ├── ticker_btc.json
        ├── oi_binance.json
        ├── oi_multi_exchange.json
        └── positions_sample.json
```

---

## 2. Mandatory Agent Rules

### 2.1 Before Writing ANY Code

1. Read the relevant spec in `docs/rust-rewrite/specs/`
2. Read `src/types.rs` to understand shared types
3. Read `src/error.rs` to understand error types
4. Check `Cargo.toml` for available dependencies
5. Check if dependent modules exist (see dependency graph in Section 5)

### 2.2 Code Style

```rust
// MANDATORY: All public functions have doc comments
/// Fetches the 24-hour ticker for a symbol.
///
/// # Errors
/// Returns `ExchangeError::ApiError` if the API request fails.
/// Returns `ExchangeError::ParseError` if the response cannot be deserialized.
pub async fn fetch_ticker(&self, symbol: &str) -> Result<Ticker> {
    // ...
}
```

- Use `anyhow::Result` in `main.rs` and command handlers (application boundary)
- Use `thiserror` for library-level errors in modules
- All async functions use `tokio`
- No `unwrap()` or `expect()` in production code. Use `?` operator
- `unwrap()` is ONLY allowed in tests
- Use `tracing::info!`, `tracing::error!`, `tracing::debug!` (never `println!`)
- Use `rust_decimal::Decimal` for financial calculations that require precision
- Use `f64` for technical indicators where floating point is acceptable
- All config values come from `Config` struct (no raw `env::var` calls in modules)

### 2.3 Error Handling Convention

```rust
// In src/error.rs — define module-specific errors
#[derive(Debug, thiserror::Error)]
pub enum ExchangeError {
    #[error("API request failed: {0}")]
    ApiError(#[from] reqwest::Error),

    #[error("Failed to parse response from {exchange}: {message}")]
    ParseError { exchange: String, message: String },

    #[error("Rate limit exceeded for {exchange}")]
    RateLimited { exchange: String },

    #[error("Symbol not found: {0}")]
    SymbolNotFound(String),
}

// In command handlers — convert to user-friendly messages
match result {
    Ok(data) => format_response(data),
    Err(e) => {
        tracing::error!("Command failed: {e:#}");
        bot.send_message(chat_id, "Failed to fetch data. Try again.").await?;
    }
}
```

### 2.4 Testing Convention

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // Unit tests: test pure functions with known inputs
    #[test]
    fn test_calculate_rsi_overbought() {
        let closes = vec![/* 15 values trending up */];
        let rsi = calculate_rsi(&closes, 14).unwrap();
        assert!(rsi > 70.0, "RSI should be overbought, got {rsi}");
    }

    // Async tests: use tokio
    #[tokio::test]
    async fn test_fetch_ticker_binance() {
        let client = BinanceClient::new_for_test();
        let ticker = client.fetch_ticker("BTCUSDT").await.unwrap();
        assert!(ticker.price > 0.0);
        assert!(ticker.volume_24h > 0.0);
    }
}
```

### 2.5 Commit Convention

Every agent commit MUST:
1. Compile: `cargo build` passes
2. Lint: `cargo clippy -- -D warnings` passes
3. Format: `cargo fmt --check` passes
4. Tests: `cargo test` passes (all existing tests)
5. Message format: `feat(module): short description` or `fix(module): short description`

### 2.6 File Size Limits

- No file > 500 lines. If approaching, split into sub-modules.
- No function > 50 lines. Extract helpers.
- No more than 5 parameters per function. Use a config/options struct.

---

## 3. Dependency Versions (Pinned)

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
teloxide = { version = "0.17", features = ["macros"] }
reqwest = { version = "0.13", features = ["json", "rustls-tls"] }
tokio-tungstenite = { version = "0.26", features = ["rustls-tls-native-roots"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sqlx = { version = "0.8", features = ["runtime-tokio", "sqlite"] }
ta = "0.5"
hmac = "0.12"
sha2 = "0.10"
hex = "0.4"
dotenvy = "0.15"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
anyhow = "1"
thiserror = "2"
chrono = { version = "0.4", features = ["serde"] }
url = "2"
rust_decimal = { version = "1", features = ["serde-with-str"] }

[dev-dependencies]
wiremock = "0.6"
tokio-test = "0.4"
approx = "0.5"
serde_json = "1"
```

---

## 4. Environment Variables Contract

Agents MUST NOT hardcode any of these. All values load through `Config` struct.

| Variable | Type | Required | Default | Used By |
|----------|------|----------|---------|---------|
| `TELEGRAM_BOT_TOKEN` | String | YES | - | telegram/ |
| `TELEGRAM_CHAT_ID` | String | NO | "" | telegram/ |
| `BINANCE_API_KEY` | String | NO | "" | exchange/binance |
| `BINANCE_SECRET_KEY` | String | NO | "" | exchange/binance |
| `BINANCE_TESTNET` | bool | NO | false | exchange/binance |
| `BYBIT_API_KEY` | String | NO | "" | exchange/bybit |
| `BYBIT_SECRET_KEY` | String | NO | "" | exchange/bybit |
| `BYBIT_TESTNET` | bool | NO | false | exchange/bybit |
| `DATABASE_URL` | String | NO | "sqlite:data/bot.db" | db |
| `LOG_LEVEL` | String | NO | "info" | main |
| `OI_MONITOR_INTERVAL_SECS` | u64 | NO | 300 | monitoring/ |
| `ALERT_RATE_LIMIT_SECS` | u64 | NO | 60 | monitoring/alerts |

---

## 5. Module Dependency Graph

```
                    main.rs
                   /   |   \
                  /    |    \
           config.rs  types.rs  error.rs    ← LAYER 0 (no deps)
              |         |         |
              v         v         v
           exchange/mod.rs                   ← LAYER 1 (depends on L0)
           /   |    |    |   \    \
     binance bybit okx gateio bitget hyper   ← LAYER 2 (depends on L1)
              |
              v
         analysis/mod.rs                     ← LAYER 3 (depends on L1)
        / |    |     |    \
  indicators volume oi profile sentiment     ← LAYER 4 (depends on L3)
              |
              v
         telegram/mod.rs                     ← LAYER 5 (depends on L3, L4)
        / |    |     |    \
   price analysis oi profile account help    ← LAYER 6
              |
              v
         monitoring/mod.rs                   ← LAYER 5 (depends on L3, L4)
        / |         \
  oi_det liquidation alerts                  ← LAYER 6
              |
              v
           db.rs                             ← LAYER 1 (depends on L0)
```

**CRITICAL**: Agents MUST build bottom-up. Never write Layer N+1 before Layer N compiles and tests pass.

---

## 6. Spec Execution Order

Agents execute specs in this EXACT order. Each spec is in `docs/rust-rewrite/specs/`.

| Order | Spec File | Depends On | Estimated LOC |
|-------|-----------|------------|---------------|
| 1 | `S00-project-setup.md` | Nothing | ~100 |
| 2 | `S01-types-and-errors.md` | S00 | ~400 |
| 3 | `S02-config.md` | S01 | ~150 |
| 4 | `S03-exchange-trait.md` | S01, S02 | ~200 |
| 5 | `S04-binance.md` | S03 | ~450 |
| 6 | `S05-bybit.md` | S03 | ~350 |
| 7 | `S06-okx.md` | S03 | ~300 |
| 8 | `S07-gateio.md` | S03 | ~300 |
| 9 | `S08-bitget.md` | S03 | ~300 |
| 10 | `S09-hyperliquid.md` | S03 | ~250 |
| 11 | `S10-indicators.md` | S01 | ~300 |
| 12 | `S11-volume-cvd.md` | S01, S10 | ~350 |
| 13 | `S12-oi-aggregator.md` | S03, S04-S09 | ~300 |
| 14 | `S13-volume-profile.md` | S01, S10 | ~350 |
| 15 | `S14-session-volume.md` | S01 | ~200 |
| 16 | `S15-sentiment.md` | S10, S11 | ~200 |
| 17 | `S16-formatting.md` | S01 | ~300 |
| 18 | `S17-telegram-bot.md` | S02, S16, S10-S15 | ~500 |
| 19 | `S18-database.md` | S01, S02 | ~200 |
| 20 | `S19-monitoring.md` | S12, S18 | ~350 |
| 21 | `S20-main-entrypoint.md` | ALL | ~150 |
| 22 | `S21-containerfile.md` | S20 | ~50 |

**Parallelizable groups:**
- S04-S09 (all exchange clients) can run in parallel after S03
- S10, S14, S16, S18 can run in parallel after S01
- S11, S13 can run after S10

---

## 7. Validation Protocol

After EVERY spec completion, agent MUST run:

```bash
# GATE 1: Compiles
cargo build 2>&1 | tail -5
# MUST show: "Finished" with no errors

# GATE 2: Clippy clean
cargo clippy -- -D warnings 2>&1 | tail -5
# MUST show: no warnings

# GATE 3: Formatted
cargo fmt --check
# MUST show: no output (already formatted)

# GATE 4: Tests pass
cargo test 2>&1 | tail -10
# MUST show: "test result: ok" with 0 failures

# GATE 5: No secrets
grep -rn "sk-\|ghp_\|xox[bps]-\|AKIA" src/ tests/ Cargo.toml || echo "CLEAN"
# MUST show: "CLEAN"
```

If ANY gate fails, the agent MUST fix before proceeding to the next spec.

---

## 8. How to Read a Spec

Every spec file follows this template:

```
# S{NN}-{module-name}

## Scope
What this module does. What it does NOT do.

## Dependencies
Which specs must be complete before this one.

## Files to Create/Modify
Exact file paths.

## Types
Exact Rust struct/enum definitions to implement.

## Functions
Exact function signatures with doc comments.

## Business Logic
Algorithms, formulas, edge cases.

## Tests
Exact test functions with inputs and expected outputs.

## Exit Criteria
Checklist that MUST all be true when done.
```

Agents: implement EXACTLY what the spec says. Do not add features. Do not "improve" the design. Do not skip tests.
