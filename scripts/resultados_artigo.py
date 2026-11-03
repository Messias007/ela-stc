"""Gera todos os números citados no manuscrito a partir do caso C172 (método v3).

Uso: python scripts/resultados_artigo.py [data/caso_c172.yaml] [saida/resultados_artigo.md]
Cada valor do artigo deve ser rastreável a uma linha deste relatório.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ela_stc.analysis import BASE, _adjusted_loads, analyze, garmin_net_change  # noqa: E402
from ela_stc.loader import load_case  # noqa: E402
from ela_stc.models import Installation  # noqa: E402
from ela_stc.montecarlo import simulate_phase  # noqa: E402
from ela_stc.sensitivity import PARAMS, global_mc, tornado  # noqa: E402

case = sys.argv[1] if len(sys.argv) > 1 else "data/caso_c172.yaml"
out_path = sys.argv[2] if len(sys.argv) > 2 else "saida/resultados_artigo.md"
aml, inst = load_case(case)
NONE = Installation(name="none")
L = []
w = L.append
pc = lambda x: f"{100 * x:.1f}%"


def bisect(f, lo, hi, it=60):
    """Root of f on [lo, hi] (f changes sign), or None."""
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(it):
        mid = (lo + hi) / 2
        if f(mid) * flo > 0:
            lo, flo = mid, f(mid)
        else:
            hi = mid
    return (lo + hi) / 2


w(f"# Resultados do artigo (gerado por scripts/resultados_artigo.py a partir de {case})\n")
w("Parâmetros base: " + ", ".join(f"{k}={v}" for k, v in BASE.items()) + "\n")

for ac in aml:
    b, a = analyze(ac, NONE), analyze(ac, inst)
    bm, am = analyze(ac, NONE, {"use_typical": 0}), analyze(ac, inst, {"use_typical": 0})
    net = garmin_net_change(ac, inst)
    w(f"## {ac.model}\n")
    w(f"- Bateria: C1={ac.battery.capacity_ah} Ah, SOH={ac.battery.soh}, SOC={ac.battery.soc}, kT={ac.battery.temp_factor}, n={ac.battery.peukert_n}")
    w(f"- R1a contínua antes→depois (típica): {pc(b['alt_frac_cont'])} → {pc(a['alt_frac_cont'])}; máxima depois {pc(am['alt_frac_cont'])}; fase {a['cont_phase']}")
    w(f"- R1b média antes→depois (típica): {pc(b['alt_frac_avg'])} → {pc(a['alt_frac_avg'])}; máxima antes/depois {pc(bm['alt_frac_avg'])}/{pc(am['alt_frac_avg'])}; fase {a['avg_phase']}")
    w(f"- R2 disjuntor: {pc(a['breaker_frac'])} no circuito '{a['breaker_circuit']}', {a['breaker_n_evaluated']} circuitos avaliados, não avaliados: {a['breaker_not_evaluated'] or 'nenhum'}")
    for tag, r in (("antes", b), ("depois", a), ("depois, máxima", am), ("antes, máxima", bm)):
        w(f"- Emergência {tag}: I_pre={r['i_pre']:.3f} I_shed={r['i_shed']:.3f} I_app={r['i_app']:.3f} A; "
          f"E_CASA={r['endurance_casa_min']:.2f} E_P={r['endurance_peukert_min']:.2f} min; M={r['margin_min']:+.2f} min; perfil CASA viável={r['casa_profile_feasible']}")
    w(f"- Variação líquida Garmin: +{net['added_a']:.3f} − {net['removed_a']:.3f} = {net['net_a']:+.3f} A")
    # CASA worked example
    C1 = a["battery_ah_1h"]; Q = 60 * C1 * BASE["casa_fraction"]
    pre = a["i_pre"] * BASE["preshed_min"]; res = a["i_app"] * BASE["approach_min"]
    w(f"- Exemplo CASA depois: Q=60×{C1:.4f}×0.72={Q:.2f} A·min; pré={pre:.2f} (2C1={2 * C1:.2f} A); reserva={res:.2f}; "
      f"cruzeiro em corte=({Q:.2f}−{pre:.2f}−{res:.2f})/{a['i_shed']:.3f}={(Q - pre - res) / a['i_shed']:.2f} min")
    # thresholds
    ll = bisect(lambda x: analyze(ac, inst, {"landing_light_duty": x})["alt_frac_avg"] - 0.8, 0.0, 1.0)
    llm = bisect(lambda x: analyze(ac, inst, {"landing_light_duty": x, "use_typical": 0})["alt_frac_avg"] - 0.8, 0.0, 1.0)
    w(f"- Limiar do farol para R1b > 80%: típica {ll if ll is None else round(ll, 3)}, máxima {llm if llm is None else round(llm, 3)}")
    for kt in (1.0, 0.7):
        for soc in (0.9, 1.0):
            s = bisect(lambda x: analyze(ac, inst, {"soh": x, "temp_factor": kt, "soc": soc})["margin_min"], 0.3, 1.0)
            w(f"- SOH com M=0 (kT={kt}, SOC={soc}): {s if s is None else round(s, 3)}")
    w("")
    # tornado
    w("| Parâmetro (grupo) | baixo | base | alto | M baixo | M base | M alto | R1b baixo | R1b alto |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for prm, t in zip(PARAMS, tornado(ac, inst)):
        w(f"| {prm.key} ({prm.group}) | {prm.low:.3g} | {prm.base:.3g} | {prm.high:.3g} | {t['margin_low']:+.2f} | {t['margin_base']:+.2f} | "
          f"{t['margin_high']:+.2f} | {pc(t['avg_low'])} | {pc(t['avg_high'])} |")
    w("")
    # Monte Carlo
    for deg in (False, True):
        r = global_mc(ac, inst, degraded=deg)
        w(f"- MC físico {'degradado (SOH 0,6-0,8)' if deg else 'em serviço (SOH 0,8-1,0)'} N={r['n']} seed={r['seed']}: "
          f"R1a p5-p95 {pc(r['cont_p5'])}-{pc(r['cont_p95'])}; R1b p5-p95 {pc(r['avg_p5'])}-{pc(r['avg_p95'])}; "
          f"fração R1b>80% {pc(r['p_avg_over_80'])} (EP {pc(r['se_avg_over_80'])}); M p5/média/p95 {r['margin_p5']:+.1f}/{r['margin_mean']:+.1f}/{r['margin_p95']:+.1f}; "
          f"fração M<0 {pc(r['p_margin_negative'])} (EP {pc(r['se_margin_negative'])})")
        w("  - correlações M: " + "; ".join(f"{k} {c:+.2f}" for k, c in r["rank_margin"]))
        w("  - correlações R1b: " + "; ".join(f"{k} {c:+.2f}" for k, c in r["rank_avg"]))
    # simplified practices
    crude_b = simulate_phase(_adjusted_loads(ac, NONE, {**BASE, "use_typical": 0}), "landing", n=10)["deterministic_worst"]
    crude_a = simulate_phase(_adjusted_loads(ac, inst, {**BASE, "use_typical": 0}), "landing", n=10)["deterministic_worst"]
    w(f"- Todas as cargas ligadas na corrente máxima, pouso: antes {pc(crude_b / ac.alternator_a)}, depois {pc(crude_a / ac.alternator_a)}")
    simp = {"cp_scaling": 0, "approach_min": 0.0, "pitot_em": 0, "casa_fraction": 0.75}
    s = analyze(ac, inst, simp)
    w(f"- Emergência simplificada (correntes no barramento, sem aproximação, sem pitot, só CASA 75%): E={s['endurance_casa_min']:.2f}, "
      f"M={s['endurance_casa_min'] - ac.required_endurance_min:+.2f} min; superestima M em {s['endurance_casa_min'] - ac.required_endurance_min - a['margin_min']:.2f} min")
    for k, v in (("pitot_em", 0), ("approach_min", 0.0), ("cp_scaling", 0), ("casa_fraction", 0.75)):
        w(f"  - efeito isolado {k}={v}: ΔM={analyze(ac, inst, {k: v})['margin_min'] - a['margin_min']:+.2f} min")
    # phase Monte Carlo
    loads = _adjusted_loads(ac, inst, BASE)
    for ph in ("cruise", "landing"):
        r = simulate_phase(loads, ph)
        w(f"- MC de fase {ph} (N={r['n']}, típica, depois): média {r['mean']:.2f} (esperado {r['expected_value']:.2f}); p95 {r['p95']:.2f}; "
          f"p99 {r['p99']:.2f} ({pc(r['p99'] / ac.alternator_a)}); pior caso {r['deterministic_worst']:.2f} ({pc(r['deterministic_worst'] / ac.alternator_a)}); "
          f"média {pc(r['mean'] / ac.alternator_a)}")
    w("")

open(out_path, "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
