# Test Matrix — Crypto-Bot Rust Rewrite

## Test Strategy

| Layer | Tool | Coverage Target | Run Frequency |
|-------|------|----------------|---------------|
| Unit | `cargo test` | 90%+ for pure functions (analysis, formatting) | Every commit |
| Integration | `cargo test --test '*'` + wiremock | All exchange clients, DB operations | Every spec |
| Smoke | Container + env check | Binary starts, config loads | Every build |
| Live validation | Manual against real APIs | Full command output comparison | Phase cutover |

---

## Complete Test Inventory

### Layer 0: Types & Config (S01, S02)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T001 | `test_market_type_display` | types | `MarketType::Usdt` | `"USDT"` | unit |
| T002 | `test_spike_level_display` | types | `SpikeLevel::Extreme` | `"EXTREME"` | unit |
| T003 | `test_trend_display` | types | `Trend::Bullish` | `"BULLISH"` | unit |
| T004 | `test_alert_priority_ordering` | types | `High` vs `Medium` | `High < Medium` | unit |
| T005 | `test_ticker_serialization_roundtrip` | types | Ticker struct | JSON → Ticker lossless | unit |
| T006 | `test_position_side_equality` | types | `Long == Long` | true | unit |
| T007 | `test_combined_price_with_none` | types | Both None | Compiles, fields are None | unit |
| T008 | `test_config_missing_token` | config | No env var | `Err` containing "TELEGRAM_BOT_TOKEN" | unit |
| T009 | `test_config_defaults` | config | Only token set | All defaults correct | unit |
| T010 | `test_config_chat_id_parsing` | config | "123,456,789" | 3 IDs in set | unit |
| T011 | `test_config_empty_allows_all` | config | No CHAT_ID | Empty set | unit |
| T012 | `test_liquidation_threshold` | config | "BTC" | 100_000 | unit |
| T013 | `test_oi_threshold` | config | "BTC" | 15.0 | unit |

### Layer 1: Exchange (S03, S04-S09)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T020 | `test_symbol_mapper_binance` | exchange | "BTC" | "BTCUSDT", "BTCUSD_PERP" | unit |
| T021 | `test_symbol_mapper_okx` | exchange | "BTC" | "BTC-USDT-SWAP" | unit |
| T022 | `test_symbol_mapper_all_oi` | exchange | "BTC" | >= 12 entries | unit |
| T023 | `test_rate_limiter_under` | exchange | 5 requests, limit=5 | No block | unit |
| T024 | `test_rate_limiter_over` | exchange | 3 requests, limit=2 | Blocks ~100ms | unit |
| T030 | `test_binance_ticker` | binance | Mock 200 + JSON | Ticker with correct price | integration |
| T031 | `test_binance_oi` | binance | Mock 200 + JSON | OI f64 value | integration |
| T032 | `test_binance_funding` | binance | Mock 200 + JSON | Funding rate f64 | integration |
| T033 | `test_binance_ohlcv` | binance | Mock array-of-arrays | Vec\<Ohlcv\> len=2 | integration |
| T034 | `test_binance_balance_no_key` | binance | No API key | Empty vec | integration |
| T035 | `test_binance_api_error` | binance | Mock 400 | ExchangeError variant | integration |
| T036 | `test_binance_historical_oi` | binance | Mock JSON array | Vec<(f64, i64)> | integration |
| T040 | `test_bybit_ticker` | bybit | Mock V5 response | Ticker, pct * 100 | integration |
| T041 | `test_bybit_oi` | bybit | Mock V5 OI | OI f64 | integration |
| T042 | `test_bybit_funding` | bybit | Mock funding | Rate f64 | integration |
| T043 | `test_bybit_error` | bybit | retCode != 0 | ExchangeError | integration |
| T050 | `test_okx_ticker` | okx | Mock V5 response | Ticker | integration |
| T051 | `test_okx_oi` | okx | Mock OI | OI f64 | integration |
| T052 | `test_okx_funding` | okx | Mock funding | Rate f64 | integration |
| T053 | `test_okx_error` | okx | code != "0" | ExchangeError | integration |
| T060 | `test_gateio_ticker` | gateio | Mock response | Ticker | integration |
| T061 | `test_gateio_oi` | gateio | Mock response | OI f64 | integration |
| T062 | `test_gateio_404` | gateio | Mock 404 | ExchangeError | integration |
| T070 | `test_bitget_ticker` | bitget | Mock response | Ticker | integration |
| T071 | `test_bitget_oi` | bitget | Mock response | OI f64 | integration |
| T072 | `test_bitget_error` | bitget | code != "00000" | ExchangeError | integration |
| T080 | `test_hyperliquid_ticker` | hyperliquid | Mock POST | Ticker from meta | integration |
| T081 | `test_hyperliquid_oi` | hyperliquid | Mock POST | OI f64 | integration |
| T082 | `test_hyperliquid_meta` | hyperliquid | Mock POST | Universe parsed | integration |

