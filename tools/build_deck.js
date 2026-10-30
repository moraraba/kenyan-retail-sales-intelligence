// Builds docs/presentation/Mavuno_Mart_Capstone_Presentation.pptx from deck_data.json + reports/figures.
// Run:  python tools/deck_data.py && node tools/build_deck.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "docs/presentation/deck_data.json"), "utf8"));
const FIG = (f) => path.join(ROOT, "reports/figures", f);
const OUT = path.join(ROOT, "docs/presentation/Mavuno_Mart_Capstone_Presentation.pptx");

// "Mavuno" means harvest: deep maize-field green, harvest gold, warm cream.
const COL = { green: "1F4D3A", green2: "2F6B52", gold: "E3A81F", cream: "F7F3EA", ink: "1B1B1B",
              mute: "5E5B53", line: "D9D3C4", white: "FFFFFF", blue: "2A78D6", orange: "EB6834", aqua: "1BAF7A" };
const HEAD = "Georgia", BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.author = "Capstone student";
pres.title = "Mavuno Mart - Customer and Sales Intelligence";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

pres.defineSlideMaster({
  title: "CONTENT", background: { color: COL.cream },
  objects: [
    { rect: { x: 0.6, y: 7.0, w: 12.13, h: 0.01, fill: { color: COL.line } } },
    { text: { text: "Mavuno Mart  |  Customer & Sales Intelligence capstone", options:
      { x: 0.6, y: 7.05, w: 8, h: 0.3, fontFace: BODY, fontSize: 9, color: COL.mute } } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontFace: BODY, fontSize: 9, color: COL.mute, align: "right" },
});
pres.defineSlideMaster({ title: "DARK", background: { color: COL.green } });

const fmt = (n, d = 0) => Number(n).toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d });

function title(slide, kicker, headline) {
  slide.addText(kicker.toUpperCase(), { x: 0.6, y: 0.35, w: 12, h: 0.3, fontFace: BODY, fontSize: 11, bold: true,
    color: COL.gold, charSpacing: 2, isTextBox: true, margin: 0 });
  slide.addText(headline, { x: 0.6, y: 0.65, w: 12.1, h: 0.9, fontFace: HEAD, fontSize: 26, color: COL.green,
    isTextBox: true, margin: 0, valign: "top" });
}
function stat(slide, x, y, w, big, label, color = COL.green) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.35, fill: { color: COL.white },
    line: { color: COL.line, width: 0.75 }, rectRadius: 0.08 });
  slide.addText(big, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true,
    color, isTextBox: true, margin: 0 });
  slide.addText(label, { x: x + 0.2, y: y + 0.8, w: w - 0.4, h: 0.5, fontFace: BODY, fontSize: 11.5, color: COL.mute,
    isTextBox: true, margin: 0, valign: "top" });
}
function bullets(slide, items, x, y, w, h, size = 14) {
  slide.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0" }, breakLine: i < items.length - 1,
    paraSpaceAfter: 8 } })), { x, y, w, h, fontFace: BODY, fontSize: size, color: COL.ink, valign: "top",
    isTextBox: true });
}
const chartBase = { catAxisLabelColor: COL.mute, valAxisLabelColor: COL.mute, catAxisLabelFontFace: BODY,
  valAxisLabelFontFace: BODY, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, valGridLine: { color: "E6E1D6", size: 0.5 },
  catGridLine: { style: "none" }, titleFontFace: BODY, titleColor: COL.ink, titleFontSize: 12, showTitle: true,
  legendFontFace: BODY, legendFontSize: 10, legendColor: COL.mute };

// 1 ---------------------------------------------------------------- title
let s = pres.addSlide({ masterName: "DARK" });
s.addShape(pres.shapes.OVAL, { x: 9.3, y: -1.2, w: 5.5, h: 5.5, fill: { color: COL.green2 }, line: { type: "none" } });
s.addShape(pres.shapes.OVAL, { x: 10.6, y: 4.3, w: 3.6, h: 3.6, fill: { color: COL.gold, transparency: 15 }, line: { type: "none" } });
s.addText("DATA SCIENCE & ANALYTICS CAPSTONE", { x: 0.8, y: 1.6, w: 9, h: 0.4, fontFace: BODY, fontSize: 13,
  bold: true, color: COL.gold, charSpacing: 3, isTextBox: true, margin: 0 });
