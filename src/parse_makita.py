"""Parse Makita's English Kessan Tanshin PDFs (data/raw/makita/releases) into tidy CSVs.

Output (data/clean/):
  makita_statements_long.csv  every parsed line: source file, statement, item, period, value (JPY m)
  makita_is.csv / makita_bs.csv / makita_cf.csv   wide, one column per fiscal year (FY = year ending March)
  makita_segments.csv        segment revenue / OP by selling-entity location
  makita_geo_revenue.csv     revenue by customer location
  makita_product_mix.csv     finished goods vs parts, repairs and accessories
  makita_supplementary.csv   capex, D&A (ex right-of-use), R&D, FX rates, shares, DPS, guidance
  makita_restatements.csv    prior-year column in release t+1 vs current-year column in release t
  makita_quarterly.csv       1Q statements used for the LTM bridge

Rule: the current-year column of each year's own release is the primary value. FY3/2018 only exists
as the IFRS comparative in the FY3/2019 release (and the IFRS opening balance sheet at 1 Apr 2017).
"""
import re
from pathlib import Path

import pandas as pd

from pdf_lines import pdf_text, rows, section

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/makita/releases"
OUT = ROOT / "data/clean"

ANNUAL = {  # fiscal year -> file
    2019: "201903e.pdf", 2020: "202003e.pdf", 2021: "financial_results202103.pdf",
    2022: "financial_results202203.pdf", 2023: "financial_results202303.pdf",
    2024: "financial_results202403.pdf", 2025: "financial_results202503.pdf",
    2026: "financial_results202603.pdf",
}
QUARTERLY = {"1Q2026": "financial_results202506.pdf", "1Q2027": "financial_results202606.pdf"}

# (context or None, regex on lower-cased label) -> canonical item. First match wins.
BS_MAP = [
    ("ca", r"^cash and cash equivalents$", "cash"),
    ("ca", r"^trade (receivables )?and other receivables$", "receivables"),
    ("ca", r"^inventories$", "inventories"),
    ("ca", r"^other financial assets$", "other_fin_assets_cur"),
    ("ca", r"other current assets$", "other_current_assets"),
    ("ca", r"^total current assets$", "total_current_assets"),
    ("nca", r"^property, plant and equipment", "ppe"),
    ("nca", r"^goodwill and intangible", "intangibles"),
    ("nca", r"^other financial assets$", "other_fin_assets_nc"),
    ("nca", r"retirement benefit asset", "retirement_benefit_assets"),
    ("nca", r"^deferred (income taxes|tax assets)$", "deferred_tax_assets"),
    ("nca", r"^other non-current assets$", "other_noncurrent_assets"),
    ("nca", r"^total non-current assets$", "total_noncurrent_assets"),
    (None, r"^total assets$", "total_assets"),
    ("cl", r"^trade (payables )?and other payables$", "payables"),
    ("cl", r"^borrowings$", "borrowings_cur"),
    ("cl", r"^other financial liabilities$", "other_fin_liab_cur"),
    ("cl", r"^income taxes payable$", "tax_payable_cur"),
    ("cl", r"^provisions$", "provisions_cur"),
    ("cl", r"^other current liabilities$", "other_current_liab"),
    ("cl", r"^total current liabilities$", "total_current_liab"),
    ("ncl", r"^borrowings$", "borrowings_nc"),
    ("ncl", r"^retirement benefit liabilities$", "retirement_benefit_liab"),
    ("ncl", r"^other financial liabilities$", "other_fin_liab_nc"),
    ("ncl", r"^provisions$", "provisions_nc"),
    ("ncl", r"^deferred (income taxes|tax liabilities)$", "deferred_tax_liab"),
    ("ncl", r"^income taxes payable$", "tax_payable_nc"),
    ("ncl", r"^other non-current liabilities$", "other_noncurrent_liab"),
    ("ncl", r"^total non-current liabilities$", "total_noncurrent_liab"),
    (None, r"^total liabilities$", "total_liabilities"),
    ("eq", r"^(common stock|share capital)$", "share_capital"),
    ("eq", r"^(additional paid-in capital|capital surplus)$", "capital_surplus"),
    ("eq", r"^retained earnings$", "retained_earnings"),
    ("eq", r"^treasury (shares|stock, at cost)$", "treasury_shares"),
    ("eq", r"^other components of equity$", "other_components_equity"),
    ("eq", r"^total equity attributable to owners", "equity_parent"),
    ("eq", r"^non-controlling interest", "nci"),
    ("eq", r"^total equity$", "total_equity"),
    (None, r"^total liabilities and equity$", "total_liab_equity"),
]
BS_CONTEXT = [(r"^current assets", "ca"), (r"^non-current assets", "nca"),
              (r"^current liabilities", "cl"), (r"^non-current liabilities", "ncl"),
              (r"^equity$", "eq")]

