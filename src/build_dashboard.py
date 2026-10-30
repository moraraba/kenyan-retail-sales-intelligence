"""
Milestone 7 - Manager dashboard.

Builds two things from the processed data and model outputs:
  1. dashboard/Mavuno_Mart_Sales_Dashboard.xlsx - a self-contained Excel dashboard (KPI tiles driven by formulas,
     native Excel charts, insight panel, drill-down sheets). Opens in Excel, LibreOffice or Google Sheets.
  2. dashboard/powerbi/*.csv - a star schema ready to import into Power BI Desktop (see dashboard/POWERBI_GUIDE.md
     and dashboard/powerbi/DAX_measures.md).

Run after the notebooks:  python src/build_dashboard.py
"""
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from config import PROCESSED, TABLES, DASHBOARD, PALETTE

PBI = DASHBOARD / "powerbi"
PBI.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ data
tx = pd.read_pickle(PROCESSED / "transactions.pkl")
sales = pd.read_pickle(PROCESSED / "sales_lines.pkl")
stores = pd.read_csv(PROCESSED / "stores.csv")
customers = pd.read_csv(PROCESSED / "customers.csv")
products = pd.read_csv(PROCESSED / "products.csv")
cpi = pd.read_csv(PROCESSED / "cpi_index.csv")
fc = pd.read_csv(PROCESSED / "forecast_oct2026_store_category.csv")
churn = pd.read_csv(PROCESSED / "churn_scores_2026-09-30.csv")
rfm = pd.read_csv(TABLES / "q08_rfm_segment_summary.csv")
stats_tbl = pd.read_csv(TABLES / "statistical_tests_summary.csv")
tx["date"] = tx.transaction_datetime.dt.normalize()
tx["month"] = tx.transaction_datetime.dt.to_period("M")
Y2 = tx.date >= "2025-10-01"

monthly = tx.groupby("month").agg(revenue=("net_amount", "sum"), receipts=("transaction_id", "count"),
                                  members=("customer_id", "nunique")).reset_index()
monthly["real_revenue"] = (sales.groupby("month").net_amount_real.sum()).values
monthly = monthly.merge(cpi.assign(month=pd.PeriodIndex(cpi.month, freq="M")), on="month")
mp = tx[tx.payment_method != "Unknown"].groupby(["month", "payment_method"]).size().unstack(fill_value=0)
monthly = monthly.merge(mp.reset_index(), on="month")
monthly["month_label"] = monthly.month.dt.strftime("%b %Y")

st = stores.copy()
st["revenue_y1"] = st.store_id.map(tx[~Y2].groupby("store_id").net_amount.sum()).fillna(0)
st["revenue_y2"] = st.store_id.map(tx[Y2].groupby("store_id").net_amount.sum()).fillna(0)
st["receipts_y2"] = st.store_id.map(tx[Y2].groupby("store_id").size()).fillna(0)
st = st.sort_values("revenue_y2", ascending=False)

cat = sales[sales.date >= "2025-10-01"].groupby("category").agg(revenue=("net_amount", "sum"),
                                                                   units=("quantity", "sum")).reset_index()
cat["revenue_y1"] = cat.category.map(sales[sales.date < "2025-10-01"].groupby("category").net_amount.sum())
cat = cat.sort_values("revenue", ascending=False)

fc_cat = fc.groupby("category")[["forecast_units", "low_80", "high_80", "forecast_revenue"]].sum().reset_index()
sep = sales[(sales.date >= "2026-09-01") & (sales.quantity > 0)].groupby("category").agg(
    sep_units=("quantity", "sum"), sep_revenue=("net_amount", "sum"))
fc_cat = fc_cat.merge(sep.reset_index(), on="category").sort_values("forecast_revenue", ascending=False)

# ------------------------------------------------------------------ styles
FONT = "Arial"
DARK = "1F2A37"
BLUE = PALETTE[0].lstrip("#").upper()
ORANGE = PALETTE[1].lstrip("#").upper()
GREEN = PALETTE[2].lstrip("#").upper()
LIGHT = "F3F4F1"
thin = Side(style="thin", color="D9D8D3")
H = Font(name=FONT, bold=True, color="FFFFFF")
HFILL = PatternFill("solid", fgColor=DARK)
B = Font(name=FONT, size=10)


