"""Copy deliverables into the website and write web/public/data/facts.json: every figure quoted in the site's text,
with its display string and source (shown on hover). history.json and valuation.json are written by
historical.py and valuation_charts.py."""
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN, WEB = ROOT / "data/clean", ROOT / "web/public"


def main():
    (WEB / "downloads").mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "report/Makita_6586_initiation.pdf", WEB / "downloads/Makita_6586_initiation.pdf")
    shutil.copy(ROOT / "model/Makita_6586_model.xlsx", WEB / "downloads/Makita_6586_model.xlsx")

    O = json.loads((CLEAN / "model_outputs.json").read_text())["Base"]
    R = pd.read_csv(CLEAN / "ratios.csv", index_col=0)
    geo = pd.read_csv(CLEAN / "makita_geo_revenue.csv").query("fy == 2026 and release_fy == 2026").set_index("region")["value"]
    chk = pd.read_csv(CLEAN / "checks_makita.csv")
    rel, fy26 = "Makita FY3/2026 earnings release", "FY3/2026"
    r = lambda k, y="FY2026": float(R.at[k, y])
    F = {
        "revenue": (f"¥{O['is']['rev']['FY2026'] / 1e3:,.1f}bn", f"{rel}, p.10 (consolidated statement of profit or loss)"),
        "op_margin": (f"{r('op_margin') * 100:.1f}%", f"{rel}, p.10; operating profit / revenue"),
        "gross_margin": (f"{r('gross_margin') * 100:.1f}%", f"{rel}, p.10"),
        "gross_margin_18": (f"{r('gross_margin', 'FY2018') * 100:.1f}%", "Makita FY3/2019 release (IFRS comparative for FY3/2018)"),
        "sga_18": (f"{r('sga_pct', 'FY2018') * 100:.1f}%", "Makita FY3/2019 release; SG&A / revenue"),
        "sga_26": (f"{r('sga_pct') * 100:.1f}%", f"{rel}; SG&A / revenue"),
        "dio": (f"{r('dio'):.0f} days", f"{rel}: inventories / cost of sales x 365 (year-end)"),
        "dio_22": (f"{r('dio', 'FY2022'):.0f} days", "Makita FY3/2022 release: inventories / cost of sales x 365"),
        "dio_24": (f"{r('dio', 'FY2024'):.0f} days", "Makita FY3/2024 release"),
        "gm_23": (f"{r('gross_margin', 'FY2023') * 100:.1f}%", "Makita FY3/2023 release"),
        "net_cash": (f"¥{r('net_cash') / 1e3:,.1f}bn", f"{rel}: cash + time deposits - borrowings - lease liabilities"),
        "roe": (f"{r('roe') * 100:.1f}%", f"{rel}: profit to owners / average parent equity"),
        "roic": (f"{r('roic') * 100:.1f}%", "NOPAT / average (operating NWC + PP&E + intangibles); data/clean/ratios.csv"),
        "europe_share": (f"{geo['Europe'] / geo['Total'] * 100:.0f}%", f"{rel}, p.16 (revenue by customer location)"),
        "na_share": (f"{geo['North America'] / geo['Total'] * 100:.0f}%", f"{rel}, p.16"),
        "aftermarket": ("22.8%", f"{rel}, p.15 (revenue by product category)"),
        "aftermarket_18": ("16.4%", "Makita FY3/2019 release (FY3/2018 comparative)"),
        "ev_ebitda": (f"{O['comps']['ev_ebitda']:.1f}x", "Model: Comps sheet; EV (incl. leases) / LTM EBITDA to Jun 2026"),
        "own_med": (f"{O['comps']['own_med']:.1f}x", "Model: Makita EV/EBITDA at each FY end, FY2019-26 median (makita_hist_multiples.csv)"),
        "peer_med": (f"{O['peer_stats']['Median|EV/EBITDA']:.1f}x", "Model: Comps sheet, peer median (last reported FY)"),
        "fcf_conv": (f"{R.loc['fcf'].sum() / R.loc['net_income'].sum() * 100:.0f}%", "Cumulative FY2018-26 FCF / net income; ratios.csv"),
        "china_share": ("51.5%", "Makita Report 2026, p.23 (production units, FYE2026)"),
        "q1_jpy": ("+10.7%", "Makita 1Q FY3/2027 release, p.3"),
        "milwaukee": ("+7.9%", "Techtronic Industries 2025 results release (local currency)"),
        "europe_lc_26": (f"{O['drivers']['eu_lc']['FY2026'] * 100:+.1f}%",
                         "Model Drivers sheet: Europe revenue growth in JPY (+4.9%) stripped of the EUR/JPY change (+6.6%)"),
        "target_margin": ("15%", "Makita Report 2026, p.19 (Vision FY2030)"),
        "target_roe": ("11%", "Makita Report 2026, p.19 (Vision FY2030)"),
        "rf": (f"{O['mk_rf'] * 100:.2f}%", "Ministry of Finance Japan, 10Y JGB, 28 Oct 2026"),
        "crp": (f"{O['mk_crp'] * 100:.2f}%", "Damodaran regional CRPs weighted by Makita revenue (crp_weighted.csv)"),
        "data_checks": (f"{int(chk['pass'].astype(bool).sum())}", "src/check_clean.py: statement subtotals, balance, cash ties, segment sums"),
    }
    facts = {k: {"display": v[0], "source": v[1]} for k, v in F.items()}
    (WEB / "data/facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("web data + downloads updated:", len(facts), "facts")


if __name__ == "__main__":
    main()
