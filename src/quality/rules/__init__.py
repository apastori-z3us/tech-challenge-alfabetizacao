"""Especificações de qualidade por entidade e registro de builders."""

from __future__ import annotations

from collections.abc import Callable

from src.quality.checks import EntityQualitySpec
from src.quality.rules.aluno import build_aluno_spec
from src.quality.rules.indicador import build_indicador_spec
from src.quality.rules.metas import (
    build_meta_brasil_spec,
    build_meta_municipio_spec,
    build_meta_uf_spec,
)
from src.quality.rules.municipio import build_municipio_spec
from src.quality.rules.uf import build_uf_spec

SPEC_BUILDERS: dict[str, Callable[[], EntityQualitySpec]] = {
    "municipio": build_municipio_spec,
    "uf": build_uf_spec,
    "meta_brasil": build_meta_brasil_spec,
    "meta_uf": build_meta_uf_spec,
    "meta_municipio": build_meta_municipio_spec,
    "indicador_alfabetizacao": build_indicador_spec,
    "aluno": build_aluno_spec,
}


def get_spec(entity: str) -> EntityQualitySpec:
    """Retorna a especificação de qualidade de uma entidade."""
    if entity not in SPEC_BUILDERS:
        raise KeyError(
            f"Sem especificação de qualidade para '{entity}'. "
            f"Disponíveis: {sorted(SPEC_BUILDERS)}"
        )
    return SPEC_BUILDERS[entity]()
