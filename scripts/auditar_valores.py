"""Audita cada corrente de data/caso_c172.yaml contra o texto extraído dos documentos-fonte.

Uso:
    python scripts/auditar_valores.py [caso.yaml] --sources DIR [--out docs/auditoria_valores.md]

DIR (ou a variável de ambiente ELA_SOURCES) deve conter os textos extraídos com `pdftotext -layout`
dos documentos listados em FILES. Os manuais não são redistribuídos com o software (direitos autorais);
cada usuário obtém os PDFs junto ao fabricante e gera os textos localmente.

Cobertura: (1) 172R/S 28 V: extração automática da tabela 24-70-00 do 172RMM; (2) equipamentos Garmin:
busca por expressão regular no texto dos manuais de instalação; (3) 172M 14 V: a tabela do Service Manual
1969-76 é digitalizada e foi conferida visualmente, por isso os valores de referência estão fixos em SM1976.
Itens sem linha na fonte são marcados como premissa.
"""
import argparse
import os
import re

import yaml

FILES = {
    "mm": "mm172r.txt",
    "gtn": "GTN6XX-7XX_IM.txt",
    "gma": "GMA 342_345 Installation Manual 190-01878-02_06.txt",
    "gtx": "Garmin_GTX3X5_InstallationManualRev9-2017-06.txt",
    "g5": "190-01112-10_28.txt",
}
ap = argparse.ArgumentParser()
ap.add_argument("case", nargs="?", default="data/caso_c172.yaml")
ap.add_argument("--sources", default=os.environ.get("ELA_SOURCES"), help="pasta com os textos extraídos")
ap.add_argument("--out", default="docs/auditoria_valores.md")
args = ap.parse_args()
if not args.sources:
    ap.error("informe --sources DIR ou defina ELA_SOURCES")
missing = [f for f in FILES.values() if not os.path.exists(os.path.join(args.sources, f))]
if missing:
    ap.error("arquivos ausentes em %s: %s" % (args.sources, ", ".join(missing)))
TXT = {k: os.path.join(args.sources, v) for k, v in FILES.items()}
txt = {k: open(v, encoding="utf-8", errors="ignore").read() for k, v in TXT.items()}
mm_lines = txt["mm"].splitlines()
i0 = next(i for i, l in enumerate(mm_lines) if "ELECTRICAL LOAD ANALYSIS - DESCRIPTION AND OPERATION" in l and i > 16000)
ela = mm_lines[i0:i0 + 170]
num = re.compile(r"(?<![\w.])(\d+\.?\d*)(?![\w.])")


def mm_row(key):
    line = next(l for l in ela if key in l)
    vals = [float(x) for x in num.findall(line.split(key, 1)[1])]
    return vals[-2], vals[-1]


KEYS = {
    "landing light 4596": "Landing Light (4596", "taxi light 4587": "Taxi Light (4587", "navigation lights": "Navigation Lights",
    "wing anti-collision lights": "Wing Anti-collision", "beacon light": "Beacon Light", "under wing courtesy lights": "Under Wing Courtesy",
    "map light": "Map Light", "pedestal light": "Pedestal Lights", "flap motor": "Flap Motor", "pitot heat": "Pitot Heat",
    "hourmeter": "Hourmeter", "battery relay coil": "Battery Relay Coil", "alternator relay coil": "Alternator Relay Coil",
    "alternator field and ACU": "Alternator Field and ACU", "ACU bus sense": "ACU Bus Sense",
    "autopilot KAP 140 computer": "Autopilot Computer (KAP 140)", "pitch servo and clutch": "Pitch Servo & Clutch",
    "pitch trim servo and clutch": "Pitch Trim Servo", "roll servo and clutch": "Roll Servo", "turn coordinator": " Turn Coordinator",
    "ADF KR 87": "ADF Receiver (KR 87)", "glareshield light fluorescent": "Glareshield Light (Fluorescent)", "radio lights": "Radio Lights",
    "annunciator panel": "Annunciator Panel (All", "avionics fan": "Avionics Fan", "engine and fuel gauges": "Engine and Fuel Gauges",
    "audio panel KMA 26": "Audio Panel (KMA-26)", "GPS KLN 94": "GPS (KLN 94)", "transponder KT 76": "Transponder (KT 76)",
    "altitude encoder SSD120": "Altitude Encoder (SSD120)", "nav/com 1 KX 155A RX": "#1 Nav/Comm (KX 155A) (Receive)",
    "nav/com 1 KX 155A TX": "#1 Nav/Comm (KX 155A) (Transmit)", "nav/com 2 KX 165A RX": "#2 Nav/Comm (KX 165A) (Receive)",
}
# 14 V: conferido visualmente na página renderizada (SM 1969-76, 16-37/16-38, coluna 1976)
SM1976 = {"battery contactor": 0.6, "fuel indicators": 0.4, "flashing beacon": 7.0, "instrument lights": 1.3, "position lights": 5.6,
          "turn coordinator": 0.8, "flap position indicator": 0.1, "strobe lights": 4.0, "nav/com 1 RT-328T": 1.5, "nav/com 2 RT-308C": 1.5,
          "transponder RT-359A": 1.0, "encoding altimeter EA-401A": 0.065, "ADF R-546E": 1.0, "glideslope R-443B": 0.4,
          "marker beacon R-402A": 0.3, "autopilot AF-295B": 2.0, "flap motor": 15.0, "landing and taxi light": 20.0,
          "courtesy and dome lights": 2.5, "map light": 0.33}


