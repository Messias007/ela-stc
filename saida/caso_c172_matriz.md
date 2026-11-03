# Matriz multimodelo: GTN 650 + GMA 345 + GTX 345 + G5 (substitui nav/com 1, audio, transponder e encoder)

PASS = atende ao critério de análise selecionado; não equivale a conformidade com a base de certificação aprovada.
Opções: corrente típica, TX 0.1, corte em 5.0 min.

| Regra | Cessna 172M 1976 (14 V) | Cessna 172R/S convencional (28 V) |
| --- | --- | --- |
| R1a-carga-continua-80 | PASS (0.478 <= 0.8) | PASS (0.303 <= 0.8) |
| R1b-carga-media-fase-80 | FAIL (0.823 <= 0.8) | PASS (0.407 <= 0.8) |
| R2-disjuntor-85 | PASS (0.528 <= 0.85) | PASS (0.416 <= 0.85) |
| R3-autonomia-30min | PASS (19.114 >= 0.0) | PASS (0.797 >= 0.0) |

## Monte Carlo (cruzeiro, A)

| Modelo | Média | P95 | P99 | Pior caso determinístico |
| --- | --- | --- | --- | --- |
| Cessna 172M 1976 (14 V) | 29.1 | 32.3 | 32.6 | 32.6 |
| Cessna 172R/S convencional (28 V) | 18.4 | 21.0 | 22.6 | 22.6 |
