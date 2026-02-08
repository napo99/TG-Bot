# S20 — Main Entrypoint

## Scope
Wire everything together in `main.rs`. Load config, init services, start bot + monitoring.

## Dependencies
- ALL previous specs

## Files to Modify

### `src/main.rs`

```rust
mod config;
mod error;
mod types;
mod exchange;
mod analysis;
mod telegram;
mod monitoring;
mod db;

use std::sync::Arc;
use tokio::sync::mpsc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. Load .env
    dotenvy::dotenv().ok();

    // 2. Load config
    let config = Arc::new(config::Config::from_env()?);

    // 3. Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(format!("crypto_bot={}", config.log_level).parse()?),
        )
        .init();

    tracing::info!("crypto-bot v{} starting", env!("CARGO_PKG_VERSION"));

    // 4. Initialize HTTP client (shared across all exchanges)
    let http = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    // 5. Initialize exchange manager
    let exchanges = Arc::new(exchange::ExchangeManager::new(&config, http));

    // 6. Initialize database
    let db = Arc::new(db::Db::connect(&config.database_url).await?);

    // 7. Create alert channel
    let (alert_tx, alert_rx) = mpsc::channel(100);

    // 8. Start monitoring tasks
    let monitor_handles = monitoring::start(
        config.clone(),
        exchanges.clone(),
        db.clone(),
        alert_tx,
    ).await;

    // 9. Start Telegram bot (blocks until shutdown)
    let bot_state = Arc::new(telegram::BotState {
        config: config.clone(),
        exchanges: exchanges.clone(),
    });
    telegram::run(bot_state).await?;

    // 10. Cleanup
    for handle in monitor_handles {
        handle.abort();
    }

    tracing::info!("crypto-bot shutdown complete");
    Ok(())
}
```

## Tests

```rust
// Integration test: verify the binary starts and stops cleanly
// This is tested via `cargo build` + the containerfile smoke test
```

## Exit Criteria

- [ ] `cargo build --release` succeeds
- [ ] Binary starts, prints version, loads config
- [ ] Missing TELEGRAM_BOT_TOKEN produces clear error
- [ ] Ctrl+C triggers graceful shutdown
- [ ] No compiler warnings
