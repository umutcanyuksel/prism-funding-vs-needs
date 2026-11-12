"""Export the inputs PRISM holds into data/raw/ as plain CSV.

This step runs only inside PRISM's own codebase, against its caches and a
backup of its production archives. Everyone else starts from the CSV files it
wrote, which are committed in data/raw/. Each file keeps the source's own
fields; nothing is modelled here.

  python scripts/00_export_from_prism.py --prism /path/to/PRISM --archives /path/to/backup/caches
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from common import RAW, YEARS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prism", required=True, type=Path, help="PRISM repository root")
    ap.add_argument("--archives", required=True, type=Path,
                    help="folder holding inform_severity_archive/ and inform_archive/ (production backup)")
    a = ap.parse_args()
    ds = a.prism / "data_sources"
    y0, y1 = min(YEARS), max(YEARS)

    # Humanitarian plans: HPC (people in need, targeted, requirements) and FTS (funding), one row per plan and country
    hp = pd.read_pickle(ds / "hpc_rpmb_cache/hpc_rpmb.pkl")
    hp = hp[hp.Year.between(y0, y1)]
    cols = ["Country", "Country Code", "Year", "Plan ID", "Plan Code", "Plan Name", "Total Population",
            "People Affected", "People In Need", "People Targeted", "Requirements USD", "Funding USD", "API_Updated"]
    hp[cols].to_csv(RAW / "hpc_fts_plans_2021_2025.csv", index=False)

    # FTS funding by donor for each country's primary plan(s)
    fd = pd.read_csv(ds / "fts_snapshots/fts_plan_donors.csv")
    fd[fd.Year.between(y0, y1)].to_csv(RAW / "fts_plan_donors_2021_2025.csv", index=False)

    # Protection cluster and its areas of responsibility (GPC countries)
    pr = pd.read_pickle(ds / "fts_hrp_cache/fts_hrp.pkl")
    keep = ["country", "year", "plan_id", "plan_name", "protection_overall_pin", "protection_overall_target",
            "protection_cluster_requirement", "protection_received_total"]
    pr[pr.year.between(y0, y1)][keep].to_csv(RAW / "protection_cluster_2021_2025.csv", index=False)

    # INFORM Severity: every crisis and month (0-5 scale through 2025)
    con = sqlite3.connect(f"file:{a.archives}/inform_severity_archive/inform_severity_archive.db?mode=ro", uri=True)
    sv = pd.read_sql("SELECT crisis_id, crisis_name, iso3, country, observation_month, inform_severity_index, "
                     "severity_category_label FROM inform_severity_snapshots "
                     f"WHERE observation_month BETWEEN '{y0}-01' AND '{y1}-12' ORDER BY iso3, crisis_id, observation_month", con)
    sv.to_csv(RAW / "inform_severity_crisis_month_2021_2025.csv", index=False)

    # INFORM Risk, the yearly release
    con = sqlite3.connect(f"file:{a.archives}/inform_archive/inform_archive.db?mode=ro", uri=True)
    rk = pd.read_sql("SELECT s.iso3, s.country_name, w.year, s.indicator_score AS inform_risk "
                     "FROM inform_risk_snapshots s JOIN inform_risk_workflows w ON w.workflow_id = s.workflow_id "
                     f"WHERE w.is_canonical = 1 AND s.indicator_id = 'INFORM' AND w.year BETWEEN {y0} AND {y1}", con)
    rk.to_csv(RAW / "inform_risk_2021_2025.csv", index=False)

    # IDMC Global Internal Displacement Database
    idmc = pd.read_csv(ds / "idmc_snapshots/idmc_combined_annual.csv")
    idmc[idmc.year.between(y0, y1)].to_csv(RAW / "idmc_gidd_2021_2025.csv", index=False)

    # Eurostat: first-time asylum applicants in the EU27 by citizenship (migr_asyappctza)
    e = pd.read_parquet(ds / "migration_statistics/processed/asylum/applicants.eu27.parquet")
    e["year"] = pd.to_numeric(e.year, errors="coerce")
    e[(e.application_type == "FRST") & e.year.between(y0, y1)].to_csv(RAW / "eurostat_asylum_first_time_eu27_2021_2025.csv", index=False)

    # CERF allocations by window
    c = pd.read_pickle(ds / "funding_cache/cerf.pkl")
    c["Year"] = pd.to_numeric(c.Year, errors="coerce")
    c[c.Year.between(y0, y1)].drop(columns=["API_Updated"], errors="ignore").to_csv(RAW / "cerf_allocations_2021_2025.csv", index=False)

    # GRFC: population in IPC/CH Phase 3 or above
    g = pd.read_pickle(ds / "grfc_food_security_cache/grfc_food_security.pkl")["by_iso3"]
    rows = [{"iso3": iso, "year": r["year"], "edition": r.get("edition"), "source": r.get("source"),
             "pop_analysed": r.get("pop_analysed"), "phase3plus_n": r.get("phase3plus_n"), "phase3plus_pct": r.get("phase3plus_pct")}
            for iso, lst in g.items() for r in lst if y0 <= int(r["year"]) <= y1]
    pd.DataFrame(rows).sort_values(["iso3", "year", "edition"]).to_csv(RAW / "grfc_phase3plus_2021_2025.csv", index=False)
    # FTS: each top-100 donor's funding by recipient country (all humanitarian funding, inside and outside plans)
    b = pd.read_csv(ds / "fts_snapshots/fts_donor_breakdowns.csv")
    b[(b.Dimension == "country") & b.Year.between(y0, y1)].drop(columns=["Dimension"]).to_csv(RAW / "fts_donor_by_country_2021_2025.csv", index=False)

    # Eurostat: first-time asylum applicants by citizenship and by the country where they applied
    h = pd.read_parquet(ds / "migration_statistics/processed/asylum/applicants.data.parquet")
    h["year"] = pd.to_numeric(h.year, errors="coerce")
    h[(h.application_type == "FRST") & h.year.between(y0, y1)].to_csv(RAW / "eurostat_asylum_first_time_by_host_2021_2025.csv", index=False)
    print("exported to", RAW)


if __name__ == "__main__":
    main()
