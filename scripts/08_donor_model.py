"""Donor-level model: does a government donor give more to a country it once
ruled, or to a country whose citizens apply for asylum on its territory?

Unit: government donor x recipient country x year, 2021-2025. Donors are the
governments (and the European Commission) among FTS's top 100 donors each year,
leaving out governments of recipient countries. Recipients are the countries in
the main sample that year (an HRP, HNRP or flash appeal). Funding is all FTS
humanitarian funding from the donor to the country, inside and outside the
plans; a donor that year with no flow to a recipient counts as zero.

Estimator: Poisson pseudo-maximum likelihood (PPML) with donor-year and
recipient-year effects, standard errors clustered by recipient country. The
recipient-year effects absorb everything about a crisis in a year (people in
need, severity, violence, attention), and the donor-year effects absorb each
donor's budget, so the dyadic coefficients compare how one donor splits its
money across crises against how other donors split theirs.

The European Commission takes Brussels' distances, with no shared language,
border or colonial past. Asylum applications come from Eurostat, which covers
EU and EFTA states (and the European Commission through the EU27 total) but
not the United Kingdom after 2020, so the asylum models leave the UK out.

Outputs: results/donor_model.txt, results/donor_model_coefficients.csv,
results/donor_recipient_year.csv
"""
import io
import re
import warnings
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from common import PROCESSED, RAW, RESULTS

warnings.filterwarnings("ignore")
ALIAS = {"united states of america": "USA", "korea, republic of": "KOR", "saudi arabia (kingdom of)": "SAU",
         "russian federation": "RUS", "czech republic": "CZE", "czechia": "CZE", "türkiye": "TUR", "turkey": "TUR",
         "united kingdom": "GBR", "united kingdom of great britain and northern ireland": "GBR", "netherlands": "NLD",
         "switzerland": "CHE", "united arab emirates": "ARE", "china": "CHN", "iran, islamic republic of": "IRN",
         "viet nam": "VNM", "slovakia": "SVK", "estonia": "EST", "lithuania": "LTU", "latvia": "LVA", "croatia": "HRV",
         "slovenia": "SVN", "malta": "MLT", "cyprus": "CYP", "luxembourg": "LUX", "monaco": "MCO", "liechtenstein": "LIE",
         "iceland": "ISL", "kuwait": "KWT", "qatar": "QAT", "azerbaijan": "AZE", "kazakhstan": "KAZ", "thailand": "THA",
         "european commission": "EUR", "belgium": "BEL"}
LABELS = {"colony": "former colonial power (CEPII)", "col45": "colonial relationship after 1945 (CEPII)",
          "lasy": "log first-time asylum applicants from the recipient in the donor country",
          "lasy_lag": "log first-time asylum applicants, previous year", "ldist": "log distance (CEPII, population-weighted)",
          "comlang": "common official language", "contig": "shared border", "lpin": "log people in need",
          "sev": "INFORM Severity"}


def iso3_lookup():
    geo = pd.read_csv(RAW / "iso2_iso3_cepii.csv").dropna()
    m = {c.lower(): i for c, i in zip(geo.country, geo.iso3)}
    plans = pd.read_csv(RAW / "hpc_fts_plans_2021_2025.csv")
    m.update({c.lower(): i for c, i in zip(plans.Country, plans["Country Code"])})
    m.update(ALIAS)
    return m


