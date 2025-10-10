-- PostgreSQL DDL to create a unified view for transactions with joined names
-- This view allows the server to fetch all display-ready transaction data in one query.
--
-- Dependencies (FK-like relationships assumed):
--   transaction_dtl.portfolio_id         -> portfolio_dtl.portfolio_id
--   transaction_dtl.security_id          -> security_dtl.security_id
--   transaction_dtl.external_platform_id  -> external_platform_dtl.external_platform_id
--   portfolio_dtl.user_id                -> user_dtl.user_id
--
-- Usage:
--   Run this SQL in your Postgres database (psql, Adminer, DBeaver, etc.).
--   Then query:  SELECT * FROM v_transaction_full ORDER BY transaction_id DESC LIMIT 50;
--
-- Notes:
--   - LEFT JOINs are used so rows still appear even if a reference record is missing.
--   - Computed columns (gross_amount, total_fee, net_amount) are included for convenience; remove if not needed.
--   - Consider adding indexes (see suggestions at bottom) for large datasets.

DROP VIEW IF EXISTS v_transaction_full;

CREATE OR REPLACE VIEW v_transaction_full AS
SELECT
    t.transaction_id,
    -- Core foreign keys and their display names
    t.portfolio_id,
    pf.name                         AS portfolio_name,
    pf.user_id                      AS user_id,
    (COALESCE(u.first_name, '') || CASE WHEN u.first_name IS NOT NULL AND u.last_name IS NOT NULL THEN ' ' ELSE '' END || COALESCE(u.last_name, ''))
                                     AS user_full_name,

    t.security_id,
    s.ticker                        AS security_ticker,
    s.name                          AS security_name,

    t.external_platform_id,
    ep.name                         AS external_platform_name,

    -- Transaction details
    t.transaction_date,
    t.transaction_type,
    t.transaction_qty,
    t.transaction_price,
    t.transaction_fee,
    t.transaction_fee_percent,
    t.carry_fee,
    t.carry_fee_percent,
    t.management_fee,
    t.management_fee_percent,
    t.external_manager_fee,
    t.external_manager_fee_percent,

    -- Convenience computed amounts
    (t.transaction_qty * t.transaction_price)                                AS gross_amount,
    (COALESCE(t.transaction_fee, 0)
     + COALESCE(t.carry_fee, 0)
     + COALESCE(t.management_fee, 0)
     + COALESCE(t.external_manager_fee, 0))                                  AS total_fee,
    ((t.transaction_qty * t.transaction_price)
     - (COALESCE(t.transaction_fee, 0)
        + COALESCE(t.carry_fee, 0)
        + COALESCE(t.management_fee, 0)
        + COALESCE(t.external_manager_fee, 0)))                              AS net_amount,

    -- Persisted or computed total investment amount
    t.total_inv_amt,
    
    -- Related transaction ID for duplicate tracking
    t.rel_transaction_id,

    -- Timestamps
    t.created_ts,
    t.last_updated_ts
FROM transaction_dtl t
LEFT JOIN portfolio_dtl pf
    ON pf.portfolio_id = t.portfolio_id
LEFT JOIN user_dtl u
    ON u.user_id = pf.user_id
LEFT JOIN security_dtl s
    ON s.security_id = t.security_id
LEFT JOIN external_platform_dtl ep
    ON ep.external_platform_id = t.external_platform_id;

-- Optional: grant privileges (adjust role/user as needed)
-- GRANT SELECT ON v_transaction_full TO your_app_role;

-- Performance suggestions (execute as needed):
-- CREATE INDEX IF NOT EXISTS idx_transaction_dtl_portfolio_id ON transaction_dtl (portfolio_id);
-- CREATE INDEX IF NOT EXISTS idx_transaction_dtl_security_id ON transaction_dtl (security_id);
-- CREATE INDEX IF NOT EXISTS idx_transaction_dtl_platform_id ON transaction_dtl (external_platform_id);
-- CREATE INDEX IF NOT EXISTS idx_portfolio_dtl_user_id ON portfolio_dtl (user_id);
-- CREATE INDEX IF NOT EXISTS idx_transaction_dtl_date ON transaction_dtl (transaction_date);
