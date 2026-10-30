# %% [markdown]
# # Milestone 4 - SQL Analytics (PostgreSQL)
# The cleaned data is loaded into a PostgreSQL **star schema** (`sql/01_schema.sql`) by `src/load_postgres.py`.
# All analytics queries live in **`sql/03_analytics.sql`** - this notebook simply runs them and interprets the results,
# so a reviewer can also run the file directly in `psql`, DBeaver or pgAdmin.
#
# | Query | Business question | SQL techniques |
# |---|---|---|
# | q01 | Revenue by county/store, share, rank | JOIN, GROUP BY, `SUM() OVER ()`, `RANK() OVER (PARTITION BY)` |
# | q02 | Monthly trend, MoM/YoY, moving average, running total, real revenue | CTE, `LAG`, framed windows, named `WINDOW`, join to CPI |
# | q03 | Top-3 products per category | `ROW_NUMBER()` in a subquery |
# | q04 | Category mix by county | `DENSE_RANK`, partitioned share |
# | q05 | Payment-method mix by quarter | conditional aggregation with `FILTER` |
# | q06 | Cohort retention | multiple CTEs, `DATE_TRUNC`, `AGE` |
# | q07-q08 | RFM segmentation | `NTILE(5)`, `CASE` segment rules |
# | q09 | Cooking-oil promo difference-in-differences | `ANY(array)`, `CROSS JOIN`, `FIRST_VALUE` |
# | q10 | Revenue per 1,000 residents (census join) | `LEFT JOIN` from the reference table |
# | q11-q12 | Drifting regulars (win-back list) | `FILTER`, `HAVING` |
# | q13 | Market-basket affinity (support/confidence/lift) | self-join |
# | q14 | Calendar effects | `UNION ALL` |
# | q15 | Like-for-like real growth by store | windowed rank on ratios |

# %%
import sys; sys.path.append("../src")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import db
from config import ROOT, TABLES, FIGURES, set_style, PALETTE, TEXT_2, kes
set_style()
pd.set_option("display.max_columns", 20)

Q = db.load_named_queries(ROOT / "sql" / "03_analytics.sql")

def run(name, show=10):
    df = db.query(Q[name])
    df.to_csv(TABLES / f"{name}.csv", index=False)
    return df.head(show) if show else df

db.query("""SELECT table_name, (xpath('/row/c/text()', query_to_xml('select count(*) as c from retail.'||table_name, false, true, '')))[1]::text::bigint AS row_count
            FROM information_schema.tables WHERE table_schema = 'retail' AND table_type = 'BASE TABLE' ORDER BY row_count DESC""")

# %% [markdown]
# ## Q1 - Where does revenue come from?

# %%
print(Q["q01_revenue_by_county_store"])

# %%
run("q01_revenue_by_county_store", show=20)

# %% [markdown]
# The four hypermarkets bring ~37% of chain revenue; within Nairobi, Westlands leads. Express stores sit at the bottom by
# revenue but top by revenue per square metre.
#
# ## Q2 - Monthly trend with window functions

# %%
trend = run("q02_monthly_trend", show=None)
trend

# %%
fig, ax = plt.subplots(figsize=(11, 3.8))
x = pd.to_datetime(trend.month_start)
ax.bar(x, trend.yoy_growth_pct, width=20, color=[PALETTE[0]] * len(x), label="Nominal YoY growth %")
real_yoy = 100 * (trend.real_revenue_oct24_kes / trend.real_revenue_oct24_kes.shift(12) - 1)
ax.plot(x, real_yoy, color=PALETTE[1], marker="o", ms=4, label="Real YoY growth %")
ax.axhline(0, color="#999", lw=1)
ax.set_title("Year-on-year growth: real growth is roughly half of nominal growth once inflation is removed")
ax.legend(loc="upper left")
ax.set_xlim(pd.Timestamp("2025-09-10"), pd.Timestamp("2026-09-20"))
fig.savefig(FIGURES / "10_yoy_growth.png")

# %% [markdown]
# ## Q3 - Top products per category

# %%
run("q03_top_products_per_category", show=27)

# %% [markdown]
# ## Q4 - Category mix by county (first two counties shown)

# %%
mix = run("q04_category_mix_by_county", show=None)
mix.pivot(index="category", columns="county", values="pct_of_county").round(1)

