# ELA-STC

[![tests](https://github.com/Messias007/ela-stc/actions/workflows/tests.yml/badge.svg)](https://github.com/Messias007/ela-stc/actions/workflows/tests.yml)

Open-source, compliance-oriented electrical load analysis (ELA) for avionics installations approved through approved model list supplemental type certificates (AML-STC) in small airplanes. One added equipment package is evaluated against every model of the list, per bus, circuit and flight phase, and every check cites its source.

> **Scope.** Outputs state whether each **selected analysis criterion** is met (PASS / FAIL / NOT EVALUATED). They are not a finding of compliance with the approved certification basis of any aircraft, and the tool does not replace the engineering judgment of the applicant or approval by a designee or authority. See `docs/aplicabilidade.md`.

## Method (v3)

| Criterion | Metric | Limit | Source |
| --- | --- | --- | --- |
| R1a | Continuous load / alternator rating, worst phase | ≤ 0.80 | FAA AC 43.13-1B 11-35 |
| R1b | Average phase load incl. intermittent loads / alternator | ≤ 0.80 | CASA AC 21-38 v2.1 4.3.3 |
| R2 | Continuous load per circuit / breaker, maximum current | ≤ 0.85 | CASA AWB 24-007 |
| R3 | Battery endurance margin over 30 min (reference criterion) | ≥ 0 | 14 CFR 23.1353(h) amdt 23-62 |

- Typical current for capacity and endurance, maximum current for breakers and as a reported bound.
- Radio receive and transmit modeled as mutually exclusive states.
- Emergency profile (pre-shed, shed cruise, approach) at battery voltage, depleted sequentially, with the CASA method and a Peukert model that keeps state of health, state of charge and temperature separate.
- Method choices compared one at a time; physical variability sampled by Monte Carlo (fraction of sampled scenarios, with standard error and seed).

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q
python -m ela_stc data/caso_c172.yaml data/rules.yaml saida/caso_c172
```

Open `web/ela-stc.html` in a browser for the interactive version; projects exported there load directly in Python.

## Reproducing the paper

```bash
python scripts/resultados_artigo.py     # every number in the paper -> saida/resultados_artigo.md
python scripts/figuras_artigo.py        # paper/figures/*.pdf
python scripts/gerar_planilha.py        # formula spreadsheet saida/ELA_C172_calculos.xlsx
python scripts/verificar_planilha.py <path/to/recalc.py>   # LibreOffice recalculation vs Python, 8 input sets
python scripts/gerar_fixtures_web.py && python scripts/build_web.py
(cd web && node test_engine.js && node test_roundtrip.js) # browser vs Python parity
python scripts/auditar_valores.py --sources DIR            # DIR: text extracted (pdftotext -layout) from the manuals
```

The manufacturer manuals used as sources are copyrighted and are not redistributed; each load in `data/caso_c172.yaml` cites its document and page. The audit script covers load currents only.

## Repository layout

| Path | Content |
| --- | --- |
| `ela_stc/` | Python package (analysis, battery, rules, sensitivity, Monte Carlo, reports) |
| `data/` | Cessna 172 case (14 V 172M 1976, 28 V 172R/S), criteria file, illustrative example |
| `scripts/` | Paper results, figures, spreadsheet, browser build, audit |
| `tests/` | Python tests (CASA worked examples, edge cases, browser round trip) |
| `web/` | Browser version and parity tests |
| `saida/` | Generated outputs |
| `docs/` | Applicability by model, source audit |

Code comments and some outputs are in Portuguese.

## Citation

See `CITATION.cff`. Paper: M. S. de Melo, "A Compliance-Oriented Electrical Load Analysis Framework for Multi-Model Supplemental Type Certification of General Aviation Avionics Installations" (submitted to *Aerospace*).

## License

MIT
