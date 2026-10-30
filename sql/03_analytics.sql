-- =====================================================================================
-- Milestone 4 - SQL analytics on the Mavuno Mart star schema (PostgreSQL 14+)
-- Each query starts with "-- name: <id>" so notebooks/04_sql_analytics can run them one by one.
-- Techniques covered: multi-table JOINs, GROUP BY / HAVING, CTEs, CASE, FILTER,
-- window functions (SUM/AVG OVER, LAG, RANK, DENSE_RANK, ROW_NUMBER, NTILE, moving
-- averages, running totals), cohort retention and RFM segmentation.
-- Analysis "as-of" date = 2026-09-30 (last day of data).
-- =====================================================================================

-- name: q01_revenue_by_county_store
-- Q1. Which counties and stores drive revenue? Share of chain and rank within county.
-- (JOIN + GROUP BY + window SUM OVER () for share + RANK OVER (PARTITION BY))
SELECT  s.county,
        s.store_name,
        s.store_format,
        ROUND(SUM(t.net_amount))                                            AS revenue_12m,
        ROUND(100.0 * SUM(t.net_amount) / SUM(SUM(t.net_amount)) OVER (), 2) AS pct_of_chain,
        RANK() OVER (PARTITION BY s.county ORDER BY SUM(t.net_amount) DESC)  AS rank_in_county,
        ROUND(SUM(t.net_amount) / s.size_sqm)                               AS revenue_per_sqm
FROM    retail.fact_transaction t
JOIN    retail.dim_store s USING (store_id)
WHERE   t.date_key BETWEEN DATE '2025-10-01' AND DATE '2026-09-30'
GROUP BY s.county, s.store_name, s.store_format, s.size_sqm
ORDER BY revenue_12m DESC;

-- name: q02_monthly_trend
-- Q2. Monthly revenue with month-on-month and year-on-year growth, a 3-month moving
-- average, a running total, and real (inflation-adjusted) revenue.
WITH monthly AS (
    SELECT  d.month_start,
            SUM(t.net_amount)             AS revenue,
            COUNT(*)                      AS receipts,
            AVG(t.net_amount)             AS avg_basket
    FROM    retail.fact_transaction t
    JOIN    retail.dim_date d USING (date_key)
    GROUP BY d.month_start
)
SELECT  m.month_start,
        ROUND(m.revenue)                                                                AS revenue,
        m.receipts,
        ROUND(m.avg_basket, 1)                                                          AS avg_basket,
        ROUND(100 * (m.revenue / LAG(m.revenue) OVER w - 1), 1)                         AS mom_growth_pct,
        ROUND(100 * (m.revenue / LAG(m.revenue, 12) OVER w - 1), 1)                     AS yoy_growth_pct,
        ROUND(AVG(m.revenue) OVER (ORDER BY m.month_start ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)) AS moving_avg_3m,
        ROUND(SUM(m.revenue) OVER (ORDER BY m.month_start))                             AS running_total,
        c.inflation_12m_pct,
        ROUND(m.revenue * 100 / c.cpi_index)                                            AS real_revenue_oct24_kes
FROM    monthly m
JOIN    retail.ref_cpi c ON c.month = m.month_start
WINDOW  w AS (ORDER BY m.month_start)
ORDER BY m.month_start;

-- name: q03_top_products_per_category
-- Q3. Top 3 products in each category by last-12-month revenue (ROW_NUMBER over a partition).
WITH prod AS (
    SELECT  p.category, p.product_name,
            SUM(l.net_amount) AS revenue, SUM(l.quantity) AS units
    FROM    retail.fact_sales_line l
    JOIN    retail.fact_transaction t USING (transaction_id)
    JOIN    retail.dim_product p USING (product_id)
    WHERE   t.date_key >= DATE '2025-10-01'
    GROUP BY p.category, p.product_name
)
SELECT  category, product_name, ROUND(revenue) AS revenue, units, rn AS rank_in_category,
        ROUND(100 * revenue / SUM(revenue) OVER (PARTITION BY category), 1) AS pct_of_category
FROM   (SELECT prod.*, ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) AS rn FROM prod) x
WHERE   rn <= 3
ORDER BY SUM(revenue) OVER (PARTITION BY category) DESC, rn;

