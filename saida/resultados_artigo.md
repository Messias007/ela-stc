# Resultados do artigo (gerado por scripts/resultados_artigo.py a partir de data/caso_c172.yaml)

Parâmetros base: use_typical=1, tx_duty=0.1, landing_light_duty=1.0, soh=None, soc=None, temp_factor=None, peukert_n=None, casa_fraction=0.72, preshed_min=5.0, approach_min=5.0, approach_flap_duty=0.1, cp_scaling=1, pitot_em=1, bat_capacity_factor=1.0

## Cessna 172M 1976 (14 V)

- Bateria: C1=22.0 Ah, SOH=0.8, SOC=0.9, kT=1.0, n=1.2
- R1a contínua antes→depois (típica): 44.5% → 47.8%; máxima depois 52.3%; fase cruise
- R1b média antes→depois (típica): 79.4% → 82.3%; máxima antes/depois 79.4%/86.8%; fase landing
- R2 disjuntor: 52.8% no circuito 'GTN 650 main + NAV', 5 circuitos avaliados, não avaliados: nenhum
- Emergência antes: I_pre=28.666 I_shed=12.617 I_app=33.817 A; E_CASA=60.56 E_P=59.12 min; M=+29.12 min; perfil CASA viável=True
- Emergência depois: I_pre=30.699 I_shed=14.650 I_app=35.850 A; E_CASA=52.16 E_P=49.11 min; M=+19.11 min; perfil CASA viável=True
- Emergência depois, máxima: I_pre=33.907 I_shed=17.858 I_app=39.058 A; E_CASA=42.79 E_P=38.38 min; M=+8.38 min; perfil CASA viável=True
- Emergência antes, máxima: I_pre=28.666 I_shed=12.617 I_app=33.817 A; E_CASA=60.56 E_P=59.12 min; M=+29.12 min; perfil CASA viável=True
- Variação líquida Garmin: +4.400 − 2.565 = +1.835 A
- Exemplo CASA depois: Q=60×22.0000×0.72=950.40 A·min; pré=153.49 (2C1=44.00 A); reserva=179.25; cruzeiro em corte=(950.40−153.49−179.25)/14.650=42.16 min
- Limiar do farol para R1b > 80%: típica 0.932, máxima 0.795
- SOH com M=0 (kT=1.0, SOC=0.9): 0.601
- SOH com M=0 (kT=1.0, SOC=1.0): 0.541
- SOH com M=0 (kT=0.7, SOC=0.9): 0.859
- SOH com M=0 (kT=0.7, SOC=1.0): 0.773

| Parâmetro (grupo) | baixo | base | alto | M baixo | M base | M alto | R1b baixo | R1b alto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| use_typical (method) | 0 | 1 | 1 | +8.38 | +19.11 | +19.11 | 86.8% | 82.3% |
| casa_fraction (method) | 0.72 | 0.72 | 0.75 | +19.11 | +19.11 | +19.11 | 82.3% | 82.3% |
| preshed_min (method) | 10 | 5 | 5 | +11.97 | +19.11 | +19.11 | 82.3% | 82.3% |
| pitot_em (method) | 1 | 1 | 0 | +19.11 | +19.11 | +19.11 | 82.3% | 82.3% |
| cp_scaling (method) | 1 | 1 | 0 | +19.11 | +19.11 | +23.01 | 82.3% | 82.3% |
| bat_capacity_factor (method) | 1 | 1 | 1.14 | +19.11 | +19.11 | +30.04 | 82.3% | 82.3% |
| tx_duty (physical) | 0.05 | 0.1 | 0.2 | +20.00 | +19.11 | +17.43 | 82.0% | 82.9% |
| landing_light_duty (physical) | 0.3 | 1 | 1 | +19.11 | +19.11 | +19.11 | 58.9% | 82.3% |
| soh (physical) | 0.8 | 0.8 | 1 | +19.11 | +19.11 | +22.16 | 82.3% | 82.3% |
| soc (physical) | 0.8 | 0.9 | 1 | +10.43 | +19.11 | +22.16 | 82.3% | 82.3% |
| temp_factor (physical) | 0.7 | 1 | 1 | -3.83 | +19.11 | +19.11 | 82.3% | 82.3% |
| peukert_n (physical) | 1.3 | 1.2 | 1.1 | +17.33 | +19.11 | +20.72 | 82.3% | 82.3% |