s.addText("Customer and Sales Intelligence\nfor a Kenyan Retailer", { x: 0.8, y: 2.1, w: 9.5, h: 1.9,
  fontFace: HEAD, fontSize: 40, color: COL.white, isTextBox: true, margin: 0 });
s.addText("Who buys what, where and when - which customers are drifting - and what to expect next month",
  { x: 0.8, y: 4.15, w: 8.8, h: 0.8, fontFace: BODY, fontSize: 16, color: "D8E3DC", isTextBox: true, margin: 0 });
s.addText("[Your name]  |  [Programme]  |  October 2026", { x: 0.8, y: 6.3, w: 8, h: 0.4, fontFace: BODY,
  fontSize: 13, color: COL.white, isTextBox: true, margin: 0 });
s.addNotes("Introduce the client: Mavuno Mart, a fictional but realistic 20-store Kenyan chain. Explain that the sales data is generated (confidential in real life) while inflation, census and holiday data are real public sources. Today: the questions, the evidence, two models, and five actions.");

// 2 ---------------------------------------------------------------- answers first
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Executive summary", "Six questions from management - and what the data says");
const qa = [
  ["Are we growing?", `Revenue +${D.growth_nominal}%, but only +${D.growth_real}% after inflation.`],
  ["When do people buy?", `Payday days +${D.payday_lift}% revenue; December +${D.dec_vs_avg}% vs an average month.`],
  ["Where is revenue made?", `Express stores earn the most per sq m (KES ${fmt(D.fmt_rev_per_sqm.Express)} vs ${fmt(D.fmt_rev_per_sqm.Hypermarket)} for hypermarkets).`],
  ["Did promotions work?", "Cooking-oil test: +66 pp units (p < 0.001) but lost margin. Personal care: no effect."],
  ["Who is drifting away?", `Nakuru members lapse at ${fmt(100 * (D.nakuru.effect + 0.158))}% vs 16% elsewhere; churn model AUC ${D.churn["Logistic regression"].ROC_AUC}.`],
  ["What about October?", `Forecast ${fmt(D.forecast_total.forecast_units)} units (KES ${fmt(D.forecast_total.forecast_revenue / 1e6, 1)}M), +${fmt(D.forecast_total["vs_oct_2025_%"])}% on last October.`],
];
qa.forEach(([q, a], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.6 + col * 6.15, y = 1.75 + row * 1.68;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 1.5, fill: { color: COL.white },
    line: { color: COL.line, width: 0.75 }, rectRadius: 0.06 });
  s.addShape(pres.shapes.OVAL, { x: x + 0.22, y: y + 0.28, w: 0.5, h: 0.5, fill: { color: COL.gold }, line: { type: "none" } });
  s.addText(String(i + 1), { x: x + 0.22, y: y + 0.28, w: 0.5, h: 0.5, align: "center", valign: "middle",
    fontFace: HEAD, fontSize: 16, bold: true, color: COL.green, isTextBox: true, margin: 0 });
  s.addText(q, { x: x + 0.9, y: y + 0.2, w: 4.85, h: 0.4, fontFace: HEAD, fontSize: 15, bold: true, color: COL.green,
    isTextBox: true, margin: 0 });
  s.addText(a, { x: x + 0.9, y: y + 0.62, w: 4.85, h: 0.8, fontFace: BODY, fontSize: 13, color: COL.ink,
    isTextBox: true, margin: 0, valign: "top" });
});
s.addNotes("Answer first, then evidence. Every number on this slide is reproduced by the notebooks and SQL in the repository.");

