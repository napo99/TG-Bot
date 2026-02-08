# S16 — Formatting Utilities

## Scope
All number/string formatting for Telegram messages. Pure functions, no I/O.

Matches the Python `formatting_utils.py` output exactly. Users expect the same visual format.

## Dependencies
- S01 (types)

## Files to Create

### `src/telegram/formatting.rs`

```rust
/// Format large number with B/M/K suffix.
/// Examples: 3_200_000_000 → "3.20B", 150_000_000 → "150.00M", 15_000 → "15.00K"
pub fn format_large_number(value: f64) -> String {
    let abs = value.abs();
    let (scaled, suffix) = if abs >= 1_000_000_000.0 {
        (value / 1_000_000_000.0, "B")
    } else if abs >= 1_000_000.0 {
        (value / 1_000_000.0, "M")
    } else if abs >= 1_000.0 {
        (value / 1_000.0, "K")
    } else {
        (value, "")
    };
    format!("{scaled:.2}{suffix}")
}

/// Format price with dollar sign and commas.
/// Examples: 43250.5 → "$43,250.50", 0.5234 → "$0.52"
pub fn format_price(price: f64) -> String {
    // Determine decimal places based on magnitude
    // >= 1.0: 2 decimals
    // < 1.0: up to 6 significant digits
    // Add comma separators for thousands
}

/// Format percentage with sign and symbol.
/// Examples: 2.35 → "+2.35%", -1.5 → "-1.50%"
pub fn format_percentage(pct: f64) -> String {
    if pct >= 0.0 {
        format!("+{pct:.2}%")
    } else {
        format!("{pct:.2}%")
    }
}

/// Format dollar amount with sign.
/// Examples: 1234.56 → "+$1,234.56", -500.0 → "-$500.00"
pub fn format_dollar_amount(amount: f64) -> String {
    let sign = if amount >= 0.0 { "+" } else { "-" };
    let abs = amount.abs();
    format!("{sign}${}", format_with_commas(abs))
}

/// Format funding rate.
/// Examples: 0.0001 → "+0.0100%", -0.0003 → "-0.0300%"
pub fn format_funding_rate(rate: f64) -> String {
    let pct = rate * 100.0;
    format_percentage(pct)
}

/// Emoji for positive/negative change.
pub fn change_emoji(pct: f64) -> &'static str {
    if pct > 0.0 { "🟢" } else if pct < 0.0 { "🔴" } else { "⚪" }
}

/// Format timestamp in dual timezone (UTC + SGT).
/// Output: "14:32:45 UTC / 22:32:45 SGT"
pub fn format_dual_timestamp(ts: chrono::DateTime<chrono::Utc>) -> String {
    let utc = ts.format("%H:%M:%S UTC");
    let sgt = (ts + chrono::Duration::hours(8)).format("%H:%M:%S SGT");
    format!("{utc} / {sgt}")
}

/// Format volume in tokens and USD.
/// Examples: (15234.0, "BTC", 43250.0) → "15,234.00 BTC ($658.9M)"
pub fn format_volume_with_usd(volume: f64, token: &str, price: f64) -> String {
    let usd = volume * price;
    format!("{} {token} (${usd})",
        format_with_commas(volume),
        usd = format_large_number(usd),
    )
}

/// Format OI change in tokens and percentage.
pub fn format_oi_change(change: f64, current_oi: f64) -> String {
    let pct = if current_oi != 0.0 { change / current_oi * 100.0 } else { 0.0 };
    let sign = if change >= 0.0 { "+" } else { "" };
    format!("{sign}{} ({sign}{pct:.2}%)", format_large_number(change))
}

// Internal helper
fn format_with_commas(value: f64) -> String {
    // Format f64 to 2 decimal places with comma separators
    // 43250.5 → "43,250.50"
}
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_large_number() {
        assert_eq!(format_large_number(3_200_000_000.0), "3.20B");
        assert_eq!(format_large_number(150_000_000.0), "150.00M");
        assert_eq!(format_large_number(15_000.0), "15.00K");
        assert_eq!(format_large_number(500.0), "500.00");
        assert_eq!(format_large_number(-2_500_000.0), "-2.50M");
        assert_eq!(format_large_number(0.0), "0.00");
    }

    #[test]
    fn test_format_percentage() {
        assert_eq!(format_percentage(2.35), "+2.35%");
        assert_eq!(format_percentage(-1.5), "-1.50%");
        assert_eq!(format_percentage(0.0), "+0.00%");
    }

    #[test]
    fn test_format_dollar_amount() {
        assert_eq!(format_dollar_amount(1234.56), "+$1,234.56");
        assert_eq!(format_dollar_amount(-500.0), "-$500.00");
    }

    #[test]
    fn test_format_funding_rate() {
        assert_eq!(format_funding_rate(0.0001), "+0.01%");
        assert_eq!(format_funding_rate(-0.0003), "-0.03%");
    }

    #[test]
    fn test_change_emoji() {
        assert_eq!(change_emoji(5.0), "🟢");
        assert_eq!(change_emoji(-3.0), "🔴");
        assert_eq!(change_emoji(0.0), "⚪");
    }

    #[test]
    fn test_format_price_large() {
        let p = format_price(43250.5);
        assert!(p.contains("43,250"));
        assert!(p.starts_with('$'));
    }

    #[test]
    fn test_format_price_small() {
        let p = format_price(0.00523);
        assert!(p.starts_with('$'));
        assert!(p.contains("0.00523"));
    }

    #[test]
    fn test_format_oi_change_positive() {
        let s = format_oi_change(5_000_000.0, 100_000_000.0);
        assert!(s.contains("+5.00M"));
        assert!(s.contains("+5.00%"));
    }

    #[test]
    fn test_format_oi_change_negative() {
        let s = format_oi_change(-3_000_000.0, 100_000_000.0);
        assert!(s.contains("-3.00M"));
        assert!(s.contains("-3.00%"));
    }
}
```

## Exit Criteria

- [ ] `format_large_number` handles B, M, K, raw, zero, and negative
- [ ] `format_percentage` always shows sign
- [ ] `format_price` has commas and appropriate decimals
- [ ] `format_funding_rate` converts from decimal to percentage
- [ ] `change_emoji` returns correct emoji for positive/negative/zero
- [ ] All 9 tests pass
- [ ] Output matches Python formatting_utils.py behavior
