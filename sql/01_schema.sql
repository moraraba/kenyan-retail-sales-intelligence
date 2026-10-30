-- =====================================================================================
-- Milestone 4 - PostgreSQL star schema for Mavuno Mart
-- Grain of the main fact: one row per receipt line (transaction_id, line_no).
-- Run via:  python src/load_postgres.py   (creates schema, loads data, builds dim_date)
-- =====================================================================================
DROP SCHEMA IF EXISTS retail CASCADE;
CREATE SCHEMA retail;
SET search_path TO retail;

-- ---------------------------------------------------------------- reference / context
CREATE TABLE ref_county_population (
    county           TEXT PRIMARY KEY,
    population_2019  INTEGER NOT NULL CHECK (population_2019 > 0)
);

CREATE TABLE ref_cpi (
    month              DATE PRIMARY KEY,          -- first day of month
    inflation_12m_pct  NUMERIC(5,2) NOT NULL,
    cpi_index          NUMERIC(8,3) NOT NULL       -- Oct-2024 = 100 (derived)
);

CREATE TABLE ref_holiday (
    holiday_date  DATE PRIMARY KEY,
    holiday_name  TEXT NOT NULL,
    holiday_type  TEXT NOT NULL
);

-- ---------------------------------------------------------------- dimensions
CREATE TABLE dim_store (
    store_id      TEXT PRIMARY KEY,
    store_name    TEXT NOT NULL,
    county        TEXT NOT NULL,
    town          TEXT NOT NULL,
    store_format  TEXT NOT NULL CHECK (store_format IN ('Hypermarket','Supermarket','Express')),
    size_sqm      INTEGER NOT NULL,
    open_date     DATE NOT NULL
);

CREATE TABLE dim_product (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    subcategory   TEXT NOT NULL,
    base_price    NUMERIC(10,2) NOT NULL,
    brand_tier    TEXT NOT NULL
);

CREATE TABLE dim_customer (
    customer_id    TEXT PRIMARY KEY,
    gender         TEXT NOT NULL,
    birth_year     INTEGER,
    age_band       TEXT NOT NULL,
    signup_date    DATE NOT NULL,
    home_store_id  TEXT NOT NULL REFERENCES dim_store(store_id)
);

CREATE TABLE dim_promotion (
    promo_id      TEXT PRIMARY KEY,
    promo_name    TEXT NOT NULL,
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    discount_pct  NUMERIC(5,2) NOT NULL,
    scope_type    TEXT NOT NULL,
    scope_value   TEXT NOT NULL,
    store_ids     TEXT NOT NULL,           -- 'ALL' or pipe-separated list
    CHECK (end_date >= start_date)
);

CREATE TABLE dim_date (
    date_key          DATE PRIMARY KEY,
    year              SMALLINT NOT NULL,
    month             SMALLINT NOT NULL,
    month_start       DATE NOT NULL,
    day_of_month      SMALLINT NOT NULL,
    iso_dow           SMALLINT NOT NULL,   -- 1 = Monday
    day_name          TEXT NOT NULL,
    is_weekend        BOOLEAN NOT NULL,
    is_payday_window  BOOLEAN NOT NULL,    -- 25th to 3rd
    is_public_holiday BOOLEAN NOT NULL,
    holiday_name      TEXT
);

-- ---------------------------------------------------------------- facts
CREATE TABLE fact_transaction (
    transaction_id    TEXT PRIMARY KEY,
    transaction_ts    TIMESTAMP NOT NULL,
    date_key          DATE NOT NULL REFERENCES dim_date(date_key),
    store_id          TEXT NOT NULL REFERENCES dim_store(store_id),
    till_no           SMALLINT,
    customer_id       TEXT REFERENCES dim_customer(customer_id),   -- NULL = walk-in
    payment_method    TEXT NOT NULL,
    n_lines           SMALLINT,
    units             INTEGER,
    gross_amount      NUMERIC(12,2),
    discount_amount   NUMERIC(12,2),
    net_amount        NUMERIC(12,2)
);

CREATE TABLE fact_sales_line (
    transaction_id   TEXT NOT NULL REFERENCES fact_transaction(transaction_id),
    line_no          SMALLINT NOT NULL,
    product_id       TEXT NOT NULL REFERENCES dim_product(product_id),
    quantity         INTEGER NOT NULL,
    unit_price       NUMERIC(10,2) NOT NULL,
    discount_amount  NUMERIC(10,2) NOT NULL DEFAULT 0,
    promo_id         TEXT REFERENCES dim_promotion(promo_id),
    net_amount       NUMERIC(12,2) NOT NULL,
    PRIMARY KEY (transaction_id, line_no)
);
