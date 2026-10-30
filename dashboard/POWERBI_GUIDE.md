# Power BI build guide - Mavuno Mart Manager Dashboard

The repository ships two dashboard options:

| Option | File | Needs |
|---|---|---|
| **Excel dashboard (ready now)** | `dashboard/Mavuno_Mart_Sales_Dashboard.xlsx` | Excel, LibreOffice or Google Sheets |
| **Power BI report (build in ~45 min)** | this guide + `dashboard/powerbi/*.csv` | Power BI Desktop (free, Windows) |

A `.pbix` file is binary and can only be produced inside Power BI Desktop, so the repo provides everything needed to
build it reproducibly: a star schema, the DAX measures (`powerbi/DAX_measures.md`), a colour theme
(`powerbi/mavuno_theme.json`) and the page designs below. Save your finished file as `dashboard/Mavuno_Mart.pbix`.

---

## 1. Load the data (Get Data -> Text/CSV)
Load every CSV in `dashboard/powerbi/`. In Power Query set types:

| Table | Key column(s) | Notes |
|---|---|---|
| `dim_date` | `date` | Mark as date table (Table tools -> Mark as date table) |
| `dim_store` | `store_id` | includes county population |
| `dim_product` | `product_id` | category, subcategory |
| `dim_customer` | `customer_id` | |
| `fact_transaction` | `transaction_id` | one row per receipt; `date`, `store_id`, `customer_id` (blank = walk-in) |
| `fact_daily_store_category` | (`date`,`store_id`,`category`) | units and revenue per store-category-day |
| `fact_forecast_oct2026` | (`store_id`,`category`) | October forecast + 80% range |
| `fact_churn_scores` | `customer_id` | churn probability, risk band, value at risk |
| `ref_cpi` | `month` (text `YYYY-MM`) | inflation |

Optional alternative: connect Power BI straight to PostgreSQL (Get Data -> PostgreSQL database, server `localhost`,
database `mavuno`) and use the `retail` schema tables and the `retail.v_sales` view.

## 2. Model view - relationships (single direction, many-to-one)
```
dim_date[date]          1 --- *  fact_transaction[date]
dim_date[date]          1 --- *  fact_daily_store_category[date]
dim_store[store_id]     1 --- *  fact_transaction[store_id]
dim_store[store_id]     1 --- *  fact_daily_store_category[store_id]
dim_store[store_id]     1 --- *  fact_forecast_oct2026[store_id]
dim_customer[customer_id] 1 --- * fact_transaction[customer_id]
dim_customer[customer_id] 1 --- 1 fact_churn_scores[customer_id]
dim_date[year_month]    * --- 1  ref_cpi[month]   (or add a month column and relate)
```
Create a small `dim_category` table (`DISTINCT(dim_product[category])`) and relate it to
`fact_daily_store_category[category]` and `fact_forecast_oct2026[category]` so one slicer filters both.

## 3. Measures
Paste the measures from `powerbi/DAX_measures.md` into a dedicated `_Measures` table.

## 4. Theme
View -> Themes -> Browse for themes -> `powerbi/mavuno_theme.json` (colour-blind-checked categorical palette).

## 5. Pages (16:9, slicers in one row at the top of every page: Date range, County, Store format, Category)

### Page 1 - Executive overview ("How are we doing?")
* KPI cards: `Revenue`, `Revenue YoY %`, `Real Revenue YoY %`, `Receipts`, `Avg Basket`, `M-Pesa Share %`.
* Line chart: `Revenue` and `Real Revenue` by `dim_date[year_month]`.
* Bar chart: `Revenue` by `dim_store[store_name]`, coloured by `store_format`; tooltip `Revenue per sqm`.
* Smart narrative or text box with the 3 headline insights (see section 6).

### Page 2 - Where & what ("Which stores and categories drive revenue?")
* Filled map or bar: `Revenue per 1,000 residents` by county.
* Matrix: rows `category`, columns `fiscal_year`, values `Revenue`, `Revenue YoY %` with conditional formatting (diverging, grey midpoint).
* Scatter: x = `size_sqm`, y = `Revenue`, details = store, legend = format (shows Express productivity).

### Page 3 - When & how ("When do customers buy and how do they pay?")
* Matrix heatmap: rows `day_name`, columns `fact_transaction[hour]`, values `Receipts per Week` (sequential blue).
* Column chart: `Avg Daily Revenue` by `is_payday_window`.
* 100% stacked column: `Receipts` by `year_month`, legend `payment_method`.

### Page 4 - Customers & churn ("Who is drifting away?")
* Cards: `Active Members`, `High-Risk Members`, `Spend at Risk (12m)`.
* Donut or bar: members by `risk_band`.
* Bar: `High-Risk Members` by county (Nakuru stands out).
* Table (the CRM action list): customer, home store, churn probability, days since last visit, spend at risk -
  sorted by spend at risk, Top N = 100 filter.

### Page 5 - Next month ("What should we order for October?")
* Clustered column: `Forecast Units` vs `Sep Units` by category.
* Table: store x category forecast with `low_80` / `high_80`.
* Card: `Forecast Revenue Oct`.

### Page 6 - Promotions
* Table from `reports/tables/statistical_tests_summary.csv` (import it) with conclusion column.
* Line chart: daily cooking-oil units, test vs control stores, Feb-Mar 2026 (filter category = Staples,
  subcategory via `fact_sales_line` if you load it from PostgreSQL).

## 6. Storytelling - the insight text for managers
1. **Growth is half inflation.** Nominal revenue +9.6%, real +4.8%.
2. **Plan for the calendar.** December ~+40%, January ~-15%; payday days ~30% busier; Saturdays peak.
3. **Small formats win per square metre** - open Express stores; Meru (1.5M people) has no store.
4. **Nakuru is under attack** - traffic down ~20% since Feb 2026; members lapse at twice the chain rate.
5. **Promotions:** cooking-oil test worked on volume but lost margin at 15% off; personal care 5% off did nothing.
6. **Retention:** Champions (30% of members) = 80% of member revenue; target the churn model's high-risk list.

## 7. Publish
File -> Publish -> your workspace. Schedule refresh after the nightly `python run_all.py` (or point at PostgreSQL).
