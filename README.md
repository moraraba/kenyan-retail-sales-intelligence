# Customer and Sales Intelligence for a Kenyan Retailer
**Data Science and Analytics Capstone** 

*Mavuno Mart* is a (fictional) growing Kenyan retail chain with 20 stores in 11 counties. This project takes management's
business questions - who buys what, where and when; which products and stores drive revenue; which customers are drifting
away; and what demand to expect next month - and answers them with cleaned data, SQL, statistical tests, two predictive
models and a manager dashboard. Everything is reproducible from one command.

---

## Headline findings

| Question | Answer | Evidence |
|---|---|---|
| Are we growing? | Revenue **+9.6%** year on year (KES 154.8M in the last 12 months) but only **+4.8% in real terms** after KNBS inflation | `03_eda`, SQL q02/q15 |
| When do people buy? | Month-end payday window (25th-3rd) brings **~30% more daily revenue**; December ~40% above an average month, January ~15% below; Saturday late morning and weekday 5-7 pm peaks | `03_eda`, SQL q14, H4 |
| Where is revenue made? | Hypermarkets earn the most, but **Express stores earn the most per sq m** (KES 5,086 vs 3,753). Meru (1.5M people) has no store | `03_eda`, SQL q01/q10 |
| Who are our customers? | **30% of members (Champions) bring 79% of member revenue**; M-Pesa pays for ~60% of receipts and rising; card baskets ~26% larger | SQL q05/q07/q08, H5 |
| What sells together? | Exercise books+pens (lift 23), diapers+wipes (16), tea+sugar, unga+sukuma wiki, bread+milk | SQL q13 |
| Did promotions work? | Randomised cooking-oil test: **+66 pp units (95% CI 32-100, p < 0.001)** but it **lost gross profit** at 15% off. Personal-care 5% off: **no detectable effect** | `05_statistical_analysis` H1-H3, SQL q09 |
| Who is drifting away? | **Nakuru** traffic fell ~20% from Feb 2026 and its members lapse at **32% vs 16%** elsewhere (p < 0.001). Churn model: out-of-time **ROC-AUC 0.91, top-decile lift 3.7x** | `03_eda`, H7, `07_churn_model` |
| What about October? | **~56,200 units / KES 13.6M**, +2% on Oct 2025. Model WAPE 33% vs 46% for seasonal naive (28% better); monthly category totals within ~3% | `06_demand_forecast` |

**Recommended actions:** defend Nakuru now; run a model-targeted win-back (KES 150 offer to ~1,270 members, with a
holdout); stop 15% staple discounts and re-test at 7-10% with basket gross profit as the metric; order October stock from
the forecast; expand with Express stores in under-served counties.

---

## Milestones -> where to find them

| # | Milestone | Deliverable |
|---|---|---|
| 1 | Problem framing & data acquisition | `notebooks/01_problem_framing_and_data.ipynb`, `docs/data_sources.md`, `src/generate_data.py` |
| 2 | Data cleaning & preparation (pandas) | `notebooks/02_data_cleaning.ipynb`, `src/clean.py`, `data/processed/cleaning_log.csv` |
| 3 | Exploratory data analysis | `notebooks/03_eda.ipynb`, `reports/figures/` |
| 4 | SQL analytics (PostgreSQL) | `sql/01_schema.sql`, `sql/01b_dim_date.sql`, `sql/02_post_load.sql`, **`sql/03_analytics.sql`** (15 queries), `notebooks/04_sql_analytics.ipynb`, results in `reports/tables/q*.csv` |
| 5 | Statistical analysis | `notebooks/05_statistical_analysis.ipynb`, `reports/tables/statistical_tests_summary.csv` |
| 6 | Predictive models | `notebooks/06_demand_forecast.ipynb` (forecast), `notebooks/07_churn_model.ipynb` (churn) |
| 7 | Dashboard & storytelling | `dashboard/Mavuno_Mart_Sales_Dashboard.xlsx`, `dashboard/POWERBI_GUIDE.md`, `dashboard/powerbi/` |
| 8 | Documentation & presentation | this README, `docs/`, `docs/presentation/Mavuno_Mart_Capstone_Presentation.pptx` |

