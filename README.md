# Humanitarian Funding and Humanitarian Needs, 2021 to 2025

Data, code, models and charts for the PRISM Insights analysis of how humanitarian funding relates to the needs counted in OCHA's humanitarian plans. Every figure in the piece can be rebuilt from this repository.

## Question

Does funding received through HRPs, HNRPs and flash appeals follow the number of people in need (PiN) and the severity of crises? Which other factors predict it: attention, years under an appeal, donor mix, former colonial ties, migration to Europe?

## Data

One row per country and year, 2021 to 2025, for every country with a single-country humanitarian plan: 179 country-years in 45 countries. The main sample is the 155 country-years with an HRP, HNRP or flash appeal (38 countries).

| Measure | Source |
|---|---|
| People in need, people targeted, requirements | OCHA Humanitarian Programme Cycle (HPC) API |
| Funding received per plan | OCHA Financial Tracking Service (FTS) |
| Funding by donor | FTS |
| Crisis severity, risk | INFORM Severity Index, INFORM Risk Index |
| Political violence and civilian targeting | ACLED (aggregates published on HDX) |
| Conflict and disaster displacement | IDMC Global Internal Displacement Database |
| People in IPC/CH Phase 3 or above | Global Report on Food Crises (GRFC) |
| First-time asylum applicants in the EU27 | Eurostat (migr_asyappctza) |
| Reports on each country | ReliefWeb API |
| Forgotten crises | DG ECHO Forgotten Crisis Assessment (GGOPHA staff working documents) |
| Underfunded Emergencies and Rapid Response allocations | CERF |
| Former colonial powers | CEPII GeoDist (Mayer and Zignago, 2011) |
| Years under an appeal since 2000 | HPC API plan lists |
| Protection cluster people in need and funding | HPC and FTS, Global Protection Cluster countries |