// 3 ---------------------------------------------------------------- data & approach
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Data and approach", "Two years of till data joined to real Kenyan context data");
const steps = ["Frame", "Acquire", "Clean", "Explore", "SQL", "Test", "Model", "Dashboard"];
steps.forEach((t, i) => {
  const x = 0.6 + i * 1.53;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.75, w: 1.38, h: 0.75, fill: { color: i % 2 ? COL.green2 : COL.green },
    line: { type: "none" }, rectRadius: 0.08 });
  s.addText(`M${i + 1}\n${t}`, { x, y: 1.75, w: 1.38, h: 0.75, align: "center", valign: "middle", fontFace: BODY,
    fontSize: 12, bold: true, color: COL.white, isTextBox: true, margin: 0 });
});
s.addText("Internal (synthetic, documented generator)", { x: 0.6, y: 2.85, w: 6, h: 0.4, fontFace: HEAD, fontSize: 15,
  bold: true, color: COL.green, isTextBox: true, margin: 0 });
bullets(s, ["20 stores in 11 counties, 3 formats (one opened Jun 2025)", "91 products in 9 categories, KES shelf prices",
  "6,000 loyalty members + walk-in shoppers", `${fmt(D.receipts_y2 * 2 / 1000)}k receipts, 962k lines, Oct 2024 - Sep 2026`,
  "M-Pesa, cash, card, Airtel Money; 9 promotions incl. 2 randomised store tests"], 0.6, 3.3, 6, 3, 13);
s.addText("External (real, public)", { x: 6.9, y: 2.85, w: 6, h: 0.4, fontFace: HEAD, fontSize: 15, bold: true,
  color: COL.green, isTextBox: true, margin: 0 });
bullets(s, ["KNBS CPI inflation by month (via Central Bank of Kenya) -> real revenue, price drift",
  "KNBS 2019 census county population -> market penetration, white space",
  "Gazetted public holidays incl. Idd-ul-Fitr -> calendar effects, forecast features",
  "Stack: pandas, PostgreSQL 16, SciPy, scikit-learn, Excel / Power BI"], 6.9, 3.3, 5.9, 3, 13);
s.addNotes("Why synthetic: confidentiality. Realism: real inflation drives prices, real holidays shift demand, and known business events are planted so we can check whether the analysis finds them. Sources and licences are in docs/data_sources.md.");

// 4 ---------------------------------------------------------------- data quality
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Milestone 2 - cleaning", "Real-world dirt was found, fixed or removed - and every step is logged");
const c = D.clean;
[[fmt(c.payment_fixed), "payment labels standardised\n(15+ spellings of M-Pesa, cash...)"],
 [fmt(c.date_fixed), "dd/mm/yyyy dates parsed\nexplicitly day-first"],
 [fmt(c.prices_imputed), "missing prices imputed from\nproduct-store-month median"],
 [fmt(c.dup_receipts + c.dup_lines), "duplicate receipts and\nlines removed"],
 [fmt(c.outliers), "keying-error quantities (999...)\ndropped, not capped"],
 [fmt(c.test_rows + 12), "POS test receipts and\nyear-2031 clock errors removed"]].forEach(([b, l], i) => {
  stat(s, 0.6 + (i % 3) * 4.1, 1.8 + Math.floor(i / 3) * 1.6, 3.9, b, l);
});
s.addText("Checks after cleaning: unique receipt ids, all dates in range, all stores known, every line priced and categorised, till totals reconcile with line totals for 99.98% of receipts.",
  { x: 0.6, y: 5.25, w: 12.1, h: 0.9, fontFace: BODY, fontSize: 14, italic: true, color: COL.mute, isTextBox: true, margin: 0 });
s.addNotes("Principle: fix when the true value is recoverable, drop when it is not and the volume is immaterial. Walk-ins (no customer id) and returns (negative quantity) are kept - they are real business events, not errors.");

// 5 ---------------------------------------------------------------- growth vs inflation
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Q1 & Q7 - performance", `Revenue grew ${D.growth_nominal}% - but half of that is inflation`);
const mlabels = D.months.map((m) => { const [y, mo] = m.split("-"); return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+mo - 1] + " " + y.slice(2); });
s.addChart(pres.charts.LINE, [{ name: "Nominal revenue (KES M)", labels: mlabels, values: D.nominal_m },
  { name: "Real revenue, Oct-2024 prices (KES M)", labels: mlabels, values: D.real_m }],
  { ...chartBase, x: 0.6, y: 1.65, w: 8.4, h: 5.1, title: "Monthly net revenue, KES millions", chartColors: [COL.blue, COL.orange],
    lineSize: 2, lineDataSymbol: "none", showLegend: true, legendPos: "b", catAxisLabelRotate: -45, valAxisMinVal: 8 });