IS_MAP = [
    (r"^revenue$", "revenue"),
    (r"^cost of sales$", "cost_of_sales"),
    (r"^gross profit$", "gross_profit"),
    (r"^selling, general", "sga_net"),
    (r"^operating profit$", "operating_profit"),
    (r"^financial income$", "financial_income"),
    (r"^financial expenses$", "financial_expenses"),
    (r"^profit before income taxes$", "pbt"),
    (r"^income tax expenses$", "income_tax"),
    (r"^profit$", "profit"),
    (r"^owners of the parent$", "ni_parent"),
    (r"^non-controlling interests$", "ni_nci"),
]

CF_MAP = [  # context: op / inv / fin / end
    ("op", r"^profit$", "cfo_profit"),
    ("op", r"^depreciation and amortization$", "cfo_da"),
    ("op", r"^income tax expenses$", "cfo_tax_expense"),
    ("op", r"^financial income and expenses$", "cfo_fin_income_exp"),
    ("op", r"^loss \(gain\) on sales", "cfo_loss_gain_ppe"),
    ("op", r"receivables$", "cfo_chg_receivables"),
    ("op", r"inventories$", "cfo_chg_inventories"),
    ("op", r"payables$", "cfo_chg_payables"),
    ("op", r"retirement benefit", "cfo_chg_retirement"),
    ("op", r"guarantee deposits$", "cfo_chg_guarantee_dep"),
    ("op", r"^other$", "cfo_other"),
    ("op", r"^subtotal$", "cfo_subtotal"),
    ("op", r"^dividends received$", "cfo_dividends_received"),
    ("op", r"^interest received$", "cfo_interest_received"),
    ("op", r"^interest paid$", "cfo_interest_paid"),
    ("op", r"^income taxes paid$", "cfo_taxes_paid"),
    ("op", r"^cash flows from operating activities$", "cfo"),
    ("inv", r"^purchase of non-current assets$", "capex"),
    ("inv", r"^proceeds from sales? of non-current assets$", "asset_sale_proceeds"),
    ("inv", r"^purchase of investments$", "purchase_investments"),
    ("inv", r"^proceeds from sales? and redemption", "investment_proceeds"),
    ("inv", r"^payments into time deposits$", "time_deposit_payments"),
    ("inv", r"^proceeds from withdrawal of time deposits$", "time_deposit_withdrawals"),
    ("inv", r"^other$", "cfi_other"),
    ("inv", r"^cash flows from investing activities$", "cfi"),
    ("fin", r"short-term borrowings", "chg_st_borrowings"),
    ("fin", r"long-term (debt|borrowings)", "chg_lt_borrowings"),
    ("fin", r"treasury (shares|stock)", "buybacks_net"),
    ("fin", r"^cash dividends paid$", "dividends_paid"),
    ("fin", r"^repayment of lease liabilities$", "lease_repayments"),
    ("fin", r"^other$", "cff_other"),
    ("fin", r"^cash flows from financing activities$", "cff"),
    (None, r"^(effect of exchange rate|cash equivalents$)", "fx_effect_cash"),
    (None, r"^net change in cash", "net_change_cash"),
    (None, r"beginning of (year|period)$", "cash_begin"),
    (None, r"end of (year|period)$", "cash_end"),
]
CF_CONTEXT = [(r"^cash flows from operating activities:?$", "op"),
              (r"^cash flows from investing activities:?$", "inv"),
              (r"^cash flows from financing activities:?$", "fin")]


