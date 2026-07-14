"""Carga da camada Silver: local (Parquet), quarentena, auditoria e BigQuery.

A carga no BigQuery é injetável (`bq_loader`), o que permite execução e testes
totalmente offline, preservando a compatibilidade com o fluxo em nuvem.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.common.audit import (
    PipelineRun,
    record_pipeline_run,
    record_quality_result,
    write_quality_report,
)
from src.common.io_utils import partition_dir, write_parquet
from src.common.logger import configure_logger
from src.common.settings import Settings, processing_date
from src.quality.checks import EntityQualitySpec
from src.quality.models import QualityReport
from src.silver.transform import transform_entity

BqLoader = Callable[[pd.DataFrame, str], int]


@dataclass
class SilverResult:
    """Resultado consolidado da materialização Silver de uma entidade."""

    entity: str
    report: QualityReport
    silver_path: Path | None
    quarantine_path: Path | None
    bronze_count: int
    valid_count: int
    invalid_count: int
    silver_loaded_count: int | None


def _write_silver(
    settings: Settings, entity: str, dataframe: pd.DataFrame, run_id: str
) -> Path:
    directory = partition_dir(
        settings.silver_path, entity, "processing_date", processing_date()
    )
    path = directory / f"{entity}_{run_id}.parquet"
    return write_parquet(dataframe, path)


def _write_quarantine(
    settings: Settings, entity: str, dataframe: pd.DataFrame, run_id: str
) -> Path:
    directory = partition_dir(
        settings.quarantine_path, entity, "processing_date", processing_date()
    )
    path = directory / f"{entity}_{run_id}.parquet"
    return write_parquet(dataframe, path)


def build_silver(
    settings: Settings,
    entity: str,
    bronze_dataframe: pd.DataFrame,
    spec: EntityQualitySpec,
    *,
    bq_loader: BqLoader | None = None,
) -> SilverResult:
    """Executa qualidade, grava Silver/quarentena, audita e valida contagens.

    Garante os invariantes:
    - `bronze_count == valid_count + invalid_count`;
    - `valid_count == silver_loaded_count` (quando há carga no BigQuery).
    """
    logger = configure_logger(name=f"silver_{entity}", level=settings.log_level)
    bronze_count = len(bronze_dataframe)

    report = transform_entity(bronze_dataframe, spec)

    # Invariante de particionamento: nenhum registro pode se perder.
    if report.valid_count + report.invalid_count != bronze_count:
        raise RuntimeError(
            "Contagem inconsistente após qualidade: "
            f"bronze={bronze_count}, válidos={report.valid_count}, "
            f"inválidos={report.invalid_count}."
        )

    silver_path: Path | None = None
    if report.valid_count > 0:
        silver_path = _write_silver(
            settings, entity, report.valid_df, report.quality_run_id
        )
        report.silver_path = str(silver_path)

    quarantine_path: Path | None = None
    if report.invalid_count > 0:
        quarantine_path = _write_quarantine(
            settings, entity, report.invalid_df, report.quality_run_id
        )
        report.quarantine_path = str(quarantine_path)
        logger.warning(
            "%s registro(s) enviados à quarentena: %s",
            report.invalid_count,
            quarantine_path,
        )

    write_quality_report(settings, report.to_dict())
    record_quality_result(settings, report.to_dict())

    silver_loaded_count: int | None = None
    if bq_loader is not None and report.valid_count > 0:
        silver_loaded_count = bq_loader(report.valid_df, entity)
        if silver_loaded_count != report.valid_count:
            raise RuntimeError(
                "Divergência na carga Silver do BigQuery: "
                f"válidos={report.valid_count}, carregados={silver_loaded_count}."
            )

    record_pipeline_run(
        settings,
        PipelineRun(
            pipeline_name=f"silver_{entity}",
            source=entity,
            layer="silver",
            status=report.status,
            records_read=bronze_count,
            records_written=report.valid_count,
            records_valid=report.valid_count,
            records_rejected=report.invalid_count,
        ),
    )

    logger.info(
        "Silver de %s concluída: lidos=%s válidos=%s inválidos=%s",
        entity,
        bronze_count,
        report.valid_count,
        report.invalid_count,
    )

    return SilverResult(
        entity=entity,
        report=report,
        silver_path=silver_path,
        quarantine_path=quarantine_path,
        bronze_count=bronze_count,
        valid_count=report.valid_count,
        invalid_count=report.invalid_count,
        silver_loaded_count=silver_loaded_count,
    )