- MC físico em serviço (SOH 0,8-1,0) N=5000 seed=7: R1a p5-p95 47.7%-47.8%; R1b p5-p95 60.2%-81.3%; fração R1b>80% 11.5% (EP 0.5%); M p5/média/p95 -0.1/+13.7/+22.5; fração M<0 5.2% (EP 0.3%)
  - correlações M: Fator de temperatura da capacidade +0.72; Estado de carga na perda do alternador (SOC) +0.45; Estado de saúde da bateria (SOH) +0.42; Expoente de Peukert -0.12; Ciclo de transmissão COM -0.06; Farol ligado na decolagem e no pouso (fração da fase) +0.00
  - correlações R1b: Farol ligado na decolagem e no pouso (fração da fase) +1.00; Ciclo de transmissão COM +0.06; Expoente de Peukert -0.03; Estado de saúde da bateria (SOH) +0.01; Estado de carga na perda do alternador (SOC) -0.01; Fator de temperatura da capacidade -0.01
- MC físico degradado (SOH 0,6-0,8) N=5000 seed=7: R1a p5-p95 47.7%-47.8%; R1b p5-p95 60.2%-81.3%; fração R1b>80% 11.5% (EP 0.5%); M p5/média/p95 -13.3/-0.6/+14.1; fração M<0 55.0% (EP 0.7%)
  - correlações M: Fator de temperatura da capacidade +0.67; Estado de saúde da bateria (SOH) +0.54; Estado de carga na perda do alternador (SOC) +0.44; Expoente de Peukert -0.21; Ciclo de transmissão COM -0.04; Farol ligado na decolagem e no pouso (fração da fase) +0.00
  - correlações R1b: Farol ligado na decolagem e no pouso (fração da fase) +1.00; Ciclo de transmissão COM +0.06; Expoente de Peukert -0.03; Estado de saúde da bateria (SOH) +0.01; Estado de carga na perda do alternador (SOC) -0.01; Fator de temperatura da capacidade -0.01
- Todas as cargas ligadas na corrente máxima, pouso: antes 109.0%, depois 115.1%
- Emergência simplificada (correntes no barramento, sem aproximação, sem pitot, só CASA 75%): E=65.92, M=+35.92 min; superestima M em 16.81 min
  - efeito isolado pitot_em=0: ΔM=+0.00 min
  - efeito isolado approach_min=0.0: ΔM=+9.63 min
  - efeito isolado cp_scaling=0: ΔM=+3.89 min
  - efeito isolado casa_fraction=0.75: ΔM=+0.00 min
- MC de fase cruise (N=10000, típica, depois): média 29.14 (esperado 29.16); p95 32.27; p99 32.60 (54.3%); pior caso 32.60 (54.3%); média 48.6%
- MC de fase landing (N=10000, típica, depois): média 49.32 (esperado 49.36); p95 62.40; p99 62.73 (104.5%); pior caso 66.30 (110.5%); média 82.2%

## Cessna 172R/S convencional (28 V)

- Bateria: C1=10.8375 Ah, SOH=0.8, SOC=0.9, kT=1.0, n=1.2
- R1a contínua antes→depois (típica): 33.4% → 30.3%; máxima depois 33.3%; fase cruise
- R1b média antes→depois (típica): 44.5% → 40.7%; máxima antes/depois 44.5%/43.7%; fase landing
- R2 disjuntor: 41.6% no circuito 'GTN 650 main + NAV', 5 circuitos avaliados, não avaliados: nenhum
- Emergência antes: I_pre=20.353 I_shed=11.991 I_app=19.806 A; E_CASA=32.30 E_P=27.26 min; M=-2.74 min; perfil CASA viável=True
- Emergência depois: I_pre=18.081 I_shed=11.119 I_app=18.934 A; E_CASA=35.46 E_P=30.80 min; M=+0.80 min; perfil CASA viável=True
- Emergência depois, máxima: I_pre=20.140 I_shed=13.178 I_app=20.993 A; E_CASA=29.92 E_P=24.93 min; M=-5.07 min; perfil CASA viável=True
- Emergência antes, máxima: I_pre=20.353 I_shed=11.991 I_app=19.806 A; E_CASA=32.30 E_P=27.26 min; M=-2.74 min; perfil CASA viável=True
- Variação líquida Garmin: +2.200 − 4.110 = -1.910 A
- Exemplo CASA depois: Q=60×10.8375×0.72=468.18 A·min; pré=90.40 (2C1=21.68 A); reserva=94.67; cruzeiro em corte=(468.18−90.40−94.67)/11.119=25.46 min
- Limiar do farol para R1b > 80%: típica None, máxima None
- SOH com M=0 (kT=1.0, SOC=0.9): 0.786
- SOH com M=0 (kT=1.0, SOC=1.0): 0.708
- SOH com M=0 (kT=0.7, SOC=0.9): None
- SOH com M=0 (kT=0.7, SOC=1.0): None

