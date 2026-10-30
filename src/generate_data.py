"""
Milestone 1 - Synthetic data generator for "Mavuno Mart", a fictional Kenyan retail chain.

Why synthetic? Real till data from a Kenyan retailer is confidential. The brief allows a
generated dataset, so this script builds one that behaves like the real thing:
  * 20 stores in 11 counties (one opens mid-period), ~120 SKUs in 9 categories
  * ~6,000 loyalty customers who visit, drift and churn, plus anonymous walk-in shoppers
  * 24 months of transactions (Oct 2024 - Sep 2026) with weekly, payday, festive and
    back-to-school seasonality, real public holidays and real KNBS/CBK inflation in prices
  * M-Pesa, cash, card and Airtel Money payments, with M-Pesa share rising over time
  * A promotion calendar, including a controlled store-level experiment (cooking oil)
  * Known "ground-truth" business events that the analysis should rediscover:
      - a competitor opens near the Nakuru stores in Feb 2026 (walk-ins fall, churn rises)
      - the cooking-oil promo works; the personal-care promo does not
  * Deliberate data-quality problems (duplicates, mixed formats, typos, outliers, gaps)
    so Milestone 2 has real cleaning to do.

Run:  python src/generate_data.py      (deterministic: fixed seed)
"""
import numpy as np
import pandas as pd

from config import RAW, EXTERNAL, SEED, START_DATE, END_DATE

rng = np.random.default_rng(SEED)
DATES = pd.date_range(START_DATE, END_DATE, freq="D")
ND = len(DATES)

# ----------------------------------------------------------------------------- stores
STORES = [
    # id, name, county, town, format, size_sqm, open_date
    ("S001", "Mavuno Mart Westlands", "Nairobi", "Westlands", "Hypermarket", 4200, "2016-03-01"),
    ("S002", "Mavuno Mart CBD Moi Avenue", "Nairobi", "Nairobi CBD", "Supermarket", 1800, "2014-06-01"),
    ("S003", "Mavuno Mart Embakasi", "Nairobi", "Embakasi", "Supermarket", 2100, "2018-09-01"),
    ("S004", "Mavuno Mart Kasarani", "Nairobi", "Kasarani", "Supermarket", 1900, "2019-02-01"),
    ("S005", "Mavuno Mart Karen", "Nairobi", "Karen", "Express", 650, "2021-05-01"),
    ("S006", "Mavuno Mart Rongai", "Nairobi", "Rongai", "Express", 700, "2022-01-15"),
    ("S007", "Mavuno Mart Nyali", "Mombasa", "Nyali", "Hypermarket", 3900, "2017-11-01"),
    ("S008", "Mavuno Mart Mombasa Town", "Mombasa", "Mombasa CBD", "Supermarket", 1600, "2015-04-01"),
    ("S009", "Mavuno Mart Thika", "Kiambu", "Thika", "Supermarket", 2000, "2018-03-01"),
    ("S010", "Mavuno Mart Ruiru", "Kiambu", "Ruiru", "Express", 800, "2021-09-01"),
    ("S011", "Mavuno Mart Nakuru Kenyatta Ave", "Nakuru", "Nakuru Town", "Hypermarket", 3600, "2016-08-01"),
    ("S012", "Mavuno Mart Naivasha", "Nakuru", "Naivasha", "Supermarket", 1500, "2020-07-01"),
    ("S013", "Mavuno Mart Kisumu Mega", "Kisumu", "Kisumu City", "Hypermarket", 3500, "2017-05-01"),
    ("S014", "Mavuno Mart Kondele", "Kisumu", "Kondele", "Express", 600, "2022-06-01"),
    ("S015", "Mavuno Mart Eldoret", "Uasin Gishu", "Eldoret", "Supermarket", 2200, "2018-10-01"),
    ("S016", "Mavuno Mart Machakos", "Machakos", "Machakos Town", "Supermarket", 1400, "2019-08-01"),
    ("S017", "Mavuno Mart Kakamega", "Kakamega", "Kakamega Town", "Supermarket", 1300, "2020-02-01"),
    ("S018", "Mavuno Mart Nyeri", "Nyeri", "Nyeri Town", "Supermarket", 1350, "2019-11-01"),
    ("S019", "Mavuno Mart Malindi", "Kilifi", "Malindi", "Express", 750, "2021-03-01"),
    ("S020", "Mavuno Mart Kitengela", "Kajiado", "Kitengela", "Supermarket", 1700, "2025-06-14"),
]
stores = pd.DataFrame(STORES, columns=["store_id", "store_name", "county", "town",
                                       "store_format", "size_sqm", "open_date"])
stores["open_date"] = pd.to_datetime(stores["open_date"])
NS = len(stores)
store_idx = {s: i for i, s in enumerate(stores.store_id)}
fmt_walkin = {"Hypermarket": 17.0, "Supermarket": 10.0, "Express": 6.0}
fmt_basket = {"Hypermarket": 1.2, "Supermarket": 1.0, "Express": 0.72}
fmt_price = {"Hypermarket": 0.99, "Supermarket": 1.00, "Express": 1.03}
store_open = np.array([[d >= od for d in DATES] for od in stores.open_date])  # NS x ND
nakuru = stores.county.eq("Nakuru").to_numpy()
COMPETITOR_DATE = pd.Timestamp("2026-02-01")

