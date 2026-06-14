"""Punt d'entrada: config -> recollida -> processament -> sortides."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import ModeClient
from .collect import collect_all
from .config import ConfigError, load_config
from .outputs import write_outputs
from .process import process


def _debug_dump(client: ModeClient, output_dir: str) -> None:
    """Bolca l'estructura crua de /spaces (i el detall del primer espai via
    el seu self link) per inspeccionar com cal demanar els reports."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    spaces_payload = client.get("spaces")
    (out / "_debug_spaces.json").write_text(
        json.dumps(spaces_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    spaces = spaces_payload.get("_embedded", {}).get("spaces", [])
    print(f"Debug: /spaces ha retornat {len(spaces)} espais.")
    if spaces:
        self_href = spaces[0].get("_links", {}).get("self", {}).get("href")
        if self_href:
            detail = client.get(self_href)
            (out / "_debug_space_detail.json").write_text(
                json.dumps(detail, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )


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
