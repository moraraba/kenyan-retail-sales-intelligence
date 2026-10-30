"""
Reproduce the whole capstone end to end.

    python run_all.py              # everything (needs a running PostgreSQL for Milestone 4)
    python run_all.py --skip-sql   # everything except the PostgreSQL load and notebook 04

Order: generate data -> clean -> load PostgreSQL -> execute notebooks 01-07 -> build dashboard.
Takes about 5 minutes on a laptop.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
skip_sql = "--skip-sql" in sys.argv


def step(title, args):
    t = time.time()
    print(f"\n=== {title}")
    subprocess.run([sys.executable] + args, check=True, cwd=ROOT)
    print(f"    done in {time.time() - t:.0f}s")


step("M1  generate synthetic sales data", ["src/generate_data.py"])
step("M2  clean and prepare", ["src/clean.py"])
if not skip_sql:
    step("M4  load PostgreSQL star schema", ["src/load_postgres.py"])
nbs = ["01", "02", "03", "05", "06", "07"] if skip_sql else ["01", "02", "03", "04", "05", "06", "07"]
step("M1-M6  execute notebooks", ["tools/build_notebooks.py"] + nbs)
step("M7  build dashboard + Power BI extracts", ["src/build_dashboard.py"])
print("\nAll done. Open notebooks/*.ipynb, dashboard/Mavuno_Mart_Sales_Dashboard.xlsx and docs/presentation.")