PRISM (https://www.prismonitor.eu) collects most of these sources continuously and keeps the source and date of every figure. `data/README.md` describes every file and column.

**ACLED.** ACLED's terms do not allow its figures to be redistributed. The ACLED file is built by `scripts/05_fetch_acled.py` into `data/restricted/`, which this repository does not track. Cite as "ACLED, accessed 12 November 2026".

## Main results

Ordinary least squares, standard errors clustered by country. The nested models share one sample: 110 country-years in 34 countries, 2022 to 2025, with every variable present.

Share of the variation explained (R²):

| Measures | log funding received | log funding per person in need | share of requirements funded |
|---|---|---|---|
| People in need | 53% | 1% | 0% |
| + INFORM Severity | 65% | 26% | 0% |
| + violence, displacement, food insecurity, population | 72% | 41% | 12% |
| + ReliefWeb reports, years under an appeal, donor mix, colonial ties, EU asylum, flash appeal | 82% | 63% | 55% |
| + year effects | 85% | 69% | 68% |

- With people in need alone, funding received rises in proportion to it (elasticity 1.09) and funding per person in need is unrelated to it (R² 1%). At equal INFORM Severity, violence, displacement and food insecurity, the elasticity is 0.40 to 0.57. Within a country over time, the share funded falls as people in need rises (p = 0.006).
- People in need and INFORM Severity explain 0% of the variation in the share of requirements funded.
- With year effects, the share funded rises with the previous year's ReliefWeb reports (p < 0.001), with flash appeals (33 points, p < 0.001), with each year in a row under an appeal (1 point, p = 0.003), with the US share of plan funding (p = 0.025) and with political-violence fatalities (p = 0.006). At country level, the share of plan funding from former colonial powers (p = 0.29) and EU asylum applications (p = 0.19) show no association with the share funded; the donor-level model below tests both directly.
- The previous year's funding alone explains 81% of the variation in log funding received.
- Across countries, people in need rises with population and INFORM Severity, with food insecurity at the margin (p = 0.05), and falls with new conflict displacement (p = 0.006); R² 81%. Within a country over time, changes in people in need follow food insecurity (p < 0.001) and none of INFORM Severity, violence or displacement.
- Being on ECHO's forgotten-crises list or receiving a CERF Underfunded Emergencies allocation has no statistically significant association with the share funded or funding per person in need the next year; both selections draw partly on funding levels.

Donor-level model (`scripts/08_donor_model.py`): Poisson pseudo-maximum likelihood on each government donor, plan country and year, 2021 to 2025, with donor-year and recipient-year effects, so each donor's budget and everything about a crisis in a year are held constant. Funding is all FTS humanitarian funding from the donor to the country.

- Among 25 European donors (EU and EFTA governments and the European Commission), a former colonial power gives 64% more to its former colony (p = 0.002). Leaving out one former colonial power at a time gives 47% to 123%; CEPII's colony variable alone gives 52% (p = 0.012). Across 42 government donors, including the United States, the United Kingdom and Japan, the figure is 45% (p = 0.074). CEPII's post-1945 colonial relationship shows no association (p = 0.82).
- Among European donors, each doubling of first-time asylum applicants from a country in the donor country goes with 10% more funding from that donor to that country (p < 0.001); the previous year's applicants give 9% (p = 0.001).
- In a model with donor-year effects only, across 42 donors, INFORM Severity is associated with a larger share of a donor's funding (p < 0.001); people in need, at equal severity, has no association (p = 0.64).

All results are associations among 34 to 38 countries and, at donor level, 42 donors. `results/models.txt` holds every table.

## Repository layout

```
data/raw/          inputs as plain CSV, one file per source
data/processed/    the country-year panel (no ACLED columns)
data/restricted/   ACLED, rebuilt locally, not tracked
data/external/     third-party downloads (CEPII, ACLED workbooks), not tracked
scripts/           00 to 09, run in order
results/           model output: tables, coefficients, R² ladder, people-in-need residuals, donor-level model
charts/            PNG and SVG
```

## Rebuilding

Python 3.10 or later.

```bash
pip install -r requirements.txt
cd scripts
python 01_fetch_fts_plan_history.py
RELIEFWEB_APPNAME=<your appname> python 02_fetch_reliefweb.py
python 03_colonial_links.py
python 04_echo_forgotten_crises.py
python 05_fetch_acled.py
python 06_build_panel.py
python 07_models.py
python 08_donor_model.py
python 09_charts.py
```

`00_export_from_prism.py` wrote the files in `data/raw/` that come from PRISM's own collection (plans, donors, INFORM, IDMC, GRFC, Eurostat, CERF, protection). It runs only inside PRISM's codebase; the CSV files it produced are committed, so the other steps start from them. Steps 01 to 05 fetch fresh copies of the public sources, so figures can move as sources revise their data.

## Limits

- PiN is the highest figure across a country's plans in a year; requirements and funding are summed. Regional plans are left out.
- OCHA restricted PiN to areas in Phase 3 or above from 2026, so the panel stops at 2025.
- INFORM Severity is the yearly mean of the country's highest crisis score each month (0 to 5 scale through 2025).
- ReliefWeb reports measure how much the humanitarian system publishes on a country; well-funded responses publish more.
- ECHO's assessment uses FTS aid per person, and CERF's Underfunded Emergencies window selects by funding level, so both flags are partly built from the outcome.
- The country-level colonial share covers funding through the plan only; the donor-level model uses all FTS funding from each donor to each country. Eurostat covers asylum in EU and EFTA states, so the asylum models leave out the United Kingdom after 2020 and every non-European donor. The asylum association is consistent with migration-control objectives and with diaspora ties; the data cannot separate them.
- The European Commission takes Brussels' distances in the donor-level model.

## Related Work

- Yüksel, U. (2026). *Humanitarian funding cuts: power, prioritisation, and systemic injustice in global humanitarian aid*. EUI School of Transnational Governance, Policy Paper 2026/02. European University Institute. https://doi.org/10.2870/2232871. This repository tests, on 2021 to 2025 data, the paper's argument that allocation reflects geopolitical interest, colonial legacies, media visibility and path dependency alongside need.
- Lilly, D. and Pearson, M. (2026). *How to reform the Humanitarian Programme Cycle*. HPG Working Paper, ODI Global, October 2026.
- Fink, G. and Redaelli, S. (2011). Determinants of International Emergency Aid: Humanitarian Need Only? *World Development*, 39(5), 741-757.
- Mena, R. and Hilhorst, D. (2022). Path dependency when prioritising disaster and humanitarian response under high levels of conflict: a qualitative case study in South Sudan. *Journal of International Humanitarian Action*, 7, 5. https://doi.org/10.1186/s41018-021-00111-w
- Global Protection Cluster (2026). *Global Protection Update: Protection in Times of Constraint*, October 2026.

## Contributors

- Umutcan Yüksel (PRISM): research question, design, sources and editorial direction.
- Claude (Anthropic): code, data assembly, models, charts and documentation, under the author's direction.

## Licences

Code (scripts/): MIT, see `LICENSE`. Data, results and charts: CC BY-SA 4.0 for PRISM's compilation and computed fields, see `LICENSE-DATA`, which lists each source's own terms and the attribution each asks for. ACLED figures are not redistributed.

## Citation

PRISM, Protection, Risk and Impact Severity Monitor (2026). Humanitarian Funding and Humanitarian Needs, 2021 to 2025: data and code. https://www.prismonitor.eu