## Repository layout
```
kenya-retail-capstone/
|-- run_all.py                    # one command reproduces everything
|-- requirements.txt
|-- data/
|   |-- raw/                      # generated "POS export" - deliberately messy
|   |-- external/                 # real public data: KNBS inflation, 2019 census, public holidays
|   `-- processed/                # cleaned tables, model outputs (large .pkl files rebuilt by run_all)
|-- src/
|   |-- config.py                 # paths, seed, chart style
|   |-- generate_data.py          # M1 synthetic data generator
|   |-- clean.py                  # M2 cleaning + feature engineering (logged)
|   |-- db.py, load_postgres.py   # M4 PostgreSQL helper and loader
|   `-- build_dashboard.py        # M7 Excel dashboard + Power BI extracts
|-- sql/                          # schema, calendar, indexes/view, 15 analytics queries
|-- notebooks/
|   |-- src/*.py                  # notebook sources (percent format, diff-friendly)
|   `-- 01..07_*.ipynb            # executed notebooks with outputs
|-- reports/figures, reports/tables
|-- dashboard/                    # Excel dashboard, Power BI guide, star schema CSVs, DAX, theme
|-- docs/                         # data sources & licences, data dictionary, defence notes, presentation
`-- tools/                        # notebook executor, deck builder
```

## How to reproduce
```bash
# 1. Python 3.11+ and PostgreSQL 14+ (psql on PATH)
pip install -r requirements.txt

# 2. Point at your PostgreSQL (defaults: user postgres, database mavuno, local socket/localhost)
export PGUSER=postgres PGHOST=localhost        # Windows: set PGUSER=postgres
createdb mavuno                                # created automatically if missing

# 3. Run everything (~3 minutes): data -> cleaning -> PostgreSQL -> notebooks -> dashboard
python run_all.py
#    no PostgreSQL? ->  python run_all.py --skip-sql

# 4. Rebuild the deck (optional, needs Node.js + pptxgenjs)
python tools/deck_data.py && node tools/build_deck.js
```
The generator uses a fixed seed (2026), so every number in the notebooks, dashboard and deck is reproduced exactly.
Notebooks can also be opened and re-run cell by cell in Jupyter or VS Code (run them in order 01 -> 07).

## Data
Synthetic sales data (confidential in real life; allowed by the brief) joined to **real public context data**:
KNBS CPI inflation (via Central Bank of Kenya), KNBS 2019 census county populations, and gazetted Kenyan public holidays.
Full sources, acquisition dates, licences and the realism design are in **`docs/data_sources.md`**; column definitions in
**`docs/data_dictionary.md`**.

## Methods at a glance
* **Cleaning:** explicit day-first date parsing, label standardisation, robust outlier rule (|qty| > 30, >6x the 99.9th
  percentile), product-store-month median price imputation, reconciliation of till totals to lines.
* **SQL:** star schema with PK/FK constraints and indexes; joins, CTEs, `FILTER`, window functions (`LAG`, `RANK`,
  `ROW_NUMBER`, `NTILE`, moving averages, running totals), cohort retention and RFM.
* **Statistics:** store-level difference-in-differences with Welch t-test, permutation test and bootstrap CI;
  Mann-Whitney, Kruskal-Wallis + Tukey HSD, chi-square with Cramer's V, two-proportion z-test, power analysis; effect
  sizes and profit translation for every test.
* **Forecast:** gradient boosting (Poisson loss) on store x category x day with leakage-proof 35-day lags, rolling-origin
  backtest vs two baselines, empirical 80% intervals.
* **Churn:** behavioural 90-day churn label, snapshot features, grouped CV + out-of-time test, recency-rule baseline vs
  logistic regression vs gradient boosting, calibration, lift, permutation importance, campaign ROI.

## Limitations
Absolute shilling totals are illustrative (synthetic, sampled tills); store tests have ~10 stores per arm; churn cannot
see members who shop without their card; census data is from 2019. See the model cards at the end of notebooks 06 and 07.

## Licence
Code and synthetic data: MIT. External data remains under its publishers' terms (see `docs/data_sources.md`).
