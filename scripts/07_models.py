"""Run the models on the panel and write results/.

All models are OLS with standard errors clustered by country, on the main
sample (country-years with an HRP, HNRP or flash appeal). The nested models
share one sample: country-years with every variable present (2022-2025, since
the lagged ReliefWeb count needs a previous year).

ACLED is read from data/restricted/ (run 05_fetch_acled.py first).

Outputs:
  results/models.txt            every table, as printed
  results/coefficients.csv      every coefficient
  results/r2_ladder.csv         R-squared of the nested models
  results/pin_residuals.csv     people in need against what the signals predict
"""
import io
import warnings
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from common import PROCESSED, RESTRICTED, RESULTS

warnings.filterwarnings("ignore")
LABELS = {"lpin": "log people in need", "sev": "INFORM Severity", "lfat": "log ACLED political-violence fatalities",
          "lidp": "log new conflict displacement (IDMC)", "ldis": "log new disaster displacement (IDMC)",
          "lfood": "log people in IPC/CH Phase 3+ (GRFC)", "lpop": "log population",
          "lasy": "log first-time EU asylum applicants", "lrw": "log ReliefWeb reports, previous year",
          "run": "years in a row under an appeal", "colsh": "share of plan funding from former colonial powers",
          "us": "US share of plan funding", "flash": "flash appeal, no HRP that year", "lfund_lag": "log funding, previous year",
          "echo_forgotten": "on ECHO's forgotten-crises list", "cerf_ufe": "CERF Underfunded Emergencies allocation"}
OUTCOMES = {"lfund": "log funding received", "lfpp": "log funding per person in need", "cov": "share of requirements funded"}
coefs, ladder = [], []


def fit(formula, data):
    m = smf.ols(formula, data).fit()
    used = data.loc[m.model.data.row_labels]
    return smf.ols(formula, used).fit(cov_type="cluster", cov_kwds={"groups": used.iso3}), used


def report(m, used, block, outcome, model, keep=None):
    t = pd.DataFrame({"coef": m.params, "se": m.bse, "p": m.pvalues})
    t = t.loc[[i for i in t.index if not i.startswith("C(") and i != "Intercept"] if keep is None else keep]
    print(f"\n### {model}: {OUTCOMES.get(outcome, outcome)}  N={int(m.nobs)}  countries={used.iso3.nunique()}  "
          f"R2={m.rsquared:.2f}  adj. R2={m.rsquared_adj:.2f}")
    print(t.rename(index=LABELS).round(3).to_string())
    for v, r in t.iterrows():
        coefs.append({"block": block, "outcome": outcome, "model": model, "variable": v, "label": LABELS.get(v, v),
                      "coef": r.coef, "se": r.se, "p": r.p, "n": int(m.nobs), "countries": used.iso3.nunique(), "r2": m.rsquared})