stat(s, 9.3, 1.75, 3.45, `KES ${D.rev_y2_m}M`, "revenue, last 12 months");
stat(s, 9.3, 3.25, 3.45, `+${D.growth_nominal}%`, "nominal growth vs prior year", COL.blue);
stat(s, 9.3, 4.75, 3.45, `+${D.growth_real}%`, "real growth after KNBS inflation", COL.orange);
s.addNotes("Inflation rose from about 4% to 6.8% in 2026 (KNBS via CBK). Reporting nominal growth alone would overstate performance by half. Receipts grew 3.6% - the real driver.");

// 6 ---------------------------------------------------------------- when
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Q2 - timing", "Demand follows the pay cheque, the weekend and the school calendar");
s.addImage({ path: FIG("04_dow_hour_heatmap.png"), x: 0.6, y: 1.7, w: 7.6, h: 2.6, altText: "Heatmap of receipts by weekday and hour" });
s.addImage({ path: FIG("05_payday_effect.png"), x: 0.6, y: 4.4, w: 7.6, h: 2.5, altText: "Average daily revenue by day of month" });
stat(s, 8.6, 1.75, 4.15, `+${D.payday_lift}%`, "daily revenue in the payday window (25th - 3rd)");
stat(s, 8.6, 3.25, 4.15, `+${D.dec_vs_avg}%`, `December vs an average month (January ${D.jan_vs_avg}%)`);
bullets(s, ["Roster extra tills Sat 10am-1pm and weekday 5-7pm", "Stock up staples before the 25th",
  "Stationery triples in January, spikes May and Aug-Sep"], 8.6, 4.85, 4.2, 2, 13);
s.addNotes("The payday effect is both more shoppers and bigger baskets (H4: +KES 82 per basket, 95% CI 77-88). These patterns become forecast features.");

// 7 ---------------------------------------------------------------- where
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Q1 - where", "Small Express stores are the most productive use of space");
const f = D.fmt_rev_per_sqm;
s.addChart(pres.charts.BAR, [{ name: "Revenue per sq m", labels: ["Express", "Supermarket", "Hypermarket"],
  values: [f.Express, f.Supermarket, f.Hypermarket] }], { ...chartBase, x: 0.6, y: 1.65, w: 6.2, h: 4.9, barDir: "col",
  title: "Revenue per sq m by format, last 12 months (KES)", chartColors: [COL.aqua], showLegend: false,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "#,##0", dataLabelFontSize: 12, barGapWidthPct: 60 });
s.addImage({ path: FIG("03_store_revenue.png"), x: 7.1, y: 1.65, w: 5.65, h: 3.25, altText: "Store revenue and revenue per sq m" });
bullets(s, ["Hypermarkets make the most shillings, Express the most per sq m",
  "Meru (1.5M people) has no store; Kakamega and Kilifi have 1.4M+ residents per store",
  "Recommendation: next openings = Express format in under-served counties"], 7.1, 5.05, 5.7, 1.9, 12.5);
s.addNotes("Penetration from SQL q10: revenue per 1,000 residents joins the census. Mombasa and Kisumu lead; Kilifi, Kakamega and Kajiado are low - growth headroom.");