def write_table(ws, df, start_row=1, start_col=1, formats=None, widths=None):
    formats = formats or {}
    for j, col in enumerate(df.columns):
        c = ws.cell(start_row, start_col + j, col)
        c.font, c.fill = H, HFILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = float(v)
            c = ws.cell(start_row + i, start_col + j, v)
            c.font = B
            c.border = Border(bottom=thin)
            fmt = formats.get(df.columns[j])
            if fmt:
                c.number_format = fmt
    ws.row_dimensions[start_row].height = 30
    for j, col in enumerate(df.columns):
        ws.column_dimensions[get_column_letter(start_col + j)].width = (widths or {}).get(col, max(12, len(str(col)) + 2))
    ws.freeze_panes = ws.cell(start_row + 1, start_col)


KES = '#,##0;(#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
MILL = '"KES "#,##0.0,,"M"'

wb = Workbook()
dash = wb.active
dash.title = "Dashboard"

# ------------------------------------------------------------------ data sheets
ws = wb.create_sheet("Monthly")
mdf = monthly[["month_label", "revenue", "real_revenue", "receipts", "members", "inflation_12m_pct",
               "M-Pesa", "Cash", "Card", "Airtel Money"]].copy()
mdf.columns = ["Month", "Revenue (KES)", "Real revenue (Oct-24 KES)", "Receipts", "Active members",
               "Inflation 12m (%)", "M-Pesa receipts", "Cash receipts", "Card receipts", "Airtel receipts"]
write_table(ws, mdf.round(0), formats={"Revenue (KES)": KES, "Real revenue (Oct-24 KES)": KES, "Receipts": "#,##0",
                                        "Active members": "#,##0", "M-Pesa receipts": "#,##0", "Cash receipts": "#,##0",
                                        "Card receipts": "#,##0", "Airtel receipts": "#,##0"},
            widths={"Month": 11})
n = len(mdf)
extra = ["Avg basket (KES)", "M-Pesa share", "Cash share", "Card share"]
for k, title in enumerate(extra):
    c = ws.cell(1, 11 + k, title); c.font, c.fill = H, HFILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.column_dimensions[get_column_letter(11 + k)].width = 13
for r in range(2, n + 2):
    ws.cell(r, 11, f"=IFERROR(B{r}/D{r},0)").number_format = KES
    tot = f"SUM(G{r}:J{r})"
    ws.cell(r, 12, f"=IFERROR(G{r}/{tot},0)").number_format = PCT
    ws.cell(r, 13, f"=IFERROR(H{r}/{tot},0)").number_format = PCT
    ws.cell(r, 14, f"=IFERROR(I{r}/{tot},0)").number_format = PCT
    for col in range(11, 15):
        ws.cell(r, col).font = B
last = n + 1          # last data row in Monthly
y2_first = last - 11  # first row of last 12 months
y1_first, y1_last = last - 23, last - 12

ws = wb.create_sheet("Stores")
sdf = st[["store_name", "county", "store_format", "size_sqm", "revenue_y1", "revenue_y2", "receipts_y2"]].copy()
sdf["store_name"] = sdf.store_name.str.replace("Mavuno Mart ", "")
sdf.columns = ["Store", "County", "Format", "Size (sq m)", "Revenue Y1 (KES)", "Revenue Y2 (KES)", "Receipts Y2"]
write_table(ws, sdf.round(0), formats={"Revenue Y1 (KES)": KES, "Revenue Y2 (KES)": KES, "Receipts Y2": "#,##0",
                                        "Size (sq m)": "#,##0"}, widths={"Store": 22})
for k, title in enumerate(["Growth Y2 vs Y1", "Revenue per sq m (KES)", "Share of chain"]):
    c = ws.cell(1, 8 + k, title); c.font, c.fill = H, HFILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.column_dimensions[get_column_letter(8 + k)].width = 14
