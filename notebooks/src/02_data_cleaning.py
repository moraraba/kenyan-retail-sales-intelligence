# %% [markdown]
# # Milestone 2 - Data Cleaning and Preparation
# All cleaning logic lives in `src/clean.py` so it is tested once and reused by every notebook, the SQL load and the
# dashboard. This notebook walks through **each problem, the evidence for it, the decision taken and why**.
#
# Principles:
# 1. **Never silently change data** - every step is logged (rows before/after) in `data/processed/cleaning_log.csv`.
# 2. **Fix when the correct value is recoverable** (labels, date formats, prices from the price list); **drop when it is not**
#    (keying-error quantities, test receipts) - and only if the dropped volume is immaterial.
# 3. **Keep legitimate oddities**: returns (negative quantities) and walk-in shoppers (no customer id) are real business events.

# %%
import sys; sys.path.append("../src")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import clean
from config import RAW, PROCESSED, set_style, PALETTE
set_style()

raw_tx = pd.read_csv(RAW / "transactions.csv", dtype={"customer_id": str})
raw_items = pd.read_csv(RAW / "transaction_items.csv", dtype={"promo_id": str})
raw_cust = pd.read_csv(RAW / "customers.csv")
raw_stores = pd.read_csv(RAW / "stores.csv")
raw_prod = pd.read_csv(RAW / "products.csv")
print(raw_tx.dtypes, "\n")
print(raw_items.dtypes)

# %% [markdown]
# ## 1. Types
# `transaction_datetime` and `total_amount` load as text (`object`). The amount column mixes numbers with `"KES 1,234.00"`
# strings, and dates come in two formats.

# %%
print("Non-numeric total_amount examples:",
      raw_tx.total_amount[pd.to_numeric(raw_tx.total_amount, errors="coerce").isna() & raw_tx.total_amount.notna()].head(3).tolist())
print("Non-ISO datetime examples:",
      raw_tx.transaction_datetime[~raw_tx.transaction_datetime.str.match(r"\d{4}-")].head(3).tolist())

# %% [markdown]
# **Decision:** parse `dd/mm/YYYY HH:MM` explicitly (day-first - Kenyan convention) rather than letting pandas guess,
# which would read 03/04 as 4 March. Strip `KES` and thousands separators from amounts.
#
# ## 2. Missing values

# %%
miss = pd.concat({
    "transactions": raw_tx.isna().mean(), "items": raw_items.isna().mean(),
    "customers": raw_cust.isna().mean()}).mul(100).round(2)
miss[miss > 0].to_frame("% missing")

# %% [markdown]
# | Column | Why it is missing | Treatment |
# |---|---|---|
# | `customer_id` (~50%) | Walk-in shoppers without a loyalty card - **not an error** | Keep; flag `is_member` |
# | `payment_method` (~0.8%) | Till did not capture it | Label `Unknown` (dropping would lose real sales) |
# | `total_amount` (~0.4%) | Export glitch | Recompute from lines - the reliable source |
# | `unit_price` (~0.6%) | Export glitch | Median price of same product, same store, same month (prices are set monthly) |
# | `promo_id` (most rows) | Line not on promotion - **structural** | Keep as null; flag `on_promo` |
# | `gender`, `birth_year` | Not captured at sign-up | `Unknown` category; impossible years set to missing |
#
# ## 3. Duplicates

# %%
print("exact duplicate receipts :", raw_tx.duplicated().sum())
print("exact duplicate lines    :", raw_items.duplicated().sum())
print("duplicate customer rows  :", raw_cust.duplicated().sum())
print("test receipts (S999)     :", (raw_tx.store_id == "S999").sum())

# %% [markdown]
# ## 4. Outliers
# Two very different kinds of "outlier":
# * **Errors** - a quantity of 999 cooking-oil bottles in one household basket is a keying error (wrong field on the till).
# * **Genuine extremes** - a KES 15,000 festive basket is unusual but real, and must be kept.

# %%
q = raw_items.quantity
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ax[0].hist(q[(q > 0) & (q <= 30)], bins=range(1, 31), color=PALETTE[0], rwidth=0.85)
ax[0].set(title="Quantity per line (1-30)", xlabel="units", ylabel="lines")
ax[1].scatter(np.arange((q > 30).sum()), q[q > 30], color=PALETTE[1], s=18)
ax[1].set(title=f"Lines with quantity > 30 (n={(q > 30).sum()})", ylabel="units", xticks=[])
print(q[q > 0].quantile([.5, .9, .99, .999]))

# %% [markdown]
# **Decision:** the 99th percentile is 5 units and the 99.9th is under 10, while the suspicious values cluster at 99, 120, 999
# and 1000 - classic keying errors. Rule: drop lines with |quantity| > 30 (60 lines, 0.006% of lines). We *drop* rather than
# cap because the true quantity is unknowable; capping would invent data.
#
# ## 5. Inconsistent categories

# %%
print(raw_stores.county.tolist())
print("\nproducts with missing category:\n", raw_prod[raw_prod.category.isna()][["product_id", "product_name", "subcategory"]])

# %% [markdown]
# ## 6. Run the full, logged pipeline

# %%
sales = clean.main()

# %%
log = pd.read_csv(PROCESSED / "cleaning_log.csv")
log

# %% [markdown]
# ## 7. Validation after cleaning
# Checks that must all pass before any analysis:

# %%
tx = pd.read_pickle(PROCESSED / "transactions.pkl")
checks = {
    "no duplicate transaction_id": tx.transaction_id.is_unique,
    "all dates inside Oct-2024..Sep-2026": tx.transaction_datetime.between("2024-10-01", "2026-10-01").all(),
    "all stores known": tx.store_id.isin(pd.read_csv(PROCESSED / "stores.csv").store_id).all(),
    "payment methods in 5 clean labels": set(tx.payment_method) <= {"M-Pesa", "Cash", "Card", "Airtel Money", "Unknown"},
    "no missing unit price": sales.unit_price.notna().all(),
    "every line has a category": sales.category.notna().all(),
    "till totals reconcile with lines (>99.9%)": (~tx.total_mismatch).mean() > 0.999,
    "revenue from lines == revenue from receipts": np.isclose(sales.net_amount.sum(), tx.net_amount.sum()),
}
pd.Series(checks, name="passed").to_frame()

# %% [markdown]
# ## 8. Features engineered
# | Feature | Definition | Used for |
# |---|---|---|
# | `gross_amount`, `net_amount` | qty x price; less promo discount | revenue |
# | `is_return` | quantity < 0 | returns analysis, net sales |
# | `is_weekend`, `day_of_week`, `hour` | from timestamp | seasonality, staffing |
# | `is_payday_window` | day >= 25 or <= 3 (salaries paid month-end in Kenya) | payday effect |
# | `is_public_holiday` | joined from the gazetted holiday file | demand forecasting |
# | `inflation_12m_pct`, `cpi_index` | joined by month from KNBS/CBK | context |
# | `net_amount_real` | revenue deflated to Oct-2024 shillings using the CPI index | real growth (Q7) |
# | `age`, `age_band`, `tenure` | from customer master | segmentation, churn |
# | `n_lines`, `units`, `has_promo` | per receipt | basket analysis |

# %%
sales.head()

# %%
print(f"Clean fact table: {len(sales):,} lines | {sales.transaction_id.nunique():,} receipts | "
      f"net revenue KES {sales.net_amount.sum()/1e6:,.1f}M | returns {sales.is_return.mean():.2%} of lines")
