# Python → Rust Migration Analysis

## Executive Summary

**Recommendation: FULL REWRITE in Rust** (not incremental migration)

The current Python codebase (~25,500 LOC across 80 files) carries critical tech debt that makes incremental migration impractical. A clean Rust rewrite consolidating 3 microservices into a single async binary will deliver the lowest latency, fit within AWS free tier RAM constraints (1 GB), and eliminate entire categories of runtime bugs.

**Estimated scope:** ~8,000-12,000 lines of Rust (Rust is more verbose per-line but eliminates duplication and dead code present in the Python codebase)

---

## Part 1: Current State Assessment

### Architecture Overview

```
Current: 3 Python microservices + shared modules
┌─────────────────┐    HTTP     ┌──────────────────┐
│  telegram-bot    │ ─────────→ │   market-data     │
│  (Port: polling) │            │   (Port: 8001)    │
└─────────────────┘            └──────────────────┘
                                        ↑
┌─────────────────┐    HTTP     ────────┘
│   monitoring     │ ──────────
│  (Port: 8002)    │
└─────────────────┘
```

| Service | LOC | Purpose |
|---------|-----|---------|
| telegram-bot | ~3,700 | Commands, formatting, user interaction |
| market-data | ~9,500 | Exchange APIs, indicators, OI, volume, profiles |
| monitoring | ~1,200 | OI explosion detection, alert dispatch |
| shared | ~1,950 | Models, config, pipeline, thresholds |
| Validation/test/debug scripts | ~9,100 | Should not exist in production |

### Feature Inventory

| Feature | Complexity | Rust Library Coverage |
|---------|-----------|----------------------|
| 13 Telegram commands | Medium | teloxide - full coverage |
| 6+ exchange OI aggregation | High | ccxt-rust covers 4/6, rest need custom clients |
| CVD (Cumulative Volume Delta) | Medium | Custom implementation needed (same as Python) |
| Volume spike detection | Medium | Custom (same as Python) |
| Volume Profile / TPO | Medium | Custom (same as Python) |
| Technical indicators (RSI, VWAP, ATR, BB) | Low | ta-rs / RustTI - full coverage |
| Market sentiment scoring | Low | Custom business logic |
| Liquidation monitoring | Medium | WebSocket via tokio-tungstenite |
| OI explosion detection | Medium | Custom business logic |
| Alert dispatch (priority queue) | Low | tokio + BinaryHeap |
| Long/short ratio tracking | Low | Custom (Binance API only) |
| Session volume (LuxAlgo 4-session) | Medium | Custom (same as Python) |

### Tech Debt Assessment (Why Migration is Not Viable)

**Critical issues that prevent incremental porting:**

1. **God classes**: `TelegramBot` (1,457 lines, 40+ methods), `ExchangeManager` (500+ lines, 15+ methods). These cannot be ported module-by-module because responsibilities are deeply entangled.

2. **13 duplicate/abandoned files** in market-data: `*_fixed.py`, `*_working.py`, `validate_*_independently.py`. No clear which version is canonical.

3. **0% test coverage**: No tests in `/tests/`. No way to verify a partial migration preserves behavior.

4. **Import hacks**: Conditional `try/except ImportError` blocks for relative vs absolute imports. `sys.path.append()` manipulation. These indicate the Python package structure itself is broken.

5. **Hardcoded developer paths**: `/Users/screener-m3/projects/crypto-assistant/` in production code (coordinator.py lines 188, 220, 240, 374, 383).

6. **Test files in production**: `api_test_simple.py`, `integration_test_profile.py`, `inline_test.py`, etc. in the root and service directories.

7. **Silent error swallowing**: 17+ bare `except:` clauses, exceptions caught and replaced with `None` without logging. Makes behavior non-deterministic.

8. **No type safety**: Generic `Dict[str, Any]` used 50+ times. Function return types undefined. Callers cannot rely on contracts.

**Verdict**: The codebase is too fragile and undocumented for safe incremental migration. A Python-Rust bridge (PyO3) would inherit these structural problems. Clean rewrite is the lower-risk path.

---

## Part 2: Why Rust (and Not Go, Zig, etc.)

### Latency Comparison

