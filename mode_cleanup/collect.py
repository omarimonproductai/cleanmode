"""Recollida de dades crua des de l'API de MODE.

Obté fonts de dades, espais, reports (inclosos arxivats), les queries de cada
report i la informació d'execució (últim run). No transforma res; això és feina
de ``process.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .client import ModeClient


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
    """Tots els espais/col·leccions (inclou l'espai personal)."""
    return list(client.paginate("spaces", "spaces"))


def collect_report_queries(
    client: ModeClient, report_token: str
) -> list[dict[str, Any]]:
    """Queries d'un report, amb ``data_source_id`` i ``raw_query``."""
    return list(client.paginate(f"reports/{report_token}/queries", "queries"))


def collect_all(client: ModeClient) -> Collected:
    """Recull fonts de dades i tots els reports (amb queries) de tots els espais.

    Inclou reports arxivats: l'API els retorna dins de cada espai i no els
    filtrem.
    """
    data_sources = collect_data_sources(client)
    spaces = collect_spaces(client)

    reports: list[CollectedReport] = []
    for space in spaces:
        space_token = space.get("token")
        space_name = space.get("name", "(sense nom)")
        if not space_token:
            continue
        for report in client.paginate(
            f"spaces/{space_token}/reports", "reports"
        ):
            report_token = report.get("token")
            queries = (
                collect_report_queries(client, report_token)
                if report_token
                else []
            )
            reports.append(
                CollectedReport(
                    report=report, space_name=space_name, queries=queries
                )
            )

    return Collected(data_sources=data_sources, reports=reports)