ns = len(sdf) + 1
for r in range(2, ns + 1):
    ws.cell(r, 8, f'=IF(E{r}>0,F{r}/E{r}-1,"new store")').number_format = PCT
    ws.cell(r, 9, f"=F{r}/D{r}").number_format = KES
    ws.cell(r, 10, f"=F{r}/SUM($F$2:$F${ns})").number_format = PCT
    for col in (8, 9, 10):
        ws.cell(r, col).font = B
ws.cell(ns + 2, 1, "Y1 = Oct 2024 - Sep 2025; Y2 = Oct 2025 - Sep 2026. Kitengela opened 14 Jun 2025.").font = Font(name=FONT, italic=True, size=9)

ws = wb.create_sheet("Categories")
cdf = cat[["category", "revenue_y1", "revenue", "units"]].copy()
cdf.columns = ["Category", "Revenue Y1 (KES)", "Revenue Y2 (KES)", "Units Y2"]
write_table(ws, cdf.round(0), formats={"Revenue Y1 (KES)": KES, "Revenue Y2 (KES)": KES, "Units Y2": "#,##0"},
            widths={"Category": 22})
nc = len(cdf) + 1
for k, title in enumerate(["Growth", "Share Y2"]):
    c = ws.cell(1, 5 + k, title); c.font, c.fill = H, HFILL
    ws.column_dimensions[get_column_letter(5 + k)].width = 12
for r in range(2, nc + 1):
    ws.cell(r, 5, f"=C{r}/B{r}-1").number_format = PCT
    ws.cell(r, 6, f"=C{r}/SUM($C$2:$C${nc})").number_format = PCT

ws = wb.create_sheet("Forecast_Oct2026")
fdf = fc_cat[["category", "sep_units", "forecast_units", "low_80", "high_80", "sep_revenue", "forecast_revenue"]].copy()
fdf.columns = ["Category", "Sep 2026 actual units", "Oct 2026 forecast units", "Low (80%)", "High (80%)",
               "Sep 2026 revenue (KES)", "Oct 2026 forecast revenue (KES)"]
write_table(ws, fdf.round(0), formats={c: "#,##0" for c in fdf.columns[1:5]} | {fdf.columns[5]: KES, fdf.columns[6]: KES},
            widths={"Category": 22})
nf = len(fdf) + 1
c = ws.cell(1, 8, "Change vs Sep"); c.font, c.fill = H, HFILL
ws.column_dimensions["H"].width = 13
for r in range(2, nf + 1):
    ws.cell(r, 8, f"=C{r}/B{r}-1").number_format = PCT
ws.cell(nf + 1, 1, "TOTAL").font = Font(name=FONT, bold=True)
for col in (2, 3, 6, 7):
    L = get_column_letter(col)
    cc = ws.cell(nf + 1, col, f"=SUM({L}2:{L}{nf})")
    cc.font = Font(name=FONT, bold=True); cc.number_format = KES
ws.cell(nf + 3, 1, "Model: gradient boosting (Poisson), backtest WAPE 33% at store-category-day vs 46% seasonal naive; "
        "monthly category totals within ~3% on average. 80% range from backtest errors (category ranges do not add up to a total range).").font = Font(name=FONT, italic=True, size=9)
sc = fc[["store_name", "county", "category", "forecast_units", "low_80", "high_80", "forecast_revenue"]].copy()
sc["store_name"] = sc.store_name.str.replace("Mavuno Mart ", "")
sc.columns = ["Store", "County", "Category", "Forecast units", "Low (80%)", "High (80%)", "Forecast revenue (KES)"]
write_table(ws, sc.round(0), start_row=nf + 6, formats={"Forecast units": "#,##0", "Low (80%)": "#,##0",
                                                         "High (80%)": "#,##0", "Forecast revenue (KES)": KES})
ws.freeze_panes = "A2"

ws = wb.create_sheet("Churn_Risk")
cr = churn.head(500)[["customer_id", "home_store_id", "county", "risk_band", "churn_probability", "recency_days",
                      "freq_90", "spend_365", "value_at_risk_12m"]].copy()
