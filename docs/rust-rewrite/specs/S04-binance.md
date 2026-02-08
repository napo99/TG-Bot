# S04 — Binance Exchange Client

## Scope
Implement the `Exchange` trait for Binance. Covers:
- Spot API (api.binance.com)
- USD-M Futures / FAPI (fapi.binance.com)
- COIN-M Futures / DAPI (dapi.binance.com)
- Historical OI endpoint
- HMAC-SHA256 signed requests for authenticated endpoints

## Dependencies
- S03 (Exchange trait, RateLimiter, SymbolMapper)

## Files to Create

### `src/exchange/binance.rs`

## API Endpoints (Reference from Python)

| Purpose | Base URL | Path | Method | Params |
|---------|----------|------|--------|--------|
| Spot ticker | api.binance.com | /api/v3/ticker/24hr | GET | symbol |
| FAPI ticker | fapi.binance.com | /fapi/v1/ticker/24hr | GET | symbol |
| FAPI OI | fapi.binance.com | /fapi/v1/openInterest | GET | symbol |
| FAPI funding | fapi.binance.com | /fapi/v1/premiumIndex | GET | symbol |
| FAPI klines | fapi.binance.com | /fapi/v1/klines | GET | symbol, interval, limit |
| DAPI ticker | dapi.binance.com | /dapi/v1/ticker/24hr | GET | symbol |
| DAPI OI | dapi.binance.com | /dapi/v1/openInterest | GET | symbol |
| DAPI funding | dapi.binance.com | /dapi/v1/premiumIndex | GET | symbol |
| Historical OI | fapi.binance.com | /futures/data/openInterestHist | GET | symbol, period, limit |
| Account balance | fapi.binance.com | /fapi/v2/balance | GET | (signed) |
| Positions | fapi.binance.com | /fapi/v2/positionRisk | GET | (signed) |
| Long/short ratio | fapi.binance.com | /futures/data/globalLongShortAccountRatio | GET | symbol, period, limit |

## Response Schemas (JSON)

### Spot Ticker
```json
{
    "symbol": "BTCUSDT",
    "lastPrice": "43250.50",
    "volume": "15234.567",
    "priceChangePercent": "2.35"
}
```

### FAPI Open Interest
```json
{
    "symbol": "BTCUSDT",
    "openInterest": "65432.100",
    "time": 1707350400000
}
```

### FAPI Premium Index (Funding)
```json
{
    "symbol": "BTCUSDT",
    "lastFundingRate": "0.00010000",
    "nextFundingTime": 1707379200000
}
```

### FAPI Klines
```json
[
    [1707350400000, "43200.00", "43300.00", "43100.00", "43250.50", "1234.56", ...],
    // [open_time, open, high, low, close, volume, ...]
]
```

### Historical OI
```json
[
    {"symbol": "BTCUSDT", "sumOpenInterest": "65000.00", "sumOpenInterestValue": "2812500000.00", "timestamp": 1707264000000}
]
```

## Implementation Requirements

