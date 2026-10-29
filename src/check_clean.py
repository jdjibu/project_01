"""Accounting integrity checks on data/clean Makita tables. Writes data/clean/checks_makita.csv
and exits non-zero if any check fails (tolerance: 2 JPY m for rounding)."""
import sys
from pathlib import Path

import pandas as pd

CLEAN = Path(__file__).resolve().parents[1] / "data/clean"
TOL = 2.0


def main():
    IS = pd.read_csv(CLEAN / "makita_is.csv", index_col=0).fillna(0)
    BS = pd.read_csv(CLEAN / "makita_bs.csv", index_col=0).fillna(0)
    CF = pd.read_csv(CLEAN / "makita_cf.csv", index_col=0).fillna(0)
    seg = pd.read_csv(CLEAN / "makita_segments.csv")
    geo = pd.read_csv(CLEAN / "makita_geo_revenue.csv")
    prod = pd.read_csv(CLEAN / "makita_product_mix.csv")
    sup = pd.read_csv(CLEAN / "makita_supplementary_wide.csv", index_col=0)
    # own-release values; FY2018 only exists as the comparative in the FY3/2019 release
    own = lambda d: d[(d.release_fy == d.fy) | ((d.fy == 2018) & (d.release_fy == 2019))]
    seg, geo, prod = own(seg), own(geo), own(prod)

    res = []

    def chk(name, fy, lhs, rhs):
        res.append({"check": name, "fy": fy, "lhs": lhs, "rhs": rhs, "diff": lhs - rhs, "pass": abs(lhs - rhs) <= TOL})

    b = lambda i, c: BS.at[i, c] if i in BS.index else 0.0
    for c in BS.columns:
        chk("BS: current assets = sum of lines", c, b("total_current_assets", c),
            sum(b(i, c) for i in ["cash", "receivables", "inventories", "other_fin_assets_cur", "other_current_assets"]))
        chk("BS: non-current assets = sum of lines", c, b("total_noncurrent_assets", c),
            sum(b(i, c) for i in ["ppe", "intangibles", "other_fin_assets_nc", "retirement_benefit_assets",
                                  "deferred_tax_assets", "other_noncurrent_assets"]))
        chk("BS: total assets = CA + NCA", c, b("total_assets", c), b("total_current_assets", c) + b("total_noncurrent_assets", c))
        chk("BS: current liabilities = sum of lines", c, b("total_current_liab", c),
            sum(b(i, c) for i in ["payables", "borrowings_cur", "other_fin_liab_cur", "tax_payable_cur",
                                  "provisions_cur", "other_current_liab"]))
        chk("BS: non-current liabilities = sum of lines", c, b("total_noncurrent_liab", c),
            sum(b(i, c) for i in ["borrowings_nc", "retirement_benefit_liab", "other_fin_liab_nc", "provisions_nc",
                                  "deferred_tax_liab", "tax_payable_nc", "other_noncurrent_liab"]))
        chk("BS: total liabilities = CL + NCL", c, b("total_liabilities", c), b("total_current_liab", c) + b("total_noncurrent_liab", c))
        chk("BS: parent equity = sum of components", c, b("equity_parent", c),
            sum(b(i, c) for i in ["share_capital", "capital_surplus", "retained_earnings", "treasury_shares", "other_components_equity"]))
        chk("BS: total equity = parent + NCI", c, b("total_equity", c), b("equity_parent", c) + b("nci", c))
        chk("BS: assets = liabilities + equity", c, b("total_assets", c), b("total_liabilities", c) + b("total_equity", c))

    for c in IS.columns:
        i = IS[c]
        chk("IS: gross profit = revenue + COGS", c, i.gross_profit, i.revenue + i.cost_of_sales)
        chk("IS: operating profit = GP + SG&A", c, i.operating_profit, i.gross_profit + i.sga_net)
        chk("IS: PBT = OP + fin income + fin expense", c, i.pbt, i.operating_profit + i.financial_income + i.financial_expenses)
        chk("IS: profit = PBT + tax", c, i.profit, i.pbt + i.income_tax)
        chk("IS: profit = parent + NCI", c, i.profit, i.ni_parent + i.ni_nci)

    op_lines = ["cfo_profit", "cfo_da", "cfo_tax_expense", "cfo_fin_income_exp", "cfo_loss_gain_ppe", "cfo_chg_receivables",
                "cfo_chg_inventories", "cfo_chg_payables", "cfo_chg_retirement", "cfo_chg_guarantee_dep", "cfo_other"]
    for c in CF.columns:
        f = CF[c]
        chk("CF: operating subtotal = sum of lines", c, f.cfo_subtotal, f[op_lines].sum())
        chk("CF: CFO = subtotal + interest/div/tax", c, f.cfo, f.cfo_subtotal + f.cfo_dividends_received
            + f.cfo_interest_received + f.cfo_interest_paid + f.cfo_taxes_paid)
        chk("CF: CFI = sum of lines", c, f.cfi, f[["capex", "asset_sale_proceeds", "purchase_investments", "investment_proceeds",
                                                     "time_deposit_payments", "time_deposit_withdrawals", "cfi_other"]].sum())
        chk("CF: CFF = sum of lines", c, f.cff, f[[x for x in ["chg_st_borrowings", "chg_lt_borrowings", "buybacks_net",
                                                               "dividends_paid", "lease_repayments", "cff_other"] if x in f]].sum())
        chk("CF: net change = CFO + CFI + CFF + FX", c, f.net_change_cash, f.cfo + f.cfi + f.cff + f.fx_effect_cash)
        chk("CF: end cash = begin + change", c, f.cash_end, f.cash_begin + f.net_change_cash)
        chk("CF->BS: end cash = BS cash", c, f.cash_end, b("cash", c))
        prev = f"FY{int(c[2:]) - 1}"
        if prev in BS.columns:
            chk("CF->BS: begin cash = prior BS cash", c, f.cash_begin, b("cash", prev))
        chk("CF: profit line = IS profit", c, f.cfo_profit, IS.at["profit", c])
        chk("Supp: disclosed capex = CF purchase of non-current assets", c, sup.at["capex_disclosed", c], -f.capex)

    for fy, g in seg.groupby("fy"):
        c = f"FY{fy}"
        e = g[g.item == "external_revenue"].set_index("segment")["value"]
        o = g[g.item == "operating_profit"].set_index("segment")["value"]
        chk("Segments: external revenue sums to consolidated", c, e[["Subtotal", "Other", "Eliminations"]].sum(), e["Consolidated"])
        chk("Segments: consolidated = IS revenue", c, e["Consolidated"], IS.at["revenue", c])
        chk("Segments: OP sums to consolidated", c, o[["Subtotal", "Other", "Eliminations"]].sum(), o["Consolidated"])
        chk("Segments: consolidated OP = IS OP", c, o["Consolidated"], IS.at["operating_profit", c])
    for fy, g in geo.groupby("fy"):
        c = f"FY{fy}"
        v = g.set_index("region")["value"]
        chk("Geo: regions sum to total", c, v.drop("Total").sum(), v["Total"])
        chk("Geo: total = IS revenue", c, v["Total"], IS.at["revenue", c])
    for fy, g in prod.groupby("fy"):
        c = f"FY{fy}"
        v = g.set_index("category")["value"]
        chk("Product: categories sum to total", c, v.finished_goods + v.parts_repairs_accessories, v.total)
        chk("Product: total = IS revenue", c, v.total, IS.at["revenue", c])

    out = pd.DataFrame(res)
    out.to_csv(CLEAN / "checks_makita.csv", index=False)
    out["pass"] = out["pass"].astype(bool)
    fails = out.loc[~out["pass"].to_numpy()]
    print(f"{len(out)} checks, {len(fails)} failed")
    if len(fails):
        print(fails.to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
