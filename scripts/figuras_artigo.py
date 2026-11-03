"""Figuras do artigo (MDPI): gera paper/figures/*.pdf a partir do caso C172 (método v3)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from ela_stc.loader import load_case
from ela_stc.analysis import analyze, BASE
from ela_stc.models import Installation
from ela_stc.sensitivity import tornado, PARAMS, global_mc

OUT = os.path.join(os.path.dirname(__file__), "..", "paper", "figures")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "axes.titlesize": 9.5})
C_BEF, C_AFT, C_LIM, C_BAD = "#8a9aab", "#1d5f9e", "#b86e00", "#b3261e"
aml, inst = load_case(os.path.join(os.path.dirname(__file__), "..", "data", "caso_c172.yaml"))
NONE = Installation(name="none")
TITLES = ["(a) Cessna 172M 1976, 14 V", "(b) Cessna 172R/S, 28 V"]
PH = ["ground", "taxi", "takeoff_climb", "cruise", "landing"]
PHL = ["Ground", "Taxi", "Takeoff/\nclimb", "Cruise", "Landing"]

# Figure 1: framework
fig, ax = plt.subplots(figsize=(7.2, 2.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 3)
boxes = [(0.1, "Inputs", "TC-holder ELA\nper model\nEquipment manuals\nRemovals per model\nBattery SOH, SOC, kT"),
         (2.6, "Configuration", "Removed and\nadded loads\nDuty per phase,\nRX/TX pairing\nCircuits, breakers"),
         (5.1, "Analysis", "Phase loads\nCircuit loads\nSequential battery\ndepletion (CASA,\nPeukert), net change"),
         (7.6, "Criteria, outputs", "R1a to R3 with\nsource paragraph\nAML matrix\nTornado (method),\nMonte Carlo (physical)")]
for x, t, b in boxes:
    ax.add_patch(FancyBboxPatch((x, 0.25), 2.25, 2.45, boxstyle="round,pad=0.02,rounding_size=0.08", fc="#eef2f5", ec="#13202b", lw=0.8))
    ax.text(x + 1.125, 2.42, t, ha="center", va="center", weight="bold", fontsize=9)
    ax.text(x + 1.125, 1.3, b, ha="center", va="center", fontsize=6.6, linespacing=1.5)
for x in (2.38, 4.88, 7.38):
    ax.annotate("", xy=(x + 0.2, 1.45), xytext=(x - 0.02, 1.45), arrowprops=dict(arrowstyle="-|>", color="#13202b", lw=1))
fig.savefig(os.path.join(OUT, "fig1_framework.pdf"), bbox_inches="tight"); plt.close(fig)

# Figure 2: phase loads
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
for ax, ac, ti in zip(axs, aml, TITLES):
    b, a = analyze(ac, NONE), analyze(ac, inst)
    x = np.arange(len(PH)); w = 0.36
    for off, r, c, lab in ((-w / 2, b, C_BEF, "Before"), (w / 2, a, C_AFT, "After")):
        av = [r["avg_by_phase"][p] / ac.alternator_a * 100 for p in PH]
        co = [r["cont_by_phase"][p] / ac.alternator_a * 100 for p in PH]
        ax.bar(x + off, av, w, color=c, label=lab + " (average, R1b)")
        ax.hlines(co, x + off - w / 2 + 0.03, x + off + w / 2 - 0.03, colors="white", lw=1.6)
    ax.axhline(80, color=C_LIM, ls="--", lw=1.2, label="80 % limit")
    ax.set_xticks(x); ax.set_xticklabels(PHL, fontsize=8); ax.set_title(ti, loc="left")
axs[0].set_ylabel("Load (% of alternator rating)")
axs[0].legend(fontsize=6.6, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.0))
axs[0].set_ylim(0, 112)
fig.text(0.5, -0.04, "White ticks: continuous load only (R1a).", ha="center", fontsize=7.5)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_phase_loads.pdf"), bbox_inches="tight"); plt.close(fig)

# Figure 3: battery profiles (CASA available-charge model, sequential depletion)
def profile(ac, i):
    r = analyze(ac, i); p = BASE; C1 = r["battery_ah_1h"]
    bat = ac.battery
    av = C1 * 60 * p["casa_fraction"]; tp, ta = p["preshed_min"], p["approach_min"]
    rp = r["i_pre"] * (1.2 if r["i_pre"] > 2 * C1 else 1.0)
    t, q = [0.0], [av]
    if rp * tp >= av:
        t.append(av / rp); q.append(0.0)
    else:
        q1 = av - rp * tp; t.append(tp); q.append(q1)
        if q1 > r["i_app"] * ta:
            t1 = tp + (q1 - r["i_app"] * ta) / r["i_shed"]; t += [t1, t1 + ta]; q += [r["i_app"] * ta, 0.0]
        else:
            t.append(tp + q1 / r["i_app"]); q.append(0.0)
    return np.array(t), np.array(q) / av * 100, r
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True)
for ax, ac, ti in zip(axs, aml, TITLES):
    for i, c, lab in ((NONE, C_BEF, "Before"), (inst, C_AFT, "After")):
        t, q, r = profile(ac, i)
        ax.plot(t, q, color=c, lw=1.8, label=f"{lab}: CASA {r['endurance_casa_min']:.1f} min, Peukert {r['endurance_peukert_min']:.1f} min")
    ax.axvline(30, color=C_LIM, ls="--", lw=1.2); ax.text(30.8, 97, "30 min", color=C_LIM, fontsize=7.5)
    ax.set_xlim(0, max(65, ax.get_xlim()[1])); ax.set_ylim(0, 105); ax.set_xlabel("Time after alternator loss (min)"); ax.set_title(ti, loc="left")
    ax.legend(fontsize=6.6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.24))
axs[0].set_ylabel("CASA available charge remaining (%)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_battery.pdf"), bbox_inches="tight"); plt.close(fig)

# Figure 4: tornado of margin (deterministic, one factor at a time)
SHORTL = {"use_typical": "Installed current (max)*", "tx_duty": "Transmit duty", "landing_light_duty": "Landing-light duty",
          "soh": "Battery SOH", "soc": "Battery SOC", "temp_factor": "Temperature factor", "peukert_n": "Peukert exponent",
          "casa_fraction": "CASA fraction*", "preshed_min": "Pre-shed time*", "pitot_em": "Pitot heat in emergency*",
          "cp_scaling": "Battery-voltage currents*", "bat_capacity_factor": "14 V battery capacity*"}
C_LOWER, C_HIGHER = "#c4622d", "#1d5f9e"
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2))
for ax, ac, ti in zip(axs, aml, TITLES):
    rows = []
    for prm, t in zip(PARAMS, tornado(ac, inst)):
        lo, hi, base = t["margin_low"], t["margin_high"], t["margin_base"]
        if max(abs(lo - base), abs(hi - base)) > 0.05: rows.append((SHORTL[prm.key], lo, hi, base))
    rows.sort(key=lambda r: max(abs(r[1] - r[3]), abs(r[2] - r[3])))
    for k, (lab, lo, hi, base) in enumerate(rows):
        ax.barh(k, min(lo, hi) - base, left=base, color=C_LOWER, height=0.6)
        ax.barh(k, max(lo, hi) - base, left=base, color=C_HIGHER, height=0.6)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=7.2)
    ax.axvline(rows[0][3], color="#13202b", lw=0.8, ls=":"); ax.axvline(0, color=C_BAD, lw=1.2)
    ax.set_xlabel("Margin over 30 min (min)"); ax.set_title(ti, loc="left")
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=C_LOWER, label="Setting that lowers the margin"), Patch(color=C_HIGHER, label="Setting that raises the margin")],
           loc="lower center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.05))
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(OUT, "fig4_tornado.pdf"), bbox_inches="tight"); plt.close(fig)

# Figure 5: Monte Carlo of margin, physical variability only (serviceable and degraded battery)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
for ax, ac, ti in zip(axs, aml, TITLES):
    r = global_mc(ac, inst, samples=True); rd = global_mc(ac, inst, degraded=True, samples=True)
    bins = np.linspace(min(r["margin"].min(), rd["margin"].min()), max(r["margin"].max(), rd["margin"].max()), 45)
    ax.hist(r["margin"], bins=bins, color=C_AFT, alpha=0.85, label=f"SOH 0.8-1.0: {r['p_margin_negative']*100:.1f}% < 0")
    ax.hist(rd["margin"], bins=bins, color=C_LOWER, alpha=0.55, label=f"SOH 0.6-0.8: {rd['p_margin_negative']*100:.1f}% < 0")
    ax.axvline(0, color=C_BAD, lw=1.4, zorder=5); ax.set_title(ti, loc="left"); ax.set_xlabel("Margin over 30 min (min)")
    ax.legend(fontsize=6.6, frameon=False, loc="upper left")
axs[0].set_ylabel("Sampled scenarios (N = 5000)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5_montecarlo.pdf"), bbox_inches="tight"); plt.close(fig)
print("ok", sorted(os.listdir(OUT)))
