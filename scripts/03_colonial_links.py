"""Former colonial powers of each country, from CEPII's GeoDist (Mayer and
Zignago 2011). The two GeoDist files are downloaded to data/external/; only
the derived country-coloniser table is written to data/raw/.

cepii_column records where each link comes from:
  long        dyad colony = 1 and the partner in geo_cepii colonizer1-4
  short       dyad colony = 1 and the partner in short_colonizer1-3
  short_only  partner in short_colonizer1-3 while the dyad has colony = 0
              (added here; Haiti and France among them)
Successor states missing from the 2004 data inherit their predecessor's links.
"""
import pandas as pd
import requests

from common import CEPII_FIX, EXTERNAL, RAW

for f in ("dist_cepii.dta", "geo_cepii.dta"):
    p = EXTERNAL / f
    if not p.exists():
        r = requests.get(f"https://www.cepii.fr/distance/{f}", timeout=120)
        r.raise_for_status()
        p.write_bytes(r.content)

d = pd.read_stata(EXTERNAL / "dist_cepii.dta")
g = pd.read_stata(EXTERNAL / "geo_cepii.dta").drop_duplicates("iso3")
for c in ("iso_o", "iso_d"):
    d[c] = d[c].replace(CEPII_FIX)
g["iso3"] = g.iso3.replace(CEPII_FIX)
long_ = g.set_index("iso3")[["colonizer1", "colonizer2", "colonizer3", "colonizer4"]]
short = g.set_index("iso3")[["short_colonizer1", "short_colonizer2", "short_colonizer3"]]


def listed(table, iso):
    return set(table.loc[iso].dropna().replace(CEPII_FIX)) - {""} if iso in table.index else set()


links = d[d.colony == 1][["iso_o", "iso_d", "col45", "curcol"]].rename(columns={"iso_o": "iso3", "iso_d": "coloniser"})
links["cepii_column"] = [("long" if c in listed(long_, i) else "short" if c in listed(short, i) else "")
                         for i, c in zip(links.iso3, links.coloniser)]
links = links[links.cepii_column != ""]
have = set(zip(links.iso3, links.coloniser))
extra = [{"iso3": i, "coloniser": c, "col45": 0, "curcol": 0, "cepii_column": "short_only"}
         for i in short.index for c in listed(short, i) if (i, c) not in have]
links = pd.concat([links, pd.DataFrame(extra)], ignore_index=True)
for new, old in (("SSD", "SDN"), ("MNE", "YUG"), ("SRB", "YUG"), ("XKX", "YUG")):
    links = pd.concat([links, links[links.iso3 == old].assign(iso3=new)], ignore_index=True)
links.sort_values(["iso3", "coloniser"]).to_csv(RAW / "colonial_links_cepii.csv", index=False)
# distance and shared language for every pair of countries (used by the donor-level model)
pairs = d[["iso_o", "iso_d", "contig", "comlang_off", "colony", "col45", "distw", "dist"]].rename(columns={"iso_o": "donor_iso3", "iso_d": "iso3"})
pairs.to_csv(RAW / "cepii_pairs.csv", index=False)
# ISO2 to ISO3, used to match Eurostat citizenship codes
g[["iso2", "iso3", "country"]].to_csv(RAW / "iso2_iso3_cepii.csv", index=False)
print(len(links), "links")