| Parâmetro (grupo) | baixo | base | alto | M baixo | M base | M alto | R1b baixo | R1b alto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| use_typical (method) | 0 | 1 | 1 | -5.07 | +0.80 | +0.80 | 43.7% | 40.7% |
| casa_fraction (method) | 0.72 | 0.72 | 0.75 | +0.80 | +0.80 | +0.80 | 40.7% | 40.7% |
| preshed_min (method) | 10 | 5 | 5 | -3.16 | +0.80 | +0.80 | 40.7% | 40.7% |
| pitot_em (method) | 1 | 1 | 0 | +0.80 | +0.80 | +14.89 | 40.7% | 40.7% |
| cp_scaling (method) | 1 | 1 | 0 | +0.80 | +0.80 | -2.41 | 40.7% | 40.7% |
| bat_capacity_factor (method) | 1 | 1 | 1.14 | +0.80 | +0.80 | +0.80 | 40.7% | 40.7% |
| tx_duty (physical) | 0.05 | 0.1 | 0.2 | +1.11 | +0.80 | +0.19 | 40.6% | 41.0% |
| landing_light_duty (physical) | 0.3 | 1 | 1 | +0.80 | +0.80 | +0.80 | 36.6% | 40.7% |
| soh (physical) | 0.8 | 0.8 | 1 | +0.80 | +0.80 | +5.46 | 40.7% | 40.7% |
| soc (physical) | 0.8 | 0.9 | 1 | -4.37 | +0.80 | +5.46 | 40.7% | 40.7% |
| temp_factor (physical) | 0.7 | 1 | 1 | -12.86 | +0.80 | +0.80 | 40.7% | 40.7% |
| peukert_n (physical) | 1.3 | 1.2 | 1.1 | -1.53 | +0.80 | +3.13 | 40.7% | 40.7% |

- MC físico em serviço (SOH 0,8-1,0) N=5000 seed=7: R1a p5-p95 30.3%-30.3%; R1b p5-p95 36.5%-40.3%; fração R1b>80% 0.0% (EP 0.0%); M p5/média/p95 -10.8/-1.8/+5.5; fração M<0 59.4% (EP 0.7%)
  - correlações M: Fator de temperatura da capacidade +0.72; Estado de carga na perda do alternador (SOC) +0.45; Estado de saúde da bateria (SOH) +0.43; Expoente de Peukert -0.22; Ciclo de transmissão COM -0.03; Farol ligado na decolagem e no pouso (fração da fase) +0.00
  - correlações R1b: Farol ligado na decolagem e no pouso (fração da fase) +0.83; Ciclo de transmissão COM +0.12; Expoente de Peukert -0.03; Estado de saúde da bateria (SOH) +0.02; Fator de temperatura da capacidade -0.01; Estado de carga na perda do alternador (SOC) +0.00
- MC físico degradado (SOH 0,6-0,8) N=5000 seed=7: R1a p5-p95 30.3%-30.3%; R1b p5-p95 36.5%-40.3%; fração R1b>80% 0.0% (EP 0.0%); M p5/média/p95 -18.6/-10.9/-1.9; fração M<0 97.9% (EP 0.2%)
  - correlações M: Fator de temperatura da capacidade +0.66; Estado de saúde da bateria (SOH) +0.53; Estado de carga na perda do alternador (SOC) +0.43; Expoente de Peukert -0.30; Ciclo de transmissão COM -0.02; Farol ligado na decolagem e no pouso (fração da fase) +0.01
  - correlações R1b: Farol ligado na decolagem e no pouso (fração da fase) +0.83; Ciclo de transmissão COM +0.12; Expoente de Peukert -0.03; Estado de saúde da bateria (SOH) +0.02; Fator de temperatura da capacidade -0.01; Estado de carga na perda do alternador (SOC) +0.00
- Todas as cargas ligadas na corrente máxima, pouso: antes 56.2%, depois 49.7%
- Emergência simplificada (correntes no barramento, sem aproximação, sem pitot, só CASA 75%): E=53.78, M=+23.78 min; superestima M em 22.98 min
  - efeito isolado pitot_em=0: ΔM=+14.09 min
  - efeito isolado approach_min=0.0: ΔM=+4.47 min
  - efeito isolado cp_scaling=0: ΔM=-3.21 min
  - efeito isolado casa_fraction=0.75: ΔM=+0.00 min
- MC de fase cruise (N=10000, típica, depois): média 18.40 (esperado 18.39); p95 21.02; p99 22.57 (37.6%); pior caso 22.57 (37.6%); média 30.7%
- MC de fase landing (N=10000, típica, depois): média 24.45 (esperado 24.44); p95 26.42; p99 26.51 (44.2%); pior caso 28.06 (46.8%); média 40.7%
