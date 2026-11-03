"""Gera a planilha ELA_C172_calculos.xlsx (método v2) a partir de data/caso_c172.yaml.

Abas com FÓRMULAS (recalculam ao mudar Premissas): Premissas, Cargas_14V, Cargas_28V, Resumo.
Abas com RESULTADOS do script (Monte Carlo não cabe em fórmula): Sensibilidade_Tornado, Sensibilidade_MC.
Uso: python scripts/gerar_planilha.py saida/ELA_C172_calculos.xlsx
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL

from ela_stc.analysis import analyze, garmin_net_change, is_landing_light, is_tx
from ela_stc.loader import load_case
from ela_stc.sensitivity import PARAMS, global_mc, tornado

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "saida", "ELA_C172_calculos.xlsx")
F = "Arial"
BLUE, BLACK, GREEN, BOLD = Font(name=F, color="0000FF"), Font(name=F), Font(name=F, color="008000"), Font(name=F, bold=True)
HEAD, HEADFILL = Font(name=F, bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F3864")
KEYFILL, SUBFILL = PatternFill("solid", fgColor="FFFF00"), PatternFill("solid", fgColor="D9E1F2")
THIN = Side(style="thin", color="BFBFBF")
BOX, WRAP = Border(top=THIN, bottom=THIN, left=THIN, right=THIN), Alignment(wrap_text=True, vertical="top")
PHASES = ["ground", "taxi", "takeoff_climb", "cruise", "landing", "emergency"]
PH_PT = ["Solo", "Táxi", "Decolagem/subida", "Cruzeiro", "Pouso", "Emergência"]

aml, inst = load_case(os.path.join(ROOT, "data", "caso_c172.yaml"))
ac14, ac28 = aml
wb = Workbook()


def header(ws, row, labels, widths=None):
    for c, lab in enumerate(labels, 1):
        cell = ws.cell(row=row, column=c, value=lab)
        cell.font, cell.fill, cell.alignment, cell.border = HEAD, HEADFILL, WRAP, BOX
    for c, w in enumerate(widths or [], 1):
        ws.column_dimensions[CL(c)].width = w


def title(ws, text, sub=None):
    ws["A1"], ws["A1"].font = text, Font(name=F, bold=True, size=14)
    if sub:
        ws["A2"], ws["A2"].font = sub, Font(name=F, italic=True, color="595959")


def put(ws, r, c, v, font=BLACK, nf=None, fill=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font
    if nf:
        cell.number_format = nf
    if fill:
        cell.fill = fill
    return cell


# ------------------------------------------------------------------ LEIA-ME
ws = wb.active
ws.title = "LEIA-ME"
title(ws, "ELA multimodelo (método v2): Cessna 172 + GTN 650, GMA 345, GTX 345 e G5",
      "Gerada por scripts/gerar_planilha.py a partir de data/caso_c172.yaml. Fórmulas conferidas contra ela_stc/analysis.py.")
rows = [
    ("Objetivo", "Todos os valores, fontes e cálculos do estudo de caso, com fórmulas que podem ser conferidas e alteradas."),
    ("Como usar", "Altere as células azuis da aba Premissas (amarelo = premissa-chave). Cargas_14V, Cargas_28V e Resumo recalculam."),
    ("Cores", "Azul = valor digitado (fonte na coluna Fonte); preto = fórmula; verde = vínculo com Premissas; amarelo = premissa-chave."),
    ("Ciclo de trabalho k", "Fração do tempo da fase em que a carga está ligada. Corrente média da fase = Σ k·I."),
    ("Classe", "contínua ou intermitente (AC 43.13-1B CHG 1 11-35; ELA Cessna 1976: itens 'não considerados como running load')."),
    ("R1a", "Carga contínua ≤ 80 % do alternador (AC 43.13-1B CHG 1, cap. 11, 11-35a/e; intermitentes curtas excluídas por 11-35c/d)."),
    ("R1b", "Carga média da fase, incluindo a média das intermitentes, ≤ 80 % (CASA AC 21-38 v2.1 2.1.1/4.4.3; CAA NZ AC21-11 usa 85 %)."),
    ("R2", "Carga contínua ≤ 85 % do disjuntor, com corrente MÁXIMA (CASA AWB 24-007; AC 21-38 4.3.3 e 4.6.4)."),
    ("R3", "Autonomia ≥ 30 min com perfil CASA B.2: corte de cargas, cruzeiro em emergência e aproximação de 5 min (14 CFR 23.1353(h) emenda 62)."),
    ("Emergência", "Correntes na tensão da bateria (AC 21-38 4.4.3.11): coluna 24 V do 172RMM quando publicada; aviônicos em potência constante (I·Vbarra/Vbateria); cargas resistivas sem ajuste."),
    ("Atenção", "Ferramenta de pesquisa. Não substitui a análise aprovada por DER ou autoridade."),
]
for r, (k, v) in enumerate(rows, 4):
    put(ws, r, 1, k, BOLD)
    put(ws, r, 2, v).alignment = WRAP
ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 22, 120

# ------------------------------------------------------------------ Premissas
ps = wb.create_sheet("Premissas")
title(ps, "Premissas e parâmetros", "Coluna B = 172M 1976 (14 V); coluna C = 172R/S convencional (28 V).")
header(ps, 4, ["Parâmetro", "172M 1976 (14 V)", "172R/S (28 V)", "Unidade", "Fonte / observação"], [52, 16, 16, 9, 95])
P = {}
prem = [
    ("volt", "Tensão do barramento", 14, 28, "V", "SM 1969-76 16-38; 172RMM 24-70-00", False, "0"),
    ("vbat", "Tensão nominal da bateria (emergência)", 12, 24, "V", "SM 1969-76 16-15; 172RMM 24-30", False, "0"),
    ("alt", "Alternador, valor de placa", 60, 60, "A", "SM 1969-76 16-38 (PDF 253); 172RMM 24-70-00 nota I (PDF 397)", False, "0"),
    ("alt_lim", "Limite de carga do alternador (R1a, R1b)", 0.80, 0.80, "fração", "AC 43.13-1B CHG 1, 11-35a/e; GTN IM 190-01007-A3 3.7. CAA NZ AC21-11 6.1.5.1(a) usa 85 %", False, "0%"),
    ("bk_lim", "Limite de carga contínua do disjuntor (R2)", 0.85, 0.85, "fração", "CASA AWB 24-007; AC 21-38 v2.1 4.3.3 e 4.6.4", False, "0%"),
    ("bat_nom", "Bateria, capacidade nominal", 22, 12.75, "Ah", "14 V: Concorde RG-25, 22 Ah C1 (IEC 60952-1), reposição listada para 172 A-M/N (original Cessna ~25 Ah sem taxa, SM 16-15); 28 V: 172RMM 24-30 (PDF 352), 12,75 Ah na taxa de 5 h", False, "0.00"),
    ("bat_rate", "Fator para taxa de 1 h", 1.0, 0.85, "fração", "AC 21-38 v2.1 4.5.12.2: 1 h ≈ 85 % da taxa de 5 h. 14 V: C1 já é a taxa de 1 h", False, "0.00"),
    ("rate_unc", "Cenário de capacidade (só 14 V)", 1.0, 1.0, "fração", "1 = RG-25 (22 Ah); 24/22 = RG-25XC (24 Ah C1); 25/22 = Cessna original (25 Ah). 28 V: manter 1", True, "0.000"),
    ("soh", "Estado de saúde da bateria (SOH)", ac14.battery.soh, ac28.battery.soh, "fração", "Concorde CMM 5-0171: retirar abaixo de 80 % (CASA 4.5.12.6: 80 % da capacidade)", True, "0%"),
    ("soc", "Estado de carga na perda do alternador (SOC)", ac14.battery.soc, ac28.battery.soc, "fração", "CASA AC 21-38 4.5.12.6: 90 %", True, "0%"),
    ("kt", "Fator de temperatura da capacidade", ac14.battery.temp_factor, ac28.battery.temp_factor, "fração", "1,0 = temperatura de referência da capacidade (+20 °C); 0,7 = frio", True, "0%"),
    ("n", "Expoente de Peukert", ac14.battery.peukert_n, ac28.battery.peukert_n, "-", "Chumbo-ácido 1,1 a 1,25 (literatura)", True, "0.00"),
    ("casa_f", "Fração disponível (método CASA)", 0.72, 0.72, "fração", "AC 21-38 v2.1 4.5.12.6: 80 % × 90 % (o exemplo B.2.1.2 usa 75 %)", True, "0%"),
    ("tpre", "Tempo até o corte de cargas", 5, 5, "min", "AC 21-38 v2.1 4.4.7; CAA NZ AC21-11 5.3: 5 min (10 min sem alerta claro)", True, "0"),
    ("tapp", "Aproximação e pouso na bateria", 5, 5, "min", "AC 21-38 B.2.1.2 (exemplo); CAA NZ AC21-11 App. 1", True, "0"),
    ("flap_app", "Ciclo do flap na aproximação", 0.10, 0.10, "fração", "Premissa", False, "0%"),
    ("req", "Autonomia exigida", 30, 30, "min", "14 CFR 23.1353(h) emenda 62 (≤ 25.000 ft); AC 21-38 v2.1 4.5.8", False, "0"),
    ("tx", "Ciclo de transmissão COM", 0.10, 0.10, "fração", "172RMM 24-70-00 nota J; CAA NZ AC21-11 6.1.2(b)", True, "0%"),
    ("ll", "Farol ligado na decolagem e no pouso", 1.0, 1.0, "fração", "Premissa conservadora; R1b passa de 80 % no 14 V só acima de 92 %", True, "0%"),
    ("typ", "Corrente da instalação: 1 = típica, 0 = máxima", 1, 1, "0/1", "Típica: AC 21-38 4.3.2, GTN IM 3.7.2 nota [1]. R2 usa sempre a máxima", True, "0"),
    ("cp", "Emergência na tensão da bateria (1 = sim)", 1, 1, "0/1", "AC 21-38 v2.1 4.4.3.11", True, "0"),
    ("pitot", "Pitot aquecido na emergência (1 = sim)", 1, 1, "0/1", "GTN IM 3.7.3 (lista mínima de emergência). 14 V: não há pitot na ELA de 1976", True, "0"),
]
for r, (key, lab, v14, v28, unit, src, kf, nf) in enumerate(prem, 5):
    P[key] = r
    put(ps, r, 1, lab)
    for col, v in ((2, v14), (3, v28)):
        put(ps, r, col, v, BLUE, nf, KEYFILL if kf else None)
    put(ps, r, 4, unit)
    put(ps, r, 5, src).alignment = WRAP
r = len(prem) + 5
P["bat1h"] = r
put(ps, r, 1, "Bateria efetiva na taxa de 1 h", BOLD)
for col in (2, 3):
    L = CL(col)
    put(ps, r, col, f"={L}{P['bat_nom']}*{L}{P['bat_rate']}*{L}{P['rate_unc']}", BOLD, "0.000")
put(ps, r, 4, "Ah")
put(ps, r, 5, "Nominal × fator de taxa × cenário de capacidade")


def pr(key, col):
    return f"Premissas!${col}${P[key]}"


# ------------------------------------------------------------------ Cargas
COLS = ["Item", "Barramento", "Classe", "Situação", "Antes", "Depois", "I máx (A)", "I típica (A)", "I usada (A)",
        "Disjuntor (A)"] + [f"k {p}" for p in PH_PT] + [f"k·I {p} (A)" for p in PH_PT] + [
        "Contínua (1/0)", "Carga no disjuntor (I máx)", "TX (1/0)", "I método Garmin (A)", "Potência constante (1/0)",
        "I publicada na bateria (A)", "I na bateria (A)", "Farol (1/0)", "Flap (1/0)", "Fonte"]
C = {name: i + 1 for i, name in enumerate(COLS)}
KCOL = [CL(11 + j) for j in range(6)]    # K..P
KI = [CL(17 + j) for j in range(6)]      # Q..V
CARGAS = {}


def cargas(name, ac, pc):
    cs = wb.create_sheet(name)
    title(cs, f"Cargas e cálculo por fase: {ac.model}",
          "I usada = típica (se Premissas 'típica' = 1 e o item é adicionado) ou máxima. k·I = corrente média na fase.")
    header(cs, 4, COLS, [30, 10, 12, 11, 7, 7, 8, 8, 8, 9] + [8] * 6 + [9] * 6 + [9, 10, 6, 9, 9, 9, 9, 7, 7, 70])
    removed = set(inst.removed_for(ac.model))
    pool = list(ac.baseline_loads) + list(inst.added)
    items = [(l.at_voltage(ac.voltage), "Removida" if l.name in removed else "Base", None, l) for l in ac.baseline_loads]
    for l in inst.added:
        typ = l.at_voltage(ac.voltage, True).current_a if l.typical_by_v else None
        items.append((l.at_voltage(ac.voltage), "Adicionada", typ, l))
    first = 5
    for i, (l, sit, typ, raw) in enumerate(items):
        r = first + i
        put(cs, r, 1, l.name)
        put(cs, r, 2, l.bus)
        put(cs, r, 3, "contínua" if l.cls == "continuous" else "intermitente", BLUE)
        put(cs, r, 4, sit, BLUE)
        put(cs, r, 5, f'=IF(D{r}="Adicionada",0,1)', nf="0")
        put(cs, r, 6, f'=IF(D{r}="Removida",0,1)', nf="0")
        put(cs, r, 7, l.current_a, BLUE, "0.000")
        put(cs, r, 8, typ, BLUE, "0.000")
        put(cs, r, 9, f'=IF(AND(D{r}="Adicionada",{pr("typ", pc)}=1,H{r}<>""),H{r},G{r})', nf="0.000")
        put(cs, r, 10, l.breaker_a, BLUE, "0.0")
        for j, ph in enumerate(PHASES):
            k = l.k(ph)
            if is_tx(l.name) and k > 0:
                v, f = f"={pr('tx', pc)}", GREEN
            elif l.radio and k > 0 and any(is_tx(x.name) and x.radio == l.radio and x.k(ph) > 0 for x in pool):
                v, f = f"=MAX(0,{k}-{pr('tx', pc)})", GREEN   # receive and transmit mutually exclusive
            elif is_landing_light(l) and ph in ("takeoff_climb", "landing") and k > 0:
                v, f = f"={pr('ll', pc)}", GREEN
            elif "pitot" in l.name.lower() and ph == "emergency":
                v, f = f"={pr('pitot', pc)}", GREEN
            else:
                v, f = k, BLUE
            put(cs, r, 11 + j, v, f, "0.00")
            put(cs, r, 17 + j, f"=$I{r}*{KCOL[j]}{r}", nf="0.000")
        put(cs, r, 23, f'=IF(C{r}="contínua",1,0)', nf="0")
        paired = bool(l.radio) and not is_tx(l.name) and any(is_tx(x.name) and x.radio == l.radio for x in pool)
        full = f"MAX(K{r}:P{r})+{pr('tx', pc)}>=1" if paired else f"MAX(K{r}:P{r})>=1"   # radio powered in RX or TX
        put(cs, r, 24, f'=IF(AND(D{r}="Adicionada",J{r}<>"",W{r}=1,{full}),G{r}/J{r},"")', nf="0%")
        put(cs, r, 25, 1 if is_tx(l.name) else 0, BLUE, "0")
        put(cs, r, 26, f'=IF(H{r}<>"",H{r},G{r})', nf="0.000")
        put(cs, r, 27, 1 if l.constant_power else 0, BLUE, "0")
        put(cs, r, 28, l.current_batt_a, BLUE, "0.000")
        put(cs, r, 29, f'=IF({pr("cp", pc)}=1,IF(AB{r}<>"",AB{r},IF(AA{r}=1,I{r}*{pr("volt", pc)}/{pr("vbat", pc)},I{r})),I{r})', nf="0.000")
        put(cs, r, 30, 1 if is_landing_light(l) else 0, BLUE, "0")
        put(cs, r, 31, 1 if "flap motor" in l.name.lower() else 0, BLUE, "0")
        put(cs, r, 32, l.source)
    last = first + len(items) - 1
    CARGAS[name] = {"first": first, "last": last, "pc": pc}
    cs.freeze_panes = "B5"


cargas("Cargas_14V", ac14, "B")
cargas("Cargas_28V", ac28, "C")

# ------------------------------------------------------------------ Resumo
rs = wb.create_sheet("Resumo")
title(rs, "Resumo: regras R1a, R1b, R2, R3 e atalho da Garmin", "Tudo por fórmula a partir de Premissas e das abas de cargas.")
header(rs, 4, ["Grandeza", "172M 1976 (14 V)", "172R/S (28 V)", "Unidade", "Como é calculado"], [50, 18, 18, 8, 85])
R, row = {}, [5]
SHEETS = ("Cargas_14V", "Cargas_28V")


def rng(sh, col):
    i = CARGAS[sh]
    return f"{sh}!${col}${i['first']}:${col}${i['last']}"


def line(key, label, fn, unit, how, nf="0.00", bold=False, fill=None):
    r = row[0]
    R[key] = r
    put(rs, r, 1, label, BOLD if bold else BLACK)
    for col, sh in ((2, SHEETS[0]), (3, SHEETS[1])):
        put(rs, r, col, fn(sh, CL(col), CARGAS[sh]["pc"]), BOLD if bold else BLACK, nf, fill)
    put(rs, r, 4, unit)
    put(rs, r, 5, how).alignment = WRAP
    row[0] += 1


def sec(text):
    r = row[0]
    put(rs, r, 1, text, BOLD, fill=SUBFILL)
    for c in range(2, 6):
        rs.cell(row=r, column=c).fill = SUBFILL
    row[0] += 1


for state, flag in (("ANTES", "E"), ("DEPOIS", "F")):
    sec(f"Corrente média por fase (Σ k·I), {state} da instalação")
    for j, ph in enumerate(PH_PT):
        line(f"avg{flag}{j}", ph, lambda sh, L, pc, j=j, flag=flag: f"=SUMPRODUCT({rng(sh, flag)},{rng(sh, KI[j])})",
             "A", "Todas as cargas, intermitentes pela média (k)")
    sec(f"Corrente contínua por fase (só classe contínua), {state}")
    for j, ph in enumerate(PH_PT[:5]):
        line(f"cont{flag}{j}", ph, lambda sh, L, pc, j=j, flag=flag: f"=SUMPRODUCT({rng(sh, flag)},{rng(sh, 'W')},{rng(sh, KI[j])})",
             "A", "Exclui farol, flap, transmissão e luzes de cortesia (AC 43.13-1B 11-35)")

sec("R1a: carga contínua ≤ 80 % do alternador (AC 43.13-1B CHG 1, 11-35a/e)")
for state, flag in (("antes", "E"), ("depois", "F")):
    line(f"r1a{flag}", f"Carga contínua / alternador, {state}",
         lambda sh, L, pc, flag=flag: f"=MAX({L}{R[f'cont{flag}0']}:{L}{R[f'cont{flag}4']})/{pr('alt', pc)}",
         "%", "Maior soma contínua das fases normais ÷ placa", "0.0%", bold=flag == "F")
line("r1a", "R1a atendida (depois)?", lambda sh, L, pc: f'=IF({L}{R["r1aF"]}<={pr("alt_lim", pc)},"SIM","NÃO")', "", "", "@", True, KEYFILL)
sec("R1b: carga média da fase ≤ 80 % (CASA AC 21-38 2.1.1 e 4.4.3; CAA NZ AC21-11 App. 1)")
for state, flag in (("antes", "E"), ("depois", "F")):
    line(f"r1b{flag}", f"Carga média / alternador, {state}",
         lambda sh, L, pc, flag=flag: f"=MAX({L}{R[f'avg{flag}0']}:{L}{R[f'avg{flag}4']})/{pr('alt', pc)}",
         "%", "Maior média das fases normais ÷ placa", "0.0%", bold=flag == "F")
line("r1b", "R1b atendida (depois)?", lambda sh, L, pc: f'=IF({L}{R["r1bF"]}<={pr("alt_lim", pc)},"SIM","NÃO")', "", "", "@", True, KEYFILL)
sec("R2: disjuntores, corrente máxima (CASA AWB 24-007; AC 21-38 4.6.4)")
line("bk", "Maior carga contínua / disjuntor", lambda sh, L, pc: f"=MAX({rng(sh, 'X')})", "%", "Coluna 'Carga no disjuntor'", "0.0%")
line("r2", "R2 atendida?", lambda sh, L, pc: f'=IF({L}{R["bk"]}<={pr("bk_lim", pc)},"SIM","NÃO")', "", "", "@", True, KEYFILL)

for state, flag in (("ANTES", "E"), ("DEPOIS", "F")):
    sec(f"R3: bateria de emergência, {state} (perfil CASA AC 21-38 B.2)")
    s = flag
    line(f"ipre{s}", "I antes do corte (cargas de cruzeiro na bateria)",
         lambda sh, L, pc, s=s: f"=SUMPRODUCT({rng(sh, s)},{rng(sh, KCOL[3])},{rng(sh, 'AC')})", "A", "Σ k_cruzeiro · I_bateria")
    line(f"ished{s}", "I após o corte (cargas essenciais)",
         lambda sh, L, pc, s=s: f"=SUMPRODUCT({rng(sh, s)},{rng(sh, KCOL[5])},{rng(sh, 'AC')})", "A", "Σ k_emergência · I_bateria")
    line(f"iapp{s}", "I na aproximação (essenciais + farol + flap)",
         lambda sh, L, pc, s=s: (f"={L}{R[f'ished{s}']}+SUMPRODUCT({rng(sh, s)},{rng(sh, 'AD')},{rng(sh, 'AC')})"
                                 f"+{pr('flap_app', pc)}*SUMPRODUCT({rng(sh, s)},{rng(sh, 'AE')},{rng(sh, 'AC')})"
                                 f"-SUMPRODUCT({rng(sh, s)},{rng(sh, 'AE')},{rng(sh, KCOL[5])},{rng(sh, 'AC')})"),
         "A", "I_corte + farol + k_flap·I_flap (troca o k de emergência do flap pelo da aproximação)")
    line(f"av{s}", "CASA: capacidade disponível", lambda sh, L, pc: f"={pr('bat1h', pc)}*60*{pr('casa_f', pc)}",
         "A·min", "C₁ × 60 × 72 % (AC 21-38 4.5.12.6)", "0.0")
    line(f"pre{s}", "CASA: consumo até o corte",
         lambda sh, L, pc, s=s: f"={L}{R[f'ipre{s}']}*{pr('tpre', pc)}*IF({L}{R[f'ipre{s}']}>2*{pr('bat1h', pc)},1.2,1)",
         "A·min", "I_pré × t_corte, +20 % se I_pré > 2·C₁ (4.5.12.4)", "0.0")
    line(f"res{s}", "CASA: reserva da aproximação", lambda sh, L, pc, s=s: f"={L}{R[f'iapp{s}']}*{pr('tapp', pc)}",
         "A·min", "I_aprox × t_aprox", "0.0")
    line(f"casa{s}", "Autonomia, método CASA",
         lambda sh, L, pc, s=s: (f"=IF({L}{R[f'pre{s}']}>={L}{R[f'av{s}']},{L}{R[f'av{s}']}/({L}{R[f'pre{s}']}/{pr('tpre', pc)}),"
                                 f"IF({L}{R[f'av{s}']}-{L}{R[f'pre{s}']}-{L}{R[f'res{s}']}<0,"
                                 f"{pr('tpre', pc)}+({L}{R[f'av{s}']}-{L}{R[f'pre{s}']})/{L}{R[f'iapp{s}']},"
                                 f"{pr('tpre', pc)}+({L}{R[f'av{s}']}-{L}{R[f'pre{s}']}-{L}{R[f'res{s}']})/{L}{R[f'ished{s}']}+{pr('tapp', pc)}))"),
         "min", "Perfil viável: t_corte + (disponível − pré − reserva) ÷ I_corte + t_aprox; inviável: esgotamento sequencial", "0.0")

    def tpk(cur, s=s):
        return lambda sh, L, pc: f"=60*({pr('bat1h', pc)}*{pr('soh', pc)}*{pr('soc', pc)}*{pr('kt', pc)}/{L}{R[cur + s]})^{pr('n', pc)}"
    line(f"tpre{s}", "Peukert: tempo de descarga total a I_pré", tpk("ipre"), "min", "t(I) = 60·(C₁·SOH·SOC·k_T / I)^n", "0.0")
    line(f"tshed{s}", "Peukert: tempo de descarga total a I_corte", tpk("ished"), "min", "idem", "0.0")
    line(f"tapp{s}", "Peukert: tempo de descarga total a I_aprox", tpk("iapp"), "min", "idem", "0.0")
    line(f"x{s}", "Peukert: tempo em cruzeiro de emergência",
         lambda sh, L, pc, s=s: f"=(1-{pr('tpre', pc)}/{L}{R[f'tpre{s}']}-{pr('tapp', pc)}/{L}{R[f'tapp{s}']})*{L}{R[f'tshed{s}']}",
         "min", "x = (1 − t_corte/t(I_pré) − t_aprox/t(I_aprox)) · t(I_corte)", "0.0")
    line(f"pk{s}", "Autonomia, Peukert",
         lambda sh, L, pc, s=s: (f"=IF({pr('tpre', pc)}/{L}{R[f'tpre{s}']}>=1,{L}{R[f'tpre{s}']},"
                                 f"IF({pr('tpre', pc)}/{L}{R[f'tpre{s}']}+{pr('tapp', pc)}/{L}{R[f'tapp{s}']}>1,"
                                 f"{pr('tpre', pc)}+(1-{pr('tpre', pc)}/{L}{R[f'tpre{s}']})*{L}{R[f'tapp{s}']},"
                                 f"{pr('tpre', pc)}+{L}{R[f'x{s}']}+{pr('tapp', pc)}))"),
         "min", "Perfil viável: t_corte + x + t_aprox; inviável: esgotamento sequencial", "0.0")
    line(f"mg{s}", f"Margem sobre 30 min, {state.lower()}",
         lambda sh, L, pc, s=s: f"=MIN({L}{R[f'casa{s}']},{L}{R[f'pk{s}']})-{pr('req', pc)}", "min",
         "Menor das duas autonomias − exigido", "0.0", bold=True)
line("r3", "R3 atendida (depois)?", lambda sh, L, pc: f'=IF({L}{R["mgF"]}>=0,"SIM","NÃO")', "", "", "@", True, KEYFILL)

sec("Atalho da Garmin: variação líquida (GTN IM 190-01007-A3 3.7.2, Fig. 3-14)")
garm = lambda flag: (lambda sh, L, pc: f'=SUMPRODUCT(--({rng(sh, "D")}="{flag}"),1-{rng(sh, "Y")},{rng(sh, "Z")})')
line("gadd", "Adicionado (típica, sem transmissão)", garm("Adicionada"), "A", "Corrente típica dos itens adicionados")
line("grem", "Removido (sem transmissão)", garm("Removida"), "A", "Corrente da ELA original dos itens removidos")
line("gnet", "Variação líquida", lambda sh, L, pc: f"={L}{R['gadd']}-{L}{R['grem']}", "A", "Adicionado − removido", "+0.00;-0.00;0.00", True)
line("gdec", "Decisão pelo atalho", lambda sh, L, pc: f'=IF({L}{R["gnet"]}<=0,"Dispensa análise adicional","Exige ELA completa")',
     "", "3.7.2.1 dispensa análise se a carga cai, assumindo sistema dentro dos limites antes", "@", True)

# ------------------------------------------------------------------ Sensibilidade
ts = wb.create_sheet("Sensibilidade_Tornado")
title(ts, "Sensibilidade, um parâmetro por vez", "Resultados de ela_stc/sensitivity.py (valores, não fórmulas). Os demais parâmetros ficam na base.")
header(ts, 4, ["Modelo", "Parâmetro", "Baixo", "Base", "Alto", "R1a baixo", "R1a base", "R1a alto", "R1b baixo", "R1b base",
               "R1b alto", "Margem baixo (min)", "Margem base", "Margem alto", "Fonte do intervalo"],
       [24, 50, 7, 7, 7, 9, 9, 9, 9, 9, 9, 10, 10, 10, 60])
r = 5
for ac in aml:
    for t in tornado(ac, inst):
        vals = [ac.model, t["param"], t["low"], t["base"], t["high"], t["cont_low"], t["cont_base"], t["cont_high"],
                t["avg_low"], t["avg_base"], t["avg_high"], t["margin_low"], t["margin_base"], t["margin_high"], t["source"]]
        for c, v in enumerate(vals, 1):
            put(ts, r, c, v, nf="0.0%" if 6 <= c <= 11 else ("0.0" if 12 <= c <= 14 else ("0.00" if 3 <= c <= 5 else None)))
        r += 1
    r += 1
put(ts, r, 1, "Limiares", BOLD)
r += 1
for typ, lab in ((1, "típica"), (0, "máxima")):
    for d in np.arange(0.3, 1.0001, 0.01):
        if analyze(ac14, inst, {"landing_light_duty": d, "use_typical": typ})["alt_frac_avg"] > 0.80:
            put(ts, r, 1, f"14 V, corrente {lab}: R1b passa de 80 % se o farol ficar ligado mais de {d - 0.01:.0%} da decolagem e do pouso")
            r += 1
            break
for kt, lab in ((1.0, "temperatura de referência"), (0.7, "frio, kT 0,7")):
    for s_ in np.arange(1.0, 0.39, -0.01):
        if analyze(ac28, inst, {"soh": s_, "temp_factor": kt})["margin_min"] < 0:
            msg = (f"28 V ({lab}): margem negativa mesmo com SOH 100 %" if s_ > 0.995
                   else f"28 V ({lab}): margem negativa com SOH abaixo de {s_ + 0.01:.0%}")
            put(ts, r, 1, msg)
            r += 1
            break

ms = wb.create_sheet("Sensibilidade_MC")
title(ms, "Variabilidade física (Monte Carlo)", "Só os parâmetros físicos (uniformes e independentes); escolhas de método ficam na base. N = 5000, semente 7. Frações de cenários amostrados, não probabilidades operacionais.")
header(ms, 4, ["Métrica", ac14.model, ac28.model], [44, 26, 26])
mc = [global_mc(ac, inst, 5000) for ac in aml]
r = 5
for lab, key, nf in [("R1a, P5", "cont_p5", "0.0%"), ("R1a, P95", "cont_p95", "0.0%"), ("Fração de cenários com R1a > 80 %", "p_cont_over_80", "0.0%"),
                     ("R1b, P5", "avg_p5", "0.0%"), ("R1b, P95", "avg_p95", "0.0%"), ("Fração de cenários com R1b > 80 %", "p_avg_over_80", "0.0%"), ("  erro-padrão amostral", "se_avg_over_80", "0.0%"),
                     ("Margem, P5 (min)", "margin_p5", "0.0"), ("Margem, média (min)", "margin_mean", "0.0"),
                     ("Margem, P95 (min)", "margin_p95", "0.0"), ("Fração de cenários com margem negativa", "p_margin_negative", "0.0%"), ("  erro-padrão amostral", "se_margin_negative", "0.0%")]:
    put(ms, r, 1, lab)
    for c, m in enumerate(mc, 2):
        put(ms, r, c, m[key], nf=nf)
    r += 1
r += 1
for key, lab in (("rank_avg", "Correlação com R1b"), ("rank_margin", "Correlação com a margem")):
    put(ms, r, 1, lab, BOLD)
    r += 1
    for idx in range(len(mc[0][key])):
        for c, m in enumerate(mc, 2):
            put(ms, r, c, f"{m[key][idx][0]}: {m[key][idx][1]:+.2f}")
        r += 1
    r += 1

# ------------------------------------------------------------------ Fontes
fs = wb.create_sheet("Fontes")
title(fs, "Documentos e páginas")
header(fs, 4, ["Documento", "Identificação", "O que foi usado", "Página / seção"], [44, 30, 64, 40])
src = [
    ("Cessna 172 & Skyhawk Service Manual 1969-76", "Change 5", "ELA oficial (14 V) e classificação 'running load'; alternador; bateria", "16-37/16-38 (PDF 285-286); PDF 253; PDF 246"),
    ("Cessna Model 172 Maintenance Manual (1996 & On)", "172RMM rev. 15", "ELA oficial 24 V e 28 V; notas A, B, C, I, J, K; bateria 12,75 Ah (5 h)", "24-70-00 (PDF 394-397); PDF 352, 361, 371"),
    ("Garmin GTN 6XX/7XX AML STC Installation Manual", "190-01007-A3 Rev 4 (2012)", "Correntes (Table 1-5); disjuntores (Fig. E-4); procedimento de ELA (3.7)", "PDF 35, 303, 116-118"),
    ("Garmin GMA 342/345 Installation Manual", "190-01878-02 Rev 6 (2023)", "Correntes (Table 1-7); disjuntor 5 A", "1.3.3"),
    ("Garmin GTX 3X5 TSO Installation Manual", "190-01499-02 Rev 9 (2017)", "Correntes (Table 1-12)", "1.13"),
    ("Garmin G5 Part 23 AML STC Installation Manual", "190-01112-10 Rev 28 (2021)", "Correntes (Table 1-4); disjuntor 5 A", "1.7.2; 3.2.1"),
    ("FAA AC 43.13-1B", "CHG 1 (27/09/2001)", "Regra dos 80 % sobre a carga contínua (11-35a/e); intermitentes curtas excluídas (11-35c/d); determinar o estado antes de instalar (11-36)", "Cap. 11, Sec. 3, p. 11-12"),
    ("FAA AC 43.13-2C", "29/07/2026", "ELA na condição mais adversa (noite/IFR); ASTM F2490-20; reaproveitar ELA anterior", "3.9"),
    ("14 CFR 23.1351(a)(2) (até emenda 23-63)", "", "ELA ou medição com combinações e durações prováveis", ""),
    ("CASA AC 21-38", "v2.1 (dez/2022)", "Média e máxima; máxima não usada para capacidade; RMS; tensão de bateria; bateria 72 %; perfil B.2", "2.1.1, 4.3.2, 4.4.3, 4.4.7, 4.5.12, 4.6.4, B.2"),
    ("CAA NZ AC21-11 / AC91-23", "Rev 1 (2019)", "Corrente nominal; máxima se desconhecida; média da fase; limite 85 %; TX 10 %; 75 % e +20 %", "6.1.2, 6.1.3, 6.1.5.1, 5.3, App. 1"),
    ("Concorde CMM 5-0171", "Rev Q (2018)", "Nunca usar bateria abaixo de 80 % da capacidade", "Introdução 4.A; Testing 7"),
    ("Concorde RG-25 / RG-25XC, folheto", "IEC 60952-1", "Bateria 14 V: 22 Ah C1 (RG-25) e 24 Ah C1 (RG-25XC)", "Rated capacity C1"),
]
for r, rr in enumerate(src, 5):
    for c, v in enumerate(rr, 1):
        put(fs, r, c, v).alignment = WRAP

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
wb.save(OUT)
print("saved", OUT)
print("ROWS", {k: R[k] for k in ("r1aE", "r1aF", "r1bE", "r1bF", "bk", "casaE", "pkE", "mgE", "casaF", "pkF", "mgF", "gnet", "isrhedF" if False else "ishedF")})