| Metric | Python (current) | Rust (projected) | Improvement |
|--------|-----------------|-------------------|-------------|
| Cold start | 3-8s (Python interpreter + imports) | 10-50ms (static binary) | 60-160x |
| API response parse (JSON) | 1-5ms (json module) | 0.05-0.2ms (serde) | 20-25x |
| Indicator calculation (RSI/ATR) | 0.5-2ms (numpy) | 0.01-0.05ms (native) | 50-100x |
| WebSocket message processing | 0.1-0.5ms | 0.005-0.02ms | 20-25x |
| Memory per service | 100-200 MB | 5-20 MB | 10-40x |
| Telegram command response (e2e) | 200-800ms | 50-150ms | 4-5x |
| GC pauses | 10-50ms (unpredictable) | 0ms (no GC) | Eliminated |

### Why Not Go?

Go would be viable but Rust wins on:
- **No garbage collector**: Critical for real-time market data processing. Go's GC introduces 1-10ms pauses.
- **Zero-cost abstractions**: Rust's generics and traits compile to the same code as hand-written specializations.
- **Memory**: Rust uses 2-5x less memory than Go for equivalent programs. On a 1 GB free tier instance, this matters.
- **teloxide maturity**: teloxide is more feature-complete than Go's telegram-bot-api libraries.

### AWS Free Tier Reality Check

**t2.micro / t3.micro**: 1 vCPU, 1 GB RAM, burstable CPU credits

| Stack | RAM Usage | CPU Profile | Viability |
|-------|-----------|-------------|-----------|
| Python 3 containers | 400-700 MB | Steady, GIL-limited | Marginal - will OOM under load |
| Python 1 container | 200-350 MB | Steady | Tight but workable |
| Rust single binary | 15-40 MB | Burst only | Comfortable - 95% RAM free |
| Go single binary | 30-80 MB | Burst + GC | Good |

**Rust is the only option that leaves meaningful headroom on 1 GB RAM** for the OS, SQLite page cache, and network buffers.

---

## Part 3: Recommended Rust Architecture

### Single Binary, Multi-Module Design

Collapse 3 microservices into one async Rust binary. On a single t2.micro there is zero benefit to inter-process HTTP communication - it only adds latency and resource overhead.

```
crypto-bot (single binary)
├── main.rs                     # Entry point, config loading, task spawning
├── config/
│   ├── mod.rs                  # Configuration types
│   └── thresholds.rs           # Alert thresholds
├── telegram/
│   ├── mod.rs                  # Bot setup, command routing
│   ├── commands/
│   │   ├── mod.rs
│   │   ├── price.rs            # /price, /top10
│   │   ├── analysis.rs         # /analysis, /volume, /cvd, /volscan
│   │   ├── oi.rs               # /oi
│   │   ├── profile.rs          # /profile
│   │   ├── account.rs          # /balance, /positions, /pnl
│   │   └── help.rs             # /start, /help
│   └── formatting.rs           # Message formatting utilities
├── exchange/
│   ├── mod.rs                  # Exchange trait + manager
│   ├── binance.rs              # Binance REST + WS
│   ├── bybit.rs                # Bybit REST + WS
│   ├── okx.rs                  # OKX REST + WS
│   ├── bitget.rs               # Bitget REST + WS
│   ├── gateio.rs               # Gate.io REST + WS
│   ├── hyperliquid.rs          # Hyperliquid REST
│   ├── types.rs                # Shared exchange types (Ticker, OHLCV, OI, etc.)
│   └── rate_limiter.rs         # Per-exchange rate limiting
├── analysis/
│   ├── mod.rs
│   ├── indicators.rs           # RSI, ATR, VWAP, Bollinger Bands
│   ├── volume.rs               # Volume spike detection, CVD
│   ├── oi.rs                   # OI aggregation, explosion detection
│   ├── profile.rs              # Volume Profile, TPO, Value Area
│   ├── session.rs              # LuxAlgo 4-session framework
│   └── sentiment.rs            # Market sentiment scoring
├── monitoring/
│   ├── mod.rs                  # Background task coordinator
│   ├── oi_detector.rs          # OI explosion detector
│   ├── liquidation.rs          # Liquidation monitor
│   └── alerts.rs               # Alert priority queue + dispatch
├── db/
│   ├── mod.rs                  # SQLite connection pool
│   └── models.rs               # Alert history, cached data
└── utils/
    ├── mod.rs
    └── formatting.rs           # Number formatting, timestamps
```

