"""Regras de qualidade dos dados de alunos (com anonimização)."""

from __future__ import annotations

from src.quality.checks import (
    ColumnRule,
    EntityQualitySpec,
    hash_text,
    not_null,
    strip_text,
    upper_text,
    year_valid,
)


def build_aluno_spec() -> EntityQualitySpec:
    """`id_aluno` é anonimizado (hash) já na padronização Silver.

    Nenhum dado pessoal identificável deve trafegar para a Gold.
    """
    return EntityQualitySpec(
        entity="aluno",
        required_columns=["ano", "id_aluno"],
        standardizers={
            "ano": strip_text,
            "id_aluno": hash_text,  # anonimização irreversível
            "rede": upper_text,
        },
        rules=[
            ColumnRule(
                name="ano.valid_year",
                column="ano",
                func=lambda df: year_valid(df["ano"]),
            ),
            ColumnRule(
                name="id_aluno.not_null",
                column="id_aluno",
                func=lambda df: not_null(df["id_aluno"]),
            ),
        ],
        unique_keys=["ano", "id_aluno"],
    )
