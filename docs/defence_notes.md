# Defence notes - questions an examiner is likely to ask

Use these to rehearse. Each answer points to where the evidence lives.

**1. Why synthetic data? Isn't that "cheating"?**
The brief allows generated data, and real till data is confidential. What matters is that it is realistic and documented:
real KNBS inflation drives prices, real holidays shift demand, Kenyan payday and M-Pesa behaviour are built in, and the
data is dirty like a real POS export. Known events were planted (Nakuru competitor, promo effects) so I could *check*
the methods recover them - something you cannot do with real data. (`src/generate_data.py`, `docs/data_sources.md`)

**2. How did you decide what was an outlier?**
Two kinds: errors and genuine extremes. Quantities of 99/120/999/1000 are keying errors - the 99.9th percentile is 6
units. I dropped |qty| > 30 (60 lines, 0.006%) rather than capping because the true value is unknowable. Large festive
baskets were kept. (`02_data_cleaning`, section 4)

**3. Why the store, not the receipt, as the unit in the promo test?**
Stores were randomised, and receipts in the same store are correlated. Using 300k receipts as independent would give a
falsely tiny p-value (pseudo-replication). With 19 stores I also ran a permutation test, which needs no normality.

**4. The promo was significant - why do you say it failed?**
Statistical significance is not profit. A 15% discount is given on every unit, including those that would have sold
anyway; with ~22% margin, volume would need to roughly triple to break even. Observed incremental units were ~65%, so
gross profit on cooking oil fell. (H3)

**5. With 300k receipts everything is significant. How do you handle that?**
I report effect sizes and confidence intervals, not just p-values. E.g. payday basket difference is KES 82 (95% CI 77-88),
Cohen's d = 0.11 - small per basket, but it matters because payday days also bring more shoppers. Chi-square for payment
vs format is "significant" but Cramer's V = 0.008, i.e. practically no relationship.

**6. How do you know the forecast has no data leakage?**
Every sales-based feature is lagged at least 35 days, which is always before the forecast origin for any day in the
month. Calendar, holidays and planned promotions are known in advance. The backtest re-trains for each month using only
earlier data. (`06_demand_forecast`)

**7. Why is daily WAPE 33% - isn't that bad?**
Store x category x day counts are small and noisy (Poisson noise alone is large at ~10 units). The baselines score 39-46%,
so the model is 28% better than seasonal naive, meeting the success criterion. At the level buyers order (monthly category
totals) the error is ~3%.

**8. Your churn model barely beats "rank by recency". Why bother?**
True - recency is a strong baseline (AUC 0.89 vs 0.91), and I say so. The model adds calibrated probabilities, which let
us put a shilling value at risk on each customer and choose who is worth an offer; it also captures county effects
(Nakuru) and momentum that a single rule ignores. Model targeting nets ~3x what random targeting would.

**9. How was churn defined, and why 90 days?**
No purchase in the 90 days after a snapshot, among members active in the previous 180 days. 90 days is several times the
typical gap between visits, so a quiet member is very likely gone rather than between trips. It is a business choice that
should be agreed with CRM; changing it is one parameter.

**10. Why out-of-time validation instead of a random split?**
The model will be used on future customers. A random split lets the same customer and season leak into both sides and
overstates performance. Testing on a later quarter (Jul-Sep 2026) that includes new shocks (Nakuru, inflation jump) is the
honest test.

**11. How did you use the external data?**
CPI -> real revenue (deflating to Oct-2024 shillings) and a forecast feature; census -> revenue per 1,000 residents and
white-space (Meru); holidays -> calendar effects and forecast features.

**12. What would you do with more time?**
SKU-level forecasts for top sellers; weekly re-forecasting; a properly powered promo test with customer-level holdouts;
uplift modelling for the win-back campaign (who responds, not just who churns); connect Power BI live to PostgreSQL.
