"""Càrrega i validació de la configuració des de variables d'entorn."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    # Carrega .env si python-dotenv està instal·lat (opcional en execució real).
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv és opcional
    pass


class ConfigError(RuntimeError):
    """Falta configuració obligatòria o és invàlida."""


@dataclass(frozen=True)
class Config:
    """Configuració necessària per parlar amb l'API de MODE."""

    workspace: str
    api_token: str
    api_secret: str
    base_url: str = "https://app.mode.com/api"

    @property
    def workspace_url(self) -> str:
        """URL base per a totes les crides d'aquest workspace."""
        return f"{self.base_url}/{self.workspace}"


_REQUIRED_VARS = ("MODE_WORKSPACE", "MODE_API_TOKEN")


def _resolve_secret(source) -> str | None:
    """El secret pot venir com MODE_API_SECRET o, com a àlies, MODE_SECRET."""
    return source.get("MODE_API_SECRET") or source.get("MODE_SECRET")


def load_config(env: dict[str, str] | None = None) -> Config:
    """Llegeix la configuració de l'entorn i falla amb un missatge clar si en falta alguna.

    Args:
        env: diccionari de variables (per defecte ``os.environ``); útil per a tests.
    """
    source = os.environ if env is None else env
    missing = [name for name in _REQUIRED_VARS if not source.get(name)]
    if not _resolve_secret(source):
        missing.append("MODE_API_SECRET (o MODE_SECRET)")
    if missing:
        raise ConfigError(
            "Falten variables d'entorn obligatòries: "
            + ", ".join(missing)
            + ". Copia .env.example a .env i omple els valors."
        )

    return Config(
        workspace=source["MODE_WORKSPACE"],
        api_token=source["MODE_API_TOKEN"],
        api_secret=_resolve_secret(source),
    )
