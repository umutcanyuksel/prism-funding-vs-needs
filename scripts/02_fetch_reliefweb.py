"""ReliefWeb reports per country and year, 2021-2025, by original publication
date, for every country in the plan file: all reports, and those from sources
ReliefWeb types as Media. Set RELIEFWEB_APPNAME to your approved appname."""
import os
import time

import pandas as pd
import requests

from common import RAW

APP = os.environ.get("RELIEFWEB_APPNAME")
if not APP:
    raise SystemExit("Set RELIEFWEB_APPNAME (https://apidoc.reliefweb.int/parameters#appname)")
URL = f"https://api.reliefweb.int/v2/reports?appname={APP}"


def counts(iso3: str, media: bool) -> dict:
    conds = [{"field": "primary_country.iso3", "value": iso3.lower()},
             {"field": "date.original", "value": {"from": "2021-01-01T00:00:00+00:00", "to": "2025-12-31T23:59:59+00:00"}}]
    if media:
        conds.append({"field": "source.type.name", "value": "Media"})
    body = {"limit": 0, "filter": {"operator": "AND", "conditions": conds},
            "facets": [{"field": "date.original", "interval": "year"}]}
    for attempt in range(3):
        r = requests.post(URL, json=body, timeout=60)
        if r.ok:
            return {x["value"][:4]: x["count"] for x in r.json()["embedded"]["facets"]["date.original"]["data"]}
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()


isos = sorted(pd.read_csv(RAW / "hpc_fts_plans_2021_2025.csv")["Country Code"].dropna().unique())
rows = []
for iso in isos:
    a, m = counts(iso, False), counts(iso, True)
    rows += [{"iso3": iso, "year": y, "reports_all": a.get(str(y), 0), "reports_media": m.get(str(y), 0)} for y in range(2021, 2026)]
    time.sleep(0.5)
pd.DataFrame(rows).to_csv(RAW / "reliefweb_counts_2021_2025.csv", index=False)
print(len(isos), "countries")
