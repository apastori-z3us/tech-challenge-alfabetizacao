"""Sincronização das auditorias locais (JSONL) para as tabelas BigQuery.

Lê os arquivos `pipeline_runs.jsonl`, `quality_results.jsonl` e
`streaming_metrics.jsonl` e materializa as tabelas do dataset de auditoria.
Campos aninhados são serializados como JSON para caber em colunas STRING.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.common.logger import configure_logger
from src.common.settings import Settings

logger = configure_logger(name="audit_bq")

_AUDIT_FILES = {
    "pipeline_runs": "pipeline_runs.jsonl",
    "quality_results": "quality_results.jsonl",
    "streaming_metrics": "streaming_metrics.jsonl",
}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _flatten(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Serializa colunas com dict/list em texto JSON (compatível com BigQuery)."""
    result = dataframe.copy()
    for column in result.columns:
        if result[column].apply(lambda v: isinstance(v, (dict, list))).any():
            result[column] = result[column].apply(
                lambda v: json.dumps(v, ensure_ascii=False, default=str)
                if isinstance(v, (dict, list))
                else v
            )
    return result


def sync_audit_tables(client, settings: Settings) -> dict[str, int]:
    """Carrega as auditorias locais nas tabelas do dataset de auditoria."""
    from src.bronze.loader import load_dataframe_to_bigquery

    loaded: dict[str, int] = {}
    for table, filename in _AUDIT_FILES.items():
        records = _read_jsonl(settings.audit_path / filename)
        if not records:
            continue
        frame = _flatten(pd.DataFrame(records))
        result = load_dataframe_to_bigquery(
            client, settings, frame, table, layer="audit"
        )
        loaded[table] = result.records_loaded
        logger.info("Auditoria '%s' sincronizada: %s linha(s).", table, loaded[table])
    return loaded
