"""Phase 3: historical ratio analysis and charts.

Reads data/clean, writes:
  data/clean/ratios.csv            one row per metric, one column per FY
  report/charts/*.png              print charts (light palette) for the PDF
  web/public/data/history.json     the same series for the website
Definitions are in the METRICS docstrings below and in report/analysis/03_historical.md.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLEAN, CHARTS = ROOT / "data/clean", ROOT / "report/charts"
WEB = ROOT / "web/public/data"

# validated with the dataviz skill's validate_palette.js (light surface): all six checks pass
GOLD, BLUE, OXBLOOD, GREY = "#A8792A", "#3B6CB0", "#B0463C", "#8C8C8C"
INK, MUTED, RULE = "#1A1A1A", "#5C5C5C", "#D9D6CF"
SOURCE = "Source: Makita Corporation earnings releases (IFRS), student analysis."


def load():
    IS = pd.read_csv(CLEAN / "makita_is.csv", index_col=0)
    BS = pd.read_csv(CLEAN / "makita_bs.csv", index_col=0)
    CF = pd.read_csv(CLEAN / "makita_cf.csv", index_col=0)
    sup = pd.read_csv(CLEAN / "makita_supplementary_wide.csv", index_col=0)
    return IS, BS.fillna(0), CF.fillna(0), sup


def avg(s: pd.Series) -> pd.Series:
    """Average of opening and closing balance (FY2018 uses the 1 Apr 2017 IFRS opening balance)."""
    return (s + s.shift(1)) / 2


def compute():
    IS, BS, CF, sup = load()
    yrs = list(IS.columns)
    bs = BS[["FY2017"] + yrs].T
    i, c = IS.T, CF.T[[x for x in CF.index]]
    b_end = bs.loc[yrs]
    r = pd.DataFrame(index=yrs)

    r["revenue"] = i.revenue
    r["revenue_growth"] = i.revenue.pct_change()
    r["gross_margin"] = i.gross_profit / i.revenue
    r["sga_pct"] = -i.sga_net / i.revenue
    r["op_margin"] = i.operating_profit / i.revenue
    r["ebitda"] = i.operating_profit + c.cfo_da            # IFRS 16 basis (CF D&A incl. right-of-use)
    r["ebitda_margin"] = r.ebitda / i.revenue
    r["net_income"] = i.ni_parent
    r["net_margin"] = i.ni_parent / i.revenue
    r["effective_tax_rate"] = -i.income_tax / i.pbt
    r["eps"] = i.ni_parent / sup.loc["avg_shares", yrs].astype(float) * 1e6
    r["eps_growth"] = r.eps.pct_change()

    # DuPont on parent equity: ROE = net margin x asset turnover x equity multiplier
    avg_assets, avg_eq = avg(bs.total_assets).loc[yrs], avg(bs.equity_parent).loc[yrs]
    r["asset_turnover"] = i.revenue / avg_assets
    r["equity_multiplier"] = avg_assets / avg_eq
    r["roe"] = i.ni_parent / avg_eq
    r["roe_dupont_check"] = r.net_margin * r.asset_turnover * r.equity_multiplier - r.roe

    # ROIC, operating approach: invested capital = operating NWC + PP&E + intangibles
    nwc = (bs.receivables + bs.inventories + bs.other_current_assets
           - bs.payables - bs.other_current_liab - bs.provisions_cur)
    ic = nwc + bs.ppe + bs.intangibles
    r["invested_capital"] = ic.loc[yrs]
    r["nopat"] = i.operating_profit * (1 - r.effective_tax_rate)
    r["roic"] = r.nopat / avg(ic).loc[yrs]
    r["ic_turnover"] = i.revenue / avg(ic).loc[yrs]

    # working capital days (year-end balances; averages would lag the FY2022 build)
    r["dso"] = b_end.receivables / i.revenue * 365
    r["dio"] = b_end.inventories / -i.cost_of_sales * 365
    r["dpo"] = b_end.payables / -i.cost_of_sales * 365
    r["cash_conversion_cycle"] = r.dso + r.dio - r.dpo
    r["inventory"] = b_end.inventories

    # balance sheet and coverage
    leases = b_end.other_fin_liab_cur + b_end.other_fin_liab_nc   # mostly IFRS 16 lease liabilities from FY2020
    r["gross_debt_incl_leases"] = b_end.borrowings_cur + b_end.get("borrowings_nc", 0) + leases
    r["cash_and_deposits"] = b_end.cash + b_end.other_fin_assets_cur
    r["net_cash"] = r.cash_and_deposits - r.gross_debt_incl_leases
    r["net_cash_to_equity"] = r.net_cash / b_end.equity_parent
    r["equity_ratio"] = b_end.equity_parent / b_end.total_assets
    r["interest_coverage"] = i.operating_profit / -c.cfo_interest_paid

    # cash flow
    r["cfo"] = c.cfo
    r["capex"] = -c.capex
    r["fcf"] = c.cfo + c.capex + c.lease_repayments          # after lease principal (IFRS 16 neutral)
    r["fcf_conversion"] = r.fcf / i.ni_parent
    r["capex_to_sales"] = r.capex / i.revenue
    r["capex_to_da_ex_rou"] = r.capex / sup.loc["da_ex_rou", yrs]
    r["shareholder_returns"] = -(c.dividends_paid + c.buybacks_net)
    r["total_payout"] = r.shareholder_returns / i.ni_parent
    r["rnd_to_sales"] = sup.loc["rnd", yrs] / i.revenue
    r["usdjpy"], r["eurjpy"] = sup.loc["fx_usdjpy", yrs], sup.loc["fx_eurjpy", yrs]

    out = r.T
    out.to_csv(CLEAN / "ratios.csv")
    return out


def style(ax, ylabel=None):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(axis="y", color=RULE, linewidth=0.6)
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=8)


def fig(h=3.1):
    plt.rcParams.update({"font.family": "Carlito", "font.size": 8.5})
    return plt.figure(figsize=(6.6, h), dpi=200)


def save(f, name, title, source=SOURCE):
    f.suptitle(title, x=0.01, ha="left", fontsize=10, fontweight="bold", color=INK)
    f.text(0.01, 0.01, source, fontsize=6.5, color=MUTED)
    f.tight_layout(rect=(0, 0.04, 1, 0.94))
    CHARTS.mkdir(parents=True, exist_ok=True)
    f.savefig(CHARTS / f"{name}.png")
    plt.close(f)


def labels(r):
    return [c.replace("FY20", "FY") for c in r.columns]


def charts(r):
    x = np.arange(r.shape[1])
    lab = labels(r)

    # 1. revenue (bars) and margins (lines) as two stacked panels - no dual axis
    f = fig(3.6)
    a1, a2 = f.add_subplot(2, 1, 1), f.add_subplot(2, 1, 2, sharex=None)
    a1.bar(x, r.loc["revenue"] / 1e3, color=GOLD, width=0.62)
    for xi, v in zip(x, r.loc["revenue"] / 1e3):
        a1.text(xi, v + 12, f"{v:,.0f}", ha="center", fontsize=6.5, color=MUTED)
    style(a1, "Revenue, JPY bn"); a1.set_xticks(x, lab); a1.set_ylim(0, 900); a1.set_xlim(-0.5, len(x) + 0.6)
    for k, col, nm in [("gross_margin", GREY, "Gross"), ("ebitda_margin", BLUE, "EBITDA"), ("op_margin", GOLD, "Operating")]:
        a2.plot(x, r.loc[k] * 100, color=col, linewidth=2, marker="o", markersize=3.5)
        a2.text(x[-1] + 0.15, r.loc[k].iloc[-1] * 100, nm, color=MUTED, fontsize=7, va="center")
    style(a2, "Margin, %"); a2.set_xticks(x, lab); a2.set_xlim(-0.5, len(x) + 0.6)
    save(f, "01_revenue_margins", "Revenue grew 6.3% a year; operating margin is still below the FY2018 peak")

    # 2. inventory days vs operating margin, stacked panels
    f = fig(3.4)
    a1, a2 = f.add_subplot(2, 1, 1), f.add_subplot(2, 1, 2)
    a1.bar(x, r.loc["dio"], color=OXBLOOD, width=0.62)
    for xi, v in zip(x, r.loc["dio"]):
        a1.text(xi, v + 6, f"{v:.0f}", ha="center", fontsize=6.5, color=MUTED)
    style(a1, "Inventory days"); a1.set_xticks(x, lab); a1.set_ylim(0, 400); a1.set_xlim(-0.5, len(x) - 0.5)
    a2.plot(x, r.loc["op_margin"] * 100, color=GOLD, linewidth=2, marker="o", markersize=3.5)
    style(a2, "Operating margin, %"); a2.set_xticks(x, lab); a2.set_xlim(-0.5, len(x) - 0.5)
    save(f, "02_inventory_cycle", "Margins collapsed after the FY2022 inventory build; days are rising again")

    # 3. revenue mix by customer region (3 named regions + rest in grey)
    geo = pd.read_csv(CLEAN / "makita_geo_revenue.csv")
    geo = geo[(geo.release_fy == geo.fy) | ((geo.fy == 2018) & (geo.release_fy == 2019))]
    g = geo.pivot(index="fy", columns="region", values="value")
    share = g.div(g["Total"], axis=0) * 100
    rest = 100 - share[["Europe", "Japan", "North America"]].sum(axis=1)
    f = fig(3.0)
    a = f.add_subplot(1, 1, 1)
    bottom = np.zeros(len(share))
    for k, col in [("Europe", GOLD), ("Japan", BLUE), ("North America", OXBLOOD)]:
        a.bar(x, share[k], bottom=bottom, color=col, width=0.62, edgecolor="white", linewidth=1)
        a.text(x[-1] + 0.4, bottom[-1] + share[k].iloc[-1] / 2, f"{k} {share[k].iloc[-1]:.0f}%", fontsize=7, color=MUTED, va="center")
        bottom += share[k].values
    a.bar(x, rest, bottom=bottom, color=GREY, width=0.62, edgecolor="white", linewidth=1, alpha=0.55)
    a.text(x[-1] + 0.4, bottom[-1] + rest.iloc[-1] / 2, f"Rest of world {rest.iloc[-1]:.0f}%", fontsize=7, color=MUTED, va="center")
    style(a, "Share of revenue, %"); a.set_xticks(x, lab); a.set_xlim(-0.5, len(x) + 1.6); a.set_ylim(0, 100)
    save(f, "03_region_mix", "Europe is now half of revenue; North America has shrunk to 10%")

    # 4. ROE (DuPont) and ROIC
    f = fig(3.0)
    a = f.add_subplot(1, 1, 1)
    for k, col, nm in [("roic", GOLD, "ROIC (operating)"), ("roe", BLUE, "ROE")]:
        a.plot(x, r.loc[k] * 100, color=col, linewidth=2, marker="o", markersize=3.5)
        a.text(x[-1] + 0.15, r.loc[k].iloc[-1] * 100, nm, color=MUTED, fontsize=7, va="center")
    a.axhline(11, color=GREY, linewidth=1, linestyle=(0, (4, 3)))
    a.text(0, 11.4, "Company ROE target 11% (FY2030)", fontsize=6.5, color=MUTED)
    style(a, "%"); a.set_xticks(x, lab); a.set_xlim(-0.5, len(x) + 1.2)
    save(f, "04_returns", "Returns on operating capital are high; ROE is diluted by surplus equity")

    # 5. FCF vs net income
    f = fig(3.0)
    a = f.add_subplot(1, 1, 1)
    w = 0.36
    a.bar(x - w / 2, r.loc["fcf"] / 1e3, width=w, color=GOLD, label="Free cash flow (after leases)")
    a.bar(x + w / 2, r.loc["net_income"] / 1e3, width=w, color=BLUE, label="Net income (parent)")
    a.axhline(0, color=INK, linewidth=0.8)
    style(a, "JPY bn"); a.set_xticks(x, lab)
    a.legend(frameon=False, fontsize=7, loc="upper left")
    save(f, "05_fcf_vs_ni", "Cash conversion swings with inventory: FCF -167bn in FY2022, +215bn in FY2024")

    # 6. aftermarket share
    p = pd.read_csv(CLEAN / "makita_product_mix.csv")
    p = p[(p.release_fy == p.fy) | ((p.fy == 2018) & (p.release_fy == 2019))].pivot(index="fy", columns="category", values="value")
    sh = p.parts_repairs_accessories / p.total * 100
    f = fig(2.6)
    a = f.add_subplot(1, 1, 1)
    a.plot(x, sh.values, color=GOLD, linewidth=2, marker="o", markersize=3.5)
    for xi, v in zip(x, sh.values):
        a.text(xi, v + 0.35, f"{v:.1f}", ha="center", fontsize=6.5, color=MUTED)
    style(a, "% of revenue"); a.set_xticks(x, lab); a.set_ylim(14, 25)
    save(f, "06_aftermarket", "Parts, repairs and accessories: a rising, steadier share of sales")
    return share, sh


def export_web(r, share, aftermarket):
    WEB.mkdir(parents=True, exist_ok=True)
    keep = ["revenue", "revenue_growth", "gross_margin", "op_margin", "ebitda_margin", "net_margin", "eps", "roe",
            "roic", "asset_turnover", "equity_multiplier", "dio", "dso", "dpo", "cash_conversion_cycle", "fcf",
            "cfo", "capex", "net_cash", "equity_ratio", "fcf_conversion", "capex_to_sales", "total_payout"]
    d = {"years": list(r.columns),
         "metrics": {k: [None if pd.isna(v) else round(float(v), 6) for v in r.loc[k]] for k in keep},
         "region_share": {k: [round(float(v), 2) for v in share[k]] for k in ["Europe", "Japan", "North America"]},
         "aftermarket_share": [round(float(v), 2) for v in aftermarket.values],
         "sga_pct": [round(float(v), 6) for v in r.loc["sga_pct"]],
         "source": SOURCE}
    (WEB / "history.json").write_text(json.dumps(d, indent=1))


def main():
    r = compute()
    assert r.loc["roe_dupont_check"].abs().max() < 1e-9, "DuPont does not reconcile"
    share, aft = charts(r)
    export_web(r, share, aft)
    pd.set_option("display.width", 250)
    show = ["revenue_growth", "gross_margin", "sga_pct", "op_margin", "ebitda_margin", "net_margin", "roe", "net_margin",
            "asset_turnover", "equity_multiplier", "roic", "ic_turnover", "dso", "dio", "dpo", "cash_conversion_cycle",
            "net_cash", "net_cash_to_equity", "equity_ratio", "interest_coverage", "fcf", "fcf_conversion",
            "capex_to_sales", "capex_to_da_ex_rou", "total_payout", "rnd_to_sales", "effective_tax_rate", "eps"]
    print(r.loc[show].astype(float).round(3).to_string())


if __name__ == "__main__":
    main()
