# S18 — Database (SQLite via SQLx)

## Scope
Alert history storage, deduplication tracking. Minimal schema.

## Dependencies
- S01 (types: Alert), S02 (Config: database_url)

## Files to Create

### `src/db.rs`

```rust
use sqlx::SqlitePool;
use crate::types::Alert;
use chrono::{DateTime, Utc};

/// Database connection pool and operations.
pub struct Db {
    pool: SqlitePool,
}

impl Db {
    /// Connect to SQLite and run migrations.
    pub async fn connect(database_url: &str) -> anyhow::Result<Self> {
        let pool = SqlitePool::connect(database_url).await?;
        sqlx::migrate!("./migrations").run(&pool).await?;
        Ok(Self { pool })
    }

    /// Insert an alert into history.
    pub async fn insert_alert(&self, alert: &Alert) -> anyhow::Result<()> {
        sqlx::query(
            "INSERT INTO alert_history (id, alert_type, priority, symbol, message, created_at)
             VALUES (?, ?, ?, ?, ?, ?)"
        )
        .bind(&alert.id)
        .bind(&alert.alert_type)
        .bind(alert.priority as i32)
        .bind(&alert.symbol)
        .bind(&alert.message)
        .bind(alert.created_at)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Check if an alert with this type + symbol was sent within the dedup window.
    pub async fn is_duplicate(
        &self,
        alert_type: &str,
        symbol: &str,
        window_mins: u64,
    ) -> anyhow::Result<bool> {
        let cutoff = Utc::now() - chrono::Duration::minutes(window_mins as i64);
        let count: (i64,) = sqlx::query_as(
            "SELECT COUNT(*) FROM alert_history
             WHERE alert_type = ? AND symbol = ? AND created_at > ?"
        )
        .bind(alert_type)
        .bind(symbol)
        .bind(cutoff)
        .fetch_one(&self.pool)
        .await?;
        Ok(count.0 > 0)
    }

    /// Clean up old alerts beyond retention period.
    pub async fn cleanup(&self, retain_hours: u64) -> anyhow::Result<u64> {
        let cutoff = Utc::now() - chrono::Duration::hours(retain_hours as i64);
        let result = sqlx::query("DELETE FROM alert_history WHERE created_at < ?")
            .bind(cutoff)
            .execute(&self.pool)
            .await?;
        Ok(result.rows_affected())
    }
}
```

### `migrations/001_initial.sql`

```sql
CREATE TABLE IF NOT EXISTS alert_history (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    priority INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alert_type_symbol ON alert_history(alert_type, symbol, created_at);
```

## Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{Alert, AlertPriority};

    async fn test_db() -> Db {
        Db::connect("sqlite::memory:").await.unwrap()
    }

    #[tokio::test]
    async fn test_insert_and_query() {
        let db = test_db().await;
        let alert = Alert {
            id: "test-1".to_string(),
            priority: AlertPriority::High,
            alert_type: "oi_explosion".to_string(),
            symbol: "BTC".to_string(),
            message: "OI exploded".to_string(),
            created_at: Utc::now(),
        };
        db.insert_alert(&alert).await.unwrap();
        assert!(db.is_duplicate("oi_explosion", "BTC", 5).await.unwrap());
    }

    #[tokio::test]
    async fn test_not_duplicate_different_symbol() {
        let db = test_db().await;
        let alert = Alert {
            id: "test-2".to_string(),
            priority: AlertPriority::Medium,
            alert_type: "oi_explosion".to_string(),
            symbol: "BTC".to_string(),
            message: "msg".to_string(),
            created_at: Utc::now(),
        };
        db.insert_alert(&alert).await.unwrap();
        assert!(!db.is_duplicate("oi_explosion", "ETH", 5).await.unwrap());
    }

    #[tokio::test]
    async fn test_cleanup_removes_old() {
        let db = test_db().await;
        let old_alert = Alert {
            id: "old-1".to_string(),
            priority: AlertPriority::Low,
            alert_type: "test".to_string(),
            symbol: "BTC".to_string(),
            message: "old".to_string(),
            created_at: Utc::now() - chrono::Duration::hours(48),
        };
        db.insert_alert(&old_alert).await.unwrap();
        let removed = db.cleanup(24).await.unwrap();
        assert_eq!(removed, 1);
    }
}
```

## Exit Criteria

- [ ] SQLite in-memory tests pass (no file dependency)
- [ ] `insert_alert` stores all fields
- [ ] `is_duplicate` detects same type+symbol within window
- [ ] `is_duplicate` returns false for different symbol
- [ ] `cleanup` removes alerts older than retention period
- [ ] All 3 tests pass
- [ ] Migration runs automatically on connect
