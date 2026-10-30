"""
Milestone 2 - Data cleaning and preparation (pandas).

Each function takes a raw DataFrame and returns a clean one, recording what it changed in
a shared `LOG` list so the notebook and README can report a data-quality audit trail.

Run:  python src/clean.py      (reads data/raw, writes data/processed)
"""
import re
import numpy as np
import pandas as pd

from config import RAW, EXTERNAL, PROCESSED, START_DATE, END_DATE

LOG = []


def log(table, step, before, after, note=""):
    LOG.append({"table": table, "step": step, "rows_before": before,
                "rows_after": after, "rows_affected": before - after if before != after else None,
                "note": note})


# ------------------------------------------------------------------ dimension tables
def clean_stores(df):
    df = df.copy()
    n_bad = (df.county != df.county.str.strip().str.title()).sum()
    df["county"] = df.county.str.strip().str.title()
    df["open_date"] = pd.to_datetime(df.open_date)
    log("stores", "standardise county names (case/whitespace)", len(df), len(df), f"{n_bad} values fixed")
    return df


def clean_products(df):
    df = df.copy()
    missing = df.category.isna().sum()
    lookup = df.dropna(subset=["category"]).groupby("subcategory").category.agg(lambda s: s.mode()[0])
    # subcategories that appear only once cannot be looked up -> curated merchandising map
    manual = {"Yoghurt": "Dairy"}
    df["category"] = df.category.fillna(df.subcategory.map(lookup)).fillna(df.subcategory.map(manual))
    assert df.category.notna().all(), "unmapped subcategory - extend the manual map"
    log("products", "impute missing category from subcategory", len(df), len(df), f"{missing} filled")
    return df


def clean_customers(df):
    df = df.copy()
    n0 = len(df)
    df = df.drop_duplicates()
    log("customers", "drop duplicate sign-up rows", n0, len(df))
    g = df.gender.astype("string").str.strip().str.upper().str[0]
    df["gender"] = g.where(g.isin(["F", "M"]), "Unknown").fillna("Unknown")
    log("customers", "standardise gender to F/M/Unknown", len(df), len(df),
        f"{(df.gender == 'Unknown').sum()} unknown")
    bad = ~df.birth_year.between(1930, 2008)
    df.loc[bad, "birth_year"] = np.nan
    log("customers", "set impossible birth years (<1930 or >2008) to missing", len(df), len(df), f"{bad.sum()} values")
    df["signup_date"] = pd.to_datetime(df.signup_date)
    df["age"] = 2026 - df.birth_year
    df["age_band"] = pd.cut(df.age, [17, 24, 34, 44, 54, 120],
                            labels=["18-24", "25-34", "35-44", "45-54", "55+"]).astype("string").fillna("Unknown")
    return df


def clean_promotions(df):
    df = df.copy()
    df["start_date"] = pd.to_datetime(df.start_date)
    df["end_date"] = pd.to_datetime(df.end_date)
    df["duration_days"] = (df.end_date - df.start_date).dt.days + 1
    return df


# ------------------------------------------------------------------ fact tables
PAYMENT_MAP = {"MPESA": "M-Pesa", "M-PESA": "M-Pesa", "M PESA": "M-Pesa",
               "CASH": "Cash", "CSH": "Cash", "CARD": "Card", "VISA/MASTERCARD": "Card",
               "AIRTEL MONEY": "Airtel Money", "AIRTEL": "Airtel Money"}


def parse_amount(v):
    """'KES 1,234.50' -> 1234.5 ; numbers pass through ; blanks -> NaN"""
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^0-9.\-]", "", str(v))
    return float(s) if s else np.nan