cr.columns = ["Customer", "Home store", "County", "Risk band", "Churn probability", "Days since last visit",
              "Visits last 90d", "Spend last 12m (KES)", "12m spend at risk (KES)"]
write_table(ws, cr, formats={"Churn probability": "0%", "Spend last 12m (KES)": KES, "12m spend at risk (KES)": KES})
ws2 = wb.create_sheet("Churn_All")   # full scored list feeds the KPI tiles
write_table(ws2, churn[["customer_id", "county", "risk_band", "churn_probability", "value_at_risk_12m"]],
            formats={"churn_probability": "0%", "value_at_risk_12m": KES})
nch = len(churn) + 1

ws = wb.create_sheet("RFM_Segments")
write_table(ws, rfm, formats={"revenue_12m": KES})

ws = wb.create_sheet("Promo_Tests")
stdf = stats_tbl.copy()
write_table(ws, stdf.round(4), widths={"test": 26, "conclusion": 44})

# ------------------------------------------------------------------ dashboard sheet
dash.sheet_view.showGridLines = False
for col in range(1, 26):
    dash.column_dimensions[get_column_letter(col)].width = 11.5
dash["B2"] = "Mavuno Mart - Customer & Sales Intelligence"
dash["B2"].font = Font(name=FONT, size=20, bold=True, color=DARK)
dash["B3"] = "Last 12 months = Oct 2025 - Sep 2026 vs prior 12 months. All amounts in Kenya shillings (KES). Data refreshed 30 Sep 2026."
dash["B3"].font = Font(name=FONT, size=10, color="52514E")

tiles = [
    ("Revenue, last 12 months", f"=SUM(Monthly!B{y2_first}:B{last})", MILL),
    ("Growth vs prior year", f"=SUM(Monthly!B{y2_first}:B{last})/SUM(Monthly!B{y1_first}:B{y1_last})-1", PCT),
    ("Real growth (after inflation)", f"=SUM(Monthly!C{y2_first}:C{last})/SUM(Monthly!C{y1_first}:C{y1_last})-1", PCT),
    ("Receipts, last 12 months", f"=SUM(Monthly!D{y2_first}:D{last})", "#,##0"),
    ("Average basket", f"=SUM(Monthly!B{y2_first}:B{last})/SUM(Monthly!D{y2_first}:D{last})", '"KES "#,##0'),
    ("M-Pesa share (Sep 26)", f"=Monthly!L{last}", PCT),
    ("High-risk members", f'=COUNTIF(Churn_All!C2:C{nch},"High")', "#,##0"),
    ("Oct 2026 forecast revenue", f"=Forecast_Oct2026!G{nf + 1}", MILL),
]
for i, (label, formula, fmt) in enumerate(tiles):
    r = 5 if i < 4 else 9
    c = 2 + (i % 4) * 3
    for rr in range(r, r + 3):
        for cc in range(c, c + 3):
            dash.cell(rr, cc).fill = PatternFill("solid", fgColor=LIGHT)
    dash.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + 2)
    dash.merge_cells(start_row=r + 1, start_column=c, end_row=r + 2, end_column=c + 2)
    lab = dash.cell(r, c, label)
    lab.font = Font(name=FONT, size=9, color="52514E")
    val = dash.cell(r + 1, c, formula)
    val.font = Font(name=FONT, size=18, bold=True, color=DARK)
    val.number_format = fmt
    val.alignment = Alignment(horizontal="left", vertical="center")

# insight panel
dash["N5"] = "What the data says - and what to do"
dash["N5"].font = Font(name=FONT, size=13, bold=True, color=DARK)
insights = [
    "1. Real growth is about half of nominal growth - report both; 2026 inflation (6-7%) flatters sales.",
    "2. December is ~40% above an average month and January ~15% below; month-end payday days bring ~30% more revenue - roster and stock to it.",
    "3. Express stores earn the most per sq m - prioritise small-format openings (Meru has 1.5M people and no store).",
    "4. Nakuru traffic fell ~20% from Feb 2026 (new competitor); Nakuru members lapse at 2x the chain rate - act now.",
    "5. The cooking-oil test lifted units ~65% (significant) but lost gross profit at 15% off - rerun at 7-10%.",
    "6. Champions (~30% of members) bring ~80% of member revenue - protect them; churn model flags at-risk members.",
    "7. Tea+sugar, unga+sukuma, diapers+wipes, books+pens sell together - use for adjacency and bundles.",
]
for k, t in enumerate(insights):
    cell = dash.cell(6 + k, 14, t)
    cell.font = Font(name=FONT, size=10)