def build():
    look = iso3_lookup()
    f = pd.read_csv(RAW / "fts_donor_by_country_2021_2025.csv")
    f = f[f.Donor.str.endswith(", Government of") | f.Donor.eq("European Commission")].copy()
    f["donor_iso3"] = f.Donor.str.replace(", Government of", "", regex=False).str.strip().str.lower().map(look)
    f["iso3"] = f.Item.str.lower().map(look)
    miss_d = sorted(f[f.donor_iso3.isna()].Donor.unique())
    panel = pd.read_csv(PROCESSED / "funding_vs_needs_panel_2021_2025.csv")
    rec = panel[(panel.main_sample == 1) & panel.pin.gt(0)][["iso3", "year", "pin", "inform_severity"]]
    donors = f.dropna(subset=["donor_iso3"])[["donor_iso3", "Donor", "Year"]].drop_duplicates().rename(columns={"Year": "year"})
    donors = donors[~donors.donor_iso3.isin(set(rec.iso3))]
    grid = donors.merge(rec, on="year")
    flows = f.dropna(subset=["donor_iso3", "iso3"]).groupby(["donor_iso3", "iso3", "Year"]).Funding_USD.sum().reset_index().rename(columns={"Year": "year"})
    g = grid.merge(flows, on=["donor_iso3", "iso3", "year"], how="left")
    g["funding"] = g.Funding_USD.fillna(0)
    # colonial ties from the repository's own link table (includes short_only links), and CEPII's dyad variables
    links = pd.read_csv(RAW / "colonial_links_cepii.csv")
    g["colony"] = g.set_index(["iso3", "donor_iso3"]).index.isin(set(zip(links.iso3, links.coloniser))).astype(int)
    pairs = pd.read_csv(RAW / "cepii_pairs.csv").drop_duplicates(["donor_iso3", "iso3"])
    # the European Commission takes Brussels' distances, with no shared language, border or colonial past
    ec = pairs[pairs.donor_iso3 == "BEL"].assign(donor_iso3="EUR", contig=0, comlang_off=0, colony=0, col45=0)
    pairs = pd.concat([pairs, ec], ignore_index=True)
    g = g.merge(pairs[["donor_iso3", "iso3", "contig", "comlang_off", "col45", "distw", "dist"]], on=["donor_iso3", "iso3"], how="left")
    g["ldist"] = np.log(g.distw.fillna(g.dist))
    g["comlang"], g["contig"], g["col45"] = g.comlang_off.fillna(0), g.contig.fillna(0), g.col45.fillna(0)
    # asylum: applicants from the recipient lodged in the donor country (EU27 total for the European Commission)
    a = pd.read_csv(RAW / "eurostat_asylum_first_time_by_host_2021_2025.csv", keep_default_na=False)
    i2 = pd.read_csv(RAW / "iso2_iso3_cepii.csv").dropna().drop_duplicates("iso2")
    i2 = dict(zip(i2.iso2, i2.iso3))
    i2.update({"PS": "PSE", "CD": "COD", "SS": "SSD", "EL": "GRC", "UK": "GBR", "XK": "XKX", "RS": "SRB", "ME": "MNE"})
    a["iso3"], a["donor_iso3"] = a.citizenship.map(i2), a.reporting_country.map(i2)
    a = a.dropna(subset=["iso3", "donor_iso3"]).groupby(["donor_iso3", "iso3", "year"]).value.sum().rename("asylum").reset_index()
    eu = pd.read_csv(RAW / "eurostat_asylum_first_time_eu27_2021_2025.csv", keep_default_na=False)
    eu["iso3"] = eu.citizenship.map(i2)
    eu = eu.dropna(subset=["iso3"]).groupby(["iso3", "year"]).value.sum().rename("asylum").reset_index().assign(donor_iso3="EUR")
    a = pd.concat([a, eu])
    hosts = set(a.donor_iso3)
    g = g.merge(a, on=["donor_iso3", "iso3", "year"], how="left")
    g["european_host"] = g.donor_iso3.isin(hosts).astype(int)
    g.loc[g.european_host.eq(1), "asylum"] = g.loc[g.european_host.eq(1), "asylum"].fillna(0)
    g["lasy"] = np.log1p(g.asylum)
    g = g.sort_values(["donor_iso3", "iso3", "year"])
    g["lasy_lag"] = g.groupby(["donor_iso3", "iso3"]).lasy.shift(1).where(g.groupby(["donor_iso3", "iso3"]).year.diff().eq(1))
    g["lpin"], g["sev"] = np.log(g.pin), g.inform_severity
    g["dy"], g["ry"] = g.donor_iso3 + "_" + g.year.astype(str), g.iso3 + "_" + g.year.astype(str)
    return g, miss_d