# ----------------------------------------------------------------------------- products
# (category, subcategory, name, base_price_KES_Oct2024, popularity, qty_profile)
P = [
    ("Staples", "Flour", "Maize Flour 2kg", 165, 9.0, "bulk"),
    ("Staples", "Flour", "Maize Flour 1kg", 88, 5.0, "bulk"),
    ("Staples", "Flour", "Wheat Flour Home Baking 2kg", 195, 4.5, "bulk"),
    ("Staples", "Flour", "Atta Mark 1 2kg", 210, 2.5, "bulk"),
    ("Staples", "Rice", "Pishori Rice 2kg", 390, 3.5, "bulk"),
    ("Staples", "Rice", "Long Grain Rice 1kg", 155, 3.0, "bulk"),
    ("Staples", "Sugar", "White Sugar 2kg", 330, 6.0, "bulk"),
    ("Staples", "Sugar", "White Sugar 1kg", 168, 5.0, "bulk"),
    ("Staples", "Cooking Oil", "Vegetable Cooking Oil 1L", 330, 5.5, "bulk"),
    ("Staples", "Cooking Oil", "Vegetable Cooking Oil 3L", 940, 2.5, "bulk"),
    ("Staples", "Cooking Oil", "Cooking Fat 500g", 210, 3.0, "bulk"),
    ("Staples", "Pulses", "Green Grams 1kg", 230, 1.5, "bulk"),
    ("Staples", "Pulses", "Dry Beans Rosecoco 1kg", 210, 2.0, "bulk"),
    ("Staples", "Pasta", "Spaghetti 400g", 110, 2.0, "bulk"),
    ("Staples", "Salt & Spices", "Table Salt 1kg", 45, 2.0, "bulk"),
    ("Staples", "Salt & Spices", "Royco Style Mchuzi Mix 200g", 95, 2.0, "bulk"),
    ("Fresh Produce", "Vegetables", "Tomatoes per kg", 120, 5.0, "bulk"),
    ("Fresh Produce", "Vegetables", "Onions per kg", 110, 4.5, "bulk"),
    ("Fresh Produce", "Vegetables", "Sukuma Wiki Bunch", 30, 4.0, "bulk"),
    ("Fresh Produce", "Vegetables", "Cabbage Head", 70, 2.5, "bulk"),
    ("Fresh Produce", "Vegetables", "Potatoes 2kg", 180, 3.0, "bulk"),
    ("Fresh Produce", "Fruit", "Bananas per kg", 90, 3.0, "bulk"),
    ("Fresh Produce", "Fruit", "Avocado each", 25, 2.0, "bulk"),
    ("Fresh Produce", "Fruit", "Mangoes per kg", 140, 1.5, "bulk"),
    ("Fresh Produce", "Fruit", "Oranges per kg", 160, 1.2, "bulk"),
    ("Fresh Produce", "Bakery", "White Bread 400g", 65, 8.0, "bulk"),
    ("Fresh Produce", "Bakery", "Brown Bread 600g", 90, 3.0, "single"),
    ("Fresh Produce", "Meat & Eggs", "Eggs Tray 30", 450, 3.0, "single"),
    ("Fresh Produce", "Meat & Eggs", "Beef Steak per kg", 750, 1.8, "single"),
    ("Fresh Produce", "Meat & Eggs", "Whole Chicken 1.2kg", 650, 1.8, "single"),
    ("Dairy", "Milk", "Fresh Milk 500ml", 65, 9.0, "bulk"),
    ("Dairy", "Milk", "Long Life Milk 500ml", 70, 4.0, "bulk"),
    ("Dairy", "Milk", "Mala Fermented Milk 500ml", 80, 2.0, "bulk"),
    ("Dairy", "Yoghurt", "Strawberry Yoghurt 500ml", 140, 2.5, "single"),
    ("Dairy", "Butter & Cheese", "Salted Butter 250g", 320, 1.5, "single"),
    ("Dairy", "Butter & Cheese", "Margarine 500g", 230, 2.5, "single"),
    ("Dairy", "Butter & Cheese", "Cheddar Cheese 200g", 420, 0.6, "single"),
    ("Beverages", "Tea & Coffee", "Kenya Tea Leaves 500g", 260, 4.0, "single"),
    ("Beverages", "Tea & Coffee", "Tea Bags 100s", 220, 2.5, "single"),
    ("Beverages", "Tea & Coffee", "Instant Coffee 100g", 480, 1.2, "single"),
    ("Beverages", "Soft Drinks", "Soda 2L", 190, 4.0, "bulk"),
    ("Beverages", "Soft Drinks", "Soda 500ml", 80, 4.5, "bulk"),
    ("Beverages", "Soft Drinks", "Mango Juice 1L", 210, 2.5, "single"),
    ("Beverages", "Water", "Drinking Water 1.5L", 80, 3.5, "bulk"),
    ("Beverages", "Water", "Drinking Water 10L", 330, 1.2, "single"),
    ("Beverages", "Snacks", "Potato Crisps 150g", 160, 2.0, "single"),
    ("Beverages", "Snacks", "Biscuits Assorted 500g", 230, 2.5, "single"),
    ("Beverages", "Snacks", "Roasted Peanuts 200g", 120, 1.5, "single"),
    ("Beverages", "Snacks", "Chocolate Bar 80g", 150, 1.2, "single"),
    ("Household", "Cleaning", "Bar Soap 1kg", 230, 4.0, "single"),
    ("Household", "Cleaning", "Washing Powder 1kg", 320, 3.5, "single"),
    ("Household", "Cleaning", "Dishwashing Liquid 750ml", 210, 2.5, "single"),
    ("Household", "Cleaning", "Bleach 1L", 180, 1.5, "single"),
    ("Household", "Cleaning", "Toilet Cleaner 500ml", 260, 1.2, "single"),
    ("Household", "Paper", "Toilet Paper 10 Pack", 420, 3.5, "single"),
    ("Household", "Paper", "Serviettes 100s", 120, 1.0, "single"),
    ("Household", "Fuel", "Charcoal 4kg Bag", 380, 1.5, "single"),
    ("Household", "Fuel", "Gas Refill 6kg", 1350, 0.9, "single"),
    ("Household", "Fuel", "Matches 10 Pack", 50, 1.5, "single"),
    ("Household", "Storage", "Plastic Bucket 20L", 450, 0.5, "single"),
    ("Household", "Storage", "Storage Containers Set", 680, 0.4, "single"),
    ("Personal Care", "Oral Care", "Toothpaste 140g", 210, 2.8, "single"),
    ("Personal Care", "Oral Care", "Toothbrush Twin Pack", 150, 1.2, "single"),
    ("Personal Care", "Skin Care", "Petroleum Jelly 250ml", 180, 2.0, "single"),
    ("Personal Care", "Skin Care", "Body Lotion 400ml", 450, 1.8, "single"),
    ("Personal Care", "Hair Care", "Shampoo 400ml", 420, 1.2, "single"),
    ("Personal Care", "Hair Care", "Hair Food 250g", 190, 1.0, "single"),
    ("Personal Care", "Hygiene", "Sanitary Pads 10s", 140, 2.2, "single"),
    ("Personal Care", "Hygiene", "Roll-on Deodorant 50ml", 330, 1.2, "single"),
    ("Personal Care", "Hygiene", "Bathing Soap 3 Pack", 240, 2.0, "single"),
    ("Personal Care", "Hygiene", "Hand Sanitizer 500ml", 290, 0.6, "single"),
    ("Baby & Kids", "Diapers", "Baby Diapers 40s", 1250, 1.3, "single"),
    ("Baby & Kids", "Diapers", "Baby Wipes 80s", 280, 1.4, "single"),
    ("Baby & Kids", "Baby Food", "Infant Cereal 400g", 520, 0.8, "single"),
    ("Baby & Kids", "Baby Food", "Infant Formula 400g", 1650, 0.6, "single"),
    ("Baby & Kids", "Baby Care", "Baby Jelly 250ml", 230, 0.7, "single"),
    ("Stationery & School", "Books", "Exercise Books A5 10 Pack", 380, 0.9, "school"),
    ("Stationery & School", "Books", "Counter Book 4 Quire", 280, 0.4, "single"),
    ("Stationery & School", "Writing", "Ball Pens 10 Pack", 190, 0.8, "school"),
    ("Stationery & School", "Writing", "HB Pencils 12 Pack", 150, 0.6, "school"),
    ("Stationery & School", "Writing", "Mathematical Set", 260, 0.4, "single"),
    ("Stationery & School", "Bags", "School Bag", 1450, 0.25, "single"),
    ("Stationery & School", "Uniform", "School Socks 3 Pack", 350, 0.35, "school"),
    ("Electronics & Phone", "Phone Accessories", "Phone Charger USB-C", 650, 0.6, "single"),
    ("Electronics & Phone", "Phone Accessories", "Earphones Wired", 450, 0.4, "single"),
    ("Electronics & Phone", "Airtime", "Airtime Voucher KES 100", 100, 2.5, "bulk"),
    ("Electronics & Phone", "Lighting", "LED Bulb 9W", 220, 0.7, "single"),
    ("Electronics & Phone", "Batteries", "AA Batteries 4 Pack", 240, 0.6, "single"),
    ("Electronics & Phone", "Small Appliances", "Electric Kettle 1.7L", 2400, 0.12, "single"),
    ("Electronics & Phone", "Small Appliances", "Extension Cable 4-Way", 1150, 0.15, "single"),
    ("Electronics & Phone", "Small Appliances", "Solar Lantern", 1900, 0.12, "single"),
]
products = pd.DataFrame(P, columns=["category", "subcategory", "product_name",
                                    "base_price", "popularity", "qty_profile"])