# charts
def line_chart(title, sheet, cols, min_row, max_row, cats_col, y_title, colors, w=17, h=7.5):
    ch = LineChart()
    ch.title, ch.y_axis.title, ch.height, ch.width = title, y_title, h, w
    for col, color in zip(cols, colors):
        ref = Reference(sheet, min_col=col, min_row=min_row - 1, max_row=max_row)
        ch.add_data(ref, titles_from_data=True)
        s = ch.series[-1]
        s.graphicalProperties.line.solidFill = color
        s.graphicalProperties.line.width = 22000
        s.smooth = False
    ch.set_categories(Reference(sheet, min_col=cats_col, min_row=min_row, max_row=max_row))
    ch.legend.position = "b"
    ch.y_axis.majorGridlines.spPr = None
    ch.y_axis.delete = False
    ch.x_axis.delete = False
    return ch


def bar_chart(title, sheet, val_cols, min_row, max_row, cats_col, colors, horizontal=True, w=17, h=7.5, y_title=None):
    ch = BarChart()
    ch.type = "bar" if horizontal else "col"
    ch.title, ch.height, ch.width = title, h, w
    if y_title:
        ch.y_axis.title = y_title
    for col, color in zip(val_cols, colors):
        ch.add_data(Reference(sheet, min_col=col, min_row=min_row - 1, max_row=max_row), titles_from_data=True)
        ch.series[-1].graphicalProperties.solidFill = color
        ch.series[-1].graphicalProperties.line.noFill = True
    ch.set_categories(Reference(sheet, min_col=cats_col, min_row=min_row, max_row=max_row))
    ch.gapWidth = 60
    ch.x_axis.tickLblSkip = 1
    if horizontal:
        ch.x_axis.scaling.orientation = "maxMin"
    ch.legend = None if len(val_cols) == 1 else ch.legend
    if ch.legend:
        ch.legend.position = "b"
    ch.y_axis.delete = False
    ch.x_axis.delete = False
    return ch


wm, wst, wc, wf = wb["Monthly"], wb["Stores"], wb["Categories"], wb["Forecast_Oct2026"]
dash.add_chart(line_chart("Monthly revenue: nominal vs real (KES)", wm, [2, 3], 2, last, 1, "KES", [BLUE, ORANGE]), "B14")
dash.add_chart(line_chart("Payment mix (share of receipts)", wm, [12, 13, 14], 2, last, 1, "share", [BLUE, ORANGE, GREEN]), "L14")
dash.add_chart(bar_chart("Revenue by category, last 12 months (KES)", wc, [3], 2, nc, 1, [BLUE], h=9.5), "B30")
dash.add_chart(bar_chart("Revenue per sq m by store (KES)", wst, [9], 2, ns, 1, [GREEN], h=12.5), "L30")
dash.add_chart(bar_chart("October 2026 forecast vs September actual (units)", wf, [2, 3], 2, nf, 1,
                         ["A8A7A0", BLUE], horizontal=False, w=17, h=7.5), "B50")
dash.add_chart(bar_chart("Store revenue, last 12 months (KES)", wst, [6], 2, ns, 1, [BLUE], h=12.5), "L57")

