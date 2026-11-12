"""ACLED political violence and civilian targeting, events and fatalities by
country and year, 2021-2025, from the two aggregate workbooks ACLED publishes
on HDX.

ACLED's terms do not allow its figures to be redistributed, so the output goes
to data/restricted/, which the repository does not track. Run this script to
rebuild it; cite as "ACLED, accessed <date>".

  python scripts/05_fetch_acled.py                 # download from HDX
  python scripts/05_fetch_acled.py --from-dir DIR  # use workbooks already downloaded
"""
import argparse
from pathlib import Path

import pandas as pd
import requests

from common import EXTERNAL, RAW, RESTRICTED, YEARS

DATASETS = {"pv": "political-violence-events-and-fatalities", "ct": "civilian-targeting-events-and-fatalities"}
ALIASES = {"democratic republic of congo": "COD", "republic of congo": "COG", "ivory coast": "CIV", "cote d'ivoire": "CIV",
           "palestine": "PSE", "syria": "SYR", "iran": "IRN", "russia": "RUS", "turkey": "TUR", "turkiye": "TUR",
           "venezuela": "VEN", "bolivia": "BOL", "laos": "LAO", "vietnam": "VNM", "north korea": "PRK",
           "south korea": "KOR", "moldova": "MDA", "tanzania": "TZA", "czech republic": "CZE", "kosovo": "XKX",
           "micronesia": "FSM", "cape verde": "CPV", "eswatini": "SWZ", "east timor": "TLS", "south sudan": "SSD",
           "united states": "USA", "united kingdom": "GBR", "bahamas": "BHS", "gambia": "GMB", "myanmar": "MMR"}


def workbook(key: str, from_dir: Path | None) -> Path:
    name = DATASETS[key] + ".xlsx"
    if from_dir:
        return from_dir / name
    dest = EXTERNAL / name
    if not dest.exists():
        meta = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": DATASETS[key]}, timeout=60).json()
        url = next(x["url"] for x in meta["result"]["resources"] if (x.get("format") or "").upper() == "XLSX")
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def names_to_iso3() -> dict:
    m = {k.lower(): v for k, v in pd.read_csv(RAW / "iso2_iso3_cepii.csv").set_index("country").iso3.items() if isinstance(k, str)}
    plans = pd.read_csv(RAW / "hpc_fts_plans_2021_2025.csv")
    m.update({c.lower(): i for c, i in zip(plans.Country, plans["Country Code"])})
    m.update(ALIASES)
    return m


def load(path: Path, lookup: dict) -> pd.DataFrame:
    frames = []
    for sheet, df in pd.read_excel(path, sheet_name=None).items():
        if "Events" not in df.columns:
            continue
        if "ISO3" not in df.columns:
            df["ISO3"] = df.Country.str.lower().map(lookup)
        frames.append(df[["Country", "ISO3", "Year", "Events", "Fatalities"]])
    return pd.concat(frames)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-dir", type=Path)
    a = ap.parse_args()
    lookup = names_to_iso3()
    out = None
    for key in ("pv", "ct"):
        df = load(workbook(key, a.from_dir), lookup)
        miss = sorted(df[df.ISO3.isna()].Country.unique())
        if miss:
            print(f"{key}: no ISO3 for", miss)
        df = df[df.Year.isin(YEARS)].dropna(subset=["ISO3"])
        agg = df.groupby(["ISO3", "Year"])[["Events", "Fatalities"]].sum().reset_index()
        agg.columns = ["iso3", "year", f"acled_{key}_events", f"acled_{key}_fatalities"]
        out = agg if out is None else out.merge(agg, on=["iso3", "year"], how="outer")
    out.to_csv(RESTRICTED / "acled_country_year_2021_2025.csv", index=False)
    print(len(out), "country-years")


if __name__ == "__main__":
    main()
