"""Punt d'entrada: config -> recollida -> processament -> sortides."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import ModeAPIError, ModeClient
from .collect import collect_all
from .config import ConfigError, load_config
from .outputs import write_outputs
from .process import process


def _probe(client: ModeClient, path: str) -> dict:
    """Prova un GET i retorna ok/status/recompte de reports, sense petar."""
    try:
        payload = client.get(path)
    except ModeAPIError as exc:
        return {"path": path, "ok": False, "status": exc.status_code}
    reports = payload.get("_embedded", {}).get("reports", [])
    return {"path": path, "ok": True, "reports_count": len(reports)}


def _debug_dump(client: ModeClient, output_dir: str) -> None:
    """Bolca l'estructura crua de /spaces i prova diverses rutes de reports
    per descobrir quina funciona. No peta mai."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    spaces_payload = client.get("spaces?filter=all")
    (out / "_debug_spaces.json").write_text(
        json.dumps(spaces_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Pla B: bolca també l'estructura de les fonts de dades (que SÍ veiem) per
    # veure si exposen enllaços cap a les seves queries/reports.
    ds_payload = client.get("data_sources")
    (out / "_debug_data_sources.json").write_text(
        json.dumps(ds_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    ds_list = ds_payload.get("_embedded", {}).get("data_sources", [])
    print(f"Debug: /data_sources ha retornat {len(ds_list)} fonts.")

    spaces = spaces_payload.get("_embedded", {}).get("spaces", [])
    print(f"Debug: /spaces?filter=all ha retornat {len(spaces)} espais.")

    probe: dict = {"space_count": len(spaces), "data_source_count": len(ds_list)}
    if ds_list:
        probe["first_data_source_links"] = ds_list[0].get("_links", {})
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

    inventory, reports = process(collected)
    paths = write_outputs(
        inventory, reports, args.output_dir, top_n=args.top_n
    )

    dead = sum(1 for r in inventory if r.data_source_alive == "no")
    print("Sortides generades:")
    for name, path in paths.items():
        print(f"  - {name}: {path}")
    print(f"Queries cap a fonts mortes/desconegudes: {dead}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
