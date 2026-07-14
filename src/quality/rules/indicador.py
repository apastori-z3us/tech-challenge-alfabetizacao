"""Regras de qualidade do indicador de alfabetização."""

from __future__ import annotations

from src.quality.checks import (
    ColumnRule,
    EntityQualitySpec,
    matches_regex,
    numeric_between,
    strip_text,
    upper_text,
    year_valid,
)

TAXA_MIN = 0.0
TAXA_MAX = 100.0


def build_indicador_spec() -> EntityQualitySpec:
    """Chave lógica: (ano, id_municipio); rede/serie desambiguam quando presentes."""
    return EntityQualitySpec(
        entity="indicador_alfabetizacao",
        required_columns=["ano", "id_municipio", "taxa_alfabetizacao"],
        standardizers={
            "ano": strip_text,
            "id_municipio": strip_text,
            "sigla_uf": upper_text,
        },
        rules=[
            ColumnRule(
                name="ano.valid_year",
                column="ano",
                func=lambda df: year_valid(df["ano"]),
            ),
            ColumnRule(
                name="id_municipio.seven_digits",
                column="id_municipio",
                func=lambda df: matches_regex(df["id_municipio"], r"\d{7}"),
            ),
            ColumnRule(
                name="taxa_alfabetizacao.in_range",
                column="taxa_alfabetizacao",
                func=lambda df: numeric_between(
                    df["taxa_alfabetizacao"], TAXA_MIN, TAXA_MAX
                ),
            ),
        ],
        unique_keys=["ano", "id_municipio"],
    )