### Recommended Stack

| Component | Crate | Version | Purpose |
|-----------|-------|---------|---------|
| Async runtime | `tokio` | 1.x | Multi-threaded async executor |
| Telegram bot | `teloxide` | 0.17 | Bot framework (commands, dialogue, dispatch) |
| HTTP client | `reqwest` | 0.13 | REST API calls to exchanges |
| WebSocket | `tokio-tungstenite` | 0.26 | Real-time market data streams |
| JSON | `serde` + `serde_json` | 1.x | Serialization/deserialization |
| Database | `sqlx` | 0.8 | Async SQLite (alert history, cache) |
| TA indicators | `ta` (ta-rs) | 0.5 | RSI, ATR, EMA, Bollinger (streaming) |
| Crypto HMAC | `hmac` + `sha2` | 0.12 | Exchange API authentication |
| Config | `dotenvy` | 0.15 | .env file loading |
| Logging | `tracing` + `tracing-subscriber` | 0.1 | Structured async-aware logging |
| Error handling | `anyhow` + `thiserror` | 1.x | Application + library errors |
| Time | `chrono` | 0.4 | Timestamps, timezone handling |
| CLI | `clap` | 4.x | Optional: CLI arg parsing |

### Exchange Integration Strategy

The biggest ecosystem gap is multi-exchange support. Strategy:

1. **Define an `Exchange` trait** with methods: `fetch_ticker()`, `fetch_ohlcv()`, `fetch_open_interest()`, `fetch_funding_rate()`, `stream_trades()`, etc.

2. **Use `ccxt-rust`** for Binance, Bybit, Bitget, Hyperliquid (4 exchanges covered).

3. **Write custom clients** for OKX and Gate.io using `reqwest`. These are straightforward REST APIs with HMAC authentication. Each is ~200-400 lines of Rust.

4. **Alternative**: Write all 6 exchange clients from scratch using `reqwest`. The current Python code already uses direct HTTP calls for OI data (not CCXT), so you have working reference implementations for the exact endpoints needed.

**Estimated effort for custom exchange clients**: 300-500 lines per exchange for the specific endpoints this bot uses (ticker, OHLCV, OI, funding rate). Total: ~2,000-3,000 lines for 6 exchanges.

### Data Flow (Single Process)

```
                    ┌─────────────────────────────────────┐
                    │         crypto-bot (single binary)    │
                    │                                       │
 Telegram ←──poll──→│  telegram::commands  ←──fn call──→   │
                    │                                       │
                    │  exchange::manager   ←──fn call──→   │
                    │     ├── binance                       │
                    │     ├── bybit                         │
                    │     ├── okx          ←──reqwest──→  Exchanges
                    │     ├── bitget                        │
                    │     ├── gateio                        │
                    │     └── hyperliquid                   │
                    │                                       │
                    │  analysis::*         (pure compute)   │
                    │                                       │
                    │  monitoring::*  ←──tokio::spawn──→   │
                    │     ├── oi_detector  (5min loop)     │
                    │     ├── liquidation  (WS stream)     │
                    │     └── alerts       (priority queue) │
                    │                                       │
                    │  db::sqlite    ←──sqlx──→  SQLite     │
                    └─────────────────────────────────────┘
```

**Latency advantage**: Telegram command → exchange API → analysis → response is all in-process function calls. No HTTP serialization/deserialization between services. Saves 5-20ms per request.

---

## Part 4: AWS Free Tier Deployment with Podman on Ubuntu

### Infrastructure

```
AWS t3.micro (Free Tier)
├── Ubuntu 24.04 LTS
├── Podman 4.x (rootless)
├── SQLite (file-based, no separate DB service)
└── systemd (service management)
```

### Why Podman Over Docker

