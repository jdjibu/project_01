"""Download every raw input into data/raw and log it in data/raw/MANIFEST.csv
(file, source URL, retrieved UTC, sha256). Raw files are never edited afterwards.

Usage: python src/fetch_data.py [--skip-filings]
"""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
UA = {"User-Agent": "project_01 student research (non-commercial)"}

MAKITA_IR = "https://www.makita.biz/ir/upload_file"
RELEASES = ["201903e", "202003e"] + [f"financial_results{y}03" for y in range(2021, 2027)] + \
           ["financial_results202503-2", "financial_results202506", "financial_results202606"]
REPORTS = ["makita_report_view2025e", "makita_report_view2026e"]  # integrated reports; >100MB, gitignored
FS = ["201903cfs", "202003cfs", "202103cfs", "202203cfs", "202303cfs", "202403cfs", "202503cfs2", "202603cfs"]

TICKER = "6586.T"
MARKET = ["1306.T", "^N225"]                       # TOPIX ETF proxy, Nikkei 225 (robustness)
PEERS = ["0669.HK", "SWK", "2285.HK", "HUSQ-B.ST", "6454.T", "6250.T", "TTC"]
FX = ["JPY=X", "EURJPY=X", "HKDJPY=X", "SEKJPY=X", "CNYJPY=X"]

MACRO = {
    "macro/mof_jgb_current_month.csv": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv",
    "macro/mof_jgb_historical.csv": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv",
    "macro/fred_IRLTLT01JPM156N.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01JPM156N",
    "damodaran/ctryprem.xlsx": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx",
    "damodaran/histimpl.xls": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/histimpl.xls",
    "damodaran/betaGlobal.xls": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaGlobal.xls",
    "damodaran/betaJapan.xls": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaJapan.xls",
    # SEC XBRL company facts for US-listed peers (cross-check of yfinance fundamentals)
    "sec/companyfacts_SWK.json": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000093556.json",
    "sec/companyfacts_TTC.json": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000737758.json",
}

manifest = []


def log(path: Path, source: str):
    manifest.append({"file": str(path.relative_to(RAW)), "source": source,
                     "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})


def download(url: str, rel: str):
    path = RAW / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            r.raise_for_status()
            path.write_bytes(r.content)
            log(path, url)
            return
        except requests.RequestException as e:
            if attempt == 3:
                print("FAILED", url, e)
            time.sleep(2 ** (attempt + 1))


def yf_save(ticker: str, folder: str, fundamentals: bool):
    import yfinance as yf
    tk = yf.Ticker(ticker)
    safe = ticker.replace("^", "").replace("=", "")
    base = RAW / folder
    base.mkdir(parents=True, exist_ok=True)
    src = f"yfinance {yf.__version__}: {ticker}"
    h = tk.history(period="10y", interval="1d", auto_adjust=False)
    p = base / f"{safe}_prices_daily.csv"
    h.to_csv(p)
    log(p, src + " history(10y, auto_adjust=False)")
    if not fundamentals:
        return
    p = base / f"{safe}_info.json"
    p.write_text(json.dumps(tk.info, indent=1, default=str))
    log(p, src + " info")
    for name in ["income_stmt", "balance_sheet", "cashflow", "quarterly_income_stmt",
                 "quarterly_balance_sheet", "quarterly_cashflow"]:
        df = getattr(tk, name)
        if df is not None and not df.empty:
            p = base / f"{safe}_{name}.csv"
            df.to_csv(p)
            log(p, src + f" {name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-filings", action="store_true")
    a = ap.parse_args()
    if not a.skip_filings:
        for f in RELEASES:
            download(f"{MAKITA_IR}/m005-m005_02/{f}.pdf", f"makita/releases/{f}.pdf")
        for f in FS:
            download(f"{MAKITA_IR}/m005-m005_03/{f}.pdf", f"makita/fs/{f}.pdf")
        for f in REPORTS:
            download(f"{MAKITA_IR}/m005-m005_05/{f}.pdf", f"makita/reports/{f}.pdf")
    for rel, url in MACRO.items():
        download(url, rel)
    yf_save(TICKER, "market", fundamentals=True)
    for t in MARKET + FX:
        yf_save(t, "market", fundamentals=False)
    for t in PEERS:
        yf_save(t, "peers", fundamentals=True)
        time.sleep(1)  # be polite to Yahoo's rate limiter

    m = pd.DataFrame(manifest)
    mp = RAW / "MANIFEST.csv"
    if mp.exists():  # keep earlier entries for files not refreshed this run
        old = pd.read_csv(mp)
        m = pd.concat([old[~old.file.isin(m.file)], m])
    m.sort_values("file").to_csv(mp, index=False)
    print(f"logged {len(manifest)} files")


if __name__ == "__main__":
    main()
