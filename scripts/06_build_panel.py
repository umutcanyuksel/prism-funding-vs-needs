"""Build the country-year panel, 2021-2025, from data/raw/.

Plans counted: HRPs and HNRPs (plan code H), flash appeals (F), and
single-country plans of other types (O, R: the Rohingya Joint Response Plan,
Lebanon's Emergency Response Plan, the Pakistan floods plans). Regional plans
are left out, because they repeat the same figures on every country's row.
When a country has more than one plan in a year, money is summed and people
in need is the highest figure, so no one is counted twice.

main_sample = 1 marks a year with an HRP, HNRP or flash appeal. ACLED is
added in 07_models.py from data/restricted/ and never written here.
"""
import numpy as np
import pandas as pd

from common import CEPII_FIX, PROCESSED, RAW, YEARS

# 1 plans
hp = pd.read_csv(RAW / "hpc_fts_plans_2021_2025.csv")
hp["prefix"] = hp["Plan Code"].str[0]
hp["n_countries"] = hp["Plan ID"].map(hp.groupby("Plan ID")["Country Code"].nunique())
hp = hp[hp.prefix.isin(["H", "F"]) | (hp.prefix.isin(["O", "R"]) & hp.n_countries.eq(1))]
g = hp.groupby(["Country Code", "Year"])
p = pd.DataFrame({
    "country": g["Country"].first(),
    "plan_codes": g["Plan Code"].apply(lambda s: " ".join(sorted(s))),
    "n_plans": g["Plan Code"].count(),
    "has_hrp": g["prefix"].apply(lambda s: int("H" in set(s))),
    "has_flash": g["prefix"].apply(lambda s: int("F" in set(s))),
    "has_other_plan": g["prefix"].apply(lambda s: int(bool(set(s) & {"O", "R"}))),
    "population": g["Total Population"].max(),
    "pin": g["People In Need"].max(),
    "targeted": g["People Targeted"].max(),
    "requirements_usd": g["Requirements USD"].sum(),
    "funding_usd": g["Funding USD"].sum(),
}).reset_index().rename(columns={"Country Code": "iso3", "Year": "year"})
p.loc[p.pin.le(0), "pin"] = np.nan
p["coverage"] = p.funding_usd / p.requirements_usd
p["funding_per_pin_usd"] = p.funding_usd / p.pin
p["requirements_per_pin_usd"] = p.requirements_usd / p.pin
p["pin_share_of_population"] = p.pin / p.population
p["targeted_share_of_pin"] = p.targeted / p.pin
p["main_sample"] = ((p.has_hrp + p.has_flash) > 0).astype(int)
p = p.sort_values(["iso3", "year"]).reset_index(drop=True)
consecutive = p.groupby("iso3").year.diff().eq(1)
p["funding_usd_lag1"] = p.groupby("iso3").funding_usd.shift(1).where(consecutive)

# 2 appeal history since 2000 (single-country plans)
h = pd.read_csv(RAW / "fts_plan_history_2000_2025.csv")
hist = h[h.n_countries == 1].groupby("iso3").year.apply(set).to_dict()


def history(iso, year):
    yrs = hist.get(iso, set())
    run, y = 0, year - 1
    while y in yrs:
        run, y = run + 1, y - 1
    return sum(1 for x in yrs if x < year), run


p[["appeal_years_since_2000", "appeal_run_years"]] = [history(i, y) for i, y in zip(p.iso3, p.year)]

# 3 INFORM Severity: the highest crisis score in the country each month, averaged over the year
sv = pd.read_csv(RAW / "inform_severity_crisis_month_2021_2025.csv")
sv["year"] = sv.observation_month.str[:4].astype(int)
m = sv.groupby(["iso3", "observation_month", "year"]).inform_severity_index.max().reset_index()
sev = m.groupby(["iso3", "year"]).agg(inform_severity=("inform_severity_index", "mean"),
                                       inform_severity_months=("inform_severity_index", "count")).reset_index()
risk = pd.read_csv(RAW / "inform_risk_2021_2025.csv")[["iso3", "year", "inform_risk"]]

# 4 displacement, food insecurity, asylum, attention
idmc = pd.read_csv(RAW / "idmc_gidd_2021_2025.csv")[["iso3", "year", "conflict_total_displacement", "conflict_new_displacement", "disaster_new_displacement"]]
idmc.columns = ["iso3", "year", "idps_conflict_stock", "idp_conflict_new", "idp_disaster_new"]
grfc = pd.read_csv(RAW / "grfc_phase3plus_2021_2025.csv").sort_values("edition").drop_duplicates(["iso3", "year"], keep="last")
grfc = grfc[["iso3", "year", "phase3plus_n", "phase3plus_pct"]].rename(columns={"phase3plus_n": "grfc_phase3plus", "phase3plus_pct": "grfc_phase3plus_pct"})
i2 = pd.read_csv(RAW / "iso2_iso3_cepii.csv").dropna().drop_duplicates("iso2")
i2 = dict(zip(i2.iso2, i2.iso3))
i2.update({"PS": "PSE", "CD": "COD", "TL": "TLS", "SS": "SSD", "XK": "XKX", "RS": "SRB", "ME": "MNE", "EL": "GRC", "UK": "GBR"})
e = pd.read_csv(RAW / "eurostat_asylum_first_time_eu27_2021_2025.csv", keep_default_na=False)
e["iso3"] = e.citizenship.map(i2)
asy = e.dropna(subset=["iso3"]).groupby(["iso3", "year"]).value.sum().rename("eu_first_time_asylum").reset_index()
rw = pd.read_csv(RAW / "reliefweb_counts_2021_2025.csv").rename(columns={"reports_all": "reliefweb_reports", "reports_media": "reliefweb_media_reports"})
rw_lag = rw[["iso3", "year", "reliefweb_reports"]].assign(year=lambda x: x.year + 1).rename(columns={"reliefweb_reports": "reliefweb_reports_lag1"})

