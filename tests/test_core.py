import math
import os

import pytest

from ela_stc.battery import (CASA_EXAMPLE_AVAILABLE, casa_available_amp_min, casa_endurance_min,
                             peukert_endurance_min, peukert_profile_endurance_min)
from ela_stc.ela import delta_ela
from ela_stc.loader import load_case
from ela_stc.models import Battery
from ela_stc.montecarlo import simulate_phase
from ela_stc.report import matrix_markdown, run_aml
from ela_stc.rules import load_rules

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")


# --- Benchmark against CASA AC 21-38 (2017 draft) worked examples -----------------

def test_casa_b2_available_capacity():
    # B.2.1.2: 12 Ah -> 720 A-min; 75 % available -> 540 A-min
    assert casa_available_amp_min(Battery(capacity_ah=12), CASA_EXAMPLE_AVAILABLE) == pytest.approx(540)


def test_casa_v21_default_72_percent():
    # AC 21-38 v2.1 4.5.12.6: 80 % x 90 % = 72 % -> 12 Ah gives 518.4 A-min
    assert casa_available_amp_min(Battery(capacity_ah=12)) == pytest.approx(518.4)


def test_casa_b2_worked_endurance():
    # B.2.1.2 example: 15 A for 5 min pre-shed (75 A-min), 10 A after shed,
    # approach 20 A for 5 min (100 A-min). Remaining 365 A-min / 10 A = 36.5 min.
    t = casa_endurance_min(Battery(capacity_ah=12), 15, 5, 10, 20, 5,
                           available_fraction=CASA_EXAMPLE_AVAILABLE)
    assert t == pytest.approx(5 + 36.5 + 5)


def test_casa_a6_consumption():
    # A.6 table as published: (units simultaneous, A per unit, minutes) -> 857 A-min.
    # Prop feather row is published as 50 A-min (100 A, two 15-s operations = 0.5 min).
    rows = [(1, 120, 0.25), (1, 100, 0.5), (1, 160, 0.5), (3, 4, 1), (2, 10, 3),
            (1, 15, 15), (5, 1, 20), (1, 5, 20), (1, 5, 20), (1, 5, 20)]
    assert sum(u * a * m for u, a, m in rows) == pytest.approx(857)


def test_casa_preshed_penalty():
    # 4.5.8.5: +20 % when average pre-shed current > 2x the 1-hour rating
    b = Battery(capacity_ah=10)   # v2.1 default: 72 % -> 432 A-min available
    assert casa_endurance_min(b, 21, 5, 5) == pytest.approx(5 + (432 - 21 * 5 * 1.2) / 5)
    assert casa_endurance_min(b, 19, 5, 5) == pytest.approx(5 + (432 - 19 * 5) / 5)


# --- Peukert -----------------------------------------------------------------------

def test_peukert_reduces_to_rated_time_at_rated_current():
    b = Battery(capacity_ah=12, peukert_n=1.2)
    assert peukert_endurance_min(b, 12) == pytest.approx(60)


def test_peukert_soh_and_temperature_reduce_endurance():
    new = Battery(capacity_ah=12, peukert_n=1.2)
    aged = Battery(capacity_ah=12, peukert_n=1.2, soh=0.8, temp_factor=0.9)
    assert peukert_endurance_min(aged, 8) < peukert_endurance_min(new, 8)


def test_peukert_profile_equals_constant_when_single_current():
    b = Battery(capacity_ah=12, peukert_n=1.15)
    assert peukert_profile_endurance_min(b, [(6, 10)], 6) == pytest.approx(peukert_endurance_min(b, 6))


# --- Monte Carlo -------------------------------------------------------------------

def test_montecarlo_bounds():
    aml, inst = load_case(os.path.join(DATA, "exemplo_aml.yaml"))
    from ela_stc.ela import configured_loads
    r = simulate_phase(configured_loads(aml[0], inst), "cruise", n=20_000)
    assert r["mean"] == pytest.approx(r["expected_value"], rel=0.02)
    assert r["p99"] <= r["deterministic_worst"] + 1e-9


# --- End to end --------------------------------------------------------------------

def test_delta_and_matrix():
    aml, inst = load_case(os.path.join(DATA, "exemplo_aml.yaml"))
    d = delta_ela(aml[0], inst)
    assert d["delta"]["cruise"] > 0           # glass cockpit adds load in cruise
    run = run_aml(aml, inst, load_rules(os.path.join(DATA, "rules.yaml")))
    assert len(run["results"]) == len(aml) * 4
    md = matrix_markdown(run)
    assert "Modelo A" in md and "R1a-carga-continua-80" in md


def test_removed_unknown_load_raises():
    aml, inst = load_case(os.path.join(DATA, "exemplo_aml.yaml"))
    inst.removed.append("nao existe")
    with pytest.raises(ValueError):
        delta_ela(aml[0], inst)


def test_current_by_voltage_resolves_per_model():
    from ela_stc.models import Load
    l = Load(name="gns", bus="avionics", current_by_v={14: 2.5, 28: 1.2}, duty={"cruise": 1})
    assert l.at_voltage(14).current_a == 2.5 and l.at_voltage(28).current_a == 1.2
    with pytest.raises(ValueError):
        l.at_voltage(12)


def test_case_c172_multimodel_runs():
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    assert {a.voltage for a in aml} == {14, 28}
    run = run_aml(aml, inst, load_rules(os.path.join(DATA, "rules.yaml")))
    assert len(run["results"]) == 4 * len(aml)


def test_breaker_and_typical_by_voltage():
    from ela_stc.models import Load
    l = Load(name="gtn", bus="avionics", current_by_v={14: 3.96, 28: 2.08},
             typical_by_v={14: 2.2, 28: 1.1}, breaker_by_v={14: 7.5, 28: 5})
    assert l.at_voltage(14).breaker_a == 7.5 and l.at_voltage(28).breaker_a == 5
    assert l.at_voltage(28, use_typical=True).current_a == 1.1


def test_tx_filter_does_not_match_gtx():
    from ela_stc.sensitivity import is_tx
    assert is_tx("GTN 650 COM TX") and is_tx("nav/com 1 KX 155A TX")
    assert not is_tx("GTX 345 transponder ADS-B")


def test_sensitivity_base_matches_deterministic_ela():
    from ela_stc.sensitivity import evaluate
    from ela_stc.rules import metrics
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    for ac in aml:
        assert evaluate(ac, inst, {})["alt_frac_avg"] == pytest.approx(metrics(ac, inst)["average_load_fraction"])


def test_continuous_load_excludes_intermittent():
    from ela_stc.analysis import analyze
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    for ac in aml:
        r = analyze(ac, inst)
        assert r["alt_frac_cont"] < r["alt_frac_avg"]       # landing light, flaps and TX are excluded
        assert r["cont_phase"] in ("taxi", "takeoff_climb", "cruise", "landing", "ground")


def test_battery_voltage_raises_avionics_current():
    from ela_stc.analysis import analyze
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    for ac in aml:
        on, off = analyze(ac, inst, {"cp_scaling": 1}), analyze(ac, inst, {"cp_scaling": 0, "pitot_em": 1})
        assert on["endurance_casa_min"] != off["endurance_casa_min"]


def test_casa_profile_with_approach_matches_b2_structure():
    # B.2.1.2 structure: pre-shed, shed cruise, 5-min approach reserve
    b = Battery(capacity_ah=12)
    t = casa_endurance_min(b, 15, 5, 10, 20, 5, available_fraction=CASA_EXAMPLE_AVAILABLE)
    assert t == pytest.approx(46.5)
