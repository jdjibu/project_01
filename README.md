# Makita Corporation (6586 JP): Initiation of Coverage

**Student equity research project. Not investment advice.**

| | |
|---|---|
| Rating | **HOLD** |
| 12-month target price | **JPY 5,850** (+11.4%; +14.5% total return incl. dividends) |
| Price (29 Oct 2026) | JPY 5,253 |
| Scenarios | Bull JPY 7,600 (BUY) / Bear JPY 4,400 (SELL) |
| Rule | BUY if upside > +15%, SELL if < -10%, else HOLD |

Deliverables: [8-page report (PDF)](report/Makita_6586_initiation.pdf) · [Excel model](model/Makita_6586_model.xlsx) ·
[website](web/) (Vercel-ready) · [portfolio summary](report/portfolio_summary.md)

## The question
Makita, a Japanese cordless power-tool maker (IFRS, JPY), has recovered from its FY2022-23 inventory crisis, yet its
shares rose only 15% in two years against 50% for TOPIX. Is the recovery priced in, and what do driver-based
fundamentals imply for a 12-month target price?

## The answer, in three points
1. **The margin recovery is complete.** Gross margin is back to 36.5% (FY2018: 36.9%), but SG&A has risen from 20.0% to
   23.1% of sales, so the 15% operating-margin target needs cost leverage, not pricing.
2. **Growth is currency, not volume.** Europe (50% of sales) fell 1.5% in local currency in FY2026; 1Q FY2027 was +10.7%
   in yen and flat in local currency.
3. **The balance sheet limits the downside.** Net cash of JPY 269bn and a 7.8x EV/EBITDA multiple (FY2019-26 median 9.8x)
   make buybacks the most likely trigger for a re-rating.

## Method
| Step | What | Where |
|---|---|---|
| Data | Makita English Kessan Tanshin FY3/2019-FY3/2026 + 1Q FY3/2027 (IFRS), audited statements, integrated reports; yfinance prices; MoF 10Y JGB; Damodaran ERP/CRP/betas; SEC XBRL for US peers | `src/fetch_data.py`, `data/raw/MANIFEST.csv` |
| Clean and check | PDF statements parsed to tidy tables; **342 accounting checks** (subtotals, balance sheet, cash ties, segment sums); restatements and accounting changes flagged | `src/parse_makita.py`, `src/check_clean.py`, `data/clean/ACCOUNTING_NOTES.md` |
| History | Growth, margins, DuPont ROE, ROIC, working-capital days, leverage, FCF conversion, capex intensity | `src/historical.py`, `report/analysis/03_historical.md` |
| Model | Excel with live formulas: Assumptions (Base/Bull/Bear switch), regional revenue = local-currency growth x FX, IS/BS/CF, DCF, comps, sensitivities, football field, checks | `src/build_model.py`, `model/Makita_6586_model.xlsx` |
| Valuation | WACC 8.84% (CAPM: 10Y JGB 2.87%, bottom-up beta 1.12, ERP 4.23% + revenue-weighted CRP 1.20%); FCF from 1 Jul 2026, mid-period; value-driver terminal value cross-checked with an exit multiple | DCF sheet |
| Risks | Each risk re-runs the full model with one driver shocked | `src/risks.py`, `report/analysis/06_risks_catalysts.md` |
| Report and site | PDF and website generated from the same model outputs | `src/build_report.py`, `web/` |

### Key judgment calls (and the main alternative)
| Choice | Alternative | Why |
|---|---|---|
| Revenue by customer region x FX | Product-line build | Makita discloses product data only as finished goods vs parts; regional data has 9 years of history and makes FX explicit |
| Value-driver terminal value, NOPAT(1+g)(1-g/RONIC) | FCF x (1+g) | Avoids assuming FY2031's low reinvestment forever; RONIC 12% = Makita's median ROIC |
| Exit multiple 7.5x, within 0.5x of the Gordon-implied multiple | Makita's own 9.8x median | At 8.5x+ the exit method implied 4% perpetual growth, above the risk-free rate; a hard check now enforces consistency |
| Bottom-up beta (Damodaran Japan Machinery, relevered 1.12) | Regression beta | Regression (1.08 weekly vs TOPIX, s.e. 0.10) agrees but is noisier |
| Country risk premium weighted by revenue (1.20%) | Japan only (0.91%) or none | 83% of revenue is outside Japan |
| Leases deducted in FCF, excluded from the equity bridge | Leases as debt | Consistent with IFRS 16 EBITDA treatment; avoids double counting |
| Comps on last reported fiscal year | LTM | Peer quarterly data is patchy (TTI and Chervon report half-yearly) |
| DCF-based target price; comps as cross-check | Blend comps into the TP | Peers (TTI, Toro) grow faster with higher ROIC; their multiples are not a fair anchor |

## Reproduce
System tools: `pdftotext` (poppler-utils) and LibreOffice (headless, `python3-uno`) for formula recalculation.
```bash
pip install -r requirements.txt
```
```bash
python src/pipeline.py --offline    # rebuild everything from the committed raw data
```
```bash
python src/pipeline.py              # re-download all sources first (filings, prices, rates)
```
Website:
```bash
cd web && npm install && npm run dev
```
Deploy: import the repository in Vercel and set **Root Directory** to `web` (details in `web/README.md`).

## Folder guide
```
data/raw/          untouched downloads (Makita PDFs, prices, FX, JGB, Damodaran, SEC); MANIFEST.csv with sha256
data/clean/        tidy statements, ratios, market inputs, model outputs, checks, ACCOUNTING_NOTES.md
model/             Makita_6586_model.xlsx (live formulas, values cached)
report/            Makita_6586_initiation.pdf, charts/, analysis/ (phase write-ups), portfolio_summary.md
src/               pipeline scripts (fetch, parse, check, clean, historical, build_model, recalc, risks, report, web export)
web/               Vite website for Vercel (DESIGN.md, index.html, src/, public/data generated by the pipeline)
notebooks/         reserved for exploration (the analysis lives in src/ so it is reproducible)
SOURCES.md         every dataset with URL and retrieval date
```

## Limitations
- **Peer data** comes from yfinance. SWK and Toro match SEC 10-K figures exactly; TTI, Chervon, Husqvarna, Max and Yamabiko
  could not be cross-checked from this environment. Peers are on their last reported fiscal year, not LTM.
- **FX** is modelled as translation with constant margins. Yen-denominated fixed costs mean the true FX effect is larger.
- **No consensus estimates.** Free sources do not provide reliable broker consensus, so forecasts are compared with
  company guidance instead.
- **Tariff risk** is estimated outside the model because Makita does not disclose the sourcing of US-bound units.
- **Timing simplifications:** dividends are paid in the year earned, FX translation of the balance sheet is not forecast,
  and other balance-sheet items are held flat.
- **2Q FY3/2027 results** (expected around 30 Oct - early Nov 2026) were not yet published on the valuation date.
- Integrated reports (100MB+) are downloaded by `fetch_data.py` but not committed.

## Disclaimer
Prepared for educational and portfolio purposes. Not investment advice, not an offer or solicitation, and not reviewed by
Makita Corporation or any regulated firm. The author holds no position. Sources are believed reliable but accuracy is
not guaranteed.
