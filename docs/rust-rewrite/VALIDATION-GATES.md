# Validation Gates — Phase Exit Criteria

Every phase has hard gates. An agent CANNOT proceed to the next phase until ALL gates pass.

---

## Gate Protocol

After completing a spec, the agent runs:

```bash
#!/bin/bash
# gate-check.sh — Run after every spec completion

echo "=== GATE 1: Compile ==="
cargo build 2>&1 | tail -3
BUILD_OK=$?

echo "=== GATE 2: Clippy ==="
cargo clippy -- -D warnings 2>&1 | tail -3
CLIPPY_OK=$?

echo "=== GATE 3: Format ==="
cargo fmt --check 2>&1
FMT_OK=$?

echo "=== GATE 4: Tests ==="
cargo test 2>&1 | tail -10
TEST_OK=$?

echo "=== GATE 5: No Secrets ==="
grep -rn "sk-\|ghp_\|xox[bps]-\|AKIA\|token.*=.*['\"]" src/ tests/ Cargo.toml 2>/dev/null
SECRETS=$?
# SECRETS should be non-zero (grep found nothing)

echo ""
echo "=== GATE RESULTS ==="
[ $BUILD_OK -eq 0 ] && echo "✅ Build" || echo "❌ Build FAILED"
[ $CLIPPY_OK -eq 0 ] && echo "✅ Clippy" || echo "❌ Clippy FAILED"
[ $FMT_OK -eq 0 ] && echo "✅ Format" || echo "❌ Format FAILED"
[ $TEST_OK -eq 0 ] && echo "✅ Tests" || echo "❌ Tests FAILED"
[ $SECRETS -ne 0 ] && echo "✅ No Secrets" || echo "❌ SECRETS FOUND"
```

---

## Phase 0: Foundation (S00-S02)

### Entry Criteria
- Rust 1.82+ installed (`rustc --version`)
- Git repo initialized

### Exit Gates

| Gate | Command | Pass Condition |
|------|---------|----------------|
| G0.1 | `cargo build` | Compiles with zero errors |
| G0.2 | `cargo clippy -- -D warnings` | Zero warnings |
| G0.3 | `cargo fmt --check` | No formatting diff |
| G0.4 | `cargo test` | All tests pass (T001-T013) |
| G0.5 | `ls .env.example` | File exists with all variables |
| G0.6 | `cat .gitignore \| grep target` | target/ is excluded |

### Test Count Checkpoint
- Expected: 13 tests passing
- Command: `cargo test 2>&1 | grep "test result"`
- Must show: `test result: ok. 13 passed; 0 failed`

---

## Phase 1: Exchange Connectivity (S03-S09)

### Entry Criteria
- Phase 0 gates pass

### Exit Gates

| Gate | Command | Pass Condition |
|------|---------|----------------|
| G1.1 | `cargo build` | Compiles with all 6 exchange clients |
| G1.2 | `cargo clippy -- -D warnings` | Zero warnings |
| G1.3 | `cargo test` | All tests pass (T001-T082) |
| G1.4 | Code review | Each exchange implements all 6 trait methods |
| G1.5 | Code review | RateLimiter called before every API request |
| G1.6 | Code review | All string→f64 parsing uses `.parse::<f64>()` with error handling |
| G1.7 | Code review | No `unwrap()` in production code |

### Test Count Checkpoint
- Expected: 40 tests passing (13 + 5 + 22)
- Must show: `test result: ok. 40 passed; 0 failed`

### Validation Script
```bash
# Verify all exchange modules exist
for ex in binance bybit okx gateio bitget hyperliquid; do
    test -f src/exchange/$ex.rs && echo "✅ $ex" || echo "❌ $ex MISSING"
done
```

---

## Phase 2: Analysis Engine (S10-S16)

### Entry Criteria
- Phase 1 gates pass

### Exit Gates

| Gate | Command | Pass Condition |
|------|---------|----------------|
| G2.1 | `cargo build` | Compiles with all analysis modules |
| G2.2 | `cargo test` | All tests pass (T001-T215) |
| G2.3 | Code review | No async code in indicators.rs, volume.rs, profile.rs, session.rs, sentiment.rs |
| G2.4 | Code review | No `f64 ==` comparisons (use approx) |
| G2.5 | Code review | All `calculate_*` return `Option` for insufficient data |
| G2.6 | Code review | Formatting output matches Python formatting_utils.py examples |

### Test Count Checkpoint
- Expected: 98 tests passing (40 + 12 + 12 + 5 + 4 + 5 + 16 + 4 = 98)
- Must show: `test result: ok. 98 passed; 0 failed`

