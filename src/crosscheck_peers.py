"""Cross-check yfinance peer fundamentals against SEC XBRL (10-K) for US-listed peers.
Writes data/clean/peer_crosscheck.csv."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, CLEAN = ROOT / "data/raw", ROOT / "data/clean"
CONCEPTS = {"revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
            "net_income": ["NetIncomeLoss"]}


def sec_annual(facts, concepts, fy_end):
    for c in concepts:
        units = facts["facts"]["us-gaap"].get(c, {}).get("units", {}).get("USD", [])
        hits = [u for u in units if u.get("form") == "10-K"
                and abs((pd.Timestamp(u["end"]) - pd.Timestamp(fy_end)).days) <= 7  # 52/53-week years
                and u.get("fp") == "FY" and (pd.Timestamp(u["end"]) - pd.Timestamp(u["start"])).days > 350]
        if hits:
            return hits[-1]["val"], c, hits[-1]["accn"]
    return None, None, None


def main():
    peers = pd.read_csv(CLEAN / "peers_financials.csv").set_index("ticker")
    rows = []
    for t in ["SWK", "TTC"]:
        facts = json.loads((RAW / f"sec/companyfacts_{t}.json").read_text())
        fy_end = peers.at[t, "fy_end"]
        yi = pd.read_csv(RAW / f"peers/{t}_income_stmt.csv", index_col=0)[fy_end]
        for item, yf_row in [("revenue", "Total Revenue"), ("net_income", "Net Income Common Stockholders")]:
            sec_val, concept, accn = sec_annual(facts, CONCEPTS[item], fy_end)
            yv = float(yi[yf_row])
            rows.append({"ticker": t, "fy_end": fy_end, "item": item, "yfinance_usd": yv, "sec_usd": sec_val,
                         "sec_concept": concept, "sec_accession": accn,
                         "pct_diff": (yv / sec_val - 1) if sec_val else None})
    d = pd.DataFrame(rows)
    d.to_csv(CLEAN / "peer_crosscheck.csv", index=False)
    print(d.to_string())


if __name__ == "__main__":
    main()