# notes sheet
notes = wb.create_sheet("Notes")
rows = [
    ("Definitions", ""),
    ("Revenue", "Net sales after promotional discounts and returns, VAT-inclusive shelf prices (KES)."),
    ("Real revenue", "Revenue deflated to October-2024 shillings with a CPI index built from KNBS 12-month inflation."),
    ("Receipt", "One till transaction. Average basket = revenue / receipts."),
    ("Active member", "Loyalty member with at least one receipt in the month."),
    ("High-risk member", "Churn model probability >= 50% of no purchase in the next 90 days (scored 30 Sep 2026)."),
    ("12m spend at risk", "Churn probability x the member's spend in the last 12 months."),
    ("Forecast", "Gradient-boosting demand model, store x category x day, aggregated to October 2026."),
    ("", ""),
    ("Sources", ""),
    ("Sales data", "Synthetic data for the fictional chain Mavuno Mart (src/generate_data.py, seed 2026)."),
    ("Inflation", "KNBS CPI 12-month inflation, published by the Central Bank of Kenya (centralbank.go.ke/inflation-rates)."),
    ("Population", "KNBS 2019 Kenya Population and Housing Census, Vol. I."),
    ("Holidays", "Public Holidays Act (Cap. 110) and Gazette notices."),
    ("", ""),
    ("How to refresh", "Run `python run_all.py` in the project folder, which regenerates every sheet of this workbook."),
]
for i, (a, b) in enumerate(rows, start=1):
    notes.cell(i, 1, a).font = Font(name=FONT, bold=True)
    notes.cell(i, 2, b).font = Font(name=FONT)
notes.column_dimensions["A"].width = 20
notes.column_dimensions["B"].width = 110

wb.calculation.fullCalcOnLoad = True   # Excel recomputes every formula on open
dash.page_setup.orientation = "landscape"
dash.page_setup.fitToWidth = 1
dash.page_setup.fitToHeight = 0
dash.sheet_properties.pageSetUpPr.fitToPage = True
out = DASHBOARD / "Mavuno_Mart_Sales_Dashboard.xlsx"
wb.save(out)
print("saved", out)

# ------------------------------------------------------------------ Power BI star schema
pd.DataFrame({"date": pd.date_range("2024-10-01", "2026-10-31")}).assign(
    year=lambda d: d.date.dt.year, month_num=lambda d: d.date.dt.month,
    month_name=lambda d: d.date.dt.strftime("%b"), year_month=lambda d: d.date.dt.strftime("%Y-%m"),
    day_name=lambda d: d.date.dt.strftime("%a"), day_of_week=lambda d: d.date.dt.dayofweek + 1,
    is_weekend=lambda d: d.date.dt.dayofweek >= 5,
    is_payday_window=lambda d: (d.date.dt.day >= 25) | (d.date.dt.day <= 3),
    fiscal_year=lambda d: np.where(d.date >= "2025-10-01", "FY2026", "FY2025"),
).to_csv(PBI / "dim_date.csv", index=False)
stores.merge(pd.read_csv(PROCESSED.parent / "external" / "county_population_2019.csv"), on="county", how="left") \
    .to_csv(PBI / "dim_store.csv", index=False)
products.to_csv(PBI / "dim_product.csv", index=False)
customers[["customer_id", "gender", "age_band", "signup_date", "home_store_id"]].to_csv(PBI / "dim_customer.csv", index=False)
t = tx[["transaction_id", "date", "store_id", "customer_id", "payment_method", "n_lines", "units",
        "gross_amount", "discount_amount", "net_amount", "has_promo"]].copy()
t["hour"] = tx.transaction_datetime.dt.hour
t.round({"gross_amount": 2, "discount_amount": 2, "net_amount": 2}).to_csv(PBI / "fact_transaction.csv", index=False)
dsc = sales.groupby(["date", "store_id", "category"]).agg(units=("quantity", "sum"), net_amount=("net_amount", "sum"),
                                                          net_amount_real=("net_amount_real", "sum"),
                                                          discount_amount=("discount_amount", "sum")).reset_index()
dsc.round({"net_amount": 2, "net_amount_real": 2, "discount_amount": 2}).to_csv(PBI / "fact_daily_store_category.csv", index=False)
cpi.to_csv(PBI / "ref_cpi.csv", index=False)
fc.to_csv(PBI / "fact_forecast_oct2026.csv", index=False)
churn.to_csv(PBI / "fact_churn_scores.csv", index=False)
print("Power BI CSVs written to", PBI)