products.insert(0, "product_id", [f"P{i+1:04d}" for i in range(len(products))])
tiers = rng.choice(["Private Label", "Standard", "Premium"], len(products), p=[.25, .55, .20])
products["brand_tier"] = tiers
NP = len(products)
cat_of = products.category.to_numpy()
FOOD = {"Staples", "Fresh Produce", "Dairy", "Beverages"}

# Monthly seasonality multipliers by category (applied to product choice weights).
def cat_season(cat, month):
    s = 1.0
    if cat == "Stationery & School":
        s = {1: 3.2, 2: 1.2, 4: 1.3, 5: 1.9, 8: 1.5, 9: 1.4, 12: 0.8}.get(month, 0.7)
    elif cat == "Beverages":
        s = {12: 1.55, 1: 0.9, 4: 1.1}.get(month, 1.0)
    elif cat == "Electronics & Phone":
        s = {12: 1.6, 11: 1.15}.get(month, 1.0)
    elif cat == "Household":
        s = {12: 1.2}.get(month, 1.0)
    elif cat == "Fresh Produce":
        s = {12: 1.15, 4: 1.05}.get(month, 1.0)
    return s

months = DATES.to_period("M")
uniq_months = months.unique()
month_of_day = np.array([uniq_months.get_loc(m) for m in months])

