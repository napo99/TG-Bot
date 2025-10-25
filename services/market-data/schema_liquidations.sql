-- ============================================================================
-- LIQUIDATION TRACKING SCHEMA WITH TIMESCALEDB
-- Multi-Level Storage Architecture
-- ============================================================================

-- Enable TimescaleDB extension (already done, but included for completeness)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- LEVEL 3: SIGNIFICANT LIQUIDATIONS TABLE
-- Only stores institutional-level liquidations (>$100K)
-- ============================================================================

CREATE TABLE IF NOT EXISTS liquidations_significant (
    time TIMESTAMPTZ NOT NULL,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    price NUMERIC NOT NULL,
    quantity NUMERIC NOT NULL,
    value_usd NUMERIC NOT NULL,

    -- Cascade context
    is_cascade BOOLEAN DEFAULT FALSE,
    cascade_id UUID,
    cascade_event_count INT,

    -- Risk scoring
    risk_score NUMERIC,
    session_type TEXT,  -- 'asian', 'european', 'us', 'weekend'

    -- Metadata
    raw_data JSONB,

    -- Composite primary key
    PRIMARY KEY (time, exchange, symbol, side)
);

-- Create hypertable (automatic partitioning by time)
SELECT create_hypertable(
    'liquidations_significant',
    'time',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- ============================================================================
-- INDEXES FOR FAST QUERIES
-- ============================================================================

-- Index for exchange queries
CREATE INDEX IF NOT EXISTS idx_liquidations_exchange
ON liquidations_significant (exchange, time DESC);

-- Index for symbol queries
CREATE INDEX IF NOT EXISTS idx_liquidations_symbol
ON liquidations_significant (symbol, time DESC);

-- Index for cascade queries
CREATE INDEX IF NOT EXISTS idx_liquidations_cascade
ON liquidations_significant (cascade_id, time DESC)
WHERE cascade_id IS NOT NULL;

-- Index for value-based queries (find large liquidations)
CREATE INDEX IF NOT EXISTS idx_liquidations_value
ON liquidations_significant (value_usd DESC, time DESC);

-- Index for side analysis
CREATE INDEX IF NOT EXISTS idx_liquidations_side
ON liquidations_significant (symbol, side, time DESC);

-- ============================================================================
-- COMPRESSION POLICY (10x space savings after 7 days)
-- ============================================================================

ALTER TABLE liquidations_significant SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'exchange,symbol',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy(
    'liquidations_significant',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- RETENTION POLICY (auto-delete data older than 90 days)
-- ============================================================================

SELECT add_retention_policy(
    'liquidations_significant',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- LEVEL 4: CONTINUOUS AGGREGATES (Pre-computed rollups)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. HOURLY ROLLUPS - Liquidation summary by hour
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS liquidations_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    exchange,
    symbol,
    side,
    COUNT(*) as event_count,
    SUM(value_usd) as total_value_usd,
    AVG(value_usd) as avg_value_usd,
    MAX(value_usd) as max_value_usd,
    MIN(value_usd) as min_value_usd,
    STDDEV(value_usd) as stddev_value_usd,
    SUM(quantity) as total_quantity,
    COUNT(*) FILTER (WHERE is_cascade) as cascade_count,
    AVG(risk_score) as avg_risk_score
FROM liquidations_significant
GROUP BY hour, exchange, symbol, side;

-- Refresh policy (auto-update every 10 minutes)
SELECT add_continuous_aggregate_policy(
    'liquidations_hourly',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '10 minutes',
    schedule_interval => INTERVAL '10 minutes',
    if_not_exists => TRUE
);

-- Index for fast hourly queries
CREATE INDEX IF NOT EXISTS idx_liquidations_hourly_symbol
ON liquidations_hourly (symbol, hour DESC);

-- ----------------------------------------------------------------------------
-- 2. PRICE LEVEL HEATMAP - WHERE liquidations cluster by price
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS liquidation_price_levels
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    symbol,
    -- Round to $100 levels for BTC/ETH, $10 for others
    CASE
        WHEN symbol IN ('BTCUSDT', 'ETHUSDT')
        THEN FLOOR(price / 100) * 100
        ELSE FLOOR(price / 10) * 10
    END AS price_level,
    side,
    exchange,
    COUNT(*) as liquidation_count,
    SUM(value_usd) as total_value_usd,
    SUM(quantity) as total_quantity,
    AVG(value_usd) as avg_liquidation_size
FROM liquidations_significant
GROUP BY hour, symbol, price_level, side, exchange
HAVING COUNT(*) >= 2;  -- Only show levels with 2+ liquidations

-- Refresh policy
SELECT add_continuous_aggregate_policy(
    'liquidation_price_levels',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '10 minutes',
    schedule_interval => INTERVAL '10 minutes',
    if_not_exists => TRUE
);

-- Index for heatmap queries
CREATE INDEX IF NOT EXISTS idx_price_levels_symbol
ON liquidation_price_levels (symbol, hour DESC, price_level);

-- ----------------------------------------------------------------------------
-- 3. EXCHANGE COMPARISON - Cross-exchange volume breakdown
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS liquidation_exchange_comparison
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('4 hours', time) AS period,
    symbol,
    exchange,
    COUNT(*) as event_count,
    SUM(value_usd) as total_value_usd,
    AVG(value_usd) as avg_value_usd,
    COUNT(*) FILTER (WHERE is_cascade) as cascade_count,
    COUNT(*) FILTER (WHERE side = 'LONG') as long_count,
    COUNT(*) FILTER (WHERE side = 'SHORT') as short_count
FROM liquidations_significant
GROUP BY period, symbol, exchange;

-- Refresh policy
SELECT add_continuous_aggregate_policy(
    'liquidation_exchange_comparison',
    start_offset => INTERVAL '8 hours',
    end_offset => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- ----------------------------------------------------------------------------
-- 4. CASCADE ANALYSIS - Detailed cascade event tracking
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS liquidation_cascades
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    cascade_id,
    symbol,
    MIN(time) as cascade_start,
    MAX(time) as cascade_end,
    EXTRACT(EPOCH FROM (MAX(time) - MIN(time))) as duration_seconds,
    COUNT(*) as event_count,
    SUM(value_usd) as total_value_usd,
    AVG(risk_score) as avg_risk_score,
    MAX(risk_score) as max_risk_score,
    array_agg(DISTINCT exchange) as exchanges_involved,
    COUNT(DISTINCT exchange) as exchange_count,
    COUNT(*) FILTER (WHERE side = 'LONG') as long_count,
    COUNT(*) FILTER (WHERE side = 'SHORT') as short_count
FROM liquidations_significant
WHERE cascade_id IS NOT NULL
GROUP BY hour, cascade_id, symbol;

-- Refresh policy
SELECT add_continuous_aggregate_policy(
    'liquidation_cascades',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE
);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get recent significant liquidations
CREATE OR REPLACE FUNCTION get_recent_liquidations(
    p_symbol TEXT,
    p_minutes INT DEFAULT 60
) RETURNS TABLE (
    time TIMESTAMPTZ,
    exchange TEXT,
    side TEXT,
    price NUMERIC,
    quantity NUMERIC,
    value_usd NUMERIC,
    is_cascade BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.time,
        l.exchange,
        l.side,
        l.price,
        l.quantity,
        l.value_usd,
        l.is_cascade
    FROM liquidations_significant l
    WHERE l.symbol = p_symbol
      AND l.time >= NOW() - (p_minutes || ' minutes')::INTERVAL
    ORDER BY l.time DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get price level clusters
CREATE OR REPLACE FUNCTION get_price_level_clusters(
    p_symbol TEXT,
    p_hours INT DEFAULT 4
) RETURNS TABLE (
    price_level NUMERIC,
    liquidation_count BIGINT,
    total_value_usd NUMERIC,
    long_percentage NUMERIC,
    exchanges TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN p_symbol IN ('BTCUSDT', 'ETHUSDT')
            THEN FLOOR(price / 100) * 100
            ELSE FLOOR(price / 10) * 10
        END AS price_level,
        COUNT(*) as liquidation_count,
        SUM(value_usd) as total_value_usd,
        ROUND((COUNT(*) FILTER (WHERE side = 'LONG')::NUMERIC / COUNT(*) * 100), 1) as long_percentage,
        array_agg(DISTINCT exchange) as exchanges
    FROM liquidations_significant
    WHERE symbol = p_symbol
      AND time >= NOW() - (p_hours || ' hours')::INTERVAL
    GROUP BY price_level
    HAVING COUNT(*) >= 2
    ORDER BY liquidation_count DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Function to get cascade details
CREATE OR REPLACE FUNCTION get_cascade_details(
    p_cascade_id UUID
) RETURNS TABLE (
    time TIMESTAMPTZ,
    exchange TEXT,
    symbol TEXT,
    side TEXT,
    price NUMERIC,
    value_usd NUMERIC,
    risk_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.time,
        l.exchange,
        l.symbol,
        l.side,
        l.price,
        l.value_usd,
        l.risk_score
    FROM liquidations_significant l
    WHERE l.cascade_id = p_cascade_id
    ORDER BY l.time ASC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Liquidation tracking schema created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Created tables:';
    RAISE NOTICE '  - liquidations_significant (hypertable)';
    RAISE NOTICE '';
    RAISE NOTICE '📈 Created continuous aggregates:';
    RAISE NOTICE '  - liquidations_hourly';
    RAISE NOTICE '  - liquidation_price_levels';
    RAISE NOTICE '  - liquidation_exchange_comparison';
    RAISE NOTICE '  - liquidation_cascades';
    RAISE NOTICE '';
    RAISE NOTICE '⚙️  Policies enabled:';
    RAISE NOTICE '  - Compression: 7 days (10x space savings)';
    RAISE NOTICE '  - Retention: 90 days (auto-delete)';
    RAISE NOTICE '  - Auto-refresh: Every 10-30 minutes';
    RAISE NOTICE '';
    RAISE NOTICE '🔍 Helper functions:';
    RAISE NOTICE '  - get_recent_liquidations(symbol, minutes)';
    RAISE NOTICE '  - get_price_level_clusters(symbol, hours)';
    RAISE NOTICE '  - get_cascade_details(cascade_id)';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Database ready for liquidation tracking!';
END $$;
