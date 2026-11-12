"""Every humanitarian plan OCHA's HPC API lists for 2000-2025, one row per plan
and country, to count each country's years under an appeal."""
import time

import pandas as pd
import requests

from common import RAW

rows = []
for year in range(2000, 2026):
    r = requests.get(f"https://api.hpc.tools/v1/public/plan/year/{year}", timeout=60)
    r.raise_for_status()
    for p in r.json().get("data", []):
        locs = sorted({l["iso3"] for l in p.get("locations", []) if l.get("adminLevel") == 0 and l.get("iso3")})
        for iso in locs:
            rows.append({"year": year, "plan_id": p["id"], "plan_code": p["planVersion"].get("code"),
                         "plan_name": p["planVersion"].get("name"), "iso3": iso, "n_countries": len(locs)})
    time.sleep(0.5)
pd.DataFrame(rows).to_csv(RAW / "fts_plan_history_2000_2025.csv", index=False)
print(len(rows), "plan-country rows")