# Product choice probability per month (NM x NP)
W = np.array([[products.popularity[j] * cat_season(cat_of[j], m.month) for j in range(NP)]
              for m in uniq_months])
W = W / W.sum(axis=1, keepdims=True)
Wcum = W.cumsum(axis=1)

# ----------------------------------------------------------------------------- prices
infl = pd.read_csv(EXTERNAL / "kenya_inflation_monthly.csv")
infl["period"] = pd.PeriodIndex.from_fields(year=infl.year, month=infl.month, freq="M")
infl = infl.set_index("period")
# Monthly price growth implied by 12-month inflation: (1+yoy)^(1/12)-1. Food moves 1.25x
# the headline rate, non-food 0.7x (KNBS reports food inflation running above headline).
cum_food, cum_non = [], []
f = n = 1.0
for m in uniq_months:
    g = (1 + infl.loc[m, "inflation_12m_pct"] / 100) ** (1 / 12) - 1
    f *= 1 + 1.25 * g
    n *= 1 + 0.70 * g
    cum_food.append(f)
    cum_non.append(n)
cum_food, cum_non = np.array(cum_food), np.array(cum_non)
# extra fuel/food shock from April 2026 for staples (mirrors the 2026 inflation jump)
shock = np.array([1.0 + (0.05 if m >= pd.Period("2026-04", "M") else 0.0) for m in uniq_months])

def round_price(p):
    return np.where(p >= 100, np.round(p / 5) * 5, np.round(p))

price = np.zeros((len(uniq_months), NS, NP))
for j in range(NP):
    cum = cum_food if cat_of[j] in FOOD else cum_non
    sh = shock if cat_of[j] == "Staples" else 1.0
    noise = 1 + rng.normal(0, 0.01, len(uniq_months))
    for s in range(NS):
        price[:, s, j] = round_price(products.base_price[j] * cum * sh * noise
                                     * fmt_price[stores.store_format[s]])

# ----------------------------------------------------------------------------- calendar
hol = pd.read_csv(EXTERNAL / "kenya_public_holidays.csv", parse_dates=["date"])
hol = hol[hol.type != "reference"]
hol_set = set(hol.date)
eve_set = {d - pd.Timedelta(days=1) for d in hol_set}
dow_f = np.array([0.86, 0.84, 0.88, 0.95, 1.12, 1.38, 1.02])
mon_f = {1: 0.84, 2: 0.9, 3: 0.97, 4: 1.04, 5: 0.98, 6: 0.99, 7: 1.0,
         8: 1.05, 9: 0.98, 10: 1.0, 11: 1.03, 12: 1.32}

def day_factor(d):
    x = dow_f[d.dayofweek] * mon_f[d.month]
    if d.day >= 25 or d.day <= 3:
        x *= 1.17          # payday window
    elif 14 <= d.day <= 20:
        x *= 0.92          # mid-month squeeze
    if d in hol_set:
        x *= 0.78
    if d in eve_set:
        x *= 1.25
    if d.month == 12 and d.day in (23, 24):
        x *= 1.45
    if d.month == 12 and d.day == 25:
        x *= 0.45
    return x

DF = np.array([day_factor(d) for d in DATES])
payday = np.array([(d.day >= 25 or d.day <= 3) for d in DATES])
weekend = np.array([d.dayofweek >= 5 for d in DATES])
trend = np.linspace(1.0, 1.12, ND)  # modest organic growth

