"""Phase 5-7 charts from the recalculated model (data/clean/model_outputs.json), plus website JSON."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from historical import BLUE, GOLD, GREY, INK, MUTED, OXBLOOD, RULE, CHARTS, WEB, fig, save, style

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data/clean"
SRC_MODEL = "Source: Makita filings, yfinance, MoF, Damodaran; student model (model/Makita_6586_model.xlsx)."


def football(o):
    ff = o["football"]
    order = ["dcf_g", "dcf_x", "own", "cmp_ev", "cmp_pe", "w52"]
    labels = [ff[k]["label"] for k in order]
    f = fig(3.3)
    a = f.add_subplot(1, 1, 1)
    y = np.arange(len(order))[::-1]
    for yi, k in zip(y, order):
        lo, hi = ff[k]["low"], ff[k]["high"]
        col = GOLD if k.startswith("dcf") else (GREY if k == "w52" else BLUE)
        a.barh(yi, hi - lo, left=lo, height=0.5, color=col)
        a.text(lo - 60, yi, f"{lo:,.0f}", ha="right", va="center", fontsize=7, color=MUTED)
        a.text(hi + 60, yi, f"{hi:,.0f}", ha="left", va="center", fontsize=7, color=MUTED)
    px, tp = o["price"], o["tp"]
    a.axvline(px, color=INK, linewidth=1.2)
    a.axvline(tp, color=OXBLOOD, linewidth=1.2, linestyle=(0, (4, 2)))
    a.text(px - 40, len(order) - 0.45, f"Price {px:,.0f}", ha="right", fontsize=7.5, color=INK)
    a.text(tp + 40, len(order) - 0.45, f"TP {tp:,.0f}", ha="left", fontsize=7.5, color=OXBLOOD)
    a.set_yticks(y, labels)
    style(a, None)
    a.grid(axis="x", color=RULE, linewidth=0.6); a.grid(axis="y", visible=False)
    a.set_xlim(3500, 10000); a.set_ylim(-0.6, len(order) - 0.1)
    a.set_xlabel("JPY per share", color=MUTED, fontsize=8)
    save(f, "07_football_field", "Valuation range: DCF sits below peer multiples, inside Makita's own history", SRC_MODEL)


def forecast(O):
    o = O["Base"]
    yrs = list(o["is"]["rev"].keys())
    lab = [y.replace("FY20", "FY") + ("A" if int(y[2:]) <= 2026 else "E") for y in yrs]
    x = np.arange(len(yrs))
    f = fig(3.5)
    a1, a2 = f.add_subplot(2, 1, 1), f.add_subplot(2, 1, 2)
    rev = [o["is"]["rev"][y] / 1e3 for y in yrs]
    cols = [GREY if int(y[2:]) <= 2026 else BLUE for y in yrs]
    a1.bar(x, rev, color=cols, width=0.62)
    for xi, v in zip(x, rev):
        a1.text(xi, v + 12, f"{v:,.0f}", ha="center", fontsize=6.5, color=MUTED)
    style(a1, "Revenue, JPY bn"); a1.set_xticks(x, lab); a1.set_ylim(0, 1050); a1.set_xlim(-0.5, len(x) - 0.5)
    a1.text(-0.3, 960, "Actual (grey) / Base forecast (blue)", fontsize=7, color=MUTED)
    nh = sum(int(y[2:]) <= 2026 for y in yrs)
    hist = [o["is"]["opm"][y] * 100 for y in yrs[:nh]]
    a2.plot(x[:nh], hist, color=GREY, linewidth=2, marker="o", markersize=3)
    for name, col in [("Bull", GOLD), ("Base", BLUE), ("Bear", OXBLOOD)]:
        m = [O[name]["is"]["opm"][y] * 100 for y in yrs[nh - 1:]]
        a2.plot(x[nh - 1:], m, color=col, linewidth=2 if name == "Base" else 1.4, marker="o", markersize=3)
        a2.text(x[-1] + 0.2, m[-1], name, color=MUTED, fontsize=7, va="center", clip_on=False)
    a2.axhline(15, color=GREY, linewidth=1, linestyle=(0, (4, 3)))
    a2.text(0, 15.4, "Vision FY2030 target: 15%", fontsize=6.5, color=MUTED)
    style(a2, "Operating margin, %"); a2.set_xticks(x, lab); a2.set_xlim(-0.5, len(x) - 0.5)
    save(f, "08_forecast", "Base case: ~3% revenue growth, operating margin edging up to 14%", SRC_MODEL)


def price_rel():
    from clean_market import prices
    p = prices(ROOT / "data/raw/market/6586.T_prices_daily.csv")
    t = prices(ROOT / "data/raw/market/1306.T_prices_daily.csv")
    df = pd.concat([p["Close"], t["Close"]], axis=1, keys=["mk", "tp"]).loc["2024-10-29":"2026-10-29"].dropna()
    df = df / df.iloc[0] * 100
    f = fig(2.7)
    a = f.add_subplot(1, 1, 1)
    a.plot(df.index, df.mk, color=GOLD, linewidth=1.6)
    a.plot(df.index, df.tp, color=GREY, linewidth=1.2)
    a.text(df.index[-1], df.mk.iloc[-1], "  Makita", color=MUTED, fontsize=7, va="center")
    a.text(df.index[-1], df.tp.iloc[-1], "  TOPIX ETF", color=MUTED, fontsize=7, va="center")
    style(a, "Rebased, 29 Oct 2024 = 100")
    save(f, "09_price_vs_topix", "Two-year share price vs TOPIX: Makita has lagged the market",
         "Source: yfinance (6586.T, 1306.T TOPIX ETF), closing prices.")
    return float(df.mk.iloc[-1]), float(df.tp.iloc[-1])


def tornado():
    r = pd.read_csv(CLEAN / "risk_sensitivities.csv").dropna(subset=["tp_chg_jpy"])
    r = r[r.shock != "Base"].sort_values("tp_chg_jpy")
    f = fig(2.9)
    a = f.add_subplot(1, 1, 1)
    y = np.arange(len(r))
    a.barh(y, r.tp_chg_jpy, color=[OXBLOOD if v < 0 else GOLD for v in r.tp_chg_jpy], height=0.55)
    for yi, v in zip(y, r.tp_chg_jpy):
        a.text(v + (-15 if v < 0 else 15), yi, f"{v:+,.0f}", ha="right" if v < 0 else "left", va="center", fontsize=7, color=MUTED)
    a.set_yticks(y, r.shock.str.replace(" (all years)", "", regex=False))
    a.axvline(0, color=INK, linewidth=0.8)
    style(a, None); a.grid(axis="x", color=RULE, linewidth=0.6); a.grid(axis="y", visible=False)
    a.set_xlabel("Change in 12-month TP, JPY per share (Base TP 5,850)", color=MUTED, fontsize=8)
    a.set_xlim(-800, 400)
    save(f, "10_risk_tornado", "Margins matter more than the yen", SRC_MODEL)


def export_web(O, rel):
    WEB.mkdir(parents=True, exist_ok=True)
    keep = ["rating", "tp", "price", "upside", "tsr", "fv", "ps_g", "ps_x", "wacc", "ke", "g", "mult", "ronic",
            "impl_mult", "impl_g", "sum_pv", "bridge", "pv_tv_g", "ev_g", "tv_share_g", "dps12"]
    out = {s: {**{k: O[s][k] for k in keep}, "is": O[s]["is"], "cf": O[s]["cf"], "bs": O[s]["bs"],
               "drivers": O[s]["drivers"], "dcf": O[s]["dcf"]} for s in O}
    b = O["Base"]
    out["Base"].update({"sensitivity": b["sensitivity"], "football": b["football"], "comps": b["comps"],
                        "peer_stats": b["peer_stats"],
                        "wacc_build": {k: b["mk_" + k] for k in ["rf", "erp", "crp", "bu", "bl", "ke", "kd", "wd", "we", "wacc", "de"]}})
    peers = pd.read_csv(CLEAN / "peers_financials.csv")
    peers = peers[peers.ticker != "6586.T"]
    out["peers"] = [{"ticker": p.ticker, "name": p["name"], "ev_ebitda": p.ev_jpy_m / p.ebitda_jpy_m,
                     "pe": p.market_cap_jpy_m / p.net_income_jpy_m, "ev_sales": p.ev_jpy_m / p.revenue_jpy_m,
                     "ebitda_margin": p.ebitda_jpy_m / p.revenue_jpy_m, "mcap_jpy_bn": p.market_cap_jpy_m / 1e3}
                    for _, p in peers.iterrows()]
    out["risks"] = json.loads((CLEAN / "risk_sensitivities.json").read_text())
    snap = pd.read_csv(CLEAN / "market_snapshot.csv").set_index("item")["value"]
    out["market"] = {"price_date": snap["price_date"], "high_52w": float(snap["high_52w_close"]), "low_52w": float(snap["low_52w_close"]),
                     "market_cap_jpy_m": float(snap["market_cap_jpy_m"]), "rel_2y_makita": rel[0], "rel_2y_topix": rel[1]}
    (WEB / "valuation.json").write_text(json.dumps(out, indent=1, default=str))


def main():
    O = json.loads((CLEAN / "model_outputs.json").read_text())
    football(O["Base"])
    forecast(O)
    rel = price_rel()
    tornado()
    export_web(O, rel)
    print("charts + valuation.json written; 2y rebased Makita / TOPIX:", rel)


if __name__ == "__main__":
    main()