def gtn_tab():
    i = txt["gtn"].index("Table 1-5. GTN and GMA 35 Current Specifications\n")
    return txt["gtn"][i:i + 2500]


GAR = {  # name -> (doc key, regex that must appear in source text, {V: (typ, max)})
    "GTN 650 main + NAV": ("gtn", [r"1\.6 A \[1\]\s+2\.8 A \[2\]\s+0\.8 A \[1\]\s+1\.5 A \[2\]", r"0\.60 A\s+1\.16 A \[2\]\s+0\.30 A\s+0\.58 A \[2\]"],
                           {14: (1.6 + 0.60, 2.8 + 1.16), 28: (0.8 + 0.30, 1.5 + 0.58)}),
    "GTN 650 COM RX": ("gtn", [r"0\.45 A\s+4\.02 A \(10W COM\)\s+0\.21 A"], {14: (0.45, 0.45), 28: (0.21, 0.21)}),
    "GTN 650 COM TX": ("gtn", [r"4\.02 A \(10W COM\)", r"1\.76 A \(10W COM\)"], {14: (4.02, 4.02), 28: (1.76, 1.76)}),
    "GMA 345 audio panel": ("gma", [r"0\.83 A @ 14 VDC", r"0\.43 A @ 28 VDC", r"1\.19 A @ 14 VDC", r"0\.90 A @ 28 VDC"], {14: (0.83, 1.19), 28: (0.43, 0.90)}),
    "GTX 345 transponder ADS-B": ("gtx", [r"GTX 345\s+Input current, typical\s+0\.72 A\s+0\.36 A", r"Input current, maximum\s+1\.30 A\s+0\.65 A"], {14: (0.72, 1.30), 28: (0.36, 0.65)}),
    "G5 indicador de atitude": ("g5", [r"Average Current Draw @ 14 VDC\s+\.200 A", r"Max Current Draw @ 14 VDC\s+\.250 A", r"Average Current Draw @ 28 VDC\s+\.100 A", r"Max Current Draw @ 28 VDC\s+\.125 A"],
                                {14: (0.20, 0.25), 28: (0.10, 0.125)}),
}

d = yaml.safe_load(open(args.case, encoding="utf-8"))
out = ["# Auditoria dos valores do caso de estudo", "",
       "Gerado por `scripts/auditar_valores.py`: cada corrente do arquivo do caso é comparada com o texto extraído do documento-fonte.", "",
       "Cobertura: correntes de carga (típica e máxima). Não são auditados por este script: capacidades de disjuntor, ciclos de trabalho, "
       "fases e premissas de operação; esses itens têm a fonte citada no próprio arquivo do caso.", ""]
problems = 0
out += ["## 172M 1976 (14 V): Service Manual 1969-76, 16-37/16-38, coluna 1976", "",
        "Conferência: página renderizada e comparada visualmente (tabela digitalizada, texto desalinhado).", "",
        "| Item | Arquivo do caso (A) | Fonte (A) | Situação |", "| --- | --- | --- | --- |"]
for l in d["aml"][0]["baseline_loads"]:
    src = SM1976.get(l["name"])
    if src is None:
        st = "Não consta da tabela (premissa)"
    else:
        st = "OK" if abs(src - l["current_a"]) < 1e-9 else "**DIFERENTE**"
        problems += st != "OK"
    out.append(f"| {l['name']} | {l['current_a']} | {src if src is not None else '-'} | {st} |")
out += ["", "## 172R/S (28 V): Maintenance Manual 172RMM, 24-70-00, coluna 28 VDC (extração automática do texto)", "",
        "| Item | Arquivo do caso (A) | Fonte 24 V / 28 V (A) | Situação |", "| --- | --- | --- | --- |"]
for l in d["aml"][1]["baseline_loads"]:
    k = KEYS.get(l["name"])
    if not k:
        out.append(f"| {l['name']} | {l['current_a']} | 0,02 A por instrumento (quantidade assumida) | Premissa |")
        continue
    v24, v28 = mm_row(k)
    st = "OK" if abs(v28 - l["current_a"]) < 1e-9 else "**DIFERENTE**"
    problems += st != "OK"
    out.append(f"| {l['name']} | {l['current_a']} | {v24} / {v28} | {st} |")
out += ["", "## Instalação Garmin (extração automática do texto dos manuais)", "",
        "| Item | Tensão | Típica / máxima no caso (A) | Típica / máxima na fonte (A) | Trecho da fonte encontrado | Situação |",
        "| --- | --- | --- | --- | --- | --- |"]
for l in d["installation"]["added"]:
    doc, pats, ref = GAR[l["name"]]
    text = gtn_tab() if doc == "gtn" else txt[doc]
    found = all(re.search(p, text) for p in pats)
    for v in (14, 28):
        case = (l["typical_by_v"][v], l["current_by_v"][v])
        okv = all(abs(a - b) < 1e-9 for a, b in zip(case, ref[v]))
        st = "OK" if (okv and found) else "**DIFERENTE**"
        problems += st != "OK"
        out.append(f"| {l['name']} | {v} V | {case[0]} / {case[1]} | {ref[v][0]:.3g} / {ref[v][1]:.3g} | {'sim' if found else 'NÃO'} | {st} |")
out += ["", f"**Divergências encontradas: {problems}**", ""]
open(args.out, "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out[-3:]))
