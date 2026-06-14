"""Punt d'entrada: config -> recollida -> processament -> sortides."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import ModeAPIError, ModeClient
from .collect import collect_all
from .config import ConfigError, load_config
from .outputs import write_data_sources, write_outputs
from .process import process, process_data_sources


def _probe(client: ModeClient, path: str) -> dict:
    """Prova un GET i retorna ok/status/recompte de reports, sense petar."""
    try:
        payload = client.get(path)
    except ModeAPIError as exc:
        return {"path": path, "ok": False, "status": exc.status_code}
    reports = payload.get("_embedded", {}).get("reports", [])
    return {"path": path, "ok": True, "reports_count": len(reports)}


def _safe_dump(client: ModeClient, path: str, out_path: Path) -> tuple[dict | None, Any]:
    """GET defensiu: bolca el JSON a disc si va bé; mai peta."""
    try:
        payload = client.get(path)
    except ModeAPIError as exc:
        return None, exc.status_code
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return payload, None


def _debug_dump(client: ModeClient, output_dir: str) -> None:
    """Bolca l'estructura crua de /spaces i /data_sources i prova rutes de
    reports. Cada secció és independent: un error no atura la resta."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    probe: dict = {}

    # --- Espais / col·leccions ---
    spaces_payload, sp_err = _safe_dump(
        client, "spaces", out / "_debug_spaces.json"
    )
    if spaces_payload is not None:
        spaces = spaces_payload.get("_embedded", {}).get("spaces", [])
        probe["space_count"] = len(spaces)
        if spaces:
            sp = spaces[0]
            token = sp.get("token")
            probe["first_space_links"] = sp.get("_links", {})
            candidates = []
            reports_link = sp.get("_links", {}).get("reports", {}).get("href")
            if reports_link:
                candidates.append(reports_link)
            if token:
                candidates.append(f"collections/{token}/reports")
                candidates.append(f"spaces/{token}/reports")
            probe["report_path_probes"] = [_probe(client, p) for p in candidates]
    else:
        probe["spaces_error_status"] = sp_err

    # --- Pla B: fonts de dades (que SÍ veiem) i els seus enllaços ---
    ds_payload, ds_err = _safe_dump(
        client, "data_sources", out / "_debug_data_sources.json"
    )
    if ds_payload is not None:
        ds_list = ds_payload.get("_embedded", {}).get("data_sources", [])
        probe["data_source_count"] = len(ds_list)
        if ds_list:
            probe["first_data_source_links"] = ds_list[0].get("_links", {})
    else:
        probe["data_sources_error_status"] = ds_err

    # --- Batch API (app.mode.com/batch/...): pot saltar-se els permisos de
    #     col·leccions. Provem reports i queries i registrem què retorna. ---
    ws = client._config.workspace  # noqa: SLF001 (diagnòstic)
    batch_urls = [
        f"https://app.mode.com/batch/{ws}/reports",
        f"https://app.mode.com/batch/{ws}/reports/",
        f"https://app.mode.com/batch/{ws}/reports?format=json",
        f"https://app.mode.com/batch/{ws}/queries",
    ]
    batch_probes = []
    for url in batch_urls:
        try:
            # Primer sense seguir redirects, per veure si n'hi ha.
            no_redir = client.raw_get(url, allow_redirects=False)
            resp = client.raw_get(url)
        except Exception as exc:  # noqa: BLE001 - diagnòstic, no ha de petar
            batch_probes.append({"url": url, "error": str(exc)})
            continue
        body = resp.text or ""
        entry = {
            "url": url,
            "status_no_redirect": no_redir.status_code,
            "redirect_location": no_redir.headers.get("Location", ""),
            "status": resp.status_code,
            "final_url": resp.url,
            "redirect_chain": [r.status_code for r in resp.history],
            "content_type": resp.headers.get("Content-Type", ""),
            "length": len(body),
            "snippet": body[:600],
        }
        batch_probes.append(entry)
        if resp.status_code == 200 and "reports" in url:
            (out / "_debug_batch_reports.txt").write_text(
                body[:200000], encoding="utf-8"
            )
    probe["batch_probes"] = batch_probes

    (out / "_debug_probe.json").write_text(
        json.dumps(probe, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Debug: proves escrites a {out / '_debug_probe.json'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventari de reports/queries de MODE per font de dades."
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Carpeta on desar els CSV i el resum (per defecte: output/).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Nombre de reports més antics a mostrar al resum.",
    )
    parser.add_argument(
        "--debug-dump",
        action="store_true",
        help="Bolca l'estructura crua de /spaces a output/ i surt (diagnòstic).",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Error de configuració: {exc}", file=sys.stderr)
        return 2

    client = ModeClient(config)

    if args.debug_dump:
        _debug_dump(client, args.output_dir)
        return 0

    print(f"Recollint dades del workspace '{config.workspace}'...")
    collected = collect_all(client)
    print(
        f"  {len(collected.data_sources)} fonts de dades, "
        f"{len(collected.reports)} reports."
    )

    # Inventari de fonts de dades: sempre es genera.
    ds_rows = process_data_sources(collected.data_sources)
    ds_path = write_data_sources(ds_rows, args.output_dir)
    print(f"Inventari de fonts de dades: {ds_path}")

    # Inventari per report/query: només si el token hi té accés.
    if collected.reports:
        inventory, reports = process(collected)
        paths = write_outputs(
            inventory, reports, args.output_dir, top_n=args.top_n
        )
        dead = sum(1 for r in inventory if r.data_source_alive == "no")
        print("Sortides de reports generades:")
        for name, path in paths.items():
            print(f"  - {name}: {path}")
        print(f"Queries cap a fonts mortes/desconegudes: {dead}")
    else:
        print(
            "Avís: 0 reports accessibles amb aquest token (permisos de "
            "col·leccions). Generat només l'inventari de fonts de dades.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
