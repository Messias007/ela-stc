# Matriz multimodelo: Retrofit glass cockpit ilustrativo (PFD + navegador GPS + transponder ADS-B)

PASS = atende ao critério de análise selecionado; não equivale a conformidade com a base de certificação aprovada.
Opções: corrente típica, TX 0.1, corte em 5.0 min.

| Regra | Modelo A (familia C172, 28 V) | Modelo B (familia C172, alternador menor) |
| --- | --- | --- |
| R1a-carga-continua-80 | PASS (0.434 <= 0.8) | PASS (0.651 <= 0.8) |
| R1b-carga-media-fase-80 | PASS (0.434 <= 0.8) | PASS (0.651 <= 0.8) |
| R2-disjuntor-85 | PASS (0.7 <= 0.85) | PASS (0.7 <= 0.85) |
| R3-autonomia-30min | FAIL (-1.01 >= 0.0) | FAIL (-8.985 >= 0.0) |

## Monte Carlo (cruzeiro, A)

| Modelo | Média | P95 | P99 | Pior caso determinístico |
| --- | --- | --- | --- | --- |
| Modelo A (familia C172, 28 V) | 18.4 | 25.3 | 30.3 | 30.3 |
| Modelo B (familia C172, alternador menor) | 18.4 | 25.3 | 30.3 | 30.3 |