### Layer 2: Analysis (S10-S15)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T100 | `test_rsi_all_gains` | indicators | 20 ascending closes | RSI ≈ 100 | unit |
| T101 | `test_rsi_all_losses` | indicators | 20 descending closes | RSI ≈ 0 | unit |
| T102 | `test_rsi_neutral` | indicators | Alternating closes | 40 < RSI < 60 | unit |
| T103 | `test_rsi_insufficient` | indicators | 10 closes, period=14 | None | unit |
| T104 | `test_vwap_simple` | indicators | 2 known candles | VWAP ≈ 102.22 | unit |
| T105 | `test_vwap_empty` | indicators | 0 candles | None | unit |
| T106 | `test_atr_known` | indicators | 3 candles, period=2 | ATR > 0 | unit |
| T107 | `test_bollinger_constant` | indicators | 25 × 100.0 | Bands collapse to 100 | unit |
| T108 | `test_bollinger_spread` | indicators | [98,99,100,101,102] | Upper≈102.83, Lower≈97.17 | unit |
| T109 | `test_volume_ratio` | indicators | [100,100,100,100,200] | 2.0 | unit |
| T110 | `test_volatility_constant` | indicators | 20 × 100.0 | 0.0 | unit |
| T111 | `test_calculate_all` | indicators | 100 candles | All fields Some | unit |
| T120 | `test_split_volume_bullish` | volume | close=high | (1000, 0) | unit |
| T121 | `test_split_volume_bearish` | volume | close=low | (0, 1000) | unit |
| T122 | `test_split_volume_doji` | volume | high=low | (500, 500) | unit |
| T123 | `test_split_volume_midpoint` | volume | close=mid | (500, 500) | unit |
| T124 | `test_classify_spike_levels` | volume | 50, 150, 300, 600 | N, M, H, E | unit |
| T125 | `test_spike_normal` | volume | 50 × vol=100, last=100 | Normal, not significant | unit |
| T126 | `test_spike_extreme` | volume | 50 × vol=100, last=1000 | Extreme, significant | unit |
| T127 | `test_spike_insufficient` | volume | 5 candles | None | unit |
| T128 | `test_cvd_bullish` | volume | 50 × close=high | Bullish, CVD > 0 | unit |
| T129 | `test_cvd_bearish` | volume | 50 × close=low | Bearish, CVD < 0 | unit |
| T130 | `test_cvd_divergence` | volume | price up, close near low | divergence = true | unit |
| T131 | `test_cvd_empty` | volume | 0 candles | None | unit |
| T140 | `test_profile_poc` | profile | Clustered candles | POC at cluster price | unit |
| T141 | `test_value_area_70pct` | profile | Diverse candles | VA vol >= 70% total | unit |
| T142 | `test_vah_above_val` | profile | Any candles | VAH >= POC >= VAL | unit |
| T143 | `test_profile_vwap_distance` | profile | Known price + VWAP | Correct % | unit |
| T144 | `test_profile_empty` | profile | 0 candles | None | unit |
| T150 | `test_session_ny` | session | 15:30 UTC | NewYork | unit |
| T151 | `test_session_asia` | session | 23:00 UTC | Asia | unit |
| T152 | `test_session_london` | session | 08:00 UTC | London | unit |
| T153 | `test_session_totals` | session | Mixed candles | Sum = total vol | unit |
| T160 | `test_sentiment_bull` | sentiment | +6%, EXTREME, BULL, RSI=65 | score > 50 | unit |
| T161 | `test_sentiment_bear` | sentiment | -6%, none, BEAR+div, RSI=25 | score < -30 | unit |
| T162 | `test_sentiment_neutral` | sentiment | +0.5%, none, NEUTRAL, RSI=50 | -30 ≤ s ≤ 30 | unit |
| T163 | `test_sentiment_divergence` | sentiment | BULL CVD + divergence | Lower than without | unit |
| T164 | `test_sentiment_none_inputs` | sentiment | All None | Valid score range | unit |

