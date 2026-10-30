# DAX measures (paste into a `_Measures` table)

```DAX
Revenue = SUM ( fact_transaction[net_amount] )

Receipts = COUNTROWS ( fact_transaction )

Avg Basket = DIVIDE ( [Revenue], [Receipts] )

Units = SUM ( fact_daily_store_category[units] )

Discounts = SUM ( fact_transaction[discount_amount] )

Revenue PY =
CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Revenue YoY % = DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )

Real Revenue = SUM ( fact_daily_store_category[net_amount_real] )

Real Revenue PY =
CALCULATE ( [Real Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Real Revenue YoY % = DIVIDE ( [Real Revenue] - [Real Revenue PY], [Real Revenue PY] )

Revenue MoM % =
VAR prev = CALCULATE ( [Revenue], DATEADD ( dim_date[date], -1, MONTH ) )
RETURN DIVIDE ( [Revenue] - prev, prev )

Revenue 3M Moving Avg =
DIVIDE (
    CALCULATE ( [Revenue], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) ),
    3
)

Revenue per sqm = DIVIDE ( [Revenue], SUM ( dim_store[size_sqm] ) )

Revenue per 1000 Residents =
-- use in a visual grouped by dim_store[county]; every store in a county carries the same population
DIVIDE ( [Revenue], MAX ( dim_store[population_2019] ) ) * 1000

Avg Daily Revenue = AVERAGEX ( VALUES ( dim_date[date] ), [Revenue] )

Receipts per Week = DIVIDE ( [Receipts], DISTINCTCOUNT ( dim_date[date] ) ) * 7

M-Pesa Share % =
DIVIDE ( CALCULATE ( [Receipts], fact_transaction[payment_method] = "M-Pesa" ),
         CALCULATE ( [Receipts], fact_transaction[payment_method] <> "Unknown" ) )

Member Share of Revenue =
DIVIDE ( CALCULATE ( [Revenue], NOT ISBLANK ( fact_transaction[customer_id] ) ), [Revenue] )

Active Members = DISTINCTCOUNT ( fact_transaction[customer_id] )

High-Risk Members =
CALCULATE ( COUNTROWS ( fact_churn_scores ), fact_churn_scores[risk_band] = "High" )

Spend at Risk (12m) = SUM ( fact_churn_scores[value_at_risk_12m] )

Forecast Units = SUM ( fact_forecast_oct2026[forecast_units] )

Forecast Revenue Oct = SUM ( fact_forecast_oct2026[forecast_revenue] )

Sep Units =
CALCULATE ( [Units], DATESBETWEEN ( dim_date[date], DATE ( 2026, 9, 1 ), DATE ( 2026, 9, 30 ) ) )

Promo Share of Receipts =
DIVIDE ( CALCULATE ( [Receipts], fact_transaction[has_promo] = TRUE () ), [Receipts] )
```
