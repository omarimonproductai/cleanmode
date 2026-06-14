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
    """Tots els espais/col·leccions de què l'usuari del token és membre."""
    return list(client.paginate("spaces", "spaces"))


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


_SKIP_STATUSES = {403, 404}


def _collection_name(client: ModeClient, token: str) -> str:
    """Intenta llegir el nom d'una col·lecció pel seu token; si no, retorna el token."""
    try:
        detail = client.get(f"collections/{token}")
    except ModeAPIError:
        return token
    return detail.get("name", token)


def _iter_collection_sources(
    client: ModeClient,
    collection_tokens: list[str] | None,
    collection_names: dict[str, str] | None,
) -> list[tuple[str, str]]:
    """Retorna (nom, reports_path) per cada col·lecció a recórrer.

    Si es passen tokens explícits, s'accedeix directament a
    ``collections/{token}/reports`` (encara que /spaces no els llisti). El nom
    s'agafa de ``collection_names`` si es coneix; si no, es demana a l'API. Si
    no hi ha tokens, s'enumeren els espais de què l'usuari del token és membre.
    """
    names = collection_names or {}
    if collection_tokens:
        return [
            (
                names.get(t) or _collection_name(client, t),
                f"collections/{t}/reports",
            )
            for t in collection_tokens
        ]

    sources: list[tuple[str, str]] = []
    for space in collect_spaces(client):
        name = space.get("name", "(sense nom)")
        path = _href(space, "reports")
        if not path:
            token = space.get("token")
            if not token:
                continue
            path = f"collections/{token}/reports"
        sources.append((name, path))
    return sources


def collect_all(
    client: ModeClient,
    collection_tokens: list[str] | None = None,
    collection_names: dict[str, str] | None = None,
) -> Collected:
    """Recull fonts de dades i els reports (amb queries) de les col·leccions.

    Inclou reports arxivats. Si ``collection_tokens`` es passa, accedeix
    directament a aquestes col·leccions; si no, recorre els espais de què
    l'usuari del token és membre. Salta amb un avís les col·leccions/reports no
    accessibles (403/404) en comptes de tombar el run.
    """
    data_sources = collect_data_sources(client)

    reports: list[CollectedReport] = []
    query_failures = 0
    for space_name, reports_path in _iter_collection_sources(
        client, collection_tokens, collection_names
    ):
        try:
            space_reports = list(client.paginate(reports_path, "reports"))
        except ModeAPIError as exc:
            # Qualsevol error (permís, 500, reintents exhaurits) -> saltar la
            # col·lecció sencera amb avís, però no tombar el run.
            print(
                f"  Avís: col·lecció '{space_name}' no accessible "
                f"({exc.status_code or 'error'}), s'omet.",
                file=sys.stderr,
            )
            continue

        for report in space_reports:
            try:
                queries = collect_report_queries(client, report)
            except ModeAPIError as exc:
                # Un report concret que falla no ha d'aturar tot l'escaneig.
                query_failures += 1
                print(
                    f"  Avís: queries del report "
                    f"'{report.get('name', report.get('token'))}' no "
                    f"recuperables ({exc.status_code or 'error'}), queries=0.",
                    file=sys.stderr,
                )
                queries = []
            reports.append(
                CollectedReport(
                    report=report, space_name=space_name, queries=queries
                )
            )

    if query_failures:
        print(
            f"  Total reports amb queries no recuperables: {query_failures}.",
            file=sys.stderr,
        )

    return Collected(data_sources=data_sources, reports=reports)
