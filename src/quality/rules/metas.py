"""Regras de qualidade das metas de alfabetização (Brasil, UF e Município)."""

from __future__ import annotations

from src.quality.checks import (
    ColumnRule,
    EntityQualitySpec,
    in_set,
    matches_regex,
    numeric_between,
    strip_text,
    upper_text,
    year_valid,
)
from src.quality.reference import UFS_VALIDAS

META_MIN = 0.0
META_MAX = 100.0


def _ano_rule() -> ColumnRule:
    return ColumnRule(
        name="ano.valid_year",
        column="ano",
        func=lambda df: year_valid(df["ano"]),
    )


def _valor_meta_rule() -> ColumnRule:
    return ColumnRule(
        name="valor_meta.in_range",
        column="valor_meta",
        func=lambda df: numeric_between(df["valor_meta"], META_MIN, META_MAX),
    )


def build_meta_brasil_spec() -> EntityQualitySpec:
    return EntityQualitySpec(
        entity="meta_brasil",
        required_columns=["ano", "valor_meta"],
        standardizers={"ano": strip_text},
        rules=[_ano_rule(), _valor_meta_rule()],
        unique_keys=["ano"],
    )


def build_meta_uf_spec() -> EntityQualitySpec:
    return EntityQualitySpec(
        entity="meta_uf",
        required_columns=["ano", "sigla_uf", "valor_meta"],
        standardizers={"ano": strip_text, "sigla_uf": upper_text},
        rules=[
            _ano_rule(),
            ColumnRule(
                name="sigla_uf.valid_uf",
                column="sigla_uf",
                func=lambda df: in_set(df["sigla_uf"], sorted(UFS_VALIDAS)),
            ),
            _valor_meta_rule(),
        ],
        unique_keys=["ano", "sigla_uf"],
    )


def build_meta_municipio_spec() -> EntityQualitySpec:
    return EntityQualitySpec(
        entity="meta_municipio",
        required_columns=["ano", "id_municipio", "valor_meta"],
        standardizers={"ano": strip_text, "id_municipio": strip_text},
        rules=[
            _ano_rule(),
            ColumnRule(
                name="id_municipio.seven_digits",
                column="id_municipio",
                func=lambda df: matches_regex(df["id_municipio"], r"\d{7}"),
            ),
            _valor_meta_rule(),
        ],
        unique_keys=["ano", "id_municipio"],
    )
