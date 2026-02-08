# S02 — Configuration

## Scope
Load all environment variables into a typed `Config` struct. This is the ONLY place that reads env vars. All other modules receive config by reference.

## Dependencies
- S00, S01

## Files to Create/Modify

### `src/config.rs`

```rust
use std::env;
use std::collections::HashSet;

/// Application configuration loaded from environment variables.
/// This is the single source of truth for all config values.
#[derive(Debug, Clone)]
pub struct Config {
    // Telegram
    pub telegram_bot_token: String,
    pub authorized_chat_ids: HashSet<i64>,

    // Exchanges
    pub binance_api_key: Option<String>,
    pub binance_secret_key: Option<String>,
    pub binance_testnet: bool,
    pub bybit_api_key: Option<String>,
    pub bybit_secret_key: Option<String>,
    pub bybit_testnet: bool,

    // Database
    pub database_url: String,

    // Logging
    pub log_level: String,

    // Monitoring
    pub oi_monitor_interval_secs: u64,
    pub alert_rate_limit_secs: u64,

    // Thresholds
    pub thresholds: Thresholds,
}

#[derive(Debug, Clone)]
pub struct Thresholds {
    pub liquidation: LiquidationThresholds,
    pub oi_explosion: OiExplosionThresholds,
    pub alert_rate: AlertRateLimits,
}

#[derive(Debug, Clone)]
pub struct LiquidationThresholds {
    pub btc_single_usd: f64,       // default: 100_000
    pub eth_single_usd: f64,       // default: 50_000
    pub sol_single_usd: f64,       // default: 25_000
    pub cascade_count: u32,         // default: 5
    pub cascade_window_secs: u64,   // default: 30
}

#[derive(Debug, Clone)]
pub struct OiExplosionThresholds {
    pub btc_change_pct: f64,       // default: 15.0
    pub eth_change_pct: f64,       // default: 18.0
    pub sol_change_pct: f64,       // default: 25.0
    pub time_window_mins: u64,     // default: 15
}

#[derive(Debug, Clone)]
pub struct AlertRateLimits {
    pub max_per_hour: u32,          // default: 10
    pub dedup_window_mins: u64,     // default: 5
    pub telegram_rate_per_sec: u32, // default: 30
}

impl Config {
    /// Load configuration from environment variables.
    /// Call `dotenvy::dotenv().ok()` before this.
    pub fn from_env() -> Result<Self, ConfigError> {
        // Implementation: read each env var, apply defaults, validate
    }

    /// Returns the liquidation threshold for a given base symbol.
    pub fn liquidation_threshold(&self, symbol: &str) -> f64 {
        match symbol {
            "BTC" => self.thresholds.liquidation.btc_single_usd,
            "ETH" => self.thresholds.liquidation.eth_single_usd,
            "SOL" => self.thresholds.liquidation.sol_single_usd,
            _ => self.thresholds.liquidation.sol_single_usd, // default to smallest
        }
    }

    /// Returns the OI explosion threshold % for a given base symbol.
    pub fn oi_threshold_pct(&self, symbol: &str) -> f64 {
        match symbol {
            "BTC" => self.thresholds.oi_explosion.btc_change_pct,
            "ETH" => self.thresholds.oi_explosion.eth_change_pct,
            "SOL" => self.thresholds.oi_explosion.sol_change_pct,
            _ => self.thresholds.oi_explosion.sol_change_pct,
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("Required environment variable {name} is not set")]
    Missing { name: String },

    #[error("Invalid value for {name}: {value} — {reason}")]
    Invalid { name: String, value: String, reason: String },
}
```

### Helper function for reading env vars

