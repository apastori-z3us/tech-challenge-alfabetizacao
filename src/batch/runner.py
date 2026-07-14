"""Orquestração da ingestão Batch por fonte, com auditoria e idempotência."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from src.batch.extractor import (
    BronzeExtractionResult,
    DataReader,
    extract_to_bronze,
)
from src.batch.registry import get_source
from src.common.audit import PipelineRun, record_pipeline_run
from src.common.logger import configure_logger
from src.common.settings import Settings

BronzeLoader = Callable[[pd.DataFrame, str], int]


@dataclass
class BatchRunResult:
    """Resumo de uma execução de ingestão Batch."""

    source_name: str
    records_read: int
    bronze_loaded_count: int | None
    output_path: str
    ingestion_id: str
    bytes_processed: int


def run_batch_source(
    settings: Settings,
    source_name: str,
    reader: DataReader,
    *,
    bronze_loader: BronzeLoader | None = None,
) -> BatchRunResult:
    """Executa a ingestão Batch de uma fonte até a Bronze, com auditoria."""
    logger = configure_logger(name="batch_runner", level=settings.log_level)
    source = get_source(settings, source_name)

    result: BronzeExtractionResult = extract_to_bronze(settings, source, reader)

    bronze_loaded_count: int | None = None
    if bronze_loader is not None:
        bronze_loaded_count = bronze_loader(result.dataframe, source.name)
        if bronze_loaded_count != result.records_read:
            raise RuntimeError(
                f"Divergência de carga Bronze de '{source.name}': "
                f"lidos={result.records_read}, carregados={bronze_loaded_count}."
            )

    record_pipeline_run(
        settings,
        PipelineRun(
            pipeline_name=f"batch_{source.name}",
            source=source.table_id,
            layer="bronze",
            status="SUCCESS",
            records_read=result.records_read,
            records_written=result.records_read,
            bytes_processed=result.bytes_processed,
        ),
    )
    logger.info("Ingestão Batch de '%s' concluída.", source.name)

    return BatchRunResult(
        source_name=source.name,
        records_read=result.records_read,
        bronze_loaded_count=bronze_loaded_count,
        output_path=str(result.output_path),
        ingestion_id=result.ingestion_id,
        bytes_processed=result.bytes_processed,
    )