```rust
pub struct BinanceClient {
    http: reqwest::Client,
    rate_limiter: RateLimiter,
    api_key: Option<String>,
    secret_key: Option<String>,
    testnet: bool,
}

impl BinanceClient {
    pub fn new(http: reqwest::Client, config: &Config) -> Self { ... }

    /// Base URL based on testnet flag
    fn fapi_base(&self) -> &str {
        if self.testnet { "https://testnet.binancefuture.com" }
        else { "https://fapi.binance.com" }
    }

    fn dapi_base(&self) -> &str {
        if self.testnet { "https://testnet.binancefuture.com" }
        else { "https://dapi.binance.com" }
    }

    fn spot_base(&self) -> &str { "https://api.binance.com" }

    /// HMAC-SHA256 signature for authenticated requests
    fn sign(&self, query: &str) -> Result<String, ExchangeError> { ... }

    /// Fetch historical OI for calculating 24h and 15m changes.
    /// `period`: "5m" or "1d"
    pub async fn fetch_historical_oi(
        &self,
        symbol: &str,
        period: &str,
        limit: u32,
    ) -> Result<Vec<(f64, i64)>, ExchangeError> { ... }
    // Returns Vec<(oi_value, timestamp_ms)>

    /// Fetch global long/short account ratio from Binance.
    pub async fn fetch_long_short_ratio(
        &self,
        symbol: &str,
    ) -> Result<f64, ExchangeError> { ... }
}

#[async_trait::async_trait]
impl Exchange for BinanceClient {
    fn name(&self) -> &str { "binance" }

    async fn fetch_ticker(&self, symbol: &str) -> Result<Ticker, ExchangeError> {
        self.rate_limiter.acquire().await;
        // Determine if spot or futures from symbol suffix
        // Parse response into Ticker
    }

    async fn fetch_ohlcv(
        &self, symbol: &str, timeframe: &str, limit: u32,
    ) -> Result<Vec<Ohlcv>, ExchangeError> {
        self.rate_limiter.acquire().await;
        // Call /fapi/v1/klines
        // Map interval names: "1m", "5m", "15m", "1h", "4h", "1d"
        // Parse array-of-arrays into Vec<Ohlcv>
    }

    async fn fetch_open_interest(&self, symbol: &str) -> Result<f64, ExchangeError> {
        self.rate_limiter.acquire().await;
        // Detect FAPI vs DAPI from symbol format
        // BTCUSDT → FAPI, BTCUSD_PERP → DAPI
        // Parse "openInterest" field as f64
    }

    async fn fetch_funding_rate(&self, symbol: &str) -> Result<f64, ExchangeError> {
        self.rate_limiter.acquire().await;
        // Call /fapi/v1/premiumIndex or /dapi/v1/premiumIndex
        // Parse "lastFundingRate" field as f64
    }

    async fn fetch_balance(&self) -> Result<Vec<Balance>, ExchangeError> {
        // If no API key, return Ok(vec![])
        // Otherwise: signed GET /fapi/v2/balance
        // Filter to non-zero balances
    }

    async fn fetch_positions(&self) -> Result<Vec<Position>, ExchangeError> {
        // If no API key, return Ok(vec![])
        // Otherwise: signed GET /fapi/v2/positionRisk
        // Filter to non-zero positions
        // Map side from "LONG"/"SHORT" to PositionSide
    }
}
```

## Tests