# ----------------------------------------------------------------------------- promotions
promos = pd.DataFrame([
    # id, name, start, end, pct, scope_type, scope_value, stores, true unit uplift
    ("PR001", "Festive Drinks & Snacks 2024", "2024-12-09", "2024-12-31", 10, "category", "Beverages", "ALL", 0.20),
    ("PR002", "Back-to-School 2025", "2024-12-30", "2025-01-19", 10, "category", "Stationery & School", "ALL", 0.30),
    ("PR003", "Easter Dairy & Bakery", "2025-04-14", "2025-04-21", 8, "subcategory", "Milk|Bakery", "ALL", 0.15),
    ("PR004", "Personal Care Week", "2025-07-07", "2025-07-20", 5, "category", "Personal Care", "TREAT_A", 0.0),
    ("PR005", "Mid-Month Unga Saver", "2025-11-14", "2025-11-20", 8, "subcategory", "Flour", "ALL", 0.25),
    ("PR006", "Festive Drinks & Snacks 2025", "2025-12-08", "2025-12-31", 10, "category", "Beverages", "ALL", 0.22),
    ("PR007", "Back-to-School 2026", "2025-12-29", "2026-01-18", 10, "category", "Stationery & School", "ALL", 0.30),
    ("PR008", "Cooking Oil Price Drop (store test)", "2026-03-02", "2026-03-22", 15, "subcategory", "Cooking Oil", "TREAT_B", 0.35),
    ("PR009", "Household Cleaning Bonanza", "2026-06-08", "2026-06-21", 7, "subcategory", "Cleaning", "ALL", 0.12),
], columns=["promo_id", "promo_name", "start_date", "end_date", "discount_pct",
            "scope_type", "scope_value", "store_scope", "_true_uplift"])
promos["start_date"] = pd.to_datetime(promos.start_date)
promos["end_date"] = pd.to_datetime(promos.end_date)
# Randomised store assignment for the two store-level tests (open stores only)
eligible = [s for s in stores.store_id if s != "S020"]
treat_a = sorted(str(s) for s in rng.choice(eligible, 9, replace=False))
treat_b = sorted(str(s) for s in rng.choice(eligible, 10, replace=False))
store_lists = {"ALL": "ALL", "TREAT_A": "|".join(treat_a), "TREAT_B": "|".join(treat_b)}
promos["store_ids"] = promos.store_scope.map(store_lists)

def promo_products(row):
    vals = row.scope_value.split("|")
    col = row.scope_type
    return products.index[products[col].isin(vals)].to_numpy()

# ----------------------------------------------------------------------------- customers
NC = 6000
seg = rng.choice(["Loyal", "Regular", "Occasional", "Deal Seeker"], NC, p=[.18, .35, .32, .15])
seg_rate = {"Loyal": 1.05, "Regular": 0.42, "Occasional": 0.15, "Deal Seeker": 0.27}
rate = np.array([seg_rate[s] for s in seg]) * rng.lognormal(0, 0.35, NC)
# signup: 62% existing members, the rest join during the period (acquisition growing)
existing = rng.random(NC) < 0.62
signup = np.where(
    existing,
    pd.Timestamp("2021-01-01").value + rng.random(NC) * (pd.Timestamp(START_DATE).value - pd.Timestamp("2021-01-01").value),
    pd.Timestamp(START_DATE).value + (rng.random(NC) ** 0.8) * (pd.Timestamp("2026-08-31").value - pd.Timestamp(START_DATE).value),
)
signup = pd.to_datetime(signup).normalize()
size_w = stores.size_sqm.to_numpy() ** 0.8
home = np.empty(NC, dtype=int)
for i in range(NC):
    ok = (stores.open_date <= signup[i]).to_numpy()
    w = size_w * ok
    home[i] = rng.choice(NS, p=w / w.sum())
gender = rng.choice(["F", "M"], NC, p=[.58, .42])
birth_year = np.clip(np.round(rng.normal(1988, 10, NC)), 1950, 2007).astype(int)
pay_methods = np.array(["M-Pesa", "Cash", "Card", "Airtel Money"])
cust_pref = rng.choice(4, NC, p=[.60, .22, .15, .03])

# Churn: exponential time-to-churn with segment-specific hazard (per day).
seg_haz = {"Loyal": 1 / 2200, "Regular": 1 / 900, "Occasional": 1 / 420, "Deal Seeker": 1 / 520}
haz = np.array([seg_haz[s] for s in seg])
start_idx = np.maximum(0, (signup - pd.Timestamp(START_DATE)).days.to_numpy())
churn_idx = np.full(NC, 10**6)
for i in range(NC):
    t = start_idx[i]
    while t < ND:
        h = haz[i]
        if nakuru[home[i]] and DATES[t] >= COMPETITOR_DATE:
            h *= 2.6                                   # competitor effect
        if DATES[t] >= pd.Timestamp("2026-04-01") and seg[i] in ("Occasional", "Deal Seeker"):
            h *= 1.35                                  # cost-of-living squeeze
        step = 30
        if rng.random() < 1 - np.exp(-h * step):
            churn_idx[i] = t + rng.integers(0, step)
            break
        t += step

# ----------------------------------------------------------------------------- loyalty visits
day_ix = np.arange(ND)
P_visit = (rate[:, None] / 7.0) * DF[None, :]
active = (day_ix[None, :] >= start_idx[:, None]) & (day_ix[None, :] < churn_idx[:, None])
# "drifting": visit rate decays over the 75 days before churn
to_churn = churn_idx[:, None] - day_ix[None, :]
decay = np.where((to_churn > 0) & (to_churn <= 75), 0.35 + 0.65 * (to_churn / 75), 1.0)
P_visit = np.clip(P_visit * decay * active, 0, 0.9)
vis_c, vis_d = np.nonzero(rng.random(P_visit.shape) < P_visit)
del P_visit, active, to_churn, decay