def main():
    d = pd.read_csv(PROCESSED / "funding_vs_needs_panel_2021_2025.csv")
    d = d.merge(pd.read_csv(RESTRICTED / "acled_country_year_2021_2025.csv"), on=["iso3", "year"], how="left")
    d = d[(d.main_sample == 1) & d.pin.gt(0) & d.funding_usd.gt(0)].copy()
    L = np.log1p
    d["lpin"], d["lfund"] = np.log(d.pin), np.log(d.funding_usd)
    d["lfpp"], d["cov"] = np.log(d.funding_per_pin_usd), d.coverage.clip(upper=1.5)
    d["sev"], d["lpop"] = d.inform_severity, np.log(d.population)
    d["lfat"] = L(d.acled_pv_fatalities.fillna(0))
    d["lidp"], d["ldis"] = L(d.idp_conflict_new.fillna(0)), L(d.idp_disaster_new.fillna(0))
    d["lfood"] = np.log(d.grfc_phase3plus.where(d.grfc_phase3plus > 0))
    d["lasy"], d["lrw"] = L(d.eu_first_time_asylum), L(d.reliefweb_reports_lag1)
    d["run"], d["colsh"], d["us"] = d.appeal_run_years, d.share_from_former_colonisers, d.us_share
    d["flash"] = ((d.has_flash == 1) & (d.has_hrp == 0)).astype(int)
    d["lfund_lag"] = np.log(d.funding_usd_lag1)

    needs = "lpin + sev + lfat + lidp + ldis + lfood + lpop"
    other = "lasy + lrw + run + colsh + us + flash"
    base = d.dropna(subset=["lpin", "sev", "lfat", "lidp", "ldis", "lfood", "lasy", "lrw", "colsh", "us", "lpop"])
    print(f"Common sample for the nested models: {len(base)} country-years, {base.iso3.nunique()} countries, "
          f"{base.year.min()}-{base.year.max()}")
    for y in OUTCOMES:
        print(f"\n================ {OUTCOMES[y]} ================")
        for model, f in (("M1 people in need", f"{y} ~ lpin"), ("M2 + INFORM Severity", f"{y} ~ lpin + sev"),
                         ("M3 + other needs measures", f"{y} ~ {needs}"), ("M4 + non-needs factors", f"{y} ~ {needs} + {other}"),
                         ("M5 M4 + year effects", f"{y} ~ {needs} + {other} + C(year)")):
            m, used = fit(f, base)
            ladder.append({"outcome": y, "outcome_label": OUTCOMES[y], "model": model, "r2": m.rsquared, "adj_r2": m.rsquared_adj, "n": int(m.nobs)})
            report(m, used, "nested", y, model)

    print("\n================ Within-country change (country and year effects) ================")
    w = d.dropna(subset=["lpin", "sev", "lfat", "lidp"])
    for y in ("lfund", "cov"):
        m, used = fit(f"{y} ~ lpin + sev + lfat + lidp + C(iso3) + C(year)", w)
        report(m, used, "within", y, "within-country", keep=["lpin", "sev", "lfat", "lidp"])

    print("\n================ Path dependency ================")
    p = d.dropna(subset=["lfund_lag", "lpin", "sev"])
    for f in ("lfund ~ lfund_lag", "lfund ~ lpin + sev", "lfund ~ lfund_lag + lpin + sev"):
        m, used = fit(f, p)
        report(m, used, "path", "lfund", f)

    print("\n================ What people in need follows ================")
    q = d.dropna(subset=["sev", "lfat", "lidp", "ldis", "lfood", "lpop"])
    m, used = fit("lpin ~ lpop + sev + lfat + lidp + ldis + lfood + C(year)", q)
    report(m, used, "pin", "lpin", "across countries", keep=["lpop", "sev", "lfat", "lidp", "ldis", "lfood"])
    res = used.assign(residual=m.resid, predicted_pin=np.exp(m.fittedvalues))[["iso3", "country", "year", "plan_codes", "pin", "predicted_pin", "residual"]]
    res.sort_values("residual").to_csv(RESULTS / "pin_residuals.csv", index=False)
    m, used = fit("lpin ~ sev + lfat + lidp + lfood + C(iso3) + C(year)", q)
    report(m, used, "pin", "lpin", "within-country", keep=["sev", "lfat", "lidp", "lfood"])

    print("\n================ Forgotten-crisis flags and the following year ================")
    d = d.sort_values(["iso3", "year"])
    nxt = d.groupby("iso3").year.diff(-1).eq(-1)
    d["cov_next"] = d.groupby("iso3")["cov"].shift(-1).where(nxt)
    d["lfpp_next"] = d.groupby("iso3")["lfpp"].shift(-1).where(nxt)
    f = d.dropna(subset=["cov_next", "lpin", "sev"])
    for y in ("cov_next", "lfpp_next"):
        m, used = fit(f"{y} ~ echo_forgotten + cerf_ufe + {y[:-5]} + lpin + sev + C(year)", f)
        report(m, used, "flags", y, "flags this year, outcome next year", keep=["echo_forgotten", "cerf_ufe"])
    print("\nMedian funding per person in need (USD), by ECHO flag:", d.groupby("echo_forgotten").funding_per_pin_usd.median().round(1).to_dict())
    print("Median funding per person in need (USD), by CERF UFE allocation:", d.groupby("cerf_ufe").funding_per_pin_usd.median().round(1).to_dict())


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    text = buf.getvalue()
    print(text)
    (RESULTS / "models.txt").write_text(text)
    pd.DataFrame(coefs).to_csv(RESULTS / "coefficients.csv", index=False)
    pd.DataFrame(ladder).to_csv(RESULTS / "r2_ladder.csv", index=False)
