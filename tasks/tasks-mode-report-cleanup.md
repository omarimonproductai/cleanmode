## Relevant Files

- `mode_cleanup/__init__.py` - Marca el paquet Python de l'eina.
- `mode_cleanup/config.py` - Llegeix i valida la configuració des de variables d'entorn (`MODE_WORKSPACE`, `MODE_API_TOKEN`, `MODE_API_SECRET`).
- `mode_cleanup/client.py` - Client de l'API REST de MODE: auth Basic, paginació HAL, reintents/backoff per rate limits.
- `mode_cleanup/collect.py` - Recollida de dades: fonts de dades, espais, reports, queries i runs.
- `mode_cleanup/process.py` - Mapeig `data_source_id`→nom, marca de fonts mortes/desconegudes i càlcul de `days_since_last_run`.
- `mode_cleanup/outputs.py` - Generació dels CSV (inventari per font de dades, reports per antiguitat) i del `summary.md`.
- `mode_cleanup/main.py` - Punt d'entrada (CLI) que orquestra config → recollida → processament → sortides.
- `tests/test_config.py` - Tests de càrrega/validació de configuració.
- `tests/test_client.py` - Tests del client (paginació i backoff) amb respostes mockejades.
- `tests/test_process.py` - Tests del mapeig de fonts de dades i del càlcul d'antiguitat.
- `tests/test_outputs.py` - Tests del format i contingut dels CSV i el resum.
- `requirements.txt` - Dependències (p. ex. `requests`; `pytest` per tests).
- `.env.example` - Plantilla de variables d'entorn (sense valors reals).
- `.gitignore` - Ignora `.env` i secrets; **no** ignora la carpeta de sortides versionada.
- `output/` - Carpeta versionada on es desen els CSV i el `summary.md` generats.
- `README.md` - Instruccions d'ús de l'eina.

### Notes

- Tests amb `pytest`; col·loca'ls a `tests/` i executa'ls amb `pytest` (o `pytest tests/test_process.py` per un fitxer concret).
- Les crides reals a l'API es mockegen als tests (p. ex. amb `responses` o `unittest.mock`) per no dependre de credencials ni de la xarxa.
- Les credencials només viuen a variables d'entorn / `.env` (no versionat). Els CSV de sortida no han de contenir secrets.

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [ ] 0.0 Create feature branch
  - [ ] 0.1 El treball es desenvolupa a la branca designada `claude/festive-cori-w94f1m` (ja creada); confirmar que hi estem situats abans de començar.

- [ ] 1.0 Configuració del projecte i connexió autenticada a l'API de MODE
  - [ ] 1.1 Crear l'estructura del paquet `mode_cleanup/` i `requirements.txt` (afegir `requests` i `pytest`).
  - [ ] 1.2 Crear `.env.example` amb `MODE_WORKSPACE`, `MODE_API_TOKEN`, `MODE_API_SECRET` i `.gitignore` que ignori `.env`.
  - [ ] 1.3 Implementar `config.py`: llegir les variables d'entorn i fallar amb missatge clar si en falta alguna.
  - [ ] 1.4 Implementar `client.py` amb auth HTTP Basic (token:secret) i capçalera `Accept: application/hal+json`.
  - [ ] 1.5 Afegir al client la gestió de **paginació HAL** (seguir `_links.next` fins esgotar resultats).
  - [ ] 1.6 Afegir al client **reintents amb backoff** davant respostes 429 / errors transitoris.
  - [ ] 1.7 Test de fum: una crida autenticada a `/api/{workspace}/data_sources` retorna 200 i llista fonts.

- [ ] 2.0 Recollida de dades: fonts de dades, reports, queries i runs
  - [ ] 2.1 `collect.py`: obtenir **totes les fonts de dades** (id, nom, token, tipus).
  - [ ] 2.2 Obtenir **tots els espais** (`/spaces`) i enumerar-ne tots els **reports**, incloent l'espai personal.
  - [ ] 2.3 Incloure també els reports **arxivats** a l'enumeració.
  - [ ] 2.4 Per cada report, obtenir les seves **queries** amb `data_source_id` i `raw_query`.
  - [ ] 2.5 Per cada report, obtenir la data de l'**últim run** (i últim run reeixit si està disponible) via `/runs` o el camp del report.
  - [ ] 2.6 Confirmar els noms exactes dels camps de l'API (p. ex. `last_run_at` vs `last_successfully_run_at`) contra una resposta real i ajustar el codi.

- [ ] 3.0 Processament: mapeig query→font de dades i càlcul d'antiguitat de l'últim run
  - [ ] 3.1 `process.py`: construir un índex `data_source_id` → nom de font de dades a partir de 2.1.
  - [ ] 3.2 Per cada query, resoldre el nom de la font de dades; si l'id no existeix al llistat actual, marcar-la com **"morta/desconeguda"** (`data_source_alive = no`).
  - [ ] 3.3 Calcular `days_since_last_run` per cada report; si no s'ha executat mai, marcar **"mai"**.
  - [ ] 3.4 Construir les estructures de dades per a les dues sortides (files report+query i files report).

- [ ] 4.0 Generació de sortides (Inventari per font de dades, Reports per antiguitat i resum)
  - [ ] 4.1 `outputs.py`: generar **Sortida 1** CSV (una fila per report+query) amb les columnes del PRD, ordenada/agrupada per font de dades.
  - [ ] 4.2 Generar **Sortida 2** CSV (un report per fila) ordenada per `days_since_last_run` descendent, cobrint tots els reports.
  - [ ] 4.3 Generar `summary.md` amb els recomptes globals i top-N reports més antics sense executar.
  - [ ] 4.4 Garantir que cap sortida conté credencials ni secrets.
  - [ ] 4.5 `main.py`: orquestrar config → recollida → processament → sortides i desar els fitxers a `output/`.

- [ ] 5.0 Documentació, versionat de sortides i validació final
  - [ ] 5.1 Escriure `README.md` amb requisits, configuració de variables d'entorn i com executar l'eina.
  - [ ] 5.2 Escriure tests bàsics (`tests/`) amb crides a l'API mockejades i executar `pytest` en verd.
  - [ ] 5.3 Fer una execució real contra el workspace i validar els dos CSV + el resum.
  - [ ] 5.4 Versionar la carpeta `output/` amb la primera "fotografia" generada.
  - [ ] 5.5 Commit i push de tot el treball a la branca designada.
