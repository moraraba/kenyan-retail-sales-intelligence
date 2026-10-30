"""
Milestone 4 - Load the cleaned data into PostgreSQL.

Steps: create database -> run sql/01_schema.sql -> \\copy reference + dimension CSVs ->
build dim_date (sql/01b_dim_date.sql) -> \\copy facts -> indexes + view (sql/02_post_load.sql).

Run:  python src/load_postgres.py
"""
import pandas as pd

import db
from config import ROOT, PROCESSED, EXTERNAL

STAGE = PROCESSED / "sql_stage"
STAGE.mkdir(exist_ok=True)
SQL = ROOT / "sql"


def stage(df, name, cols):
    path = STAGE / f"{name}.csv"
    df[cols].to_csv(path, index=False)
    return path


def copy(table, path, cols):
    db.execute(f"\\copy retail.{table} ({', '.join(cols)}) FROM '{path}' WITH (FORMAT csv, HEADER true)")


def main():
    db.ensure_database()
    db.execute("SET client_min_messages = warning; DROP SCHEMA IF EXISTS retail CASCADE;")
    db.run_file(SQL / "01_schema.sql")

    pop = pd.read_csv(EXTERNAL / "county_population_2019.csv")
    copy("ref_county_population", stage(pop, "pop", ["county", "population_2019"]), ["county", "population_2019"])

    cpi = pd.read_csv(PROCESSED / "cpi_index.csv")
    cpi["month"] = pd.PeriodIndex(cpi.month, freq="M").to_timestamp().strftime("%Y-%m-%d")
    copy("ref_cpi", stage(cpi.round(3), "cpi", ["month", "inflation_12m_pct", "cpi_index"]),
         ["month", "inflation_12m_pct", "cpi_index"])

    hol = pd.read_csv(EXTERNAL / "kenya_public_holidays.csv").rename(
        columns={"date": "holiday_date", "type": "holiday_type"})
    hol = hol.drop_duplicates("holiday_date")
    copy("ref_holiday", stage(hol, "hol", ["holiday_date", "holiday_name", "holiday_type"]),
         ["holiday_date", "holiday_name", "holiday_type"])

    stores = pd.read_csv(PROCESSED / "stores.csv")
    c = ["store_id", "store_name", "county", "town", "store_format", "size_sqm", "open_date"]
    copy("dim_store", stage(stores, "stores", c), c)

    prod = pd.read_csv(PROCESSED / "products.csv")
    c = ["product_id", "product_name", "category", "subcategory", "base_price", "brand_tier"]
    copy("dim_product", stage(prod, "products", c), c)

    cust = pd.read_csv(PROCESSED / "customers.csv")
    cust["birth_year"] = cust.birth_year.astype("Int64")
    c = ["customer_id", "gender", "birth_year", "age_band", "signup_date", "home_store_id"]
    copy("dim_customer", stage(cust, "customers", c), c)

    promo = pd.read_csv(PROCESSED / "promotions.csv")
    c = ["promo_id", "promo_name", "start_date", "end_date", "discount_pct", "scope_type", "scope_value", "store_ids"]
    copy("dim_promotion", stage(promo, "promos", c), c)

    db.run_file(SQL / "01b_dim_date.sql")

    tx = pd.read_pickle(PROCESSED / "transactions.pkl")
    tx["transaction_ts"] = tx.transaction_datetime.dt.strftime("%Y-%m-%d %H:%M:%S")
    tx["date_key"] = tx.transaction_datetime.dt.strftime("%Y-%m-%d")
    for col in ["n_lines", "units"]:
        tx[col] = tx[col].astype("Int64")
    c = ["transaction_id", "transaction_ts", "date_key", "store_id", "till_no", "customer_id", "payment_method",
         "n_lines", "units", "gross_amount", "discount_amount", "net_amount"]
    tx[["gross_amount", "discount_amount", "net_amount"]] = tx[["gross_amount", "discount_amount", "net_amount"]].round(2)
    copy("fact_transaction", stage(tx, "transactions", c), c)

    items = pd.read_pickle(PROCESSED / "transaction_items.pkl")
    c = ["transaction_id", "line_no", "product_id", "quantity", "unit_price", "discount_amount", "promo_id", "net_amount"]
    copy("fact_sales_line", stage(items.round(2), "lines", c), c)

    db.run_file(SQL / "02_post_load.sql")
    counts = db.query("""
        SELECT 'fact_transaction' AS table_name, COUNT(*) AS rows FROM retail.fact_transaction UNION ALL
        SELECT 'fact_sales_line', COUNT(*) FROM retail.fact_sales_line UNION ALL
        SELECT 'dim_customer', COUNT(*) FROM retail.dim_customer UNION ALL
        SELECT 'dim_date', COUNT(*) FROM retail.dim_date""")
    print(counts.to_string(index=False))


if __name__ == "__main__":
    main()
