"""Extrator Batch genérico e configurável.

Uma única interface (`extract_to_bronze`) atende todas as fontes habilitadas em
`sources.yaml`, evitando um extrator duplicado por fonte. A leitura dos dados é
injetável (`DataReader`): em produção usa BigQuery (com dry run e
`maximum_bytes_billed`); offline/testes usam um leitor local.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import pandas as pd

from src.batch.models import SourceConfig
from src.batch.queries import build_query
from src.common.io_utils import partition_dir, write_parquet
from src.common.logger import configure_logger
from src.common.settings import Settings

METADATA_COLUMNS = [
    "_ingestion_id",
    "_ingestion_timestamp",
    "_source_project",
    "_source_dataset",
    "_source_table",
    "_load_type",
    "_record_hash",
    "_schema_version",
]

MAX_BYTES_BILLED = 1_000_000_000  # 1 GB — proteção FinOps por consulta.


class DataReader(Protocol):
    """Leitor de dados de uma fonte. Retorna (DataFrame, bytes_processados)."""

    def fetch(
        self, settings: Settings, source: SourceConfig
    ) -> tuple[pd.DataFrame, int]: ...


@dataclass
class BigQueryReader:
    """Leitor de produção: consulta o BigQuery com dry run e limite de bytes."""

    client: object

    def fetch(
        self, settings: Settings, source: SourceConfig
    ) -> tuple[pd.DataFrame, int]:
        from google.cloud import bigquery

        logger = configure_logger(name="bq_reader", level=settings.log_level)
        sql = build_query(settings, source)

        dry_run_config = bigquery.QueryJobConfig(
            dry_run=True, use_query_cache=False
        )
        dry_job = self.client.query(
            sql, job_config=dry_run_config, location=settings.bigquery_location
        )
        estimated = int(dry_job.total_bytes_processed or 0)
        logger.info(
            "Dry run de %s: ~%.2f MB estimados.",
            source.name,
            estimated / 1_000_000,
        )
        if estimated > MAX_BYTES_BILLED:
            raise RuntimeError(
                f"Consulta de '{source.name}' excede o limite de bytes: "
                f"{estimated} > {MAX_BYTES_BILLED}."
            )

        job_config = bigquery.QueryJobConfig(
            use_query_cache=True, maximum_bytes_billed=MAX_BYTES_BILLED
        )
        job = self.client.query(
            sql, job_config=job_config, location=settings.bigquery_location
        )
        dataframe = job.to_dataframe(create_bqstorage_client=False)
        processed = int(getattr(job, "total_bytes_processed", 0) or 0)
        return dataframe, processed


@dataclass
class CallableReader:
    """Leitor offline/derivado a partir de uma função Python."""

    func: object

    def fetch(
        self, settings: Settings, source: SourceConfig
    ) -> tuple[pd.DataFrame, int]:
        dataframe = self.func(settings, source)
        return dataframe, 0


@dataclass
class BronzeExtractionResult:
    """Resultado de uma extração Batch para a camada Bronze."""

    source_name: str
    dataframe: pd.DataFrame
    output_path: Path
    ingestion_id: str
    ingestion_timestamp: datetime
    source_table: str
    records_read: int
    bytes_processed: int


def generate_record_hash(
    dataframe: pd.DataFrame, columns: list[str]
) -> pd.Series:
    """Gera um hash SHA-256 por registro sobre as colunas de negócio."""
    normalized = (
        dataframe[columns].fillna("").astype(str).agg("|".join, axis=1)
    )
    return normalized.map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
    )


def extract_to_bronze(
    settings: Settings,
    source: SourceConfig,
    reader: DataReader,
) -> BronzeExtractionResult:
    """Extrai uma fonte, valida, adiciona metadados e grava Parquet Bronze."""
    logger = configure_logger(name=f"batch_{source.name}", level=settings.log_level)
    source.validate()

    if not source.enabled:
        raise RuntimeError(
            f"Fonte '{source.name}' está desabilitada (enabled: false)."
        )

    ingestion_id = str(uuid4())
    ingestion_timestamp = datetime.now(timezone.utc)
    logger.info("Extraindo fonte '%s'. ingestion_id=%s", source.name, ingestion_id)

    dataframe, bytes_processed = reader.fetch(settings, source)

    if dataframe is None or dataframe.empty:
        raise RuntimeError(f"A fonte '{source.name}' não retornou registros.")

    missing = [c for c in source.selected_columns if c not in dataframe.columns]
    if missing:
        raise RuntimeError(
            f"Fonte '{source.name}': colunas mínimas ausentes: {missing}."
        )

    business_columns = list(source.selected_columns)
    dataframe = dataframe.copy()
    dataframe["_ingestion_id"] = ingestion_id
    dataframe["_ingestion_timestamp"] = ingestion_timestamp.isoformat()
    dataframe["_source_project"] = source.source_project
    dataframe["_source_dataset"] = source.source_dataset
    dataframe["_source_table"] = source.table_id
    dataframe["_load_type"] = "BATCH"
    dataframe["_record_hash"] = generate_record_hash(dataframe, business_columns)
    dataframe["_schema_version"] = source.schema_version

    ingestion_date = ingestion_timestamp.strftime("%Y-%m-%d")
    directory = partition_dir(
        settings.bronze_path / "batch", source.name, "ingestion_date", ingestion_date
    )
    output_path = directory / f"{source.name}_{ingestion_id}.parquet"
    write_parquet(dataframe, output_path)

    logger.info(
        "Extração de '%s' concluída: %s registro(s) -> %s",
        source.name,
        len(dataframe),
        output_path,
    )
    return BronzeExtractionResult(
        source_name=source.name,
        dataframe=dataframe,
        output_path=output_path,
        ingestion_id=ingestion_id,
        ingestion_timestamp=ingestion_timestamp,
        source_table=source.table_id,
        records_read=len(dataframe),
        bytes_processed=bytes_processed,
    )
