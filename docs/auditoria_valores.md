# Auditoria dos valores do caso de estudo

Gerado por `scripts/auditar_valores.py`: cada corrente do arquivo do caso é comparada com o texto extraído do documento-fonte.

Cobertura: correntes de carga (típica e máxima). Não são auditados por este script: capacidades de disjuntor, ciclos de trabalho, fases e premissas de operação; esses itens têm a fonte citada no próprio arquivo do caso.

## 172M 1976 (14 V): Service Manual 1969-76, 16-37/16-38, coluna 1976

Conferência: página renderizada e comparada visualmente (tabela digitalizada, texto desalinhado).

| Item | Arquivo do caso (A) | Fonte (A) | Situação |
| --- | --- | --- | --- |
| battery contactor | 0.6 | 0.6 | OK |
| fuel indicators | 0.4 | 0.4 | OK |
| flashing beacon | 7.0 | 7.0 | OK |
| instrument lights | 1.3 | 1.3 | OK |
| position lights | 5.6 | 5.6 | OK |
| turn coordinator | 0.8 | 0.8 | OK |
| flap position indicator | 0.1 | 0.1 | OK |
| strobe lights | 4.0 | 4.0 | OK |
| nav/com 1 RT-328T | 1.5 | 1.5 | OK |
| COM 1 legado TX | 6.0 | - | Não consta da tabela (premissa) |
| nav/com 2 RT-308C | 1.5 | 1.5 | OK |
| transponder RT-359A | 1.0 | 1.0 | OK |
| encoding altimeter EA-401A | 0.065 | 0.065 | OK |
| ADF R-546E | 1.0 | 1.0 | OK |
| glideslope R-443B | 0.4 | 0.4 | OK |
| marker beacon R-402A | 0.3 | 0.3 | OK |
| autopilot AF-295B | 2.0 | 2.0 | OK |
| flap motor | 15.0 | 15.0 | OK |
| landing and taxi light | 20.0 | 20.0 | OK |
| courtesy and dome lights | 2.5 | 2.5 | OK |
| map light | 0.33 | 0.33 | OK |

## 172R/S (28 V): Maintenance Manual 172RMM, 24-70-00, coluna 28 VDC (extração automática do texto)

| Item | Arquivo do caso (A) | Fonte 24 V / 28 V (A) | Situação |
| --- | --- | --- | --- |
| landing light 4596 | 8.93 | 7.65 / 8.93 | OK |
| taxi light 4587 | 8.93 | 7.65 / 8.93 | OK |
| navigation lights | 3.1 | 2.65 / 3.1 | OK |
| wing anti-collision lights | 1.7 | 1.98 / 1.7 | OK |
| beacon light | 1.25 | 1.07 / 1.25 | OK |
| under wing courtesy lights | 1.14 | 0.98 / 1.14 | OK |
| map light | 0.09 | 0.08 / 0.09 | OK |
| instrument lights (10 x 0.02) | 0.2 | 0,02 A por instrumento (quantidade assumida) | Premissa |
| pedestal light | 0.05 | 0.04 / 0.05 | OK |
| flap motor | 2.4 | 2.06 / 2.4 | OK |
| pitot heat | 3.89 | 3.33 / 3.89 | OK |
| hourmeter | 0.02 | 0.01 / 0.02 | OK |
| battery relay coil | 0.33 | 0.29 / 0.33 | OK |
| alternator relay coil | 0.33 | 0.29 / 0.33 | OK |
| alternator field and ACU | 1.9 | 1.63 / 1.9 | OK |
| ACU bus sense | 0.02 | 0.02 / 0.02 | OK |
| autopilot KAP 140 computer | 0.5 | 0.58 / 0.5 | OK |
| pitch servo and clutch | 0.5 | 0.58 / 0.5 | OK |
| pitch trim servo and clutch | 0.5 | 0.58 / 0.5 | OK |
| roll servo and clutch | 0.45 | 0.53 / 0.45 | OK |
| turn coordinator | 0.33 | 0.27 / 0.33 | OK |
| ADF KR 87 | 0.52 | 0.6 / 0.52 | OK |
| glareshield light fluorescent | 1.0 | 0.86 / 1.0 | OK |
| radio lights | 0.2 | 0.17 / 0.2 | OK |
| annunciator panel | 0.3 | 0.35 / 0.3 | OK |
| avionics fan | 0.5 | 0.43 / 0.5 | OK |
| engine and fuel gauges | 0.45 | 0.38 / 0.45 | OK |
| audio panel KMA 26 | 1.29 | 1.5 / 1.29 | OK |
| GPS KLN 94 | 1.2 | 1.4 / 1.2 | OK |
| transponder KT 76 | 0.7 | 0.6 / 0.7 | OK |
| altitude encoder SSD120 | 0.23 | 0.2 / 0.23 | OK |
| nav/com 1 KX 155A RX | 0.69 | 0.8 / 0.69 | OK |
| nav/com 1 KX 155A TX | 6.0 | 6.0 / 6.0 | OK |
| nav/com 2 KX 165A RX | 0.69 | 0.8 / 0.69 | OK |

## Instalação Garmin (extração automática do texto dos manuais)

| Item | Tensão | Típica / máxima no caso (A) | Típica / máxima na fonte (A) | Trecho da fonte encontrado | Situação |
| --- | --- | --- | --- | --- | --- |
| GTN 650 main + NAV | 14 V | 2.2 / 3.96 | 2.2 / 3.96 | sim | OK |
| GTN 650 main + NAV | 28 V | 1.1 / 2.08 | 1.1 / 2.08 | sim | OK |
| GTN 650 COM RX | 14 V | 0.45 / 0.45 | 0.45 / 0.45 | sim | OK |
| GTN 650 COM RX | 28 V | 0.21 / 0.21 | 0.21 / 0.21 | sim | OK |
| GTN 650 COM TX | 14 V | 4.02 / 4.02 | 4.02 / 4.02 | sim | OK |
| GTN 650 COM TX | 28 V | 1.76 / 1.76 | 1.76 / 1.76 | sim | OK |
| GMA 345 audio panel | 14 V | 0.83 / 1.19 | 0.83 / 1.19 | sim | OK |
| GMA 345 audio panel | 28 V | 0.43 / 0.9 | 0.43 / 0.9 | sim | OK |
| GTX 345 transponder ADS-B | 14 V | 0.72 / 1.3 | 0.72 / 1.3 | sim | OK |
| GTX 345 transponder ADS-B | 28 V | 0.36 / 0.65 | 0.36 / 0.65 | sim | OK |
| G5 indicador de atitude | 14 V | 0.2 / 0.25 | 0.2 / 0.25 | sim | OK |
| G5 indicador de atitude | 28 V | 0.1 / 0.125 | 0.1 / 0.125 | sim | OK |

**Divergências encontradas: 0**
