# PRD: Inventari i neteja de reports/queries de MODE Analytics per font de dades

## 1. Introducció / Overview

El compte de MODE Analytics ha acumulat **reports i queries que apunten a fonts de dades (data sources) que ja no existeixen o ja no s'utilitzen**. Això genera soroll i brutícia: reports que no es poden executar, queries que consulten bases de dades mortes i informes que ningú executa des de fa mesos.

Aquest projecte crea un **artefacte autònom (script)** que, mitjançant l'**API REST de MODE (Discovery API)**, fa una **"gran fotografia"** de tot el que hi ha al workspace **agrupat per font de dades**, i a més genera una llista separada de **reports obsolets segons l'antiguitat del seu últim run**.

L'objectiu d'aquesta primera versió és **purament informatiu (no destructiu)**: produir l'inventari que permetrà després anar netejant quirúrgicament. La sobre quins data sources i quins reports esborrar es prendrà manualment a partir d'aquests llistats.

## 2. Goals

1. Obtenir un **mapa complet** de quins reports i quines queries consumeixen cada font de dades del workspace.
2. Identificar fàcilment les fonts de dades "mortes" i tot el que en penja, per poder netejar després.
3. Saber **quant de temps fa que no s'executa** cada report, per detectar candidats a eliminar per desús.
4. Lliurar la informació en un format **simple i revisable a mà** (CSV/Markdown), sense esborrar res.
5. Que el procés sigui **reexecutable** quan calgui tornar a fer la foto.

## 3. User Stories

- **Com a** data analyst / owner del compte de MODE, **vull** una llista de tots els reports i queries agrupats per font de dades **per** veure d'un cop d'ull què penja de la base de dades morta i decidir què esborro.
- **Com a** responsable de neteja, **vull** saber quant fa que no s'executa cada report **per** prioritzar l'eliminació dels que ningú fa servir.
- **Com a** equip, **vull** poder tornar a generar aquesta foto quan vulgui **per** validar que la neteja avança i no reapareix soroll.

## 4. Functional Requirements

### Connexió i configuració
1. El sistema ha d'autenticar-se contra l'API REST de MODE mitjançant **HTTP Basic Auth** amb un **API token** (usuari) i **API secret** (contrasenya).
2. La configuració (workspace/organització, token, secret) s'ha de llegir de **variables d'entorn** (p. ex. `MODE_WORKSPACE`, `MODE_API_TOKEN`, `MODE_API_SECRET`), mai hardcodejada.
3. El sistema ha de gestionar la **paginació** de l'API (seguir els enllaços HAL `_links.next` fins esgotar resultats).
4. El sistema ha de respectar els **límits de rate** de l'API (backoff/reintents si rep 429).

