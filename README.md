# MODE inventory & cleanup

Eina d'inventari de **reports i queries de MODE Analytics agrupats per font de dades**, pensada per detectar i netejar reports/queries que apunten a bases de dades mortes o que ja no s'executen.

És **només lectura**: no esborra ni arxiva res. Genera fitxers perquè la decisió de neteja sigui humana.

Veure el detall a [`tasks/prd-mode-report-cleanup.md`](tasks/prd-mode-report-cleanup.md).

## Què genera

Dins de `output/`:

- **`inventory_by_data_source.csv`** — una fila per cada combinació report + query, agrupada per font de dades. Marca les fonts **mortes/desconegudes** (`data_source_alive = no`).
- **`reports_by_staleness.csv`** — un report per fila, ordenat per `days_since_last_run` (els mai executats primer).
- **`summary.md`** — recomptes globals i top-N reports més antics.

## Configuració

Credencials de la Discovery API de MODE (Settings → API Tokens). Variables d'entorn:

| Variable | Descripció |
| --- | --- |
| `MODE_WORKSPACE` | Nom del workspace (a la URL `app.mode.com/<workspace>/...`). |
| `MODE_API_TOKEN` | Token de l'API (usuari del Basic Auth). |
| `MODE_API_SECRET` | Secret de l'API. També s'accepta com a `MODE_SECRET`. |

Copia `.env.example` a `.env` i omple els valors. **Mai versionis `.env`.**

## Ús local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m mode_cleanup.main --output-dir output
```

Opcions: `--output-dir` (per defecte `output/`), `--top-n` (mida del top al resum).

## Ús via GitHub Actions

Hi ha un workflow manual a `.github/workflows/mode-inventory.yml`:

1. Configura els secrets del repo `MODE_API_TOKEN` i `MODE_SECRET` (Settings → Secrets → Actions).
2. Llança el workflow **MODE inventory** (Actions → Run workflow) indicant el workspace.
3. El workflow executa l'eina i **committeja `output/`** de tornada a la branca.

## Tests

```bash
pip install -r requirements.txt
pytest
```

Les crides a l'API es mockegen; no calen credencials per als tests.
