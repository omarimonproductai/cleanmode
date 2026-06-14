"""Transformació de les dades crues en files llestes per exportar.

- Mapeja el ``data_source_id`` de cada query al nom de la font de dades.
- Marca com a "morta/desconeguda" qualsevol query que apunti a un id que ja no
  existeix al llistat actual de fonts de dades.
- Calcula els dies des de l'últim run de cada report.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .collect import Collected, CollectedReport

DEAD_SOURCE_LABEL = "(morta/desconeguda)"
NEVER_RUN = "mai"

# Possibles noms del camp d'últim run al report (es confirmaran contra l'API
# real — tasca 2.6). Es prova en ordre i s'agafa el primer present.
_LAST_RUN_KEYS = ("last_successfully_run_at", "last_run_at", "last_saved_at")
# Possibles noms del camp d'owner del report.
_OWNER_KEYS = ("account_username", "user_username", "created_by")


@dataclass
class InventoryRow:
    """Una fila de la Sortida 1: combinació report + query."""

    data_source_name: str
    data_source_id: Any
    data_source_alive: str  # "si" / "no"
    report_name: str
    report_token: str
    report_url: str
    space_name: str
    query_name: str
    last_run_at: str
    days_since_last_run: Any  # int o "mai"
    owner: str
    is_archived: str  # "si" / "no"


@dataclass
class ReportRow:
    """Una fila de la Sortida 2: un report."""

    report_name: str
    report_token: str
    report_url: str
    space_name: str
    owner: str
    last_run_at: str
    days_since_last_run: Any  # int o "mai"
    is_archived: str


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _yes_no(value: Any) -> str:
    return "si" if value else "no"


def _report_url(report: dict[str, Any]) -> str:
    return report.get("_links", {}).get("web", {}).get("href", "")


def _owner(report: dict[str, Any]) -> str:
    for key in _OWNER_KEYS:
        if report.get(key):
            return str(report[key])
    return ""


def _last_run_raw(report: dict[str, Any]) -> str | None:
    for key in _LAST_RUN_KEYS:
        if report.get(key):
            return str(report[key])
    return None


def _days_since(last_run: str | None, now: datetime) -> Any:
    dt = _parse_dt(last_run)
    if dt is None:
        return NEVER_RUN
    return (now - dt).days


def build_data_source_index(data_sources: list[dict[str, Any]]) -> dict[Any, str]:
    """Mapa ``data_source_id`` -> nom de la font de dades."""
    return {ds.get("id"): ds.get("name", "(sense nom)") for ds in data_sources}


def _process_report(
    cr: CollectedReport, ds_index: dict[Any, str], now: datetime
) -> tuple[list[InventoryRow], ReportRow]:
    report = cr.report
    last_run = _last_run_raw(report)
    last_run_display = last_run or ""
    days = _days_since(last_run, now)
    owner = _owner(report)
    archived = _yes_no(report.get("archived"))
    url = _report_url(report)
    name = report.get("name", "(sense nom)")
    token = report.get("token", "")

    inventory: list[InventoryRow] = []
    for query in cr.queries:
        ds_id = query.get("data_source_id")
        alive = ds_id in ds_index
        inventory.append(
            InventoryRow(
                data_source_name=ds_index.get(ds_id, DEAD_SOURCE_LABEL),
                data_source_id=ds_id if ds_id is not None else "",
                data_source_alive=_yes_no(alive),
                report_name=name,
                report_token=token,
                report_url=url,
                space_name=cr.space_name,
                query_name=query.get("name", ""),
                last_run_at=last_run_display,
                days_since_last_run=days,
                owner=owner,
                is_archived=archived,
            )
        )

    report_row = ReportRow(
        report_name=name,
        report_token=token,
        report_url=url,
        space_name=cr.space_name,
        owner=owner,
        last_run_at=last_run_display,
        days_since_last_run=days,
        is_archived=archived,
    )
    return inventory, report_row


def process(
    collected: Collected, now: datetime | None = None
) -> tuple[list[InventoryRow], list[ReportRow]]:
    """Genera les files de les dues sortides a partir de les dades recollides.

    Returns:
        (inventory_rows, report_rows)
        - inventory_rows: ordenades per font de dades (mortes/desconegudes primer).
        - report_rows: ordenades per dies sense executar (més antics primer).
    """
    now = now or datetime.now(timezone.utc)
    ds_index = build_data_source_index(collected.data_sources)

    inventory: list[InventoryRow] = []
    reports: list[ReportRow] = []
    for cr in collected.reports:
        inv_rows, report_row = _process_report(cr, ds_index, now)
        inventory.extend(inv_rows)
        reports.append(report_row)

    # Sortida 1: agrupada per font de dades; les mortes/desconegudes primer.
    inventory.sort(
        key=lambda r: (r.data_source_alive == "si", r.data_source_name)
    )
    # Sortida 2: més antics (o mai executats) primer.
    reports.sort(key=_report_staleness_key, reverse=True)
    return inventory, reports


def _report_staleness_key(row: ReportRow) -> float:
    """Ordena per antiguitat: 'mai' és el més antic possible (infinit)."""
    if row.days_since_last_run == NEVER_RUN:
        return float("inf")
    return float(row.days_since_last_run)


def row_to_dict(row: InventoryRow | ReportRow) -> dict[str, Any]:
    return asdict(row)
