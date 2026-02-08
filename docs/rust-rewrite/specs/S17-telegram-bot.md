# S17 — Telegram Bot Commands

## Scope
Wire up teloxide bot with all 13 commands. Each command handler fetches data, formats it, sends the Telegram message.

## Dependencies
- S02 (Config), S03 (ExchangeManager), S10-S15 (analysis), S16 (formatting)

## Files to Create

### `src/telegram/mod.rs`

```rust
pub mod commands;
pub mod formatting;

use crate::config::Config;
use crate::exchange::ExchangeManager;
use std::sync::Arc;
use teloxide::prelude::*;

/// Shared state available to all command handlers.
pub struct BotState {
    pub config: Arc<Config>,
    pub exchanges: Arc<ExchangeManager>,
}

/// Start the Telegram bot with long polling.
pub async fn run(state: Arc<BotState>) -> anyhow::Result<()> {
    let bot = Bot::new(&state.config.telegram_bot_token);

    let handler = dptree::entry()
        .branch(
            Update::filter_message()
                .filter_command::<commands::Command>()
                .endpoint(commands::handle_command),
        );

    Dispatcher::builder(bot, handler)
        .dependencies(dptree::deps![state])
        .enable_ctrlc_handler()
        .build()
        .dispatch()
        .await;

    Ok(())
}
```

### `src/telegram/commands/mod.rs`

```rust
use teloxide::prelude::*;
use teloxide::utils::command::BotCommands;
use crate::telegram::BotState;
use std::sync::Arc;

mod price;
mod analysis;
mod oi;
mod profile;
mod account;
mod help;

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase")]
pub enum Command {
    /// Show help and available commands
    Start,
    /// Show help and available commands
    Help,
    /// Get price data: /price BTC
    Price(String),
    /// Full market analysis: /analysis BTC [15m]
    Analysis(String),
    /// Volume spike: /volume BTC [15m]
    Volume(String),
    /// CVD analysis: /cvd BTC [1h]
    Cvd(String),
    /// Volume scan: /volscan [200] [15m]
    Volscan(String),
    /// Open interest: /oi [BTC]
    Oi(String),
    /// Market profile: /profile [BTC]
    Profile(String),
    /// Account balance
    Balance,
    /// Open positions
    Positions,
    /// P&L summary
    Pnl,
    /// Top 10 markets: /top10 spot|perps
    Top10(String),
}

/// Main command dispatcher.
pub async fn handle_command(
    bot: Bot,
    msg: Message,
    cmd: Command,
    state: Arc<BotState>,
) -> ResponseResult<()> {
    // Authorization check
    if !is_authorized(&state.config, msg.chat.id.0) {
        bot.send_message(msg.chat.id, "Unauthorized.").await?;
        return Ok(());
    }

    match cmd {
        Command::Start | Command::Help => help::handle(bot, msg).await,
        Command::Price(args) => price::handle_price(bot, msg, args, &state).await,
        Command::Analysis(args) => analysis::handle_analysis(bot, msg, args, &state).await,
        Command::Volume(args) => analysis::handle_volume(bot, msg, args, &state).await,
        Command::Cvd(args) => analysis::handle_cvd(bot, msg, args, &state).await,
        Command::Volscan(args) => analysis::handle_volscan(bot, msg, args, &state).await,
        Command::Oi(args) => oi::handle_oi(bot, msg, args, &state).await,
        Command::Profile(args) => profile::handle_profile(bot, msg, args, &state).await,
        Command::Balance => account::handle_balance(bot, msg, &state).await,
        Command::Positions => account::handle_positions(bot, msg, &state).await,
        Command::Pnl => account::handle_pnl(bot, msg, &state).await,
        Command::Top10(args) => price::handle_top10(bot, msg, args, &state).await,
    }
}

fn is_authorized(config: &Config, chat_id: i64) -> bool {
    config.authorized_chat_ids.is_empty() || config.authorized_chat_ids.contains(&chat_id)
}
```

