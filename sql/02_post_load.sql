-- =====================================================================================
-- Runs after the CSV bulk load: indexes, statistics and a convenience view.
-- (dim_date is built in 01b_dim_date.sql before the facts are loaded.)
-- =====================================================================================
SET search_path TO retail;

CREATE INDEX ix_tx_date      ON fact_transaction (date_key);
CREATE INDEX ix_tx_store     ON fact_transaction (store_id, date_key);
CREATE INDEX ix_tx_customer  ON fact_transaction (customer_id, date_key) WHERE customer_id IS NOT NULL;
CREATE INDEX ix_line_product ON fact_sales_line (product_id);
CREATE INDEX ix_line_promo   ON fact_sales_line (promo_id) WHERE promo_id IS NOT NULL;

ANALYZE;

-- Wide view used by many analytics queries and by Power BI DirectQuery if wanted.
CREATE OR REPLACE VIEW v_sales AS
SELECT  l.transaction_id, l.line_no, t.transaction_ts, t.date_key, d.month_start,
        t.store_id, s.store_name, s.county, s.store_format,
        t.customer_id, t.payment_method,
        l.product_id, p.product_name, p.category, p.subcategory,
        l.quantity, l.unit_price, l.discount_amount, l.net_amount, l.promo_id,
        d.is_weekend, d.is_payday_window, d.is_public_holiday,
        c.cpi_index, ROUND(l.net_amount * 100 / c.cpi_index, 2) AS net_amount_real
FROM    fact_sales_line l
JOIN    fact_transaction t ON t.transaction_id = l.transaction_id
JOIN    dim_store   s ON s.store_id   = t.store_id
JOIN    dim_product p ON p.product_id = l.product_id
JOIN    dim_date    d ON d.date_key   = t.date_key
JOIN    ref_cpi     c ON c.month      = d.month_start;
