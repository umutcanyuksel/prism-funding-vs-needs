"""Charts for the piece, as PNG (for the web) and SVG (editable), in charts/.
No chart shows an ACLED figure."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from common import CHARTS, PROCESSED, RAW, RESULTS

INK, MUTED, RULE, BLUE, PERI = "#0B1B33", "#4A5972", "#D5DAE2", "#1e40af", "#8FB0FF"
BLUES = LinearSegmentedColormap.from_list("prism_blues", ["#DCE6FF", PERI, BLUE, "#0B1B33"])
plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"], "font.size": 10,
                     "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": RULE, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white"})
SOURCE_PLANS = "Source: OCHA HPC and FTS, via PRISM (accessed 11 November 2026). Plans: HRP, HNRP and flash appeals."


def frame(fig, title, subtitle, source):
    fig.text(0.06, 0.965, title, fontsize=15, fontweight="bold", color=INK, va="top", family="serif")
    fig.text(0.06, 0.915, subtitle, fontsize=9.5, color=MUTED, va="top", wrap=True)
    fig.text(0.06, 0.025, source, fontsize=8, color=MUTED)


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(CHARTS / f"{name}.{ext}", dpi=200)
    plt.close(fig)


def money(v):
    return f"${v / 1e9:.0f}bn" if v >= 1e9 else f"${v / 1e6:.0f}m" if v >= 1e6 else f"${v:,.0f}"


def people(v):
    return f"{v / 1e6:.0f}m" if v >= 1e6 else f"{v / 1e3:.0f}k"


d = pd.read_csv(PROCESSED / "funding_vs_needs_panel_2021_2025.csv")
m = d[(d.main_sample == 1) & d.pin.gt(0) & d.funding_usd.gt(0)].copy()

# 1 people in need against funding received, coloured by the share funded
fig, ax = plt.subplots(figsize=(9, 6.6))
fig.subplots_adjust(left=0.1, right=0.86, top=0.82, bottom=0.12)
xs = np.logspace(5, 8.6, 50)
for per in (10, 100, 1000):
    ax.plot(xs, xs * per, color=RULE, lw=0.8, zorder=0)
    ax.text(1.15e5, 1.15e5 * per * 1.25, f"${per:,} per person", color=MUTED, fontsize=8, ha="left")
sc = ax.scatter(m.pin, m.funding_usd, c=m.coverage.clip(upper=1), cmap=BLUES, vmin=0, vmax=1, s=34, edgecolor="white", lw=0.5, zorder=2)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(1e5, 4e7); ax.set_ylim(1e6, 1e10)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: people(v)))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: money(v)))
ax.set_xlabel("People in need (log scale)"); ax.set_ylabel("Funding received (log scale)")
ax.grid(True, which="major", color=RULE, lw=0.5, alpha=0.6)
LABEL = {("PSE", 2025): (-60, 18), ("UKR", 2022): (-70, 22), ("ZWE", 2025): (40, -20), ("ZMB", 2025): (-50, -28), ("MWI", 2025): (35, 22)}
for (iso, yr), (dx, dy) in LABEL.items():
    r = m[(m.iso3 == iso) & (m.year == yr)].iloc[0]
    name = {"PSE": "oPt"}.get(iso, r.country)
    ax.annotate(f"{name} {yr}", (r.pin, r.funding_usd), xytext=(dx, dy), textcoords="offset points", fontsize=8, color=INK,
                ha="left" if dx > 0 else "right", va="center",
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6, "shrinkA": 0, "shrinkB": 4})
r2_fund = np.corrcoef(np.log(m.pin), np.log(m.funding_usd))[0, 1] ** 2
r2_cov = np.corrcoef(np.log(m.pin), m.coverage.clip(upper=1.5))[0, 1] ** 2
cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02)
cb.set_label("Share of requirements funded"); cb.ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1)); cb.outline.set_visible(False)
frame(fig, "People in Need and Funding Received, 2021 to 2025",
      f"Each dot is a country and year with an HRP, HNRP or flash appeal ({len(m)}). People in need explains {r2_fund:.0%} of the variation in\n"
      f"funding received (log scale) and {r2_cov:.0%} of the variation in the share of requirements funded.", SOURCE_PLANS)
save(fig, "01_people_in_need_and_funding")

# 2 funding per person in need, 2025, with ECHO's forgotten crises marked
y = m[m.year.eq(2025)].sort_values("funding_per_pin_usd")
fig, ax = plt.subplots(figsize=(9, 0.26 * len(y) + 2.2))
fig.subplots_adjust(left=0.26, right=0.95, top=1 - 1.25 / (0.26 * len(y) + 2.2), bottom=1.0 / (0.26 * len(y) + 2.2))
yy = np.arange(len(y))
ax.hlines(yy, 0, y.funding_per_pin_usd, color=RULE, lw=1)
fc = y.echo_forgotten.map({1: "white", 0: BLUE})
ax.scatter(y.funding_per_pin_usd, yy, s=40, color=fc, edgecolor=BLUE, lw=1.4, zorder=3)
for i, v in zip(yy, y.funding_per_pin_usd):
    ax.annotate(f"${v:,.0f}", (v, i), xytext=(8, 0), textcoords="offset points", va="center", fontsize=8, color=MUTED)
ax.set_yticks(yy, y.country, fontsize=9); ax.tick_params(axis="y", length=0)
ax.set_xlabel("Funding received per person in need, USD")
med = y.funding_per_pin_usd.median()
ax.axvline(med, color=MUTED, lw=0.8, ls=":"); ax.text(med + 4, len(y) - 0.4, f"median ${med:,.0f}", fontsize=8, color=MUTED)
ax.scatter([], [], s=40, color=BLUE, label="Other plans"); ax.scatter([], [], s=40, color="white", edgecolor=BLUE, lw=1.4, label="On ECHO's 2025 forgotten-crises list")
ax.legend(loc="lower right", frameon=False, fontsize=8.5)
frame(fig, "Funding per Person in Need, 2025",
      f"Funding received through each country's HRP, HNRP or flash appeal(s), divided by people in need ({len(y)} countries).",
      SOURCE_PLANS + " ECHO list: SWD(2024) 257.")
save(fig, "02_funding_per_person_in_need_2025")

# 3 how much each model explains
lad = pd.read_csv(RESULTS / "r2_ladder.csv")
steps = ["People in need", "+ INFORM\nSeverity", "+ violence,\ndisplacement,\nfood insecurity", "+ attention, history,\ndonor mix", "+ year\neffects"]
fig, ax = plt.subplots(figsize=(9, 5.6))
fig.subplots_adjust(left=0.08, right=0.76, top=0.8, bottom=0.2)
style = {"lfund": (INK, "-"), "lfpp": (BLUE, "-"), "cov": (PERI, "-")}
for out, gr in lad.groupby("outcome", sort=False):
    c, ls = style[out]
    ax.plot(range(5), gr.r2, color=c, ls=ls, lw=2.2, marker="o", ms=6)
    nudge = {"lfund": 0, "lfpp": 0.06, "cov": -0.06}[out]
    name = {"lfund": "Funding received\n(log)", "lfpp": "Funding per person\nin need (log)", "cov": "Share of requirements\nfunded"}[out]
    ax.text(4.15, gr.r2.iloc[-1] + nudge, f"{name}: {gr.r2.iloc[0]:.0%} to {gr.r2.iloc[-1]:.0%}", va="center", fontsize=8.5, color=c)
ax.set_xticks(range(5), steps, fontsize=8.5); ax.set_ylim(0, 1)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1)); ax.set_ylabel("Variation explained (R²)")
ax.grid(True, axis="y", color=RULE, lw=0.5); ax.set_xlim(-0.2, 4.1)

n = int(lad.n.iloc[0])
frame(fig, "Variation Explained by Each Set of Measures, 2022 to 2025",
      f"OLS on {n} country-years in 34 countries with an HRP, HNRP or flash appeal; each step adds measures to the one before.\n"
      "People in need and INFORM Severity explain 0% of the variation in the share of requirements funded.",
      "Sources: OCHA HPC and FTS; INFORM Severity and Risk; ACLED (accessed 12 November 2026); IDMC; GRFC; ReliefWeb; Eurostat; CEPII; via PRISM.")
save(fig, "03_variation_explained")
print("charts written to", CHARTS)

# 4 donor-level associations (PPML), European donors; written only when 08_donor_model.py has run
coef_path = RESULTS / "donor_model_coefficients.csv"
if coef_path.exists():
    c = pd.read_csv(coef_path)
    d_ = c[c.model.str.startswith("D.")].set_index("variable")
    lo = c[c.model.str.startswith("G.") & c.variable.eq("colony")].pct_effect_dummy
    a_ = c[c.model.str.startswith("A.")].set_index("variable")
    b_col, p_col = d_.loc["colony", "coef"], d_.loc["colony", "p"]
    b_asy, se_asy, p_asy = d_.loc["lasy", "coef"], d_.loc["lasy", "se"], d_.loc["lasy", "p"]
    rows_ = [("Former colonial power", np.exp(b_col) - 1, lo.min(), lo.max(), "range leaving out one former colonial power at a time", p_col),
             ("Asylum applicants from the country\nin the donor country, doubled", 2 ** b_asy - 1, 2 ** (b_asy - 1.96 * se_asy) - 1,
              2 ** (b_asy + 1.96 * se_asy) - 1, "95% confidence interval", p_asy)]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    fig.subplots_adjust(left=0.3, right=0.95, top=0.7, bottom=0.18)
    ys = np.array([1, 0])
    for y_, (lab, v, lo_, hi_, note, pv) in zip(ys, rows_):
        ax.barh(y_, v, color=BLUE, height=0.5)
        ax.plot([lo_, hi_], [y_, y_], color=INK, lw=1.2)
        ax.plot([lo_, lo_], [y_ - 0.08, y_ + 0.08], color=INK, lw=1.2); ax.plot([hi_, hi_], [y_ - 0.08, y_ + 0.08], color=INK, lw=1.2)
        ptxt = "p < 0.001" if pv < 0.001 else f"p = {pv:.3f}"
        ax.annotate(f"{v:+.0%} ({ptxt})", (hi_, y_), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.set_yticks(ys, [r[0] for r in rows_], fontsize=9.5); ax.tick_params(axis="y", length=0)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1)); ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("Difference in funding from a European donor to a country"); ax.grid(True, axis="x", color=RULE, lw=0.5)
    ax.set_xlim(0, 2.4)
    n_d = int(d_.loc["colony", "n"])
    frame(fig, "Former Colonial Ties, Asylum and Donor Funding, 2021 to 2025",
          f"PPML, 25 European donors, {int(d_.loc['colony', 'recipients'])} plan countries, 2021 to 2025 ({n_d:,} observations), with each donor's yearly budget\n"
          "and each crisis-year held constant. Lines: range leaving out one former colonial power at a time; 95% confidence interval.",
          "Sources: FTS donor funding by country; CEPII GeoDist; Eurostat migr_asyappctza; INFORM Severity; OCHA HPC; via PRISM.")
    save(fig, "04_colonial_ties_asylum_and_funding")