def _parse_statement(text, mapping, contexts, has_context):
    """Return {item: [values...]} for one statement section."""
    out, ctx = {}, None
    for label, nums in rows(text, int_only=True):
        low = label.lower().rstrip(":").strip()
        if not nums:
            for pat, c in contexts:
                if re.match(pat, low):
                    ctx = c
            continue
        for entry in mapping:
            c, pat, item = entry if has_context else (None, *entry)
            if (c is None or c == ctx) and re.search(pat, low) and item not in out:
                out[item] = nums
                break
        # totals close a sub-section, so the next 'Other' maps correctly
        if has_context and re.match(r"^cash flows from (operating|investing|financing) activities$", low):
            ctx = None
    return out


def statements(text):
    bs = section(text, r"\(1\)\s*Consolidated Statements? of Financial Position", r"Statements? of Profit or Loss and")
    is_ = section(text, r"^\s*Consolidated Statements? of (Profit or Loss|Income)\s*$", r"^\s*Consolidated Statements? of Comprehensive")
    cf = section(text, r"\(4\)\s*Consolidated Statements? of Cash Flows", r"Notes to Consolidated|Segment Information")
    return {"BS": _parse_statement(bs, BS_MAP, BS_CONTEXT, True),
            "IS": _parse_statement(is_, IS_MAP, [], False),
            "CF": _parse_statement(cf, CF_MAP, CF_CONTEXT, True)}


def segments(text, fy):
    """Two blocks (prior, current); columns: Japan, Europe, North America, Asia, Total, Other, Elim, Consolidated."""
    sec = section(text, r"^\s*Segment Information\s*$", r"Revenue by product categor")
    cols = ["Japan", "Europe", "North America", "Asia", "Subtotal", "Other", "Eliminations", "Consolidated"]
    blocks, cur = [], {}
    for label, nums in rows(sec):
        low = label.lower()
        if len(nums) != 8:
            continue
        if re.search(r"customers|external", low):
            cur = {"external_revenue": nums}
        elif "inter-segment" in low:
            cur["intersegment_revenue"] = nums
        elif re.match(r"^total", low):
            cur["total_revenue"] = nums
        elif "operating profit" in low:
            cur["operating_profit"] = nums
            blocks.append(cur)
    recs = []
    for year, blk in zip([fy - 1, fy], blocks[-2:]):
        for item, vals in blk.items():
            for col, v in zip(cols, vals):
                recs.append({"fy": year, "segment": col, "item": item, "value": v})
    return recs


def simple_table(text, start, end, labels, min_abs=0):
    """For supplementary tables: {canonical: [numbers]} keeping |x| >= min_abs."""
    sec = section(text, start, end)
    out = {}
    for label, nums in rows(sec):
        low = label.lower()
        for pat, item in labels:
            if re.search(pat, low) and item not in out:
                vals = [n for n in nums if abs(n) >= min_abs]
                if vals:
                    out[item] = vals
    return out


GEO = [(r"^japan", "Japan"), (r"^europe", "Europe"), (r"^north america", "North America"),
       (r"^asia", "Asia"), (r"central and south america", "Central & South America"),
       (r"^oceania", "Oceania"), (r"middle east", "Middle East & Africa"), (r"^total", "Total")]


def shares(text):
    """Issued, treasury (period end) and average shares from the front page."""
    t = re.sub(r"\s+", " ", text)
    issued = re.search(r"shares issued \(including treasury (?:shares|stock)\):\s*As of [A-Za-z]+ \d+, \d{4}:\s*([\d,]+)", t, re.I)
    treas = re.search(r"Number of treasury (?:shares|stock):\s*As of [A-Za-z]+ \d+, \d{4}:\s*([\d,]+)", t, re.I)
    avg = re.search(r"Average number of shares outstanding:\s*For the (?:year|three months) ended\s*(?:[A-Za-z]+ \d+, \d{4}:)?\s*([\d,]+)", t, re.I)
    if avg is None:  # quarterly layout puts the date after the phrase
        avg = re.search(r"Average number of shares outstanding:\s*For the three months ended\s*[A-Za-z]+ \d+, \d{4}:\s*([\d,]+)", t, re.I)
    f = lambda m: float(m.group(1).replace(",", "")) if m else None
    return {"shares_issued": f(issued), "treasury_shares_count": f(treas), "avg_shares": f(avg)}


