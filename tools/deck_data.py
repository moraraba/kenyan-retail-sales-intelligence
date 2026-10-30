"""Collect the numbers the presentation needs into docs/presentation/deck_data.json (run before build_deck.js)."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import PROCESSED, TABLES  # noqa: E402

out_dir = ROOT / "docs" / "presentation"
out_dir.mkdir(parents=True, exist_ok=True)

tx = pd.read_pickle(PROCESSED / "transactions.pkl")
sales = pd.read_pickle(PROCESSED / "sales_lines.pkl")
stores = pd.read_csv(PROCESSED / "stores.csv")
tx["date"] = tx.transaction_datetime.dt.normalize()
y2 = tx.date >= "2025-10-01"
s_y2 = sales.date >= "2025-10-01"

monthly = sales.groupby("month").agg(nominal=("net_amount", "sum"), real=("net_amount_real", "sum"))
rev_y1, rev_y2 = tx.net_amount[~y2].sum(), tx.net_amount[y2].sum()
real_y1, real_y2 = sales.net_amount_real[~s_y2].sum(), sales.net_amount_real[s_y2].sum()

st = tx[y2].groupby("store_id").net_amount.sum().rename("rev").to_frame().join(stores.set_index("store_id"))
fmt = (st.groupby("store_format").rev.sum() / st.groupby("store_format").size_sqm.sum()).round(0)

daily = tx.groupby("date").net_amount.sum()
pay = daily.groupby((daily.index.day >= 25) | (daily.index.day <= 3)).mean()
mon = tx.groupby(tx.transaction_datetime.dt.month).net_amount.sum() / tx.groupby(tx.transaction_datetime.dt.month).date.nunique()

log = pd.read_csv(PROCESSED / "cleaning_log.csv")
stats = pd.read_csv(TABLES / "statistical_tests_summary.csv")
churn = pd.read_csv(TABLES / "churn_model_test_metrics.csv").set_index("model")
camp = pd.read_csv(TABLES / "churn_campaign_business_case.csv")
fc = pd.read_csv(TABLES / "forecast_oct2026_by_category.csv")
rfm = pd.read_csv(TABLES / "q08_rfm_segment_summary.csv")
q09 = pd.read_csv(TABLES / "q09_promo_cooking_oil_did.csv")
q12 = pd.read_csv(TABLES / "q12_drifting_by_county.csv")
mp = tx[tx.payment_method != "Unknown"]
mshare_last = (mp[mp.date >= "2026-09-01"].payment_method == "M-Pesa").mean()
mshare_first = (mp[mp.date < "2024-11-01"].payment_method == "M-Pesa").mean()


def stat(name):
    return stats[stats.test.str.startswith(name)].iloc[0].to_dict()


data = {
    "months": [str(m) for m in monthly.index],
    "nominal_m": (monthly.nominal / 1e6).round(2).tolist(),
    "real_m": (monthly.real / 1e6).round(2).tolist(),
    "rev_y2_m": round(rev_y2 / 1e6, 1),
    "growth_nominal": round(100 * (rev_y2 / rev_y1 - 1), 1),
    "growth_real": round(100 * (real_y2 / real_y1 - 1), 1),
    "receipts_y2": int(y2.sum()),
    "avg_basket": round(tx.net_amount[y2].mean()),
    "fmt_rev_per_sqm": fmt.to_dict(),
    "payday_lift": round(100 * (pay[True] / pay[False] - 1)),
    "dec_vs_avg": round(100 * (mon[12] / mon.mean() - 1)),
    "jan_vs_avg": round(100 * (mon[1] / mon.mean() - 1)),
    "mpesa_first": round(100 * mshare_first, 1), "mpesa_last": round(100 * mshare_last, 1),
    "clean": {
        "dup_receipts": int(log.loc[log.step.str.startswith("drop exact duplicate rows"), "rows_affected"].iloc[0]),
        "dup_lines": int(log.loc[log.step.str.startswith("drop exact duplicate lines"), "rows_affected"].iloc[0]),
        "payment_fixed": int(log.loc[log.step.str.startswith("standardise payment"), "note"].iloc[0].split()[0]),
        "prices_imputed": int(log.loc[log.step.str.startswith("impute missing unit_price"), "note"].iloc[0].split()[0]),
        "date_fixed": int(log.loc[log.step.str.startswith("parse mixed"), "note"].iloc[0].split()[0]),
        "outliers": int(log.loc[log.step.str.startswith("drop quantity outliers"), "rows_affected"].iloc[0]),
        "test_rows": int(log.loc[log.step.str.startswith("remove POS test"), "rows_affected"].iloc[0]),
    },
    "promo": {"h1": stat("H1"), "h2": stat("H2"),
              "q09": q09[["grp", "period", "avg_daily_units_per_store"]].to_dict("records")},
    "nakuru": stat("H7"), "drift": q12.head(5).to_dict("records"),
    "rfm": rfm[["rfm_segment", "pct_customers", "pct_revenue"]].to_dict("records"),
    "churn": {k: churn.loc[k].round(3).to_dict() for k in churn.index},
    "campaign": camp.to_dict("records"),
    "forecast": fc[fc.category != "TOTAL"][["category", "sep_2026_actual", "forecast_units", "low_80", "high_80"]].to_dict("records"),
    "forecast_total": fc[fc.category == "TOTAL"].iloc[0].to_dict(),
}
(out_dir / "deck_data.json").write_text(json.dumps(data, indent=1, default=float))
print("wrote", out_dir / "deck_data.json")
