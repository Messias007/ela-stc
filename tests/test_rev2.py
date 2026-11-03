"""Regression tests for the issues raised in the external review (1 Nov 2026)."""
import os

import pytest

from ela_stc.analysis import BASE, _adjusted_loads, analyze
from ela_stc.battery import (casa_endurance_min, casa_profile_feasible, peukert_endurance_min,
                             peukert_sequential_endurance_min)
from ela_stc.loader import load_case
from ela_stc.models import Aircraft, Battery, Bus, Installation, Load
from ela_stc.report import run_aml
from ela_stc.rules import Rule, evaluate, load_rules

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
ALL = {"taxi": 1, "takeoff_climb": 1, "cruise": 1, "landing": 1, "emergency": 1}


def _ac(loads, cap=10.0):
    return Aircraft(model="T", tcds="-", cert_basis="-", voltage=28, battery_v=24, alternator_a=60,
                    battery=Battery(capacity_ah=cap, soh=0.8, soc=0.9), buses=[Bus("main"), Bus("avionics")],
                    baseline_loads=loads)


# D. sequential depletion when the profile is infeasible
def test_casa_infeasible_approach_is_sequential():
    b = Battery(capacity_ah=1.0)                       # 43.2 A-min at 72 %
    t = casa_endurance_min(b, 1.0, 5, 1.0, 10.0, 5)   # 5 A-min pre-shed, 38.2 left, approach at 10 A
    assert t == pytest.approx(5 + 3.82)
    assert not casa_profile_feasible(b, 1.0, 5, 10.0, 5)


def test_casa_exhaustion_during_preshed():
    b = Battery(capacity_ah=1.0)
    assert casa_endurance_min(b, 20.0, 5, 1.0, 1.0, 5) == pytest.approx(43.2 / (20 * 1.2))


def test_casa_exact_exhaustion_at_end_of_profile():
    b = Battery(capacity_ah=10.0)                      # 432 A-min; no penalty at 10 A (< 2 C1)
    assert casa_endurance_min(b, 10.0, 5, 1.0, 76.4, 5) == pytest.approx(10.0)
    assert casa_profile_feasible(b, 10.0, 5, 76.4, 5)


def test_casa_zero_shed_current_is_unbounded():
    assert casa_endurance_min(Battery(capacity_ah=10.0), 5, 5, 0.0, 5, 5) == float("inf")


def test_peukert_sequential_branches():
    b = Battery(capacity_ah=1.0)
    tp = peukert_endurance_min(b, 30.0)
    assert peukert_sequential_endurance_min(b, 30.0, 5, 1, 1, 5) == pytest.approx(tp)
    ta = peukert_endurance_min(b, 20.0)
    f_pre = 5 / peukert_endurance_min(b, 2.0)
    assert peukert_sequential_endurance_min(b, 2.0, 5, 1, 20.0, 5) == pytest.approx(5 + (1 - f_pre) * ta)


# A. state of health, state of charge and temperature are separate inputs
def test_soc_enters_peukert_separately():
    b1 = Battery(capacity_ah=10, soh=0.8, soc=0.9, temp_factor=1.0)
    b2 = Battery(capacity_ah=10, soh=0.8, soc=1.0, temp_factor=0.9)
    assert peukert_endurance_min(b1, 5) == pytest.approx(peukert_endurance_min(b2, 5))
    b3 = Battery(capacity_ah=10, soh=0.8, soc=0.9, temp_factor=0.9)
    assert peukert_endurance_min(b3, 5) < peukert_endurance_min(b1, 5)


# E. receive and transmit of one radio are mutually exclusive
def test_rx_tx_mutually_exclusive():
    rx = Load("COM RX", "avionics", 0.45, duty=dict(ALL), radio="c1")
    tx = Load("COM TX", "avionics", 4.02, duty={k: 0.1 for k in ALL}, radio="c1", cls="intermittent")
    ac = _ac([rx, tx])
    ls = _adjusted_loads(ac, Installation("n"), BASE)
    mean = sum(l.k("cruise") * l.current_a for l in ls)
    assert mean == pytest.approx(0.9 * 0.45 + 0.1 * 4.02)


def test_case_gtn_com_contribution():
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    ls = _adjusted_loads(aml[0], inst, BASE)
    com = sum(l.k("cruise") * l.current_a for l in ls if l.radio == "gtn_com")
    assert com == pytest.approx(0.807)


# C. breaker check: shared circuits are summed; missing ratings are not evaluated
def test_shared_circuit_is_aggregated():
    a = Load("A", "avionics", 3.0, breaker_a=5, duty=dict(ALL), circuit="CB1")
    b = Load("B", "avionics", 3.0, breaker_a=5, duty=dict(ALL), circuit="CB1")
    r = analyze(_ac([]), Installation("i", added=[a, b]))
    assert r["breaker_frac"] == pytest.approx(1.2)
    assert r["breaker_n_evaluated"] == 1


def test_missing_breaker_is_not_evaluated():
    a = Load("A", "avionics", 1.0, duty=dict(ALL))
    rule = Rule("R2", "s", "p", "max_breaker_load_fraction", 0.85)
    out = evaluate(_ac([]), Installation("i", added=[a]), [rule])
    assert out[0]["status"] == "NOT EVALUATED"


def test_case_breakers_all_evaluated():
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    for ac in aml:
        r = analyze(ac, inst)
        assert r["breaker_not_evaluated"] == [] and r["breaker_n_evaluated"] == 5   # GTN main+NAV, GTN COM, GMA, GTX, G5


# input validation
@pytest.mark.parametrize("kw", [{"current_a": -1}, {"duty": {"cruise": 1.5}}, {"duty": {"cruse": 1}}])
def test_invalid_load_rejected(kw):
    with pytest.raises(ValueError):
        Load("x", "main", **{"current_a": 1, **kw})


def test_invalid_aircraft_and_rule_rejected():
    with pytest.raises(ValueError):
        _ac([Load("x", "nobus", 1.0)])
    with pytest.raises(ValueError):
        Battery(capacity_ah=10, soh=1.2)
    with pytest.raises(ValueError):
        Rule("r", "s", "p", "m", 1.0, comparison="=>")


# report consistency: every output uses the same analysis options
def test_report_uses_typical_current():
    aml, inst = load_case(os.path.join(DATA, "caso_c172.yaml"))
    run = run_aml(aml, inst, load_rules(os.path.join(DATA, "rules.yaml")))
    for ac, mc in zip(aml, run["montecarlo"]):
        assert mc["expected_value"] == pytest.approx(analyze(ac, inst)["avg_by_phase"]["cruise"])


def test_mc_radio_states_exclusive():
    from ela_stc.models import Load
    from ela_stc.montecarlo import simulate_phase
    rx = Load(name="com rx", bus="main", current_a=1.0, cls="continuous", duty={"cruise": 0.9}, radio="c1")
    tx = Load(name="com tx", bus="main", current_a=5.0, cls="intermittent", duty={"cruise": 0.1}, radio="c1")
    r = simulate_phase([rx, tx], "cruise", n=20000)
    assert r["max_sampled"] <= 5.0 + 1e-9          # never both on
    assert abs(r["mean"] - 1.4) < 0.05
    assert r["deterministic_worst"] == 5.0
