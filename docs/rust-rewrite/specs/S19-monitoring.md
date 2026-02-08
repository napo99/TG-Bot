# S19 — Background Monitoring

## Scope
Background async tasks: OI explosion detection, liquidation monitoring (WebSocket), alert dispatch with priority queue and rate limiting.

## Dependencies
- S01 (types), S02 (config), S03 (ExchangeManager), S12 (OI aggregator), S18 (database)

## Files to Create

### `src/monitoring/mod.rs`

```rust
pub mod oi_detector;
pub mod liquidation;
pub mod alerts;

use crate::config::Config;
use crate::exchange::ExchangeManager;
use crate::db::Db;
use std::sync::Arc;
use tokio::sync::mpsc;

/// Start all background monitoring tasks.
/// Returns a JoinHandle for graceful shutdown.
pub async fn start(
    config: Arc<Config>,
    exchanges: Arc<ExchangeManager>,
    db: Arc<Db>,
    alert_tx: mpsc::Sender<Alert>,
) -> Vec<tokio::task::JoinHandle<()>> {
    let mut handles = vec![];

    // OI detector: polls every config.oi_monitor_interval_secs
    handles.push(tokio::spawn(
        oi_detector::run(config.clone(), exchanges.clone(), alert_tx.clone())
    ));

    // Liquidation monitor: WebSocket stream
    handles.push(tokio::spawn(
        liquidation::run(config.clone(), alert_tx.clone())
    ));

    // Alert dispatcher: processes alert queue, sends to Telegram
    handles.push(tokio::spawn(
        alerts::run(config.clone(), db, alert_tx)
    ));

    handles
}
```

### `src/monitoring/oi_detector.rs`

```rust
/// OI explosion detection loop.
///
/// Algorithm:
/// 1. Every `interval_secs`, fetch OI for monitored symbols
/// 2. Compare to previous snapshot
/// 3. If change_pct > threshold for symbol → create Alert
/// 4. Send alert to alert_tx channel
///
/// Monitored symbols: BTC, ETH, SOL, ADA, DOT, AVAX, MATIC, ATOM
pub async fn run(
    config: Arc<Config>,
    exchanges: Arc<ExchangeManager>,
    alert_tx: mpsc::Sender<Alert>,
) {
    let monitored = ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "ATOM"];
    let mut snapshots: HashMap<String, f64> = HashMap::new();

    loop {
        for symbol in &monitored {
            match fetch_current_oi(&exchanges, symbol).await {
                Ok(oi_usd) => {
                    if let Some(&prev) = snapshots.get(*symbol) {
                        let change_pct = ((oi_usd - prev) / prev) * 100.0;
                        let threshold = config.oi_threshold_pct(symbol);
                        if change_pct.abs() > threshold {
                            let alert = Alert {
                                id: format!("oi_{symbol}_{}", Utc::now().timestamp()),
                                priority: AlertPriority::High,
                                alert_type: "oi_explosion".to_string(),
                                symbol: symbol.to_string(),
                                message: format_oi_alert(symbol, change_pct, oi_usd),
                                created_at: Utc::now(),
                            };
                            let _ = alert_tx.send(alert).await;
                        }
                    }
                    snapshots.insert(symbol.to_string(), oi_usd);
                }
                Err(e) => tracing::warn!("OI fetch failed for {symbol}: {e}"),
            }
        }
        tokio::time::sleep(Duration::from_secs(config.oi_monitor_interval_secs)).await;
    }
}
```

### `src/monitoring/liquidation.rs`

```rust
/// WebSocket liquidation monitor.
///
/// Connects to Binance forceOrder stream:
///   wss://fstream.binance.com/ws/!forceOrder@arr
///
/// For each liquidation:
/// 1. Parse symbol, side, price, quantity
/// 2. Calculate USD value
/// 3. If value > threshold → create Alert
/// 4. Auto-reconnect with exponential backoff: [1, 2, 4, 8, 16] seconds
pub async fn run(
    config: Arc<Config>,
    alert_tx: mpsc::Sender<Alert>,
) {
    let url = "wss://fstream.binance.com/ws/!forceOrder@arr";
    let reconnect_delays = [1, 2, 4, 8, 16];

    loop {
        match connect_and_stream(url, &config, &alert_tx).await {
            Ok(()) => tracing::info!("Liquidation stream ended cleanly"),
            Err(e) => tracing::error!("Liquidation stream error: {e}"),
        }
        // Reconnect with backoff
        for delay in &reconnect_delays {
            tokio::time::sleep(Duration::from_secs(*delay)).await;
            // Try reconnect...
        }
    }
}
```

### `src/monitoring/alerts.rs`

```rust
/// Alert dispatcher with priority queue and rate limiting.
///
/// 1. Receives alerts from mpsc channel
/// 2. Checks deduplication (via Db)
/// 3. Sends to Telegram with rate limiting
/// 4. Stores in alert history
///
/// Rate limit: max 30 messages/sec to Telegram (hard limit)
/// Dedup window: config.alert_rate_limit_secs
pub async fn run(
    config: Arc<Config>,
    db: Arc<Db>,
    mut alert_rx: mpsc::Receiver<Alert>,
) {
    let bot = teloxide::Bot::new(&config.telegram_bot_token);

    while let Some(alert) = alert_rx.recv().await {
        // Dedup check
        if db.is_duplicate(&alert.alert_type, &alert.symbol,
            config.thresholds.alert_rate.dedup_window_mins).await.unwrap_or(false)
        {
            tracing::debug!("Skipping duplicate alert: {} {}", alert.alert_type, alert.symbol);
            continue;
        }

        // Send to all authorized chat IDs
        for &chat_id in &config.authorized_chat_ids {
            if let Err(e) = bot.send_message(
                teloxide::types::ChatId(chat_id),
                &alert.message,
            ).parse_mode(teloxide::types::ParseMode::Html).await {
                tracing::error!("Failed to send alert to {chat_id}: {e}");
            }
        }

        // Store in history
        if let Err(e) = db.insert_alert(&alert).await {
            tracing::error!("Failed to store alert: {e}");
        }
    }
}
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tokio::sync::mpsc;

    #[tokio::test]
    async fn test_oi_detector_sends_alert_on_threshold() {
        // Setup: mock exchange returning OI of 100M, then 120M (20% change)
        // Config: BTC threshold = 15%
        // Verify: alert_tx receives an alert
    }

    #[tokio::test]
    async fn test_oi_detector_no_alert_below_threshold() {
        // Setup: mock exchange returning OI of 100M, then 105M (5% change)
        // Config: BTC threshold = 15%
        // Verify: alert_tx receives nothing
    }

    #[tokio::test]
    async fn test_alert_dedup_skips_recent() {
        // Insert alert for BTC oi_explosion
        // Send same alert type+symbol within 5 minutes
        // Verify: only first one sent
    }

    #[test]
    fn test_format_oi_alert_message() {
        let msg = format_oi_alert("BTC", 18.5, 2_800_000_000.0);
        assert!(msg.contains("BTC"));
        assert!(msg.contains("18.5"));
    }
}
```

## Exit Criteria

- [ ] OI detector loops at configured interval
- [ ] Alerts sent when change > threshold
- [ ] No alert when change < threshold
- [ ] Liquidation monitor reconnects on disconnect
- [ ] Alert deduplication prevents repeat sends
- [ ] All 4 tests pass
- [ ] Alert messages include symbol, change %, and OI value
