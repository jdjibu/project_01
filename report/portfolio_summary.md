# Portfolio summary

## Card version (110 words)
**Makita (6586 JP): initiation of coverage**

Is Makita fairly priced after its post-COVID inventory reset? I built an initiation of coverage on the Japanese
power-tool maker from its IFRS filings: a Python pipeline parses nine years of statements (342 accounting checks), feeds
a three-statement Excel model with live formulas, a driver-based DCF (regional growth x FX, value-driver terminal value),
trading comps and sensitivities. Finding: HOLD, 12-month target JPY 5,850 (+11%). The margin recovery is done, recent
growth came from the weak yen, and a fortress balance sheet limits the downside. Each risk re-runs the full model: a
200bp gross-margin slip matters three times more than a 10% yen move. Tools: Python, pandas, openpyxl/xlsxwriter,
LibreOffice, reportlab, Vite.

## Three-sentence version
I wrote an initiation of coverage on Makita (6586 JP), the Japanese power-tool maker, built from its IFRS filings with a
reproducible Python pipeline and a live-formula Excel model. The driver-based DCF and peer comps give a HOLD with a
12-month target of JPY 5,850 (+11%): margins have recovered, but recent growth came from the weak yen rather than volume.
The project ships as an 8-page sell-side-style report, an interactive website and a GitHub repository with every number
traceable to its source.

## Card fields
| Field | Content |
|---|---|
| Question | Is Makita fairly priced after its FY2022-23 inventory reset? |
| Finding | HOLD, 12-month TP JPY 5,850 (+11.4%); margins recovered, growth is FX-driven, downside limited by JPY 269bn net cash |
| Methods | Three-statement model, driver-based DCF (CAPM WACC 8.84%, value-driver terminal value), trading comps, scenario and risk sensitivities |
| Tools | Python (pandas, openpyxl, xlsxwriter, matplotlib, reportlab), LibreOffice headless, yfinance, Vite |
| Links | Report PDF: `report/Makita_6586_initiation.pdf` · Model: `model/Makita_6586_model.xlsx` · Code: https://github.com/jdjibu/project_01 · Website: your Vercel URL after deploying `web/` |
