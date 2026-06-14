"""Recollida de dades crua des de l'API de MODE.

Obté fonts de dades, espais, reports (inclosos arxivats), les queries de cada
report i la informació d'execució (últim run). No transforma res; això és feina
de ``process.py``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from .client import ModeAPIError, ModeClient


@dataclass
class CollectedReport:
    """Un report amb les seves queries, tal com arriben de l'API."""

    report: dict[str, Any]
    space_name: str
    queries: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Collected:
    """Tot el que s'ha recollit del workspace."""

    data_sources: list[dict[str, Any]]
    reports: list[CollectedReport]


def collect_data_sources(client: ModeClient) -> list[dict[str, Any]]:
    """Totes les fonts de dades del workspace."""
    return list(client.paginate("data_sources", "data_sources"))


def collect_spaces(client: ModeClient) -> list[dict[str, Any]]:
    """Tots els espais/col·leccions.

    ``filter=all`` demana totes les col·leccions del workspace (cal ser
    Workspace Admin perquè en retorni més enllà de les pròpies); sense això
    l'API només retorna les col·leccions de què l'usuari del token és membre.
    """
    return list(client.paginate("spaces?filter=all", "spaces"))


def _href(obj: dict[str, Any], rel: str) -> str | None:
    """Enllaç HAL ``rel`` d'un objecte (p. ex. la URL de reports d'un espai)."""
    link = obj.get("_links", {}).get(rel)
    return link.get("href") if link else None


def collect_report_queries(
    client: ModeClient, report: dict[str, Any]
) -> list[dict[str, Any]]:
    """Queries d'un report, amb ``data_source_id`` i ``raw_query``.

    Segueix l'enllaç HAL ``queries`` del report; si no hi és, construeix el path.
    """
    path = _href(report, "queries") or f"reports/{report.get('token')}/queries"
    return list(client.paginate(path, "queries"))


def collect_all(client: ModeClient) -> Collected:
    """Recull fonts de dades i tots els reports (amb queries) de tots els espais.

    Inclou reports arxivats. Segueix els enllaços HAL que dona l'API per cada
    espai/report en comptes de construir paths a mà. Si un espai no és accessible
    (404), el salta amb un avís en comptes de tombar tot el run.
    """
    data_sources = collect_data_sources(client)
    spaces = collect_spaces(client)

    reports: list[CollectedReport] = []
    for space in spaces:
        space_name = space.get("name", "(sense nom)")
        reports_path = _href(space, "reports")
        if not reports_path:
            token = space.get("token")
            if not token:
                continue
            reports_path = f"spaces/{token}/reports"

        try:
            space_reports = list(client.paginate(reports_path, "reports"))
        except ModeAPIError as exc:
            if exc.status_code == 404:
                print(
                    f"  Avís: espai '{space_name}' no accessible (404), s'omet.",
                    file=sys.stderr,
                )
                continue
            raise

        for report in space_reports:
            try:
                queries = collect_report_queries(client, report)
            except ModeAPIError as exc:
                if exc.status_code == 404:
                    queries = []
                else:
                    raise
            reports.append(
                CollectedReport(
                    report=report, space_name=space_name, queries=queries
                )
            )

    return Collected(data_sources=data_sources, reports=reports)