### Layer 3: Formatting (S16)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T200 | `test_format_large_number_billions` | formatting | 3.2e9 | "3.20B" | unit |
| T201 | `test_format_large_number_millions` | formatting | 1.5e8 | "150.00M" | unit |
| T202 | `test_format_large_number_thousands` | formatting | 15000.0 | "15.00K" | unit |
| T203 | `test_format_large_number_small` | formatting | 500.0 | "500.00" | unit |
| T204 | `test_format_large_number_negative` | formatting | -2.5e6 | "-2.50M" | unit |
| T205 | `test_format_large_number_zero` | formatting | 0.0 | "0.00" | unit |
| T206 | `test_format_percentage_positive` | formatting | 2.35 | "+2.35%" | unit |
| T207 | `test_format_percentage_negative` | formatting | -1.5 | "-1.50%" | unit |
| T208 | `test_format_dollar_positive` | formatting | 1234.56 | "+$1,234.56" | unit |
| T209 | `test_format_dollar_negative` | formatting | -500.0 | "-$500.00" | unit |
| T210 | `test_format_funding_rate` | formatting | 0.0001 | "+0.01%" | unit |
| T211 | `test_change_emoji` | formatting | 5.0, -3.0, 0.0 | 🟢, 🔴, ⚪ | unit |
| T212 | `test_format_price_large` | formatting | 43250.5 | Contains "$43,250" | unit |
| T213 | `test_format_price_small` | formatting | 0.00523 | Contains "0.00523" | unit |
| T214 | `test_format_oi_change_positive` | formatting | 5e6, 1e8 | "+5.00M (+5.00%)" | unit |
| T215 | `test_format_oi_change_negative` | formatting | -3e6, 1e8 | "-3.00M (-3.00%)" | unit |

### Layer 4: Telegram (S17)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T300 | `test_parse_both_args` | telegram | "eth 4h" | ("ETH", "4h") | unit |
| T301 | `test_parse_symbol_only` | telegram | "sol" | ("SOL", "15m") | unit |
| T302 | `test_parse_empty` | telegram | "" | ("BTC", "15m") | unit |
| T303 | `test_authorized_empty` | telegram | empty set, id=12345 | true | unit |
| T304 | `test_authorized_match` | telegram | {12345}, id=12345 | true | unit |
| T305 | `test_authorized_reject` | telegram | {12345}, id=99999 | false | unit |

### Layer 5: Database (S18)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T400 | `test_insert_and_query` | db | Insert alert | is_duplicate = true | integration |
| T401 | `test_not_duplicate_different` | db | Insert BTC, check ETH | false | integration |
| T402 | `test_cleanup_old` | db | 48h old alert, retain=24h | Removed | integration |

### Layer 6: Monitoring (S19)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T500 | `test_oi_detector_alert` | monitoring | 20% OI change, threshold=15% | Alert sent | integration |
| T501 | `test_oi_detector_no_alert` | monitoring | 5% OI change, threshold=15% | No alert | integration |
| T502 | `test_alert_dedup` | monitoring | Same alert within 5min | Second skipped | integration |
| T503 | `test_format_oi_alert` | monitoring | "BTC", 18.5, 2.8e9 | Contains all values | unit |

### Smoke Tests (S21)

| ID | Test Name | Module | Input | Expected Output | Type |
|----|-----------|--------|-------|-----------------|------|
| T600 | `container_builds` | container | Containerfile | Exit 0 | smoke |
| T601 | `image_size_limit` | container | Built image | < 150 MB | smoke |
| T602 | `missing_token_error` | container | No env vars | Error mentions token | smoke |
| T603 | `binary_exists` | container | ls crypto-bot | Executable file | smoke |

---

## Total Test Count

| Category | Count |
|----------|-------|
| Types & Config | 13 |
| Exchange Trait | 5 |
| Exchange Clients (6) | 22 |
| Indicators | 12 |
| Volume / CVD | 12 |
| Profile | 5 |
| Session | 4 |
| Sentiment | 5 |
| Formatting | 16 |
| Telegram | 6 |
| Database | 3 |
| Monitoring | 4 |
| Smoke | 4 |
| **TOTAL** | **111** |

---

## Test Data Fixtures

Agents MUST create JSON fixtures in `tests/fixtures/` for wiremock tests:

| File | Contents | Used By |
|------|----------|---------|
| `ohlcv_btc_15m.json` | 100 Binance kline arrays | T033, T100-T111 |
| `ticker_btc.json` | Binance spot ticker | T030 |
| `oi_binance.json` | Binance OI response | T031, T036 |
| `ticker_bybit.json` | Bybit V5 ticker | T040 |
| `ticker_okx.json` | OKX V5 ticker | T050 |

---

## Test Commands

```bash
# Run all tests
cargo test

# Run specific test category
cargo test types_test
cargo test indicators_test
cargo test binance

# Run with output
cargo test -- --nocapture

# Run single test
cargo test test_rsi_all_gains

# Coverage (requires cargo-tarpaulin)
cargo tarpaulin --out Html
```
