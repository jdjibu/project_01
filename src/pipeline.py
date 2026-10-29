"""End-to-end pipeline: data -> checks -> ratios -> Excel model -> risks -> report -> website data.
`python src/pipeline.py --offline` rebuilds everything from the committed data/raw only."""
import argparse
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
STEPS = ["parse_makita.py", "check_clean.py", "clean_market.py", "crosscheck_peers.py",  # Phase 1 data
         "historical.py",                                     # Phase 3 ratios + charts
         "build_model.py",                                    # Phase 4-5 Excel model (LibreOffice recalc)
         "risks.py",                                          # Phase 6 risk shocks through the model
         "valuation_charts.py", "build_report.py",            # Phase 7 charts + PDF
         "export_web.py"]                                     # website data + downloads

ap = argparse.ArgumentParser()
ap.add_argument("--offline", action="store_true", help="skip downloads, rebuild from data/raw")
args = ap.parse_args()
steps = STEPS if args.offline else ["fetch_data.py"] + STEPS
for s in steps:
    print(f"== {s}")
    if subprocess.run([sys.executable, str(SRC / s)]).returncode:
        sys.exit(f"step failed: {s}")
