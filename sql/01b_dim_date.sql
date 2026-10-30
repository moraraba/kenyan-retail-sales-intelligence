-- Calendar dimension generated in SQL (generate_series) and enriched with gazetted holidays.
SET search_path TO retail;

INSERT INTO dim_date
SELECT  d::date                                   AS date_key,
        EXTRACT(YEAR  FROM d)::smallint           AS year,
        EXTRACT(MONTH FROM d)::smallint           AS month,
        DATE_TRUNC('month', d)::date              AS month_start,
        EXTRACT(DAY   FROM d)::smallint           AS day_of_month,
        EXTRACT(ISODOW FROM d)::smallint          AS iso_dow,
        TO_CHAR(d, 'FMDay')                       AS day_name,
        EXTRACT(ISODOW FROM d) IN (6, 7)          AS is_weekend,
        EXTRACT(DAY FROM d) >= 25 OR EXTRACT(DAY FROM d) <= 3 AS is_payday_window,
        h.holiday_date IS NOT NULL                AS is_public_holiday,
        h.holiday_name
FROM    generate_series(DATE '2024-10-01', DATE '2026-12-31', INTERVAL '1 day') AS d
LEFT JOIN ref_holiday h ON h.holiday_date = d::date AND h.holiday_type <> 'reference';
