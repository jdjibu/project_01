"""Phase 6: quantify key risks by re-running the full Excel model (build -> LibreOffice recalc) with one
driver shocked at a time, Base scenario. Writes data/clean/risk_sensitivities.csv and .json."""
import json
import shutil
from pathlib import Path

import pandas as pd

from build_model import CLEAN, MODEL, TS, SV, build, load_hist, read_outputs
from recalc import recalc

BASE = {k: v["Base"] for k, _, _, _, v, _ in TS}
SVB = {k: (b, u, e) for k, _, _, b, u, e, _ in SV}
Q1 = {"fx_usd": 159.57, "fx_eur": 185.41}            # 1Q FY2027 actual averages (release p.10)
SPOT = {"fx_usd": 157.82, "fx_eur": 176.03}          # 29 Oct 2026


def fx_shock(m):
    """Yen move from today: FY2027 keeps the 1Q actual and applies the shock to the remaining 3 quarters."""
    return {k: {"Base": [(Q1[k] + 3 * SPOT[k] * m) / 4] + [SPOT[k] * m] * 4} for k in Q1}


def add(key, delta, years=5):
    return {key: {"Base": [v + (delta if i < years else 0) for i, v in enumerate(BASE[key])]}}


SHOCKS = {
    "Base": {},
    "Yen +10% vs USD and EUR": fx_shock(1 / 1.1),
    "Yen -10% vs USD and EUR": fx_shock(1.1),
    "Gross margin -200bp (all years)": add("gm", -0.02),
    "Construction downturn: local-currency growth -3pp in FY2027-28":
        {k: {"Base": [v - (0.03 if i < 2 else 0) for i, v in enumerate(BASE[k])]} for k in ["lcg_eur", "lcg_jpn", "lcg_na", "lcg_row"]},
    "Inventory build: +30 inventory days (all years)": add("dio", 30),
    "SG&A +100bp of revenue (all years)": add("sga", 0.01),
    "Terminal growth -0.5pp": {"tg": tuple(x - 0.005 for x in SVB["tg"])},
}


def main():
    d = load_hist()
    tmp = MODEL / "_risk"
    tmp.mkdir(exist_ok=True)
    rows = []
    for name, ov in SHOCKS.items():
        raw, calc = tmp / "r.xlsx", tmp / "r_calc.xlsx"
        refs = build(d, 1, raw, overrides=ov)
        recalc(raw, calc)
        o = read_outputs(calc, refs)
        # shocks hold the exit multiple fixed (all else equal), so only the TV-consistency flag may trip
        hard = [c for c in o["check_failures"] if not c.startswith("Exit-multiple implied growth")]
        assert not hard, (name, hard)
        rows.append({"shock": name, "eps_fy2027": o["is"]["eps"]["FY2027"], "eps_fy2028": o["is"]["eps"]["FY2028"],
                     "op_fy2028": o["is"]["op"]["FY2028"], "fair_value": o["fv"], "tp": o["tp"], "upside": o["upside"],
                     "rating": o["rating"],
                     "tv_consistency_flag": bool(o["check_failures"])})
        print(name, round(o["is"]["eps"]["FY2028"], 1), o["tp"], o["rating"])
    shutil.rmtree(tmp)
    r = pd.DataFrame(rows)
    b = r.iloc[0]
    for k in ["eps_fy2027", "eps_fy2028", "op_fy2028", "fair_value"]:
        r[k + "_chg"] = r[k] / b[k] - 1
    r["tp_chg_jpy"] = r.tp - b.tp

    # tariff risk: outside the model (needs a sourcing split Makita does not disclose for US-bound units)
    base = json.loads((CLEAN / "model_outputs.json").read_text())["Base"]
    na_rev = base["drivers"]["na"]["FY2028"]
    cogs_ratio = 1 - base["is"]["gm"]["FY2028"]
    china_share, tariff, pass_through, tax = 0.515, 0.25, 0.5, 0.27
    cost = na_rev * cogs_ratio * china_share * tariff * (1 - pass_through)
    eps_hit = cost * (1 - tax) / (base["is"]["ni"]["FY2028"] / base["is"]["eps"]["FY2028"]) / base["is"]["eps"]["FY2028"]
    tariff_row = {"shock": "US tariff: 25% on China-made goods sold in North America, 50% passed on (outside model)",
                  "op_fy2028": base["is"]["op"]["FY2028"] - cost, "op_fy2028_chg": -cost / base["is"]["op"]["FY2028"],
                  "eps_fy2028_chg": -cost * (1 - tax) / base["is"]["ni"]["FY2028"],
                  "note": f"NA revenue FY2028E {na_rev:,.0f} x COGS {cogs_ratio:.1%} x China share {china_share:.1%} "
                          f"(group unit share, Makita Report 2026) x 25% x (1 - 50% pass-through) = JPY {cost:,.0f}m"}
    r = pd.concat([r, pd.DataFrame([tariff_row])], ignore_index=True)
    r.to_csv(CLEAN / "risk_sensitivities.csv", index=False)
    (CLEAN / "risk_sensitivities.json").write_text(r.to_json(orient="records", indent=1))
    print(r[["shock", "eps_fy2028_chg", "op_fy2028_chg", "tp", "tp_chg_jpy", "rating"]].round(3).to_string())


if __name__ == "__main__":
    main()
