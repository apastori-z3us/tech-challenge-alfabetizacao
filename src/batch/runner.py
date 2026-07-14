"""Orquestração da ingestão Batch por fonte, com auditoria e idempotência."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from src.batch.extractor import (
    BronzeExtractionResult,
    CallableReader,
    DataReader,
    extract_to_bronze,
)
from src.batch.models import SourceConfig
from src.batch.registry import get_source
from src.common.audit import PipelineRun, record_pipeline_run
from src.common.io_utils import read_parquet_dir
from src.common.logger import configure_logger
from src.common.settings import Settings
from src.quality.reference import (
    SIGLA_TO_CODIGO_UF,
    UF_CODIGO_TO_SIGLA,
    UF_SIGLA_TO_NOME,
    UF_TO_REGIAO,
)

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


def derive_uf_from_municipio(
    settings: Settings, source: SourceConfig
) -> pd.DataFrame:
    """Deriva a dimensão UF a partir da Bronze de municípios + referência oficial.

    Decisão documentada: evita depender de uma tabela externa não validada.
    """
    municipio_dir = settings.bronze_path / "batch" / "municipio"
    if municipio_dir.exists():
        base = read_parquet_dir(municipio_dir)
        siglas = sorted(
            s for s in base["sigla_uf"].astype("string").str.upper().unique() if s
        )
        siglas = [s for s in siglas if s in SIGLA_TO_CODIGO_UF]
    else:
        siglas = sorted(UF_CODIGO_TO_SIGLA.values())

    return pd.DataFrame(
        {
            "codigo_uf": [SIGLA_TO_CODIGO_UF[s] for s in siglas],
            "sigla_uf": siglas,
            "nome": [UF_SIGLA_TO_NOME[s] for s in siglas],
            "regiao": [UF_TO_REGIAO[s] for s in siglas],
        }
    )


def reader_for(settings: Settings, source: SourceConfig) -> DataReader:
    """Escolhe o leitor adequado para a fonte (derivada usa função local)."""
    if source.ingestion_type == "derived" and source.name == "uf":
        return CallableReader(derive_uf_from_municipio)
    raise RuntimeError(
        f"Fonte '{source.name}' requer um leitor BigQuery explícito "
        "(indisponível offline). Ver docs/blockers.md."
    )


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