# 5 forgotten-crisis flags
fca = pd.read_csv(RAW / "echo_forgotten_crises_2021_2026.csv").dropna(subset=["iso3"])
fca = fca.assign(iso3=fca.iso3.str.split()).explode("iso3")
fca = fca.groupby(["iso3", "year"]).crisis_name.apply("; ".join).rename("echo_forgotten_crises").reset_index().assign(echo_forgotten=1)
cerf = pd.read_csv(RAW / "cerf_allocations_2021_2025.csv")
cerf["window"] = np.where(cerf.Indicator.str.contains("Underfunded"), "cerf_ufe_usd",
                          np.where(cerf.Indicator.str.contains("Rapid Response"), "cerf_rr_usd", "cerf_other_usd"))
cf = cerf.pivot_table(index=["Country Code", "Year"], columns="window", values="Value", aggfunc="sum").reset_index()
cf = cf.rename(columns={"Country Code": "iso3", "Year": "year"})

# 6 donors: mix of each country's primary plan(s) and the share from former colonial powers
fd = pd.read_csv(RAW / "fts_plan_donors_2021_2025.csv")
col = pd.read_csv(RAW / "colonial_links_cepii.csv")
GOV = {"GBR": ["United Kingdom, Government of"], "FRA": ["France, Government of"], "BEL": ["Belgium, Government of"],
       "PRT": ["Portugal, Government of"], "ITA": ["Italy, Government of"], "ESP": ["Spain, Government of"],
       "NLD": ["Netherlands, Government of"], "DEU": ["Germany, Government of"], "JPN": ["Japan, Government of"],
       "TUR": ["Türkiye, Government of"], "EGY": ["Egypt, Government of"], "RUS": ["Russian Federation, Government of"],
       "AUS": ["Australia, Government of"], "NZL": ["New Zealand, Government of"], "ZAF": ["South Africa, Government of"],
       "DNK": ["Denmark, Government of"], "NOR": ["Norway, Government of"], "SWE": ["Sweden, Government of"],
       "USA": ["United States of America, Government of", "United States Department of State",
               "United States Agency for International Development"]}
US = GOV["USA"]
rows = []
for (iso, yr), gr in fd.groupby(["Country Code", "Year"]):
    t = gr["Funding US$"].sum()
    by = gr.groupby("Donor")["Funding US$"].sum().sort_values(ascending=False)
    colonisers = sorted(set(col[col.iso3 == iso].coloniser))
    names = [n for c in colonisers for n in GOV.get(c, [])]
    rows.append({"iso3": iso, "year": yr, "plan_donor_total_usd": t,
                 "top_donor": by.index[0] if len(by) else None,
                 "top_donor_share": by.iloc[0] / t if t else np.nan,
                 "us_share": gr[gr.Donor.isin(US)]["Funding US$"].sum() / t if t else np.nan,
                 "echo_share": gr[gr.Donor.str.contains("Humanitarian Aid and Civil Protection", na=False)]["Funding US$"].sum() / t if t else np.nan,
                 "donor_hhi": float(((by / t) ** 2).sum()) if t else np.nan,
                 "from_former_colonisers_usd": gr[gr.Donor.isin(names)]["Funding US$"].sum(),
                 "share_from_former_colonisers": gr[gr.Donor.isin(names)]["Funding US$"].sum() / t if t else np.nan})
dm = pd.DataFrame(rows)
colmap = col.groupby("iso3").coloniser.apply(lambda s: " ".join(sorted(set(s)))).rename("former_colonisers").reset_index()

# 7 protection cluster (GPC countries), matched to ISO3 through the plan id
pr = pd.read_csv(RAW / "protection_cluster_2021_2025.csv")
pr["iso3"] = pr.plan_id.map(dict(zip(hp["Plan ID"], hp["Country Code"])))
pr = pr.dropna(subset=["iso3"]).groupby(["iso3", "year"]).agg(
    protection_pin=("protection_overall_pin", "max"), protection_target=("protection_overall_target", "max"),
    protection_required_usd=("protection_cluster_requirement", "sum"), protection_received_usd=("protection_received_total", "sum")).reset_index()

df = p
for t in (sev, risk, idmc, grfc, asy, rw, rw_lag, fca, cf, dm, pr):
    t = t.copy()
    t["year"] = t.year.astype(int)
    df = df.merge(t, on=["iso3", "year"], how="left")
df = df.merge(colmap, on="iso3", how="left")
df["echo_forgotten"] = df.echo_forgotten.fillna(0).astype(int)
for c in ("cerf_ufe_usd", "cerf_rr_usd", "cerf_other_usd"):
    if c in df:
        df[c] = df[c].fillna(0)
df["cerf_ufe"] = (df.cerf_ufe_usd > 0).astype(int)
df["eu_first_time_asylum"] = df.eu_first_time_asylum.fillna(0)
for c in ("protection_pin", "protection_target", "protection_required_usd", "protection_received_usd"):
    df.loc[df[c].eq(0), c] = np.nan
df["protection_coverage"] = df.protection_received_usd / df.protection_required_usd
df = df[df.year.isin(YEARS)]
df.to_csv(PROCESSED / "funding_vs_needs_panel_2021_2025.csv", index=False)
print(df.shape, "main sample:", int(df.main_sample.sum()))
