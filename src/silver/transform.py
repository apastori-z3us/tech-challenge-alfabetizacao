"""Transformações da camada Silver.

Reutiliza o motor de qualidade (`run_quality`) e acrescenta os metadados
padronizados da camada Silver aos registros aprovados.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.quality.checks import EntityQualitySpec, run_quality
from src.quality.models import QualityReport

SILVER_METADATA_COLUMNS = [
    "_quality_status",
    "_silver_processed_timestamp",
    "_ingestion_id",
    "_record_hash",
]


def add_silver_metadata(
    dataframe: pd.DataFrame, quality_status: str
) -> pd.DataFrame:
    """Acrescenta os metadados obrigatórios da camada Silver.

    Preserva os metadados vindos da Bronze (`_ingestion_id`, `_record_hash`).
    """
    result = dataframe.copy()
    result["_quality_status"] = quality_status
    result["_silver_processed_timestamp"] = datetime.now(timezone.utc).isoformat()
    if "_ingestion_id" not in result.columns:
        result["_ingestion_id"] = None
    if "_record_hash" not in result.columns:
        result["_record_hash"] = None
    return result


def transform_entity(
    dataframe: pd.DataFrame, spec: EntityQualitySpec
) -> QualityReport:
    """Executa qualidade e prepara os registros Silver de uma entidade.

    Levanta `CriticalSchemaError` se faltar coluna obrigatória.
    """
    report = run_quality(dataframe, spec, layer="silver")
    report.valid_df = add_silver_metadata(report.valid_df, "VALID")
    if not report.invalid_df.empty:
        report.invalid_df = add_silver_metadata(report.invalid_df, "INVALID")
    return report
