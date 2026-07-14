from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from google.cloud import bigquery

from src.common.logger import configure_logger
from src.common.settings import Settings


SOURCE_TABLE = "basedosdados.br_bd_diretorios_brasil.municipio"


@dataclass
class BronzeExtractionResult:
    """Resultado produzido por uma extração para a camada Bronze."""

    dataframe: pd.DataFrame
    output_path: Path
    ingestion_id: str
    ingestion_timestamp: datetime
    source_table: str
    records_read: int


def read_sql_file(settings: Settings, relative_path: str) -> str:
    """Lê um arquivo SQL localizado dentro do projeto."""

    sql_path = settings.project_root / relative_path

    if not sql_path.exists():
        raise FileNotFoundError(
            f"Arquivo SQL não encontrado: {sql_path}"
        )

    return sql_path.read_text(encoding="utf-8")


def generate_record_hash(dataframe: pd.DataFrame) -> pd.Series:
    """
    Gera uma identificação única para o conteúdo de cada registro.

    O hash será útil para detectar alterações e duplicidades.
    """

    business_columns = [
        "id_municipio",
        "nome",
        "sigla_uf",
    ]

    normalized = (
        dataframe[business_columns]
        .fillna("")
        .astype(str)
        .agg("|".join, axis=1)
    )

    return normalized.map(
        lambda value: hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()
    )


def save_audit_file(
    settings: Settings,
    ingestion_id: str,
    ingestion_timestamp: datetime,
    output_path: Path,
    records_read: int,
) -> Path:
    """Salva localmente as informações de auditoria da extração."""

    audit_directory = (
        settings.audit_path
        / "batch"
        / "municipio"
    )

    audit_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    audit_path = audit_directory / f"{ingestion_id}.json"

    audit_data = {
        "pipeline": "batch_municipio",
        "layer": "bronze",
        "source_table": SOURCE_TABLE,
        "ingestion_id": ingestion_id,
        "ingestion_timestamp": ingestion_timestamp.isoformat(),
        "records_read": records_read,
        "local_output_path": str(output_path),
        "status": "SUCCESS",
    }

    audit_path.write_text(
        json.dumps(
            audit_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return audit_path


def extract_municipios_to_bronze(
    client: bigquery.Client,
    settings: Settings,
) -> BronzeExtractionResult:
    """
    Consulta os municípios na Base dos Dados e salva o resultado
    bruto em um arquivo Parquet local.
    """

    logger = configure_logger(
        name="batch_municipio",
        level=settings.log_level,
    )

    ingestion_id = str(uuid4())
    ingestion_timestamp = datetime.now(timezone.utc)

    logger.info(
        "Iniciando extração. ingestion_id=%s",
        ingestion_id,
    )

    sql = read_sql_file(
        settings,
        "sql/extraction/municipio.sql",
    )

    query_config = bigquery.QueryJobConfig(
        use_query_cache=True,
        maximum_bytes_billed=1_000_000_000,
    )

    logger.info(
        "Consultando tabela de origem: %s",
        SOURCE_TABLE,
    )

    query_job = client.query(
        sql,
        job_config=query_config,
        location=settings.bigquery_location,
    )

    dataframe = query_job.to_dataframe(
        create_bqstorage_client=False,
    )

    if dataframe.empty:
        raise RuntimeError(
            "A consulta de municípios não retornou registros."
        )

    required_columns = {
        "id_municipio",
        "nome",
        "sigla_uf",
    }

    missing_columns = required_columns.difference(
        dataframe.columns
    )

    if missing_columns:
        raise RuntimeError(
            "A consulta não retornou as colunas obrigatórias: "
            f"{sorted(missing_columns)}"
        )

    dataframe["_ingestion_id"] = ingestion_id
    dataframe["_ingestion_timestamp"] = ingestion_timestamp
    dataframe["_source_table"] = SOURCE_TABLE
    dataframe["_load_type"] = "BATCH"
    dataframe["_record_hash"] = generate_record_hash(dataframe)

    ingestion_date = ingestion_timestamp.strftime("%Y-%m-%d")

    output_directory = (
        settings.bronze_path
        / "batch"
        / "municipio"
        / f"ingestion_date={ingestion_date}"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_directory
        / f"municipio_{ingestion_id}.parquet"
    )

    dataframe.to_parquet(
        output_path,
        index=False,
        engine="pyarrow",
        compression="snappy",
    )

    save_audit_file(
        settings=settings,
        ingestion_id=ingestion_id,
        ingestion_timestamp=ingestion_timestamp,
        output_path=output_path,
        records_read=len(dataframe),
    )

    logger.info(
        "Extração concluída. registros=%s | arquivo=%s",
        len(dataframe),
        output_path,
    )

    return BronzeExtractionResult(
        dataframe=dataframe,
        output_path=output_path,
        ingestion_id=ingestion_id,
        ingestion_timestamp=ingestion_timestamp,
        source_table=SOURCE_TABLE,
        records_read=len(dataframe),
    )