| Aspect | Podman | Docker |
|--------|--------|--------|
| Daemon | Daemonless (no root daemon) | Requires dockerd (root) |
| Security | Rootless by default | Root by default |
| Systemd | Native `podman generate systemd` | Requires docker-compose |
| RAM overhead | ~0 MB (no daemon) | ~50-80 MB (dockerd) |
| Compose | `podman-compose` or pods | docker-compose |
| CLI | Drop-in Docker compatible | - |
| Ubuntu install | `apt install podman` | Add Docker repo |

On a 1 GB instance, saving 50-80 MB by not running dockerd is significant.

### Container Strategy

```dockerfile
# Containerfile (Podman-compatible Dockerfile)
# Build stage
FROM docker.io/library/rust:1.82-slim-bookworm AS builder
WORKDIR /app

# Cache dependencies
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main(){}" > src/main.rs
RUN cargo build --release && rm -rf src

# Build actual application
COPY src/ src/
RUN touch src/main.rs && cargo build --release
RUN strip target/release/crypto-bot

# Runtime stage - minimal Ubuntu
FROM docker.io/library/ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 app
WORKDIR /home/app
COPY --from=builder /app/target/release/crypto-bot .
USER app
ENTRYPOINT ["./crypto-bot"]
```

**Image size**: ~85 MB (Ubuntu base) vs current ~350-500 MB (3 Python containers)

### Alternative: Scratch Container (Smallest Possible)

```dockerfile
FROM docker.io/library/rust:1.82-alpine AS builder
WORKDIR /app
RUN apk add musl-dev
COPY . .
RUN cargo build --release --target x86_64-unknown-linux-musl
RUN strip target/x86_64-unknown-linux-musl/release/crypto-bot

FROM scratch
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/crypto-bot /crypto-bot
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/crypto-bot"]
```

**Image size**: ~10-15 MB. But since Ubuntu is required for the host, using Ubuntu as base is fine.

### Deployment Setup

```bash
# On Ubuntu 24.04 t3.micro

# 1. Install Podman
sudo apt update && sudo apt install -y podman

# 2. Enable lingering (allows rootless containers to persist)
sudo loginctl enable-linger ubuntu

# 3. Pull and run
podman pull ghcr.io/<your-repo>/crypto-bot:latest
podman run -d \
  --name crypto-bot \
  --restart=always \
  --env-file /home/ubuntu/.env \
  -v /home/ubuntu/data:/home/app/data:Z \
  ghcr.io/<your-repo>/crypto-bot:latest

# 4. Generate systemd service for auto-start
mkdir -p ~/.config/systemd/user/
podman generate systemd --name crypto-bot --new > \
  ~/.config/systemd/user/crypto-bot.service
systemctl --user enable crypto-bot.service
systemctl --user start crypto-bot.service
```

### Resource Budget (1 GB RAM)

| Component | RAM |
|-----------|-----|
| Ubuntu 24.04 (minimal) | ~200 MB |
| Podman (rootless, no daemon) | ~0 MB |
| crypto-bot binary | ~15-30 MB |
| SQLite page cache | ~10-20 MB |
| Network buffers / OS cache | ~50-100 MB |
| **Total** | **~275-350 MB** |
| **Headroom** | **~650-725 MB free** |

Compare to current Python:
| Component | RAM |
|-----------|-----|
| Ubuntu 24.04 | ~200 MB |
| Docker daemon | ~70 MB |
| market-data container | ~200 MB |
| telegram-bot container | ~150 MB |
| monitoring container | ~100 MB |
| **Total** | **~720 MB** |
| **Headroom** | **~280 MB** (dangerously low) |

### CI/CD Pipeline

```yaml
# .github/workflows/build.yml
name: Build and Push
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build container
        run: |
          podman build -t ghcr.io/${{ github.repository }}:latest .
          podman build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .

      - name: Push to GHCR
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | podman login ghcr.io -u ${{ github.actor }} --password-stdin
          podman push ghcr.io/${{ github.repository }}:latest
          podman push ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to AWS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.AWS_HOST }}
          username: ubuntu
          key: ${{ secrets.AWS_SSH_KEY }}
          script: |
            podman pull ghcr.io/${{ github.repository }}:latest
            podman stop crypto-bot || true
            podman rm crypto-bot || true
            podman run -d --name crypto-bot --restart=always \
              --env-file ~/.env \
              -v ~/data:/home/app/data:Z \
              ghcr.io/${{ github.repository }}:latest
```

