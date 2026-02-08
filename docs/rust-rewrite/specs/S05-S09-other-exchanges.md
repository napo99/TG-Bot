# S05-S09 — Other Exchange Clients (Bybit, OKX, Gate.io, Bitget, Hyperliquid)

## Scope
Implement the `Exchange` trait for each remaining exchange. Each exchange follows the same pattern as Binance (S04) but with exchange-specific API URLs and response formats.

All 5 exchanges can be implemented in parallel by separate agents.

## Dependencies
- S03 (Exchange trait)

## Common Pattern

Each exchange client:
1. Struct with `http: reqwest::Client`, `rate_limiter: RateLimiter`
2. Implements `Exchange` trait (6 methods)
3. Uses `SymbolMapper` for symbol format conversion
4. Has wiremock tests for all endpoints

---

## S05 — Bybit (`src/exchange/bybit.rs`)

### API Reference

| Purpose | Base URL | Path | Params |
|---------|----------|------|--------|
| Ticker | api.bybit.com | /v5/market/tickers | category=linear&symbol={sym} |
| OI | api.bybit.com | /v5/market/open-interest | category=linear&symbol={sym}&intervalTime=5min |
| Funding | api.bybit.com | /v5/market/funding/history | category=linear&symbol={sym}&limit=1 |
| Klines | api.bybit.com | /v5/market/kline | category=linear&symbol={sym}&interval={tf}&limit={n} |

### Response Format (all Bybit V5 responses)
```json
{
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "list": [/* data here */]
    }
}
```

### Ticker list item
```json
{"symbol": "BTCUSDT", "lastPrice": "43250.50", "volume24h": "15234.567", "price24hPcnt": "0.0235"}
```
Note: `price24hPcnt` is a decimal (0.0235 = 2.35%), multiply by 100.

### Symbol formats
- USDT: `BTCUSDT`
- USDC: `BTCPERP` (Bybit uses PERP suffix for USDC)
- Inverse: `BTCUSD`

### Tests (minimum 4)
- `test_fetch_ticker_bybit` — mock V5 ticker, verify parsing
- `test_fetch_oi_bybit` — mock OI response
- `test_fetch_funding_bybit` — mock funding response
- `test_bybit_error_handling` — mock retCode != 0

---

## S06 — OKX (`src/exchange/okx.rs`)

### API Reference

| Purpose | Base URL | Path | Params |
|---------|----------|------|--------|
| Ticker | www.okx.com | /api/v5/market/ticker | instId={sym} |
| OI | www.okx.com | /api/v5/public/open-interest | instType=SWAP&instId={sym} |
| Funding | www.okx.com | /api/v5/public/funding-rate | instId={sym} |
| Klines | www.okx.com | /api/v5/market/candles | instId={sym}&bar={tf}&limit={n} |

### Response Format
```json
{
    "code": "0",
    "msg": "",
    "data": [/* items */]
}
```
Note: `code` is a string "0" for success.

### Ticker data item
```json
{"instId": "BTC-USDT-SWAP", "last": "43250.5", "vol24h": "15234.567", "volCcy24h": "659242567.89"}
```
Note: OKX ticker does NOT have a percentage change field. Calculate from open24h if available, or omit.

### Symbol formats
- USDT: `BTC-USDT-SWAP`
- USDC: `BTC-USDC-SWAP`
- Inverse: `BTC-USD-SWAP`

### Tests (minimum 4)
- `test_fetch_ticker_okx` — verify OKX's string code parsing
- `test_fetch_oi_okx` — verify OI from swap endpoint
- `test_fetch_funding_okx` — verify funding rate parsing
- `test_okx_error_non_zero_code` — mock code != "0"

---

## S07 — Gate.io (`src/exchange/gateio.rs`)

### API Reference

| Purpose | Base URL | Path | Params |
|---------|----------|------|--------|
| Ticker | api.gateio.ws | /api/v4/futures/usdt/contracts/{sym} | — |
| OI | api.gateio.ws | /api/v4/futures/usdt/contracts/{sym} | — (field: open_interest) |
| Funding | api.gateio.ws | /api/v4/futures/usdt/contracts/{sym} | — (field: funding_rate) |
| Klines | api.gateio.ws | /api/v4/futures/usdt/candlesticks | contract={sym}&interval={tf}&limit={n} |

### Response Format
Gate.io returns direct JSON objects (no wrapper):
```json
{"name": "BTC_USDT", "last_price": "43250.5", "volume_24h": "15234", "open_interest": "65432"}
```

### Symbol formats
- USDT: `BTC_USDT`
- USDC: `BTC_USDC`
- Inverse: `BTC_USD`

### Tests (minimum 3)
- `test_fetch_ticker_gateio`
- `test_fetch_oi_gateio`
- `test_gateio_404_symbol`

---

## S08 — Bitget (`src/exchange/bitget.rs`)

### API Reference

| Purpose | Base URL | Path | Params |
|---------|----------|------|--------|
| Ticker | api.bitget.com | /api/v2/mix/market/ticker | symbol={sym}&productType=USDT-FUTURES |
| OI | api.bitget.com | /api/v2/mix/market/open-interest | symbol={sym}&productType=USDT-FUTURES |
| Funding | api.bitget.com | /api/v2/mix/market/current-fund-rate | symbol={sym}&productType=USDT-FUTURES |

### Response Format
```json
{"code": "00000", "msg": "success", "data": {/* ... */}}
```

### Symbol formats
- USDT: `BTCUSDT` (with productType=USDT-FUTURES)
- Inverse: `BTCUSD` (with productType=COIN-FUTURES)

### Tests (minimum 3)
- `test_fetch_ticker_bitget`
- `test_fetch_oi_bitget`
- `test_bitget_error_code`

---

## S09 — Hyperliquid (`src/exchange/hyperliquid.rs`)

### API Reference

| Purpose | Base URL | Path | Method | Body |
|---------|----------|------|--------|------|
| All data | api.hyperliquid.xyz | /info | POST | `{"type": "metaAndAssetCtxs"}` |

Hyperliquid is unique: single POST endpoint returns ALL data.

### Response Format
```json
[
    {"universe": [{"name": "BTC", "szDecimals": 5}]},
    [{"funding": "0.00010000", "openInterest": "1234.5", "dayNtlVlm": "50000000", "markPx": "43250.50"}]
]
```

The response is a 2-element array:
- `[0].universe`: list of assets with metadata
- `[1]`: list of asset contexts (same index order as universe)

### Symbol format
- Just base symbol: `BTC`, `ETH` (Hyperliquid uses plain names)

### Tests (minimum 3)
- `test_fetch_ticker_hyperliquid`
- `test_fetch_oi_hyperliquid`
- `test_hyperliquid_meta_parsing`

---

## Exit Criteria (Per Exchange)

- [ ] Implements all 6 `Exchange` trait methods
- [ ] Rate limiter called before every request
- [ ] Response parsing handles string-to-f64 conversion safely
- [ ] API errors return appropriate `ExchangeError` variants
- [ ] Minimum 3 wiremock tests pass per exchange
- [ ] `cargo clippy` clean
- [ ] `fetch_balance()` and `fetch_positions()` return empty vec (read-only for non-Binance)
