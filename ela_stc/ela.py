"""Deterministic delta ELA per bus and flight phase.

I_{b,f} = sum_i k_{i,f} * I_i ;  Delta = after - before
"""
from __future__ import annotations

from .models import PHASES, Aircraft, Installation, Load


def configured_loads(ac: Aircraft, inst: Installation | None, use_typical: bool = False) -> list[Load]:
    loads = [l.at_voltage(ac.voltage, use_typical) for l in ac.baseline_loads]
    if inst is None:
        return loads
    removed = inst.removed_for(ac.model)
    unknown = set(removed) - {l.name for l in loads}
    if unknown:
        raise ValueError(f"{ac.model}: removed loads not in baseline: {sorted(unknown)}")
    loads = [l for l in loads if l.name not in removed]
    return loads + [l.at_voltage(ac.voltage, use_typical) for l in inst.added]


def bus_phase_table(loads: list[Load]) -> dict[str, dict[str, float]]:
    table: dict[str, dict[str, float]] = {}
    for l in loads:
        row = table.setdefault(l.bus, {p: 0.0 for p in PHASES})
        for p in PHASES:
            row[p] += l.k(p) * l.current_a
    return table


def total_by_phase(loads: list[Load]) -> dict[str, float]:
    return {p: sum(l.k(p) * l.current_a for l in loads) for p in PHASES}


def delta_ela(ac: Aircraft, inst: Installation) -> dict:
    before = configured_loads(ac, None)
    after = configured_loads(ac, inst)
    tb, ta = total_by_phase(before), total_by_phase(after)
    return {
        "model": ac.model,
        "before": tb,
        "after": ta,
        "delta": {p: ta[p] - tb[p] for p in PHASES},
        "by_bus_after": bus_phase_table(after),
        "worst_normal_phase": max((p for p in PHASES if p != "emergency"), key=lambda p: ta[p]),
    }