def clean_transactions(df, stores):
    df = df.copy()
    n0 = len(df)
    df = df.drop_duplicates()
    log("transactions", "drop exact duplicate rows", n0, len(df))

    df["store_id"] = df.store_id.str.strip().str.upper()
    n1 = len(df)
    df = df[df.store_id.isin(stores.store_id) & ~df.transaction_id.str.startswith("TEST")]
    log("transactions", "remove POS test transactions (unknown store S999 / TEST ids)", n1, len(df))

    # mixed date formats: ISO 'YYYY-mm-dd HH:MM:SS' and 'dd/mm/YYYY HH:MM'
    iso = pd.to_datetime(df.transaction_datetime, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    dmy = pd.to_datetime(df.transaction_datetime, format="%d/%m/%Y %H:%M", errors="coerce")
    log("transactions", "parse mixed datetime formats (dd/mm/YYYY rows)", len(df), len(df),
        f"{iso.isna().sum()} non-ISO rows parsed day-first")
    df["transaction_datetime"] = iso.fillna(dmy)
    n2 = len(df)
    in_range = df.transaction_datetime.between(START_DATE, pd.Timestamp(END_DATE) + pd.Timedelta(days=1))
    df = df[in_range]
    log("transactions", "drop rows with impossible dates (POS clock errors, year 2031)", n2, len(df))

    # duplicate transaction ids that are not exact duplicates (e.g. a re-keyed date format)
    n3 = len(df)
    df = df.sort_values("transaction_datetime").drop_duplicates("transaction_id", keep="first")
    log("transactions", "drop repeated transaction_id (same receipt keyed twice)", n3, len(df))

    raw_pm = df.payment_method.astype("string").str.strip()
    norm = raw_pm.str.upper().map(PAYMENT_MAP).fillna(raw_pm)
    norm = norm.where(norm.isin(["M-Pesa", "Cash", "Card", "Airtel Money"]))
    fixed = (raw_pm != norm).sum()
    df["payment_method"] = norm.fillna("Unknown")
    log("transactions", "standardise payment method labels; missing -> 'Unknown'", len(df), len(df),
        f"{fixed} labels changed, {(df.payment_method == 'Unknown').sum()} unknown")

    df["total_amount_reported"] = df.total_amount.map(parse_amount)
    df = df.drop(columns="total_amount")
    df["customer_id"] = df.customer_id.replace("", np.nan)
    df["is_member"] = df.customer_id.notna()
    return df.reset_index(drop=True)


def clean_items(df, tx, products):
    df = df.copy()
    n0 = len(df)
    df = df.drop_duplicates()
    log("items", "drop exact duplicate lines", n0, len(df))
    n1 = len(df)
    df = df[df.transaction_id.isin(tx.transaction_id)]
    log("items", "drop orphan lines whose transaction was removed", n1, len(df))

    # quantity keying errors: robust rule = above 30 units of one SKU in a household basket
    # (99th pct of positive qty is ~4; 30 is >7x that). We drop them rather than guess.
    n2 = len(df)
    pos = df.quantity[df.quantity > 0]
    q99 = pos.quantile(0.99)
    out = df.quantity.abs() > 30
    df = df[~out]
    log("items", f"drop quantity outliers (|qty| > 30; 99th pct = {q99:.0f})", n2, len(df))

    # missing unit price -> median price of that product, same store, same month
    tx_ix = tx.set_index("transaction_id")
    df["store_id"] = df.transaction_id.map(tx_ix.store_id)
    df["month"] = df.transaction_id.map(tx_ix.transaction_datetime).dt.to_period("M")
    miss = df.unit_price.isna().sum()
    med = df.groupby(["product_id", "store_id", "month"]).unit_price.transform("median")
    med2 = df.groupby(["product_id", "month"]).unit_price.transform("median")
    df["unit_price"] = df.unit_price.fillna(med).fillna(med2)
    log("items", "impute missing unit_price (product-store-month median)", len(df), len(df), f"{miss} filled")

    df["promo_id"] = df.promo_id.replace("", np.nan)
    df["is_return"] = df.quantity < 0
    df["gross_amount"] = df.quantity * df.unit_price
    df["net_amount"] = df.gross_amount - df.discount_amount
    return df.drop(columns=["store_id", "month"]).reset_index(drop=True)


# ------------------------------------------------------------------ context + features
def cpi_index():
    """Monthly price index (Oct 2024 = 100) built from KNBS 12-month inflation via CBK.
    Monthly growth is approximated as (1+yoy)^(1/12)-1 - documented as an approximation."""
    infl = pd.read_csv(EXTERNAL / "kenya_inflation_monthly.csv")
    infl["month"] = pd.PeriodIndex.from_fields(year=infl.year, month=infl.month, freq="M")
    infl = infl[infl.month >= pd.Period("2024-10", "M")].reset_index(drop=True)
    g = (1 + infl.inflation_12m_pct / 100) ** (1 / 12)
    g.iloc[0] = 1.0
    infl["cpi_index"] = 100 * g.cumprod()
    return infl[["month", "inflation_12m_pct", "cpi_index"]]


def holidays():
    h = pd.read_csv(EXTERNAL / "kenya_public_holidays.csv", parse_dates=["date"])
    return h[h.type != "reference"]


def build_sales_fact(items, tx, products, stores, customers):
    """Line-level fact table with every feature the analysis needs."""
    f = items.merge(tx[["transaction_id", "transaction_datetime", "store_id", "customer_id",
                        "payment_method", "is_member"]], on="transaction_id", how="left")
    f = f.merge(products[["product_id", "product_name", "category", "subcategory", "brand_tier"]],
                on="product_id", how="left")
    f = f.merge(stores[["store_id", "store_name", "county", "store_format"]], on="store_id", how="left")
    dt = f.transaction_datetime
    f["date"] = dt.dt.normalize()
    f["month"] = dt.dt.to_period("M")
    f["year"] = dt.dt.year
    f["month_num"] = dt.dt.month
    f["day_of_week"] = dt.dt.day_name()
    f["hour"] = dt.dt.hour
    f["is_weekend"] = dt.dt.dayofweek >= 5
    f["is_payday_window"] = (dt.dt.day >= 25) | (dt.dt.day <= 3)
    hol = set(holidays().date)
    f["is_public_holiday"] = f.date.isin(hol)
    f["on_promo"] = f.promo_id.notna()
    cpi = cpi_index()
    f = f.merge(cpi, on="month", how="left")
    f["net_amount_real"] = f.net_amount * 100 / f.cpi_index   # Oct-2024 shillings
    return f


def build_transactions_enriched(tx, items):
    agg = items.groupby("transaction_id").agg(
        n_lines=("product_id", "nunique"), units=("quantity", "sum"),
        gross_amount=("gross_amount", "sum"), discount_amount=("discount_amount", "sum"),
        net_amount=("net_amount", "sum"), has_promo=("promo_id", lambda s: s.notna().any()))
    t = tx.merge(agg, on="transaction_id", how="left")
    # reported till total vs recomputed from lines - a reconciliation check
    t["total_mismatch"] = (t.total_amount_reported - t.net_amount).abs() > 1
    return t


def main():
    stores = clean_stores(pd.read_csv(RAW / "stores.csv"))
    products = clean_products(pd.read_csv(RAW / "products.csv"))
    customers = clean_customers(pd.read_csv(RAW / "customers.csv"))
    promos = clean_promotions(pd.read_csv(RAW / "promotions.csv"))
    tx = clean_transactions(pd.read_csv(RAW / "transactions.csv", dtype={"customer_id": str}), stores)
    items = clean_items(pd.read_csv(RAW / "transaction_items.csv", dtype={"promo_id": str}), tx, products)
    tx = build_transactions_enriched(tx, items)
    n = len(tx)
    tx = tx[tx.n_lines.notna()]
    log("transactions", "drop transactions left with no lines", n, len(tx))
    sales = build_sales_fact(items, tx, products, stores, customers)

    stores.to_csv(PROCESSED / "stores.csv", index=False)
    products.to_csv(PROCESSED / "products.csv", index=False)
    customers.to_csv(PROCESSED / "customers.csv", index=False)
    promos.to_csv(PROCESSED / "promotions.csv", index=False)
    tx.to_csv(PROCESSED / "transactions.csv", index=False)
    items.to_pickle(PROCESSED / "transaction_items.pkl")
    sales.to_pickle(PROCESSED / "sales_lines.pkl")   # large: kept as pickle, rebuilt by run_all
    tx.to_pickle(PROCESSED / "transactions.pkl")
    cpi_index().to_csv(PROCESSED / "cpi_index.csv", index=False)
    pd.DataFrame(LOG).to_csv(PROCESSED / "cleaning_log.csv", index=False)
    print(pd.DataFrame(LOG).to_string())
    return sales


if __name__ == "__main__":
    main()
