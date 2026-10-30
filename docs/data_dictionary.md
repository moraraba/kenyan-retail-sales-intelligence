# Data dictionary (cleaned data, `data/processed/` and PostgreSQL schema `retail`)

## fact_transaction (one row per receipt) - `transactions.pkl/csv`, `retail.fact_transaction`
| Column | Type | Description |
|---|---|---|
| transaction_id | text (PK) | Receipt number `T0000001` |
| transaction_datetime / transaction_ts | timestamp | Till timestamp (local time) |
| store_id | text (FK dim_store) | Store |
| till_no | int | Till number 1-8 |
| customer_id | text (FK dim_customer), nullable | Loyalty member; **NULL = walk-in shopper** |
| is_member | bool | customer_id present |
| payment_method | text | M-Pesa, Cash, Card, Airtel Money, Unknown |
| n_lines | int | Distinct products on the receipt |
| units | int | Net units (returns negative) |
| gross_amount | KES | Sum of qty x unit price |
| discount_amount | KES | Promotional discounts |
| net_amount | KES | gross - discount = **revenue** |
| total_amount_reported | KES | Till total as exported (for reconciliation only) |
| total_mismatch | bool | Reported total differs from lines by > KES 1 |
| has_promo | bool | At least one promoted line |

## fact_sales_line (one row per receipt line) - `transaction_items.pkl`, `retail.fact_sales_line`
| Column | Type | Description |
|---|---|---|
| transaction_id, line_no | PK | Lines 90+ are returns |
| product_id | FK dim_product | |
| quantity | int | Negative = return/refund |
| unit_price | KES | Shelf price that month in that store |
| discount_amount | KES | Discount on the line |
| promo_id | FK dim_promotion, nullable | Promotion applied |
| net_amount | KES | qty x price - discount |

`sales_lines.pkl` = the line table joined to receipt, product, store, calendar and CPI, adding: `date`, `month`,
`year`, `month_num`, `day_of_week`, `hour`, `is_weekend`, `is_payday_window` (day >= 25 or <= 3),
`is_public_holiday`, `on_promo`, `inflation_12m_pct`, `cpi_index` (Oct 2024 = 100), `net_amount_real` (Oct-2024 KES).

## dim_store
store_id, store_name, county, town, store_format (Hypermarket / Supermarket / Express), size_sqm, open_date.

## dim_product
product_id, product_name, category (10), subcategory, base_price (KES, Oct 2024), brand_tier (Private Label / Standard / Premium).

## dim_customer
customer_id, gender (F/M/Unknown), birth_year (nullable), age, age_band, signup_date, home_store_id.

## dim_promotion
promo_id, promo_name, start_date, end_date, discount_pct, scope_type (category/subcategory), scope_value, store_ids ('ALL' or pipe list), duration_days.

## dim_date (SQL-generated)
date_key, year, month, month_start, day_of_month, iso_dow, day_name, is_weekend, is_payday_window, is_public_holiday, holiday_name.

## Reference
* `ref_cpi`: month, inflation_12m_pct, cpi_index
* `ref_county_population`: county, population_2019
* `ref_holiday`: holiday_date, holiday_name, holiday_type

## Model outputs
* `forecast_oct2026_store_category.csv`: store_id, category, forecast_units, low_80, high_80, avg_price, forecast_revenue, store_name, county
* `forecast_oct2026_daily.csv`: store_id, category, date, forecast_units
* `churn_scores_2026-09-30.csv`: customer_id, home_store_id, county, churn_probability, risk_band (Low < 0.2 <= Medium < 0.5 <= High), recency_days, freq_90, spend_90, spend_365, value_at_risk_12m, trend_45
