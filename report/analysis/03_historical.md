# Phase 3: Historical analysis (FY2018 to FY2026)

Data: `data/clean/ratios.csv`, produced by `src/historical.py` from the parsed IFRS statements. Charts: `report/charts/`.
FY = year to 31 March. JPY m unless stated.

## Definitions (the choices that matter)
| Metric | Definition | Main alternative and why not |
|---|---|---|
| EBITDA | Operating profit + cash-flow D&A (includes right-of-use depreciation) | D&A excluding leases. Lease liabilities are treated as debt, so EBITDA should be pre-lease-cost |
| FCF | CFO + capex (purchase of non-current assets) + lease principal repayments | CFO + capex. That would flatter FCF after IFRS 16 because lease payments sit in financing |
| ROIC | NOPAT / average invested capital, with IC = operating NWC + PP&E + intangibles, NOPAT = OP x (1 - effective tax rate) | Financing approach (equity + debt - cash). Mathematically close here, but the operating approach isolates the business from Makita's large cash pile |
| ROE | Profit to owners / average parent equity, with a DuPont split (checked to reconcile exactly) | Year-end equity. Averages are standard for flows against stocks |
| Working-capital days | Year-end balance / revenue (DSO) or / cost of sales (DIO, DPO) x 365 | Average balances. Year-end shows the FY2022 build more clearly |
| Net cash | Cash + other current financial assets (mostly time deposits) - borrowings - other financial liabilities (mostly leases) | Cash only. Time deposits are liquid and Makita moves cash between the two |

## Key ratios
| | FY2018 | FY2020 | FY2022 | FY2023 | FY2024 | FY2025 | FY2026 |
|---|---|---|---|---|---|---|---|
| Revenue growth | n/a | 0.4% | 21.5% | 3.4% | -3.0% | 1.6% | 3.2% |
| Gross margin | 36.9% | 34.3% | 30.9% | 24.7% | 30.2% | 36.0% | 36.5% |
| SG&A / revenue | 20.0% | 21.3% | 18.5% | 21.0% | 21.3% | 21.8% | 23.1% |
| Operating margin | 16.8% | 13.0% | 12.4% | 3.7% | 8.9% | 14.2% | 13.5% |
| EBITDA margin | 19.1% | 15.9% | 15.2% | 7.1% | 12.8% | 18.2% | 17.4% |
| ROE | 10.4% | 8.3% | 9.2% | 1.5% | 5.3% | 8.8% | 8.3% |
| = Net margin | 11.5% | 9.7% | 8.8% | 1.5% | 5.9% | 10.5% | 10.2% |
| x Asset turnover | 0.76 | 0.73 | 0.81 | 0.73 | 0.69 | 0.70 | 0.68 |
| x Equity multiplier | 1.19 | 1.18 | 1.30 | 1.39 | 1.32 | 1.21 | 1.19 |
| ROIC (operating) | 18.4% | 12.6% | 10.7% | 1.8% | 6.3% | 12.2% | 11.7% |
| DSO (days) | 60 | 52 | 58 | 53 | 57 | 51 | 57 |
| DIO (days) | 238 | 242 | 339 | 288 | 244 | 256 | 278 |
| DPO (days) | 42 | 39 | 48 | 26 | 35 | 41 | 41 |
| Cash conversion cycle | 256 | 254 | 349 | 314 | 266 | 266 | 294 |
| Net cash (JPY m) | 191,434 | 148,315 | -27,178 | -39,039 | 172,098 | 260,464 | 268,657 |
| Equity ratio | 84.6% | 84.7% | 74.1% | 70.0% | 82.2% | 83.7% | 84.4% |
| Interest coverage (OP / interest paid) | 1,866x | 149x | 136x | 13x | 39x | 80x | 90x |
| FCF (JPY m) | 19,146 | 10,364 | -167,208 | 966 | 215,007 | 106,657 | 75,653 |
| FCF / net income | 0.35 | 0.22 | -2.58 | 0.08 | 4.92 | 1.34 | 0.95 |
| Capex / revenue | 3.2% | 9.0% | 8.1% | 5.1% | 2.4% | 2.3% | 2.8% |
| Capex / D&A (ex right-of-use) | 1.4x | 3.7x | 3.4x | 1.8x | 0.7x | 0.7x | 0.9x |
| Dividends + buybacks / net income | 25% | 35% | 29% | 167% | 36% | 23% | 108% |

IFRS 16 caveat: from FY2020, lease liabilities (about JPY 19-23bn) enter net cash and D&A rises by about JPY 5bn.
FY2018-19 EBITDA and net cash are therefore not strictly comparable.

## What the numbers say that a casual reader would miss
1. **The margin gap against FY2018 is all overhead, not pricing.** Gross margin is back to 36.5% (FY2018: 36.9%),
   but SG&A has risen from 20.0% to 23.1% of revenue, so operating margin is 13.5% against 16.8%. Getting to the
   company's 15% target is a cost-leverage story (sales headcount is rising under the plan), not a pricing story.

2. **Over the full cycle Makita converted only 54% of its profit into free cash.** Cumulative FCF from FY2018 to FY2026
   was JPY 272bn against net income of JPY 499bn. Inventory absorbed JPY 179bn (JPY 196bn to JPY 376bn) and capex ran at
   3.4-3.7x depreciation in FY2020-22. A DCF that assumes 100% conversion from day one would overvalue the company.

3. **Inventory days are rising again: 244 (FY2024) to 278 (FY2026).** That is not yet the 339 days of FY2022, which
   preceded the margin collapse, but the direction matters. Makita carries about 9 months of cost of sales in stock,
   so a demand slowdown hits margins through under-absorption with a lag.

4. **ROE is capped by the balance sheet, not by the business.** ROIC on operating capital is 11.7%, but ROE is only 8.3%,
   because the equity multiplier is 1.19 and net cash is 27% of equity. The 11% ROE target is a capital-allocation
   question: the FY2026 buyback (JPY 56bn) and the 50% payout policy point that way.

5. **The capex cycle has turned in shareholders' favour, for now.** After heavy FY2020-22 spending (the filings do not
   split capex by project; Makita Report 2026 p.23 describes added capacity in Romania, Thailand and Brazil over this
   period), capex fell to 0.7-0.9x depreciation. The company guides JPY 30bn for
   FY2027 (about 3.7% of guided revenue), so free cash flow will not keep benefiting from below-depreciation capex.

Also notable: North America has run at about break-even for nine years (Phase 2), and the aftermarket share of revenue
rose from 16.4% to 22.8% (chart 06).

## Charts
| File | Shows |
|---|---|
| `01_revenue_margins.png` | Revenue (bars) and gross, EBITDA and operating margins (separate panel) |
| `02_inventory_cycle.png` | Inventory days against operating margin |
| `03_region_mix.png` | Revenue share by customer region |
| `04_returns.png` | ROE and ROIC against the 11% ROE target |
| `05_fcf_vs_ni.png` | Free cash flow against net income |
| `06_aftermarket.png` | Parts, repairs and accessories share of revenue |