### Numerical Validation
```bash
# Run indicator tests with output to verify values
cargo test indicators_test -- --nocapture 2>&1 | grep -E "RSI|VWAP|ATR|BB"
# Manually verify values match Python reference implementation
```

---

## Phase 3: Telegram + DB + Monitoring (S17-S19)

### Entry Criteria
- Phase 2 gates pass

### Exit Gates

| Gate | Command | Pass Condition |
|------|---------|----------------|
| G3.1 | `cargo build` | Full project compiles |
| G3.2 | `cargo test` | All 111 tests pass |
| G3.3 | Code review | All 13 commands registered |
| G3.4 | Code review | Authorization check before every command |
| G3.5 | Code review | Error responses are user-friendly (no stack traces) |
| G3.6 | Code review | SQLite migrations exist in `migrations/` |
| G3.7 | Code review | Alert deduplication prevents repeat sends |
| G3.8 | `grep -rn "unwrap()" src/` | Zero results |

### Test Count Checkpoint
- Expected: 111 tests passing
- Must show: `test result: ok. 111 passed; 0 failed`

---

## Phase 4: Integration & Deployment (S20-S21)

### Entry Criteria
- Phase 3 gates pass
- Podman installed (`podman --version`)

### Exit Gates

| Gate | Command | Pass Condition |
|------|---------|----------------|
| G4.1 | `cargo build --release` | Release build succeeds |
| G4.2 | `ls -la target/release/crypto-bot` | Binary exists, < 30 MB |
| G4.3 | `podman build -t test -f Containerfile .` | Image builds successfully |
| G4.4 | `podman image inspect test --format '{{.Size}}'` | < 157286400 (150 MB) |
| G4.5 | `podman run --rm test` | Exits with config error (no token) |
| G4.6 | Code review | main.rs wires all modules correctly |
| G4.7 | Code review | Graceful shutdown on Ctrl+C |
| G4.8 | `test -f deploy.sh` | Deployment script exists |
| G4.9 | `test -f crypto-bot.service` | Systemd service file exists |

### Final Checklist (Before Live Deployment)

```
[ ] cargo test shows 111 passed, 0 failed
[ ] cargo clippy -- -D warnings shows 0 warnings
[ ] cargo build --release succeeds
[ ] Binary size < 30 MB
[ ] Container image < 150 MB
[ ] No secrets in code (grep check passes)
[ ] .env.example documents all variables
[ ] All 13 Telegram commands registered
[ ] SQLite migration runs on first start
[ ] Monitoring loops start in background
[ ] Ctrl+C triggers clean shutdown
[ ] Container runs as non-root user
```

---

## Live Cutover Validation

Before switching from Python to Rust:

### Side-by-Side Comparison

Run both bots simultaneously. For each command, compare output:

| Command | Python Output | Rust Output | Match? |
|---------|--------------|-------------|--------|
| /price BTC | Record | Record | ✅/❌ |
| /analysis BTC | Record | Record | ✅/❌ |
| /volume BTC | Record | Record | ✅/❌ |
| /cvd BTC | Record | Record | ✅/❌ |
| /oi BTC | Record | Record | ✅/❌ |
| /profile BTC | Record | Record | ✅/❌ |
| /balance | Record | Record | ✅/❌ |
| /positions | Record | Record | ✅/❌ |
| /pnl | Record | Record | ✅/❌ |
| /top10 spot | Record | Record | ✅/❌ |
| /top10 perps | Record | Record | ✅/❌ |
| /volscan | Record | Record | ✅/❌ |

**All 12 commands must produce equivalent output** (numbers may differ by timing, but format and structure must match).

### Performance Baseline

Measure before and after:

| Metric | Python | Rust | Target |
|--------|--------|------|--------|
| /price response time | Xms | Xms | < 200ms |
| /analysis response time | Xms | Xms | < 500ms |
| /oi response time | Xms | Xms | < 1000ms |
| Memory usage (idle) | X MB | X MB | < 50 MB |
| Memory usage (under load) | X MB | X MB | < 100 MB |
| Container image size | X MB | X MB | < 150 MB |
| Cold start time | Xs | Xs | < 1s |

---

## Rollback Plan

If Rust bot fails in production:

1. `podman stop crypto-bot`
2. `docker-compose up -d` (start Python stack)
3. Investigate Rust logs: `podman logs crypto-bot --tail 100`
4. Fix issue, rebuild, retry

Keep Python stack deployment files intact until Rust has run stable for 7 days.
