# Accounting changes, restatements and data caveats (Makita, 6586 JP)

All figures are JPY millions, IFRS, fiscal year (FY) ending 31 March. FY2026 = year to 31 Mar 2026.

| # | Item | Years affected | What happened | How the data handles it |
|---|---|---|---|---|
| 1 | US GAAP to IFRS | FY2018 and earlier | Makita adopted IFRS from FY3/2019. FY3/2018 was restated to IFRS as the comparative in the FY3/2019 release; 1 Apr 2017 is the IFRS opening balance sheet. | History starts at FY2018 (IS, CF) and 1 Apr 2017 (BS, shown as FY2017). No US GAAP years are mixed in. |
| 2 | IFRS 16 Leases | From FY2020 | Right-of-use assets now sit inside PP&E; lease liabilities inside "other financial liabilities" (non-current jumps from 256 to 9,894). Lease principal repayments move to financing cash flow. | Ratios that use PP&E, D&A, EBITDA or debt are not like-for-like across FY2019/FY2020. Flagged in the historical analysis. |
| 3 | Lease reclassification of FY2019 comparative | FY2019 CF | FY3/2020 release split 36 of lease repayments out of FY2019 "Other" financing. | Each year uses its own release, so FY2019 shows "Other" -371 and no lease line. Logged in `makita_restatements.csv`. |
| 4 | Non-current income taxes payable | FY2025 | FY3/2026 release shows 104 as a separate "income taxes payable" (non-current) line, previously inside "other non-current liabilities" (129 to 25). | Totals unchanged. Logged in `makita_restatements.csv`. |
| 5 | Two D&A figures | All years | Cash-flow D&A (e.g. FY2026: 30,465) includes right-of-use depreciation; the supplementary table's D&A (25,205) excludes it. The gap (about 5,000) tracks lease repayments (5,151). | Model uses CF D&A for EBITDA (IFRS 16 basis) and treats lease liabilities as debt-like, so EV and EBITDA are on the same basis. |
| 6 | Capex definition | All years | "Capital expenditures" in the supplementary table equals CF "purchase of non-current assets" in every year (checked). | One capex series. |
| 7 | Time deposits | All years | Large swings in investing cash flow are time-deposit placements and withdrawals (e.g. FY2026 -82,104 / +85,949). Deposits sit in "other financial assets" (current). | Excluded from capex and FCF; considered for net cash in valuation. |
| 8 | US tariff refund | 1Q FY2027 | Company states 1Q FY3/2027 cost ratio improved because of a refund of U.S. tariffs. This is non-recurring. | LTM to Jun-2026 is reported as is; normalisation is an explicit forecast assumption. |
| 9 | Treasury shares | FY2024, FY2026, 1Q FY2027 | Buybacks: about 10,000 (FY2024), 55,928 (FY2026), 4,075 (1Q FY2027). Treasury shares rose from 8.5m to 22.4m. | Share count for valuation is from the latest filing (257.66m at 30 Jun 2026), not yfinance. |
| 10 | IAS 21 amendment | FY2026 | Lack of exchangeability guidance. Company states no material impact. | None. |

## Integrity checks
`src/check_clean.py` runs 342 checks (statement subtotals, BS balance, CF-to-BS cash tie, segment and region sums
to consolidated revenue and OP, segment totals, capex tie). Result at last run: **342 / 342 pass** (`checks_makita.csv`).

## Known gaps
- Share counts for FY2018 are not parsed (only needed for FY2018 per-share history; EPS from the release is used instead).
- Peer fundamentals come from yfinance. SWK and Toro were verified exactly against SEC XBRL 10-K data
  (`peer_crosscheck.csv`). TTI, Chervon, Husqvarna, Max and Yamabiko could not be cross-checked from this environment.
- yfinance's precomputed peer ratios are wrong for cross-currency listings (TTI EV/EBITDA shown as 140x because
  EV is in HKD and EBITDA in USD). All multiples are recomputed in JPY in `peers_financials.csv`.

## Market-data cleaning
- `src/clean_market.py` drops vendor price errors: closes more than 3x away from the median of the surrounding
  10 trading days. Removed: 1306.T (TOPIX ETF) on 30 and 31 Mar 2026, quoted at about 37 against about 383
  (a split adjustment misapplied for two days). Log: `price_outliers_removed.csv`. The bad 31 Mar close distorted monthly betas
  (0.99-1.12 after the fix, in line with weekly betas of 1.08-1.13); weekly betas were unaffected.