-- name: q04_category_mix_by_county
-- Q4. Category share of revenue in each county - do tastes differ by region?
SELECT  county, category, ROUND(revenue) AS revenue,
        ROUND(100 * revenue / SUM(revenue) OVER (PARTITION BY county), 1) AS pct_of_county,
        DENSE_RANK() OVER (PARTITION BY county ORDER BY revenue DESC)     AS rank_in_county
FROM   (SELECT county, category, SUM(net_amount) AS revenue
        FROM retail.v_sales
        WHERE date_key >= DATE '2025-10-01'
        GROUP BY county, category) x
ORDER BY county, rank_in_county;

-- name: q05_payment_mix
-- Q5. Payment-method mix per quarter using conditional aggregation (FILTER).
SELECT  DATE_TRUNC('quarter', date_key)::date                                         AS quarter,
        COUNT(*)                                                                    AS receipts,
        ROUND(100.0 * COUNT(*) FILTER (WHERE payment_method = 'M-Pesa') / COUNT(*), 1)       AS mpesa_pct,
        ROUND(100.0 * COUNT(*) FILTER (WHERE payment_method = 'Cash') / COUNT(*), 1)         AS cash_pct,
        ROUND(100.0 * COUNT(*) FILTER (WHERE payment_method = 'Card') / COUNT(*), 1)         AS card_pct,
        ROUND(100.0 * COUNT(*) FILTER (WHERE payment_method = 'Airtel Money') / COUNT(*), 1) AS airtel_pct,
        ROUND(AVG(net_amount) FILTER (WHERE payment_method = 'M-Pesa'), 0)                   AS mpesa_avg_basket,
        ROUND(AVG(net_amount) FILTER (WHERE payment_method = 'Cash'), 0)                     AS cash_avg_basket,
        ROUND(AVG(net_amount) FILTER (WHERE payment_method = 'Card'), 0)                     AS card_avg_basket
FROM    retail.fact_transaction
GROUP BY 1
ORDER BY 1;

-- name: q06_cohort_retention
-- Q6. Monthly cohort retention: customers grouped by the month of their FIRST purchase;
-- % of each cohort that purchased again N months later.
WITH first_purchase AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(date_key))::date AS cohort_month
    FROM   retail.fact_transaction
    WHERE  customer_id IS NOT NULL
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT t.customer_id, DATE_TRUNC('month', t.date_key)::date AS active_month
    FROM   retail.fact_transaction t
    WHERE  t.customer_id IS NOT NULL
),
cohort_activity AS (
    SELECT f.cohort_month,
           (EXTRACT(YEAR FROM AGE(a.active_month, f.cohort_month)) * 12
            + EXTRACT(MONTH FROM AGE(a.active_month, f.cohort_month)))::int AS months_since,
           a.customer_id
    FROM   first_purchase f
    JOIN   activity a USING (customer_id)
),
sizes AS (SELECT cohort_month, COUNT(*) AS cohort_size FROM first_purchase GROUP BY cohort_month)
SELECT  ca.cohort_month, s.cohort_size, ca.months_since,
        COUNT(DISTINCT ca.customer_id) AS active_customers,
        ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / s.cohort_size, 1) AS retention_pct
FROM    cohort_activity ca
JOIN    sizes s USING (cohort_month)
WHERE   ca.months_since <= 12
GROUP BY ca.cohort_month, s.cohort_size, ca.months_since
ORDER BY ca.cohort_month, ca.months_since;

-- name: q07_rfm_segments
-- Q7. RFM segmentation of loyalty members as at 2026-09-30.
-- Recency = days since last purchase, Frequency = receipts in last 12 months,
-- Monetary = spend in last 12 months. Scores 1-5 with NTILE; segments via CASE.
WITH base AS (
    SELECT  customer_id,
            DATE '2026-09-30' - MAX(date_key)                                AS recency_days,
            COUNT(*) FILTER (WHERE date_key > DATE '2025-09-30')             AS frequency_12m,
            COALESCE(SUM(net_amount) FILTER (WHERE date_key > DATE '2025-09-30'), 0) AS monetary_12m
    FROM    retail.fact_transaction
    WHERE   customer_id IS NOT NULL
    GROUP BY customer_id
),
scored AS (
    SELECT  b.*,
            NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,   -- recent = 5
            NTILE(5) OVER (ORDER BY frequency_12m)     AS f_score,
            NTILE(5) OVER (ORDER BY monetary_12m)      AS m_score
    FROM    base b
)
SELECT  customer_id, recency_days, frequency_12m, ROUND(monetary_12m) AS monetary_12m,
        r_score, f_score, m_score, CONCAT(r_score, f_score, m_score) AS rfm_code,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal'
            WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Promising'
            WHEN r_score = 3  AND f_score <= 2                  THEN 'Needs Attention'
            WHEN r_score = 2                                     THEN 'At Risk'
            ELSE 'Lost / Hibernating'
        END AS rfm_segment
