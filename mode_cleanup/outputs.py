"""Escriptura de les sortides: dos CSV i un resum en Markdown."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import fields
from pathlib import Path

from .process import (
    NEVER_RUN,
    DataSourceRow,
    InventoryRow,
    ReportRow,
    row_to_dict,
)

INVENTORY_CSV = "inventory_by_data_source.csv"
REPORTS_CSV = "reports_by_staleness.csv"
DATA_SOURCES_CSV = "data_sources.csv"
SUMMARY_MD = "summary.md"


def _write_csv(path: Path, rows: list, row_type) -> None:
    headers = [f.name for f in fields(row_type)]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_dict(row))


def write_data_sources(
    rows: list[DataSourceRow], output_dir: str | Path
) -> Path:
    """Escriu l'inventari de fonts de dades. Retorna el path generat."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / DATA_SOURCES_CSV
    _write_csv(path, rows, DataSourceRow)
    return path


def write_outputs(
    inventory: list[InventoryRow],
    reports: list[ReportRow],
    output_dir: str | Path,
    *,
    top_n: int = 20,
) -> dict[str, Path]:
    """Escriu els dos CSV i el resum. Retorna els paths generats."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    inventory_path = out / INVENTORY_CSV
    reports_path = out / REPORTS_CSV
    summary_path = out / SUMMARY_MD

    _write_csv(inventory_path, inventory, InventoryRow)
    _write_csv(reports_path, reports, ReportRow)
    summary_path.write_text(
        _build_summary(inventory, reports, top_n), encoding="utf-8"
    )

    return {
        "inventory": inventory_path,
        "reports": reports_path,
        "summary": summary_path,
    }


def _build_summary(
    inventory: list[InventoryRow], reports: list[ReportRow], top_n: int
) -> str:
    total_reports = len(reports)
    total_queries = len(inventory)
    dead_queries = sum(1 for r in inventory if r.data_source_alive == "no")
    never_run = sum(1 for r in reports if r.days_since_last_run == NEVER_RUN)

    # Recompte de queries per font de dades.
    by_source = Counter(r.data_source_name for r in inventory)

    lines = [
        "# Resum — Inventari de reports/queries de MODE",
        "",
        f"- Reports totals: **{total_reports}**",
        f"- Queries totals (files d'inventari): **{total_queries}**",
        f"- Queries cap a fonts mortes/desconegudes: **{dead_queries}**",
        f"- Reports mai executats: **{never_run}**",
        "",
        "## Queries per font de dades",
        "",
        "| Font de dades | Queries |",
        "| --- | --- |",
    ]
    for name, count in by_source.most_common():
        lines.append(f"| {name} | {count} |")

    lines += [
        "",
        f"## Top {top_n} reports més antics (o mai executats)",
        "",
        "| Report | Espai | Últim run | Dies | Arxivat |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in reports[:top_n]:
        last = row.last_run_at or NEVER_RUN
        lines.append(
            f"| {row.report_name} | {row.space_name} | {last} | "
            f"{row.days_since_last_run} | {row.is_archived} |"
        )

    return "\n".join(lines) + "\n"