```rust
fn env_required(name: &str) -> Result<String, ConfigError> {
    env::var(name).map_err(|_| ConfigError::Missing { name: name.to_string() })
}

fn env_optional(name: &str) -> Option<String> {
    env::var(name).ok().filter(|v| !v.is_empty())
}

fn env_or_default<T: std::str::FromStr>(name: &str, default: T) -> T {
    env::var(name)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}

fn env_bool(name: &str, default: bool) -> bool {
    env::var(name)
        .ok()
        .map(|v| matches!(v.to_lowercase().as_str(), "true" | "1" | "yes"))
        .unwrap_or(default)
}
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_missing_required_token() {
        // Clear env to ensure TELEGRAM_BOT_TOKEN is not set
        std::env::remove_var("TELEGRAM_BOT_TOKEN");
        let result = Config::from_env();
        assert!(result.is_err());
        let err = result.unwrap_err().to_string();
        assert!(err.contains("TELEGRAM_BOT_TOKEN"));
    }

    #[test]
    fn test_config_defaults_applied() {
        std::env::set_var("TELEGRAM_BOT_TOKEN", "test_token_123");
        let config = Config::from_env().unwrap();
        assert_eq!(config.database_url, "sqlite:data/bot.db");
        assert_eq!(config.log_level, "info");
        assert_eq!(config.oi_monitor_interval_secs, 300);
        assert_eq!(config.alert_rate_limit_secs, 60);
        assert!(!config.binance_testnet);
        std::env::remove_var("TELEGRAM_BOT_TOKEN");
    }

    #[test]
    fn test_config_chat_id_parsing() {
        std::env::set_var("TELEGRAM_BOT_TOKEN", "test_token_123");
        std::env::set_var("TELEGRAM_CHAT_ID", "123,456,789");
        let config = Config::from_env().unwrap();
        assert!(config.authorized_chat_ids.contains(&123));
        assert!(config.authorized_chat_ids.contains(&456));
        assert!(config.authorized_chat_ids.contains(&789));
        assert_eq!(config.authorized_chat_ids.len(), 3);
        std::env::remove_var("TELEGRAM_BOT_TOKEN");
        std::env::remove_var("TELEGRAM_CHAT_ID");
    }

    #[test]
    fn test_config_empty_chat_id_allows_all() {
        std::env::set_var("TELEGRAM_BOT_TOKEN", "test_token_123");
        std::env::remove_var("TELEGRAM_CHAT_ID");
        let config = Config::from_env().unwrap();
        assert!(config.authorized_chat_ids.is_empty());
        std::env::remove_var("TELEGRAM_BOT_TOKEN");
    }

    #[test]
    fn test_liquidation_threshold_lookup() {
        std::env::set_var("TELEGRAM_BOT_TOKEN", "test_token_123");
        let config = Config::from_env().unwrap();
        assert_eq!(config.liquidation_threshold("BTC"), 100_000.0);
        assert_eq!(config.liquidation_threshold("ETH"), 50_000.0);
        assert_eq!(config.liquidation_threshold("SOL"), 25_000.0);
        assert_eq!(config.liquidation_threshold("UNKNOWN"), 25_000.0);
        std::env::remove_var("TELEGRAM_BOT_TOKEN");
    }

    #[test]
    fn test_oi_threshold_lookup() {
        std::env::set_var("TELEGRAM_BOT_TOKEN", "test_token_123");
        let config = Config::from_env().unwrap();
        assert!((config.oi_threshold_pct("BTC") - 15.0).abs() < f64::EPSILON);
        assert!((config.oi_threshold_pct("ETH") - 18.0).abs() < f64::EPSILON);
        std::env::remove_var("TELEGRAM_BOT_TOKEN");
    }
}
```

## Exit Criteria

- [ ] `Config::from_env()` returns `Err` when `TELEGRAM_BOT_TOKEN` is missing
- [ ] All default values match the table in the playbook Section 4
- [ ] `authorized_chat_ids` correctly parses comma-separated IDs
- [ ] Empty/missing `TELEGRAM_CHAT_ID` results in empty set (allow all)
- [ ] `liquidation_threshold()` and `oi_threshold_pct()` return correct per-symbol values
- [ ] All 6 tests pass
- [ ] No `env::var()` calls exist outside `config.rs`
