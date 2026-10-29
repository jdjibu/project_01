# Sources

Every dataset used in the model, report or website. File-level detail (URL, UTC retrieval time, SHA-256)
is in `data/raw/MANIFEST.csv`, written by `src/fetch_data.py`. All retrievals below: **29 Oct 2026**.

## Company filings (primary)
| Dataset | Source | URL | Notes |
|---|---|---|---|
| Consolidated financial results FY3/2019 to FY3/2026 (IS, BS, CF, segments, regions, product mix, FX, capex, R&D, shares, DPS, guidance) | Makita Corporation, English translation of Kessan Tanshin | https://www.makita.biz/ir/library/library_02.html | IFRS. FY3/2018 from comparatives in the FY3/2019 release. Unaudited releases; audited statements below |
| 1Q FY3/2026 and 1Q FY3/2027 results | Makita Corporation | same | Used for LTM to 30 Jun 2026 |
| Notice on non-consolidated results FY3/2025 | Makita Corporation | same (`financial_results202503-2.pdf`) | Context only |
| Audited consolidated financial statements with notes FY3/2019 to FY3/2026 | Makita Corporation | https://www.makita.biz/ir/library/library_03.html | Leases, debt, PP&E and tax notes for Phase 4 |
| Makita Report (integrated report) 2016 to 2026 | Makita Corporation | https://www.makita.biz/ir/library/library_05.html | Strategy and narrative; not downloaded in bulk (12MB each), cited by page when used |

## Market data
| Dataset | Source | Notes |
|---|---|---|
| 6586.T daily prices (10y), info snapshot, yfinance statements | Yahoo Finance via `yfinance` | Price on valuation date: JPY 5,253 (close 29 Oct 2026). Shares from filings, not Yahoo |
| TOPIX ETF (1306.T), Nikkei 225 daily prices | Yahoo Finance via `yfinance` | `^TOPX` not available; 1306.T used as TOPIX proxy for beta |
| FX: USD, EUR, HKD, SEK, CNY vs JPY daily | Yahoo Finance via `yfinance` | Peer conversion at valuation-date rates |
| Peer prices and fundamentals: 0669.HK, SWK, 2285.HK, HUSQ-B.ST, 6454.T, 6250.T, TTC | Yahoo Finance via `yfinance` | Last reported fiscal year. SWK and TTC verified against SEC |
| SWK, TTC XBRL company facts | U.S. SEC EDGAR | https://data.sec.gov/api/xbrl/companyfacts/ | Cross-check: 0.0% difference on revenue and net income |

## Rates and risk premia
| Dataset | Source | URL | Notes |
|---|---|---|---|
| 10Y JGB yield, daily since 1974 | Ministry of Finance Japan | https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/ | 2.867% on 28 Oct 2026 (latest published) |
| Japan long-term rate (backup) | FRED, IRLTLT01JPM156N | https://fred.stlouisfed.org/series/IRLTLT01JPM156N | Not retrieved: proxy blocked FRED on 29 Oct 2026. Not needed, MoF series is primary |
| Country risk premium, mature-market ERP | Damodaran Online, `ctryprem.xlsx` | https://pages.stern.nyu.edu/~adamodar/ | Japan A1, CRP 0.91%, total ERP 5.14%, mature ERP 4.23% |
| Implied ERP history | Damodaran Online, `histimpl.xls` | same | Implied ERP (FCFE) 4.23% at start of 2026 |
| Industry betas (Machinery, Japan and Global) | Damodaran Online, `betaJapan.xls`, `betaGlobal.xls` | same | Japan unlevered 1.11 (1.27 cash-corrected); Global unlevered 1.24 |
