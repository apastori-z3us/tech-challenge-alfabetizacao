"""Regras de qualidade da entidade UF."""

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


def build_uf_spec() -> EntityQualitySpec:
    return EntityQualitySpec(
        entity="uf",
        required_columns=["codigo_uf", "sigla_uf", "nome"],
        standardizers={
            "codigo_uf": strip_text,
            "sigla_uf": upper_text,
            "nome": strip_text,
        },
        rules=[
            ColumnRule(
                name="codigo_uf.two_digits",
                column="codigo_uf",
                func=lambda df: matches_regex(df["codigo_uf"], r"\d{2}"),
            ),
            ColumnRule(
                name="sigla_uf.valid_uf",
                column="sigla_uf",
                func=lambda df: in_set(df["sigla_uf"], sorted(UFS_VALIDAS)),
            ),
            ColumnRule(
                name="nome.not_null",
                column="nome",
                func=lambda df: not_null(df["nome"]),
            ),
        ],
        unique_keys=["sigla_uf"],
    )