---

## Part 5: Migration Plan (Phased Rewrite)

### Phase 0: Foundation (Week 1)

**Goal**: Skeleton compiles and runs, connects to Telegram

```
Tasks:
- [ ] Initialize Cargo workspace
- [ ] Set up module structure (telegram/, exchange/, analysis/, monitoring/, db/)
- [ ] Configure teloxide with long polling
- [ ] Implement /start and /help commands
- [ ] Set up dotenvy for config loading
- [ ] Set up tracing for structured logging
- [ ] Set up SQLx with SQLite (empty schema)
- [ ] Create Containerfile, test with Podman locally
- [ ] Verify bot responds on Telegram
```

**Deliverable**: Bot responds to /start and /help on Telegram. Single binary, ~500 lines.

### Phase 1: Exchange Connectivity (Weeks 2-3)

**Goal**: Fetch live data from all 6 exchanges

```
Tasks:
- [ ] Define Exchange trait: fetch_ticker, fetch_ohlcv, fetch_open_interest, fetch_funding_rate
- [ ] Implement Binance client (FAPI + DAPI + spot)
- [ ] Implement Bybit client (V5 API)
- [ ] Implement OKX client (swap API)
- [ ] Implement Gate.io client
- [ ] Implement Bitget client
- [ ] Implement Hyperliquid client
- [ ] Build ExchangeManager with concurrent fetching (tokio::join!)
- [ ] Implement per-exchange rate limiter
- [ ] Add HMAC-SHA256 signing for authenticated endpoints
- [ ] Implement /price command (combined spot + perp)
- [ ] Implement /balance, /positions, /pnl commands
```

**Deliverable**: All exchange data flows working. /price shows live data. ~3,000 lines.

### Phase 2: Analysis Engine (Weeks 4-5)

**Goal**: All analysis features ported

```
Tasks:
- [ ] Integrate ta-rs for RSI, ATR, Bollinger Bands
- [ ] Implement VWAP calculation
- [ ] Port volume spike detection algorithm
- [ ] Port CVD calculation
- [ ] Port Volume Profile / TPO / Value Area calculation
- [ ] Port LuxAlgo 4-session framework
- [ ] Port market sentiment scoring system
- [ ] Port OI aggregation across exchanges
- [ ] Implement /analysis, /volume, /cvd, /volscan, /oi, /profile commands
- [ ] Implement /top10 command
- [ ] Port all formatting utilities (format_large_number, format_price, etc.)
```

**Deliverable**: Feature parity with current bot for on-demand commands. ~6,000 lines.

### Phase 3: Real-Time Monitoring (Week 6)

**Goal**: Background monitoring and alerting

```
Tasks:
- [ ] Implement OI explosion detector (5-minute polling loop)
- [ ] Implement liquidation monitor (WebSocket streams)
- [ ] Build alert priority queue with dispatch
- [ ] Implement alert deduplication and rate limiting
- [ ] Store alert history in SQLite
- [ ] Implement health check endpoint (optional HTTP server)
- [ ] Port dynamic threshold engine
```

**Deliverable**: Full feature parity. ~8,000-10,000 lines.

### Phase 4: Deployment & Cutover (Week 7)

**Goal**: Production deployment on AWS free tier

```
Tasks:
- [ ] Final Containerfile optimization
- [ ] Set up Ubuntu 24.04 on t3.micro
- [ ] Install Podman, configure rootless
- [ ] Set up systemd service
- [ ] Configure .env with production credentials
- [ ] Deploy and run parallel with Python bot (both reading, only one writing to Telegram)
- [ ] Validate all commands produce correct output
- [ ] Cut over: stop Python, Rust is primary
- [ ] Set up GitHub Actions CI/CD pipeline
- [ ] Monitor for 1 week, fix edge cases
```

**Deliverable**: Production Rust bot running on AWS free tier.

### Phase 5: Rust-Only Enhancements (Post-Launch)

Features that become practical only with Rust's performance:

