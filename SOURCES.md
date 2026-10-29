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
| Makita Report 2025 and 2026 (integrated reports) | Makita Corporation | https://www.makita.biz/ir/library/library_05.html | Vision FY2030 targets (p.19), 40Vmax (p.20), market size (p.22), production mix (p.23). 100MB+, downloaded by fetch_data.py, not committed |

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

## Industry and context (web sources, retrieved 29 Oct 2026)
| Fact used | Source |
|---|---|
| TTI 2025 sales US$15.3bn (+4.1% local currency); Milwaukee +7.9% local currency | [TTI Annual Report 2025](https://www.ttigroup.com/sites/default/files/2026-03/ar2025.pdf) (primary; verified in PDF text) |
| Hilti 2025 sales CHF 6.3bn (+1.9% local currency) | [Hilti media release](https://www.hilti.group/content/hilti/CP/XX/en/company/media-relations/media-releases/2025-business-result.html) |
| Bosch Power Tools 2025 sales about EUR 5bn | [Bosch Media Service](https://www.bosch-presse.de/pressportal/de/en/personnel-changes-at-bosch-power-tools-254528.html) |
| Power-tool market US$29.7bn (2025), cordless share 62% | [Straits Research](https://straitsresearch.com/report/power-tools-market) |
| Power-tool market US$36.6bn (2026E) | [Persistence Market Research](https://www.persistencemarketresearch.com/market-research/power-tools-market.asp) |
| Power-tool market US$46.8bn (2025) | [Arizton](https://www.arizton.com/market-reports/power-tools-market) |
| California zero-emission small off-road engines from MY2024 | [CARB, Dec 2021](https://ww2.arb.ca.gov/node/16486) |
| EU Battery Regulation (EU) 2023/1542 | [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2023/1542/oj) |
| Supreme Court IEEPA ruling (20 Feb 2026) and CIT refund order (4 Mar 2026) | [Baker Tilly](https://www.bakertilly.com/insights/ieepa-tariff-refunds-and-the-supreme-court-ruling) |

## Derived datasets
| Dataset | How | File |
|---|---|---|
| Revenue-weighted CRP 1.20% | Damodaran GDP-weighted regional CRPs x Makita FY2026 revenue by customer region | `data/clean/crp_weighted.csv` |
| Makita historical EV/EBITDA FY2019-26 | FY-end close x filing share count; net cash and EBITDA from filings | `data/clean/makita_hist_multiples.csv` |
| Price-error log | 1306.T 30-31 Mar 2026 removed (vendor error) | `data/clean/price_outliers_removed.csv` |
