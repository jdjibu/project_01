"""Build clean market / valuation inputs from data/raw (no network).

Outputs (data/clean/):
  market_snapshot.csv   Makita price, 52-week range, shares (from filings), market cap, net cash
  beta_regressions.csv  OLS beta of 6586.T vs TOPIX ETF (1306.T) and Nikkei 225, several windows
  rf_jgb10y.csv         daily 10Y JGB yield (MoF), with latest value
  damodaran_inputs.csv  ERP, Japan CRP, industry betas
  fx_daily.csv          JPY crosses used to convert peers
  peers_financials.csv  last-reported-FY fundamentals + price, converted to JPY
  ltm_makita.csv        LTM to 30 Jun 2026 = FY3/2026 + 1Q FY3/2027 - 1Q FY3/2026
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, CLEAN = ROOT / "data/raw", ROOT / "data/clean"
VAL_DATE = "2026-10-29"
PEERS = {"0669.HK": "Techtronic Industries", "SWK": "Stanley Black & Decker", "2285.HK": "Chervon",
         "HUSQ-B.ST": "Husqvarna", "6454.T": "Max Co.", "6250.T": "Yamabiko", "TTC": "Toro"}
FX_TICKER = {"USD": "JPYX", "EUR": "EURJPYX", "HKD": "HKDJPYX", "SEK": "SEKJPYX", "CNY": "CNYJPYX"}


def prices(path, log=True):
    """Daily prices on the exchange-local trading date. Drops vendor errors: closes more than 3x away from the median
    of the surrounding 10 trading days (e.g. 1306.T on 30-31 Mar 2026, a mis-applied split at about 1/10 of true value)."""
    d = pd.read_csv(path, index_col=0)
    d.index = pd.to_datetime(d.index.str[:10])  # exchange-local trading date (avoid UTC shift)
    ref = d["Close"].rolling(11, center=True, min_periods=5).median()
    bad = (d["Close"] / ref > 3) | (d["Close"] / ref < 1 / 3)
    if bad.any() and log:
        rows = d.loc[bad, ["Close"]].assign(neighbour_median=ref[bad], file=Path(path).name)
        logf = CLEAN / "price_outliers_removed.csv"
        old = pd.read_csv(logf, index_col=0) if logf.exists() else None
        rows.index = rows.index.strftime("%Y-%m-%d")
        out = rows if old is None else pd.concat([old[old.file != Path(path).name], rows])
        out.to_csv(logf)
    return d[~bad]


def fx_rates():
    out = {}
    for ccy, t in FX_TICKER.items():
        out[ccy] = prices(RAW / f"market/{t}_prices_daily.csv")["Close"]
    fx = pd.DataFrame(out)
    fx["JPY"] = 1.0
    fx.to_csv(CLEAN / "fx_daily.csv")
    return fx


def fx_on(fx, ccy, date):
    s = fx[ccy].loc[:date].dropna()
    return float(s.iloc[-1])


def beta_table():
    mk = prices(RAW / "market/6586.T_prices_daily.csv")["Adj Close"]
    rows = []
    for idx_name, f in [("TOPIX ETF (1306.T)", "1306.T"), ("Nikkei 225", "N225")]:
        ix = prices(RAW / f"market/{f}_prices_daily.csv")["Adj Close"]
        for freq, label in [("W-FRI", "weekly"), ("ME", "monthly")]:
            for yrs in [2, 5]:
                start = pd.Timestamp(VAL_DATE) - pd.DateOffset(years=yrs)
                df = pd.concat([mk, ix], axis=1, keys=["s", "m"]).loc[start:VAL_DATE].resample(freq).last()
                r = np.log(df).diff().dropna()
                if len(r) < 20:
                    continue
                cov = np.cov(r.s, r.m)
                b = cov[0, 1] / cov[1, 1]
                resid = r.s - (r.s.mean() + b * (r.m - r.m.mean()))
                se = np.sqrt(resid.var(ddof=2) / ((r.m - r.m.mean()) ** 2).sum())
                r2 = np.corrcoef(r.s, r.m)[0, 1] ** 2
                rows.append({"index": idx_name, "frequency": label, "years": yrs, "n_obs": len(r),
                             "raw_beta": b, "std_err": se, "r_squared": r2,
                             "blume_adjusted_beta": 0.67 * b + 0.33})
    t = pd.DataFrame(rows)
    t.to_csv(CLEAN / "beta_regressions.csv", index=False)
    return t


def jgb():
    h = pd.read_csv(RAW / "macro/mof_jgb_historical.csv", skiprows=1, encoding="shift_jis", encoding_errors="replace")
    c = pd.read_csv(RAW / "macro/mof_jgb_current_month.csv", skiprows=1, encoding="shift_jis", encoding_errors="replace")
    d = pd.concat([h, c])[["Date", "10Y"]]
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    d["10Y"] = pd.to_numeric(d["10Y"], errors="coerce")
    d = d.dropna().drop_duplicates("Date", keep="last").sort_values("Date")
    d = d[d.Date >= "2000-01-01"]
    d.to_csv(CLEAN / "rf_jgb10y.csv", index=False)
    return d


def damodaran():
    c = pd.read_excel(RAW / "damodaran/ctryprem.xlsx", sheet_name="ERPs by country", header=None)
    jp = c[c[0].astype(str).str.strip() == "Japan"].iloc[0]
    h = pd.read_excel(RAW / "damodaran/histimpl.xls", header=None)
    yrs = h[pd.to_numeric(h[0], errors="coerce").notna()]
    last = yrs.iloc[-1]
    rows = [
        ("Japan Moody's rating", jp[2], "ctryprem.xlsx / ERPs by country"),
        ("Japan rating-based default spread", jp[3], "ctryprem.xlsx / ERPs by country"),
        ("Japan total ERP (rating-based)", jp[4], "ctryprem.xlsx / ERPs by country"),
        ("Japan country risk premium (rating-based)", jp[5], "ctryprem.xlsx / ERPs by country"),
        ("Mature market ERP (= Japan total ERP - Japan CRP)", jp[4] - jp[5], "derived"),
        (f"US implied ERP (FCFE), start of {int(last[0]) + 1}", last[15], "histimpl.xls, year-end row"),
    ]
    for f, region in [("betaJapan.xls", "Japan"), ("betaGlobal.xls", "Global")]:
        b = pd.read_excel(RAW / f"damodaran/{f}", sheet_name="Industry Averages", header=None)
        m = b[b[0].astype(str).str.strip() == "Machinery"].iloc[0]
        rows += [(f"{region} Machinery: levered beta", m[2], f), (f"{region} Machinery: D/E", m[3], f),
                 (f"{region} Machinery: unlevered beta", m[5], f),
                 (f"{region} Machinery: unlevered beta corrected for cash", m[7], f),
                 (f"{region} Machinery: number of firms", m[1], f)]
    d = pd.DataFrame(rows, columns=["item", "value", "source"])
    d.to_csv(CLEAN / "damodaran_inputs.csv", index=False)

    # revenue-weighted country risk premium: GDP-weighted CRP per Damodaran region, weighted by Makita FY2026
    # revenue by customer location. Japan uses its own CRP.
    reg = pd.read_excel(RAW / "damodaran/ctryprem.xlsx", sheet_name="Regional Weighted Averages", header=0)
    reg = reg.dropna(subset=["Region", "Country Risk Premium"])
    reg["gdp"] = pd.to_numeric(reg.iloc[:, 1], errors="coerce")
    crp = reg.groupby("Region").apply(lambda g: (g["Country Risk Premium"] * g.gdp).sum() / g.gdp.sum())
    geo = pd.read_csv(CLEAN / "makita_geo_revenue.csv").query("fy == 2026 and release_fy == 2026").set_index("region")["value"]
    mapping = {"Japan": None, "Europe": "Western Europe", "North America": "North America", "Asia": "Asia",
               "Central & South America": "Central and South America", "Oceania": "Australia & New Zealand",
               "Middle East & Africa": ["Middle East", "Africa"]}
    rows = []
    for region, dam in mapping.items():
        if dam is None:
            v = float(jp[5])
        elif isinstance(dam, list):
            v = float(crp[dam].mean())
        else:
            v = float(crp[dam])
        rows.append({"makita_region": region, "damodaran_region": str(dam or "Japan (country)"),
                     "crp": v, "revenue_fy2026": geo[region], "weight": geo[region] / geo["Total"]})
    w = pd.DataFrame(rows)
    w.loc[len(w)] = {"makita_region": "Revenue-weighted CRP", "damodaran_region": "", "crp": (w.crp * w.weight).sum(),
                     "revenue_fy2026": w.revenue_fy2026.sum(), "weight": w.weight.sum()}
    w.to_csv(CLEAN / "crp_weighted.csv", index=False)
    return d


def makita_hist_multiples(fx):
    """Makita EV/EBITDA and P/E at each fiscal year-end (31 Mar) from price history and filings."""
    px = prices(RAW / "market/6586.T_prices_daily.csv")["Close"]
    IS = pd.read_csv(CLEAN / "makita_is.csv", index_col=0)
    BS = pd.read_csv(CLEAN / "makita_bs.csv", index_col=0).fillna(0)
    CF = pd.read_csv(CLEAN / "makita_cf.csv", index_col=0)
    sup = pd.read_csv(CLEAN / "makita_supplementary_wide.csv", index_col=0)
    rows = []
    for fy in range(2019, 2027):
        c = f"FY{fy}"
        p = float(px.loc[:f"{fy}-03-31"].iloc[-1])
        sh = sup.at["shares_issued", c] - sup.at["treasury_shares_count", c]
        mcap = p * sh / 1e6
        debt = BS.at["borrowings_cur", c] + BS.at["other_fin_liab_cur", c] + BS.at["other_fin_liab_nc", c]
        cash = BS.at["cash", c] + BS.at["other_fin_assets_cur", c]
        ev = mcap + debt - cash + BS.at["nci", c]
        ebitda = IS.at["operating_profit", c] + CF.at["cfo_da", c]
        rows.append({"fy": c, "price": p, "shares": sh, "market_cap": mcap, "ev": ev, "ebitda": ebitda,
                     "ev_ebitda": ev / ebitda, "pe": mcap / IS.at["ni_parent", c],
                     "pb": mcap / BS.at["equity_parent", c]})
    d = pd.DataFrame(rows)
    d.to_csv(CLEAN / "makita_hist_multiples.csv", index=False)
    return d


def ltm():
    q = pd.read_csv(CLEAN / "makita_quarterly.csv")
    IS = pd.read_csv(CLEAN / "makita_is.csv", index_col=0)
    CF = pd.read_csv(CLEAN / "makita_cf.csv", index_col=0)
    rows = []
    for stmt, wide in [("IS", IS), ("CF", CF)]:
        for item in wide.index:
            a = q[(q.period == "1Q2027") & (q.statement == stmt) & (q["item"] == item)]
            b = q[(q.period == "1Q2026") & (q.statement == stmt) & (q["item"] == item)]
            if a.empty or b.empty or item in ("cash_begin", "cash_end"):
                continue
            fy, q1, q0 = wide.at[item, "FY2026"], a.value.iloc[0], b.value.iloc[0]
            rows.append({"statement": stmt, "item": item, "FY2026": fy, "1Q2027": q1, "1Q2026": q0,
                         "LTM_Jun2026": fy + q1 - q0,
                         "check_1Q2026_restated_in_1Q2027_release": a.prior.iloc[0] - q0})
    d = pd.DataFrame(rows)
    d.to_csv(CLEAN / "ltm_makita.csv", index=False)
    return d


def bs_latest():
    q = pd.read_csv(CLEAN / "makita_quarterly.csv")
    return q[(q.period == "1Q2027") & (q.statement == "BS")].set_index("item")["value"]


def snapshot(bsq, fx):
    p = prices(RAW / "market/6586.T_prices_daily.csv")
    p = p.loc[:VAL_DATE]
    last = p.iloc[-1]
    yr = p.loc[pd.Timestamp(VAL_DATE) - pd.DateOffset(weeks=52):]
    q = pd.read_csv(CLEAN / "makita_quarterly.csv")
    sup = q[(q.period == "1Q2027") & (q.statement == "SUP")].set_index("item")["value"]
    shares = sup["shares_issued"] - sup["treasury_shares_count"]
    info = json.loads((RAW / "market/6586.T_info.json").read_text())
    debt = bsq.get("borrowings_cur", 0) + bsq.get("borrowings_nc", 0)
    leases = bsq.get("other_fin_liab_cur", 0) + bsq.get("other_fin_liab_nc", 0)
    rows = [
        ("valuation_date", VAL_DATE, "close date used"),
        ("price_close_jpy", last["Close"], "yfinance 6586.T"),
        ("price_date", str(p.index[-1].date()), "yfinance 6586.T"),
        ("high_52w_close", yr["Close"].max(), "computed from daily closes"),
        ("low_52w_close", yr["Close"].min(), "computed from daily closes"),
        ("high_52w_intraday", yr["High"].max(), "computed from daily highs"),
        ("low_52w_intraday", yr["Low"].min(), "computed from daily lows"),
        ("avg_daily_value_traded_3m_jpy_m", (p["Close"] * p["Volume"]).iloc[-63:].mean() / 1e6, "computed"),
        ("shares_outstanding_30jun2026", shares, "1Q FY3/2027 release: issued - treasury"),
        ("shares_outstanding_yfinance", info.get("sharesOutstanding"), "yfinance info (cross-check)"),
        ("market_cap_jpy_m", last["Close"] * shares / 1e6, "price x filing shares"),
        ("cash_30jun2026_jpy_m", bsq["cash"], "1Q FY3/2027 BS"),
        ("other_fin_assets_cur_30jun2026_jpy_m", bsq["other_fin_assets_cur"], "1Q BS: mainly time deposits"),
        ("borrowings_30jun2026_jpy_m", debt, "1Q BS"),
        ("other_fin_liab_30jun2026_jpy_m", leases, "1Q BS: mainly lease liabilities (IFRS 16)"),
        ("nci_30jun2026_jpy_m", bsq["nci"], "1Q BS"),
        ("usdjpy_on_val_date", fx_on(fx, "USD", VAL_DATE), "yfinance JPY=X"),
        ("eurjpy_on_val_date", fx_on(fx, "EUR", VAL_DATE), "yfinance EURJPY=X"),
    ]
    d = pd.DataFrame(rows, columns=["item", "value", "source"])
    d.to_csv(CLEAN / "market_snapshot.csv", index=False)
    return d


def peers(fx):
    rows = []
    pick = lambda df, names: next((float(df.at[n, df.columns[0]]) for n in names
                                   if n in df.index and pd.notna(df.at[n, df.columns[0]])), np.nan)
    for t, name in {**PEERS, "6586.T": "Makita (yfinance, cross-check)"}.items():
        folder = "market" if t == "6586.T" else "peers"
        info = json.loads((RAW / f"{folder}/{t}_info.json").read_text())
        i = pd.read_csv(RAW / f"{folder}/{t}_income_stmt.csv", index_col=0)
        b = pd.read_csv(RAW / f"{folder}/{t}_balance_sheet.csv", index_col=0)
        px = prices(RAW / f"{folder}/{t}_prices_daily.csv").loc[:VAL_DATE]
        ccy_px, ccy_fin = info["currency"], info["financialCurrency"]
        fx_px, fx_fin = fx_on(fx, ccy_px, VAL_DATE), fx_on(fx, ccy_fin, VAL_DATE)
        price = float(px["Close"].iloc[-1])
        shares = float(info["sharesOutstanding"])
        r = {"ticker": t, "name": name, "fy_end": i.columns[0], "price_ccy": ccy_px, "fin_ccy": ccy_fin,
             "price_local": price, "price_date": str(px.index[-1].date()), "shares_m": shares / 1e6,
             "fx_price_to_jpy": fx_px, "fx_fin_to_jpy": fx_fin,
             "revenue": pick(i, ["Total Revenue"]), "ebitda": pick(i, ["EBITDA"]),
             "ebitda_normalized": pick(i, ["Normalized EBITDA"]), "ebit": pick(i, ["EBIT"]),
             "operating_income": pick(i, ["Operating Income"]), "net_income": pick(i, ["Net Income Common Stockholders"]),
             "da": pick(i, ["Reconciled Depreciation"]), "total_debt": pick(b, ["Total Debt"]),
             "cash_sti": pick(b, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"]),
             "equity": pick(b, ["Stockholders Equity"]), "minority": pick(b, ["Minority Interest"])}
        r["minority"] = 0.0 if np.isnan(r["minority"]) else r["minority"]
        # all money values in JPY millions
        for k in ["revenue", "ebitda", "ebitda_normalized", "ebit", "operating_income", "net_income", "da",
                  "total_debt", "cash_sti", "equity", "minority"]:
            r[k + "_jpy_m"] = r.pop(k) * fx_fin / 1e6
        r["market_cap_jpy_m"] = price * shares * fx_px / 1e6
        r["ev_jpy_m"] = r["market_cap_jpy_m"] + r["total_debt_jpy_m"] - r["cash_sti_jpy_m"] + r["minority_jpy_m"]
        h52 = px.loc[pd.Timestamp(VAL_DATE) - pd.DateOffset(weeks=52):]
        r["high_52w_local"], r["low_52w_local"] = h52["Close"].max(), h52["Close"].min()
        r["yf_enterpriseToEbitda_DO_NOT_USE"] = info.get("enterpriseToEbitda")
        rows.append(r)
    d = pd.DataFrame(rows)
    d.to_csv(CLEAN / "peers_financials.csv", index=False)
    return d


def main():
    fx = fx_rates()
    jgb()
    damodaran()
    beta_table()
    ltm()
    snapshot(bs_latest(), fx)
    makita_hist_multiples(fx)
    peers(fx)
    print("market inputs written to", CLEAN)


if __name__ == "__main__":
    main()
