"""ELA method v2: single implementation used by the rule engine, the sensitivity study and the report.

Changes from v1 after the source review (see docs/revisao_fundamentacao.md):
  * Capacity check split in two, as the guidance itself is split:
      R1a continuous connected load (FAA AC 43.13-1B CHG 1, 11-35a/e: "total continuous electrical load",
          short intermittent loads such as gear and flaps excluded; Cessna 1976 ELA "running load");
      R1b average phase load including the time-average of intermittent loads
          (CASA AC 21-38 v2.1 2.1.1 and 4.4.3; CAA NZ AC21-11 App. 1).
  * Base current = typical/average for capacity and battery (CASA 4.3.2: maximum load is generally not used;
    Garmin GTN IM 3.7.2 note [1]); maximum current for breaker loading (R2) and as an upper bound.
  * Emergency currents at battery voltage (CASA 4.4.3.11): manufacturer 24 V column when published,
    constant-power scaling V_bus/V_batt for avionics otherwise; resistive loads unscaled (conservative).
  * Emergency profile per CASA AC 21-38 B.2 and CAA NZ AC21-11 5.3: pre-shed period, shed cruise,
    and a 5-min approach with landing light and flaps; essential loads per Garmin GTN IM 3.7.3 (pitot heat).
"""
from __future__ import annotations

import re
from dataclasses import replace

from .battery import casa_endurance_min, casa_profile_feasible, peukert_sequential_endurance_min
from .ela import configured_loads
from .models import PHASES, Aircraft, Installation, Load

NORMAL = [p for p in PHASES if p not in ("start", "emergency")]
TX_RE = re.compile(r"\bTX\b")


def is_tx(name: str) -> bool:
    return bool(TX_RE.search(name))


def is_landing_light(l: Load) -> bool:
    return "landing" in l.name.lower() and l.cls == "intermittent"


BASE = {
    "use_typical": 1,          # 1 = typical (base), 0 = maximum
    "tx_duty": 0.10,           # 172RMM 24-70-00 note J; CAA NZ AC21-11 6.1.2(b)
    "landing_light_duty": 1.0, # fraction of takeoff and landing phases with the landing light on
    "soh": None, "soc": None, "temp_factor": None, "peukert_n": None,   # None = value from the aircraft file
    "casa_fraction": 0.72,     # CASA AC 21-38 v2.1 4.5.12.6
    "preshed_min": 5.0,        # CASA 4.4.7.1; CAA NZ 5.3
    "approach_min": 5.0,       # CASA B.2.1.2 example; CAA NZ App. 1 (battery approach/landing 5 min)
    "approach_flap_duty": 0.10,
    "cp_scaling": 1,           # emergency currents at battery voltage
    "pitot_em": 1,             # pitot heat on in emergency (Garmin GTN IM 3.7.3 minimum list)
    "bat_capacity_factor": 1.0,
}


def _adjusted_loads(ac: Aircraft, inst: Installation, p: dict) -> list[Load]:
    loads = configured_loads(ac, inst, use_typical=bool(round(p["use_typical"])))
    tx_duty: dict[str, dict[str, float]] = {}
    out = []
    for l in loads:
        duty = dict(l.duty)
        if is_tx(l.name):
            duty = {ph: (p["tx_duty"] if v > 0 else 0.0) for ph, v in duty.items()}
            if l.radio:
                tx_duty[l.radio] = duty
        if is_landing_light(l):
            for ph in ("takeoff_climb", "landing"):
                if duty.get(ph, 0) > 0:
                    duty[ph] = p["landing_light_duty"]
        if "pitot" in l.name.lower():
            duty["emergency"] = float(p["pitot_em"])
        out.append(replace(l, duty=duty))
    # receive and transmit are mutually exclusive states of one radio (manufacturer transmit current is the total)
    for n, l in enumerate(out):
        if l.radio and not is_tx(l.name) and l.radio in tx_duty:
            tx = tx_duty[l.radio]
            out[n] = replace(l, duty={ph: max(0.0, k - tx.get(ph, 0.0)) for ph, k in l.duty.items()})
    return out


def breaker_check(ac: Aircraft, inst: Installation, p: dict) -> dict:
    """R2 over the circuits that carry installed equipment, at maximum current.

    Loads sharing a circuit id are summed. A circuit with continuous load and no breaker rating is
    reported as not evaluated rather than silently skipped. Wire sizing, fault protection and transient
    compatibility are outside this check.
    """
    loads = _adjusted_loads(ac, inst, {**p, "use_typical": 0})
    added = {l.name for l in inst.added}
    circuits: dict[str, list[Load]] = {}
    for l in loads:
        circuits.setdefault(l.circuit or l.name, []).append(l)
    # a radio is powered continuously when its receive and transmit states together cover a whole phase
    radio_duty: dict[str, dict[str, float]] = {}
    for l in loads:
        if l.radio:
            d = radio_duty.setdefault(l.radio, {})
            for ph, k in l.duty.items():
                d[ph] = d.get(ph, 0.0) + k

    def full_duty(l: Load) -> bool:
        if max(l.duty.values(), default=0) >= 1.0:
            return True
        return bool(l.radio) and max(radio_duty[l.radio].values(), default=0) >= 1.0 - 1e-9

    evaluated, missing = [], []
    for cid, ls in circuits.items():
        if not any(l.name in added for l in ls):
            continue
        cont = [l for l in ls if l.cls == "continuous" and full_duty(l)]
        if not cont:
            continue
        ratings = {l.breaker_a for l in ls if l.breaker_a}
        if len(ratings) > 1:
            raise ValueError(f"{ac.model}: circuit '{cid}' has conflicting breaker ratings {sorted(ratings)}")
        if not ratings:
            missing.append(cid)
            continue
        evaluated.append((sum(l.current_a for l in cont) / ratings.pop(), cid))
    worst = max(evaluated, default=(0.0, None))
    return {"frac": worst[0], "circuit": worst[1], "n_evaluated": len(evaluated), "not_evaluated": missing}