def ppml(formula, data, label, keep, rows):
    # PPML cannot estimate an effect for a group whose funding is all zero; drop such donor-years and recipient-years
    data = data.copy()
    for fe in ("dy", "ry"):
        if f"C({fe})" in formula:
            data = data[data.groupby(fe).funding.transform("sum") > 0]
    data["funding"] = data.funding / 1e6   # USD million
    m = smf.glm(formula, data, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": data.iso3.astype("category").cat.codes}, maxiter=200)
    t = pd.DataFrame({"coef": m.params, "se": m.bse, "p": m.pvalues}).loc[keep]
    t["pct_effect"] = np.where(t.index.isin(["colony", "col45", "comlang", "contig"]), np.exp(t.coef) - 1, np.nan)
    print(f"\n### {label}\nPPML, N={int(m.nobs)} donor-recipient-years, donors={data.donor_iso3.nunique()}, "
          f"recipients={data.iso3.nunique()}, flows>0={int((data.funding > 0).sum())}")
    print(t.rename(index=LABELS).round(3).to_string())
    for v, r in t.iterrows():
        rows.append({"model": label, "variable": v, "label": LABELS.get(v, v), "coef": r.coef, "se": r.se, "p": r.p,
                     "pct_effect_dummy": r.pct_effect, "n": int(m.nobs), "donors": data.donor_iso3.nunique(), "recipients": data.iso3.nunique()})


def main():
    g, miss = build()
    rows = []
    print("Government donors with no ISO3 match (left out):", miss)
    print(f"Donor-recipient-years: {len(g)}; donors: {g.donor_iso3.nunique()}; recipients: {g.iso3.nunique()}; "
          f"years {g.year.min()}-{g.year.max()}; colonial pairs: {int(g[['donor_iso3','iso3']].drop_duplicates().merge(g[g.colony==1][['donor_iso3','iso3']].drop_duplicates()).shape[0])}")
    print("Colonial pairs in the sample:", sorted(set(map(tuple, g[g.colony == 1][["donor_iso3", "iso3"]].drop_duplicates().values))))
    ppml("funding ~ lpin + sev + colony + ldist + comlang + contig + C(dy)", g.dropna(subset=["lpin", "sev", "ldist"]),
         "A. Needs and ties, donor-year effects", ["lpin", "sev", "colony", "ldist", "comlang", "contig"], rows)
    ppml("funding ~ colony + ldist + comlang + contig + C(dy) + C(ry)", g.dropna(subset=["ldist"]),
         "B. Ties, donor-year and recipient-year effects (all governments)", ["colony", "ldist", "comlang", "contig"], rows)
    ppml("funding ~ col45 + ldist + comlang + contig + C(dy) + C(ry)", g.dropna(subset=["ldist"]),
         "C. Colonial relationship after 1945 only", ["col45", "ldist", "comlang", "contig"], rows)
    e = g[g.european_host.eq(1)].dropna(subset=["ldist", "lasy"])
    ppml("funding ~ lasy + colony + ldist + comlang + contig + C(dy) + C(ry)", e,
         "D. Asylum applications, European donors (EU and EFTA governments, European Commission; the UK has no Eurostat data after 2020)", ["lasy", "colony", "ldist", "comlang", "contig"], rows)
    el = e.dropna(subset=["lasy_lag"])
    ppml("funding ~ lasy_lag + colony + ldist + comlang + contig + C(dy) + C(ry)", el,
         "E. Asylum applications in the previous year, European donors", ["lasy_lag", "colony", "ldist", "comlang", "contig"], rows)
    # robustness: CEPII's own colony variable only (no short_only links), and each large former colonial power left out
    pairs = pd.read_csv(RAW / "cepii_pairs.csv").drop_duplicates(["donor_iso3", "iso3"])
    strict = e.drop(columns=["colony"]).merge(pairs[["donor_iso3", "iso3", "colony"]], on=["donor_iso3", "iso3"], how="left").fillna({"colony": 0})
    ppml("funding ~ lasy + colony + ldist + comlang + contig + C(dy) + C(ry)", strict,
         "F. As D, CEPII colony variable only", ["lasy", "colony"], rows)
    for out in ("FRA", "ESP", "ITA", "BEL", "DEU", "PRT"):
        ppml("funding ~ lasy + colony + ldist + comlang + contig + C(dy) + C(ry)", e[e.donor_iso3 != out],
             f"G. As D, without {out}", ["lasy", "colony"], rows)
    pd.DataFrame(rows).to_csv(RESULTS / "donor_model_coefficients.csv", index=False)
    g.drop(columns=["dy", "ry"]).to_csv(RESULTS / "donor_recipient_year.csv", index=False)


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    print(buf.getvalue())
    (RESULTS / "donor_model.txt").write_text(buf.getvalue())