// 8 ---------------------------------------------------------------- who
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Q3 - customers", "30% of members bring 79% of member revenue - and they pay with M-Pesa");
const rfm = D.rfm;
s.addChart(pres.charts.BAR, [
  { name: "% of members", labels: rfm.map((r) => r.rfm_segment), values: rfm.map((r) => r.pct_customers) },
  { name: "% of member revenue", labels: rfm.map((r) => r.rfm_segment), values: rfm.map((r) => r.pct_revenue) }],
  { ...chartBase, x: 0.6, y: 1.65, w: 7.8, h: 5.1, barDir: "bar", title: "RFM segments (SQL NTILE scoring)",
    chartColors: [COL.blue, COL.orange], showLegend: true, legendPos: "b", catAxisOrientation: "maxMin",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", dataLabelFontSize: 10, barGapWidthPct: 40 });
stat(s, 8.75, 1.75, 4.0, `${D.mpesa_last}%`, `of receipts paid by M-Pesa (up from ${D.mpesa_first}%)`);
stat(s, 8.75, 3.25, 4.0, "+26%", "typical card basket vs M-Pesa (Tukey HSD, p < 0.001)");
bullets(s, ["Protect Champions: availability, recognition", "Lipa na M-Pesa loyalty points reach most shoppers",
  "Bundle tea+sugar, unga+sukuma, diapers+wipes (lift 3-16x)"], 8.75, 4.8, 4.1, 2, 12.5);
s.addNotes("RFM computed in PostgreSQL with NTILE(5). Basket affinity from a self-join (q13): support, confidence and lift. Payment mix is the same in every format (Cramer's V = 0.008).");

// 9 ---------------------------------------------------------------- promo
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Q4 - promotions (randomised store test)", "The cooking-oil promo lifted volume - but gave away more margin than it earned");
const q = D.promo.q09;
const g = (grp, per) => q.find((r) => r.grp === grp && r.period === per).avg_daily_units_per_store;
s.addChart(pres.charts.BAR, [
  { name: "4 weeks before", labels: ["Control stores (9)", "Test stores (10)"], values: [g("Control", "Before"), g("Test", "Before")] },
  { name: "During promo (15% off)", labels: ["Control stores (9)", "Test stores (10)"], values: [g("Control", "During"), g("Test", "During")] }],
  { ...chartBase, x: 0.6, y: 1.65, w: 6.4, h: 4.9, barDir: "col", title: "Cooking-oil units per store per day",
    chartColors: ["A8A49A", COL.orange], showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0", dataLabelFontSize: 12, barGapWidthPct: 50 });
const h1 = D.promo.h1, h2 = D.promo.h2;
stat(s, 7.3, 1.75, 2.65, `+${fmt(h1.effect)} pp`, `diff-in-diff, 95% CI ${fmt(h1.CI95_low)} to ${fmt(h1.CI95_high)}`, COL.orange);
stat(s, 10.1, 1.75, 2.65, h1.p_value < 0.001 ? "p < 0.001" : `p = ${h1.p_value.toFixed(3)}`, "Welch t-test; permutation test agrees");
bullets(s, ["Stores were randomly assigned, so the uplift is causal",
  "But at 15% off a ~22%-margin staple, volume must ~triple to break even - gross profit fell",
  `Personal-care 5% off: no detectable effect (p = ${h2.p_value.toFixed(2)})`,
  "Next test: 7-10% off, success metric = gross profit per receipt, 20+ stores per arm"], 7.3, 3.35, 5.5, 3.4, 13);
s.addNotes("Unit of analysis is the store, avoiding pseudo-replication. Power analysis: with ~10 stores per arm we can only detect ~30% uplifts; 10% needs ~86 per arm - so future tests should run longer or use customer-level holdouts.");

// 10 ---------------------------------------------------------------- Nakuru
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Q5 - an early warning", "Nakuru has lost a fifth of its traffic since February 2026");
s.addImage({ path: FIG("09_nakuru_anomaly.png"), x: 0.6, y: 1.65, w: 8.2, h: 3.0, altText: "Nakuru weekly receipts vs chain" });
const nk = D.nakuru;
stat(s, 9.1, 1.75, 3.65, `${fmt(100 * (nk.effect + 0.158))}%`, "of active Nakuru members lapsed in Q3 2026", COL.orange);
stat(s, 9.1, 3.25, 3.65, "16%", "lapse rate in the rest of the chain");
bullets(s, [`Difference +${fmt(100 * nk.effect, 1)} pp (95% CI ${fmt(100 * nk.CI95_low, 1)} to ${fmt(100 * nk.CI95_high, 1)}), z = ${nk.statistic.toFixed(1)}`,
  `Nakuru has the highest share of drifting regulars (${D.drift[0].drifting_pct}%, SQL q12)`,
  "Timing matches a competitor opening near both Nakuru stores",
  "Action: targeted retention offer + price check vs competitor, weekly tracking"], 0.6, 4.85, 12, 2, 13.5);
s.addNotes("The EDA anomaly, the SQL drifting list, the two-proportion z-test and the churn model all point to the same place - triangulation makes the finding credible.");

// 11 ---------------------------------------------------------------- churn model
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Milestone 6b - churn model", "The model finds 64% of next quarter's churners in the riskiest 20% of members");
const ch = D.churn;
const rows = [["Model (out-of-time test, Jul-Sep 2026)", "ROC-AUC", "PR-AUC", "Lift top 10%"]];
for (const k of ["Baseline: rank by recency", "Logistic regression", "Gradient boosting"]) {
  rows.push([k, ch[k].ROC_AUC.toFixed(3), ch[k].PR_AUC.toFixed(3), ch[k]["lift_top10%"].toFixed(2) + "x"]);
}
s.addTable(rows.map((r, i) => r.map((v) => ({ text: v, options: { bold: i === 0, color: i === 0 ? COL.white : COL.ink,
  fill: { color: i === 0 ? COL.green : (i === 2 ? "FFF4D6" : COL.white) } } }))),
  { x: 0.6, y: 1.75, w: 7.2, colW: [3.6, 1.2, 1.2, 1.2], fontFace: BODY, fontSize: 12.5, border: { type: "solid", color: COL.line, pt: 0.75 }, rowH: 0.45 });
s.addImage({ path: FIG("19_churn_lift.png"), x: 0.6, y: 3.85, w: 7.2, h: 2.9, altText: "Churn rate by risk decile" });
const camp = D.campaign[0];
stat(s, 8.2, 1.75, 4.55, `KES ${fmt(camp.net_KES / 1000)}K`, `expected net gain: KES ${camp.offer_KES} offer to ${fmt(camp.members_contacted)} members picked by the model`, COL.aqua);
bullets(s, ["Churn = no purchase in next 90 days; features only from before the snapshot",
  "Trained on 3 snapshots, tested on a later, unseen quarter",
  "Recency is a strong baseline; the model adds calibrated probabilities -> a shilling value per customer",
  `Random targeting of the same list would net only KES ${fmt(camp.net_if_random_KES / 1000)}K`], 8.2, 3.3, 4.6, 3.6, 12.5);
s.addNotes("Success criteria from Milestone 1: AUC >= 0.75 and top-decile lift >= 2.5x - both met. Drivers: recent visit frequency, recency relative to the customer's own rhythm, home county Nakuru. Demographics add nothing. The campaign assumptions (25% save rate) must be validated with a holdout.");

// 12 ---------------------------------------------------------------- forecast
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Milestone 6a - demand forecast", `October 2026: about ${fmt(D.forecast_total.forecast_units / 1000, 1)}k units, KES ${fmt(D.forecast_total.forecast_revenue / 1e6, 1)}M`);
const fc = D.forecast;
s.addChart(pres.charts.BAR, [
  { name: "Sep 2026 actual", labels: fc.map((r) => r.category), values: fc.map((r) => r.sep_2026_actual) },
  { name: "Oct 2026 forecast", labels: fc.map((r) => r.category), values: fc.map((r) => Math.round(r.forecast_units)) }],
  { ...chartBase, x: 0.6, y: 1.65, w: 8.0, h: 5.1, barDir: "col", title: "Units by category", chartColors: ["A8A49A", COL.blue],
    showLegend: true, legendPos: "b", catAxisLabelRotate: -30, barGapWidthPct: 50 });
stat(s, 8.95, 1.75, 3.8, "33% vs 46%", "daily WAPE: model vs seasonal-naive baseline (28% better)", COL.blue);
stat(s, 8.95, 3.25, 3.8, "3.1%", "average error on monthly category totals (target < 10%)", COL.aqua);
bullets(s, ["Gradient boosting (Poisson), store x category x day", "Only lags of 35+ days: no look-ahead leakage",
  "Rolling backtest Jul, Aug, Sep 2026", "80% ranges per store-category for safety stock"], 8.95, 4.8, 3.9, 2.1, 12.5);
s.addNotes("Backtest WAPE: seasonal naive 46%, recent weekday average 39%, model 33% - beats the 15%-improvement criterion. Daily store-category counts are noisy, so orders should be placed at weekly/monthly level. Mazingira Day (10 Oct) and Mashujaa Day (20 Oct) are in the features.");

// 13 ---------------------------------------------------------------- recommendations
s = pres.addSlide({ masterName: "CONTENT" });
title(s, "Recommendations", "Five actions for the next quarter");
const recs = [
  ["Defend Nakuru now", "Retention offer to at-risk Nakuru members + competitor price audit", "CRM / Area manager", "Nakuru lapse rate back under 20%"],
  ["Run a model-targeted win-back", `KES 150 offer to the ${fmt(camp.members_contacted)} highest-value-at-risk members, 10% holdout`, "CRM", "Measured save rate, net KES"],
  ["Re-design promotions", "No more 15% staple discounts; test 7-10% with basket GP as the metric", "Commercial", "GP per receipt vs control"],
  ["Order to the forecast", "Use the October store x category forecast and 80% range for POs", "Supply chain", "Stock-outs and waste vs last year"],
  ["Grow with Express stores", "Shortlist Express sites in Meru, Kakamega, Kilifi", "Strategy / Property", "Revenue per sq m >= KES 5,000"],
];
const recRows = [["Action", "What", "Owner", "Success measure"]].concat(recs);
s.addTable(recRows.map((r, i) => r.map((v, j) => ({ text: v, options: { bold: i === 0 || j === 0,
  color: i === 0 ? COL.white : (j === 0 ? COL.green : COL.ink), fill: { color: i === 0 ? COL.green : (i % 2 ? COL.white : "FBF8F1") } } }))),
  { x: 0.6, y: 1.75, w: 12.1, colW: [2.6, 5.1, 1.9, 2.5], fontFace: BODY, fontSize: 13, rowH: 0.78,
    border: { type: "solid", color: COL.line, pt: 0.75 }, valign: "middle" });
s.addNotes("Each recommendation traces back to a specific piece of evidence and has an owner and a measurable outcome.");

// 14 ---------------------------------------------------------------- limitations & close
s = pres.addSlide({ masterName: "DARK" });
s.addText("Limitations, next steps and reproducibility", { x: 0.8, y: 0.6, w: 11.5, h: 0.8, fontFace: HEAD, fontSize: 30,
  color: COL.white, isTextBox: true, margin: 0 });
s.addText("Limitations", { x: 0.8, y: 1.7, w: 5.6, h: 0.4, fontFace: HEAD, fontSize: 17, color: COL.gold, bold: true, isTextBox: true, margin: 0 });
s.addText([
  "Sales data is synthetic: patterns are realistic, absolute shilling totals are illustrative",
  "Store tests have ~10 stores per arm: only large effects are detectable",
  "Churn cannot see members who shop without scanning their card",
  "Census population is from 2019"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 8 } })),
  { x: 0.8, y: 2.15, w: 5.6, h: 3, fontFace: BODY, fontSize: 14, color: "E3ECE6", valign: "top", isTextBox: true });
s.addText("Reproduce everything", { x: 7.0, y: 1.7, w: 5.6, h: 0.4, fontFace: HEAD, fontSize: 17, color: COL.gold, bold: true, isTextBox: true, margin: 0 });
s.addText([
  "python run_all.py  - data, cleaning, PostgreSQL, 7 notebooks, dashboard (~3 min)",
  "sql/03_analytics.sql - 15 documented queries",
  "dashboard/ - Excel dashboard + Power BI star schema, DAX and build guide",
  "docs/ - data sources & licences, data dictionary"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 8 } })),
  { x: 7.0, y: 2.15, w: 5.6, h: 3, fontFace: BODY, fontSize: 14, color: "E3ECE6", valign: "top", isTextBox: true });
s.addText("Asante - questions?", { x: 0.8, y: 5.9, w: 11, h: 0.8, fontFace: HEAD, fontSize: 32, color: COL.gold, isTextBox: true, margin: 0 });
s.addNotes("Close with the reproducibility story: a reviewer can regenerate every number from one command with a fixed seed.");

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote " + OUT));