FROM    scored
ORDER BY monetary_12m DESC;

-- name: q08_rfm_segment_summary
-- Q8. Size and value of each RFM segment (re-uses the Q7 logic via a CTE).
WITH base AS (
    SELECT  customer_id,
            DATE '2026-09-30' - MAX(date_key) AS recency_days,
            COUNT(*) FILTER (WHERE date_key > DATE '2025-09-30') AS frequency_12m,
            COALESCE(SUM(net_amount) FILTER (WHERE date_key > DATE '2025-09-30'), 0) AS monetary_12m
    FROM retail.fact_transaction WHERE customer_id IS NOT NULL GROUP BY customer_id
), scored AS (
    SELECT b.*, NTILE(5) OVER (ORDER BY recency_days DESC) r, NTILE(5) OVER (ORDER BY frequency_12m) f,
           NTILE(5) OVER (ORDER BY monetary_12m) m FROM base b
), seg AS (
    SELECT *, CASE WHEN r>=4 AND f>=4 AND m>=4 THEN 'Champions' WHEN r>=3 AND f>=3 THEN 'Loyal'
                   WHEN r>=4 AND f<=2 THEN 'New / Promising' WHEN r=3 AND f<=2 THEN 'Needs Attention'
                   WHEN r=2 THEN 'At Risk' ELSE 'Lost / Hibernating' END AS rfm_segment
    FROM scored
)
SELECT  rfm_segment,
        COUNT(*)                                                    AS customers,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct_customers,
        ROUND(SUM(monetary_12m))                                    AS revenue_12m,
        ROUND(100.0 * SUM(monetary_12m) / SUM(SUM(monetary_12m)) OVER (), 1) AS pct_revenue,
        ROUND(AVG(recency_days))                                    AS avg_recency_days,
        ROUND(AVG(frequency_12m), 1)                                AS avg_frequency
FROM    seg
GROUP BY rfm_segment
ORDER BY revenue_12m DESC;

-- name: q09_promo_cooking_oil_did
-- Q9. Did the March 2026 cooking-oil promotion work? Average daily cooking-oil units per
-- store, before (4 weeks) vs during (3 weeks), in test vs control stores -> difference-in-differences.
WITH promo AS (
    SELECT start_date, end_date, string_to_array(store_ids, '|') AS stores
    FROM   retail.dim_promotion WHERE promo_id = 'PR008'
),
daily AS (
    SELECT  t.store_id, t.date_key, SUM(l.quantity) AS units
    FROM    retail.fact_sales_line l
    JOIN    retail.fact_transaction t USING (transaction_id)
    JOIN    retail.dim_product p USING (product_id)
    WHERE   p.subcategory = 'Cooking Oil'
      AND   t.date_key BETWEEN DATE '2026-02-02' AND DATE '2026-03-22'
    GROUP BY t.store_id, t.date_key
),
labelled AS (
    SELECT  d.*,
            CASE WHEN d.store_id = ANY (pr.stores) THEN 'Test' ELSE 'Control' END            AS grp,
            CASE WHEN d.date_key >= pr.start_date THEN 'During' ELSE 'Before' END              AS period
    FROM    daily d CROSS JOIN promo pr
    WHERE   d.store_id <> 'S020'
),
cell AS (
    SELECT grp, period, ROUND(AVG(units), 2) AS avg_daily_units_per_store, COUNT(DISTINCT store_id) AS stores
    FROM labelled GROUP BY grp, period
)
SELECT  c.*,
        ROUND(100 * (avg_daily_units_per_store
              / FIRST_VALUE(avg_daily_units_per_store) OVER (PARTITION BY grp ORDER BY period) - 1), 1) AS change_vs_before_pct
FROM    cell c
ORDER BY grp DESC, period;