# store visited: 86% home store, else another store in same county, else any open store
v_store = home[vis_c].copy()
alt = rng.random(len(vis_c)) > 0.86
counties = stores.county.to_numpy()
for k in np.nonzero(alt)[0]:
    d = vis_d[k]
    same = np.nonzero((counties == counties[home[vis_c[k]]]) & store_open[:, d])[0]
    pool = same if len(same) > 1 and rng.random() < 0.7 else np.nonzero(store_open[:, d])[0]
    v_store[k] = rng.choice(pool)
ok = store_open[v_store, vis_d]
vis_c, vis_d, v_store = vis_c[ok], vis_d[ok], v_store[ok]

# ----------------------------------------------------------------------------- walk-ins
w_rows = []
for s in range(NS):
    base = fmt_walkin[stores.store_format[s]]
    lam = base * DF * trend * store_open[s]
    if nakuru[s]:
        lam = lam * np.where(DATES >= COMPETITOR_DATE, 0.78, 1.0)
    if stores.store_id[s] == "S020":            # new store ramps up over 5 months
        ramp = np.clip((DATES - stores.open_date[s]).days / 150, 0.25, 1.0)
        lam = lam * ramp
    cnt = rng.poisson(lam)
    d = np.repeat(day_ix, cnt)
    w_rows.append(np.column_stack([np.full(len(d), s), d]))
w = np.vstack(w_rows)

# ----------------------------------------------------------------------------- transactions
tx_store = np.concatenate([v_store, w[:, 0]])
tx_day = np.concatenate([vis_d, w[:, 1]])
tx_cust = np.concatenate([vis_c, np.full(len(w), -1)])
order = np.lexsort((rng.random(len(tx_day)), tx_day))
tx_store, tx_day, tx_cust = tx_store[order], tx_day[order], tx_cust[order]
NT = len(tx_day)

# time of day: lunchtime and evening peaks; Saturday mornings busier
hours = np.arange(7, 22)
hw_week = np.array([2, 4, 5, 6, 8, 9, 7, 6, 6, 8, 11, 12, 9, 5, 2], float)
hw_sat = np.array([3, 6, 9, 11, 11, 10, 9, 8, 7, 7, 7, 6, 4, 2, 1], float)
sat = np.array([DATES[d].dayofweek >= 5 for d in tx_day])
hr = np.where(sat, rng.choice(hours, NT, p=hw_sat / hw_sat.sum()),
              rng.choice(hours, NT, p=hw_week / hw_week.sum()))
minute = rng.integers(0, 60, NT)
second = rng.integers(0, 60, NT)
ts = (DATES[tx_day] + pd.to_timedelta(hr, "h") + pd.to_timedelta(minute, "m")
      + pd.to_timedelta(second, "s"))

# payment method: M-Pesa share rises, cash falls over the period
frac = tx_day / ND
p_mpesa = 0.56 + 0.10 * frac
p_cash = 0.27 - 0.10 * frac
p_card = np.full(NT, 0.14)
p_air = 1 - p_mpesa - p_cash - p_card
U = rng.random(NT)
date_pay = np.where(U < p_mpesa, 0, np.where(U < p_mpesa + p_cash, 1,
                    np.where(U < p_mpesa + p_cash + p_card, 2, 3)))
is_member = tx_cust >= 0
use_pref = is_member & (rng.random(NT) < 0.75)
pay = np.where(use_pref, cust_pref[np.maximum(tx_cust, 0)], date_pay)
# walk-ins use a little more cash
walk_cash = (~is_member) & (rng.random(NT) < 0.08)
pay = np.where(walk_cash, 1, pay)

# basket size (number of distinct lines)
seg_basket = {"Loyal": 1.25, "Regular": 1.05, "Occasional": 0.95, "Deal Seeker": 1.1}
segm = np.where(is_member, [seg_basket[s] for s in seg[np.maximum(tx_cust, 0)]], 0.85)
lam = (1.55 * segm
       * np.array([fmt_basket[f] for f in stores.store_format.to_numpy()[tx_store]])
       * np.where(payday[tx_day], 1.15, 1.0) * np.where(weekend[tx_day], 1.12, 1.0)
       * np.where(pay == 2, 1.35, 1.0)
       * np.where(np.array([DATES[d].month for d in tx_day]) == 12, 1.18, 1.0))
n_lines = 1 + rng.poisson(lam)
NL = n_lines.sum()
line_tx = np.repeat(np.arange(NT), n_lines)
line_m = month_of_day[tx_day[line_tx]]
u = rng.random(NL)
line_p = np.empty(NL, dtype=int)
for m in range(len(uniq_months)):
    sel = line_m == m
    line_p[sel] = np.minimum(np.searchsorted(Wcum[m], u[sel]), NP - 1)

# complementary products: buying A makes buying B more likely (gives real basket affinity)
pid = {n: i for i, n in enumerate(products.product_name)}
PAIRS = [("Maize Flour 2kg", "Sukuma Wiki Bunch", 0.25), ("White Bread 400g", "Fresh Milk 500ml", 0.30),
         ("Kenya Tea Leaves 500g", "White Sugar 1kg", 0.30), ("Baby Diapers 40s", "Baby Wipes 80s", 0.40),
         ("Spaghetti 400g", "Tomatoes per kg", 0.25), ("Vegetable Cooking Oil 1L", "Onions per kg", 0.15),
         ("Exercise Books A5 10 Pack", "Ball Pens 10 Pack", 0.45)]