### Recollida de dades
5. El sistema ha de llistar **totes les fonts de dades** del workspace (id, nom, token, tipus).
6. El sistema ha d'enumerar **tots els reports** del workspace, recorrent tots els espais/col·leccions (spaces) i l'espai personal.
7. Per cada report, el sistema ha d'obtenir les seves **queries** i, per cada query, el seu **`data_source_id`** i el text SQL (`raw_query`).
8. El sistema ha de **resoldre el `data_source_id` de cada query al nom de la font de dades** corresponent (creuant amb el llistat del requisit 5). Si l'id no existeix al llistat actual de fonts de dades, s'ha de marcar com **"font de dades morta / desconeguda"**.
9. Per cada report, el sistema ha d'obtenir la **data de l'últim run** (i, si està disponible, l'últim run reeixit) i calcular els **dies des de l'últim run**. Si un report no s'ha executat mai, s'ha de marcar explícitament com **"mai executat"**.

### Sortida 1 — Inventari per font de dades (la "gran fotografia")
10. El sistema ha de generar un fitxer (CSV) on cada fila representi una **combinació report + query**, amb com a mínim aquestes columnes:
    - `data_source_name`, `data_source_id`, `data_source_alive` (sí/no)
    - `report_name`, `report_token`, `report_url`
    - `space_name`
    - `query_name`
    - `last_run_at`, `days_since_last_run` (o "mai")
    - `owner`
    - `is_archived`
11. Les files s'han de poder **agrupar/ordenar per font de dades** perquè quedi clar tot el que penja de cada DB (incloses les mortes/desconegudes).

### Sortida 2 — Reports obsolets per antiguitat
12. El sistema ha de generar un **segon fitxer separat** (CSV) amb **un report per fila**, ordenat per `days_since_last_run` descendent, amb columnes: `report_name`, `report_token`, `report_url`, `space_name`, `owner`, `last_run_at`, `days_since_last_run`, `is_archived`.
13. Aquesta segona llista ha de cobrir **tots els reports**, independentment de la font de dades, per poder detectar desús pur.

### Resum
14. El sistema ha d'imprimir per consola (i opcionalment en un petit `summary.md`) un **resum**: nombre total de reports, queries, fonts de dades, quantes queries apunten a fonts mortes/desconegudes, i top-N reports més antics sense executar.

## 5. Non-Goals (Out of Scope)

- **No esborra ni arxiva** cap report, query ni font de dades. Aquesta versió és només lectura/informe.
- **No té interfície gràfica** ni dashboard; la sortida són fitxers CSV/Markdown.
- **No automatitza l'execució** (no cron, no scheduling) — es llança manualment.
- **No interpreta el SQL** per detectar taules concretes; només mapeja a nivell de font de dades.
- **No decideix** què és brossa: només presenta dades perquè la decisió sigui humana.
- No fa neteja "quirúrgica" automàtica — això és una fase posterior, fora d'aquest PRD.

## 6. Design Considerations

- Sortida pensada per obrir-se directament a Google Sheets/Excel (CSV amb capçaleres clares).
- Agrupació per font de dades destacant visualment (a `summary.md`) les fonts **mortes/desconegudes** i el recompte de reports afectats.
- Imatge de referència aportada per l'usuari: el panell de fonts de dades de MODE (QuestDB, App_FirebaseEvents, EF_Gecco, EF_PRIME, EF_postgresql, EF_postgresql_backup, ETENDO PRO Replica lectura, Fluctuo_datawarehouse, Invers_datawarehouse, Numintec_datawarehouse, SFSC_DataWarehouse, Snowflake, Web_LT_datawarehouse, ZEUS - PRO, Public Warehouse). Aquests són els noms que han d'aparèixer a la columna `data_source_name`.

## 7. Technical Considerations

- **API de MODE (Discovery API):** base `https://app.mode.com/api/{workspace}`. Auth Basic (token:secret), capçaleres `Accept: application/hal+json`.
  - Fonts de dades: `GET /api/{workspace}/data_sources`
  - Espais: `GET /api/{workspace}/spaces`; reports per espai: `GET /api/{workspace}/spaces/{space}/reports`
  - Queries d'un report: `GET /api/{workspace}/reports/{report}/queries` (cada query inclou `data_source_id` i `raw_query`)
  - Runs d'un report: `GET /api/{workspace}/reports/{report}/runs` (timestamps); el report pot exposar també un camp d'últim run.
  - *Els noms exactes dels camps (p. ex. `last_run_at` vs `last_successfully_run_at`) s'han de confirmar contra la resposta real de l'API durant la implementació.*
- **Requisit de pla:** l'accés complet a la Discovery API sol requerir pla **Business/Enterprise** de MODE. Cal confirmar que el compte hi té accés i generar un parell token/secret.
- **Volum/rendiment:** recórrer tots els reports + queries + runs pot implicar **molts requests**. L'usuari accepta començar així i replantejar si va massa lent (p. ex. paral·lelitzar, cachejar respostes en disc, o limitar a runs en comptes de report a report).
- **Llenguatge suggerit:** Python (requests) per simplicitat; sortida amb el mòdul `csv`. Sense dependències pesades.
- **Seguretat:** credencials només via variables d'entorn / `.env` no versionat; mai al repo.

## 8. Success Metrics

- L'script genera els **dos CSV** i el resum sense errors en una passada completa del workspace.
- L'inventari permet **identificar el 100% dels reports/queries** que apunten a fonts de dades mortes/desconegudes.
- L'equip pot, a partir dels llistats, **iniciar la neteja quirúrgica** i mesurar la reducció de reports/queries soroll en passades successives.

## 9. Open Questions

1. **Quin/s data source/s** són exactament els "morts" a prioritzar un cop tinguem la foto? (es decidirà amb l'inventari a la mà).
2. Confirmació que el compte de MODE té **pla i permisos** per usar la Discovery API i qui genera el token/secret.
3. **On es desen** els CSV de sortida (carpeta local del repo, Google Drive, etc.) i si cal versionar-los o no.
4. Llindar de "obsolet" per la Sortida 2 (p. ex. > 3, 6, 12 mesos) — o deixem només `days_since_last_run` perquè es filtri a mà?
5. Cal incloure també reports **arxivats** a l'inventari, o només els actius?
