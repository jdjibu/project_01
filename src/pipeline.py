"""End-to-end data pipeline. `python src/pipeline.py --offline` rebuilds data/clean from data/raw only."""
import argparse
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
STEPS = ["parse_makita.py", "check_clean.py", "clean_market.py", "crosscheck_peers.py"]

ap = argparse.ArgumentParser()
ap.add_argument("--offline", action="store_true", help="skip downloads, rebuild from data/raw")
args = ap.parse_args()
steps = STEPS if args.offline else ["fetch_data.py"] + STEPS
for s in steps:
    print(f"== {s}")
    if subprocess.run([sys.executable, str(SRC / s)]).returncode:
        sys.exit(f"step failed: {s}")
