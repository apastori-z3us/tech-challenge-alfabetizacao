"""Registro de fontes carregado de `config/sources.yaml`."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.batch.models import SourceConfig, parse_source
from src.common.settings import Settings


def load_sources(settings: Settings) -> dict[str, SourceConfig]:
    """Carrega e valida todas as fontes declaradas em sources.yaml."""
    path: Path = settings.config_path / "sources.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de fontes não encontrado: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_sources = payload.get("sources", {}) or {}

    sources: dict[str, SourceConfig] = {}
    for name, spec in raw_sources.items():
        config = parse_source(name, spec)
        config.validate()
        sources[name] = config
    return sources


def get_source(settings: Settings, name: str) -> SourceConfig:
    """Retorna a configuração de uma fonte específica."""
    sources = load_sources(settings)
    if name not in sources:
        raise KeyError(
            f"Fonte '{name}' não encontrada. Disponíveis: {sorted(sources)}"
        )
    return sources[name]


def enabled_sources(settings: Settings) -> dict[str, SourceConfig]:
    """Retorna apenas as fontes habilitadas."""
    return {
        name: cfg for name, cfg in load_sources(settings).items() if cfg.enabled
    }