def guidance(text):
    sec = section(text, r"Consolidated Financial Performance Forecast for the year ending", r"Profit attributable to\s*$|per share|Notes?:")[:1500]
    g = {}
    if re.search(r"difficult", sec, re.I):  # FY3/2021: no guidance issued (COVID-19)
        return g
    for label, nums in rows(sec):
        low = label.lower()
        for pat, item in [(r"^revenue", "guide_revenue"), (r"^operating profit", "guide_op"),
                          (r"^profit before", "guide_pbt"), (r"^profit attributable", "guide_ni")]:
            if re.search(pat, low) and nums and item not in g:
                g[item] = nums[0]
    return g


def dps(text):
    sec = section(text, r"Cash dividends? per share", r"Total cash dividend|Notes?:")
    for label, nums in rows(sec):
        if label.lower().startswith("total") and nums:
            return nums  # [prior, current]
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    long, seg_recs, geo_recs, prod_recs, sup = [], [], [], [], []
    for fy, fname in ANNUAL.items():
        text = pdf_text(RAW / fname)
        for stmt, items in statements(text).items():
            for item, vals in items.items():
                # BS in the FY3/2019 release has 3 columns: 1 Apr 2017 (IFRS opening), FY2018, FY2019
                periods = [fy - len(vals) + 1 + i for i in range(len(vals))]
                for p, v in zip(periods, vals):
                    long.append({"source": fname, "release_fy": fy, "statement": stmt,
                                 "item": item, "fy": p, "value": v,
                                 "column": "current" if p == fy else "prior"})
        seg_recs += [dict(r, source=fname, release_fy=fy) for r in segments(text, fy)]

        geo = simple_table(text, r"^\s*(\(\d\)|\d\.)\s*Consolidated Revenue by Geographic Area", r"Notes?:", GEO, min_abs=1000)
        for region, vals in geo.items():
            for p, v in zip([fy - 1, fy], vals[-2:]):
                geo_recs.append({"fy": p, "region": region, "value": v, "source": fname, "release_fy": fy})

        prod = simple_table(text, r"Revenue by product categor", r"Information per share|Notes?:",
                            [(r"^finished goods", "finished_goods"), (r"^parts, repairs", "parts_repairs_accessories"),
                             (r"^total revenue", "total")], min_abs=1000)
        for cat, vals in prod.items():
            for p, v in zip([fy - 1, fy], vals[:2]):
                prod_recs.append({"fy": p, "category": cat, "value": v, "source": fname, "release_fy": fy})

        fx = simple_table(text, r"^\s*(\(\d\)|\d\.)\s*Exchange Rates\s*$", r"Production Ratio",
                          [(r"^usd", "fx_usdjpy"), (r"^eur", "fx_eurjpy"), (r"^rmb", "fx_rmbjpy")])
        cap = simple_table(text, r"Capital Expenditures, Depreciation", r"English translation|$\Z",
                           [(r"^capital expenditures", "capex_disclosed"), (r"^depreciation", "da_ex_rou"),
                            (r"^r&d", "rnd")])
        for item, vals in {**fx, **cap}.items():
            for i, v in enumerate(vals[:3]):
                p = fy - 1 + i
                sup.append({"fy": p, "item": item, "value": v,
                            "basis": ["actual_prior_col", "actual", "forecast"][i],
                            "source": fname, "release_fy": fy})
        for item, v in shares(text).items():
            sup.append({"fy": fy, "item": item, "value": v, "basis": "actual", "source": fname, "release_fy": fy})
        d = dps(text)
        if d:
            for p, v in zip([fy - 1, fy], d[:2]):
                sup.append({"fy": p, "item": "dps", "value": v, "basis": "actual", "source": fname, "release_fy": fy})
        for item, v in guidance(text).items():
            sup.append({"fy": fy + 1, "item": item, "value": v, "basis": "company_guidance",
                        "source": fname, "release_fy": fy})

    # quarterly (1Q) statements for the LTM bridge
    q_recs = []
    for q, fname in QUARTERLY.items():
        text = pdf_text(RAW / fname)
        for stmt, items in statements(text).items():
            for item, vals in items.items():
                q_recs.append({"period": q, "statement": stmt, "item": item,
                               "prior": vals[-2] if len(vals) > 1 else None, "value": vals[-1], "source": fname})
        for item, v in {**shares(text), **guidance(text)}.items():
            q_recs.append({"period": q, "statement": "SUP", "item": item, "prior": None, "value": v, "source": fname})

    long = pd.DataFrame(long)
    long.to_csv(OUT / "makita_statements_long.csv", index=False)

    # primary values: a year's own release only. FY2018 / FY2017-opening exist only as comparatives in
    # the FY3/2019 release. Later comparatives are not used to fill gaps (they can carry reclassifications).
    primary = long[(long.column == "current") | (~long.fy.isin(list(ANNUAL)))]
    primary = primary.sort_values("release_fy").drop_duplicates(["statement", "item", "fy"])
    for stmt in ["IS", "BS", "CF"]:
        wide = primary[primary.statement == stmt].pivot(index="item", columns="fy", values="value")
        order = [m[-1] for m in (BS_MAP if stmt == "BS" else CF_MAP if stmt == "CF" else IS_MAP)]
        wide = wide.reindex([i for i in order if i in wide.index])
        wide.columns = [f"FY{c}" for c in wide.columns]
        wide.to_csv(OUT / f"makita_{stmt.lower()}.csv")

    # restatement check: prior column of release t+1 vs current column of release t
    cur = long[long.column == "current"].set_index(["statement", "item", "fy"])["value"]
    pri = long[(long.column == "prior") & (long.fy == long.release_fy - 1)].set_index(["statement", "item", "fy"])["value"]
    rs = pd.concat([cur.rename("as_first_reported"), pri.rename("as_restated_next_year")], axis=1).dropna()
    rs["diff"] = rs["as_restated_next_year"] - rs["as_first_reported"]
    rs[rs["diff"].abs() > 0.5].reset_index().to_csv(OUT / "makita_restatements.csv", index=False)

    pd.DataFrame(seg_recs).to_csv(OUT / "makita_segments.csv", index=False)
    pd.DataFrame(geo_recs).to_csv(OUT / "makita_geo_revenue.csv", index=False)
    pd.DataFrame(prod_recs).to_csv(OUT / "makita_product_mix.csv", index=False)
    sup = pd.DataFrame(sup)
    sup.to_csv(OUT / "makita_supplementary.csv", index=False)
    # wide actuals: own-release value first; prior-year column only where no own release (FY2018)
    act = sup[sup.basis.isin(["actual", "actual_prior_col"])].copy()
    act["rank"] = (act.basis != "actual").astype(int)
    act = act[(act.basis == "actual") | (~act.fy.isin(list(ANNUAL)))]
    act = act.sort_values("rank").drop_duplicates(["item", "fy"])
    w = act.pivot(index="item", columns="fy", values="value")
    w.columns = [f"FY{c}" for c in w.columns]
    w.to_csv(OUT / "makita_supplementary_wide.csv")
    g = sup[sup.basis.isin(["forecast", "company_guidance"])].pivot_table(
        index=["fy", "release_fy"], columns="item", values="value", aggfunc="first")
    g.to_csv(OUT / "makita_company_forecasts.csv")
    pd.DataFrame(q_recs).to_csv(OUT / "makita_quarterly.csv", index=False)
    print("parsed", len(long), "statement values;", len(rs[rs['diff'].abs() > 0.5]), "restated values")


if __name__ == "__main__":
    main()