### Command Handler Pattern (each file)

Every command handler follows this pattern:

```rust
pub async fn handle_price(
    bot: Bot,
    msg: Message,
    args: String,
    state: &BotState,
) -> ResponseResult<()> {
    // 1. Parse arguments
    let symbol = parse_symbol(&args).unwrap_or("BTC".to_string());

    // 2. Send "loading" indicator
    // (optional: bot.send_chat_action(msg.chat.id, ChatAction::Typing).await?)

    // 3. Fetch data
    let result = fetch_price_data(&state.exchanges, &symbol).await;

    // 4. Format response
    let text = match result {
        Ok(data) => format_price_response(&data),
        Err(e) => {
            tracing::error!("Price command failed: {e:#}");
            format!("Failed to fetch price for {symbol}. Try again.")
        }
    };

    // 5. Send message (HTML parse mode for formatting)
    bot.send_message(msg.chat.id, text)
        .parse_mode(teloxide::types::ParseMode::Html)
        .await?;

    Ok(())
}
```

## Argument Parsing Rules

| Command | Args | Parse Rule | Default |
|---------|------|-----------|---------|
| /price BTC | "BTC" | First word → uppercase → symbol | "BTC" |
| /analysis BTC 15m | "BTC 15m" | Word1=symbol, Word2=timeframe | "BTC", "15m" |
| /volume BTC 15m | "BTC 15m" | Word1=symbol, Word2=timeframe | "BTC", "15m" |
| /cvd BTC 1h | "BTC 1h" | Word1=symbol, Word2=timeframe | "BTC", "1h" |
| /volscan 200 15m | "200 15m" | Word1=threshold, Word2=timeframe | 200, "15m" |
| /oi BTC | "BTC" | First word → symbol | "BTC" |
| /profile BTC | "BTC" | First word → symbol | "BTC" |
| /top10 spot | "spot" | First word → "spot" or "perps" | "spot" |

```rust
/// Parse "BTC" or "BTC 15m" into (symbol, timeframe).
fn parse_symbol_timeframe(args: &str, default_tf: &str) -> (String, String) {
    let parts: Vec<&str> = args.split_whitespace().collect();
    let symbol = parts.first().map(|s| s.to_uppercase()).unwrap_or("BTC".to_string());
    let timeframe = parts.get(1).map(|s| s.to_string()).unwrap_or(default_tf.to_string());
    (symbol, timeframe)
}
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_symbol_timeframe_both() {
        let (s, t) = parse_symbol_timeframe("eth 4h", "15m");
        assert_eq!(s, "ETH");
        assert_eq!(t, "4h");
    }

    #[test]
    fn test_parse_symbol_timeframe_symbol_only() {
        let (s, t) = parse_symbol_timeframe("sol", "15m");
        assert_eq!(s, "SOL");
        assert_eq!(t, "15m");
    }

    #[test]
    fn test_parse_symbol_timeframe_empty() {
        let (s, t) = parse_symbol_timeframe("", "15m");
        assert_eq!(s, "BTC");
        assert_eq!(t, "15m");
    }

    #[test]
    fn test_is_authorized_empty_allows_all() {
        let config = Config { authorized_chat_ids: HashSet::new(), /* ... */ };
        assert!(is_authorized(&config, 12345));
    }

    #[test]
    fn test_is_authorized_checks_id() {
        let mut ids = HashSet::new();
        ids.insert(12345_i64);
        let config = Config { authorized_chat_ids: ids, /* ... */ };
        assert!(is_authorized(&config, 12345));
        assert!(!is_authorized(&config, 99999));
    }
}
```

## Exit Criteria

- [ ] All 13 commands registered in enum with correct names
- [ ] Authorization check runs before every command
- [ ] Empty authorized_chat_ids allows all users
- [ ] Each command handler: parses args → fetches data → formats → sends
- [ ] Errors produce user-friendly messages (not panic/crash)
- [ ] All 5 tests pass
- [ ] `cargo clippy` clean