### Unit Tests (with wiremock)

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use wiremock::{MockServer, Mock, ResponseTemplate};
    use wiremock::matchers::{method, path, query_param};

    async fn setup_mock() -> (MockServer, BinanceClient) {
        let server = MockServer::start().await;
        // Create client pointing to mock server
        // ...
        (server, client)
    }

    #[tokio::test]
    async fn test_fetch_ticker_spot() {
        let (server, client) = setup_mock().await;
        Mock::given(method("GET"))
            .and(path("/api/v3/ticker/24hr"))
            .and(query_param("symbol", "BTCUSDT"))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
                "symbol": "BTCUSDT",
                "lastPrice": "43250.50",
                "volume": "15234.567",
                "priceChangePercent": "2.35"
            })))
            .mount(&server).await;

        let ticker = client.fetch_ticker("BTCUSDT").await.unwrap();
        assert_eq!(ticker.symbol, "BTCUSDT");
        assert!((ticker.price - 43250.50).abs() < 0.01);
        assert!((ticker.volume_24h - 15234.567).abs() < 0.001);
        assert!((ticker.change_24h_pct - 2.35).abs() < 0.01);
    }

    #[tokio::test]
    async fn test_fetch_open_interest_fapi() {
        let (server, client) = setup_mock().await;
        Mock::given(method("GET"))
            .and(path("/fapi/v1/openInterest"))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
                "symbol": "BTCUSDT",
                "openInterest": "65432.100",
                "time": 1707350400000_i64
            })))
            .mount(&server).await;

        let oi = client.fetch_open_interest("BTCUSDT").await.unwrap();
        assert!((oi - 65432.1).abs() < 0.1);
    }

    #[tokio::test]
    async fn test_fetch_funding_rate() {
        let (server, client) = setup_mock().await;
        Mock::given(method("GET"))
            .and(path("/fapi/v1/premiumIndex"))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
                "symbol": "BTCUSDT",
                "lastFundingRate": "0.00010000"
            })))
            .mount(&server).await;

        let rate = client.fetch_funding_rate("BTCUSDT").await.unwrap();
        assert!((rate - 0.0001).abs() < 1e-8);
    }

    #[tokio::test]
    async fn test_fetch_ohlcv_parses_array() {
        let (server, client) = setup_mock().await;
        Mock::given(method("GET"))
            .and(path("/fapi/v1/klines"))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
                [1707350400000_i64, "43200.00", "43300.00", "43100.00", "43250.50", "1234.56",
                 1707350459999_i64, "53456789.00", 500, "617.28", "26709876.00", "0"],
                [1707350460000_i64, "43250.50", "43400.00", "43200.00", "43350.00", "2345.67",
                 1707350519999_i64, "101567890.00", 800, "1172.84", "50784567.00", "0"]
            ])))
            .mount(&server).await;

        let candles = client.fetch_ohlcv("BTCUSDT", "1m", 2).await.unwrap();
        assert_eq!(candles.len(), 2);
        assert!((candles[0].open - 43200.0).abs() < 0.01);
        assert!((candles[0].close - 43250.50).abs() < 0.01);
        assert!((candles[0].volume - 1234.56).abs() < 0.01);
    }

    #[tokio::test]
    async fn test_fetch_balance_without_api_key() {
        let (_, client) = setup_mock().await;
        // Client created without API key
        let balances = client.fetch_balance().await.unwrap();
        assert!(balances.is_empty());
    }

    #[tokio::test]
    async fn test_api_error_returns_exchange_error() {
        let (server, client) = setup_mock().await;
        Mock::given(method("GET"))
            .and(path("/fapi/v1/openInterest"))
            .respond_with(ResponseTemplate::new(400).set_body_json(serde_json::json!({
                "code": -1121,
                "msg": "Invalid symbol."
            })))
            .mount(&server).await;

        let result = client.fetch_open_interest("INVALID").await;
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert!(matches!(err, ExchangeError::ApiError { .. } | ExchangeError::Parse { .. }));
    }

    #[tokio::test]
    async fn test_fetch_historical_oi() {
        let (server, client) = setup_mock().await;
        Mock::given(method("GET"))
            .and(path("/futures/data/openInterestHist"))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!([
                {"symbol": "BTCUSDT", "sumOpenInterest": "65000.00", "sumOpenInterestValue": "2812500000.00", "timestamp": 1707264000000_i64},
                {"symbol": "BTCUSDT", "sumOpenInterest": "65500.00", "sumOpenInterestValue": "2834125000.00", "timestamp": 1707350400000_i64}
            ])))
            .mount(&server).await;

        let hist = client.fetch_historical_oi("BTCUSDT", "1d", 2).await.unwrap();
        assert_eq!(hist.len(), 2);
        assert!((hist[0].0 - 65000.0).abs() < 0.1);
    }
}
```

## Exit Criteria

- [ ] `BinanceClient` implements all 6 methods of `Exchange` trait
- [ ] FAPI vs DAPI URL routing works based on symbol format
- [ ] OHLCV parsing handles Binance's array-of-arrays format
- [ ] HMAC signing is implemented (test with known test vectors)
- [ ] `fetch_balance()` and `fetch_positions()` return empty vec when no API key
- [ ] All 7 mock tests pass
- [ ] Rate limiter is called before every API request
- [ ] All string prices parsed to f64 without panic
