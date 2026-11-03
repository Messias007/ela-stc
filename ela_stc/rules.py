"""Rule engine: each rule is data (source, paragraph, metric, limit) loaded from YAML."""
from __future__ import annotations

from dataclasses import dataclass

import yaml

from .analysis import analyze
from .models import Aircraft, Installation


@dataclass
class Rule:
    id: str
    source: str
    paragraph: str
    metric: str
    limit: float
    comparison: str = "<="   # "<=" or ">="
    note: str = ""
    kind: str = "criterion"  # "requirement" when it is part of the aircraft's certification basis, else "criterion"

    def __post_init__(self):
        if self.comparison not in ("<=", ">="):
            raise ValueError(f"rule {self.id}: comparison must be '<=' or '>=', got {self.comparison!r}")


def load_rules(path: str) -> list[Rule]:
    with open(path, encoding="utf-8") as f:
        return [Rule(**r) for r in yaml.safe_load(f)["rules"]]


def metrics(ac: Aircraft, inst: Installation, params: dict | None = None) -> dict[str, float]:
    """Decision metrics of the ELA (method v3, ela_stc.analysis)."""
    a = analyze(ac, inst, params)
    return {
        "_breaker_not_evaluated": a["breaker_not_evaluated"],
        "continuous_load_fraction": a["alt_frac_cont"],
        "average_load_fraction": a["alt_frac_avg"],
        "alternator_load_fraction": a["alt_frac_avg"],
        "max_breaker_load_fraction": a["breaker_frac"],
        "endurance_peukert_min": a["endurance_peukert_min"],
        "endurance_casa_min": a["endurance_casa_min"],
        "endurance_margin_min": a["margin_min"],
    }


def evaluate(ac: Aircraft, inst: Installation, rules: list[Rule], params: dict | None = None) -> list[dict]:
    """Status per rule: PASS, FAIL or NOT EVALUATED (insufficient data). PASS means the selected
    analysis criterion is met; it is not a finding of compliance with the aircraft's approved basis."""
    m = metrics(ac, inst, params)
    out = []
    for r in rules:
        v = m[r.metric]
        if r.metric == "max_breaker_load_fraction" and m["_breaker_not_evaluated"]:
            status = "NOT EVALUATED"
            note = "no breaker rating for: " + ", ".join(m["_breaker_not_evaluated"])
        else:
            ok = v <= r.limit if r.comparison == "<=" else v >= r.limit
            status, note = ("PASS" if ok else "FAIL"), ""
        out.append({"model": ac.model, "rule": r.id, "kind": r.kind, "source": f"{r.source} {r.paragraph}",
                    "value": round(v, 3), "limit": r.limit, "comparison": r.comparison,
                    "status": status, "pass": status == "PASS", "note": note})
    return out
