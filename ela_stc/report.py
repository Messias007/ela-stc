"""Multi-model compliance matrix and traceability output."""
from __future__ import annotations

import csv
import io

from .analysis import BASE, _adjusted_loads
from .ela import delta_ela
from .models import Aircraft, Installation
from .montecarlo import simulate_phase
from .rules import Rule, evaluate


def run_aml(aml: list[Aircraft], inst: Installation, rules: list[Rule], params: dict | None = None) -> dict:
    """Every output uses the same analysis options (typical current, duty adjustments, RX/TX exclusivity)."""
    p = {**BASE, **(params or {})}
    results, deltas, mc = [], [], []
    for ac in aml:
        results += evaluate(ac, inst, rules, p)
        deltas.append(delta_ela(ac, inst))
        mc.append({"model": ac.model, **simulate_phase(_adjusted_loads(ac, inst, p), "cruise")})
    return {"installation": inst.name, "results": results, "deltas": deltas, "montecarlo": mc, "params": p}


def matrix_markdown(run: dict) -> str:
    models = list(dict.fromkeys(r["model"] for r in run["results"]))
    rules = list(dict.fromkeys(r["rule"] for r in run["results"]))
    cell = {(r["model"], r["rule"]): r for r in run["results"]}
    lines = [f"# Matriz multimodelo: {run['installation']}", "",
             "PASS = atende ao critério de análise selecionado; não equivale a conformidade com a base de certificação aprovada.",
             f"Opções: corrente {'típica' if run['params']['use_typical'] else 'máxima'}, TX {run['params']['tx_duty']}, corte em {run['params']['preshed_min']} min.", "",
             "| Regra | " + " | ".join(models) + " |",
             "| --- | " + " | ".join("---" for _ in models) + " |"]
    for rule in rules:
        row = [rule]
        for m in models:
            r = cell[(m, rule)]
            row.append(f"{r['status']} ({r['value']} {r['comparison']} {r['limit']})" + (f"; {r['note']}" if r['note'] else ""))
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "## Monte Carlo (cruzeiro, A)", "", "| Modelo | Média | P95 | P99 | Pior caso determinístico |",
              "| --- | --- | --- | --- | --- |"]
    for x in run["montecarlo"]:
        lines.append(f"| {x['model']} | {x['mean']:.1f} | {x['p95']:.1f} | {x['p99']:.1f} | {x['deterministic_worst']:.1f} |")
    return "\n".join(lines) + "\n"


def traceability_csv(run: dict) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["model", "rule", "kind", "source", "value", "comparison", "limit", "status", "pass", "note"])
    w.writeheader()
    w.writerows(run["results"])
    return buf.getvalue()
