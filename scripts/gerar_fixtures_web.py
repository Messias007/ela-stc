"""Generate the browser-engine fixtures from the Python implementation.

Writes web/fixtures/caso.json (engine input for each aircraft) and web/fixtures/expected.json (Python results
for a set of parameter cases). Run: python scripts/gerar_fixtures_web.py [case.yaml]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ela_stc.analysis import analyze, garmin_net_change, is_landing_light, is_tx  # noqa: E402
from ela_stc.loader import load_case  # noqa: E402
from ela_stc.models import Installation  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "caso_c172.yaml")
OUT = os.path.join(ROOT, "web", "fixtures")
os.makedirs(OUT, exist_ok=True)


def engine_model(ac, inst):
    rem = set(inst.removed_for(ac.model))
    items = []

    def add(l, st):
        mx = l.at_voltage(ac.voltage)
        ty = l.at_voltage(ac.voltage, True).current_a if l.typical_by_v else None
        items.append(dict(n=l.name, bus=l.bus, cls=l.cls, st=st, imax=mx.current_a, ityp=ty, ibat=l.current_batt_a,
                          bk=mx.breaker_a, cp=bool(l.constant_power), duty={k: v for k, v in l.duty.items() if v},
                          src=l.source, tx=is_tx(l.name), ll=is_landing_light(l), flap="flap motor" in l.name.lower(),
                          pitot="pitot" in l.name.lower(), radio=l.radio, circuit=l.circuit))
    for l in ac.baseline_loads:
        add(l, "removed" if l.name in rem else "base")
    for l in inst.added:
        add(l, "added")
    b = ac.battery
    return dict(model=ac.model, V=ac.voltage, Vb=ac.battery_v, alt=ac.alternator_a, req=ac.required_endurance_min,
                bat=dict(C=b.capacity_ah, n=b.peukert_n, H=b.rated_hours, soh=b.soh, soc=b.soc, kt=b.temp_factor,
                         scen=b.capacity_scenarios), items=items)


CASES = [{}, {"use_typical": 0}, {"pitot_em": 0}, {"cp_scaling": 0}, {"approach_min": 0},
         {"soh": 0.6, "soc": 0.8, "temp_factor": 0.7, "peukert_n": 1.3, "preshed_min": 10},
         {"bat_capacity_factor": 25 / 22}, {"tx_duty": 0.2, "landing_light_duty": 0.3}, {"casa_fraction": 0.75},
         {"soh": 0.3, "temp_factor": 0.5}, {"soh": 0.1, "soc": 0.5, "temp_factor": 0.3}]
KEYS = ["alt_frac_cont", "alt_frac_avg", "breaker_frac", "i_pre", "i_shed", "i_app", "endurance_casa_min",
        "endurance_peukert_min", "margin_min", "casa_profile_feasible"]

aml, inst = load_case(CASE)
models = [engine_model(ac, inst) for ac in aml]
exp = []
for mi, ac in enumerate(aml):
    for installed in (0, 1):
        for c in CASES:
            r = analyze(ac, inst if installed else Installation(name="none"), c)
            exp.append(dict(m=mi, inst=installed, p=c, **{k: r[k] for k in KEYS}))
    exp.append(dict(m=mi, garmin=garmin_net_change(ac, inst)["net_a"]))
json.dump(models, open(os.path.join(OUT, "caso.json"), "w"), ensure_ascii=False)
json.dump(exp, open(os.path.join(OUT, "expected.json"), "w"))
print(f"{len(models)} models, {len(exp)} expected records -> {OUT}")
