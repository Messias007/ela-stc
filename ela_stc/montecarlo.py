"""Probabilistic ELA (Monte Carlo).

Continuous loads (duty 1.0) are always on. An intermittent load with duty factor k in a
phase is treated as on with probability k at a random instant; the sampled total current
distribution gives mean, P95 and P99, compared with the deterministic worst case
(all intermittent loads on simultaneously; one state per radio).
"""
from __future__ import annotations

import numpy as np

from .models import Load


def simulate_phase(loads: list[Load], phase: str, n: int = 10_000, seed: int = 42) -> dict:
    """Loads that share a `radio` id are mutually exclusive states (receive, transmit) of one radio:
    they share one random draw and occupy consecutive probability intervals, so they are never on together."""
    rng = np.random.default_rng(seed)
    k = np.array([l.k(phase) for l in loads])
    i = np.array([l.current_a for l in loads])
    u = rng.random((n, len(loads)))
    lower = np.zeros(len(loads))
    groups: dict[str, list[int]] = {}
    for j, l in enumerate(loads):
        if getattr(l, "radio", None):
            groups.setdefault(l.radio, []).append(j)
    for js in groups.values():
        start = 0.0
        for j in js:
            u[:, j] = u[:, js[0]]
            lower[j] = start
            start += k[j]
    on = (u >= lower) & (u < lower + k)
    totals = on.astype(float) @ i
    ind = [j for j in range(len(loads)) if k[j] > 0 and not any(j in js for js in groups.values())]
    worst = float(i[ind].sum()) + sum(max((i[j] for j in js if k[j] > 0), default=0.0) for js in groups.values())
    return {
        "phase": phase,
        "n": n,
        "mean": float(totals.mean()),
        "p95": float(np.percentile(totals, 95)),
        "p99": float(np.percentile(totals, 99)),
        "max_sampled": float(totals.max()),
        "deterministic_worst": worst,
        "expected_value": float((k * i).sum()),
    }
