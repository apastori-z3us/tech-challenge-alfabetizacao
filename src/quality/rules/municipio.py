"""Regras de qualidade da entidade Município."""

from __future__ import annotations

from src.quality.checks import (
    ColumnRule,
    EntityQualitySpec,
    in_set,
    matches_regex,
    not_null,
    strip_text,
    upper_text,
)
from src.quality.reference import UFS_VALIDAS

ID_MUNICIPIO_PATTERN = r"\d{7}"


def build_municipio_spec() -> EntityQualitySpec:
    """Especificação de qualidade para municípios."""
    return EntityQualitySpec(
        entity="municipio",
        required_columns=["id_municipio", "nome", "sigla_uf"],
        standardizers={
            "id_municipio": strip_text,
            "nome": strip_text,
            "sigla_uf": upper_text,
        },
        rules=[
            ColumnRule(
                name="id_municipio.not_null",
                column="id_municipio",
                func=lambda df: not_null(df["id_municipio"]),
            ),
            ColumnRule(
                name="id_municipio.seven_digits",
                column="id_municipio",
                func=lambda df: matches_regex(
                    df["id_municipio"], ID_MUNICIPIO_PATTERN
                ),
            ),
            ColumnRule(
                name="nome.not_null",
                column="nome",
                func=lambda df: not_null(df["nome"]),
            ),
            ColumnRule(
                name="sigla_uf.not_null",
                column="sigla_uf",
                func=lambda df: not_null(df["sigla_uf"]),
            ),
            ColumnRule(
                name="sigla_uf.valid_uf",
                column="sigla_uf",
                func=lambda df: in_set(df["sigla_uf"], sorted(UFS_VALIDAS)),
            ),
        ],
        unique_keys=["id_municipio"],
    )
