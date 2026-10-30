# %% [markdown]
# # Milestone 1 - Problem Framing and Data Acquisition
# **Project:** Customer and Sales Intelligence for *Mavuno Mart*, a (fictional) growing Kenyan retail chain
#
# ## 1. The business problem
# Mavuno Mart runs 20 stores in 11 counties. Management has till data but little insight. They want to know:
#
# | # | Business question | Owner | Decision it informs |
# |---|---|---|---|
# | Q1 | Which **stores, counties and categories** drive revenue and growth? | Ops Director | Where to invest staff, space and stock |
# | Q2 | **When** do customers buy - weekdays, paydays, holidays, festive and school seasons? | Supply chain | Staffing rosters and replenishment timing |
# | Q3 | **Who** buys what - which customer segments matter most, and how do they pay (M-Pesa vs cash vs card)? | Marketing | Loyalty offers, payment partnerships |
# | Q4 | **Did our promotions work?** (especially the March 2026 cooking-oil store test) | Commercial | Whether to repeat or stop a promotion |
# | Q5 | Which **customers are drifting away**, and can we spot them early? | CRM | Who to target with win-back offers |
# | Q6 | What **demand should we expect next month** by store and category? | Supply chain | Purchase orders for October 2026 |
# | Q7 | How much of our sales "growth" is just **inflation**? | Finance | Honest performance reporting |
#
# ## 2. Success measures (agreed before looking at results)
# * **Descriptive (Q1-Q3, Q7):** every headline number is reproducible from SQL and pandas and reconciles within 0.1%.
# * **Promotion test (Q4):** a pre-registered hypothesis test at alpha = 0.05 with a 95% confidence interval for the uplift.
# * **Demand forecast (Q6):** on a 3-month hold-out (Jul-Sep 2026), WAPE at store x category x day is **at least 15% better
#   than a seasonal-naive baseline**, and monthly chain-level category forecasts are within +/-10%.
# * **Churn model (Q5):** ROC-AUC >= 0.75 on a later, out-of-time cohort and the top-risk decile captures **>= 2.5x** the
#   average churn rate (lift), so a win-back budget aimed at it is 2.5x more efficient than random targeting.
#
# ## 3. Data needed and how it was obtained
# | Dataset | Content | Source / how obtained | Licence / terms |
# |---|---|---|---|
# | `stores.csv` | 20 stores: county, town, format, size, open date | Synthetic, `src/generate_data.py` | Own work (MIT, same as repo) |
# | `products.csv` | 91 SKUs, 9 categories, KES price points (Oct 2024) | Synthetic; prices set to typical Nairobi supermarket shelf prices | Own work |
# | `customers.csv` | 6,000 loyalty members: gender, birth year, signup, home store | Synthetic | Own work |
# | `transactions.csv` / `transaction_items.csv` | 328k receipts, 928k lines, Oct 2024 - Sep 2026, payment method incl. M-Pesa | Synthetic | Own work |
# | `promotions.csv` | 9 promotions incl. two randomised store tests | Synthetic | Own work |
# | `kenya_inflation_monthly.csv` | 12-month and annual-average CPI inflation, Jan 2024 - Sep 2026 | KNBS CPI as published by the Central Bank of Kenya, centralbank.go.ke/inflation-rates (copied Oct 2026) | Public government statistics; no licence stated - reuse with attribution to KNBS/CBK |
# | `county_population_2019.csv` | 2019 census population for the 11 store counties plus Meru (expansion candidate) | KNBS 2019 Kenya Population and Housing Census, Vol. I (via Wikipedia "List of counties of Kenya by population") | KNBS public data; Wikipedia text CC BY-SA 4.0 |
# | `kenya_public_holidays.csv` | Gazetted public holidays Oct 2024 - Dec 2026 incl. Sunday-substitution days | Public Holidays Act (Cap. 110) + Gazette/Interior Ministry declarations for Idd-ul-Fitr (31 Mar 2025, 20 Mar 2026) | Public law - no restriction |
#
# **Why synthetic sales data?** Real retailer till data is commercially confidential, and the brief allows a generated dataset.
# The generator is deterministic (seed 2026) and *realistic by design*: real inflation drives prices, real holidays shift demand,
# M-Pesa dominates payments, customers churn, and it contains real-world data-quality problems. It also plants some known
# business events (a competitor opening near Nakuru in Feb 2026; one promotion that works and one that does not) so we can
# check whether the analysis rediscovers them. The planted truth lives in `data/raw/_ground_truth_customers.csv` and is
# **never** used for modelling.

# %%
import sys; sys.path.append("../src")   # lets the notebook import the project modules
import pandas as pd
from config import RAW, EXTERNAL

files = {p.name: p for p in sorted(RAW.glob("*.csv")) if not p.name.startswith("_")}
files.update({p.name: p for p in sorted(EXTERNAL.glob("*.csv"))})
inventory = []
for name, p in files.items():
    df = pd.read_csv(p, low_memory=False)
    inventory.append({"file": name, "rows": len(df), "columns": df.shape[1],
                      "missing_cells_%": round(100 * df.isna().mean().mean(), 2),
                      "size_MB": round(p.stat().st_size / 1e6, 2)})
pd.DataFrame(inventory)

# %% [markdown]
# ## 4. First look at the raw tables
# The raw files are exactly what a POS export looks like - including the problems. A quick peek:

# %%
tx = pd.read_csv(RAW / "transactions.csv", dtype={"customer_id": str})
tx.head(8)

# %%
print("Payment method labels as typed at the till:")
print(tx.payment_method.value_counts(dropna=False).to_string())

# %%
items = pd.read_csv(RAW / "transaction_items.csv", dtype={"promo_id": str})
items.describe().round(2)

# %% [markdown]
# Already visible: payment methods typed 15+ ways, `KES 1,234.00` strings in `total_amount`, missing prices, a quantity of
# 1000 for a single SKU, and duplicate rows. These are handled in Milestone 2.
#
# ## 5. Data model
# A classic retail **star schema**: one fact table at receipt-line grain, with dimensions for store, product, customer,
# date and promotion; context data join on `county` (population) and `month` (inflation) or `date` (holidays).
#
# ```
#             dim_customer          dim_product
#                   \                  /
#  dim_store --- fact_sales_line (transaction_id, line_no) --- dim_date --- holidays / CPI
#                   /
#            dim_promotion          county population -> dim_store.county
# ```

# %%
pd.read_csv(RAW / "stores.csv")

# %%
pd.read_csv(RAW / "promotions.csv")