# %% [markdown]
# Category mix is remarkably stable across counties (staples ~33% everywhere), so a single national range with local
# tweaks is reasonable.
#
# ## Q5 - Payment mix (conditional aggregation)

# %%
run("q05_payment_mix")

# %% [markdown]
# ## Q6 - Cohort retention

# %%
coh = run("q06_cohort_retention", show=None)
grid = coh.pivot(index="cohort_month", columns="months_since", values="retention_pct")
grid = grid[grid.index >= "2024-11-01"]       # the Oct-24 'cohort' mixes years of existing members
fig, ax = plt.subplots(figsize=(11, 5.5))
im = ax.imshow(grid, aspect="auto", cmap="Blues", vmin=0, vmax=100)
ax.set_yticks(range(len(grid)), [d[:7] for d in grid.index])
ax.set_xticks(range(grid.shape[1]), grid.columns)
ax.set_xlabel("months since first purchase"); ax.grid(False)
for i in range(grid.shape[0]):
    for j in range(grid.shape[1]):
        v = grid.iat[i, j]
        if pd.notna(v) and j > 0:
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                    color="white" if v > 60 else TEXT_2)
fig.colorbar(im, ax=ax, label="% of cohort active")
ax.set_title("Monthly cohort retention (new members): about half are still shopping 6 months after joining")
fig.savefig(FIGURES / "11_cohort_retention.png")

# %%
avg_curve = grid.mean().round(1)
print("Average retention curve (% active by month since first purchase):")
print(avg_curve.to_string())

# %% [markdown]
# ## Q7-Q8 - RFM segmentation

# %%
rfm = run("q07_rfm_segments", show=None)
rfm.head()

# %%
seg = run("q08_rfm_segment_summary", show=None)
seg

# %%
fig, ax = plt.subplots(figsize=(10, 3.8))
s = seg.set_index("rfm_segment")
y = range(len(s))
ax.barh([i + 0.2 for i in y], s.pct_customers, height=0.38, color=PALETTE[0], label="% of members")
ax.barh([i - 0.2 for i in y], s.pct_revenue, height=0.38, color=PALETTE[1], label="% of 12-month revenue")
ax.set_yticks(list(y), s.index); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
ax.set_title("RFM segments: Champions are ~30% of members but ~80% of member revenue")
ax.legend(loc="lower right")
fig.savefig(FIGURES / "12_rfm_segments.png")

# %% [markdown]
# **So what?** Protect Champions (service, availability, recognition); push Loyal members up with personalised offers;
# run a cheap win-back for *At Risk*; don't spend on *Lost*.
#
# ## Q9 - Did the cooking-oil promotion work? (difference-in-differences)

# %%
print(Q["q09_promo_cooking_oil_did"])
run("q09_promo_cooking_oil_did")

# %% [markdown]
# Test stores' cooking-oil sales rose ~37% during the promotion while control stores fell slightly - a difference-in-differences
# of roughly +45 percentage points. Milestone 5 tests whether this is statistically significant.
#
# ## Q10 - Market penetration (census join)

# %%
run("q10_county_penetration", show=12)

# %% [markdown]
# Meru (1.55M residents, no store) and Kakamega/Kilifi (over 1.4M residents per store) are the clearest white-space.
#
# ## Q11-Q12 - Drifting regulars

# %%
drift = run("q11_drifting_customers", show=None)
print(f"{len(drift)} regular customers have drifted; they spent KES {drift.spend_h1.sum():,.0f} in H1 2026")
drift.head(10)

# %%
run("q12_drifting_by_county")

# %% [markdown]
# Nakuru has by far the highest share of drifting regulars - matching the traffic drop seen in the EDA.
#
# ## Q13 - What is bought together?

# %%
run("q13_basket_affinity", show=10)

# %% [markdown]
# Strong, actionable pairs: exercise books and pens (lift ~23), diapers and wipes, tea and sugar, unga and sukuma wiki,
# bread and milk. Use them for shelf adjacency and bundle offers (e.g. "Tea + Sugar" combo).
#
# ## Q14-Q15 - Calendar effects and like-for-like growth

# %%
run("q14_calendar_effects")

# %%
run("q15_store_yoy_growth", show=19)
