"""Geração de consultas SQL seguras para a ingestão Batch.

Prioriza um arquivo SQL versionado em `sql/extraction/<fonte>.sql`. Se ele não
existir, gera um SELECT explícito (apenas colunas necessárias, sem `SELECT *`)
a partir de `selected_columns`, o que reduz bytes lidos (FinOps).
"""

from __future__ import annotations

from src.batch.models import SourceConfig
from src.common.settings import Settings

_IDENTIFIER_MAX_LEN = 300


def _safe_identifier(identifier: str) -> str:
    """Valida um identificador de coluna/tabela para evitar injeção."""
    if not identifier or len(identifier) > _IDENTIFIER_MAX_LEN:
        raise ValueError(f"Identificador inválido: {identifier!r}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if not set(identifier).issubset(allowed):
        raise ValueError(f"Identificador com caracteres inválidos: {identifier!r}")
    return identifier


def sql_file_for(settings: Settings, source: SourceConfig):
    """Caminho do arquivo SQL versionado da fonte, se existir."""
    path = settings.sql_path / "extraction" / f"{source.name}.sql"
    return path if path.exists() else None


def build_query(settings: Settings, source: SourceConfig) -> str:
    """Retorna o SQL da fonte (arquivo versionado ou SELECT gerado)."""
    sql_file = sql_file_for(settings, source)
    if sql_file is not None:
        return sql_file.read_text(encoding="utf-8")

    if not source.is_bigquery_source:
        raise ValueError(
            f"Fonte '{source.name}' não é uma tabela BigQuery válida "
            "para geração de SQL."
        )

    columns = ", ".join(_safe_identifier(c) for c in source.selected_columns)
    table = _safe_identifier(source.table_id)
    order = ", ".join(_safe_identifier(c) for c in source.key_columns)
    query = f"SELECT {columns}\nFROM `{table}`"
    if order:
        query += f"\nORDER BY {order}"
    return query
