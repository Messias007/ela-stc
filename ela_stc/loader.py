"""Load aircraft (AML) and installation definitions from YAML."""
from __future__ import annotations

import yaml

from .models import Aircraft, Battery, Bus, Installation, Load


def _load(d: dict) -> Load:
    return Load(**d)


def load_params(path: str) -> dict:
    """Optional top-level 'analysis_params' (e.g. written by the browser version)."""
    with open(path, encoding="utf-8") as f:
        return dict(yaml.safe_load(f).get("analysis_params") or {})


def load_case(path: str) -> tuple[list[Aircraft], Installation]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    aml = []
    for a in data["aml"]:  # extra top-level keys (e.g. YAML anchors) are ignored
        aml.append(Aircraft(
            model=a["model"], tcds=a["tcds"], cert_basis=a["cert_basis"], voltage=a["voltage"],
            alternator_a=a["alternator_a"], battery=Battery(**a["battery"]),
            buses=[Bus(**b) for b in a["buses"]],
            required_endurance_min=a.get("required_endurance_min", 30.0),
            battery_v=a.get("battery_v", a["voltage"]),
            baseline_loads=[_load(l) for l in a["baseline_loads"]],
            source=a.get("source", "PLACEHOLDER"),
        ))
    i = data["installation"]
    inst = Installation(name=i["name"], added=[_load(l) for l in i["added"]], removed=i.get("removed", []),
                        removed_by_model=i.get("removed_by_model", {}))
    return aml, inst