def battery_current(l: Load, ac: Aircraft, p: dict, use_typical: bool) -> float:
    """Current drawn by the load when the bus is supplied by the battery."""
    if not p["cp_scaling"]:
        return l.current_a
    if l.current_batt_a is not None and not (use_typical and l.typical_by_v):
        return l.current_batt_a
    if l.constant_power:
        return l.current_a * ac.voltage / ac.battery_v
    return l.current_a


def analyze(ac: Aircraft, inst: Installation, params: dict | None = None) -> dict:
    p = {**BASE, **(params or {})}
    typ = bool(round(p["use_typical"]))
    loads = _adjusted_loads(ac, inst, p)

    avg = {ph: sum(l.k(ph) * l.current_a for l in loads) for ph in PHASES}
    cont = {ph: sum(l.k(ph) * l.current_a for l in loads if l.cls == "continuous") for ph in PHASES}
    ph_avg = max(NORMAL, key=lambda ph: avg[ph])
    ph_cont = max(NORMAL, key=lambda ph: cont[ph])

    bk = breaker_check(ac, inst, p)

    # emergency profile at battery voltage
    i_pre = sum(l.k("cruise") * battery_current(l, ac, p, typ) for l in loads)
    i_shed = sum(l.k("emergency") * battery_current(l, ac, p, typ) for l in loads)
    i_app = i_shed
    for l in loads:
        if is_landing_light(l) and l.k("landing") > 0:
            i_app += battery_current(l, ac, p, typ)
        if "flap motor" in l.name.lower():
            i_app += (p["approach_flap_duty"] - l.k("emergency")) * battery_current(l, ac, p, typ)

    bat = replace(ac.battery,
                  capacity_ah=ac.battery.capacity_ah * (p["bat_capacity_factor"] if ac.battery.capacity_scenarios else 1.0),
                  soh=p["soh"] if p["soh"] is not None else ac.battery.soh,
                  soc=p["soc"] if p["soc"] is not None else ac.battery.soc,
                  temp_factor=p["temp_factor"] if p["temp_factor"] is not None else ac.battery.temp_factor,
                  peukert_n=p["peukert_n"] if p["peukert_n"] is not None else ac.battery.peukert_n)
    t_pre, t_app = p["preshed_min"], p["approach_min"]
    e_casa = casa_endurance_min(bat, i_pre, t_pre, i_shed, i_app, t_app, available_fraction=p["casa_fraction"])
    feasible = casa_profile_feasible(bat, i_pre, t_pre, i_app, t_app, p["casa_fraction"])
    e_pk = peukert_sequential_endurance_min(bat, i_pre, t_pre, i_shed, i_app, t_app)

    return {
        "alt_frac_cont": cont[ph_cont] / ac.alternator_a, "cont_a": cont[ph_cont], "cont_phase": ph_cont,
        "alt_frac_avg": avg[ph_avg] / ac.alternator_a, "avg_a": avg[ph_avg], "avg_phase": ph_avg,
        "avg_by_phase": avg, "cont_by_phase": cont,
        "breaker_frac": bk["frac"], "breaker_circuit": bk["circuit"],
        "breaker_n_evaluated": bk["n_evaluated"], "breaker_not_evaluated": bk["not_evaluated"],
        "casa_profile_feasible": feasible,
        "i_pre": i_pre, "i_shed": i_shed, "i_app": i_app,
        "endurance_casa_min": e_casa, "endurance_peukert_min": e_pk,
        "margin_min": min(e_casa, e_pk) - ac.required_endurance_min,
        "battery_ah_1h": bat.capacity_ah,
    }


def garmin_net_change(ac: Aircraft, inst: Installation) -> dict:
    """Garmin GTN IM 190-01007-A3 3.7.2 / Fig. 3-14: typical currents, COM not transmitting,
    normal bus (28 V values for 28 V aircraft). Removed items use the baseline ELA value."""
    added = [l.at_voltage(ac.voltage, use_typical=True) for l in inst.added if not is_tx(l.name)]
    names = set(inst.removed_for(ac.model))
    removed = [l.at_voltage(ac.voltage) for l in ac.baseline_loads if l.name in names and not is_tx(l.name)]
    a, r = sum(l.current_a for l in added), sum(l.current_a for l in removed)
    return {"added_a": a, "removed_a": r, "net_a": a - r,
            "added": [(l.name, l.current_a) for l in added], "removed": [(l.name, l.current_a) for l in removed]}
