# Llista de neteja accionable — MODE

> Generat a partir de 574 reports / 41 col·leccions accessibles. **No destructiu**: són candidats a revisar, no s'ha esborrat res.

## 1. Fonts de dades sense cap ús (candidates a eliminar a MODE)

Cap report/query de tot l'escaneig les utilitza:

- **Numintec_datawarehouse**
- **SFSC_DataWarehouse**
- **Web_LT_datawarehouse**

> Nota: "sense ús" es refereix a les 41 col·leccions accessibles. Les col·leccions Personal bloquejades (403) no s'han pogut mirar.

## 2. Reports només "from definition" (12) — orfes/trencats probables

Totes les seves queries són "from definition" (cap font de dades real):

| Report | Col·lecció | Dies sense run | URL |
| --- | --- | --- | --- |
| OB-BACKUP Definitions | + ORIOL - OB investigacions | 2149 | https://app.mode.com/editor/ecooltra706/reports/5cdc5f386ca1 |
| OB-Estudi de taules a nivell quantitats de registres - privat | + ORIOL - OB investigacions | 2120 | https://app.mode.com/editor/ecooltra706/reports/9e2a797503a9 |
| 24h Online Bookings tracking | ++ aSlack reports | 2058 | https://app.mode.com/editor/ecooltra706/reports/ed2dacdf3196 |
| [OB] Contratos activos LT | Data Science | 1948 | https://app.mode.com/editor/ecooltra706/reports/d8b1e99135b0 |
| OB_B2CLT_activos | Data Science | 1907 | https://app.mode.com/editor/ecooltra706/reports/fa6832663951 |
| Clone of Monthly P&L per Business Line (Ebidta before HQ) | Personal | 1895 | https://app.mode.com/editor/ecooltra706/reports/b493e5e705af |
| B2C Revenue by categories | Personal | 1699 | https://app.mode.com/editor/ecooltra706/reports/abdd68fd790d |
| Portugal ST and LT revenues | ++ City Managers | 1317 | https://app.mode.com/editor/ecooltra706/reports/2e481914888f |
| [ZEUS] Work shifts | Backup Lluís | 1308 | https://app.mode.com/editor/ecooltra706/reports/e76e7adcd105 |
| Clone of Contratos y reservas | Backup Lluís | 1305 | https://app.mode.com/editor/ecooltra706/reports/6f65ece8bb4b |
| Current location of bikes | Backup Lluís | 1299 | https://app.mode.com/editor/ecooltra706/reports/ef8de8d3e701 |
| TES_IAG | Personal | 1263 | https://app.mode.com/editor/ecooltra706/reports/3be905b243cc |

## 3. Reports sense cap query (6)

| Report | Col·lecció | Dies sense run | URL |
| --- | --- | --- | --- |
| [DBT] SEMANTIC LAYER INTEGRATION | Personal | 1178 | https://app.mode.com/editor/ecooltra706/reports/ee63a7874224 |
| [TEST] METRICS SEMANTIC LAYER | Personal | 1177 | https://app.mode.com/editor/ecooltra706/reports/a7ad52fd9cf6 |
| [B2C-ST] ANALYSIS-Online bookings-Calendar units x category | [B2C-ST] ST reporting | 676 | https://app.mode.com/editor/ecooltra706/reports/70cd48ae73fd |
| [B2C-ST] ANALYSIS-Online bookings-When are being created? | [B2C-ST] ST reporting | 425 | https://app.mode.com/editor/ecooltra706/reports/579587b221d5 |
|  | Personal | 158 | https://app.mode.com/editor/ecooltra706/reports/7fef71047fe3 |
| [B2C-ST] DAILY-Online bookings-Units per model and day | [B2C-ST] ST reporting | 79 | https://app.mode.com/editor/ecooltra706/reports/348740640b07 |

## 4. Reports que usen EF_postgresql_backup (5)

| Report | Col·lecció | Puresa | Dies | URL |
| --- | --- | --- | --- | --- |
| LISBOA30 - Control Report | ++ CS team | pure | 1802 | https://app.mode.com/editor/ecooltra706/reports/ac5cf03781b8 |
| Location of fined rentals | ++ City Managers | pure | 1213 | https://app.mode.com/editor/ecooltra706/reports/5a6ed83d3288 |
| Cooltra Club analysis | DATA | pure | 1206 | https://app.mode.com/editor/ecooltra706/reports/d4aa3b158e0b |
| [OFFICIAL ECOOLTRA] MONTHLY KPIS FOR COOLTRA GROUP REPORTING | ++ City Managers | pure | 1140 | https://app.mode.com/editor/ecooltra706/reports/fb3f9451fa4d |
| Automatic sync (monthly subscription) | IT | mixed | 522 | https://app.mode.com/editor/ecooltra706/reports/64b5665229ef |

## 5. Reports antics (>2 anys sense executar) (282)

Llista completa a cleanup_candidates.csv (motiu antic_+2anys). Top 25 més antics:

| Report | Col·lecció | Dies | Fonts | URL |
| --- | --- | --- | --- | --- |
| [ORIOL] Control Credits | 1-Coses meves | 2551 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/804ca56d1b98 |
| Locations KPIs | DATA | 2511 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/30aa664d4f25 |
| Finance monthly export per city | 2-ORIOL Procés tancament mensual | 2510 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/0707b6e50b12 |
| ABCDE Final Analysis by Oriol | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/ade910d659d6 |
| Monthly ABC(DE) (No rental filter, excluding refunds) | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/d79a2b10bfb1 |
| Monthly ABC(DE) (Rentals prefiltered, excluding refunds) | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/5d60163d8892 |
| Monthly ABC(DE)_ Milan | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/276c4553c7d1 |
| Monthly ABC(DE)_ Lisbon | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/d4f87bd37f7b |
| Monthly ABC(DE)_ Rome | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/9eb3e72b3e82 |
| Monthly ABC(DE)_ Madrid | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/7a861b5d2e85 |
| Monthly ABC(DE)_ Barcelona | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/f40c5c672c36 |
| Monthly ABC(DE)_ Valencia | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/03e6072b0e1a |
| Lifetime ABC(DE) | eCooltra ABC(DE) Analysis | 2488 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/6db8e1a5f57d |
| Charges with 0% VAT | Exports | 2480 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/f0d398954e3a |
| PACK Campaign - Total per Pack | ++ aSlack reports | 2467 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/b56b002ccfae |
| _NOW_ promocode report (copy) | DATA | 2424 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/ade45a770a6a |
| Lisbon: Data for Insurance Purposes | ++ City Managers | 2396 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/e0dbe8064697 |
| Lisbon rentals matrix of zip codes | ++ City Managers | 2385 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/299919d56258 |
| Monthly progress of Unique Riders | Deprecated reports | 2379 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/640e5db3a5a7 |
| Lisbon users per age range and gender | ++ City Managers | 2322 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/7b93702f79f1 |
| Swapping KPIs | DATA | 2319 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/5a9f5808f86c |
| MONTHLY CSV EXPORT FOR RONAN | 2-ORIOL Procés tancament mensual | 2318 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/a4b15b27846a |
| Workshop KPIs | DATA | 2314 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/627d9bf3ba80 |
| Monthly Retention for dormants | Cohorts | 2313 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/aa3e9899eb30 |
| Main KPIs | DATA | 2294 | EF_postgresql | https://app.mode.com/editor/ecooltra706/reports/d5aa02326edd |

