"""Recalculation harness: the spreadsheet formulas must reproduce ela_stc.analysis for the base case and for
changed inputs. Each case edits the input cells of the Premissas sheet, recalculates with LibreOffice and compares
every Resumo quantity with Python. Exit code 1 on any difference above the tolerance.

Usage: python scripts/verificar_planilha.py [recalc.py path]
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from openpyxl import load_workbook  # noqa: E402

from ela_stc.analysis import analyze, garmin_net_change  # noqa: E402
from ela_stc.loader import load_case  # noqa: E402
from ela_stc.models import Installation  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
RECALC = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("XLSX_RECALC", "recalc.py")
TOL = 1e-6   # relative, on every compared quantity

LABEL = {"use_typical": "Corrente da instalação: 1 = típica, 0 = máxima", "tx_duty": "Ciclo de transmissão COM",
         "landing_light_duty": "Farol ligado na decolagem e no pouso", "soh": "Estado de saúde da bateria (SOH)",
         "soc": "Estado de carga na perda do alternador (SOC)", "temp_factor": "Fator de temperatura da capacidade",
         "peukert_n": "Expoente de Peukert", "casa_fraction": "Fração disponível (método CASA)",
         "preshed_min": "Tempo até o corte de cargas", "approach_min": "Aproximação e pouso na bateria",
         "cp_scaling": "Emergência na tensão da bateria (1 = sim)", "pitot_em": "Pitot aquecido na emergência (1 = sim)"}
CASES = [{}, {"use_typical": 0}, {"tx_duty": 0.2, "landing_light_duty": 0.4}, {"soh": 0.65, "soc": 0.8, "temp_factor": 0.7},
         {"peukert_n": 1.3, "preshed_min": 10}, {"casa_fraction": 0.75, "approach_min": 0}, {"cp_scaling": 0, "pitot_em": 0},
         {"soh": 0.2, "soc": 0.6, "temp_factor": 0.6}]   # last case: infeasible emergency profile (sequential depletion)
ROWS = [("Carga contínua / alternador, antes", 0, "alt_frac_cont", 0), ("Carga contínua / alternador, depois", 0, "alt_frac_cont", 1),
        ("Carga média / alternador, antes", 0, "alt_frac_avg", 0), ("Carga média / alternador, depois", 0, "alt_frac_avg", 1),
        ("Maior carga contínua / disjuntor", 0, "breaker_frac", 1)]
for n, inst in ((0, 0), (1, 1)):
    ROWS += [("I antes do corte (cargas de cruzeiro na bateria)", n, "i_pre", inst), ("I após o corte (cargas essenciais)", n, "i_shed", inst),
             ("I na aproximação (essenciais + farol + flap)", n, "i_app", inst), ("Autonomia, método CASA", n, "endurance_casa_min", inst),
             ("Autonomia, Peukert", n, "endurance_peukert_min", inst)]
ROWS += [("Margem sobre 30 min, antes", 0, "margin_min", 0), ("Margem sobre 30 min, depois", 0, "margin_min", 1)]


def main() -> int:
    aml, inst = load_case(os.path.join(ROOT, "data", "caso_c172.yaml"))
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "base.xlsx")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gerar_planilha.py"), base], check=True, capture_output=True)
    worst, n, bad = 0.0, 0, 0
    for ci, case in enumerate(CASES):
        path = os.path.join(tmp, f"case{ci}.xlsx")
        shutil.copy(base, path)
        wb = load_workbook(path)
        ps = wb["Premissas"]
        rows = {ps.cell(r, 1).value: r for r in range(5, ps.max_row + 1)}
        for k, v in case.items():
            for col in (2, 3):
                ps.cell(rows[LABEL[k]], col).value = v
        wb.save(path)
        out = subprocess.run([sys.executable, RECALC, path, "120"], capture_output=True, text=True)
        if '"total_errors": 0' not in out.stdout:
            print("recalc errors", case, out.stdout[-400:])
            return 1
        rs = load_workbook(path, data_only=True)["Resumo"]
        lab = {}
        for r in range(5, rs.max_row + 1):
            lab.setdefault(rs.cell(r, 1).value, []).append(r)
        for mi, ac in enumerate(aml):
            res = {0: analyze(ac, Installation(name="n"), case), 1: analyze(ac, inst, case)}
            for label, nth, key, which in ROWS:
                x = rs.cell(lab[label][nth], 2 + mi).value
                y = res[which][key]
                n += 1
                err = abs(x - y) / max(1.0, abs(y))
                worst = max(worst, err)
                if err > TOL:
                    bad += 1
                    print(f"DIFF case {case} {ac.model} {label}: sheet {x} python {y}")
            g = rs.cell(lab["Variação líquida"][0], 2 + mi).value
            n += 1
            if abs(g - garmin_net_change(ac, inst)["net_a"]) > TOL:
                bad += 1
                print("DIFF garmin", ac.model, g)
    print(f"{len(CASES)} input cases, {n} compared quantities, max relative error {worst:.2e}, mismatches {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
