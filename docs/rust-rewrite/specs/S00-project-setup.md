# S00 — Project Setup

## Scope
Initialize the Cargo project, configure dependencies, set up CI-ready structure.

## Dependencies
None. This is the first spec.

## Files to Create

### `crypto-bot/Cargo.toml`
```toml
[package]
name = "crypto-bot"
version = "0.1.0"
edition = "2021"
rust-version = "1.82"

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

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
panic = "abort"
```

### `crypto-bot/src/main.rs`
```rust
// Minimal main that proves the project compiles
mod config;
mod error;
mod types;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("crypto_bot=info".parse()?),
        )
        .init();

    tracing::info!("crypto-bot starting");
    Ok(())
}
```

### `crypto-bot/src/types.rs`
```rust
// Placeholder — filled by S01
```

### `crypto-bot/src/error.rs`
```rust
// Placeholder — filled by S01
```

### `crypto-bot/src/config.rs`
```rust
// Placeholder — filled by S02
```

### `crypto-bot/.env.example`
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
BINANCE_TESTNET=false
BYBIT_API_KEY=
BYBIT_SECRET_KEY=
BYBIT_TESTNET=false
DATABASE_URL=sqlite:data/bot.db
LOG_LEVEL=info
```

### `crypto-bot/.gitignore`
```
/target
.env
*.db
*.sqlite
data/
```

### `crypto-bot/rustfmt.toml`
```toml
edition = "2021"
max_width = 100
```

### `crypto-bot/clippy.toml`
```toml
too-many-arguments-threshold = 5
```

## Exit Criteria

- [ ] `cargo build` succeeds with zero errors
- [ ] `cargo clippy -- -D warnings` passes
- [ ] `cargo fmt --check` passes
- [ ] `cargo test` passes (even with no tests yet)
- [ ] `.env.example` exists with all variables listed
- [ ] `.gitignore` excludes `target/`, `.env`, `*.db`
- [ ] Directory structure matches the playbook Section 1