```
- [ ] WebSocket-first data feeds (replace REST polling with streaming)
- [ ] Sub-second alert latency (currently limited by Python's async overhead)
- [ ] In-memory order book reconstruction
- [ ] Tick-by-tick CVD (instead of candle-based approximation)
- [ ] Multi-symbol concurrent monitoring (hundreds of pairs)
- [ ] Historical data storage and replay (RAM-efficient with Rust structs)
```

---

## Part 6: Risk Assessment

### Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Exchange API changes during rewrite | Medium | Port one exchange at a time; keep Python bot running until cutover |
| ccxt-rust lacks needed features | Medium | Write custom clients using reqwest (reference: existing Python HTTP calls) |
| teloxide breaking changes (0.x) | Low | Pin version in Cargo.lock; teloxide is stable in practice |
| Developer unfamiliarity with Rust | High | Start with Phase 0 skeleton; Rust's compiler guides you through errors |
| Longer-than-expected timeline | Medium | Each phase is independently deployable; can run hybrid if needed |
| SQLite concurrent write contention | Low | Single process = single writer; use WAL mode for reads |
| AWS free tier CPU throttling | Low | Rust's efficiency means minimal CPU usage; t3.micro burst credits sufficient |

### What We Gain

1. **10-40x lower memory** → comfortable on free tier instead of marginal
2. **4-5x lower end-to-end latency** for command responses
3. **Zero GC pauses** → no missed market events
4. **Compile-time correctness** → no more 3 AM crashes from `NoneType has no attribute`
5. **Single binary deployment** → no Docker Compose orchestration, no inter-service networking
6. **10-15 MB container** (scratch) or 85 MB (Ubuntu) → faster deploys, lower storage
7. **No Python dependency hell** → no pip version conflicts, no broken wheels
8. **Fearless concurrency** → concurrent exchange fetches are provably safe at compile time

### What We Lose

1. **Development velocity** → 2-4x slower initial development, but maintenance is faster
2. **CCXT coverage** → Must write custom clients for OKX and Gate.io
3. **Rapid prototyping** → No REPL, every API response needs a struct
4. **ML/AI integration** → If needed later, Python is far better (mitigate with PyO3 bridge)
5. **Compile times** → Full build: 3-10 minutes, incremental: 5-30 seconds

---

## Part 7: Cargo.toml (Starter)

```toml
[package]
name = "crypto-bot"
version = "0.1.0"
edition = "2021"
rust-version = "1.82"

[dependencies]
# Async runtime
tokio = { version = "1", features = ["full"] }

# Telegram
teloxide = { version = "0.17", features = ["macros"] }

# HTTP & WebSocket
reqwest = { version = "0.13", features = ["json", "rustls-tls"] }
tokio-tungstenite = { version = "0.26", features = ["rustls-tls-native-roots"] }

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Database
sqlx = { version = "0.8", features = ["runtime-tokio", "sqlite"] }

# Technical Analysis
ta = "0.5"

# Crypto / Auth
hmac = "0.12"
sha2 = "0.10"
hex = "0.4"

# Config & Logging
dotenvy = "0.15"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# Error handling
anyhow = "1"
thiserror = "2"

# Time
chrono = { version = "0.4", features = ["serde"] }

# Misc
url = "2"
rust_decimal = "1"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
panic = "abort"
```

---

## Conclusion

The current Python codebase is **functional but structurally compromised** by rapid prototyping. With 0% test coverage, god classes, 13 duplicate files, hardcoded developer paths in production, and import hacks, an incremental migration would inherit all these problems and create a harder-to-maintain hybrid system.

A **clean Rust rewrite** is the correct approach because:

1. The codebase is small enough (~25K LOC → ~8-12K Rust) that a full rewrite is tractable
2. The architecture simplifies dramatically (3 services → 1 binary)
3. AWS free tier constraints make Python's memory overhead untenable long-term
4. The Rust ecosystem covers all required functionality (teloxide, reqwest, ta-rs, sqlx)
5. The exchange gap (ccxt-rust covers 4/6 exchanges) is bridgeable with ~2K lines of custom clients
6. Latency improvements (4-5x for commands, eliminated GC pauses) directly serve the project's core goal

**Start with Phase 0.** Get a skeleton bot responding on Telegram in Rust. Each subsequent phase builds on the previous one and is independently testable. Keep the Python bot running in parallel until Phase 4 cutover.
