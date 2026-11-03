# Aplicabilidade regulatória por modelo (rev2)

Responde ao item B da revisão externa. Objetivo: separar a base de certificação aprovada de cada modelo dos critérios de análise escolhidos no artigo.

## Fontes consultadas

| Fonte | Identificação | Uso |
| --- | --- | --- |
| EASA TCDS IM.A.051 | Issue 11, 17 nov. 2025 | Base de certificação por modelo (172M, 172R, 172S) |
| CAA NZ TAR 96/15 | Rev. 3, 28 set. 2018 | Base de certificação; cita FAA TCDS 3A12 Rev. 84 (29 jul. 2015) |
| FAA TCDS 3A12 | Rev. 84 (via TAR 96/15) | Documento de tipo de referência |
| 14 CFR 21.101(c) | eCFR | Aeronaves até 6.000 lb podem cumprir a base incorporada no TC |
| AC 21.101-1B | FAA, 2016 | Orientação sobre base de certificação de produto modificado |
| 14 CFR 23.1353(h), ed. 2013 | govinfo | Texto da exigência de 30/60 min (amdt 23-62) |

## Tabela por modelo

| Item | 172M 1976 (14 V) | 172R/S convencional (28 V) |
| --- | --- | --- |
| Base original | CAR 3, em vigor 15 maio 1956, emendas 3-1 a 3-12 | FAR 23, em vigor 1 fev. 1965, emendas 23-1 a 23-6, mais seções posteriores listadas no TCDS |
| Exigência de bateria de emergência com tempo mínimo na base original | Não | Não para a configuração convencional; o G1000 tem 23.1351/23.1353 na emenda 23-49 e o NXi cita CS 23.1353(h) |
| Base possível para a modificação | 21.101(c): a base do TC, salvo se a autoridade designar emenda posterior para mudança significativa na área | Idem |
| R3 (30 min) no artigo | Critério de referência (23.1353(h), emenda 23-62); não é requisito da base original | Idem |
| R1a, R1b, R2 | Critérios de prática aceitável (AC 43.13-1B; CASA AC 21-38; CASA AWB 24-007) | Idem |

## Consequências para o texto e o software

1. Toda saída diz "atende ao critério de análise selecionado" (PASS/FAIL/NOT EVALUATED); nenhuma saída declara conformidade com a base aprovada.
2. As regras em `data/rules.yaml` têm `kind: criterion`.
3. A margem negativa da linha de base 28 V em relação ao critério de 30 min não indica que o projeto de tipo certificado era não conforme: a exigência de 30 min não faz parte da base original desse modelo.
4. Para uma solicitação real, o requerente confirma com a autoridade (ou o DER/ODA) a base aplicável e se a autoridade designa emenda posterior na área afetada; o critério de 30 min continua relevante quando a modificação torna informação primária de voo dependente da energia elétrica.