-- name: q10_county_penetration
-- Q10. Revenue per 1,000 residents (joins external census data). Includes counties with
-- no store (LEFT JOIN from the population table) - expansion candidates.
SELECT  p.county, p.population_2019,
        COUNT(DISTINCT s.store_id)                                             AS stores,
        COALESCE(ROUND(SUM(t.net_amount)), 0)                                  AS revenue_12m,
        COALESCE(ROUND(1000 * SUM(t.net_amount) / p.population_2019), 0)       AS revenue_per_1000_residents,
        ROUND(p.population_2019::numeric / NULLIF(COUNT(DISTINCT s.store_id), 0)) AS residents_per_store
FROM    retail.ref_county_population p
LEFT JOIN retail.dim_store s ON s.county = p.county
LEFT JOIN retail.fact_transaction t ON t.store_id = s.store_id AND t.date_key >= DATE '2025-10-01'
GROUP BY p.county, p.population_2019
ORDER BY revenue_per_1000_residents DESC;

-- name: q11_drifting_customers
-- Q11. "Drifting" members: were regular (>= 8 visits in the 6 months to 2026-06-30) but have
-- made <= 1 visit since, or none in 45+ days. A ready-made win-back list for CRM.
WITH hist AS (
    SELECT  customer_id,
            COUNT(*) FILTER (WHERE date_key BETWEEN DATE '2026-01-01' AND DATE '2026-06-30') AS visits_h1,
            COUNT(*) FILTER (WHERE date_key >  DATE '2026-06-30')                           AS visits_q3,
            SUM(net_amount) FILTER (WHERE date_key BETWEEN DATE '2026-01-01' AND DATE '2026-06-30') AS spend_h1,
            MAX(date_key) AS last_visit
    FROM    retail.fact_transaction
    WHERE   customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT  h.customer_id, c.home_store_id, s.county, h.visits_h1, h.visits_q3, ROUND(h.spend_h1) AS spend_h1,
        h.last_visit, DATE '2026-09-30' - h.last_visit AS days_since_last_visit
FROM    hist h
JOIN    retail.dim_customer c USING (customer_id)
JOIN    retail.dim_store s ON s.store_id = c.home_store_id
WHERE   h.visits_h1 >= 8
  AND  (h.visits_q3 <= 1 OR DATE '2026-09-30' - h.last_visit >= 45)
ORDER BY h.spend_h1 DESC;

-- name: q12_drifting_by_county
-- Q12. Where are drifting regulars concentrated? (aggregation over the Q11 logic)
WITH hist AS (
    SELECT  customer_id,
            COUNT(*) FILTER (WHERE date_key BETWEEN DATE '2026-01-01' AND DATE '2026-06-30') AS visits_h1,
            COUNT(*) FILTER (WHERE date_key >  DATE '2026-06-30') AS visits_q3,
            MAX(date_key) AS last_visit
    FROM retail.fact_transaction WHERE customer_id IS NOT NULL GROUP BY customer_id
)
SELECT  s.county,
        COUNT(*) FILTER (WHERE h.visits_h1 >= 8)                                         AS regulars_h1,
        COUNT(*) FILTER (WHERE h.visits_h1 >= 8 AND (h.visits_q3 <= 1 OR DATE '2026-09-30' - h.last_visit >= 45)) AS drifting,
        ROUND(100.0 * COUNT(*) FILTER (WHERE h.visits_h1 >= 8 AND (h.visits_q3 <= 1 OR DATE '2026-09-30' - h.last_visit >= 45))
              / NULLIF(COUNT(*) FILTER (WHERE h.visits_h1 >= 8), 0), 1)                 AS drifting_pct
FROM    hist h
JOIN    retail.dim_customer c USING (customer_id)
JOIN    retail.dim_store s ON s.store_id = c.home_store_id
GROUP BY s.county
HAVING  COUNT(*) FILTER (WHERE h.visits_h1 >= 8) >= 20
ORDER BY drifting_pct DESC;

-- name: q13_basket_affinity
-- Q13. Market-basket affinity: product pairs bought together most often, with support,
-- confidence and lift (self-join on the line table).
WITH lines AS (
    SELECT DISTINCT l.transaction_id, l.product_id
    FROM   retail.fact_sales_line l
    JOIN   retail.fact_transaction t USING (transaction_id)
    WHERE  t.date_key >= DATE '2026-04-01' AND l.quantity > 0
),
n AS (SELECT COUNT(DISTINCT transaction_id)::numeric AS n_tx FROM lines),
single AS (SELECT product_id, COUNT(*) AS n_a FROM lines GROUP BY product_id),
pairs AS (
    SELECT a.product_id AS prod_a, b.product_id AS prod_b, COUNT(*) AS n_ab
    FROM   lines a JOIN lines b ON a.transaction_id = b.transaction_id AND a.product_id < b.product_id
    GROUP BY 1, 2
    HAVING COUNT(*) >= 200
)
SELECT  pa.product_name AS product_a, pb.product_name AS product_b, p.n_ab AS baskets_together,
        ROUND(100 * p.n_ab / n.n_tx, 2)                           AS support_pct,
        ROUND(100.0 * p.n_ab / sa.n_a, 1)                         AS confidence_a_to_b_pct,
        ROUND(p.n_ab * n.n_tx / (sa.n_a::numeric * sb.n_a), 2)    AS lift
FROM    pairs p CROSS JOIN n
JOIN    single sa ON sa.product_id = p.prod_a
JOIN    single sb ON sb.product_id = p.prod_b
JOIN    retail.dim_product pa ON pa.product_id = p.prod_a
JOIN    retail.dim_product pb ON pb.product_id = p.prod_b
ORDER BY lift DESC, baskets_together DESC
LIMIT 15;

-- name: q14_calendar_effects
-- Q14. Average daily chain revenue by calendar condition (holiday, weekend, payday).
WITH daily AS (
    SELECT d.date_key, d.is_weekend, d.is_payday_window, d.is_public_holiday, SUM(t.net_amount) AS revenue
    FROM retail.fact_transaction t JOIN retail.dim_date d USING (date_key)
    GROUP BY d.date_key, d.is_weekend, d.is_payday_window, d.is_public_holiday
)
SELECT 'Public holiday' AS condition, ROUND(AVG(revenue)) AS avg_daily_revenue, COUNT(*) AS days FROM daily WHERE is_public_holiday
UNION ALL SELECT 'Non-holiday', ROUND(AVG(revenue)), COUNT(*) FROM daily WHERE NOT is_public_holiday
UNION ALL SELECT 'Weekend', ROUND(AVG(revenue)), COUNT(*) FROM daily WHERE is_weekend
UNION ALL SELECT 'Weekday', ROUND(AVG(revenue)), COUNT(*) FROM daily WHERE NOT is_weekend
UNION ALL SELECT 'Payday window (25th-3rd)', ROUND(AVG(revenue)), COUNT(*) FROM daily WHERE is_payday_window
UNION ALL SELECT 'Rest of month', ROUND(AVG(revenue)), COUNT(*) FROM daily WHERE NOT is_payday_window;

-- name: q15_store_yoy_growth
-- Q15. Like-for-like store growth: last 12 months vs prior 12 months, real and nominal,
-- for stores open in both periods.
WITH y AS (
    SELECT  t.store_id,
            SUM(t.net_amount) FILTER (WHERE t.date_key <  DATE '2025-10-01') AS rev_y1,
            SUM(t.net_amount) FILTER (WHERE t.date_key >= DATE '2025-10-01') AS rev_y2,
            SUM(t.net_amount * 100 / c.cpi_index) FILTER (WHERE t.date_key <  DATE '2025-10-01') AS real_y1,
            SUM(t.net_amount * 100 / c.cpi_index) FILTER (WHERE t.date_key >= DATE '2025-10-01') AS real_y2
    FROM    retail.fact_transaction t
    JOIN    retail.dim_date d USING (date_key)
    JOIN    retail.ref_cpi c ON c.month = d.month_start
    GROUP BY t.store_id
)
SELECT  s.store_name, s.county, ROUND(rev_y1) AS revenue_y1, ROUND(rev_y2) AS revenue_y2,
        ROUND(100 * (rev_y2 / rev_y1 - 1), 1)   AS nominal_growth_pct,
        ROUND(100 * (real_y2 / real_y1 - 1), 1) AS real_growth_pct,
        RANK() OVER (ORDER BY real_y2 / real_y1 DESC) AS growth_rank
FROM    y JOIN retail.dim_store s USING (store_id)
WHERE   s.open_date < DATE '2024-10-01'
ORDER BY growth_rank;
