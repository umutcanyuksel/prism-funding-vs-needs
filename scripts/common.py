"""Paths and small helpers shared by the scripts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESTRICTED = ROOT / "data" / "restricted"   # ACLED: kept out of the repository (licence)
EXTERNAL = ROOT / "data" / "external"       # third-party downloads kept out of the repository
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
YEARS = range(2021, 2026)

# GeoDist (2004) codes that changed since
CEPII_FIX = {"PAL": "PSE", "ZAR": "COD", "TMP": "TLS", "ROM": "ROU"}

for d in (RAW, PROCESSED, RESTRICTED, EXTERNAL, RESULTS, CHARTS):
    d.mkdir(parents=True, exist_ok=True)