add_tx, add_p = [], []
for a, b, pr_ in PAIRS:
    hit = line_tx[(line_p == pid[a]) & (rng.random(len(line_p)) < pr_)]
    add_tx.append(hit)
    add_p.append(np.full(len(hit), pid[b]))
line_tx = np.concatenate([line_tx] + add_tx)
line_p = np.concatenate([line_p] + add_p)

# promotion uplift: extra promo-product lines for transactions in promo store-days
base_rate = np.bincount(line_p, minlength=NP) / NT   # lines per transaction, by product
extra_tx, extra_p, line_promo_tag = [], [], {}
tx_date = DATES[tx_day]
deal = is_member & (seg[np.maximum(tx_cust, 0)] == "Deal Seeker")
for _, pr in promos.iterrows():
    prods = promo_products(pr)
    in_store = np.ones(NS, bool) if pr.store_ids == "ALL" else stores.store_id.isin(pr.store_ids.split("|")).to_numpy()
    active_tx = np.nonzero(in_store[tx_store] & (tx_date >= pr.start_date) & (tx_date <= pr.end_date))[0]
    if pr._true_uplift <= 0 or len(active_tx) == 0:
        continue
    for j in prods:
        mult = np.where(deal[active_tx], 2.0, 1.0)
        q = np.clip(pr._true_uplift * base_rate[j] * cat_season(cat_of[j], tx_date[active_tx[0]].month) * mult, 0, 0.9)
        hit = active_tx[rng.random(len(active_tx)) < q]
        extra_tx.append(hit)
        extra_p.append(np.full(len(hit), j))
line_tx = np.concatenate([line_tx] + extra_tx)
line_p = np.concatenate([line_p] + extra_p)

items = pd.DataFrame({"tx": line_tx, "p": line_p})
# collapse duplicate product picks within a basket into quantity
items = items.groupby(["tx", "p"], as_index=False).size().rename(columns={"size": "k"})
qp = products.qty_profile.to_numpy()[items.p]
r = rng.random(len(items))
q_bulk = np.where(r < .70, 1, np.where(r < .90, 2, np.where(r < .97, 3, 4 + rng.integers(0, 3, len(items)))))
q_single = np.where(r < .87, 1, np.where(r < .97, 2, 3))
q_school = np.where(r < .55, 1, np.where(r < .80, 2, np.where(r < .93, 3, 4 + rng.integers(0, 4, len(items)))))
items["quantity"] = np.select([qp == "bulk", qp == "school"], [q_bulk, q_school], q_single) + items.k - 1

it_day = tx_day[items.tx]
it_store = tx_store[items.tx]
items["unit_price"] = price[month_of_day[it_day], it_store, items.p]

# discounts for lines on promotion
items["promo_id"] = ""
items["discount_amount"] = 0.0
it_date = DATES[it_day]
for _, pr in promos.iterrows():
    prods = set(promo_products(pr))
    in_store = np.ones(NS, bool) if pr.store_ids == "ALL" else stores.store_id.isin(pr.store_ids.split("|")).to_numpy()
    m = (items.p.isin(prods).to_numpy() & in_store[it_store]
         & (it_date >= pr.start_date) & (it_date <= pr.end_date))
    items.loc[m, "promo_id"] = pr.promo_id
    items.loc[m, "discount_amount"] = np.round(items.loc[m, "unit_price"] * items.loc[m, "quantity"] * pr.discount_pct / 100, 2)

# returns: 0.3% of lines are refunded later as negative-quantity lines
items = items.sort_values(["tx", "p"]).reset_index(drop=True)
items["line_no"] = items.groupby("tx").cumcount() + 1
ret = items.sample(frac=0.003, random_state=SEED).copy()
ret["quantity"] = -ret["quantity"]
ret["discount_amount"] = -ret["discount_amount"]
ret["line_no"] = 90 + ret.groupby("tx").cumcount()
items = pd.concat([items, ret]).sort_values(["tx", "line_no"]).reset_index(drop=True)

tx_ids = np.array([f"T{i+1:07d}" for i in range(NT)])
cust_ids = np.array([f"C{i+1:05d}" for i in range(NC)])
items["line_value"] = items.quantity * items.unit_price - items.discount_amount
tx_total = items.groupby("tx").line_value.sum().reindex(range(NT), fill_value=0).to_numpy()

transactions = pd.DataFrame({
    "transaction_id": tx_ids,
    "transaction_datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
    "store_id": stores.store_id.to_numpy()[tx_store],
    "till_no": rng.integers(1, 9, NT),
    "customer_id": np.where(is_member, cust_ids[np.maximum(tx_cust, 0)], ""),
    "payment_method": pay_methods[pay],
    "total_amount": np.round(tx_total, 2),
})
items_out = pd.DataFrame({
    "transaction_id": tx_ids[items.tx],
    "line_no": items.line_no,
    "product_id": products.product_id.to_numpy()[items.p],
    "quantity": items.quantity,
    "unit_price": items.unit_price,
    "discount_amount": items.discount_amount,
    "promo_id": items.promo_id,
})
customers = pd.DataFrame({
    "customer_id": cust_ids, "gender": gender, "birth_year": birth_year,
    "signup_date": signup.strftime("%Y-%m-%d"),
    "home_store_id": stores.store_id.to_numpy()[home],
})

