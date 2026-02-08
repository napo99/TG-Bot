use thiserror::Error;

#[derive(Debug, Error)]
pub enum ExchangeError {
    #[error("HTTP request failed for {exchange}: {source}")]
    Http {
        exchange: String,
        #[source]
        source: reqwest::Error,
    },

    #[error("Failed to parse {exchange} response: {message}")]
    Parse { exchange: String, message: String },

    #[error("Rate limit hit for {exchange}")]
    RateLimited { exchange: String },

    #[error("{exchange} API error: {code} - {message}")]
    ApiError {
        exchange: String,
        code: i64,
        message: String,
    },

    #[error("Symbol {symbol} not found on {exchange}")]
    SymbolNotFound { exchange: String, symbol: String },

    #[error("Timeout waiting for {exchange}")]
    Timeout { exchange: String },
}
