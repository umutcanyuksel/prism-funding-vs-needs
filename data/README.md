# Data

## data/raw/

| File | Content | Source, date | Written by |
|---|---|---|---|
| `hpc_fts_plans_2021_2025.csv` | One row per plan and country: population, people affected, in need and targeted, requirements, funding received | OCHA HPC API and FTS (`fts/flow?planid`), via PRISM, refreshed 11 Nov 2026 | 00 |
| `fts_plan_donors_2021_2025.csv` | Funding by donor for each country's primary plan(s), 55 countries | FTS, via PRISM, 2 Nov 2026 | 00 |
| `protection_cluster_2021_2025.csv` | Protection cluster and AoR people in need, targeted, requirement and funding received | HPC and FTS, via PRISM, 23 Oct 2026; Global Protection Cluster countries | 00 |
| `inform_severity_crisis_month_2021_2025.csv` | INFORM Severity Index for every crisis and month, 0 to 5 scale | INFORM Severity, PRISM's archive, 9 Nov 2026 | 00 |
| `inform_risk_2021_2025.csv` | INFORM Risk Index, each year's release | INFORM Risk, PRISM's archive, 9 Nov 2026 | 00 |
| `idmc_gidd_2021_2025.csv` | Conflict and disaster displacement, new and total | IDMC GIDD, via PRISM | 00 |
| `grfc_phase3plus_2021_2025.csv` | Population analysed and in IPC/CH Phase 3 or above | GRFC editions, via PRISM | 00 |
| `eurostat_asylum_first_time_eu27_2021_2025.csv` | First-time asylum applicants in the EU27 by citizenship (ISO2) | Eurostat migr_asyappctza, via PRISM | 00 |
| `cerf_allocations_2021_2025.csv` | CERF allocations by country, year, emergency type and window | CERF, via PRISM | 00 |
| `fts_plan_history_2000_2025.csv` | Every plan listed for 2000 to 2025, one row per plan and country | HPC API `v1/public/plan/year`, 12 Nov 2026 | 01 |
| `reliefweb_counts_2021_2025.csv` | Reports with the country as primary country, by publication year; all sources and Media sources | ReliefWeb API v2, 12 Nov 2026 | 02 |
| `colonial_links_cepii.csv` | Country and former colonial power; `cepii_column` gives the GeoDist field each link comes from | CEPII GeoDist, downloaded 12 Nov 2026 | 03 |
| `iso2_iso3_cepii.csv` | ISO2 to ISO3 codes, for Eurostat citizenship | CEPII geo_cepii | 03 |
| `fts_donor_by_country_2021_2025.csv` | Each top-100 donor's humanitarian funding by recipient country, inside and outside plans | FTS, via PRISM, 2 Nov 2026 | 00 |
| `eurostat_asylum_first_time_by_host_2021_2025.csv` | First-time asylum applicants by citizenship and by the EU or EFTA state where they applied | Eurostat migr_asyappctza, via PRISM | 00 |
| `cepii_pairs.csv` | Distance, shared border, common official language and colonial variables for every pair of countries | CEPII GeoDist dist_cepii | 03 |
| `echo_forgotten_crises_2021_2026.csv` | DG ECHO's forgotten crises, one row per crisis, with the countries each maps to | GGOPHA: SWD(2020) 253, SWD(2021) 312, SWD(2022) 352, SWD(2023) 354, SWD(2024) 257; DG ECHO page for 2026 | 04 |

Notes:
- ReliefWeb's Media source type returns 23 to 164 reports a year across all countries in the file, so `reports_media` is kept for reference only.
- CEPII's GeoDist data date from 2004. Codes are recoded to current ISO3 (PAL to PSE, ZAR to COD, TMP to TLS, ROM to ROU); South Sudan takes Sudan's links; Serbia, Montenegro and Kosovo take Yugoslavia's. `short_only` links are listed as short colonisers in geo_cepii while the dyad has `colony = 0` (Haiti and France, Afghanistan and the United Kingdom, Ethiopia and Italy, among others). CEPII counts Ottoman rule as colonial.
- ECHO's list names crises; three need a judgement to map to countries, recorded in `mapping_note`.

## data/processed/funding_vs_needs_panel_2021_2025.csv

One row per country and year.

| Column | Meaning |
|---|---|
| `iso3`, `country`, `year` | |
| `plan_codes`, `n_plans` | Plans counted that year: HRP/HNRP (code H), flash appeal (F), single-country plans of other types (O, R) |
| `has_hrp`, `has_flash`, `has_other_plan` | 0/1 |
| `main_sample` | 1 when the country had an HRP, HNRP or flash appeal that year |
| `population`, `pin`, `targeted` | Highest figure across the year's plans |
| `requirements_usd`, `funding_usd` | Summed across the year's plans |
| `coverage` | funding / requirements |
| `funding_per_pin_usd`, `requirements_per_pin_usd`, `pin_share_of_population`, `targeted_share_of_pin` | Ratios |
| `funding_usd_lag1` | Previous year's funding, when the country had a plan that year |
| `appeal_years_since_2000`, `appeal_run_years` | Years with a single-country plan before this year; unbroken run up to this year |
| `inform_severity`, `inform_severity_months` | Yearly mean of the country's highest crisis score each month; months observed |
| `inform_risk` | INFORM Risk Index |
| `idps_conflict_stock`, `idp_conflict_new`, `idp_disaster_new` | IDMC |
| `grfc_phase3plus`, `grfc_phase3plus_pct` | People in IPC/CH Phase 3 or above; share of the population analysed |
| `eu_first_time_asylum` | First-time asylum applicants in the EU27 from the country |
| `reliefweb_reports`, `reliefweb_reports_lag1`, `reliefweb_media_reports` | ReliefWeb reports, this year and the previous year |
| `echo_forgotten`, `echo_forgotten_crises` | On ECHO's forgotten-crises list that year; the crisis names |
| `cerf_ufe_usd`, `cerf_rr_usd`, `cerf_ufe` | CERF Underfunded Emergencies and Rapid Response allocations; 1 when an Underfunded Emergencies allocation was made |
| `former_colonisers` | ISO3 codes of former colonial powers |
| `from_former_colonisers_usd`, `share_from_former_colonisers` | Plan funding from the governments of former colonial powers |
| `plan_donor_total_usd`, `top_donor`, `top_donor_share`, `us_share`, `echo_share`, `donor_hhi` | Donor mix of the primary plan(s); HHI is the sum of squared donor shares |
| `protection_pin`, `protection_target`, `protection_required_usd`, `protection_received_usd`, `protection_coverage` | Protection cluster, Global Protection Cluster countries |

ACLED columns (`acled_pv_events`, `acled_pv_fatalities`, `acled_ct_events`, `acled_ct_fatalities`) are joined in `07_models.py` from `data/restricted/` and never written to this file.

## results/donor_recipient_year.csv

The donor-level model's data: one row per government donor (ISO3; `EUR` for the European Commission), plan country and year, with FTS funding (`funding`, USD, 0 when the donor funded the country nothing that year), `colony`, `col45`, `contig`, `comlang`, `ldist`, first-time asylum applicants from the country in the donor country (`asylum`, European donors only), people in need and INFORM Severity.