# ----------------------------------------------------------------------------- inject data-quality problems
def messy(series, frac, fn):
    idx = series.sample(frac=frac, random_state=int(rng.integers(1e9))).index
    series = series.copy()
    series.loc[idx] = series.loc[idx].map(fn)
    return series

pm_variants = {"M-Pesa": ["MPESA", "mpesa", "M-PESA ", "Mpesa", "M PESA"],
               "Cash": ["CASH", "cash ", "Csh"], "Card": ["CARD", "Visa/Mastercard", "card"],
               "Airtel Money": ["AIRTEL MONEY", "Airtel"]}
transactions["payment_method"] = messy(transactions.payment_method, 0.06,
                                       lambda v: rng.choice(pm_variants[v]))
transactions.loc[transactions.sample(frac=0.008, random_state=1).index, "payment_method"] = np.nan
transactions["transaction_datetime"] = messy(
    transactions.transaction_datetime, 0.02,
    lambda v: pd.Timestamp(v).strftime("%d/%m/%Y %H:%M"))
transactions.loc[transactions.sample(frac=0.004, random_state=2).index, "total_amount"] = np.nan
transactions["total_amount"] = transactions.total_amount.astype(object)
transactions["total_amount"] = messy(transactions.total_amount, 0.015,
                                     lambda v: v if pd.isna(v) else f"KES {v:,.2f}")
transactions["store_id"] = messy(transactions.store_id, 0.003, lambda v: v.lower() + " ")
# test / training transactions from the POS vendor and a few bad clock dates
junk = transactions.sample(25, random_state=3).copy()
junk["transaction_id"] = [f"TEST{i:03d}" for i in range(25)]
junk["store_id"] = "S999"
fut = transactions.sample(12, random_state=4).copy()
fut["transaction_id"] = [f"T9{i:06d}" for i in range(12)]
fut["transaction_datetime"] = "2031-01-01 00:00:00"
dups = transactions.sample(frac=0.004, random_state=5)
transactions = pd.concat([transactions, junk, fut, dups]).sample(frac=1, random_state=6).reset_index(drop=True)

items_out["unit_price"] = items_out.unit_price.astype(float)
items_out.loc[items_out.sample(frac=0.006, random_state=7).index, "unit_price"] = np.nan
out_idx = items_out[items_out.quantity > 0].sample(60, random_state=8).index
items_out.loc[out_idx, "quantity"] = rng.choice([99, 120, 999, 1000], 60)  # keying errors
items_out = pd.concat([items_out, items_out.sample(frac=0.002, random_state=9)]).reset_index(drop=True)

customers["gender"] = messy(customers.gender, 0.05, lambda v: {"F": rng.choice(["female", "f", "F "]), "M": rng.choice(["male", "m", "M "])}[v])
customers.loc[customers.sample(frac=0.03, random_state=10).index, "gender"] = np.nan
customers.loc[customers.sample(frac=0.01, random_state=11).index, "birth_year"] = rng.choice([1900, 2020, 2024], 60)
customers = pd.concat([customers, customers.sample(30, random_state=12)])  # duplicate sign-ups

prod_out = products.drop(columns=["popularity", "qty_profile"]).copy()
prod_out.loc[prod_out.sample(4, random_state=13).index, "category"] = np.nan
stores_out = stores.copy()
stores_out["open_date"] = stores_out.open_date.dt.strftime("%Y-%m-%d")
stores_out["county"] = messy(stores_out.county, 0.25, lambda v: rng.choice([v.upper(), v.lower(), " " + v]))
promos_out = promos.drop(columns=["_true_uplift", "store_scope"]).copy()
promos_out["start_date"] = promos_out.start_date.dt.strftime("%Y-%m-%d")
promos_out["end_date"] = promos_out.end_date.dt.strftime("%Y-%m-%d")

transactions.to_csv(RAW / "transactions.csv", index=False)
items_out.to_csv(RAW / "transaction_items.csv", index=False)
customers.to_csv(RAW / "customers.csv", index=False)
prod_out.to_csv(RAW / "products.csv", index=False)
stores_out.to_csv(RAW / "stores.csv", index=False)
promos_out.to_csv(RAW / "promotions.csv", index=False)

# Ground truth kept separately (never used for modelling - only to sanity-check findings)
pd.DataFrame({"customer_id": cust_ids, "segment_true": seg,
              "churn_date_true": [DATES[c].strftime("%Y-%m-%d") if c < ND else "" for c in churn_idx]}
             ).to_csv(RAW / "_ground_truth_customers.csv", index=False)

print(f"stores {NS} | products {NP} | customers {NC} | transactions {NT:,} | lines {len(items_out):,}")
print("PR004 (personal care) stores:", treat_a)
print("PR008 (cooking oil) stores:", treat_b)
