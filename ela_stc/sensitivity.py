"""Sensitivity analysis (method v3) on the ELA decision metrics.

Metrics: alt_frac_cont (R1a), alt_frac_avg (R1b) and margin_min (R3), all from ela_stc.analysis.analyze.
1. One-at-a-time (tornado). 2. Global Monte Carlo over physical variability only, reporting the fraction of sampled scenarios beyond each limit.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .analysis import BASE, analyze, garmin_net_change, is_tx  # noqa: F401  (re-exported)
from .models import Aircraft, Installation


@dataclass(frozen=True)
class Param:
    key: str
    label: str
    low: float
    base: float
    high: float
    source: str
    kind: str = "uniform"   # uniform | binary | choice
    group: str = "physical"  # physical (in-service variability) | method (analysis or configuration choice)
    choices: tuple = ()     # values sampled by "choice" (default: low and high)


PARAMS = [
    # method and configuration alternatives: deterministic comparison only, never sampled as frequencies
    Param("use_typical", "Corrente dos equipamentos instalados (1 = típica, 0 = máxima)", 0, 1, 1,
          "Típica: CASA AC 21-38 4.3.2, Garmin GTN IM 3.7.2; máxima: limite superior", "binary", group="method"),
    Param("casa_fraction", "Fração disponível da bateria (CASA)", 0.72, 0.72, 0.75,
          "AC 21-38 v2.1 4.5.12.6 (72 %) vs exemplo B.2.1.2 (75 %)", "choice", group="method"),
    Param("preshed_min", "Tempo até o corte de cargas (min)", 10, 5, 5,
          "AC 21-38 v2.1 4.4.7; CAA NZ 5.3: 5 min, até 10 sem alerta", "choice", group="method"),
    Param("pitot_em", "Aquecimento do pitot ligado na emergência (1 = sim)", 1, 1, 0,
          "Garmin GTN IM 3.7.3 (lista mínima de emergência); só existe no modelo 28 V", "binary", group="method"),
    Param("cp_scaling", "Correntes de emergência na tensão da bateria (1 = sim)", 1, 1, 0,
          "CASA AC 21-38 v2.1 4.4.3.11; coluna 24 V do 172RMM", "binary", group="method"),
    Param("bat_capacity_factor", "Bateria 14 V (1 = RG-25 22 Ah C1; 1,09 = RG-25XC 24 Ah C1; 1,14 = original 25 Ah)", 1.0, 1.0, 25 / 22,
          "Concorde RG-25/RG-25XC (IEC 60952-1, C1); SM 1969-76 16-15: ~25 Ah, base de taxa desconhecida; só 14 V", "choice",
          choices=(1.0, 24 / 22, 25 / 22), group="method"),
    # physical variability of a serviceable aircraft and battery: sampled in the Monte Carlo
    Param("tx_duty", "Ciclo de transmissão COM", 0.05, 0.10, 0.20,
          "172RMM 24-70-00 nota J; CAA NZ AC21-11 6.1.2(b): 10 %"),
    Param("landing_light_duty", "Farol ligado na decolagem e no pouso (fração da fase)", 0.3, 1.0, 1.0,
          "Premissa; base conservadora = fase toda"),
    Param("soh", "Estado de saúde da bateria (SOH)", 0.8, 0.8, 1.0,
          "Concorde CMM 5-0171: retirar abaixo de 80 % (faixa de bateria em serviço)"),
    Param("soc", "Estado de carga na perda do alternador (SOC)", 0.8, 0.9, 1.0,
          "AC 21-38 v2.1 4.5.12.6 assume 90 %"),
    Param("temp_factor", "Fator de temperatura da capacidade", 0.7, 1.0, 1.0,
          "1,0 = temperatura de referência da capacidade; 0,7 = frio (premissa)"),
    Param("peukert_n", "Expoente de Peukert", 1.30, 1.20, 1.10, "Literatura chumbo-ácido 1,1 a 1,3"),
]
DEGRADED = Param("soh", "Bateria degradada (SOH abaixo do critério de retirada)", 0.6, 0.8, 0.8,
                 "Cenário fora de serviço: SOH 0,6 a 0,8", group="degraded")


def _p(prm, v):
    return {prm.key: v}


def evaluate(ac: Aircraft, inst: Installation, params: dict) -> dict:
    return analyze(ac, inst, params)


def tornado(ac: Aircraft, inst: Installation) -> list[dict]:
    base = analyze(ac, inst)
    rows = []
    for prm in PARAMS:
        lo, hi = analyze(ac, inst, _p(prm, prm.low)), analyze(ac, inst, _p(prm, prm.high))
        rows.append({"model": ac.model, "param": prm.label, "low": prm.low, "base": prm.base, "high": prm.high,
                     "cont_low": lo["alt_frac_cont"], "cont_base": base["alt_frac_cont"], "cont_high": hi["alt_frac_cont"],
                     "avg_low": lo["alt_frac_avg"], "avg_base": base["alt_frac_avg"], "avg_high": hi["alt_frac_avg"],
                     "margin_low": lo["margin_min"], "margin_base": base["margin_min"], "margin_high": hi["margin_min"],
                     "source": prm.source})
    return rows


def global_mc(ac: Aircraft, inst: Installation, n: int = 5000, seed: int = 7, degraded: bool = False,
              samples: bool = False) -> dict:
    """Monte Carlo over the physical-variability parameters only (uniform, independent).

    Method and configuration choices stay at the base case; they are compared deterministically by tornado().
    Results are fractions of sampled scenarios under the stated ranges, not operational probabilities.
    degraded=True replaces the serviceable SOH range by 0.6-0.8 (battery below the removal criterion).
    samples=True adds the per-sample arrays (keys "cont", "avg", "margin") to the result.
    """
    rng = np.random.default_rng(seed)
    phys = [p for p in PARAMS if p.group == "physical"]
    smp = {}
    for prm in phys:
        lo, hi = min(prm.low, prm.high), max(prm.low, prm.high)
        if degraded and prm.key == "soh":
            lo, hi = 0.6, 0.8
        smp[prm.key] = rng.uniform(lo, hi, n)
    cont, avg, mar = np.empty(n), np.empty(n), np.empty(n)
    for i in range(n):
        r = analyze(ac, inst, {k: v[i] for k, v in smp.items()})
        cont[i], avg[i], mar[i] = r["alt_frac_cont"], r["alt_frac_avg"], r["margin_min"]

    def rank(y):
        out = []
        for prm in phys:
            x = smp[prm.key]
            c = float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else 0.0
            out.append((prm.label, c))
        return sorted(out, key=lambda t: -abs(t[1]))

    q = lambda a, k: float(np.percentile(a, k))
    return {"model": ac.model, "n": n,
            "cont_p5": q(cont, 5), "cont_p95": q(cont, 95), "p_cont_over_80": float((cont > 0.8).mean()),
            "avg_p5": q(avg, 5), "avg_p95": q(avg, 95), "p_avg_over_80": float((avg > 0.8).mean()),
            "margin_p5": q(mar, 5), "margin_mean": float(mar.mean()), "margin_p95": q(mar, 95),
            "p_margin_negative": float((mar < 0).mean()),
            "se_margin_negative": float(np.sqrt((mar < 0).mean() * (1 - (mar < 0).mean()) / n)),
            "se_avg_over_80": float(np.sqrt((avg > 0.8).mean() * (1 - (avg > 0.8).mean()) / n)),
            "seed": seed, "degraded": degraded,
            "p_cont_over_80_se": float(np.sqrt((cont > 0.8).mean() * (1 - (cont > 0.8).mean()) / n)),
            "rank_avg": rank(avg), "rank_margin": rank(mar),
            **({"cont": cont, "avg": avg, "margin": mar} if samples else {})}
