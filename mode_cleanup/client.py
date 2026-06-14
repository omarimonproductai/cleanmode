"""Client de l'API REST (Discovery API) de MODE.

Gestiona:
- Autenticació HTTP Basic (token:secret).
- Paginació HAL (segueix ``_links.next`` fins esgotar resultats).
- Reintents amb backoff exponencial davant 429 i errors transitoris.
"""

from __future__ import annotations

import time
from typing import Any, Iterator

import requests

from .config import Config

# Codis d'estat que es consideren transitoris i es reintenten.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ModeAPIError(RuntimeError):
    """Error no recuperable retornat per l'API de MODE."""


class ModeClient:
    """Client minimalista per a la Discovery API de MODE."""

    def __init__(
        self,
        config: Config,
        *,
        session: requests.Session | None = None,
        max_retries: int = 4,
        backoff_base: float = 2.0,
        timeout: float = 30.0,
    ) -> None:
        self._config = config
        self._session = session or requests.Session()
        self._session.auth = (config.api_token, config.api_secret)
        self._session.headers.update({"Accept": "application/hal+json"})
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._timeout = timeout

    def _absolute_url(self, path: str) -> str:
        """Converteix un path relatiu (p. ex. ``/api/<ws>/data_sources``) en URL absoluta."""
        if path.startswith("http"):
            return path
        if path.startswith("/api/"):
            return f"https://app.mode.com{path}"
        return f"{self._config.workspace_url}/{path.lstrip('/')}"

    def get(self, path: str) -> dict[str, Any]:
        """GET amb reintents/backoff. Retorna el cos JSON com a dict."""
        url = self._absolute_url(path)
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._session.get(url, timeout=self._timeout)
            except requests.RequestException as exc:  # error de xarxa transitori
                last_exc = exc
            else:
                if response.status_code == 200:
                    return response.json()
                if response.status_code not in _RETRYABLE_STATUS:
                    raise ModeAPIError(
                        f"GET {url} ha retornat {response.status_code}: {response.text[:300]}"
                    )
                last_exc = ModeAPIError(
                    f"GET {url} ha retornat {response.status_code} (transitori)"
                )

            if attempt < self._max_retries:
                time.sleep(self._backoff_base ** attempt)

        raise ModeAPIError(
            f"GET {url} ha fallat després de {self._max_retries + 1} intents"
        ) from last_exc

    def paginate(self, path: str, collection: str) -> Iterator[dict[str, Any]]:
        """Itera tots els elements d'una col·lecció HAL seguint ``_links.next``.

        Args:
            path: path inicial de la col·lecció.
            collection: clau dins de ``_embedded`` que conté la llista (p. ex. "reports").
        """
        next_path: str | None = path
        while next_path:
            payload = self.get(next_path)
            embedded = payload.get("_embedded", {})
            for item in embedded.get(collection, []):
                yield item

            next_link = payload.get("_links", {}).get("next")
            next_path = next_link.get("href") if next_link else None
